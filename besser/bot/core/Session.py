import json

from pandas import DataFrame
from websockets.sync.server import ServerConnection

from besser.bot.server.Payload import Payload, PayloadEncoder
from besser.bot.nlp.intent_classifier.IntentClassifierPrediction import IntentClassifierPrediction


class Session:

    def __init__(self, conn, current_state):
        self.conn: ServerConnection = conn
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
        self.chat_history.append((message, 0))
        payload = Payload(action=Payload.BOT_REPLY_STR,
                          message=message)
        self.conn.send(json.dumps(payload, cls=PayloadEncoder))

    def reply_dataframe(self, df: DataFrame):
        message = df.to_json()
        self.chat_history.append((message, 0))
        payload = Payload(action=Payload.BOT_REPLY_DF,
                          message=message)
        self.conn.send(json.dumps(payload, cls=PayloadEncoder))
