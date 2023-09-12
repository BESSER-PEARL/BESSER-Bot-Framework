from abc import ABC, abstractmethod

from besser.bot.core.state import State
from besser.bot.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction


class IntentClassifier(ABC):

    def __init__(self, state: State):
        self._state = state

    @abstractmethod
    def train(self) -> None:
        pass

    @abstractmethod
    def predict(self, message: str) -> list[IntentClassifierPrediction]:
        pass
