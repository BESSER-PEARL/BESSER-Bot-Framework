from typing import TYPE_CHECKING

from transformers import pipeline

from besser.bot.core.message import MessageType
from besser.bot.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction
from besser.bot.nlp.llm.llm import LLM
from besser.bot.nlp.utils import merge_llm_consecutive_messages, find_json

if TYPE_CHECKING:
    from besser.bot.core.bot import Bot
    from besser.bot.core.session import Session
    from besser.bot.nlp.intent_classifier.llm_intent_classifier import LLMIntentClassifier


class LLMHuggingFace(LLM):

    def __init__(self, bot: 'Bot', name: str, parameters: dict, num_previous_messages: int = 1):
        super().__init__(bot.nlp_engine, name, parameters)
        self.pipe = None
        self.num_previous_messages: int = num_previous_messages

    def initialize(self) -> None:
        self.pipe = pipeline("text-generation", model=self.name)

    def predict(self, message: str, parameters: dict = None) -> str:
        if not parameters:
            parameters = self.parameters
        outputs = self.pipe([{'role': 'user', 'content': message}], return_full_text=False, **parameters)
        answer = outputs[0]['generated_text']
        return answer

    def chat(self, session: 'Session', parameters: dict = None) -> str:
        if not parameters:
            parameters = self.parameters
        if self.num_previous_messages <= 0:
            raise ValueError('The number of previous messages to send to the LLM must be > 0')
        messages = [
            {'role': 'user' if message.is_user else 'assistant', 'content': message.content}
            for message in session.chat_history[-self.num_previous_messages:]  # TODO: STORE CHAT IN DB INSTEAD OF SESSION
            if message.type in [MessageType.STR, MessageType.LOCATION]
        ]
        messages = merge_llm_consecutive_messages(messages)
        outputs = self.pipe(messages, return_full_text=False, **parameters)
        answer = outputs[0]['generated_text']
        return answer

    def intent_classification(
            self,
            intent_classifier: 'LLMIntentClassifier',
            message: str,
            parameters: dict = None
    ) -> list[IntentClassifierPrediction]:
        if not parameters:
            parameters = self.parameters
        answer = self.predict(message, parameters)
        response_json = find_json(answer)
        return intent_classifier.default_json_to_intent_classifier_predictions(
            message=message,
            response_json=response_json
        )

    def set_parameters(self, parameters: dict) -> None:
        self.parameters = parameters

    def set_num_previous_messages(self, num_previous_messages: int) -> None:
        self.num_previous_messages = num_previous_messages
