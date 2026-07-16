from __future__ import annotations

from baf import nlp
from baf.nlp.llm.llm_openai_compatible import LLMOpenAICompatible


class LLMOpenRouter(LLMOpenAICompatible):
    """LLM wrapper for models accessed via OpenRouter's OpenAI-compatible API.

    OpenRouter provides a unified gateway to hundreds of models from many providers.
    Requires ``nlp.openrouter.api_key`` to be set in the agent config file.
    The default base URL points to ``https://openrouter.ai/api/v1``.

    Example model names (use the OpenRouter ``provider/model`` format):
    ``"anthropic/claude-opus-4"``, ``"google/gemini-2.5-pro"``,
    ``"openai/gpt-4o"``, ``"meta-llama/llama-3.3-70b-instruct"``.
    """

    DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
    API_KEY_PROPERTY = nlp.OPENROUTER_API_KEY
