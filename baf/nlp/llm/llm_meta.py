from __future__ import annotations

from baf import nlp
from baf.nlp.llm.llm_openai_compatible import LLMOpenAICompatible


class LLMMeta(LLMOpenAICompatible):
    """LLM wrapper for Meta Llama models via Meta's OpenAI-compatible API.

    Requires ``nlp.meta.api_key`` to be set in the agent config file.
    The default base URL points to ``https://api.llama.com/compat/v1/``.

    Example model names: ``"Llama-4-Scout-17B-16E-Instruct-FP8"``,
    ``"Llama-4-Maverick-17B-128E-Instruct-FP8"``, ``"Llama-3.3-70B-Instruct"``.
    """

    DEFAULT_BASE_URL = "https://api.llama.com/compat/v1/"
    API_KEY_PROPERTY = nlp.META_API_KEY
