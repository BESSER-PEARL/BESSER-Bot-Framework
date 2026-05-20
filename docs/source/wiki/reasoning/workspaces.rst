Workspaces
==========

A **Workspace** is a filesystem path the reasoning state can browse and
(optionally) modify on demand — the same way Claude Code browses a
repository. Instead of pre-indexing documents into a vector store, the LLM
explores the directory structure, reads files relevant to the current
question, and pulls only what it needs into context.

This is the recommended default for "knowledge" content: more transparent
than RAG (the agent reasons about *what* to read), avoids stale embeddings,
needs no vector store, and works on any folder you point at.

.. note::

    RAG is still available — and complementary — for very large knowledge
    bases where browsing is impractical. See :doc:`../nlp/rag`. You can
    expose a RAG instance as just another tool via
    :meth:`~baf.core.agent.Agent.add_tool` if you want both available.

How to use
----------

The most common path is :meth:`~baf.core.agent.Agent.new_workspace`:

.. code:: python

    from baf.core.agent import Agent

    agent = Agent('example_agent')

    agent.new_workspace(
        './docs',
        name='product_docs',
        description='Markdown product docs and API references.',
    )

The first call to :meth:`~baf.core.agent.Agent.new_workspace` (or
:meth:`~baf.core.agent.Agent.add_workspace` for a pre-built instance)
also registers the universal browsing tools on the agent — so the LLM
sees them in its tool schema:

- ``list_directory(relative_path='.', workspace=None)``
- ``read_file(relative_path, workspace=None)``

The ``workspace`` argument selects which workspace to operate on; it can
be omitted when only one workspace is registered. All paths are resolved
relative to the workspace root and any attempt to escape it (``..``,
absolute paths) is rejected with a clear error the LLM can read.

Read-only vs writable workspaces
--------------------------------

By default workspaces are *writable*: the reasoning state can not only
browse them but also modify them. Pass ``writable=False`` for an
explicitly read-only workspace:

.. code:: python

    # Read-only knowledge folder
    agent.new_workspace(
        './docs',
        name='product_docs',
        description='Reference docs the agent can read.',
        writable=False,
    )

    # Writable scratchpad / output folder
    agent.new_workspace(
        './output',
        name='output',
        description='Folder where the agent saves generated reports.',
        writable=True,
    )

Three additional universal tools — ``write_file``, ``create_file``,
``delete_file`` — are registered on the agent **only if at least one
registered workspace has** ``writable=True``. A read-only-only setup
never exposes mutating tools to the LLM in the first place.

Per-workspace enforcement is independent of the registration gate: even
in a mixed setup, calling ``write_file(workspace='product_docs')`` on a
read-only workspace returns a clear ``ERROR: ... is read-only`` string
the LLM can read, so the model can recover (route the write to the
output workspace, or skip the task).

The mutating tools:

- ``write_file(relative_path, content, workspace=None)`` — overwrites or
  creates the file (auto-creates missing parent directories).
- ``create_file(relative_path, content='', workspace=None)`` — fails if
  the path already exists.
- ``delete_file(relative_path, workspace=None)`` — file-only deletion;
  directories are refused.

How workspaces surface to the LLM
---------------------------------

The :doc:`reasoning_state` body composes a system block describing every
registered workspace at the start of every loop iteration. Each block
includes:

- The workspace's ``name`` and ``description``.
- The mode (``writable`` / ``read-only``).
- The absolute root path.
- A *top-level directory listing preview* so the LLM can see file names
  immediately, without spending a tool call on ``list_directory``.

The preview is a powerful nudge: the LLM sees ``[FILE] inception.md`` in
the system message and naturally moves to ``read_file('inception.md')``
when the user asks about Inception, instead of answering from training
data.

Pre-built Workspace instances
-----------------------------

If you already hold a :class:`~baf.reasoning.workspace.Workspace`,
register it via :meth:`~baf.core.agent.Agent.add_workspace`:

.. code:: python

    from baf.reasoning import Workspace

    ws = Workspace('./docs', name='product_docs',
                   description='...', writable=False)
    agent.add_workspace(ws)

API References
--------------

- Agent: :class:`baf.core.agent.Agent`
- Agent.new_workspace(): :meth:`baf.core.agent.Agent.new_workspace`
- Agent.add_workspace(): :meth:`baf.core.agent.Agent.add_workspace`
- Workspace: :class:`baf.reasoning.workspace.Workspace`
- WorkspaceError: :class:`baf.reasoning.workspace.WorkspaceError`
- Built-in workspace tools: :func:`baf.library.tool.workspace_tools.build_workspace_read_tools`,
  :func:`baf.library.tool.workspace_tools.build_workspace_write_tools`
