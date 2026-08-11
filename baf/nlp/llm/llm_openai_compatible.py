from __future__ import annotations

import json
from typing import TYPE_CHECKING

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
    from openai import OpenAI
except ImportError:
    logger.warning("openai dependencies in LLMOpenAICompatible could not be imported. You can install them from the "
                   "requirements/requirements-llm.txt file")


class LLMOpenAICompatible(LLM):
    """Shared implementation for all OpenAI-compatible LLM providers.

    Any provider that exposes an OpenAI-compatible chat-completions endpoint can subclass
    this class and only override two class attributes:

    - ``DEFAULT_BASE_URL`` – the provider's base URL (``None`` → use the OpenAI SDK default).
    - ``API_KEY_PROPERTY`` – the :class:`~baf.core.property.Property` constant from
      :mod:`baf.nlp` that holds the API key for the provider.

    Per-instance overrides are also accepted via the ``parameters`` dict: if ``parameters``
    contains ``"base_url"`` or ``"api_key"`` keys, they take priority over the class
    defaults and the config-file values respectively.  Both keys are *popped* from
    ``parameters`` in :meth:`initialize` so they are never forwarded to
    ``chat.completions.create``.

    Args:
        agent (Agent): the agent the LLM belongs to
        name (str): the LLM name / model identifier (e.g. ``"gpt-4o-mini"``)
        parameters (dict): the LLM parameters forwarded to ``chat.completions.create``
            (e.g. ``{"temperature": 0.7}``). May also contain the one-time connection
            overrides ``"base_url"`` and ``"api_key"`` which are consumed by
            :meth:`initialize` and not forwarded to the API.
        num_previous_messages (int): number of previous conversation turns to include in
            :meth:`chat` calls (must be > 0). Requires a connection to
            :class:`~baf.db.monitoring_db.MonitoringDB`.
        global_context (str): system-level context injected into every request.
    """

    DEFAULT_BASE_URL: str | None = None
    """Provider base URL.  ``None`` → use the OpenAI SDK default (``api.openai.com``)."""

    API_KEY_PROPERTY = nlp.OPENAI_API_KEY
    """Property constant used to look up the API key from the agent config file."""

    def __init__(self, agent: 'Agent', name: str, parameters: dict, num_previous_messages: int = 1,
                 global_context: str = None):
        super().__init__(agent, name, parameters, global_context=global_context)
        self.client: OpenAI = None
        self.num_previous_messages: int = num_previous_messages

    def set_model(self, name: str) -> None:
        """Set the LLM model name.

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
        """Instantiate the OpenAI-compatible client.

        Reads ``base_url`` and ``api_key`` from ``self.parameters`` first (popping them
        so they are not forwarded to the completion call), then falls back to the class
        ``DEFAULT_BASE_URL`` and the config-file property ``API_KEY_PROPERTY``.
        """
        base_url = self.parameters.pop('base_url', None) or self.DEFAULT_BASE_URL
        api_key = self.parameters.pop('api_key', None) \
                  or self._nlp_engine.get_property(self.API_KEY_PROPERTY)
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def predict(self, message: str, parameters: dict = None, session: 'Session' = None,
                system_message: str = None) -> str:
        messages = []
        if self._global_context:
            messages.append({"role": "system", "content": self._global_context})
        if session and session.id in self._user_context:
            messages.append({"role": "system", "content": self._user_context[session.id]})
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": message})
        if not parameters:
            parameters = self.parameters
        response = self.client.chat.completions.create(
            model=self.name,
            messages=messages,
            **parameters,
        )
        return response.choices[0].message.content

    def chat(self, session: 'Session', parameters: dict = None, system_message: str = None) -> str:
        if not parameters:
            parameters = self.parameters
        if self.num_previous_messages <= 0:
            raise ValueError('The number of previous messages to send to the LLM must be > 0')
        chat_history: list[Message] = session.get_chat_history(n=self.num_previous_messages)
        messages = [
            {'role': 'user' if message.is_user else 'assistant', 'content': message.content}
            for message in chat_history
            if message.type in [MessageType.STR, MessageType.LOCATION, MessageType.JSON]
        ]
        context_messages = []
        if self._global_context:
            context_messages.append({"role": "system", "content": self._global_context})
        if session and session.id in self._user_context:
            context_messages.append({"role": "system", "content": self._user_context[session.id]})
        if system_message:
            context_messages.append({"role": "system", "content": system_message})
        response = self.client.chat.completions.create(
            model=self.name,
            messages=context_messages + messages,
            **parameters,
        )
        return response.choices[0].message.content

    def predict_with_tools(
            self,
            messages: list[dict],
            tools: list[dict],
            parameters: dict = None,
            system_message: str = None,
    ) -> LLMResponse:
        """Make a tool-calling prediction using the OpenAI function-calling API.

        Args:
            messages (list[dict]): list of OpenAI-style chat messages. Tool result messages
                must include ``"tool_call_id"`` matching the call they answer.
            tools (list[dict]): list of OpenAI-style tool schemas. If empty, no tools are
                sent and the call behaves like a normal chat completion.
            parameters (dict): extra LLM parameters. If none is provided,
                ``self.parameters`` is used.
            system_message (str): high-priority system message inserted before
                ``messages``.

        Returns:
            LLMResponse: either a final text response or a list of tool calls to execute.
        """
        if not parameters:
            parameters = self.parameters
        final_messages: list[dict] = []
        if self._global_context:
            final_messages.append({"role": "system", "content": self._global_context})
        if system_message:
            final_messages.append({"role": "system", "content": system_message})
        final_messages.extend(messages)
        response = self.client.chat.completions.create(
            model=self.name,
            messages=final_messages,
            tools=tools if tools else None,
            tool_choice="auto" if tools else None,
            **parameters,
        )
        msg = response.choices[0].message
        if getattr(msg, "tool_calls", None):
            calls: list[ToolCall] = []
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                except json.JSONDecodeError:
                    logger.warning(
                        f"{self.__class__.__name__}: could not JSON-decode tool args: "
                        f"{tc.function.arguments!r}"
                    )
                    args = {}
                calls.append(ToolCall(id=tc.id, name=tc.function.name, arguments=args))
            return LLMResponse(text=None, tool_calls=calls, raw=response)
        return LLMResponse(text=msg.content, tool_calls=None, raw=response)

    def intent_classification(
            self,
            intent_classifier: 'LLMIntentClassifier',
            message: str,
            parameters: dict = None
    ) -> list[IntentClassifierPrediction]:
        if not parameters:
            parameters = self.parameters
        response = self.client.chat.completions.create(
            model=self.name,
            messages=[{"role": "user", "content": message}],
            response_format={"type": "json_object"},
            **parameters
        )
        response_json = json.loads(response.choices[0].message.content)
        return intent_classifier.default_json_to_intent_classifier_predictions(
            message=message,
            response_json=response_json
        )
