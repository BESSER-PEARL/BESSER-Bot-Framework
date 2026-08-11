from __future__ import annotations

from baf import nlp
from baf.nlp.llm.llm_openai_compatible import LLMOpenAICompatible


class LLMGroq(LLMOpenAICompatible):
    """LLM wrapper for Groq-hosted models via Groq's OpenAI-compatible API.

    Requires ``nlp.groq.api_key`` to be set in the agent config file.
    The default base URL points to ``https://api.groq.com/openai/v1``.

    Example model names: ``"llama-3.3-70b-versatile"``, ``"llama3-8b-8192"``,
    ``"gemma2-9b-it"``, ``"mixtral-8x7b-32768"``.
    """

    DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"
    API_KEY_PROPERTY = nlp.GROQ_API_KEY
