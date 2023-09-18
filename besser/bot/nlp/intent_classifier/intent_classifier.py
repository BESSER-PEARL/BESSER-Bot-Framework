from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from besser.bot.core.state import State
from besser.bot.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction

if TYPE_CHECKING:
    from besser.bot.nlp.nlp_engine import NLPEngine


class IntentClassifier(ABC):

    def __init__(self, nlp_engine: 'NLPEngine', state: State):
        self._nlp_engine: 'NLPEngine' = nlp_engine
        self._state = state

    @abstractmethod
    def train(self) -> None:
        pass

    @abstractmethod
    def predict(self, message: str) -> list[IntentClassifierPrediction]:
        pass
