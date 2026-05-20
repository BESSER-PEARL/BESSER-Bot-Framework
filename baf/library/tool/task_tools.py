"""Built-in *planning tools* for the predefined reasoning state.

Three tools — ``add_tasks``, ``complete_task``, ``skip_task`` — that read and
write a request-scoped :class:`~baf.library.state.reasoning_state_library.TaskList`.
They are NOT registered on the agent's permanent tool registry: a fresh
:class:`~baf.reasoning.tool.Tool` instance is built per
:func:`baf.library.state.reasoning_state_library.reasoning_body` invocation
via :func:`build_task_tools`, so each user request gets its own task list and
the tool closures cannot leak state between requests.

Compared with the universal workspace tools in
:mod:`baf.library.tool.workspace_tools`, the task tools have additional
runtime dependencies — they emit ``task_added`` / ``task_completed`` /
``task_skipped`` reasoning step events alongside the mutation, and forward a
fresh task-list snapshot to the streaming UI. The reasoning loop wires these
in by passing ``session`` + ``stream_steps`` + a single-element ``step_cell``
that holds the current iteration number.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from baf.reasoning.tool import Tool

if TYPE_CHECKING:
    from baf.core.session import Session
    from baf.library.state.reasoning_state_library import TaskList


def build_task_tools(
    task_list: 'TaskList',
    session: 'Session',
    stream_steps: bool,
    step_cell: list,
) -> list[Tool]:
    """Build the three planning :class:`~baf.reasoning.tool.Tool` instances
    that close over a single ``task_list``.

    These are private to a single ``reasoning_body`` invocation. After each
    successful task-list mutation the tools also forward a
    ``reasoning_step`` event and a ``task_list_update`` snapshot to the
    session's platform (via the helpers in
    :mod:`baf.library.state.reasoning_state_library`). The current loop
    iteration is read from ``step_cell[0]`` — the body updates it once per
    iteration so task-tool callers don't need to know it.

    Args:
        task_list (TaskList): the request-scoped task list these tools mutate.
        session (Session): the user session — used to emit step / task-list
            events back to the UI.
        stream_steps (bool): whether to forward step / task-list events to
            ``session.platform``. False disables the streaming hooks.
        step_cell (list): a 1-element mutable cell whose ``[0]`` value is the
            current loop iteration number; the reasoning body updates it.

    Returns:
        list[Tool]: ``[add_tasks_tool, complete_task_tool, skip_task_tool]``.
    """
    # Imported lazily to break a circular import: reasoning_state_library
    # imports build_task_tools from this module, while this module needs
    # `_send_step`, `_send_task_list`, `ReasoningStep` and `ReasoningStepKind`
    # from there. By the time `build_task_tools` is called from inside
    # ``reasoning_body``, both modules are fully loaded.
    from baf.library.state.reasoning_state_library import (
        ReasoningStep,
        ReasoningStepKind,
        _send_step,
        _send_task_list,
    )

    def add_tasks(descriptions: list[str]) -> str:
        """Plan multi-step work by adding one or more tasks to the task list.

        Each new task gets an integer id you can later pass to `complete_task`
        or `skip_task`. Call this once at the start of a complex request, or
        again later if you discover additional subtasks.

        Args:
            descriptions: list of short imperative task descriptions.
        """
        if not descriptions:
            return "ERROR: descriptions list is empty; pass at least one task."
        added = [task_list.add(d) for d in descriptions]
        _send_step(session, ReasoningStep(
            kind=ReasoningStepKind.TASK_ADDED,
            step=step_cell[0],
            summary=f"planned {len(added)} task(s): "
                    + ", ".join(f"#{t.id} {t.description}" for t in added),
            details={"tasks": [{"id": t.id, "description": t.description}
                               for t in added]},
        ), stream_steps)
        _send_task_list(session, task_list, stream_steps)
        return "Added tasks:\n" + "\n".join(
            f"#{t.id}: {t.description}" for t in added
        )

    def complete_task(task_id: int, result: str) -> str:
        """Mark a task as completed.

        Args:
            task_id: the id of the task to mark complete.
            result: a short summary of the outcome (what was found or done).
        """
        task = task_list.update(task_id, status="completed", result=result)
        if task is None:
            return f"ERROR: no task with id #{task_id}."
        _send_step(session, ReasoningStep(
            kind=ReasoningStepKind.TASK_COMPLETED,
            step=step_cell[0],
            summary=f"completed task #{task.id} — {task.result}",
            details={"task_id": task.id,
                     "description": task.description,
                     "result": task.result},
        ), stream_steps)
        _send_task_list(session, task_list, stream_steps)
        return f"Task #{task.id} marked completed — {task.result}"

    def skip_task(task_id: int, reason: str) -> str:
        """Mark a task as skipped because it cannot or should not be completed.

        Use this whenever a task is blocked — missing tool, missing data,
        ambiguous request — instead of getting stuck retrying.

        Args:
            task_id: the id of the task to skip.
            reason: a short explanation of why the task is being skipped.
        """
        task = task_list.update(task_id, status="skipped", result=reason)
        if task is None:
            return f"ERROR: no task with id #{task_id}."
        _send_step(session, ReasoningStep(
            kind=ReasoningStepKind.TASK_SKIPPED,
            step=step_cell[0],
            summary=f"skipped task #{task.id} — {task.result}",
            details={"task_id": task.id,
                     "description": task.description,
                     "reason": task.result},
        ), stream_steps)
        _send_task_list(session, task_list, stream_steps)
        return f"Task #{task.id} marked skipped — {task.result}"

    return [Tool(add_tasks), Tool(complete_task), Tool(skip_task)]
