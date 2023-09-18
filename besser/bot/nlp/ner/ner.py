from abc import ABC, abstractmethod

from besser.bot.core.state import State
from besser.bot.nlp.ner.ner_prediction import NERPrediction


class NER(ABC):

    def __init__(self, nlp_engine, bot):
        self._nlp_engine = nlp_engine
        self._bot = bot

    @abstractmethod
    def train(self) -> None:
        pass

    @abstractmethod
    def predict(self, state: State, message: str) -> NERPrediction:
        pass
