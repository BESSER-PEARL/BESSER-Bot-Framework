Reasoning
=========

The reasoning extension brings modern *autonomous-agent* patterns to BAF on
top of the existing state machine: an agent state can run an LLM-driven
**plan → act → observe** loop instead of a hand-written body. Inside that
loop the LLM has access to a small set of plug-in primitives the developer
declares once on the agent.

- **Tools** — Python callables the LLM can invoke (auto-introspected to
  build the JSON schema OpenAI / Anthropic function-calling expects).
- **Skills** — markdown files (or strings) acting as named system prompts —
  playbooks, personas, policies — that get spliced into the LLM's context.
- **Workspaces** — filesystem paths the LLM can browse and (optionally)
  modify on demand, just like Claude Code browses a repository.
- **Reasoning state** — the predefined state body that wires it all
  together. Manages a request-scoped task list, calls the LLM in a loop,
  dispatches tool calls, streams every step to the UI, and stops only once
  the LLM produces a final answer with all tasks resolved.

The result: a developer who wants a "modern agent" instantiates an
:class:`~baf.core.agent.Agent`, attaches some tools / skills / workspaces,
and registers a single predefined state — same DSL, new capability.

.. code:: python

    from baf.core.agent import Agent
    from baf.library.state import new_reasoning_state
    from baf.nlp.llm.llm_openai_api import LLMOpenAI

    agent = Agent('my_agent')
    agent.load_properties('config.yaml')
    agent.use_websocket_platform(use_ui=True)

    gpt = LLMOpenAI(agent=agent, name='gpt-4o-mini', parameters={})

    # Skills, tools, workspaces — see the dedicated pages below
    agent.load_skills('./skills')
    agent.load_tools('./tools.py')
    agent.new_workspace('./docs', name='product_docs',
                        description='Markdown product docs.')

    # Single predefined state that runs the LLM-driven loop
    reasoning_state = new_reasoning_state(agent, llm=gpt)
    reasoning_state.when_event().go_to(reasoning_state)

    if __name__ == '__main__':
        agent.run()

You can also check the :doc:`../examples/reasoning_agent` for a complete
runnable example.

Table of contents
-----------------

.. toctree::
   :maxdepth: 1

   reasoning/tools
   reasoning/skills
   reasoning/workspaces
   reasoning/reasoning_state

API References
--------------

- Agent: :class:`baf.core.agent.Agent`
- Agent.new_tool(): :meth:`baf.core.agent.Agent.new_tool`
- Agent.new_skill(): :meth:`baf.core.agent.Agent.new_skill`
- Agent.new_workspace(): :meth:`baf.core.agent.Agent.new_workspace`
- new_reasoning_state(): :func:`baf.library.state.reasoning_state_library.new_reasoning_state`
