from __future__ import annotations

from baf import nlp
from baf.nlp.llm.llm_openai_compatible import LLMOpenAICompatible


class LLMMistral(LLMOpenAICompatible):
    """LLM wrapper for Mistral AI models via Mistral's OpenAI-compatible API.

    Requires ``nlp.mistral.api_key`` to be set in the agent config file.
    The default base URL points to ``https://api.mistral.ai/v1``.

    Example model names: ``"mistral-small-latest"``, ``"mistral-large-latest"``,
    ``"mistral-medium-latest"``, ``"open-mistral-nemo"``.
    """

    DEFAULT_BASE_URL = "https://api.mistral.ai/v1"
    API_KEY_PROPERTY = nlp.MISTRAL_API_KEY
