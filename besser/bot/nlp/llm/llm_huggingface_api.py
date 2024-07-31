from typing import TYPE_CHECKING

import requests

from besser.bot import nlp
from besser.bot.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction
from besser.bot.nlp.llm.llm import LLM
from besser.bot.nlp.utils import find_json

if TYPE_CHECKING:
    from besser.bot.core.bot import Bot
    from besser.bot.nlp.intent_classifier.llm_intent_classifier import LLMIntentClassifier


class LLMHuggingFaceAPI(LLM):

    def __init__(self, bot: 'Bot', name: str, parameters: dict, num_previous_messages: int = 1):
        super().__init__(bot.nlp_engine, name, parameters)
        self.num_previous_messages: int = num_previous_messages

    def initialize(self) -> None:
        pass

    def predict(self, message: str, parameters: dict = None) -> str:
        if not parameters:
            parameters = self.parameters
        parameters['return_full_text'] = False
        # https://huggingface.co/docs/api-inference/detailed_parameters#text-generation-task
        headers = {"Authorization": f"Bearer {self._nlp_engine.get_property(nlp.HF_API_KEY)}"}
        api_url = F"https://api-inference.huggingface.co/models/{self.name}"
        payload = {"inputs": message, "parameters": parameters}
        response = requests.post(api_url, headers=headers, json=payload)
        return response.json()[0]['generated_text']

    def intent_classification(
            self,
            intent_classifier: 'LLMIntentClassifier',
            message: str,
            parameters: dict = None
    ) -> list[IntentClassifierPrediction]:
        if not parameters:
            parameters = self.parameters
        parameters['return_full_text'] = False
        answer = self.predict(message, parameters)
        response_json = find_json(answer)
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
