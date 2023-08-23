import inspect
import json
import logging
import os
import subprocess
import threading

from pandas import DataFrame
from websockets.exceptions import ConnectionClosedError
from websockets.sync.server import ServerConnection, serve

from besser.bot.core.session import Session
from besser.bot.exceptions.exceptions import PlatformMismatchError
from besser.bot.platforms.payload import Payload, PayloadEncoder
from besser.bot.platforms.platform import Platform
from besser.bot.platforms.websocket import streamlit_ui


class WebSocketPlatform(Platform):

    def __init__(self, bot, use_ui):
        super().__init__()
        self._bot = bot
        self._host = self._bot.config.get('websocket', 'host', fallback='localhost')
        self._port = self._bot.config.getint('websocket', 'port', fallback=8765)
        self._websocket_server = None
        self._use_ui = use_ui
        self._connections = {}

        def message_handler(conn: ServerConnection):
            self._connections[conn.id] = conn
            session = self._bot.new_session(conn.id, self)
            try:
                for payload_str in conn:
                    payload: Payload = Payload.decode(payload_str)
                    if payload.action == Payload.USER_MESSAGE:
                        self._bot.receive_message(session.id, payload.message)
                    elif payload.action == Payload.RESET:
                        self._bot.reset(session.id)
            except ConnectionClosedError:
                logging.error(f'The client closed unexpectedly')
            except Exception as e:
                logging.error("Server Error:", e)
            finally:
                logging.info(f'Session finished')
                self._bot.delete_session(session.id)

        self._websocket_server = serve(message_handler, self._host, self._port)

    def run(self):
        if self._use_ui:
            def run_streamlit():
                subprocess.run(["streamlit", "run", os.path.abspath(inspect.getfile(streamlit_ui)),
                                "--server.address", self._bot.config.get('ui', 'host', fallback='localhost'),
                                "--server.port", self._bot.config.get('ui', 'port', fallback='5000')])

            thread = threading.Thread(target=run_streamlit)
            logging.info(f'Running Streamlit UI in another thread')
            thread.start()
        logging.info(f'{self._bot.name}\'s WebSocketPlatform starting at ws://{self._host}:{self._port}')
        self._websocket_server.serve_forever()

    def _send(self, session_id, payload: Payload):
        conn = self._connections[session_id]
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
