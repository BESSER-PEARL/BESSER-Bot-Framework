from __future__ import annotations

from typing import TYPE_CHECKING

from baf import nlp
from baf.nlp.llm.llm_openai_compatible import LLMOpenAICompatible

if TYPE_CHECKING:
    from baf.core.agent import Agent


class LLMOpenAI(LLMOpenAICompatible):
    """An LLM wrapper for OpenAI's models through the OpenAI API.

    Inherits all prediction logic from :class:`~baf.nlp.llm.llm_openai_compatible.LLMOpenAICompatible`.
    The OpenAI client is initialised with the ``nlp.openai.api_key`` config property and the
    standard ``https://api.openai.com`` base URL.

    Args:
        agent (Agent): the agent the LLM belongs to
        name (str): the model identifier (e.g. ``"gpt-4o-mini"``)
        parameters (dict): parameters forwarded to ``chat.completions.create``
            (e.g. ``{"temperature": 0.7}``).
        num_previous_messages (int): number of previous turns to include in :meth:`chat`
            calls (must be > 0).
        global_context (str): system-level context injected into every request.

    Attributes:
        client (OpenAI): the OpenAI client, instantiated in :meth:`initialize`.
        num_previous_messages (int): number of previous messages used in :meth:`chat`.
    """

    DEFAULT_BASE_URL: str | None = None  # use the OpenAI SDK default
    API_KEY_PROPERTY = nlp.OPENAI_API_KEY
