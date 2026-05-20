"""
Predefined body factories for *reasoning states* — states whose behaviour is driven
by an LLM in a tool-calling loop instead of a hand-written body.

The :func:`reasoning_body` factory builds a state body that runs a plan→act→observe
loop. On each turn the LLM may:

* call any registered tool, including the three built-in *planning tools* —
  ``add_tasks``, ``complete_task`` and ``skip_task`` — that read and write a
  request-scoped :class:`TaskList`;
* emit a final text answer, which is sent back to the user only when every
  task on the list is either ``completed`` or ``skipped`` (or no tasks were
  ever added). If unresolved tasks remain, the orchestrator pushes back with
  a system message and the loop continues.

This evolves the earlier pure-ReAct loop: simple single-step requests still
work with no task list at all (the LLM just answers), while complex multi-step
requests are explicitly planned, tracked and either finished or skipped before
a final answer is allowed through.

See :class:`baf.reasoning.tool.Tool`, :class:`baf.reasoning.skill.Skill`, and
:class:`baf.reasoning.workspace.Workspace` for the user-facing primitives.
"""

import json
from dataclasses import dataclass, field
from typing import Callable, Optional, TYPE_CHECKING

from baf.core.session import Session
from baf.exceptions.logger import logger
from baf.library.tool import build_task_tools
from baf.nlp.llm.llm import LLM, LLMResponse, ToolCall
from baf.reasoning.tool import Tool

if TYPE_CHECKING:
    from baf.core.agent import Agent
    from baf.core.state import State
    from baf.reasoning.skill import Skill
    from baf.reasoning.workspace import Workspace


# --- Prompts -------------------------------------------------------------- #


DEFAULT_SYSTEM_PROMPT = (
    "You are an autonomous reasoning agent. You have access to tools and to "
    "filesystem workspaces. When the user asks about a topic that could "
    "plausibly be answered by data in a registered workspace, ALWAYS browse "
    "the workspace first — call `list_directory` to see what's there, then "
    "`read_file` on relevant files — instead of answering from your training "
    "data. Use other tools when their description matches the user's intent. "
    "Keep replies concise and grounded in tool outputs."
    
    "You MUST call `add_tasks` whenever a request requires more than one tool "
    "call or more than one piece of information to assemble a complete answer. "
    "Only skip the task list for trivial single-step questions like 'what time is it?'."
)


TASK_PLANNING_GUIDANCE = (
    "## Task planning\n"
    "For multi-step requests, plan your work using the task list:\n"
    "1. Call `add_tasks` with a list of descriptions to record the subtasks needed.\n"
    "2. Work through them using the available tools.\n"
    "3. Call `complete_task(task_id, result)` after finishing each one — `result` "
    "is a short summary of what you found / did.\n"
    "4. If a task cannot be completed (missing tool, missing data, ambiguous "
    "request), call `skip_task(task_id, reason)` instead — do not get stuck.\n"
    "5. Do NOT emit a final answer until every task is either 'completed' or "
    "'skipped'. If you reply with a final answer while tasks are still pending, "
    "you will be asked to finish or skip them.\n"
    "For simple, single-step questions you may skip the task list entirely and "
    "answer directly."
)


DEFAULT_FALLBACK_MESSAGE = (
    "I couldn't reach a final answer within the step budget. Please rephrase or "
    "narrow your question."
)


# --- Reasoning step ------------------------------------------------------- #


class ReasoningStepKind:
    """String constants for every kind of :class:`ReasoningStep` the loop emits.

    Two of these — ``REASONING_STARTED`` and ``REASONING_FINISHED`` — bracket
    every reasoning_body invocation so a streaming UI knows when to open and
    close a "live trace" group around the steps in between.
    """
    REASONING_STARTED = "reasoning_started"
    REASONING_FINISHED = "reasoning_finished"
    LLM_TEXT = "llm_text"
    LLM_TOOL_CALLS = "llm_tool_calls"
    TOOL_RESULT = "tool_result"
    TASK_ADDED = "task_added"
    TASK_COMPLETED = "task_completed"
    TASK_SKIPPED = "task_skipped"
    PUSHBACK = "pushback"
    MAX_STEPS = "max_steps"


@dataclass
class ReasoningStep:
    """One observable event emitted by the reasoning loop.

    A ``ReasoningStep`` is the canonical shape forwarded to the user via
    ``session.platform.reply_reasoning_step`` and consumed by the UI client.
    Every kind shares the same envelope (``kind`` + ``step`` + ``summary`` +
    ``details``); kind-specific data lives inside ``details`` so adding a new
    kind never breaks existing consumers.
    """

    kind: str
    """One of the constants on :class:`ReasoningStepKind`."""

    step: int
    """The loop iteration number this event belongs to (0-indexed).
    ``REASONING_STARTED`` and ``REASONING_FINISHED`` carry the step at which
    they were emitted (0 for started, last step for finished)."""

    summary: str
    """A short human-readable line — suitable for direct rendering in a UI
    without inspecting ``details``."""

    details: dict = field(default_factory=dict)
    """Kind-specific structured payload, e.g. ``{"tool_calls": [...]}`` for
    ``LLM_TOOL_CALLS`` or ``{"task_id": ..., "result": ...}`` for
    ``TASK_COMPLETED``."""

    def to_dict(self) -> dict:
        """Serialize for transport (e.g., websocket payload message)."""
        return {
            "kind": self.kind,
            "step": self.step,
            "summary": self.summary,
            "details": self.details,
        }


# --- Task list ------------------------------------------------------------ #


_VALID_STATUSES = ("pending", "in_progress", "completed", "skipped")
_RESOLVED_STATUSES = ("completed", "skipped")


@dataclass
class Task:
    """A single planned subtask within a reasoning loop."""

    id: int
    """Integer id, unique within a :class:`TaskList`. Surfaced to the LLM so
    it can refer to specific tasks via ``complete_task`` / ``skip_task``."""

    description: str
    """A short imperative description."""

    status: str = "pending"
    """One of ``pending`` / ``in_progress`` / ``completed`` / ``skipped``.
    New tasks start as ``pending``."""

    result: str = ""
    """A short summary of the outcome — populated when the task is completed
    or skipped."""


class TaskList:
    """A request-scoped list of tasks the LLM is expected to resolve.

    A new TaskList is created at the start of every reasoning_body invocation —
    it does not persist across user messages. The reasoning loop checks
    :meth:`all_resolved` before accepting a final answer from the LLM.
    """

    def __init__(self) -> None:
        self.tasks: list[Task] = []
        self._next_id: int = 1

    def add(self, description: str) -> Task:
        """Append a new pending task to the list."""
        task = Task(id=self._next_id, description=description.strip())
        self._next_id += 1
        self.tasks.append(task)
        return task

    def get(self, task_id: int) -> Optional[Task]:
        """Return the task with ``task_id`` or ``None``."""
        for t in self.tasks:
            if t.id == task_id:
                return t
        return None

    def update(self, task_id: int, status: str, result: str = "") -> Optional[Task]:
        """Update the status (and optionally the result) of an existing task."""
        if status not in _VALID_STATUSES:
            return None
        task = self.get(task_id)
        if task is None:
            return None
        task.status = status
        if result:
            task.result = result
        return task

    def all_resolved(self) -> bool:
        """True when no tasks are pending or in_progress.

        Returns True for an empty list — the LLM is allowed to skip planning
        for simple single-step requests.
        """
        return all(t.status in _RESOLVED_STATUSES for t in self.tasks)

    def pending(self) -> list[Task]:
        """Return the still-unresolved tasks."""
        return [t for t in self.tasks if t.status not in _RESOLVED_STATUSES]

    def to_prompt(self) -> str:
        """Render the current state of the list as a markdown block."""
        if not self.tasks:
            return "## Task list\n(empty — use `add_tasks` to plan multi-step work)"
        markers = {"pending": "[ ]", "in_progress": "[~]",
                   "completed": "[x]", "skipped": "[/]"}
        lines = ["## Task list"]
        for t in self.tasks:
            marker = markers.get(t.status, "[?]")
            line = f"{marker} #{t.id} ({t.status}) — {t.description}"
            if t.result:
                line += f" → {t.result}"
            lines.append(line)
        return "\n".join(lines)

    def to_dict(self) -> list[dict]:
        """Serialize for the session scratchpad."""
        return [{"id": t.id, "description": t.description,
                 "status": t.status, "result": t.result} for t in self.tasks]

# --- Step streaming ------------------------------------------------------- #


# Cap on how many characters of a tool result are included in a streamed
# `tool_result` event. Long file reads can reach the workspace's `max_read_bytes`
# (200 KB by default) — shipping that to the UI on every step is wasteful, and
# the LLM has the full content anyway.
_TOOL_RESULT_PAYLOAD_LIMIT = 4_000


def _truncate_for_payload(text: str, limit: int = _TOOL_RESULT_PAYLOAD_LIMIT) -> str:
    """Truncate ``text`` to ``limit`` chars with a clear marker if cut."""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [truncated, {len(text)} chars total]"


def _send_step(session: Session, step: ReasoningStep, stream_steps: bool = True) -> None:
    """Forward a :class:`ReasoningStep` to ``session.platform.reply_reasoning_step``.

    Silently no-ops when ``stream_steps`` is False or when the platform does
    not expose a ``reply_reasoning_step`` method (Telegram, A2A, etc.). Any
    exception from the platform is caught and logged so a UI bug cannot kill
    the reasoning loop.
    """
    if not stream_steps:
        return
    method = getattr(getattr(session, "platform", None), "reply_reasoning_step", None)
    if method is None:
        return
    try:
        method(session, step.to_dict())
    except Exception as e:
        logger.warning(f"[Reasoning] could not emit step event ({step.kind}): {e}")


def _send_task_list(session: Session, task_list: 'TaskList', stream_steps: bool = True) -> None:
    """Forward the current task list snapshot to ``session.platform.reply_task_list_update``.

    Same gating as :func:`_send_step`. Sent alongside (not in place of) the
    matching ``task_added`` / ``task_completed`` / ``task_skipped`` step events
    so a UI can render a live task panel without reconstructing it from the
    step stream.
    """
    if not stream_steps:
        return
    method = getattr(getattr(session, "platform", None), "reply_task_list_update", None)
    if method is None:
        return
    try:
        method(session, task_list.to_dict())
    except Exception as e:
        logger.warning(f"[Reasoning] could not emit task list update: {e}")


# --- System prompt builder ----------------------------------------------- #


def _build_system_prompt(
    skills: list['Skill'],
    workspaces: list['Workspace'],
    base_prompt: str,
    task_list: Optional[TaskList],
) -> str:
    """Concatenate base prompt + skills + workspace previews + task list."""
    parts: list[str] = [base_prompt]

    for skill in skills:
        parts.append(skill.to_prompt())

    if workspaces:
        ws_lines = [
            "## Workspaces",
            "Browse and read files from these filesystem workspaces using the "
            "`list_directory` and `read_file` tools. Pass the `workspace` argument "
            "to select which workspace; if only one is registered you may omit it. "
            "Each workspace's top-level entries are previewed below — use them as "
            "your starting point. If the user's question could be answered by any "
            "of these files, call `read_file` on the relevant ones BEFORE replying.",
        ]
        for ws in workspaces:
            ws_lines.append("")
            mode = "writable" if getattr(ws, "writable", True) else "read-only"
            ws_lines.append(f"### Workspace: {ws.name} ({mode})")
            if ws.description:
                ws_lines.append(ws.description)
            ws_lines.append(f"Root path: {ws.root}")
            if not getattr(ws, "writable", True):
                ws_lines.append(
                    "This workspace is read-only — `write_file`, `create_file`, "
                    "and `delete_file` will fail on it."
                )
            preview = ws.top_level_listing()
            if preview:
                ws_lines.append("Top-level entries:")
                ws_lines.append(preview)
            else:
                ws_lines.append("(empty workspace)")
        parts.append("\n".join(ws_lines))

    if task_list is not None:
        parts.append(TASK_PLANNING_GUIDANCE)
        parts.append(task_list.to_prompt())

    return "\n\n".join(parts)


# --- Tool execution helpers ---------------------------------------------- #


# How many characters of a tool's output to include in the DEBUG log line.
# Long results (e.g., a `read_file` of a 200 KB file) are truncated to keep
# the log readable; the full content is still passed to the LLM.
_TOOL_OUTPUT_LOG_LIMIT = 500


def _truncate_for_log(text: str, limit: int = _TOOL_OUTPUT_LOG_LIMIT) -> str:
    """Truncate ``text`` to ``limit`` chars with a clear marker if cut."""
    if len(text) <= limit:
        return text
    return text[:limit] + f"... [truncated, {len(text)} chars total]"


_TASK_TOOL_NAMES = ("add_tasks", "complete_task", "skip_task")


def _execute_tool_calls(
    tool_calls: list[ToolCall],
    tools_by_name: dict[str, Tool],
    session: Session = None,
    stream_steps: bool = False,
    step: int = 0,
) -> list[dict]:
    """Run each requested tool call and return the tool-result messages.

    Each call is logged at ``DEBUG`` level with its arguments and a truncated
    view of the result. When ``stream_steps`` is True, a ``tool_result`` event
    is also forwarded to the platform for each non-task tool right after it
    runs — task tools emit their own ``task_added`` / ``task_completed`` /
    ``task_skipped`` events from inside the tool function, so they are skipped
    here to avoid duplicates.
    """
    results: list[dict] = []
    for call in tool_calls:
        logger.debug(f"[Reasoning] -> calling tool '{call.name}' "
                     f"with args={call.arguments}")
        tool = tools_by_name.get(call.name)
        if tool is None:
            content = f"ERROR: tool '{call.name}' is not registered"
            logger.warning(f"[Reasoning] LLM requested unknown tool: {call.name}")
        else:
            content = tool.call(call.arguments)
        logger.debug(f"[Reasoning] <- tool '{call.name}' result "
                     f"({len(content)} chars):\n{_truncate_for_log(content)}")
        if session is not None and call.name not in _TASK_TOOL_NAMES:
            _send_step(session, ReasoningStep(
                kind=ReasoningStepKind.TOOL_RESULT,
                step=step,
                summary=f"{call.name} returned ({len(content)} chars)",
                details={
                    "name": call.name,
                    "arguments": call.arguments,
                    "content": _truncate_for_payload(content),
                    "is_error": content.startswith("ERROR"),
                },
            ), stream_steps)
        results.append({
            "role": "tool",
            "tool_call_id": call.id,
            "content": content,
        })
    return results


def _assistant_tool_call_message(tool_calls: list[ToolCall]) -> dict:
    """Build the assistant message that records the tool calls the LLM just emitted.

    OpenAI's chat format requires the model's tool-call announcement to be
    preserved in the conversation history (with matching tool_call_id values)
    before the tool-result messages.
    """
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.name,
                    "arguments": json.dumps(call.arguments),
                },
            }
            for call in tool_calls
        ],
    }


def _build_pushback_message(pending: list[Task]) -> str:
    """Compose the system message sent when the LLM tries to finalize too early."""
    summary = ", ".join(f"#{t.id} ({t.description})" for t in pending)
    return (
        "You returned a final answer but the task list still has unresolved "
        f"tasks: {summary}. Either finish them with the available tools and "
        "call `complete_task`, or call `skip_task` with a brief reason. Do "
        "not produce a final answer again until every task is resolved."
    )


# --- Body factory --------------------------------------------------------- #


def reasoning_body(
    llm: LLM,
    max_steps: int = 8,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    fallback_message: str = DEFAULT_FALLBACK_MESSAGE,
    enable_task_planning: bool = True,
    stream_steps: bool = True,
) -> Callable[[Session], None]:
    """Build a state body that runs an LLM-driven plan→act→observe loop.

    The body reads the user message from ``session.event`` and, on each
    iteration, calls ``llm.predict_with_tools`` with:

    * the agent's registered tools (read at execution time from
      ``agent._tools``);
    * the three built-in planning tools (``add_tasks``, ``complete_task``,
      ``skip_task``) when ``enable_task_planning=True``;
    * a system message containing the active skills, workspace previews,
      task-planning guidance, and the live task list.

    The loop terminates when the LLM returns a final text answer **and** every
    task on the list is resolved. If unresolved tasks remain, the orchestrator
    appends a push-back system message and continues. If ``max_steps`` is
    reached without convergence the configured fallback message is sent.

    The final task list and a per-step trace (tool calls, results, push-backs)
    are persisted to ``session['reasoning_scratchpad']`` for inspection.

    Args:
        llm (LLM): the LLM that drives the loop. Must implement
            ``predict_with_tools``.
        max_steps (int): maximum number of LLM turns per user message.
        system_prompt (str): the base system prompt prepended to the skill /
            workspace / task-list blocks.
        fallback_message (str): the message sent if ``max_steps`` is exhausted.
        enable_task_planning (bool): when False, fall back to a pure ReAct
            loop (no built-in planning tools, no push-back, first text
            response wins). Defaults to True.
        stream_steps (bool): when True, forward every intermediate event
            (LLM tool calls, tool results, task add/complete/skip, push-back,
            max-steps fallback) to the user via
            ``session.platform.reply_reasoning_step`` if the platform
            implements it. The final answer is still sent via
            ``session.reply``. No-op on platforms without a
            ``reply_reasoning_step`` method. Defaults to True.

    Returns:
        Callable[[Session], None]: a state body suitable for
        :meth:`baf.core.state.State.set_body`.
    """

    def reasoning_body(session: Session) -> None:
        agent = session._agent
        user_tools = list(getattr(agent, "_tools", {}).values())
        skills = list(getattr(agent, "_skills", {}).values())
        workspaces = list(getattr(agent, "_workspaces", {}).values())

        # Single-element list used as a mutable cell so the task-tool closures
        # can read the current loop iteration without needing a setter method.
        step_cell: list = [0]

        task_list: Optional[TaskList] = TaskList() if enable_task_planning else None
        task_tools: list[Tool] = (
            build_task_tools(task_list, session, stream_steps, step_cell)
            if task_list is not None else []
        )

        all_tools = user_tools + task_tools
        tools_by_name = {t.name: t for t in all_tools}
        tool_schemas = [t.openai_schema for t in all_tools]

        user_message = getattr(session.event, "message", None) or ""
        messages: list[dict] = [{"role": "user", "content": user_message}]
        scratchpad: list[dict] = []

        logger.debug(
            f"[Reasoning] starting loop: tools={[t.name for t in all_tools]}, "
            f"skills={[s.name for s in skills]}, "
            f"workspaces={[w.name for w in workspaces]}, "
            f"task_planning={enable_task_planning}"
        )

        # Bracket the trace with reasoning_started / reasoning_finished so a
        # streaming UI can group the steps in between into a single block.
        _send_step(session, ReasoningStep(
            kind=ReasoningStepKind.REASONING_STARTED,
            step=0,
            summary="reasoning started",
            details={
                "user_message": user_message,
                "task_planning": enable_task_planning,
                "max_steps": max_steps,
            },
        ), stream_steps)

        try:
            _run_reasoning_loop(
                session=session,
                llm=llm,
                messages=messages,
                tool_schemas=tool_schemas,
                tools_by_name=tools_by_name,
                skills=skills,
                workspaces=workspaces,
                task_list=task_list,
                step_cell=step_cell,
                scratchpad=scratchpad,
                max_steps=max_steps,
                system_prompt=system_prompt,
                fallback_message=fallback_message,
                stream_steps=stream_steps,
            )
        finally:
            _send_step(session, ReasoningStep(
                kind=ReasoningStepKind.REASONING_FINISHED,
                step=step_cell[0],
                summary="reasoning finished",
                details={
                    "final_task_list": (
                        task_list.to_dict() if task_list is not None else []
                    ),
                },
            ), stream_steps)
            # Tie all reasoning events emitted during this loop (which were
            # inserted with chat_id IS NULL) to the chat row that just closed
            # the loop — best-effort, errors are logged but do not break the
            # chat reply that already went out to the user.
            session.link_pending_reasoning_events()

    return reasoning_body


def _run_reasoning_loop(
    session: Session,
    llm: LLM,
    messages: list,
    tool_schemas: list,
    tools_by_name: dict,
    skills: list,
    workspaces: list,
    task_list: Optional[TaskList],
    step_cell: list,
    scratchpad: list,
    max_steps: int,
    system_prompt: str,
    fallback_message: str,
    stream_steps: bool,
) -> None:
    """The actual think→act→observe loop, factored out so :func:`reasoning_body`
    can wrap it in a single ``reasoning_started`` / ``reasoning_finished``
    bracket via ``try``/``finally``."""
    for step in range(max_steps):
        step_cell[0] = step
        full_system_prompt = _build_system_prompt(
            skills, workspaces, system_prompt, task_list
        )
        logger.debug(f"[Reasoning] step {step}: ")  # system prompt: full_system_prompt

        try:
            response: LLMResponse = llm.predict_with_tools(
                messages=messages,
                tools=tool_schemas,
                system_message=full_system_prompt,
            )
        except NotImplementedError as e:
            logger.error(f"[Reasoning] LLM does not support tool-calling: {e}")
            session.reply(f"ERROR: configured LLM does not support tool-calling ({llm.name}).")
            return
        except Exception as e:
            logger.exception(f"[Reasoning] LLM call failed at step {step}: {e}")
            session.reply(f"ERROR: reasoning failed ({type(e).__name__}: {e}).")
            return

        if response.tool_calls:
            logger.info(f"[Reasoning] step {step}: tool calls = "
                        f"{[c.name for c in response.tool_calls]}")
            _send_step(session, ReasoningStep(
                kind=ReasoningStepKind.LLM_TOOL_CALLS,
                step=step,
                summary=f"calling {len(response.tool_calls)} tool(s): "
                        + ", ".join(c.name for c in response.tool_calls),
                details={
                    "tool_calls": [
                        {"id": c.id, "name": c.name, "arguments": c.arguments}
                        for c in response.tool_calls
                    ],
                },
            ), stream_steps)
            messages.append(_assistant_tool_call_message(response.tool_calls))
            tool_results = _execute_tool_calls(
                response.tool_calls, tools_by_name,
                session=session, stream_steps=stream_steps, step=step,
            )
            messages.extend(tool_results)
            scratchpad.append({
                "step": step,
                "tool_calls": [{"name": c.name, "arguments": c.arguments}
                               for c in response.tool_calls],
                "tool_results": [r["content"] for r in tool_results],
            })
            continue

        if response.text is not None:
            logger.debug(f"[Reasoning] step {step}: response.text :\n{response.text}")
            pending = task_list.pending() if task_list is not None else []
            if pending:
                pushback = _build_pushback_message(pending)
                logger.info(
                    f"[Reasoning] step {step}: rejecting final answer, "
                    f"{len(pending)} task(s) still pending"
                )
                logger.debug(f"[Reasoning] push-back:\n{pushback}")
                _send_step(session, ReasoningStep(
                    kind=ReasoningStepKind.LLM_TEXT,
                    step=step,
                    summary="(intermediate) LLM proposed a final answer",
                    details={"text": response.text, "is_final": False},
                ), stream_steps)
                _send_step(session, ReasoningStep(
                    kind=ReasoningStepKind.PUSHBACK,
                    step=step,
                    summary=f"rejected: {len(pending)} task(s) still pending",
                    details={
                        "pending": [
                            {"id": t.id, "description": t.description,
                             "status": t.status}
                            for t in pending
                        ],
                    },
                ), stream_steps)
                messages.append({"role": "assistant", "content": response.text})
                messages.append({"role": "system", "content": pushback})
                scratchpad.append({
                    "step": step,
                    "rejected_answer": response.text,
                    "pending_task_ids": [t.id for t in pending],
                })
                continue

            logger.info(f"[Reasoning] step {step}: final answer ({len(response.text)} chars)")
            scratchpad.append({"step": step, "answer": response.text})
            if task_list is not None:
                scratchpad.append({"final_task_list": task_list.to_dict()})
            session.set("reasoning_scratchpad", scratchpad)
            session.reply(response.text)
            return

        logger.warning(f"[Reasoning] step {step}: empty response, breaking loop")
        break

    logger.warning(f"[Reasoning] max_steps={max_steps} exhausted without final answer")
    _send_step(session, ReasoningStep(
        kind=ReasoningStepKind.MAX_STEPS,
        step=step_cell[0],
        summary=f"step budget exhausted ({max_steps} steps)",
        details={
            "max_steps": max_steps,
            "pending": (
                [{"id": t.id, "description": t.description, "status": t.status}
                 for t in task_list.pending()]
                if task_list is not None else []
            ),
        },
    ), stream_steps)
    if task_list is not None:
        scratchpad.append({"final_task_list": task_list.to_dict()})
    session.set("reasoning_scratchpad", scratchpad)
    session.reply(fallback_message)


# --- Predefined-state factory ------------------------------------------- #


def new_reasoning_state(
    agent: 'Agent',
    llm: LLM,
    name: str = "reasoning_state",
    initial: bool = True,
    max_steps: int = 8,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    fallback_message: str = DEFAULT_FALLBACK_MESSAGE,
    enable_task_planning: bool = True,
    stream_steps: bool = True,
) -> 'State':
    """Create a predefined *reasoning state* on ``agent`` and return it.

    Equivalent to::

        state = agent.new_state(name, initial=initial)
        state.set_body(reasoning_body(llm, ...))
        return state

    Importable from the library package so callers can register predefined
    states by import (consistent with how future predefined states will be
    added)::

        from baf.library.state.reasoning_state_library import new_reasoning_state

        state = new_reasoning_state(agent, llm=gpt)
        state.when_event().go_to(state)  # caller wires transitions externally

    Transitions are intentionally NOT added here — the developer chooses how
    to connect this state to the rest of the agent's state machine (typically
    a ``state.when_event().go_to(state)`` self-loop, but other shapes are
    valid: gating on a condition, chaining from another state, etc.).

    Args:
        agent (Agent): the agent the state is created on.
        llm (LLM): the LLM that drives the reasoning loop. Must implement
            ``predict_with_tools``.
        name (str): the state's name. Defaults to ``'reasoning_state'``.
        initial (bool): whether this state is the agent's initial state.
            Defaults to True.
        max_steps (int): maximum LLM turns per user message. Defaults to 8.
        system_prompt (str): the base system prompt prepended to the skill /
            workspace / task-list blocks.
        fallback_message (str): the message sent if ``max_steps`` is exhausted.
        enable_task_planning (bool): when False, fall back to a pure ReAct
            loop (no built-in planning tools, no push-back, first text
            response wins). Defaults to True.
        stream_steps (bool): when True, forward every intermediate event to
            the user via ``session.platform.reply_reasoning_step`` if
            implemented. Defaults to True.

    Returns:
        State: the newly created reasoning state, ready for transition wiring.
    """
    state = agent.new_state(name, initial=initial)
    state.set_body(reasoning_body(
        llm,
        max_steps=max_steps,
        system_prompt=system_prompt,
        fallback_message=fallback_message,
        enable_task_planning=enable_task_planning,
        stream_steps=stream_steps,
    ))
    return state
