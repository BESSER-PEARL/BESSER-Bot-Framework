import inspect
import json
import logging
import os
import subprocess
import threading
from typing import TYPE_CHECKING

from pandas import DataFrame
from websockets.exceptions import ConnectionClosedError
from websockets.sync.server import ServerConnection, WebSocketServer, serve

from besser.bot.core.session import Session
from besser.bot.exceptions.exceptions import PlatformMismatchError
from besser.bot.platforms import websocket
from besser.bot.platforms.payload import Payload, PayloadAction, PayloadEncoder
from besser.bot.platforms.platform import Platform
from besser.bot.platforms.websocket import streamlit_ui

if TYPE_CHECKING:
    from besser.bot.core.bot import Bot


class WebSocketPlatform(Platform):
    """The WebSocket Platform allows a bot to communicate with the users using the
    `WebSocket <https://en.wikipedia.org/wiki/WebSocket>`_ bidirectional communications protocol.

    This platform implements the WebSocket server, and it can establish connection with a client, allowing the
    bidirectional communication between server and client (i.e. sending and receiving messages).

    Note:
        We provide a UI (:doc:`streamlit_ui`) implementing a WebSocket client to communicate with the bot, though you
        can use or create your own UI as long as it has a WebSocket client that connects to the bot's WebSocket server.

    Args:
        bot (Bot): the bot the platform belongs to
        use_ui (bool): weather to use the built-in UI or not

    Attributes:
        _bot (Bot): The bot the platform belongs to
        _host (str): The WebSocket host address (e.g. `localhost`)
        _port (int): The WebSocket port (e.g. `8765`)
        _use_ui (bool): Weather to use the built-in UI or not
        _connections (dict[str, ServerConnection]): The list of active connections (i.e. users connected to the bot)
        _websocket_server (WebSocketServer): The WebSocket server instance
    """

    def __init__(self, bot: 'Bot', use_ui: bool = True):
        super().__init__()
        self._bot: 'Bot' = bot
        self._host: str = self._bot.get_property(websocket.WEBSOCKET_HOST)
        self._port: int = self._bot.get_property(websocket.WEBSOCKET_PORT)
        self._use_ui: bool = use_ui
        self._connections: dict[str, ServerConnection] = {}

        def message_handler(conn: ServerConnection) -> None:
            """This method is run on each user connection to handle incoming messages and the bot sessions.

            Args:
                conn (ServerConnection): the user connection
            """
            self._connections[str(conn.id)] = conn
            session = self._bot.new_session(str(conn.id), self)
            try:
                for payload_str in conn:
                    payload: Payload = Payload.decode(payload_str)
                    if payload.action == PayloadAction.USER_MESSAGE.value:
                        self._bot.receive_message(session.id, payload.message)
                    elif payload.action == PayloadAction.RESET.value:
                        self._bot.reset(session.id)
            except ConnectionClosedError:
                logging.error(f'The client closed unexpectedly')
            except Exception as e:
                logging.error("Server Error:", e)
            finally:
                logging.info(f'Session finished')
                self._bot.delete_session(session.id)

        self._websocket_server: WebSocketServer = serve(message_handler, self._host, self._port)

    def run(self) -> None:
        if self._use_ui:
            def run_streamlit() -> None:
                """Run the Streamlit UI in a dedicated thread."""
                subprocess.run(["streamlit", "run", os.path.abspath(inspect.getfile(streamlit_ui)),
                                "--server.address", self._bot.get_property(websocket.STREAMLIT_HOST),
                                "--server.port", str(self._bot.get_property(websocket.STREAMLIT_PORT))])

            thread = threading.Thread(target=run_streamlit)
            logging.info(f'Running Streamlit UI in another thread')
            thread.start()
        logging.info(f'{self._bot.name}\'s WebSocketPlatform starting at ws://{self._host}:{self._port}')
        self._websocket_server.serve_forever()

    def _send(self, session_id, payload: Payload) -> None:
        conn = self._connections[session_id]
        conn.send(json.dumps(payload, cls=PayloadEncoder))

    def reply(self, session: Session, message: str) -> None:
        if session.platform is not self:
            raise PlatformMismatchError(self, session)
        session.chat_history.append((message, 0))
        payload = Payload(action=PayloadAction.BOT_REPLY_STR,
                          message=message)
        self._send(session.id, payload)

    def reply_dataframe(self, session: Session, df: DataFrame) -> None:
        """Send a DataFrame bot reply, i.e. a table, to a specific user.

        Args:
            session (Session): the user session
            df (DataFrame): the message to send to the user
        """
        message = df.to_json()
        session.chat_history.append((message, 0))
        payload = Payload(action=PayloadAction.BOT_REPLY_DF,
                          message=message)
        self._send(session.id, payload)
