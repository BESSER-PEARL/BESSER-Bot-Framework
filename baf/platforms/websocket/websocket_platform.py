from __future__ import annotations

import base64
import inspect
import json
import os
import time
import traceback
from datetime import datetime
from urllib.parse import parse_qs, urlsplit

import numpy as np
import subprocess
import threading
from typing import TYPE_CHECKING

from besser.BUML.metamodel.gui import GUIModel
from pandas import DataFrame
from websockets.exceptions import ConnectionClosedError
from websockets.sync.server import ServerConnection, WebSocketServer, serve

from baf.core.gui.gui_serializer import gui_to_json
from baf.library.transition.events.base_events import ReceiveMessageEvent, ReceiveFileEvent
from baf.core.message import Message, MessageType
from baf.core.session import Session
from baf.exceptions.exceptions import PlatformMismatchError, StreamlitDatabaseException
from baf.exceptions.logger import logger
from baf.nlp.rag.rag import RAGMessage
from baf.platforms import websocket
from baf.platforms.payload import Payload, PayloadAction, PayloadEncoder
from baf.platforms.platform import Platform
from baf.platforms.websocket.streamlit_ui import streamlit_ui
from baf.core.file import File
from baf.platforms.websocket.streamlit_ui import (
    DB_STREAMLIT_HOST,
    DB_STREAMLIT_PORT,
    DB_STREAMLIT_DATABASE,
    DB_STREAMLIT_USERNAME,
    DB_STREAMLIT_PASSWORD,
    DB_STREAMLIT,
)


def _extract_parameter_from_request(parameter, request) -> str | None:
    if not request:
        return None
    for attr in ("path", "raw_path", "uri"):
        value = getattr(request, attr, None)
        if not value:
            continue
        if isinstance(value, bytes):
            # Prefer UTF-8 for URL paths; fall back to latin-1 to remain robust to non-UTF-8 bytes.
            try:
                value = value.decode("utf-8")
            except UnicodeDecodeError:
                value = value.decode("latin-1", errors="replace")
        query = urlsplit(value).query
        if not query:
            continue
        params = parse_qs(query)
        user_values = params.get(parameter)
        if user_values:
            return user_values[0]
    return None


if TYPE_CHECKING:
    from baf.core.agent import Agent

try:
    import cv2
except ImportError:
    logger.warning("cv2 dependencies in WebSocketPlatform could not be imported. You can install them from "
                   "the requirements/requirements-extras.txt file")
try:
    import plotly
except ImportError:
    logger.warning("plotly dependencies in WebSocketPlatform could not be imported. You can install them from "
                   "the requirements/requirements-extras.txt file")

try:
    import librosa
except ImportError:
    logger.warning("librosa dependencies in WebSocketPlatform could not be imported. You can install them from "
                   "the requirements/requirements-extras.txt file")


class WebSocketPlatform(Platform):
    """The WebSocket Platform allows an agent to communicate with the users using the
    `WebSocket <https://en.wikipedia.org/wiki/WebSocket>`_ bidirectional communications protocol.

    This platform implements the WebSocket server, and it can establish connection with a client, allowing the
    bidirectional communication between server and client (i.e. sending and receiving messages).

    Note:
        We provide different interfaces implementing a WebSocket client to communicate with the agent, though you
        can use or create your own UI as long as it has a WebSocket client that connects to the agent's WebSocket server.

    Args:
        agent (Agent): the agent the platform belongs to
        use_ui (bool): whether to use the built-in UI or not
        authenticate_users (bool): whether to authenticate users when they connect to the agent and load their chat 
            history

    Attributes:
        _agent (Agent): The agent the platform belongs to
        _host (str): The WebSocket host address (e.g. `localhost`)
        _port (int): The WebSocket port (e.g. `8765`)
        _use_ui (bool): Whether to use the built-in UI or not
        _connections (dict[str, ServerConnection]): The list of active connections (i.e. users connected to the agent)
        _websocket_server (WebSocketServer or None): The WebSocket server instance
        _message_handler (Callable[[ServerConnection], None]): The function that handles the user connections
            (sessions) and incoming messages
    """

    def __init__(
            self,
            agent: 'Agent',
            use_ui: bool = True,
            authenticate_users: bool = False,
    ):
        super().__init__()
        self._agent: 'Agent' = agent
        self._host: str = None
        self._port: int = None
        self._use_ui: bool = use_ui
        self._authenticate_users = authenticate_users
        self._connections: dict[str, ServerConnection] = {}
        self._websocket_server: WebSocketServer = None

        def message_handler(conn: ServerConnection) -> None:
            """This method is run on each user connection to handle incoming messages and the agent sessions.

            Args:
                conn (ServerConnection): the user connection
            """
            session: Session = None
            current_time = datetime.now()
            request = getattr(conn, "request", None)
            headers = getattr(request, "headers", {}) if request else {}
            header_user = headers.get("X-User-ID") if hasattr(headers, "get") else None
            header_session = headers.get("X-Session-ID") if hasattr(headers, "get") else None
            query_user = _extract_parameter_from_request('user_id', request)
            query_session = _extract_parameter_from_request('session_id', request)
            query_session_name = _extract_parameter_from_request('session_name', request)
            username = header_user or query_user
            session_key = header_session or query_session or str(conn.id)
            session_name = query_session_name
            self._connections[str(session_key)] = conn
            session = self._agent.get_or_create_session(session_key, self, username, session_name)
            try:

                for payload_str in conn:
                    if not self.running:
                        raise ConnectionClosedError(None, None)
                    payload: Payload = Payload.decode(payload_str)
                    if payload.action == PayloadAction.USER_UPDATE_UI.value:
                        logger.info(f'Received event: {payload_str}')  # TODO: Not implemented
                    elif payload.action == PayloadAction.FETCH_USER_MESSAGES.value:
                        try:
                            chat_history = session.get_chat_history(until_timestamp=current_time)
                            reasoning_events = session.get_reasoning_events(until_timestamp=current_time)

                            # Merge both streams in chronological order so the
                            # UI's existing aggregation (reasoning_started /
                            # reasoning_finished brackets, task panel updates)
                            # rebuilds the trace exactly as it was streamed.
                            timeline: list[tuple[datetime, str, object]] = []
                            for message in chat_history:
                                action = message.get_action()
                                if action is None:
                                    # Defensive: skip rows whose MessageType
                                    # has no PayloadAction mapping (would
                                    # crash on .value below).
                                    continue
                                timeline.append((message.timestamp, 'chat',
                                                 (action, message.content, message.timestamp)))
                            for ev in reasoning_events:
                                if ev['kind'] == 'reasoning_step':
                                    action = PayloadAction.AGENT_REPLY_REASONING_STEP
                                elif ev['kind'] == 'task_list_update':
                                    action = PayloadAction.AGENT_REPLY_TASK_LIST_UPDATE
                                else:
                                    continue
                                timeline.append((ev['timestamp'], 'reasoning',
                                                 (action, ev['payload'], ev['timestamp'])))

                            timeline.sort(key=lambda t: t[0])
                            for _, _, item in timeline:
                                action, message_content, ts = item
                                history_payload = Payload(action=action,
                                                          message=message_content,
                                                          history=True,
                                                          timestamp=ts)
                                self._send(session.id, history_payload)
                        except Exception as e:
                            logger.error(f"Error fetching chat history: {e}")
                    elif payload.action == PayloadAction.USER_MESSAGE.value:
                        event: ReceiveMessageEvent = ReceiveMessageEvent.create_event_from(
                            message=payload.message,
                            session=session,
                            human=True)
                        self._agent.receive_event(event)
                    elif payload.action == PayloadAction.USER_VOICE.value:
                        # Decode the base64 string to get audio bytes
                        audio_bytes = base64.b64decode(payload.message.encode('utf-8'))
                        message = self._agent.nlp_engine.speech2text(session, audio_bytes)

                        # Send transcribed message back to the client
                        payload = Payload(action=PayloadAction.USER_MESSAGE, message=message, history=True, timestamp=datetime.now())
                        self._send(session.id, payload)

                        event: ReceiveMessageEvent = ReceiveMessageEvent.create_event_from(
                            message=message,
                            session=session,
                            human=True)
                        self._agent.receive_event(event)
                    elif payload.action == PayloadAction.USER_FILE.value:
                        event: ReceiveFileEvent = ReceiveFileEvent(
                            file=File.decode(payload.message),
                            session_id=session.id,
                            human=True)
                        self._agent.receive_event(event)
                    elif payload.action == PayloadAction.AGENT_REPLY_STR.value:
                        event: ReceiveMessageEvent = ReceiveMessageEvent.create_event_from(
                            message=payload.message,
                            session=session,
                            human=False)
                        self._agent.receive_event(event)
                    elif payload.action == PayloadAction.RESET.value:
                        self._agent.reset(session.id)
                    elif payload.action == PayloadAction.USER_SET_VARIABLE.value:
                        if not isinstance(payload.message, dict) or not payload.message:
                            logger.error('Invalid message format for USER_SET_VARIABLE')
                            continue  # skip this iteration
                        for key, value in payload.message.items():
                            session.set(key, value)
                            logger.info(f"Session variable {key} set to {value}.")
            except ConnectionClosedError:
                logger.info('Client connection closed unexpectedly')
            except Exception as e:
                logger.error(f"Server Error: {e}")
                traceback.print_exc()
            finally:
                # Remove connection from tracking
                if session:
                    session_id = str(session.id)
                    if session_id in self._connections:
                        del self._connections[session_id]
                logger.info('Session finished')
                # self._agent.delete_session(session.id)
                # del self._connections[session.id]

        self._message_handler = message_handler

    def initialize(self) -> None:
        self._host = self._agent.get_property(websocket.WEBSOCKET_HOST)
        self._port = self._agent.get_property(websocket.WEBSOCKET_PORT)
        origins = self._agent.get_property(websocket.WEBSOCKET_ORIGINS)
        self._websocket_server = serve(
            handler=self._message_handler,
            host=self._host,
            port=self._port,
            max_size=self._agent.get_property(websocket.WEBSOCKET_MAX_SIZE),
            origins=origins,
        )

    def start(self) -> None:
        if self._use_ui:
            def run_streamlit() -> None:
                """Run the Streamlit UI in a dedicated thread."""
                if self._authenticate_users:
                    db_host = self._agent.get_property(DB_STREAMLIT_HOST)
                    if not db_host:
                        raise StreamlitDatabaseException("DB_STREAMLIT_HOST")
                    db_port = self._agent.get_property(DB_STREAMLIT_PORT)
                    if not db_port:
                        raise StreamlitDatabaseException("DB_STREAMLIT_PORT")
                    db_name = self._agent.get_property(DB_STREAMLIT_DATABASE)
                    if not db_name:
                        raise StreamlitDatabaseException("DB_STREAMLIT_DATABASE")
                    db_user = self._agent.get_property(DB_STREAMLIT_USERNAME)
                    if not db_user:
                        raise StreamlitDatabaseException("DB_STREAMLIT_USERNAME")
                    db_password = self._agent.get_property(DB_STREAMLIT_PASSWORD)
                    if not db_password:
                        raise StreamlitDatabaseException("DB_STREAMLIT_PASSWORD")
                    db_streamlit = self._agent.get_property(DB_STREAMLIT)
                    if not db_streamlit:
                        raise StreamlitDatabaseException("DB_STREAMLIT")

                    os.environ["STREAMLIT_DB_HOST"] = str(db_host) if db_host else ""
                    os.environ["STREAMLIT_DB_PORT"] = str(db_port) if db_port else ""
                    os.environ["STREAMLIT_DB_NAME"] = str(db_name) if db_name else ""
                    os.environ["STREAMLIT_DB_USER"] = str(db_user) if db_user else ""
                    os.environ["STREAMLIT_DB_PASSWORD"] = str(db_password) if db_password else ""
                    os.environ["STREAMLIT_DB"] = str(db_streamlit) if db_streamlit else "False"

                # Pass user profiles to Streamlit via environment, if available and serializable
                if self._agent.user_profiles is not None:
                    try:
                        os.environ["STREAMLIT_USER_PROFILES_JSON"] = json.dumps(self._agent.user_profiles)
                    except (TypeError, ValueError):
                        logger.warning("Failed to serialize user profiles for Streamlit UI; continuing without them.")

                os.environ["STREAMLIT_AGENT_WORKDIR"] = os.getcwd()

                default_chat_style = {
                    "size": self._agent.get_property(websocket.STREAMLIT_CHAT_DEFAULT_SIZE),
                    "font": self._agent.get_property(websocket.STREAMLIT_CHAT_DEFAULT_FONT),
                    "lineSpacing": self._agent.get_property(websocket.STREAMLIT_CHAT_DEFAULT_LINE_SPACING),
                    "alignment": self._agent.get_property(websocket.STREAMLIT_CHAT_DEFAULT_ALIGNMENT),
                    "color": self._agent.get_property(websocket.STREAMLIT_CHAT_DEFAULT_COLOR),
                    "contrast": self._agent.get_property(websocket.STREAMLIT_CHAT_DEFAULT_CONTRAST),
                }
                os.environ["STREAMLIT_CHAT_INTERFACE_DEFAULT_STYLE_JSON"] = json.dumps(default_chat_style)

                try:
                    raw_configurations = self._agent.agent_configurations

                    if not raw_configurations:
                        import __main__  # noqa: PLC0415
                        main_configurations = getattr(__main__, "agent_configurations", None)
                        if isinstance(main_configurations, dict) and main_configurations:
                            raw_configurations = main_configurations
                            self._agent.set_agent_configurations(main_configurations)

                    if isinstance(raw_configurations, dict) and raw_configurations:
                        os.environ["STREAMLIT_AGENT_CONFIGURATIONS_JSON"] = json.dumps(raw_configurations)
                    else:
                        os.environ.pop("STREAMLIT_AGENT_CONFIGURATIONS_JSON", None)
                except Exception:
                    logger.warning("Failed to serialize agent configurations for Streamlit UI; using defaults.")

                subprocess.run([
                    "streamlit", "run",
                    "--server.address", self._agent.get_property(websocket.STREAMLIT_HOST),
                    "--server.port", str(self._agent.get_property(websocket.STREAMLIT_PORT)),
                    os.path.abspath(inspect.getfile(streamlit_ui)),
                    self._agent.name,
                    self._agent.get_property(websocket.WEBSOCKET_HOST),
                    str(self._agent.get_property(websocket.WEBSOCKET_PORT))
                ])

            thread = threading.Thread(target=run_streamlit)
            logger.info(f'Running Streamlit UI in another thread')
            thread.start()
            # To avoid re-running the streamlit process, set self._use_ui to False
            self._use_ui = False
        logger.info(f'{self._agent.name}\'s WebSocketPlatform starting at ws://{self._host}:{self._port}')
        self.running = True
        self._websocket_server.serve_forever()

    def stop(self):
        self.running = False
        for conn_id in list(self._connections.keys()):
            conn = self._connections[conn_id]
            conn.close_socket()
        try:
            while self._connections:
                time.sleep(0.05)
        except KeyboardInterrupt:
            logger.warning('Interrupted while waiting for WebSocket connections to close; continuing shutdown.')
        self._websocket_server.shutdown()
        logger.info(f'{self._agent.name}\'s WebSocketPlatform stopped')

    def _send(self, session_id, payload: Payload) -> None:
        if session_id in self._connections:
            conn = self._connections[session_id]
            conn.send(json.dumps(payload, cls=PayloadEncoder))

    def reply(self, session: Session, message: str) -> None:
        if session.platform is not self:
            raise PlatformMismatchError(self, session)
        message_obj: Message = Message(t=MessageType.STR, content=message, is_user=False, timestamp=datetime.now())
        session.save_message(message_obj)
        payload = Payload(action=PayloadAction.AGENT_REPLY_STR,
                          message=message,
                          timestamp=message_obj.timestamp)
        payload.message = self._agent.process(session=session, message=payload.message, is_user_message=False)
        self._send(session.id, payload)

    def reply_markdown(self, session: Session, message: str) -> None:
        """Send an agent reply to a specific user, containing text in Markdown format.

        Args:
            session (Session): the user session
            message (str): the message in Markdown format to send to the user
        """
        if session.platform is not self:
            raise PlatformMismatchError(self, session)
        message_obj: Message = Message(t=MessageType.MARKDOWN, content=message, is_user=False, timestamp=datetime.now())
        session.save_message(message_obj)
        payload = Payload(action=PayloadAction.AGENT_REPLY_MARKDOWN,
                          message=message,
                          timestamp=message_obj.timestamp)
        payload.message = self._agent.process(session=session, message=payload.message, is_user_message=False)
        self._send(session.id, payload)

    def reply_html(self, session: Session, message: str) -> None:
        """Send an agent reply to a specific user, containing text in HTML format.

        Args:
            session (Session): the user session
            message (str): the message in HTML format to send to the user
        """
        if session.platform is not self:
            raise PlatformMismatchError(self, session)
        message_obj: Message = Message(t=MessageType.HTML, content=message, is_user=False, timestamp=datetime.now())
        session.save_message(message_obj)
        payload = Payload(action=PayloadAction.AGENT_REPLY_HTML,
                          message=message,
                          timestamp=message_obj.timestamp)
        payload.message = self._agent.process(session=session, message=payload.message, is_user_message=False)
        self._send(session.id, payload)
        
    def reply_file(self, session: Session, file: File) -> None:
        """Send a file reply to a specific user

        Args:
            session (Session): the user session
            file (File): the file to send
        """
        if session.platform is not self:
            raise PlatformMismatchError(self, session)
        message_obj: Message = Message(t=MessageType.FILE, content=file.get_json_string(), is_user=False, timestamp=datetime.now())
        session.save_message(message_obj)
        payload = Payload(action=PayloadAction.AGENT_REPLY_FILE,
                          message=file.to_dict(),
                          timestamp=message_obj.timestamp)
        payload.message = self._agent.process(session=session, message=payload.message, is_user_message=False)
        self._send(session.id, payload)

    def reply_image(self, session: Session, img: np.ndarray) -> None:
        """Send an image reply to a specific user.

        Before being sent, the image is encoded as jpg and then as a base64 string. This must be known before dedocing
        the image on the client side.

        Args:
            session (Session): the user session
            img (np.ndarray): the image to send
        """
        if session.platform is not self:
            raise PlatformMismatchError(self, session)
        retval, buffer = cv2.imencode('.jpg', img)  # Encode as JPEG
        base64_img = base64.b64encode(buffer).decode('utf-8')
        message_obj: Message = Message(t=MessageType.IMAGE, content=base64_img, is_user=False, timestamp=datetime.now())
        session.save_message(message_obj)
        payload = Payload(action=PayloadAction.AGENT_REPLY_IMAGE,
                          message=base64_img,
                          timestamp=message_obj.timestamp)
        payload.message = self._agent.process(session=session, message=payload.message, is_user_message=False)
        self._send(session.id, payload)

    def reply_dataframe(self, session: Session, df: DataFrame) -> None:
        """Send a DataFrame agent reply, i.e. a table, to a specific user.

        Args:
            session (Session): the user session
            df (pandas.DataFrame): the message to send to the user
        """
        if session.platform is not self:
            raise PlatformMismatchError(self, session)
        message = df.to_json() 
        #TODO processor will check for JSON instead of Dataframe, so the processor needs to convert to DF
        message_obj: Message = Message(t=MessageType.DATAFRAME, content=message, is_user=False, timestamp=datetime.now())
        session.save_message(message_obj)
        payload = Payload(action=PayloadAction.AGENT_REPLY_DF,
                          message=message,
                          timestamp=message_obj.timestamp)
        payload.message = self._agent.process(session=session, message=payload.message, is_user_message=False)
        self._send(session.id, payload)

    def reply_options(self, session: Session, options: list[str]):
        """Send a list of options as a reply. They can be used to let the user choose one of them

        Args:
            session (Session): the user session
            options (list[str]): the list of options to send to the user
        """
        if session.platform is not self:
            raise PlatformMismatchError(self, session)
        d = {}
        for i, button in enumerate(options):
            d[i] = button
        #TODO processor should also process the individual strings in the list of strings
        message = json.dumps(d)
        message_obj: Message = Message(t=MessageType.OPTIONS, content=message, is_user=False, timestamp=datetime.now())
        session.save_message(message_obj)
        payload = Payload(action=PayloadAction.AGENT_REPLY_OPTIONS,
                          message=message,
                          timestamp=message_obj.timestamp)
        payload.message = self._agent.process(session=session, message=payload.message, is_user_message=False)
        self._send(session.id, payload)

    def reply_plotly(self, session: Session, plot: plotly.graph_objs.Figure) -> None:
        """Send a Plotly figure as an agent reply, to a specific user.

        Args:
            session (Session): the user session
            plot (plotly.graph_objs.Figure): the message to send to the user
        """
        if session.platform is not self:
            raise PlatformMismatchError(self, session)
        message = plotly.io.to_json(plot)
        message_obj: Message = Message(t=MessageType.PLOTLY, content=message, is_user=False, timestamp=datetime.now())
        session.save_message(message_obj)
        payload = Payload(action=PayloadAction.AGENT_REPLY_PLOTLY,
                          message=message,
                          timestamp=message_obj.timestamp)
        payload.message = self._agent.process(session=session, message=payload.message, is_user_message=False)
        self._send(session.id, payload)

    def reply_location(self, session: Session, latitude: float, longitude: float) -> None:
        """Send a location reply to a specific user.

        Args:
            session (Session): the user session
            latitude (str): the latitude of the location
            longitude (str): the longitude of the location
        """
        if session.platform is not self:
            raise PlatformMismatchError(self, session)
        location_dict = {'latitude': latitude, 'longitude': longitude}
        message_obj: Message = Message(t=MessageType.LOCATION, content=location_dict, is_user=False, timestamp=datetime.now())
        session.save_message(message_obj)
        payload = Payload(action=PayloadAction.AGENT_REPLY_LOCATION,
                          message=location_dict,
                          timestamp=message_obj.timestamp)
        payload.message = self._agent.process(session=session, message=payload.message, is_user_message=False)
        self._send(session.id, payload)

    def reply_task_list_update(self, session: Session, tasks: list) -> None:
        """Send a snapshot of the reasoning state's task list to a specific user.

        Emitted alongside (not in place of) the existing
        ``task_added`` / ``task_completed`` / ``task_skipped`` reasoning step
        events, so a client can render a live "task panel" without having to
        reconstruct the list from the step stream. The
        ``reasoning_started`` / ``reasoning_finished`` reasoning steps bracket
        the lifetime of this panel.

        Persisted in the dedicated ``reasoning_step`` table (kind=
        ``task_list_update``) — not in the chat table — so it does not
        pollute chat history retrieval.

        Args:
            session (Session): the user session.
            tasks (list): the current task list as a list of dicts with shape
                ``{"id": int, "description": str, "status": str, "result": str}``.
                Each call carries the *full* current snapshot — the client
                replaces its state rather than applying a diff.
        """
        if session.platform is not self:
            raise PlatformMismatchError(self, session)
        timestamp = datetime.now()
        session.save_reasoning_event('task_list_update', tasks)
        payload = Payload(action=PayloadAction.AGENT_REPLY_TASK_LIST_UPDATE,
                          message=tasks,
                          timestamp=timestamp)
        self._send(session.id, payload)

    def reply_reasoning_step(self, session: Session, step: dict) -> None:
        """Send an intermediate reasoning-state step to a specific user.

        A *reasoning step* is any observable event the predefined reasoning
        state body produces while it is working: the LLM emitting tool calls
        or text, a tool returning a result, the task list being mutated
        (planned / completed / skipped), the orchestrator pushing back a
        premature final answer, or the step budget being exhausted. Sending
        these to the client lets the UI show a live "thinking" trace before
        the final reply arrives.

        Persisted in the dedicated ``reasoning_step`` table (kind=
        ``reasoning_step``) — not in the chat table — so it does not pollute
        chat history retrieval.

        Args:
            session (Session): the user session.
            step (dict): the step payload with the shape
                ``{"kind": str, "step": int, "summary": str, "details": dict}``.
                ``kind`` is one of ``llm_text``, ``llm_tool_calls``,
                ``tool_result``, ``task_added``, ``task_completed``,
                ``task_skipped``, ``pushback`` or ``max_steps``. ``summary``
                is a short human-readable description suitable for direct
                rendering; ``details`` is a kind-specific structured object
                for richer client-side rendering.
        """
        if session.platform is not self:
            raise PlatformMismatchError(self, session)
        timestamp = datetime.now()
        session.save_reasoning_event('reasoning_step', step)
        payload = Payload(action=PayloadAction.AGENT_REPLY_REASONING_STEP,
                          message=step,
                          timestamp=timestamp)
        self._send(session.id, payload)

    def reply_rag(self, session: Session, rag_message: RAGMessage) -> None:
        """Send a rag reply to a specific user.

        Args:
            session (Session): the user session
            rag_message (RAGMessage): the rag message to send to the user
        """
        if session.platform is not self:
            raise PlatformMismatchError(self, session)
        rag_message_dict = rag_message.to_dict()
        print(rag_message_dict)
        message_obj: Message = Message(t=MessageType.RAG_ANSWER, content=rag_message_dict, is_user=False, timestamp=datetime.now())
        session.save_message(message_obj)
        payload = Payload(action=PayloadAction.AGENT_REPLY_RAG,
                          message=rag_message_dict,
                          timestamp=message_obj.timestamp)
        payload.message = self._agent.process(session=session, message=payload.message, is_user_message=False)
        self._send(session.id, payload)

    def reply_speech(self, session: Session, message: str, audio_speed: float = None) -> None:
        """Send an audio reply to a specific user.

        The text message is converted to speech and sent to the user. Before being sent, the audio is encoded as a
        Base64 string. This must be taken into account when decoding the audio on the client side.

        Args:
            session (Session): the user session
            message (str): the text message to be converted to speech and sent to the user.
            audio_speed (float, optional): The speed of the audio. If not provided, the speed is retrieved from the
            session, or defaults to 1.0. 0.5 is half speed, 2.0 is double speed, etc. Defaults to None.
        """
        
        audio_dict = session._agent.nlp_engine.text2speech(session, message)
        audio_array = audio_dict['audio']
        sample_rate = audio_dict['sampling_rate']
        dtype = audio_array.dtype
        shape = audio_array.shape

        # TODO: the sped up / slowed down audio sounds like in an echo chamber, not so good
        # Adjust audio speed if needed, preserving pitch (avoid chipmunk effect)
        if audio_speed and audio_speed != 1.0:
            # librosa expects float32 audio
            audio_array = audio_array.astype(np.float32)

            if audio_array.ndim == 1:
                # Mono audio
                audio_array = librosa.effects.time_stretch(audio_array, rate=audio_speed)

            elif audio_array.ndim == 2:
                # Multi-channel audio: librosa doesn't support stereo directly,
                # so apply time_stretch per channel and pad to equal lengths if needed
                channels = []
                for ch in range(audio_array.shape[0]):
                    stretched = librosa.effects.time_stretch(audio_array[ch], rate=audio_speed)
                    channels.append(stretched)
                
                # Find the length of the longest stretched channel
                max_len = max([c.shape[0] for c in channels])
                
                # Pad shorter channels with zeros to match
                channels = [np.pad(c, (0, max_len - c.shape[0])) for c in channels]
                
                audio_array = np.stack(channels, axis=0)

            # Update shape and dtype after speed change
            shape = audio_array.shape
            dtype = audio_array.dtype

        audio_array_contiguous = np.ascontiguousarray(audio_array)
        audio_bytes = audio_array_contiguous.tobytes()
        base64_bytes = base64.b64encode(audio_bytes)
        base64_string_audio = base64_bytes.decode('utf-8')

        message = {
            "audio_data_base64": base64_string_audio,
            "metadata": {
                "sample_rate": sample_rate,
                "dtype": str(dtype),
                "shape": shape
            }
        }

        message_obj: Message = Message(t=MessageType.AUDIO, content=message, is_user=False, timestamp=datetime.now())
        session.save_message(message_obj)
        payload = Payload(action=PayloadAction.AGENT_REPLY_AUDIO, message=message, timestamp=message_obj.timestamp)
        payload.message = self._agent.process(session=session, message=payload.message, is_user_message=False)
        self._send(session.id, payload)

    def reply_ui(self, session: Session, ui: GUIModel) -> None:
        if session.platform is not self:
            raise PlatformMismatchError(self, session)
        ui_json = gui_to_json(ui)
        message_obj: Message = Message(t=MessageType.UI, content=ui_json, is_user=False, timestamp=datetime.now())
        session.save_message(message_obj)
        payload = Payload(action=PayloadAction.AGENT_REPLY_UI,
                          message=ui_json,
                          timestamp=message_obj.timestamp)
        payload.message = self._agent.process(session=session, message=payload.message, is_user_message=False)
        self._send(session.id, payload)
