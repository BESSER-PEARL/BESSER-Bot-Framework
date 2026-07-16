"""LLM-assisted GUI generation utilities."""
from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

from baf.core.gui.agent_gui import AgentGUI
from baf.core.gui.gui_deserializer import json_to_gui
from baf.core.gui.gui_schema import get_json_schema
from baf.exceptions.logger import logger

if TYPE_CHECKING:
    from baf.nlp.llm.llm import LLM

_SYSTEM_PROMPT_TEMPLATE = (
    "You are a GUI model generator. Given a user request, respond with a single valid JSON object "
    "that conforms to the JSON Schema below. Output raw JSON only — no explanation, no markdown "
    "code fences, no prose before or after.\n\n"
    "JSON Schema:\n{schema}\n\n"
    "Rules:\n"
    "- The top-level object must contain 'name' and 'modules'.\n"
    "- Each module must have 'name' and 'screens'.\n"
    "- Each screen must have 'name' and 'view_elements'.\n"
    "- Every view element must have a 'type' field discriminating its kind.\n"
    "- Keep the model minimal but meaningful for the user request.\n"
    "- Use realistic placeholder content (titles, labels, button labels, etc.)."
)

_RETRY_PROMPT_TEMPLATE = (
    "The previous response could not be deserialized. Error: {error}\n\n"
    "Please fix the JSON and respond again with a single valid JSON object only. "
    "Original request: {prompt}"
)


def _build_system_prompt() -> str:
    return _SYSTEM_PROMPT_TEMPLATE.format(schema=json.dumps(get_json_schema(), indent=2))


def _extract_json(text: str) -> str:
    """Strip markdown code fences and return the raw JSON string from LLM output."""
    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if match:
        return match.group(1).strip()
    match = re.search(r'(\{[\s\S]*\})', text)
    if match:
        return match.group(1).strip()
    return text.strip()


def create_gui_with_llm(
    llm: 'LLM',
    prompt: str,
    gui_id: str | None = None,
    max_retries: int = 2,
) -> AgentGUI:
    """Generate an :class:`~baf.core.gui.agent_gui.AgentGUI` from a natural-language description.

    The LLM is instructed via a system prompt to produce a JSON object conforming to
    the AgentGUI JSON Schema. The JSON is then deserialized into a full
    :class:`~baf.core.gui.agent_gui.AgentGUI` instance. If the first response fails to
    parse or deserialize, the error is fed back to the LLM and the call is retried up to
    *max_retries* times.

    Args:
        llm (LLM): any BAF :class:`~baf.nlp.llm.llm.LLM` instance with a ``predict`` method.
        prompt (str): natural-language description of the GUI to generate (e.g.
            ``"A login form with email, password fields and a Submit button."``).
        gui_id (str | None): optional identifier forwarded to the returned
            :class:`~baf.core.gui.agent_gui.AgentGUI`. A random UUID is used when
            ``None`` (default).
        max_retries (int): number of correction attempts when the LLM returns invalid or
            non-deserializable JSON. Defaults to ``2``.

    Returns:
        AgentGUI | None: the generated GUI model, or ``None`` if generation failed after
        all retries.

    Example::

        from baf.core.gui.gui_llm import create_gui_with_llm

        gui = create_gui_with_llm(
            llm=gpt,
            prompt="A dashboard with a line chart and two metric cards.",
        )
        if gui is not None:
            session.set_gui(gui)
    """
    system_prompt = _build_system_prompt()
    current_prompt = prompt
    last_error: Exception | None = None

    for attempt in range(1 + max_retries):
        raw = llm.predict(current_prompt, system_message=system_prompt)
        try:
            gui = json_to_gui(_extract_json(raw), gui_id=gui_id)
            if attempt > 0:
                logger.info(f"create_gui_with_llm: succeeded on attempt {attempt + 1}.")
            return gui
        except Exception as exc:
            last_error = exc
            if attempt < max_retries:
                logger.warning(
                    f"create_gui_with_llm: attempt {attempt + 1} failed — {exc}. Retrying..."
                )
                current_prompt = _RETRY_PROMPT_TEMPLATE.format(error=exc, prompt=prompt)
            else:
                logger.warning(
                    f"create_gui_with_llm: attempt {attempt + 1} failed — {exc}. No more retries."
                )

    logger.error(
        f"create_gui_with_llm: could not generate a valid GUI after {1 + max_retries} "
        f"attempt(s). Last error: {last_error}"
    )
    return None
