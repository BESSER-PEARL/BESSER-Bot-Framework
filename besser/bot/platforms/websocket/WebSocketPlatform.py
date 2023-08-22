import inspect
import json
import logging
import os
import subprocess
import threading

from pandas import DataFrame
from websockets.exceptions import ConnectionClosedError
from websockets.sync.server import ServerConnection, serve

from besser.bot.core.Session import Session
from besser.bot.exceptions.exceptions import PlatformMismatchError
from besser.bot.platforms.Payload import Payload, PayloadEncoder
from besser.bot.platforms.Platform import Platform
from besser.bot.platforms.websocket import StreamlitUI


class WebSocketPlatform(Platform):

    def __init__(self, bot, use_ui):
        self.bot = bot
        self.host = None
        self.port = None
        self.websocket_server = None
        self.use_ui = use_ui
        self.connections = {}

    def initialize(self):
        self.host = self.bot.config.get('websocket', 'host', fallback='localhost')
        self.port = self.bot.config.getint('websocket', 'port', fallback=8765)

        def message_handler(conn: ServerConnection):
            self.connections[conn.id] = conn
            session = self.bot.new_session(conn.id, self)
            try:
                for payload_str in conn:
                    payload: Payload = Payload.decode(payload_str)
                    if payload.action == Payload.USER_MESSAGE:
                        self.bot.receive_message(session.id, payload.message)
                    elif payload.action == Payload.RESET:
                        self.bot.reset(session.id)
            except ConnectionClosedError:
                logging.error(f'The client closed unexpectedly')
            except Exception as e:
                logging.error("Server Error:", e)
            finally:
                logging.info(f'Session finished')
                self.bot.delete_session(session.id)

        self.websocket_server = serve(message_handler, self.host, self.port)

    def run(self):
        if self.use_ui:
            def run_streamlit():
                subprocess.run(["streamlit", "run", os.path.abspath(inspect.getfile(StreamlitUI)),
                                "--server.address", self.bot.config.get('ui', 'host', fallback='localhost'),
                                "--server.port", self.bot.config.get('ui', 'port', fallback='5000')])

            thread = threading.Thread(target=run_streamlit)
            logging.info(f'Running Streamlit UI in another thread')
            thread.start()
        logging.info(f'{self.bot.name}\'s WebSocketPlatform starting at ws://{self.host}:{self.port}')
        self.websocket_server.serve_forever()

    def _send(self, session_id, payload: Payload):
        conn = self.connections[session_id]
        conn.send(json.dumps(payload, cls=PayloadEncoder))

    def reply(self, session: Session, message: str):
        if session.platform is not self:
            raise PlatformMismatchError(self, session)
        session.chat_history.append((message, 0))
        payload = Payload(action=Payload.BOT_REPLY_STR,
                          message=message)
        self._send(session.id, payload)

    def reply_dataframe(self, session: Session, df: DataFrame):
        message = df.to_json()
        session.chat_history.append((message, 0))
        payload = Payload(action=Payload.BOT_REPLY_DF,
                          message=message)
        self._send(session.id, payload)
