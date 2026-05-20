from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

from baf.exceptions.logger import logger


# --- Helpers --------------------------------------------------------------- #


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)
_KV_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_\-]*)\s*:\s*(.*)$")


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse a leading ``--- ... ---`` frontmatter block.

    Frontmatter is parsed as plain ``key: value`` lines (one per line). No YAML
    dependency is used. If the block is malformed (e.g., only an opening
    delimiter, or no recognisable key/value pairs), a warning is logged and the
    full content is returned untouched as the body.

    Args:
        content (str): the raw markdown text.

    Returns:
        tuple[dict, str]: a ``(metadata, body)`` pair. ``metadata`` is empty if
        no frontmatter was found.
    """
    if not content.startswith("---"):
        return {}, content

    match = _FRONTMATTER_RE.match(content)
    if not match:
        logger.warning("[Skill] Malformed frontmatter (missing closing '---'); treating whole content as body")
        return {}, content

    block = match.group(1)
    metadata: dict = {}
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        kv = _KV_RE.match(line)
        if not kv:
            logger.warning(f"[Skill] Ignoring malformed frontmatter line: {raw_line!r}")
            continue
        key, value = kv.group(1).strip(), kv.group(2).strip()
        # Strip optional surrounding quotes.
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        metadata[key] = value

    body = content[match.end():]
    return metadata, body


def _extract_h1_title(body: str) -> Optional[str]:
    """Return the text of the first H1 ('# Title') in ``body``, or None."""
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("# "):
            return stripped[2:].strip() or None
        # First non-empty line is not an H1 — give up.
        return None
    return None


# --- Skill ----------------------------------------------------------------- #


class Skill:
    """A named, markdown-based playbook the reasoning loop can inject as system context.

    A Skill is a small, composable system prompt: a ``name``, an optional
    ``description``, and the markdown ``content`` to splice into the LLM's
    system message at run time. Skills can be loaded from a string, from a
    single ``.md`` file, or from a folder of ``.md`` files.

    Frontmatter (an optional ``---`` block at the top of the file) is parsed as
    plain ``key: value`` lines. Recognised keys: ``name``, ``description``.

    Args:
        content (str): the markdown text of the skill, optionally prefixed by a
            ``--- ... ---`` frontmatter block.
        name (str): the skill name. If not provided, falls back to
            ``frontmatter['name']``, then to the first H1 in the body.
        description (str): a short description. If not provided, falls back to
            ``frontmatter['description']``.

    Attributes:
        name (str): the skill name.
        description (Optional[str]): the optional description.
        content (str): the markdown body, with any frontmatter stripped.
    """

    def __init__(self, content: str, name: str = None, description: str = None):
        if content is None:
            raise ValueError("Skill content cannot be None")

        metadata, body = _parse_frontmatter(content)

        resolved_name = name or metadata.get("name") or _extract_h1_title(body)
        if not resolved_name:
            raise ValueError("Skill needs a name")

        resolved_description = description or metadata.get("description")

        self.name: str = resolved_name
        self.description: Optional[str] = resolved_description
        self.content: str = body.strip()

    @classmethod
    def from_file(cls, path: str) -> "Skill":
        """Load a Skill from a markdown file.

        If neither frontmatter nor a leading H1 supplies a ``name``, the file's
        stem (filename without extension) is used.

        Args:
            path (str): path to a ``.md`` file.

        Returns:
            Skill: the loaded skill.
        """
        file_path = Path(path)
        text = file_path.read_text(encoding="utf-8")
        try:
            return cls(text)
        except ValueError:
            # Fall back to using the filename stem as the name.
            return cls(text, name=file_path.stem)

    @classmethod
    def from_folder(cls, folder: str) -> list["Skill"]:
        """Load every ``*.md`` file in ``folder`` (non-recursive) as a Skill.

        Args:
            folder (str): path to a folder containing markdown files.

        Returns:
            list[Skill]: the loaded skills, sorted by filename.
        """
        folder_path = Path(folder)
        if not folder_path.is_dir():
            raise ValueError(f"Skill folder does not exist or is not a directory: {folder}")

        md_files = sorted(p for p in folder_path.iterdir() if p.is_file() and p.suffix.lower() == ".md")
        skills: list[Skill] = []
        for md in md_files:
            try:
                skills.append(cls.from_file(str(md)))
            except Exception as e:
                logger.warning(f"[Skill] Failed to load {md}: {e}")
        return skills

    def to_prompt(self) -> str:
        """Render the skill as a chunk of system-prompt markdown.

        Returns:
            str: ``"## Skill: {name}\\n{description?}\\n\\n{content}"`` — the
            description line is omitted when no description is set.
        """
        header = f"## Skill: {self.name}"
        if self.description:
            return f"{header}\n{self.description}\n\n{self.content}"
        return f"{header}\n\n{self.content}"
