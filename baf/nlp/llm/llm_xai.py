from __future__ import annotations

from baf import nlp
from baf.nlp.llm.llm_openai_compatible import LLMOpenAICompatible


class LLMxAI(LLMOpenAICompatible):
    """LLM wrapper for xAI Grok models via xAI's OpenAI-compatible API.

    Requires ``nlp.xai.api_key`` to be set in the agent config file.
    The default base URL points to ``https://api.x.ai/v1``.

    Example model names: ``"grok-3"``, ``"grok-3-mini"``, ``"grok-2-latest"``.
    """

    DEFAULT_BASE_URL = "https://api.x.ai/v1"
    API_KEY_PROPERTY = nlp.XAI_API_KEY
