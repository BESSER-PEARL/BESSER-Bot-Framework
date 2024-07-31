import logging
from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

from besser.bot.core.session import Session
from besser.bot.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction

if TYPE_CHECKING:
    from besser.bot.core.bot import Bot
    from besser.bot.nlp.intent_classifier.llm_intent_classifier import LLMIntentClassifier


class LLM(ABC):

    def __init__(self, bot: 'Bot', name: str, parameters: dict):
        self._bot: 'Bot' = bot
        self.name: str = name
        self.parameters: dict = parameters
        self._bot.nlp_engine._llms[name] = self

    @abstractmethod
    def initialize(self) -> None:
        pass

    @abstractmethod
    def predict(self, message: Any) -> str:
        pass

    def chat(self, session: Session, parameters: dict = None) -> str:
        logging.warning(f'Chat not implemented in {self.__class__.__name__}')
        return None

    def intent_classification(
            self,
            intent_classifier: 'LLMIntentClassifier',
            message: str,
            parameters: dict = None
    ) -> list[IntentClassifierPrediction]:
        logging.warning(f'Intent Classification not implemented in {self.__class__.__name__}')
        return []
