Skills
======

A **Skill** is a named, markdown-based playbook that gets injected into the
reasoning state's system prompt. Think of it as a small, composable system
message — a persona, a policy, a domain playbook — kept in plain markdown
so non-developers can write and review skills without touching Python.

Skills are pure data: they declare *how* the agent should behave for a
given topic. The actual control flow (when to call which tool, when to
plan, when to answer) stays inside the :doc:`reasoning_state` body.

How to use
----------

The most common case is loading a folder of ``.md`` files at agent build
time. Each file becomes one skill:

.. code:: python

    from baf.core.agent import Agent

    agent = Agent('example_agent')
    agent.load_skills('./skills')   # every .md in the folder

Files are parsed in alphabetical order. The skill's name comes from
(in priority order):

1. A ``name:`` field in the YAML-style frontmatter (see below).
2. The first ``# Heading`` line in the body.
3. The filename stem.

You can also add a single skill from a file path or from a literal
markdown string with :meth:`~baf.core.agent.Agent.new_skill`:

.. code:: python

    # From a file
    agent.new_skill('./skills/refund_policy.md')

    # From a string — perfect for one-off behavioural tweaks
    agent.new_skill(
        "Always greet the user by name when they introduce themselves.",
        name='GreetByName',
    )

If you already hold a :class:`~baf.reasoning.skill.Skill` instance,
:meth:`~baf.core.agent.Agent.add_skill` registers it directly (mirroring
:meth:`~baf.core.agent.Agent.add_intent`):

.. code:: python

    from baf.reasoning import Skill

    skill = Skill('Be concise and never speculate.', name='terse')
    agent.add_skill(skill)

.. note::

    Why files? Zero learning curve, easy to version-control, no Python
    wiring needed for non-developers writing skills. A markdown editor is
    enough.

Skill file format
-----------------

A skill file is just markdown. An optional YAML-style frontmatter block at
the top of the file lets you declare metadata explicitly:

.. code:: markdown

    ---
    name: ConciseAssistant
    description: Behavioural guidelines for short, accurate replies.
    ---

    # ConciseAssistant

    You are a friendly but extremely concise assistant. Keep replies under
    three sentences whenever possible. When a tool is available that can
    answer the user's question, prefer calling the tool over guessing.

Recognised frontmatter keys: ``name``, ``description``. Anything below the
closing ``---`` is the skill body.

Frontmatter is optional: a plain markdown file with no frontmatter and no
``# Heading`` will use the filename stem as the skill name and have no
description.

How skills surface to the LLM
-----------------------------

The :doc:`reasoning_state` body composes a system message at the start of
every loop iteration. Each registered skill contributes a section formatted
roughly as::

    ## Skill: <skill_name>
    <description, if any>

    <markdown body>

By default *all* skills are injected into every turn. For agents with many
skills, the recommended evolution is an LLM-based skill router that picks
only the relevant ones — this is currently a future enhancement; today
"inject all" is the rule.

API References
--------------

- Agent: :class:`baf.core.agent.Agent`
- Agent.new_skill(): :meth:`baf.core.agent.Agent.new_skill`
- Agent.add_skill(): :meth:`baf.core.agent.Agent.add_skill`
- Agent.load_skills(): :meth:`baf.core.agent.Agent.load_skills`
- Skill: :class:`baf.reasoning.skill.Skill`
- Skill.from_file(): :meth:`baf.reasoning.skill.Skill.from_file`
- Skill.from_folder(): :meth:`baf.reasoning.skill.Skill.from_folder`
