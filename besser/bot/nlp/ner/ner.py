from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from besser.bot.nlp.ner.ner_prediction import NERPrediction

if TYPE_CHECKING:
    from besser.bot.core.bot import Bot
    from besser.bot.core.state import State
    from besser.bot.nlp.nlp_engine import NLPEngine


class NER(ABC):
    """The NER (Named Entity Recognition) abstract class.

    The NER component is in charge of identifying entities in a text, particularly in a user message.

    Args:
        nlp_engine (NLPEngine): the NLPEngine that handles the NLP processes of the bot
        bot (Bot): the bot the NER belongs to

    Attributes:
        _nlp_engine (): The NLPEngine that handles the NLP processes of the bot
        _bot (): The bot the NER belongs to
    """
    def __init__(self, nlp_engine: 'NLPEngine', bot: 'Bot'):
        self._nlp_engine = nlp_engine
        self._bot = bot

    @abstractmethod
    def train(self) -> None:
        """Train the NER."""
        pass

    @abstractmethod
    def predict(self, state: 'State', message: str) -> NERPrediction:
        """
        Predict the entities of a given message.

        Args:
            state (State): the state where the user is in. It is necessary to know the entities that can be matched
                (not all entities can be matched from a specific state, only those of the state's intents)
            message (str): the message to predict the entities

        Returns:
            NERPrediction: the result of the NER prediction
        """
        pass
