import json
from typing import TYPE_CHECKING

from openai import OpenAI

from besser.bot import nlp
from besser.bot.core.message import MessageType
from besser.bot.core.session import Session
from besser.bot.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction
from besser.bot.nlp.llm.llm import LLM

if TYPE_CHECKING:
    from besser.bot.core.bot import Bot
    from besser.bot.nlp.intent_classifier.llm_intent_classifier import LLMIntentClassifier


class LLMOpenAI(LLM):

    def __init__(self, bot: 'Bot', name: str, parameters: dict, num_previous_messages: int = 1):
        super().__init__(bot, name, parameters)
        self.client: OpenAI = None
        self.num_previous_messages: int = num_previous_messages

    def initialize(self) -> None:
        self.client = OpenAI(api_key=self._bot.nlp_engine.get_property(nlp.OPENAI_API_KEY))

    def predict(self, message: str, parameters: dict = None) -> str:
        if not parameters:
            parameters = self.parameters
        response = self.client.chat.completions.create(
            model=self.name,
            messages=[
                {"role": "user", "content": message}
            ],
            **parameters,
        )
        return response.choices[0].message.content

    def chat(self, session: Session, parameters: dict = None) -> str:
        if not parameters:
            parameters = self.parameters
        if self.num_previous_messages <= 0:
            raise ValueError('The number of previous messages to send to the LLM must be > 0')
        messages = [
            {'role': 'user' if message.is_user else 'assistant', 'content': message.content}
            for message in session.chat_history[-self.num_previous_messages:]  # TODO: STORE CHAT IN DB INSTEAD OF SESSION
            if message.type in [MessageType.STR, MessageType.LOCATION]
        ]
        response = self.client.chat.completions.create(
            model=self.name,
            messages=messages,
            **parameters,
        )
        return response.choices[0].message.content

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
            messages=[
                {"role": "user", "content": message}
            ],
            response_format={"type": "json_object"},
            **parameters
        )
        response_json = json.loads(response.choices[0].message.content)
        return intent_classifier.default_json_to_intent_classifier_predictions(
            message=message,
            response_json=response_json
        )

    def set_model(self, name: str) -> None:
        self.name = name

    def set_parameters(self, parameters: dict) -> None:
        self.parameters = parameters

    def set_num_previous_messages(self, num_previous_messages: int) -> None:
        self.num_previous_messages = num_previous_messages
