"""Streamlit UI rendering and aggregation for the reasoning extension.

The Streamlit chat client receives ``AGENT_REPLY_REASONING_STEP`` and
``AGENT_REPLY_TASK_LIST_UPDATE`` payloads from the WebSocket as the
predefined reasoning state runs. Rather than rendering each step as its
own chat row (which floods the UI), this module folds them into a single
synthetic ``REASONING_TRACE`` message in the chat history and renders it
as one collapsible expander with a task panel — mirroring the React UI in
the BESSER-Agentic-Framework-UI repo.

Two halves:

* :func:`append_reasoning_step` and :func:`apply_task_list_update` —
  called from :mod:`baf.platforms.websocket.streamlit_ui.websocket_callbacks`'s
  ``on_message``. They mutate the most recent in-progress trace in
  ``HISTORY`` (or open a new one) and trigger a Streamlit rerun.
* :func:`write_reasoning_trace` and :func:`is_empty_trace` — called from
  :mod:`baf.platforms.websocket.streamlit_ui.chat`'s ``write_message``
  to render the aggregated trace as a single expander.

The module is self-contained: no public API leaks back to the rest of
the streamlit_ui package, so the existing chat/websocket code stays
otherwise unchanged.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st

from baf.core.message import Message, MessageType
from baf.platforms.websocket.streamlit_ui.vars import HISTORY


# ─── Filtering constants ──────────────────────────────────────────────── #


# Step kinds emitted from inside the built-in task tools — already shown in
# the task panel below the trace, so we don't repeat them in the step list.
_TASK_EVENT_KINDS = frozenset({"task_added", "task_completed", "task_skipped"})

# Bracket markers (signal-only) — never rendered.
_BRACKET_KINDS = frozenset({"reasoning_started", "reasoning_finished"})

# Tool names whose ``llm_tool_calls`` announcement is also redundant with the
# task panel. Mixed batches with at least one non-task tool are kept.
_TASK_TOOL_NAMES = frozenset({"add_tasks", "complete_task", "skip_task"})

_KIND_ICONS = {
    "llm_text": "💬",
    "llm_tool_calls": "🛠️",
    "tool_result": "📥",
    "pushback": "↩️",
    "max_steps": "⏱️",
}

_TASK_STATUS_BOX = {
    "pending":     "☐",
    "in_progress": "◐",
    "completed":   "✅",
    "skipped":     "⊘",
}


# ─── Filtering helpers ────────────────────────────────────────────────── #


def _is_task_only_tool_call(step: dict) -> bool:
    """True if a ``llm_tool_calls`` event invokes only built-in task tools."""
    if step.get("kind") != "llm_tool_calls":
        return False
    calls = (step.get("details") or {}).get("tool_calls") or []
    if not calls:
        return False
    return all(c.get("name") in _TASK_TOOL_NAMES for c in calls)


def _visible_steps(steps: list) -> list:
    """Filter out bracket markers, task events, and task-only tool calls."""
    return [
        s for s in steps
        if s.get("kind") not in _BRACKET_KINDS
        and s.get("kind") not in _TASK_EVENT_KINDS
        and not _is_task_only_tool_call(s)
    ]


def is_empty_trace(content: dict) -> bool:
    """True when a reasoning trace has no observable steps and no tasks.

    Empty traces typically result from a pure LLM-only reply that did not
    invoke any tools or plan any tasks — rendering them would just produce
    an empty chat bubble.
    """
    if not isinstance(content, dict):
        return True
    return (
        not _visible_steps(content.get("steps") or [])
        and not (content.get("tasks") or [])
    )


# ─── Aggregation (called from on_message) ─────────────────────────────── #


def _last_in_progress_trace(history: list) -> Message | None:
    """Return the most recent in-progress :class:`MessageType.REASONING_TRACE`
    message in ``history``, or ``None`` if every trace is closed (or none
    exists yet). Walks from the end so the latest open trace is found
    first."""
    for msg in reversed(history):
        if msg.type is MessageType.REASONING_TRACE \
                and isinstance(msg.content, dict) \
                and msg.content.get("in_progress"):
            return msg
    return None


def append_reasoning_step(streamlit_session: Any, step: dict) -> None:
    """Fold a streamed reasoning step into the active trace in HISTORY.

    * ``reasoning_started`` → append a fresh REASONING_TRACE message with
      ``in_progress=True``.
    * ``reasoning_finished`` → append the bracket marker, flip
      ``in_progress`` to False so the UI collapses the expander.
    * Any other step → append to the currently-open trace.

    Defensive fallback: if no open trace exists when a non-bracket step
    arrives (history replay, reconnect, etc.) a new trace is created so
    the step is never silently dropped.
    """
    history = streamlit_session._session_state[HISTORY]
    kind = step.get("kind") if isinstance(step, dict) else None

    if kind == "reasoning_started":
        history.append(Message(
            t=MessageType.REASONING_TRACE,
            content={"steps": [step], "tasks": [], "in_progress": True},
            is_user=False,
            timestamp=datetime.now(),
        ))
        return

    trace = _last_in_progress_trace(history)
    if trace is None:
        trace = Message(
            t=MessageType.REASONING_TRACE,
            content={
                "steps": [],
                "tasks": [],
                "in_progress": kind != "reasoning_finished",
            },
            is_user=False,
            timestamp=datetime.now(),
        )
        history.append(trace)

    trace.content["steps"].append(step)
    if kind == "reasoning_finished":
        trace.content["in_progress"] = False


def apply_task_list_update(streamlit_session: Any, tasks: list) -> None:
    """Replace the task snapshot of the active trace.

    Each task_list_update payload carries the full current snapshot, so
    the UI just swaps the trace's ``tasks`` list rather than diffing.
    Defensive: opens a fresh trace if none is currently in progress.
    """
    history = streamlit_session._session_state[HISTORY]
    trace = _last_in_progress_trace(history)
    if trace is None:
        history.append(Message(
            t=MessageType.REASONING_TRACE,
            content={
                "steps": [],
                "tasks": list(tasks or []),
                "in_progress": True,
            },
            is_user=False,
            timestamp=datetime.now(),
        ))
        return
    trace.content["tasks"] = list(tasks or [])


# ─── Rendering (called from write_message) ────────────────────────────── #


def write_reasoning_trace(content: dict) -> None:
    """Render an aggregated reasoning trace as a single collapsible expander.

    * While ``in_progress`` is True the expander is open by default so the
      user can watch the agent think.
    * Once the loop finishes (``in_progress`` flipped to False) the
      expander defaults to collapsed; the user can re-open it for inspection.
    * Steps are grouped by their ``step`` number so each loop iteration
      shows a single ``STEP N`` header. Task-related events are omitted
      from the step list — the task panel below is the source of truth
      for task progress.
    * The task panel renders the live snapshot with colored status boxes.
    """
    steps = content.get("steps") or []
    tasks = content.get("tasks") or []
    in_progress = bool(content.get("in_progress"))

    visible = _visible_steps(steps)

    # Group by step number, preserving order.
    groups: list[tuple[int, list[dict]]] = []
    for s in visible:
        if groups and groups[-1][0] == s.get("step"):
            groups[-1][1].append(s)
        else:
            groups.append((s.get("step"), [s]))

    n = len(groups)
    if in_progress:
        label = f"🧠 Reasoning… ({n} step{'s' if n != 1 else ''})"
    else:
        label = f"✨ Reasoned across {n} step{'s' if n != 1 else ''}"

    with st.expander(label, expanded=in_progress):
        for i, (_, events) in enumerate(groups):
            st.markdown(f"**STEP {i}**")
            for ev in events:
                icon = _KIND_ICONS.get(ev.get("kind"), "🔹")
                summary = ev.get("summary", "")
                st.markdown(f"{icon} *{summary}*")

        if tasks:
            st.markdown("---")
            st.markdown("**Tasks**")
            for t in tasks:
                box = _TASK_STATUS_BOX.get(t.get("status", "pending"), "☐")
                line = f"{box} **#{t.get('id', '?')}** — {t.get('description', '')}"
                result = t.get("result")
                if result:
                    line += f"  →  *{result}*"
                st.markdown(line)
