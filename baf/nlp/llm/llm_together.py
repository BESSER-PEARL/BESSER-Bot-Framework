from __future__ import annotations

from baf import nlp
from baf.nlp.llm.llm_openai_compatible import LLMOpenAICompatible


class LLMTogether(LLMOpenAICompatible):
    """LLM wrapper for Together AI models via Together's OpenAI-compatible API.

    Requires ``nlp.together.api_key`` to be set in the agent config file.
    The default base URL points to ``https://api.together.xyz/v1``.

    Example model names: ``"meta-llama/Llama-3.3-70B-Instruct-Turbo"``,
    ``"mistralai/Mixtral-8x22B-Instruct-v0.1"``,
    ``"Qwen/Qwen2.5-72B-Instruct-Turbo"``.
    """

    DEFAULT_BASE_URL = "https://api.together.xyz/v1"
    API_KEY_PROPERTY = nlp.TOGETHER_API_KEY
