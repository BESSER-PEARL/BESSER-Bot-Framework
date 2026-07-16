from __future__ import annotations

from baf import nlp
from baf.nlp.llm.llm_openai_compatible import LLMOpenAICompatible


class LLMDeepSeek(LLMOpenAICompatible):
    """LLM wrapper for DeepSeek models via DeepSeek's OpenAI-compatible API.

    Requires ``nlp.deepseek.api_key`` to be set in the agent config file.
    The default base URL points to ``https://api.deepseek.com``.

    Example model names: ``"deepseek-chat"``, ``"deepseek-reasoner"``.
    """

    DEFAULT_BASE_URL = "https://api.deepseek.com"
    API_KEY_PROPERTY = nlp.DEEPSEEK_API_KEY
