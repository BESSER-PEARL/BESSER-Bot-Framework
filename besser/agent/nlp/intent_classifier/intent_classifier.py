from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from besser.agent.exceptions.exceptions import IntentClassifierWithoutIntentsError
from besser.agent.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction

if TYPE_CHECKING:
    from besser.agent.nlp.nlp_engine import NLPEngine
    from besser.agent.core.state import State


class IntentClassifier(ABC):
    """The Intent Classifier abstract class.

    An intent classifier is in charge of determining the intent of a user message. Given a text (a user message) and a
    set of intents, the intent classifier predicts the probability of each intent to be the actual message's intent.

    The intent classifier belongs to a specific agent state, thus the predicted intent will always be one of the state's
    intents. Therefore, the state must have at least 1 intent.

    This class serves as a template to implement intent classifiers.

    Args:
        nlp_engine (NLPEngine): the NLPEngine that handles the NLP processes of the agent
        state (State): the state the intent classifier belongs to

    Attributes:
        _nlp_engine (NLPEngine): The NLPEngine that handles the NLP processes of the agent.
        _state (State): The state the intent classifier belongs to.
    """

    def __init__(
            self,
            nlp_engine: 'NLPEngine',
            state: 'State'
    ):
        if not state.intents:
            raise IntentClassifierWithoutIntentsError(state, self)
        self._nlp_engine: 'NLPEngine' = nlp_engine
        self._state = state

    @abstractmethod
    def train(self) -> None:
        """Train the intent classifier."""
        pass

    @abstractmethod
    def predict(self, message: str) -> list[IntentClassifierPrediction]:
        """Predict the intent of a given message.

        Instead of returning only the intent with the highest likelihood, return all predictions. Predictions include
        not only the intent scores but other information extracted from the message.

        Args:
            message (str): the message to predict the intent

        Returns:
            list[IntentClassifierPrediction]: the list of predictions made by the intent classifier.
        """
        pass
