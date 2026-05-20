"""Universal workspace tools — factories that produce callables bound to a
specific :class:`~baf.core.agent.Agent`'s workspace registry.

Each factory returns a list of plain Python callables (not :class:`Tool`
instances) — the agent layer wraps them via :meth:`Agent.add_tool`. Two
families are exposed:

* :func:`build_workspace_read_tools` — ``list_directory``, ``read_file``.
  Always safe to register: read-only operations work on any workspace.
* :func:`build_workspace_write_tools` — ``write_file``, ``create_file``,
  ``delete_file``. The agent only registers these when at least one
  workspace has ``writable=True`` so the LLM never sees mutating tools when
  the entire setup is read-only. Per-workspace enforcement happens inside
  :class:`~baf.reasoning.workspace.Workspace` itself.

Both factories close over the agent so the tools dispatch to the right
workspace at call time via :meth:`Agent._resolve_workspace`. Splitting the
factories into "read" and "write" lets the agent enable each family
independently based on its workspace registry.
"""

from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from baf.core.agent import Agent


def build_workspace_read_tools(agent: 'Agent') -> list[Callable]:
    """Return the universal read-only workspace tools.

    Args:
        agent (Agent): the agent whose ``_workspaces`` registry the returned
            callables will dispatch into.

    Returns:
        list[Callable]: ``[list_directory, read_file]``. The function names
        match the tool names the LLM will see in the schema.
    """

    def list_directory(relative_path: str = ".", workspace: str = None) -> str:
        """List files and subfolders inside a registered workspace.

        Args:
            relative_path: a path relative to the workspace root. Use '.' for the root.
            workspace: the workspace name. Optional when only one workspace is registered.
        """
        ws = agent._resolve_workspace(workspace)
        return ws.list_directory(relative_path)

    def read_file(relative_path: str, workspace: str = None) -> str:
        """Read a file inside a registered workspace.

        Args:
            relative_path: a path relative to the workspace root.
            workspace: the workspace name. Optional when only one workspace is registered.
        """
        ws = agent._resolve_workspace(workspace)
        return ws.read_file(relative_path)

    return [list_directory, read_file]


def build_workspace_write_tools(agent: 'Agent') -> list[Callable]:
    """Return the universal mutating workspace tools.

    The tools dispatch to the chosen workspace's mutating methods, which
    raise :class:`~baf.reasoning.workspace.WorkspaceError` on read-only
    workspaces — so even if the LLM picks a read-only workspace from a
    mixed setup, the per-workspace check still applies.

    Args:
        agent (Agent): the agent whose ``_workspaces`` registry the returned
            callables will dispatch into.

    Returns:
        list[Callable]: ``[write_file, create_file, delete_file]``.
    """

    def write_file(relative_path: str, content: str, workspace: str = None) -> str:
        """Write content to a file inside a registered workspace, overwriting any existing content.

        Creates the file (and any missing parent directories) if it does not exist.
        Use `create_file` instead when the file should not yet exist. Fails on
        read-only workspaces.

        Args:
            relative_path: a path relative to the workspace root.
            content: the new file contents (UTF-8). Pass an empty string to truncate.
            workspace: the workspace name. Optional when only one workspace is registered.
        """
        ws = agent._resolve_workspace(workspace)
        return ws.write_file(relative_path, content)

    def create_file(relative_path: str, content: str = "", workspace: str = None) -> str:
        """Create a new file inside a registered workspace.

        Fails if the file already exists (use `write_file` to overwrite) or if the
        workspace is read-only. Missing parent directories are created.

        Args:
            relative_path: a path relative to the workspace root.
            content: the initial file contents (UTF-8). Defaults to empty.
            workspace: the workspace name. Optional when only one workspace is registered.
        """
        ws = agent._resolve_workspace(workspace)
        return ws.create_file(relative_path, content)

    def delete_file(relative_path: str, workspace: str = None) -> str:
        """Delete a file inside a registered workspace.

        Only files are deleted — directories are refused. Fails on read-only
        workspaces or when the target does not exist.

        Args:
            relative_path: a path relative to the workspace root.
            workspace: the workspace name. Optional when only one workspace is registered.
        """
        ws = agent._resolve_workspace(workspace)
        return ws.delete_file(relative_path)

    return [write_file, create_file, delete_file]
