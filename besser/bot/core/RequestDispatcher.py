import json
import threading

from flask import Flask, request

from besser.bot.core.Session import SessionEncoder


class RequestDispatcher:

    def __init__(self, bot):
        self.bot = bot
        self.app = Flask(__name__)
        self.app.add_url_rule('/new_session', view_func=self.new_session, methods=['POST'])
        self.app.add_url_rule('/message', view_func=self.receive_message, methods=['POST'])
        self.app.add_url_rule('/session', view_func=self.session, methods=['POST'])
        self.app.add_url_rule('/reset', view_func=self.reset, methods=['POST'])

    def run(self):
        client_thread = threading.Thread(target=self.app.run)
        client_thread.start()

    def new_session(self):
        user_id = request.json.get('user_id')
        session = self.bot.new_session(user_id)
        return json.dumps(session, cls=SessionEncoder)

    def receive_message(self):
        message = request.json.get('message')
        user_id = request.json.get('user_id')
        session = self.bot.receive_message(user_id, message)
        return json.dumps(session, cls=SessionEncoder)

    def session(self):
        user_id = request.json.get('user_id')
        return json.dumps(self.bot.get_session(user_id), cls=SessionEncoder)

    def reset(self):
        user_id = request.json.get('user_id')
        session = self.bot.reset(user_id)
        return json.dumps(session, cls=SessionEncoder)
