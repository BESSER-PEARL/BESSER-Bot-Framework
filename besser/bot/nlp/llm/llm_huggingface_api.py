from typing import TYPE_CHECKING

import requests

from besser.bot import nlp
from besser.bot.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction
from besser.bot.nlp.llm.llm import LLM
from besser.bot.nlp.utils import find_json

if TYPE_CHECKING:
    from besser.bot.core.bot import Bot
    from besser.bot.core.session import Session
    from besser.bot.nlp.intent_classifier.llm_intent_classifier import LLMIntentClassifier


class LLMHuggingFaceAPI(LLM):
    """A HuggingFace LLM wrapper for HuggingFace's Inference API.

    Normally, we consider an LLM in HuggingFace those models under the tasks ``text-generation`` or
    ``text2text-generation`` tasks (`more info <https://huggingface.co/tasks/text-generation>`_), but there could be
    exceptions for other tasks (which have not been tested in this class).

    Args:
        bot (Bot): the bot the LLM belongs to
        name (str): the LLM name
        parameters (dict): the LLM parameters
        num_previous_messages (int): for the chat functionality, the number of previous messages of the conversation
            to add to the prompt context (must be > 0)
        global_context (str): the global context to be provided to the LLM for each request

    Attributes:
        _nlp_engine (NLPEngine): the NLPEngine that handles the NLP processes of the bot the LLM belongs to
        name (str): the LLM name
        parameters (dict): the LLM parameters
        num_previous_messages (int): for the chat functionality, the number of previous messages of the conversation
            to add to the prompt context (must be > 0)
        _global_context (str): the global context to be provided to the LLM for each request
        _user_context (dict): user specific context to be provided to the LLM for each request
    """

    def __init__(self, bot: 'Bot', name: str, parameters: dict, num_previous_messages: int = 1, 
                 global_context: str = None):
        super().__init__(bot.nlp_engine, name, parameters, global_context=global_context)
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

    def initialize(self) -> None:
        pass

    def predict(self, message: str, parameters: dict = None, session: 'Session' = None, system_message: str = None) -> str:
        """Make a prediction, i.e., generate an output.

        Runs the `Text Generation Inference API task
        <https://huggingface.co/docs/api-inference/detailed_parameters#text-generation-task>`_

        Args:
            message (Any): the LLM input text
            parameters (dict): the LLM parameters to use in the prediction. If none is provided, the default LLM
                parameters will be used
            system_message (str): system message to give high priority context to the LLM
            
        Returns:
            str: the LLM output
        """
        if not parameters:
            parameters = self.parameters.copy()
        else:
            parameters = parameters.copy()
        parameters['return_full_text'] = False
        headers = {"Authorization": f"Bearer {self._nlp_engine.get_property(nlp.HF_API_KEY)}"}
        api_url = F"https://api-inference.huggingface.co/models/{self.name}"
        context_messages = ""
        if self._global_context:
            context_messages = f"{self._global_context}\n"
        if session and session.id in self._user_context:
            context_messages = context_messages + f"{self._user_context[session.id]}\n"
        if system_message:
            context_messages = context_messages + f"{system_message}\n"
        if context_messages != "":
            message = context_messages + message
        payload = {"inputs": message, "parameters": parameters}
        response = requests.post(api_url, headers=headers, json=payload)
        return response.json()[0]['generated_text']

    def intent_classification(
            self,
            intent_classifier: 'LLMIntentClassifier',
            message: str,
            parameters: dict = None
    ) -> list[IntentClassifierPrediction]:
        answer = self.predict(message, parameters)
        response_json = find_json(answer)
        return intent_classifier.default_json_to_intent_classifier_predictions(
            message=message,
            response_json=response_json
        )
