from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from baf import nlp
from baf.core.message import MessageType, Message
from baf.exceptions.logger import logger
from baf.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction
from baf.nlp.llm.llm import LLM, LLMResponse, ToolCall

if TYPE_CHECKING:
    from baf.core.agent import Agent
    from baf.core.session import Session
    from baf.nlp.intent_classifier.llm_intent_classifier import LLMIntentClassifier

try:
    import anthropic as anthropic_sdk
except ImportError:
    anthropic_sdk = None
    logger.warning("anthropic dependencies in LLMAnthropic could not be imported. You can install them via "
                   "'pip install anthropic' or by adding it to requirements/requirements-llms.txt")

_DEFAULT_MAX_TOKENS = 4096
"""Default ``max_tokens`` used when the caller does not supply one.

The Anthropic Messages API requires ``max_tokens`` to be provided explicitly; this
constant is used as a safe default when it is absent from ``self.parameters``.
"""


class LLMAnthropic(LLM):
    """LLM wrapper for Anthropic Claude models using the native ``anthropic`` SDK.

    Anthropic's API differs enough from the OpenAI shape (system-prompt placement,
    tool-use schema, required ``max_tokens``, streaming model) that a dedicated
    implementation is cleaner than relying on the OpenAI-compat endpoint.

    Requires ``nlp.anthropic.api_key`` to be set in the agent config file (or
    passed as ``"api_key"`` inside ``parameters`` for a one-time override).

    Args:
        agent (Agent): the agent the LLM belongs to
        name (str): the model identifier (e.g. ``"claude-opus-4-5"``,
            ``"claude-sonnet-4-5"``, ``"claude-haiku-4-5-20251001"``).
        parameters (dict): parameters forwarded to ``messages.create``
            (e.g. ``{"temperature": 0.7, "max_tokens": 2048}``). May also contain
            ``"api_key"`` which is consumed by :meth:`initialize` and not forwarded.
        num_previous_messages (int): number of previous conversation turns to include
            in :meth:`chat` calls (must be > 0).
        global_context (str): system-level context injected into every request.

    Attributes:
        client: the ``anthropic.Anthropic`` client, instantiated in :meth:`initialize`.
        num_previous_messages (int): number of previous messages used in :meth:`chat`.
    """

    def __init__(self, agent: 'Agent', name: str, parameters: dict, num_previous_messages: int = 1,
                 global_context: str = None):
        super().__init__(agent, name, parameters, global_context=global_context)
        self.client: Any = None
        self.num_previous_messages: int = num_previous_messages

    def set_model(self, name: str) -> None:
        """Set the Claude model identifier.

        Args:
            name (str): the new model identifier
        """
        self.name = name

    def set_num_previous_messages(self, num_previous_messages: int) -> None:
        """Set the number of previous messages used in :meth:`chat`.

        Args:
            num_previous_messages (int): the new number of previous messages
        """
        self.num_previous_messages = num_previous_messages

    def initialize(self) -> None:
        """Instantiate the Anthropic client.

        Reads ``api_key`` from ``self.parameters`` first (popping it so it is not
        forwarded to the API call), then falls back to the ``nlp.anthropic.api_key``
        config-file property.
        """
        if anthropic_sdk is None:
            raise ImportError(
                "The 'anthropic' package is required for LLMAnthropic. "
                "Install it with: pip install anthropic"
            )
        api_key = self.parameters.pop('api_key', None) \
                  or self._nlp_engine.get_property(nlp.ANTHROPIC_API_KEY)
        self.client = anthropic_sdk.Anthropic(api_key=api_key)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_system(self, system_message: str = None, session: 'Session' = None) -> str | anthropic_sdk.NOT_GIVEN:
        """Assemble the Anthropic ``system`` parameter.

        Anthropic's API requires a single top-level ``system`` string (or ``NOT_GIVEN``),
        not a list of system-role messages.  We concatenate global context, session user
        context, and the per-call system message in that order.
        """
        parts = []
        if self._global_context:
            parts.append(self._global_context)
        if session and session.id in self._user_context:
            parts.append(self._user_context[session.id])
        if system_message:
            parts.append(system_message)
        if parts:
            return "\n\n".join(parts)
        return anthropic_sdk.NOT_GIVEN

    def _resolve_params(self, parameters: dict) -> dict:
        """Merge call-time parameters with defaults.

        Ensures ``max_tokens`` is always present (Anthropic requires it).
        """
        params = dict(self.parameters) if not parameters else dict(parameters)
        params.setdefault('max_tokens', _DEFAULT_MAX_TOKENS)
        return params

    @staticmethod
    def _openai_tools_to_anthropic(tools: list[dict]) -> list[dict]:
        """Convert OpenAI-style tool schemas to Anthropic tool format.

        OpenAI:  ``{"type": "function", "function": {"name", "description", "parameters"}}``
        Anthropic: ``{"name", "description", "input_schema"}``
        """
        result = []
        for t in tools:
            fn = t.get("function", {}) if t.get("type") == "function" else t
            result.append({
                "name": fn.get("name", ""),
                "description": fn.get("description", ""),
                "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
            })
        return result

    # ------------------------------------------------------------------
    # Public API (implements LLM abstract methods)
    # ------------------------------------------------------------------

    def predict(self, message: str, parameters: dict = None, session: 'Session' = None,
                system_message: str = None) -> str:
        params = self._resolve_params(parameters)
        system = self._build_system(system_message=system_message, session=session)
        response = self.client.messages.create(
            model=self.name,
            system=system,
            messages=[{"role": "user", "content": message}],
            **params,
        )
        return response.content[0].text

    def chat(self, session: 'Session', parameters: dict = None, system_message: str = None) -> str:
        if self.num_previous_messages <= 0:
            raise ValueError('The number of previous messages to send to the LLM must be > 0')
        params = self._resolve_params(parameters)
        system = self._build_system(system_message=system_message, session=session)
        chat_history: list[Message] = session.get_chat_history(n=self.num_previous_messages)
        messages = [
            {'role': 'user' if message.is_user else 'assistant', 'content': message.content}
            for message in chat_history
            if message.type in [MessageType.STR, MessageType.LOCATION, MessageType.JSON]
        ]
        response = self.client.messages.create(
            model=self.name,
            system=system,
            messages=messages,
            **params,
        )
        return response.content[0].text

    def predict_with_tools(
            self,
            messages: list[dict],
            tools: list[dict],
            parameters: dict = None,
            system_message: str = None,
    ) -> LLMResponse:
        """Make a tool-calling prediction using the native Anthropic SDK.

        Input ``messages`` and ``tools`` use OpenAI schema; this method translates them
        to the Anthropic format and maps the response back to the shared
        :class:`~baf.nlp.llm.llm.LLMResponse` / :class:`~baf.nlp.llm.llm.ToolCall`
        types so callers remain provider-agnostic.

        Args:
            messages (list[dict]): OpenAI-style chat messages. Tool result messages must
                include ``"tool_call_id"`` matching the call they answer.
            tools (list[dict]): OpenAI-style tool schemas.
            parameters (dict): extra parameters (e.g. ``temperature``, ``max_tokens``).
            system_message (str): high-priority system message.

        Returns:
            LLMResponse: final text or list of tool calls.
        """
        params = self._resolve_params(parameters)
        system = self._build_system(system_message=system_message)
        anthropic_tools = self._openai_tools_to_anthropic(tools) if tools else anthropic_sdk.NOT_GIVEN

        # Convert OpenAI tool-result messages (role=tool) to Anthropic's user/tool_result format.
        converted: list[dict] = []
        for msg in messages:
            if msg.get("role") == "tool":
                converted.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.get("tool_call_id", ""),
                        "content": msg.get("content", ""),
                    }]
                })
            else:
                converted.append(msg)

        response = self.client.messages.create(
            model=self.name,
            system=system,
            messages=converted,
            tools=anthropic_tools,
            **params,
        )

        # Map Anthropic response blocks back to the shared LLMResponse shape.
        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        if tool_use_blocks:
            calls = [
                ToolCall(id=b.id, name=b.name, arguments=b.input if isinstance(b.input, dict) else {})
                for b in tool_use_blocks
            ]
            return LLMResponse(text=None, tool_calls=calls, raw=response)

        text_blocks = [b for b in response.content if b.type == "text"]
        text = text_blocks[0].text if text_blocks else ""
        return LLMResponse(text=text, tool_calls=None, raw=response)

    def intent_classification(
            self,
            intent_classifier: 'LLMIntentClassifier',
            message: str,
            parameters: dict = None
    ) -> list[IntentClassifierPrediction]:
        """Classify intent via the Anthropic API, returning the same shape as LLMOpenAI.

        The output is fed to
        :meth:`~baf.nlp.intent_classifier.llm_intent_classifier.LLMIntentClassifier.default_json_to_intent_classifier_predictions`
        so that intent classifiers remain provider-agnostic.
        """
        params = self._resolve_params(parameters)
        response = self.client.messages.create(
            model=self.name,
            messages=[{"role": "user", "content": message}],
            **params,
        )
        raw_text = response.content[0].text
        try:
            response_json = json.loads(raw_text)
        except json.JSONDecodeError:
            logger.warning(f"LLMAnthropic: could not JSON-decode intent response: {raw_text!r}")
            response_json = {}
        return intent_classifier.default_json_to_intent_classifier_predictions(
            message=message,
            response_json=response_json
        )
