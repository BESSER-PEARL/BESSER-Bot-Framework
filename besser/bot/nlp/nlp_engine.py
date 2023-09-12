import logging

from besser.bot.nlp.nlp_configuration import NLPConfiguration
from besser.bot.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction, \
    fallback_intent_prediction
from besser.bot.nlp.intent_classifier.simple_intent_classifier import SimpleIntentClassifier
from besser.bot.nlp.ner.simple_ner import SimpleNER
from besser.bot.nlp.preprocessing.text_preprocessing import preprocess_text, preprocess_custom_entity_entries


class NLPEngine:

    def __init__(self, bot):
        self._bot = bot
        self._configuration: NLPConfiguration = NLPConfiguration()
        self._intent_classifiers = {}
        self._intent_threshold = 0.4
        self._ner = SimpleNER(self, self._bot)

    @property
    def configuration(self):
        return self._configuration
    
    def set_language(self, country):
        self._configuration.country = country

    @property
    def ner(self):
        return self._ner

    def initialize(self):
        for state in self._bot.states:
            if state not in self._intent_classifiers and state.intents:
                self._intent_classifiers[state] = SimpleIntentClassifier(self, state)

    def train(self):
        for entity in self._bot.entities:
            if not entity.base_entity:
                preprocess_custom_entity_entries(entity, self._configuration)
        for state, intent_classifier in self._intent_classifiers.items():
            if not state.intents:
                logging.info(f"Intent classifier in {state.name} not trained (no intents found).")
            else:
                intent_classifier.train()
                logging.info(f"Intent classifier in {state.name} successfully trained.")

    def predict_intent(self, session):
        message = session.message
        message = preprocess_text(message, self._configuration)
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
        if best_intent_prediction.score < self._intent_threshold:
            best_intent_prediction = fallback
            best_intent_prediction.score = self._intent_threshold
        return best_intent_prediction
