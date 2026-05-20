"""Predefined tools that ship with BAF and can be registered on any agent.

Currently:

* :mod:`baf.library.tool.workspace_tools` — the universal ``list_directory``,
  ``read_file``, ``write_file``, ``create_file``, ``delete_file`` tools that
  the predefined reasoning state uses to browse and modify any workspace
  registered on the agent.
* :mod:`baf.library.tool.task_tools` — the request-scoped ``add_tasks``,
  ``complete_task``, ``skip_task`` planning tools used by the predefined
  reasoning state to track multi-step work.

Future predefined tool families (e.g. RAG, web fetch, MCP wrappers) will
land here too.
"""

from baf.library.tool.task_tools import build_task_tools
from baf.library.tool.workspace_tools import (
    build_workspace_read_tools,
    build_workspace_write_tools,
)

__all__ = [
    "build_task_tools",
    "build_workspace_read_tools",
    "build_workspace_write_tools",
]
