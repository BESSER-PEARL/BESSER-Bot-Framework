import logging
from typing import Any, TYPE_CHECKING

from besser.bot import nlp
from besser.bot.core.property import Property
from besser.bot.nlp.intent_classifier.intent_classifier import IntentClassifier
from besser.bot.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction, \
    fallback_intent_prediction
from besser.bot.nlp.intent_classifier.simple_intent_classifier import SimpleIntentClassifier
from besser.bot.nlp.ner.simple_ner import SimpleNER

if TYPE_CHECKING:
    from besser.bot.core.bot import Bot


class NLPEngine:

    def __init__(self, bot: 'Bot'):
        self._bot: 'Bot' = bot
        self._intent_classifiers: list[IntentClassifier] = {}
        self._ner = None

    @property
    def ner(self):
        return self._ner

    def initialize(self):
        for state in self._bot.states:
            if state not in self._intent_classifiers and state.intents:
                self._intent_classifiers[state] = SimpleIntentClassifier(self, state)
        self._ner = SimpleNER(self, self._bot)

    def get_property(self, prop: Property) -> Any:
        """Get a NLP property's value from the NLPEngine's bot.

        Args:
            prop (Property): the property to get its value

        Returns:
            Any: the property value, or None if the property is not an NLP property
        """
        if prop.section != nlp.SECTION_NLP:
            return None
        return self._bot.get_property(prop)

    def train(self):
        self._ner.train()
        logging.info(f"NER successfully trained.")
        for state, intent_classifier in self._intent_classifiers.items():
            if not state.intents:
                logging.info(f"Intent classifier in {state.name} not trained (no intents found).")
            else:
                intent_classifier.train()
                logging.info(f"Intent classifier in {state.name} successfully trained.")

    def predict_intent(self, session):
        message = session.message
        intent_classifier = self._intent_classifiers[session.current_state]
        intent_classifier_predictions: list[IntentClassifierPrediction] = intent_classifier.predict(message)
        best_intent_prediction = self.get_best_intent_prediction(session, intent_classifier_predictions)

        return best_intent_prediction

    def get_best_intent_prediction(self, session, intent_classifier_predictions: list[IntentClassifierPrediction]):
        fallback = fallback_intent_prediction(session.message)
        best_intent_prediction: IntentClassifierPrediction
        if not intent_classifier_predictions:
            best_intent_prediction = fallback
        else:
            best_intent_prediction = intent_classifier_predictions[0]
        for intent_prediction in intent_classifier_predictions[1:]:
            if intent_prediction.score > best_intent_prediction.score:
                best_intent_prediction = intent_prediction
        intent_threshold: float = self.get_property(nlp.NLP_INTENT_THRESHOLD)
        if best_intent_prediction.score < intent_threshold:
            best_intent_prediction = fallback
            best_intent_prediction.score = intent_threshold
        return best_intent_prediction
