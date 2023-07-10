import json
import threading

from flask import Flask, request

from besser.bot.core.Session import SessionEncoder


class RequestDispatcher:

    def __init__(self, bot):
        self.bot = bot
        self.app = Flask(__name__)
        self.app.add_url_rule('/message', view_func=self.receive_message, methods=['POST'])
        self.app.add_url_rule('/history', view_func=self.history, methods=['POST'])
        self.app.add_url_rule('/reset', view_func=self.reset, methods=['POST'])

    def run(self):
        client_thread = threading.Thread(target=self.app.run)
        client_thread.start()

    def receive_message(self):
        message = request.json.get('message')
        self.bot.session.set_message(message)
        self.bot.session.clear_answer()
        self.bot.receive_message()
        self.bot.session.update_history()
        return json.dumps(self.bot.session, cls=SessionEncoder)

    def history(self):
        return json.dumps(self.bot.session, cls=SessionEncoder)

    def reset(self):
        self.bot.reset()
        return json.dumps(self.bot.session, cls=SessionEncoder)
