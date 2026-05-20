from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from baf.exceptions.logger import logger


class WorkspaceError(Exception):
    """Raised when a Workspace operation fails (path escape, missing file, etc.)."""
    pass


# --- Helpers --------------------------------------------------------------- #


def _is_within(parent: Path, child: Path) -> bool:
    """Return True if ``child`` is at or below ``parent`` on the filesystem.

    Uses :py:meth:`pathlib.Path.is_relative_to` when available (Python 3.9+),
    and falls back to :py:func:`os.path.commonpath` otherwise so the helper
    keeps working on older interpreters.
    """
    is_relative_to = getattr(Path, "is_relative_to", None)
    if is_relative_to is not None:
        try:
            return child.is_relative_to(parent)  # type: ignore[attr-defined]
        except ValueError:
            return False
    try:
        return os.path.commonpath([str(parent), str(child)]) == str(parent)
    except ValueError:
        return False


# --- Workspace ------------------------------------------------------------- #


class Workspace:
    """A filesystem path the reasoning loop can browse on demand.

    A Workspace is a pure data + behaviour holder: it stores a sandboxed root
    path and exposes ``list_directory`` and ``read_file`` methods that the
    reasoning loop invokes through the agent's *universal* ``list_directory``
    and ``read_file`` tools (registered automatically by
    :meth:`baf.core.agent.Agent.add_workspace` the first time a workspace is
    added). Tools take a ``workspace`` argument that selects which workspace
    to use, and may omit it when only one workspace is registered.

    All paths are resolved relative to ``root`` and any attempt to escape the
    workspace (via ``..`` or absolute paths) is rejected with a
    :class:`WorkspaceError`.

    Args:
        path (str): the workspace root path. Must exist and be a directory.
        name (str): the workspace identifier the LLM passes as the
            ``workspace`` tool argument. Must be unique within the agent.
        description (str): a short human-readable explanation of *what* the
            workspace contains. Surfaced to the LLM in the system prompt so it
            knows when this workspace is relevant — without a description the
            LLM only sees the name and root path and may not realise it should
            browse the workspace at all.
        writable (bool): if False, the mutating operations (``write_file``,
            ``create_file``, ``delete_file``) raise ``WorkspaceError`` and the
            corresponding universal tools are not registered on the agent
            unless at least one *other* workspace is writable. Defaults to
            True.
        max_read_bytes (int): the maximum number of bytes ``read_file`` will
            return; the rest is replaced with a clear truncation marker.
            Defaults to ``200_000``.

    Attributes:
        root (Path): the resolved absolute path to the workspace root.
        name (str): the workspace identifier.
        description (Optional[str]): the optional human-readable description.
        writable (bool): whether mutating operations are allowed.
        max_read_bytes (int): cap on ``read_file`` output.
    """

    def __init__(self, path: str, name: str = "workspace",
                 description: str = None, writable: bool = True,
                 max_read_bytes: int = 200_000):
        resolved = Path(path).resolve()
        if not resolved.exists():
            raise WorkspaceError(f"Workspace path does not exist: {resolved}")
        if not resolved.is_dir():
            raise WorkspaceError(f"Workspace path is not a directory: {resolved}")

        self.root: Path = resolved
        self.name: str = name
        self.description: Optional[str] = description
        self.writable: bool = writable
        self.max_read_bytes: int = max_read_bytes

    def _require_writable(self) -> None:
        """Guard for mutating operations. Raises if the workspace is read-only."""
        if not self.writable:
            raise WorkspaceError(
                f"Workspace '{self.name}' is read-only; cannot modify files."
            )

    def top_level_listing(self) -> str:
        """Return a one-line-per-entry preview of the workspace root.

        Used to hint the LLM at what's inside without forcing a separate
        ``list_directory`` call. Returns ``''`` if the directory is empty or
        unreadable.
        """
        try:
            entries = sorted(self.root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError as e:
            logger.warning(f"[Workspace] Could not preview root of '{self.name}': {e}")
            return ""
        lines = []
        for entry in entries:
            prefix = "[DIR] " if entry.is_dir() else "[FILE] "
            lines.append(f"{prefix}{entry.name}")
        return "\n".join(lines)

    # -- Public API ----------------------------------------------------------

    def list_directory(self, relative_path: str = ".") -> str:
        """List files and subfolders inside the workspace at ``relative_path``.

        Args:
            relative_path (str): a path relative to the workspace root. Defaults
                to ``'.'`` (the root itself).

        Returns:
            str: one entry per line, prefixed by ``'[DIR] '`` or ``'[FILE] '``.

        Raises:
            WorkspaceError: if the resolved path escapes the workspace root or
                does not point at a directory.
        """
        target = self._safe_resolve(relative_path)
        if not target.is_dir():
            raise WorkspaceError(f"Not a directory: {relative_path}")

        entries = []
        for entry in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            prefix = "[DIR] " if entry.is_dir() else "[FILE] "
            entries.append(f"{prefix}{entry.name}")

        if not entries:
            return f"(empty directory: {relative_path})"
        return "\n".join(entries)

    def read_file(self, relative_path: str) -> str:
        """Read a file inside the workspace.

        Output is truncated at ``self.max_read_bytes`` with a clear marker so
        the LLM knows it can ask for a follow-up read.

        Args:
            relative_path (str): a path relative to the workspace root.

        Returns:
            str: the file's textual content (possibly truncated).

        Raises:
            WorkspaceError: if the path escapes the workspace root or the
                target is not a file.
        """
        target = self._safe_resolve(relative_path)
        if not target.is_file():
            raise WorkspaceError(f"Not a file: {relative_path}")

        try:
            data = target.read_bytes()
        except OSError as e:
            raise WorkspaceError(f"Could not read file '{relative_path}': {e}") from e

        total_bytes = len(data)
        truncated = False
        if total_bytes > self.max_read_bytes:
            data = data[: self.max_read_bytes]
            truncated = True

        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("utf-8", errors="replace")

        if truncated:
            text = f"{text}\n... [truncated, file is {total_bytes} bytes total]"
        return text

    def write_file(self, relative_path: str, content: str) -> str:
        """Write ``content`` to a file inside the workspace, overwriting any
        existing content.

        Creates the file (and any missing parent directories) if it does not
        exist. Use :meth:`create_file` instead when you want the call to fail
        if the file already exists.

        Args:
            relative_path (str): a path relative to the workspace root.
            content (str): the new contents of the file (UTF-8). May be empty,
                which truncates an existing file.

        Returns:
            str: a short confirmation including the byte count written.

        Raises:
            WorkspaceError: if the workspace is read-only, the path escapes
                the workspace root, or the target points at an existing
                directory.
        """
        self._require_writable()
        target = self._safe_resolve(relative_path)
        if target.exists() and target.is_dir():
            raise WorkspaceError(f"Cannot write file: '{relative_path}' is a directory")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        except OSError as e:
            raise WorkspaceError(f"Could not write file '{relative_path}': {e}") from e
        return f"Wrote {len(content.encode('utf-8'))} bytes to '{relative_path}'."

    def create_file(self, relative_path: str, content: str = "") -> str:
        """Create a new file inside the workspace with the given content.

        Fails if the target path already exists (use :meth:`write_file` to
        overwrite instead). Missing parent directories are created.

        Args:
            relative_path (str): a path relative to the workspace root.
            content (str): the initial contents of the file (UTF-8). Defaults
                to an empty string for an empty file.

        Returns:
            str: a short confirmation including the byte count written.

        Raises:
            WorkspaceError: if the workspace is read-only, the path escapes
                the workspace root, or the target already exists.
        """
        self._require_writable()
        target = self._safe_resolve(relative_path)
        if target.exists():
            kind = "directory" if target.is_dir() else "file"
            raise WorkspaceError(
                f"Cannot create '{relative_path}': {kind} already exists "
                f"(use write_file to overwrite)"
            )
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        except OSError as e:
            raise WorkspaceError(f"Could not create file '{relative_path}': {e}") from e
        return f"Created '{relative_path}' ({len(content.encode('utf-8'))} bytes)."

    def delete_file(self, relative_path: str) -> str:
        """Delete a file inside the workspace.

        Only deletes regular files — directories are refused (deletion
        cascades are intentionally not exposed). Fails if the target does
        not exist so the LLM gets explicit feedback rather than a silent
        no-op.

        Args:
            relative_path (str): a path relative to the workspace root.

        Returns:
            str: a short confirmation message.

        Raises:
            WorkspaceError: if the workspace is read-only, the path escapes
                the workspace root, the target does not exist, or the target
                is a directory.
        """
        self._require_writable()
        target = self._safe_resolve(relative_path)
        if not target.exists():
            raise WorkspaceError(f"Cannot delete: '{relative_path}' does not exist")
        if target.is_dir():
            raise WorkspaceError(
                f"Cannot delete: '{relative_path}' is a directory "
                f"(only file deletion is supported)"
            )
        try:
            target.unlink()
        except OSError as e:
            raise WorkspaceError(f"Could not delete file '{relative_path}': {e}") from e
        return f"Deleted '{relative_path}'."

    # -- Internals -----------------------------------------------------------

    def _safe_resolve(self, relative_path: str) -> Path:
        """Resolve ``relative_path`` and guard against workspace escape.

        Args:
            relative_path (str): the user-supplied (LLM-supplied) path.

        Returns:
            Path: the absolute, resolved path inside the workspace.

        Raises:
            WorkspaceError: if the resolved path escapes the workspace root.
        """
        if relative_path is None:
            relative_path = "."
        candidate = (self.root / relative_path).resolve()
        if not _is_within(self.root, candidate):
            raise WorkspaceError("Path escapes workspace")
        return candidate

