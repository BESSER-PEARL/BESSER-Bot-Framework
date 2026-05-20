Tools
=====

A **Tool** is a Python callable the reasoning state can invoke during its
loop. BAF auto-introspects each function's signature, type hints and
docstring to build a JSON schema in the OpenAI / Anthropic function-calling
format — you don't write any schema by hand.

At runtime the LLM picks a tool, BAF validates the arguments against the
auto-generated schema, the function runs, and the stringified result goes
back to the LLM as the next observation.

How to use
----------

The simplest path is :meth:`~baf.core.agent.Agent.new_tool` — pass any
callable, BAF builds the wrapper and registers it on the agent:

.. code:: python

    from baf.core.agent import Agent

    agent = Agent('example_agent')

    def get_weather(city: str) -> str:
        """Get current weather for a city."""
        return f"sunny in {city}"

    agent.new_tool(get_weather)

Type hints and the docstring drive the schema:

- ``str`` / ``int`` / ``float`` / ``bool`` / ``list[X]`` / ``dict`` map to
  the equivalent JSON schema types.
- ``Optional[X]`` / ``X | None`` makes the parameter optional.
- The first non-empty line of the docstring becomes the tool description
  (overridable via the ``description=`` argument).
- A Google-style ``Args:`` block populates per-parameter descriptions.

.. note::

    Each tool is wrapped so that any exception it raises becomes an
    ``ERROR: <type>: <message>`` string fed back to the LLM. This way the
    model can read the failure and recover (retry with corrected
    arguments, skip the task, etc.) instead of breaking the loop.

Decorator form
--------------

For agents whose tools live in the same file, the ``@agent.tool``
decorator is syntactic sugar over :meth:`~baf.core.agent.Agent.new_tool`:

.. code:: python

    @agent.tool
    def echo(text: str) -> str:
        """Echo the user-supplied text back, unchanged."""
        return text

You can also pass ``name`` / ``description`` overrides:

.. code:: python

    @agent.tool(name='lookup_user', description='Find a user by id.')
    def _lookup(user_id: int) -> dict:
        ...

Bulk-load tools from a module or folder
---------------------------------------

When tools are organised in their own Python file (or folder of files),
:meth:`~baf.core.agent.Agent.load_tools` walks every public top-level
callable and registers each as a tool:

.. code:: python

    agent.load_tools('./tools.py')   # single module
    agent.load_tools('./tools')      # every .py file in the folder

Names starting with ``_`` and callables imported *from other modules* are
skipped, so importing helpers in your tools module does not pollute the
registry.

Pre-built Tool instances
------------------------

If you already hold a :class:`~baf.reasoning.tool.Tool` instance, register
it with :meth:`~baf.core.agent.Agent.add_tool` (mirroring how
:meth:`~baf.core.agent.Agent.add_intent` works for intents):

.. code:: python

    from baf.reasoning import Tool

    tool = Tool(get_weather, description='Get weather for a city.')
    agent.add_tool(tool)

Argument validation
-------------------

Before a tool is executed, BAF validates the LLM-supplied arguments
against the auto-generated schema:

- Unknown / missing required arguments fail with a clear
  ``ToolError`` message the LLM can read.
- Light coercion is applied: ``int`` accepts strings of digits,
  ``float`` accepts ``int`` and parseable strings, ``bool`` accepts the
  case-insensitive strings ``"true"`` / ``"false"``.

Built-in predefined tools
-------------------------

BAF ships with two families of predefined tools that the reasoning state
uses out of the box. They live under :mod:`baf.library.tool` and are
registered automatically when you set up the relevant primitives:

- **Workspace tools** (:doc:`workspaces` page) — ``list_directory``,
  ``read_file``, and (when at least one workspace is writable)
  ``write_file``, ``create_file``, ``delete_file``. Registered the moment
  the first workspace is added to the agent.
- **Task-planning tools** (:doc:`reasoning_state` page) — ``add_tasks``,
  ``complete_task``, ``skip_task``. Per-invocation tools created fresh
  for every reasoning loop so each user request has its own task list.

API References
--------------

- Agent: :class:`baf.core.agent.Agent`
- Agent.new_tool(): :meth:`baf.core.agent.Agent.new_tool`
- Agent.add_tool(): :meth:`baf.core.agent.Agent.add_tool`
- Agent.load_tools(): :meth:`baf.core.agent.Agent.load_tools`
- Agent.tool() decorator: :meth:`baf.core.agent.Agent.tool`
- Tool: :class:`baf.reasoning.tool.Tool`
- ToolError: :class:`baf.reasoning.tool.ToolError`
