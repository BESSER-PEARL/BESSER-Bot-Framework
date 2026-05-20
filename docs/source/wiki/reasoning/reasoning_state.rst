Reasoning state
===============

The **reasoning state** is a predefined :class:`~baf.core.state.State` whose
body runs an LLM-driven **plan → act → observe** loop instead of a
hand-written body. On each iteration the LLM may call any registered
:doc:`tool <tools>`, browse / modify a registered :doc:`workspace
<workspaces>`, plan multi-step work via the built-in *task list*, or emit
a final answer. The loop exits only when every planned task is resolved
(``completed`` or ``skipped``) and the LLM emits a final text reply.

This evolves the simpler ReAct loop with two additions on top:

- **Skills, workspaces and task planning** automatically fold into the
  system prompt so the LLM doesn't need to be told manually about each.
- **Push-back semantics**: if the LLM tries to finalise with tasks still
  pending, the orchestrator rejects the answer and asks it to finish or
  explicitly skip them.

How to use
----------

The recommended factory is :func:`~baf.library.state.reasoning_state_library.new_reasoning_state`,
imported from the library package:

.. code:: python

    from baf.library.state import new_reasoning_state
    from baf.nlp.llm.llm_openai_api import LLMOpenAI

    gpt = LLMOpenAI(agent=agent, name='gpt-4o-mini')

    reasoning_state = new_reasoning_state(agent, llm=gpt)
    reasoning_state.when_event().go_to(reasoning_state)

The factory creates the state on the agent and attaches the predefined
body. Transitions are intentionally **not** wired automatically — the
developer chooses how to connect this state to the rest of the agent's
state machine. The most common shape is a self-loop on any incoming
event (the snippet above), but the state can also be reached from another
state, gated on a condition, etc.

You can also check the :doc:`../../examples/reasoning_agent` for a complete
runnable example.

The LLM passed in must support tool-calling. Today
:class:`~baf.nlp.llm.llm_openai_api.LLMOpenAI` implements it natively;
other wrappers raise ``NotImplementedError`` if used. See
:meth:`baf.nlp.llm.llm.LLM.predict_with_tools` for the contract.

Configuration
-------------

:func:`~baf.library.state.reasoning_state_library.new_reasoning_state`
forwards a few configuration knobs to the underlying body:

.. code:: python

    new_reasoning_state(
        agent,
        llm=gpt,
        name='reasoning_state',     # state name
        initial=True,               # mark as the agent's initial state
        max_steps=8,                # max LLM turns per user message
        system_prompt=...,          # override the base system prompt
        fallback_message=...,       # message sent when max_steps is exhausted
        enable_task_planning=True,  # built-in task list + push-back
        stream_steps=True,          # forward intermediate steps to the UI
    )

Setting ``enable_task_planning=False`` falls back to a pure ReAct loop:
no built-in planning tools are exposed, no push-back fires, and the first
text response from the LLM wins.

Setting ``stream_steps=False`` disables intermediate-event streaming —
useful if the platform doesn't support it or for noise-free deployments.

The plan → act → observe loop
-----------------------------

On each iteration of the loop:

1. The body composes a system message from the configured base prompt +
   skills + workspace previews + the live task list, and calls
   ``llm.predict_with_tools(...)``.
2. If the LLM requested tool calls, each is dispatched to the matching
   :class:`~baf.reasoning.tool.Tool`. The result is appended to the
   conversation as the next observation. The loop continues.
3. If the LLM returned a final text answer:

   - If every task on the list is ``completed`` or ``skipped`` (or no
     tasks were ever added), the answer is sent via ``session.reply`` and
     the loop exits.
   - Otherwise the orchestrator pushes back with a system message
     enumerating the still-pending tasks. The loop continues.
4. If ``max_steps`` is exhausted without a final answer, the configured
   fallback message is sent.

Built-in task planning
----------------------

When ``enable_task_planning=True`` (the default) the body exposes three
*built-in* tools to the LLM, scoped to the current request:

- ``add_tasks(descriptions)`` — record a list of subtasks. Each gets an
  integer id.
- ``complete_task(task_id, result)`` — mark a task as completed (with a
  short summary of the outcome).
- ``skip_task(task_id, reason)`` — mark a task as skipped because it
  cannot or should not be completed (missing tool, missing data,
  ambiguous request, etc.).

These tools live in :mod:`baf.library.tool.task_tools` and are built fresh
per ``reasoning_body`` invocation, so each user request gets its own task
list. The system prompt nudges the LLM to plan complex requests up front
and check off tasks as it works through them.

ReasoningStep events
--------------------

Every observable event the loop produces — LLM tool calls, tool results,
task add/complete/skip, push-back, max-steps fallback, plus
``reasoning_started`` / ``reasoning_finished`` brackets that delimit the
trace — is shipped as a :class:`~baf.library.state.reasoning_state_library.ReasoningStep`:

.. code:: python

    @dataclass
    class ReasoningStep:
        kind: str         # one of ReasoningStepKind.*
        step: int         # loop iteration number (0-indexed)
        summary: str      # short human-readable description
        details: dict     # kind-specific structured payload

When ``stream_steps=True`` the body forwards each event to
``session.platform.reply_reasoning_step(...)`` if the platform implements
it. The :class:`~baf.platforms.websocket.websocket_platform.WebSocketPlatform`
does — its UI client can render a live "thinking" trace before the final
reply lands. Other platforms (Telegram, A2A, …) silently no-op.

In parallel, every task list mutation also fires a snapshot event via
``session.platform.reply_task_list_update(...)`` carrying the full current
list of tasks — handy for a UI panel that mirrors the agent's planning
state without having to reconstruct it from the step stream.

Persisted in the database
-------------------------

Reasoning step events and task list snapshots are persisted in a
dedicated ``reasoning_step`` table separate from the chat history (see
:mod:`baf.db.monitoring_db`). When a session is reloaded, the
:class:`~baf.platforms.websocket.websocket_platform.WebSocketPlatform`
fetches both the chat rows and the reasoning events and merges them by
timestamp, so the UI rebuilds the trace exactly as it streamed live.

API References
--------------

- new_reasoning_state(): :func:`baf.library.state.reasoning_state_library.new_reasoning_state`
- reasoning_body(): :func:`baf.library.state.reasoning_state_library.reasoning_body`
- ReasoningStep: :class:`baf.library.state.reasoning_state_library.ReasoningStep`
- ReasoningStepKind: :class:`baf.library.state.reasoning_state_library.ReasoningStepKind`
- TaskList: :class:`baf.library.state.reasoning_state_library.TaskList`
- Task: :class:`baf.library.state.reasoning_state_library.Task`
- build_task_tools(): :func:`baf.library.tool.task_tools.build_task_tools`
- LLM.predict_with_tools(): :meth:`baf.nlp.llm.llm.LLM.predict_with_tools`
- WebSocketPlatform.reply_reasoning_step(): :meth:`baf.platforms.websocket.websocket_platform.WebSocketPlatform.reply_reasoning_step`
- WebSocketPlatform.reply_task_list_update(): :meth:`baf.platforms.websocket.websocket_platform.WebSocketPlatform.reply_task_list_update`
