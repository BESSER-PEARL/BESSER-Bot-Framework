from __future__ import annotations

from baf import nlp
from baf.nlp.llm.llm_openai_compatible import LLMOpenAICompatible


class LLMQwen(LLMOpenAICompatible):
    """LLM wrapper for Alibaba Qwen models via DashScope's OpenAI-compatible endpoint.

    Requires ``nlp.qwen.api_key`` to be set in the agent config file.
    The default base URL points to the international DashScope endpoint.

    Example model names: ``"qwen-max"``, ``"qwen-plus"``, ``"qwen-turbo"``,
    ``"qwen3-235b-a22b"``.
    """

    DEFAULT_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    API_KEY_PROPERTY = nlp.QWEN_API_KEY
