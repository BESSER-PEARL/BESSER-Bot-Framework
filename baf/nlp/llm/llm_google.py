from __future__ import annotations

from baf import nlp
from baf.nlp.llm.llm_openai_compatible import LLMOpenAICompatible


class LLMGoogle(LLMOpenAICompatible):
    """LLM wrapper for Google Gemini models via Google's OpenAI-compatible endpoint.

    Requires ``nlp.google.api_key`` to be set in the agent config file.
    The default base URL points to the Gemini OpenAI-compatible endpoint.

    Example model names: ``"gemini-2.5-pro"``, ``"gemini-2.5-flash"``,
    ``"gemini-2.0-flash"``, ``"gemini-1.5-pro"``.

    Note: for advanced Gemini-specific features (grounding, multimodal tool use, etc.)
    a native ``google-genai`` SDK wrapper can be added separately.
    """

    DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
    API_KEY_PROPERTY = nlp.GOOGLE_API_KEY
