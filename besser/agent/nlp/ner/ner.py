from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from besser.agent.nlp.ner.ner_prediction import NERPrediction

if TYPE_CHECKING:
    from besser.agent.core.agent import Agent
    from besser.agent.core.state import State
    from besser.agent.nlp.nlp_engine import NLPEngine


class NER(ABC):
    """The NER (Named Entity Recognition) abstract class.

    The NER component is in charge of identifying entities in a text, particularly in a user message.

    Args:
        nlp_engine (NLPEngine): the NLPEngine that handles the NLP processes of the agent
        agent (Agent): the agent the NER belongs to

    Attributes:
        _nlp_engine (): The NLPEngine that handles the NLP processes of the agent
        _agent (): The agent the NER belongs to
    """
    def __init__(self, nlp_engine: 'NLPEngine', agent: 'Agent'):
        self._nlp_engine = nlp_engine
        self._agent = agent

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
