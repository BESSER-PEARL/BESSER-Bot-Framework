from besser.agent.core.intent.intent import Intent
from besser.agent.library.intent.intent_library import fallback_intent
from besser.agent.nlp.ner.matched_parameter import MatchedParameter


class IntentClassifierPrediction:
    """The prediction result of an Intent Classifier for a specific intent.
    
    The intent classifier tries to determine the intent of a user message. For each possible intent, it will return
    an IntentClassifierPrediction containing the results, that include the probability itself and other information.

    Args:
        intent (Intent): the target intent of the prediction
        score (float): the probability that this is the actual intent of the user message
        matched_sentence (str): the sentence used in the intent classifier (the original user message is previously
            processed, is modified by the NER, etc.)
        matched_parameters (list[MatchedParameter]): the list of parameters (i.e. entities) found in the user message

    Attributes:
        intent (Intent): The target intent of the prediction
        score (float): The probability that this is the message intent
        matched_sentence (str): The sentence used in the intent classifier (the original user message is previously
            processed, is modified by the NER, etc.)
        matched_parameters (list[MatchedParameter]): The list of parameters (i.e. entities) found in the user message
    """

    def __init__(
            self,
            intent: Intent,
            score: float = None,
            matched_sentence: str = None,
            matched_parameters: list[MatchedParameter] = None
    ):
        self.intent: Intent = intent
        self.score: float = score
        self.matched_sentence: str = matched_sentence
        self.matched_parameters: list[MatchedParameter] = matched_parameters

    def get_parameter(self, name: str) -> MatchedParameter or None:
        """Get a parameter from the intent classifier prediction.

        Args:
            name (str): the name of the parameter to get

        Returns:
            MatchedParameter or None: the parameter if it exists, None otherwise
        """
        for parameter in self.matched_parameters:
            if parameter.name == name:
                return parameter
        return None


def fallback_intent_prediction(message: str) -> IntentClassifierPrediction:
    """Return a *fallback intent prediction* for when none of the possible intents is matched.

    Args:
        message (str): the user message

    Returns:
        IntentClassifierPrediction: the fallback intent classifier prediction
    """
    return IntentClassifierPrediction(
                intent=fallback_intent,
                score=1,
                matched_sentence=message,
                matched_parameters=[])
