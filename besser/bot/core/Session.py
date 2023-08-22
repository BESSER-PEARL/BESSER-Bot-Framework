from besser.bot.nlp.intent_classifier.IntentClassifierPrediction import IntentClassifierPrediction
from besser.bot.platforms.Platform import Platform


class Session:

    def __init__(self, session_id, bot, platform, current_state):
        self.id = session_id
        self.bot = bot
        self.platform: Platform = platform
        self.current_state = current_state
        self.dictionary = {}
        self.predicted_intent = None
        self.message = None
        self.answer = []
        self.chat_history = []

    def set(self, key, value):
        self.dictionary[key] = value

    def get(self, key):
        return self.dictionary[key]

    def delete(self, key):
        del self.dictionary[key]

    def set_predicted_intent(self, prediction: IntentClassifierPrediction):
        self.predicted_intent = prediction

    def get_predicted_intent(self):
        return self.predicted_intent

    def set_message(self, message: str):
        self.chat_history.append((message, 1))
        self.message = message

    def get_message(self):
        return self.message

    def reply(self, message: str):
        # Multi-platform
        self.platform.reply(self, message)
