import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from besser.bot.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction

if TYPE_CHECKING:
    from besser.bot.core.session import Session
    from besser.bot.nlp.intent_classifier.llm_intent_classifier import LLMIntentClassifier
    from besser.bot.nlp.nlp_engine import NLPEngine


class LLM(ABC):
    """The LLM abstract class.

    An LLM (Large Language Model) receives a text input and generates an output. Depending on the LLM, several tasks can be performed, such as
    question answering, translation, text classification, etc.

    This class serves as a template to be implemented for specific LLM providers.

    Args:
        nlp_engine (NLPEngine): the NLPEngine that handles the NLP processes of the bot the LLM belongs to
        name (str): the LLM name
        parameters (dict): the LLM parameters
        global_context (str): the global context to be provided to the LLM for each request

    Attributes:
        _nlp_engine (NLPEngine): the NLPEngine that handles the NLP processes of the bot the LLM belongs to
        name (str): the LLM name
        parameters (dict): the LLM parameters
        _global_context (str): the global context to be provided to the LLM for each request
        _user_context (dict): aggregation of user specific contexts to be provided to the LLM for each request
        _user_contexts (dict): dictionary containing the different context elements making up the user's context
            user specific context to be provided to the LLM for each request
    """

    def __init__(self, nlp_engine: 'NLPEngine', name: str, parameters: dict, global_context: str = None):
        self._nlp_engine: 'NLPEngine' = nlp_engine
        self.name: str = name
        self.parameters: dict = parameters
        self._nlp_engine._llms[name] = self
        self._global_context: str = global_context
        self._user_context: dict = dict()
        self._user_contexts: dict = dict()

    def set_parameters(self, parameters: dict) -> None:
        """Set the LLM parameters.

        Args:
            parameters (dict): the new LLM parameters
        """
        self.parameters = parameters

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the LLM. This function is called during the bot training."""
        pass

    @abstractmethod
    def predict(self, message: str, parameters: dict = None, session: 'Session' = None,
                system_message: str = None) -> str:
        """Make a prediction, i.e., generate an output.

        Args:
            message (Any): the LLM input text
            session (Session): the ongoing session, can be None if no context needs to be applied
            parameters (dict): the LLM parameters to use in the prediction. If none is provided, the default LLM
                parameters will be used
            system_message (str): system message to give high priority context to the LLM

        Returns:
            str: the LLM output
        """
        pass

    def chat(self, session: 'Session', parameters: dict = None, system_message: str = None) -> str:
        """Make a prediction, i.e., generate an output.

        This function can provide the chat history to the LLM for the output generation, simulating a conversation or
        remembering previous messages.

        Args:
            session (Session): the user session
            parameters (dict): the LLM parameters. If none is provided, the RAG's default value will be used
            system_message (str): system message to give high priority context to the LLM
            
        Returns:
            str: the LLM output
        """
        logging.warning(f'Chat not implemented in {self.__class__.__name__}')
        return None

    def intent_classification(
            self,
            intent_classifier: 'LLMIntentClassifier',
            message: str,
            parameters: dict = None
    ) -> list[IntentClassifierPrediction]:
        """Predict the intent of a given message.

        Instead of returning only the intent with the highest likelihood, return all predictions. Predictions include
        not only the intent scores but other information extracted from the message.

        Args:
            intent_classifier (LLMIntentClassifier): the intent classifier that is running the intent classification
                process
            message (str): the message to predict the intent
            parameters (dict): the LLM parameters. If none is provided, the RAG's default value will be used

        Returns:
            list[IntentClassifierPrediction]: the list of predictions made by the LLM.
        """
        logging.warning(f'Intent Classification not implemented in {self.__class__.__name__}')
        return []

    def add_user_context(self, session: 'Session', context: str, context_name: str) -> None:
        """Add user-specific context.

        Args:
            session (Session): the ongoing session
            context (str): the user-specific context
            context_name (str): the key given to the specific user context
        """
        if session.id not in self._user_context:
            self._user_contexts[session.id] = {}
        self._user_contexts[session.id][context_name] = context
        context_message = ""
        for context_element in self._user_contexts[session.id]:
            context_message = context_message + self._user_contexts[session.id][context_element] + "\n"
        self._user_context[session.id] = context_message
        
    def remove_user_context(self, session: 'Session', context_name: str) -> None:
        """Remove user-specific context.

        Args:
            session (Session): the ongoing session
            context_name (str): the key given to the specific user context
        """
        if session.id not in self._user_context or context_name not in self._user_contexts[session.id]:
            return
        else:
            self._user_contexts[session.id].pop(context_name)
        context_message = ""
        for context_element in self._user_contexts[session.id]:
            context_message = context_message + self._user_contexts[session.id][context_element] + "\n"
        if context_message != "":
            self._user_context[session.id] = context_message
        else:
            self._user_context.pop(session.id)
