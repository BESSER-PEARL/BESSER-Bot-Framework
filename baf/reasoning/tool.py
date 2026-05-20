from __future__ import annotations

import inspect
import json
import re
import typing
from typing import Any, Callable, Optional, Union, get_args, get_origin, get_type_hints

from baf.exceptions.logger import logger


class ToolError(Exception):
    """Raised when a Tool's argument validation fails.

    The message is intended to be readable by an LLM so it can recover and retry
    with corrected arguments on the next reasoning step.
    """
    pass


# --- Helpers --------------------------------------------------------------- #


def _is_optional(annotation: Any) -> bool:
    """Return True if the annotation is an `Optional[X]` / `X | None` form.

    Args:
        annotation: a type annotation as seen by ``typing.get_type_hints``.

    Returns:
        bool: True if ``None`` is one of the union members, False otherwise.
    """
    origin = get_origin(annotation)
    if origin is Union or origin is getattr(typing, "UnionType", None):
        return type(None) in get_args(annotation)
    return False


def _strip_optional(annotation: Any) -> Any:
    """Return the underlying annotation of an `Optional[X]` / `X | None`.

    If the annotation is not optional, it is returned unchanged.
    """
    if not _is_optional(annotation):
        return annotation
    non_none = [a for a in get_args(annotation) if a is not type(None)]
    if len(non_none) == 1:
        return non_none[0]
    # Fallback for Union[A, B, None] — treat as the first non-None member.
    return non_none[0] if non_none else annotation


def _annotation_to_schema(annotation: Any, param_name: str = "") -> dict:
    """Map a Python annotation to a minimal JSONSchema property.

    Args:
        annotation: the annotation to translate.
        param_name (str): the parameter name, only used for diagnostic logging.

    Returns:
        dict: the JSONSchema property describing the annotation.
    """
    annotation = _strip_optional(annotation)

    if annotation is inspect.Parameter.empty or annotation is None:
        logger.debug(f"[Tool] No type annotation for parameter '{param_name}', falling back to string")
        return {"type": "string"}

    if annotation is str:
        return {"type": "string"}
    if annotation is bool:
        return {"type": "boolean"}
    if annotation is int:
        return {"type": "integer"}
    if annotation is float:
        return {"type": "number"}

    origin = get_origin(annotation)

    if annotation is list or origin is list or origin is typing.List:
        args = get_args(annotation)
        items_schema = _annotation_to_schema(args[0], param_name) if args else {"type": "string"}
        return {"type": "array", "items": items_schema}

    if annotation is dict or origin is dict or origin is typing.Dict:
        return {"type": "object"}

    logger.debug(
        f"[Tool] Unsupported annotation {annotation!r} for parameter '{param_name}', falling back to string"
    )
    return {"type": "string"}


# Match lines like: `arg_name (type): description` or `arg_name: description`.
_ARG_LINE_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:\([^)]*\))?\s*:\s*(.+)$")


def _parse_arg_descriptions(docstring: Optional[str]) -> dict[str, str]:
    """Best-effort extraction of per-argument descriptions from a docstring.

    Recognises Google-style ``Args:`` blocks and bare ``Arguments:`` / ``Parameters:``
    blocks. Lines that do not match the simple ``name (type?): description`` pattern
    are ignored.

    Args:
        docstring (Optional[str]): the function docstring, may be None.

    Returns:
        dict[str, str]: a mapping ``arg_name -> description``.
    """
    if not docstring:
        return {}

    lines = docstring.splitlines()
    in_block = False
    descriptions: dict[str, str] = {}
    last_arg: Optional[str] = None

    for raw in lines:
        stripped = raw.strip()
        if re.match(r"^(Args|Arguments|Parameters)\s*:\s*$", stripped):
            in_block = True
            last_arg = None
            continue
        if in_block:
            # Stop the block on a new section header (e.g., Returns:, Raises:, Example:).
            if re.match(r"^[A-Z][A-Za-z]+\s*:\s*$", stripped) and not _ARG_LINE_RE.match(stripped):
                in_block = False
                last_arg = None
                continue
            if not stripped:
                last_arg = None
                continue
            match = _ARG_LINE_RE.match(raw)
            if match:
                name, desc = match.group(1), match.group(2).strip()
                descriptions[name] = desc
                last_arg = name
            elif last_arg is not None:
                # Continuation line of the previous argument's description.
                descriptions[last_arg] = (descriptions[last_arg] + " " + stripped).strip()

    return descriptions


def _first_non_empty_line(text: Optional[str]) -> str:
    """Return the first non-empty stripped line of ``text`` (or empty string)."""
    if not text:
        return ""
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""


def _build_schema(fn: Callable) -> dict:
    """Introspect ``fn`` and build a JSONSchema ``parameters`` object.

    The returned dict has the shape::

        {"type": "object", "properties": {...}, "required": [...]}

    Args:
        fn (Callable): the function to introspect.

    Returns:
        dict: the JSONSchema parameters object.
    """
    sig = inspect.signature(fn)
    try:
        hints = get_type_hints(fn)
    except Exception as e:  # pragma: no cover - defensive: forward refs that can't resolve
        logger.debug(f"[Tool] get_type_hints failed for {fn!r}: {e}")
        hints = {}

    arg_docs = _parse_arg_descriptions(inspect.getdoc(fn))

    properties: dict[str, dict] = {}
    required: list[str] = []

    for name, param in sig.parameters.items():
        if name == "self":
            continue
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            # *args / **kwargs aren't expressible in a simple JSONSchema — skip.
            continue

        annotation = hints.get(name, param.annotation)
        prop = _annotation_to_schema(annotation, param_name=name)
        if name in arg_docs:
            prop["description"] = arg_docs[name]
        properties[name] = prop

        if param.default is inspect.Parameter.empty and not _is_optional(annotation):
            required.append(name)

    return {"type": "object", "properties": properties, "required": required}


# --- Validation helpers ---------------------------------------------------- #


def _coerce_value(value: Any, json_type: str, arg_name: str) -> Any:
    """Validate and lightly coerce ``value`` to the expected JSONSchema ``json_type``.

    Allowed coercions:
        * integer accepts strings of digits (optionally signed).
        * number accepts ints and strings parseable as floats.
        * boolean accepts the strings "true"/"false" (case-insensitive).

    Raises:
        ToolError: if the value cannot be safely coerced.
    """
    if json_type == "string":
        if isinstance(value, str):
            return value
        raise ToolError(f"Invalid argument '{arg_name}': expected string, got {value!r}")

    if json_type == "integer":
        if isinstance(value, bool):  # bool is a subclass of int — reject.
            raise ToolError(f"Invalid argument '{arg_name}': expected integer, got {value!r}")
        if isinstance(value, int):
            return value
        if isinstance(value, str) and re.fullmatch(r"[+-]?\d+", value.strip()):
            return int(value)
        raise ToolError(f"Invalid argument '{arg_name}': expected integer, got {value!r}")

    if json_type == "number":
        if isinstance(value, bool):
            raise ToolError(f"Invalid argument '{arg_name}': expected number, got {value!r}")
        if isinstance(value, (int, float)):
            return float(value) if isinstance(value, int) else value
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                pass
        raise ToolError(f"Invalid argument '{arg_name}': expected number, got {value!r}")

    if json_type == "boolean":
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.strip().lower() in ("true", "false"):
            return value.strip().lower() == "true"
        raise ToolError(f"Invalid argument '{arg_name}': expected boolean, got {value!r}")

    if json_type == "array":
        if isinstance(value, list):
            return value
        raise ToolError(f"Invalid argument '{arg_name}': expected array, got {value!r}")

    if json_type == "object":
        if isinstance(value, dict):
            return value
        raise ToolError(f"Invalid argument '{arg_name}': expected object, got {value!r}")

    # Unknown JSON type — accept as-is.
    return value


# --- Tool ------------------------------------------------------------------ #


class Tool:
    """Wraps a Python callable so a reasoning loop can invoke it via JSON-schema args.

    The wrapper auto-introspects the callable's signature, type hints and docstring
    to build a JSON schema in OpenAI function-calling format, validates LLM-supplied
    arguments before invocation, and converts the result (and any raised exception)
    to a string the LLM can read.

    Args:
        fn (Callable): the Python callable to expose as a tool.
        name (str): the public tool name. Defaults to ``fn.__name__``.
        description (str): a short description shown to the LLM. Defaults to the
            first non-empty line of ``fn.__doc__``.

    Attributes:
        fn (Callable): the wrapped callable.
        name (str): the public tool name.
        description (str): the human-readable description.
        schema (dict): the JSONSchema ``parameters`` object describing ``fn``'s
            signature.
    """

    def __init__(self, fn: Callable, name: str = None, description: str = None):
        if not callable(fn):
            raise TypeError(f"Tool requires a callable, got {type(fn).__name__}")
        self.fn: Callable = fn
        self.name: str = name or getattr(fn, "__name__", "tool")
        self.description: str = description or _first_non_empty_line(inspect.getdoc(fn)) or self.name
        self.schema: dict = _build_schema(fn)

    @property
    def openai_schema(self) -> dict:
        """Return the OpenAI function-calling schema for this tool.

        Returns:
            dict: a dict of the shape
            ``{"type": "function", "function": {"name", "description", "parameters"}}``.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.schema,
            },
        }

    def validate_args(self, args: dict) -> dict:
        """Validate and lightly coerce ``args`` against ``self.schema``.

        Args:
            args (dict): the arguments supplied by the LLM.

        Returns:
            dict: the validated (possibly coerced) arguments, ready to be passed
            as ``**kwargs`` to ``self.fn``.

        Raises:
            ToolError: if an argument is missing, unknown, or has the wrong type.
        """
        if args is None:
            args = {}
        if not isinstance(args, dict):
            raise ToolError(f"Tool '{self.name}' expects a dict of arguments, got {type(args).__name__}")

        properties: dict = self.schema.get("properties", {})
        required: list = self.schema.get("required", [])

        # Reject unknown args first so the LLM sees a clear error.
        unknown = [k for k in args.keys() if k not in properties]
        if unknown:
            raise ToolError(f"Tool '{self.name}' received unknown argument(s): {unknown}")

        # Reject missing required args.
        missing = [k for k in required if k not in args]
        if missing:
            raise ToolError(f"Tool '{self.name}' missing required argument(s): {missing}")

        validated: dict = {}
        for arg_name, value in args.items():
            json_type = properties[arg_name].get("type", "string")
            validated[arg_name] = _coerce_value(value, json_type, arg_name)
        return validated

    def call(self, args: dict) -> str:
        """Validate ``args``, invoke the wrapped callable, and stringify the result.

        Any exception raised either by validation or by the callable itself is
        caught and converted to a string of the form
        ``ERROR: <ExceptionType>: <message>`` so the reasoning loop can read it
        and recover.

        Args:
            args (dict): the LLM-supplied arguments.

        Returns:
            str: the stringified result (``"OK"`` for ``None``), or an
            ``ERROR: ...`` string on failure.
        """
        try:
            validated = self.validate_args(args)
        except Exception as e:
            logger.debug(f"[Tool] '{self.name}' argument validation failed: {e}")
            return f"ERROR: {type(e).__name__}: {e}"

        try:
            result = self.fn(**validated)
        except Exception as e:
            logger.debug(f"[Tool] '{self.name}' raised {type(e).__name__}: {e}")
            return f"ERROR: {type(e).__name__}: {e}"

        if result is None:
            return "OK"
        if isinstance(result, str):
            return result
        try:
            return json.dumps(result)
        except (TypeError, ValueError):
            return str(result)
