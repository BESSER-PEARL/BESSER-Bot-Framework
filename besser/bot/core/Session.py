import json

from besser.bot.nlp.intent_classifier.IntentClassifierPrediction import IntentClassifierPrediction


class Session:

    def __init__(self):
        self.user_id = 1
        self.dictionary = {}
        self.predicted_intent = None
        self.message = None
        self.answer = []
        self.history = []

    def set(self, key, value):
        self.dictionary[key] = value

    def put_answer(self, value):
        self.answer.append(value)

    def clear_answer(self):
        self.answer = []

    def get(self, key):
        return self.dictionary[key]

    def delete(self, key):
        del self.dictionary[key]

    def update_history(self):
        last_message = self.get_message()
        if last_message is not None:
            self.history.append((last_message, 1))
        self.history.extend([(m, 0) for m in self.answer])

    def set_predicted_intent(self, prediction: IntentClassifierPrediction):
        self.predicted_intent = prediction

    def get_predicted_intent(self):
        return self.predicted_intent

    def set_message(self, message: str):
        self.message = message

    def get_message(self):
        return self.message


class SessionEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Session):
            # Convert the Session object to a dictionary
            session_dict = {
                'dictionary': obj.dictionary,
                'user_id': obj.user_id,
                'message': obj.message,
                'answer': obj.answer,
                'history': obj.history
            }
            return session_dict
        return super().default(obj)
