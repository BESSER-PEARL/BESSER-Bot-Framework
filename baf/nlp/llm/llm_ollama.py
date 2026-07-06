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
    logger.warning("openai dependencies in LLMOllama could not be imported. You can install them from the "
                   "requirements/requirements-llms.txt file")


class LLMOllama(LLM):
    """An LLM wrapper for locally hosted Ollama models via the OpenAI-compatible API.

    Args:
        agent (Agent): the agent the LLM belongs to
        name (str): the LLM name (used for registration)
        parameters (dict): the LLM parameters; expected keys: ``base_url`` (default
            ``http://localhost:11434``) and ``model`` (e.g. ``llama3``). Extra keys are
            forwarded to the completions API.
        num_previous_messages (int): for the chat functionality, the number of previous messages
            of the conversation to add to the prompt context (must be > 0)
        global_context (str): the global context to be provided to the LLM for each request

    Attributes:
        _nlp_engine (NLPEngine): the NLPEngine that handles the NLP processes of the agent the LLM belongs to
        name (str): the LLM name
        parameters (dict): the LLM parameters
        num_previous_messages (int): for the chat functionality, the number of previous messages
            of the conversation to add to the prompt context (must be > 0)
        _global_context (str): the global context to be provided to the LLM for each request
        _user_context (dict): user specific context to be provided to the LLM for each request
    """

    def __init__(self, agent: 'Agent', name: str, parameters: dict, num_previous_messages: int = 1,
                 global_context: str = None):
        super().__init__(agent, name, parameters, global_context=global_context)
        self.client: OpenAI = None
        self.num_previous_messages: int = num_previous_messages

    def set_model(self, name: str) -> None:
        """Set the LLM model name.

        Args:
            name (str): the new LLM name
        """
        self.name = name

    def set_num_previous_messages(self, num_previous_messages: int) -> None:
        """Set the number of previous messages to use in the chat functionality

        Args:
            num_previous_messages (int): the new number of previous messages
        """
        self.num_previous_messages = num_previous_messages

    def _base_url(self) -> str:
        url = (
            self.parameters.get('base_url')
            or self._nlp_engine.get_property(nlp.OLLAMA_BASE_URL)
            or 'http://localhost:11434'
        )
        url = str(url).rstrip('/')
        if not url.endswith('/v1'):
            url += '/v1'
        return url

    def _model(self) -> str:
        return self.parameters.get('model', self.name)

    def _api_params(self, override: dict = None) -> dict:
        excluded = {'base_url', 'model'}
        base = {k: v for k, v in self.parameters.items() if k not in excluded}
        if override:
            base = override
        return base

    def initialize(self) -> None:
        self.client = OpenAI(base_url=self._base_url(), api_key='ollama')

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
        response = self.client.chat.completions.create(
            model=self._model(),
            messages=messages,
            **self._api_params(parameters),
        )
        return response.choices[0].message.content

    def chat(self, session: 'Session', parameters: dict = None, system_message: str = None) -> str:
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
            model=self._model(),
            messages=context_messages + messages,
            **self._api_params(parameters),
        )
        return response.choices[0].message.content

    def predict_with_tools(
            self,
            messages: list[dict],
            tools: list[dict],
            parameters: dict = None,
            system_message: str = None,
    ) -> LLMResponse:
        """Make a tool-calling prediction using Ollama's OpenAI-compatible function-calling API.

        Args:
            messages (list[dict]): list of OpenAI-style chat messages
            tools (list[dict]): list of OpenAI-style tool schemas
            parameters (dict): extra LLM parameters
            system_message (str): high-priority system message inserted before ``messages``

        Returns:
            LLMResponse: either a final text response or a list of tool calls to execute
        """
        final_messages: list[dict] = []
        if self._global_context:
            final_messages.append({"role": "system", "content": self._global_context})
        if system_message:
            final_messages.append({"role": "system", "content": system_message})
        final_messages.extend(messages)
        response = self.client.chat.completions.create(
            model=self._model(),
            messages=final_messages,
            tools=tools if tools else None,
            tool_choice="auto" if tools else None,
            **self._api_params(parameters),
        )
        msg = response.choices[0].message
        if getattr(msg, "tool_calls", None):
            calls: list[ToolCall] = []
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                except json.JSONDecodeError:
                    logger.warning(f"LLMOllama: could not JSON-decode tool args: {tc.function.arguments!r}")
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
        response = self.client.chat.completions.create(
            model=self._model(),
            messages=[{"role": "user", "content": message}],
            response_format={"type": "json_object"},
            **self._api_params(parameters),
        )
        response_json = json.loads(response.choices[0].message.content)
        return intent_classifier.default_json_to_intent_classifier_predictions(
            message=message,
            response_json=response_json
        )
