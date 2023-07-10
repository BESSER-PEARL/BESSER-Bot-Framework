from besser.bot.core.intent.Intent import Intent
from besser.bot.library.intent.IntentLibrary import fallback_intent
from besser.bot.nlp.intent_classifier.MatchedParameter import MatchedParameter


class IntentClassifierPrediction:

    def __init__(self, intent: Intent, score: float = None, matched_utterance: str = None,
                 matched_parameters: list[MatchedParameter] = None):
        self.intent: Intent = intent
        self.score: float = score
        self.matched_utterance: str = matched_utterance
        self.matched_parameters: list[MatchedParameter] = matched_parameters

    def get_parameter(self, name: str):
        for parameter in self.matched_parameters:
            if parameter.name == name:
                return parameter
        return None


def fallback_intent_prediction(message: str):
    return IntentClassifierPrediction(
                intent=fallback_intent,
                score=1,
                matched_utterance=message,
                matched_parameters=[])
