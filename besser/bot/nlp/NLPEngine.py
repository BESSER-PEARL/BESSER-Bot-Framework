import logging

from besser.bot.nlp.NLPConfiguration import NLPConfiguration
from besser.bot.nlp.intent_classifier.IntentClassifierPrediction import IntentClassifierPrediction, \
    fallback_intent_prediction
from besser.bot.nlp.intent_classifier.SimpleIntentClassifier import SimpleIntentClassifier
from besser.bot.nlp.ner.SimpleNER import SimpleNER
from besser.bot.nlp.preprocessing.text_preprocessing import preprocess_text, preprocess_custom_entity_entries


class NLPEngine:

    def __init__(self, bot):
        self.bot = bot
        self.configuration: NLPConfiguration = NLPConfiguration()
        self.intent_classifiers = {}
        self.intent_threshold = 0.4
        self.ner = SimpleNER(self, self.bot)

    def initialize(self):
        for state in self.bot.states:
            if state not in self.intent_classifiers and state.intents:
                self.intent_classifiers[state] = SimpleIntentClassifier(self, state)

    def train(self):
        for entity in self.bot.entities:
            if not entity.base_entity:
                preprocess_custom_entity_entries(entity, self.configuration)
        for state, intent_classifier in self.intent_classifiers.items():
            if not state.intents:
                logging.info(f"Intent classifier in {state.name} not trained (no intents found).")
            else:
                intent_classifier.train()
                logging.info(f"Intent classifier in {state.name} successfully trained.")

    def predict_intent(self, session):
        message = session.get_message()
        message = preprocess_text(message, self.configuration)
        intent_classifier = self.intent_classifiers[session.current_state]
        intent_classifier_predictions: list[IntentClassifierPrediction] = intent_classifier.predict(message)
        best_intent_prediction = self.get_best_intent_prediction(session, intent_classifier_predictions)

        return best_intent_prediction

    def get_best_intent_prediction(self, session, intent_classifier_predictions: list[IntentClassifierPrediction]):
        fallback = fallback_intent_prediction(session.get_message())
        best_intent_prediction: IntentClassifierPrediction
        if not intent_classifier_predictions:
            best_intent_prediction = fallback
        else:
            best_intent_prediction = intent_classifier_predictions[0]
        for intent_prediction in intent_classifier_predictions[1:]:
            if intent_prediction.score > best_intent_prediction.score:
                best_intent_prediction = intent_prediction
        if best_intent_prediction.score < self.intent_threshold:
            best_intent_prediction = fallback
            best_intent_prediction.score = self.intent_threshold
        return best_intent_prediction
