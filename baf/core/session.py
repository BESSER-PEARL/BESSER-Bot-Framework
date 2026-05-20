import asyncio
import json
import threading
import time
from asyncio import TimerHandle
from collections import deque
from typing import Any, TYPE_CHECKING
from datetime import datetime

from pandas import DataFrame
from websocket import WebSocketApp

from baf import CHECK_TRANSITIONS_DELAY
from baf.core.transition.event import Event
from baf.core.transition.transition import Transition
from baf.library.transition.conditions import IntentMatcher
from baf.library.transition.events.base_events import ReceiveMessageEvent, ReceiveTextEvent
from baf.core.message import Message, get_message_type
from baf.exceptions.logger import logger
from baf.db import DB_MONITORING
from baf.nlp.rag.rag import RAGMessage
from baf.platforms.payload import PayloadEncoder, Payload, PayloadAction

if TYPE_CHECKING:
    from baf.core.agent import Agent
    from baf.db.db_handler import DBHandler
    from baf.core.state import State
    from baf.platforms.platform import Platform


class Session:
    """A user session in an agent execution.

    When a user starts interacting with an agent, a session is assigned to him/her to store user related information, such
    as the current state of the agent, the conversation history, the detected intent with its parameters or any user's
    private data. A session can be accessed from the body of the states to read/write user information.

    Args:
        session_id (str): The session id, which must unique among all agent sessions
        agent (Agent): The agent the session belongs to
        platform (Platform): The platform where the session has been created
        username (str): the name of the session user (optional)
        session_name (str): the name of the session (optional)

    Attributes:
        _id (str): The session id, which must unique among all agent sessions
        _username (str): the name of the session user (optional)
        _session_name (str): the name of the session (optional)
        _agent (str): The agent the session belongs to
        _platform (str): The platform where the session has been created
        _current_state (str): The current state in the agent for this session
        _dictionary (str): Storage of private data for this session
        _event (Any or None): The last event to trigger a transition.
        _events (deque[Any]): The queue of received external events to process
        _event_loop (asyncio.AbstractEventLoop): The loop in charge of managing incoming events
        _event_thread (threading.Thread): The thread where the event loop is running
        _timer_handle (TimerHandle): Handler of scheduled calls on the event loop
        _agent_connections (dict[str, WebSocketApp]): WebSocket client connections to other agent's WebSocket platforms.
            These connections enable an agent to send messages to other agents.
    """

    def __init__(
            self,
            session_id: str,
            agent: 'Agent',
            platform: 'Platform',
            username: str or None = None,
            session_name: str or None = None
    ):
        self._id: str = session_id
        self._username: str = username
        self._session_name: str = session_name
        self._agent: 'Agent' = agent
        self._platform: 'Platform' = platform
        self._current_state: 'State' = self._agent.initial_state()
        self._dictionary: dict[str, Any] = {}
        self._event: Event = None
        self._events: deque[Event] = deque()
        self._event_loop: asyncio.AbstractEventLoop or None = None
        self._event_thread: threading.Thread or None = None
        self._timer_handle: TimerHandle = None
        self._agent_connections: dict[str, WebSocketApp] = {}

    @property
    def id(self):
        """str: The session id."""
        return self._id

    @property
    def platform(self):
        """Platform: The session platform."""
        return self._platform

    @property
    def db_handler(self) -> 'DBHandler':
        """DBHandler: relational DB handler configured for this agent."""
        return self._agent.use_db_handler()

    @property
    def current_state(self):
        """State: The current agent state of the session."""
        return self._current_state

    @property
    def event(self):
        """Event: The last event matched by the agent."""
        return self._event

    @event.setter
    def event(self, event: Event):
        """
        Set the last event matched by the agent.
        Args:
            event (Event): the event to set in the session
        """
        self._event = event

    @property
    def events(self):
        """dequeue[Event]: The queue of pending events for this session"""
        return self._events

    def call_manage_transition(self) -> None:
        """Schedule the next call to manage_transition as soon as possible (cancelling the previously scheduled
        call).
        """
        if self._timer_handle:
            self._timer_handle.cancel()  # Cancel previously scheduled call to session.manage_transition()
        self._event_loop.call_soon_threadsafe(self.manage_transition)

    def manage_transition(self) -> None:
        """Evaluate the session's current state transitions, where one could be satisfied and triggered."""
        self.current_state.check_transitions(self)
        # The delay is in seconds
        delay = self._agent.get_property(CHECK_TRANSITIONS_DELAY)
        self._timer_handle = self._event_loop.call_later(delay, self.manage_transition)

    def _run_event_thread(self) -> None:
        """Start the thread managing external events"""
        self._event_loop = asyncio.new_event_loop()

        def start_event_loop():
            logger.debug(f'Starting Event Loop for session: {self.id}')
            # Wait for the platform to finish starting before running the agent.
            # Platforms run in their own threads and may not be ready immediately.
            timeout = 30  # seconds
            elapsed = 0.0
            interval = 0.05  # 50ms polling interval
            while not self._platform.running:
                if elapsed >= timeout:
                    logger.error(f'Platform did not start within {timeout}s for session {self.id}. Aborting session start.')
                    return
                time.sleep(interval)
                elapsed += interval
            asyncio.set_event_loop(self._event_loop)
            asyncio.get_event_loop().call_soon(self.manage_transition)
            self._event_loop.run_forever()
            logger.debug(f'Event Loop stopped for: {self.id}')

        thread = threading.Thread(target=start_event_loop)
        self._event_thread = thread
        thread.start()

    def _stop_event_thread(self) -> None:
        """Stop the thread managing external events"""
        self._event_loop.stop()
        self._event_thread.join()
        self._event_loop = None
        self._event_thread = None

    def get_chat_history(self, n: int = None, until_timestamp: datetime = None) -> list[Message]:
        """Get the history of messages between this session and its agent.

        Args:
            n (int or None): the number of messages to get (from the most recents). If none is provided, gets all the
                messages

        Returns:
            list[Message]: the conversation history
        """
        chat_history: list[Message] = []
        if self._agent.get_property(DB_MONITORING) and self._agent._monitoring_db.connected:
            chat_df: DataFrame = self._agent._monitoring_db.select_chat(self, n=n, until_timestamp=until_timestamp)
            for i, row in chat_df.iterrows():
                t = get_message_type(row['type'])
                chat_history.append(Message(t=t, content=row['content'], is_user=row['is_user'], timestamp=row['timestamp']))
        else:
            logger.warning('Could not retrieve the chat history from the database.')
        return chat_history

    def save_message(self, message: Message) -> None:
        """Save a message in the dedicated chat DB

        Args:
            message (Message): the message to save
        """
        self._agent._monitoring_db_insert_chat(self, message)

    def save_reasoning_event(self, kind: str, payload: Any) -> None:
        """Persist a reasoning-state event in the dedicated ``reasoning_step``
        table.

        Reasoning events (LLM tool calls, tool results, task list mutations,
        push-backs, max_steps, reasoning_started/finished brackets) are NOT
        stored in the chat table because they would mismatch the chat
        message-type schema. This method routes them to their own table.

        Args:
            kind (str): ``'reasoning_step'`` for a single
                :class:`~baf.library.state.reasoning_state_library.ReasoningStep`
                event, or ``'task_list_update'`` for a full task list snapshot.
            payload (Any): the structured event payload — a step dict or a
                list of task dicts.
        """
        self._agent._monitoring_db_insert_reasoning_event(self, kind, payload)

    def get_reasoning_events(self, until_timestamp: datetime = None) -> list[dict]:
        """Get the reasoning-state events for this session.

        Includes both step events and task-list snapshots, ordered by their
        emission timestamp.

        Args:
            until_timestamp (datetime): if provided, only events at or before
                this timestamp are returned.

        Returns:
            list[dict]: each entry has ``kind``, ``step_kind``, ``step``,
            ``summary``, ``payload``, ``timestamp``, ``chat_id`` keys (some
            may be None depending on ``kind``).
        """
        if not (self._agent.get_property(DB_MONITORING) and self._agent._monitoring_db.connected):
            return []
        df = self._agent._monitoring_db_select_reasoning_events(
            self, until_timestamp=until_timestamp,
        )
        if df is None or df.empty:
            return []
        return df.to_dict(orient="records")

    def link_pending_reasoning_events(self) -> None:
        """Link reasoning events with chat_id IS NULL to the most recent chat
        row for this session. Called once at the end of each reasoning loop
        so the events emitted during that loop are tied to the chat reply
        that closed it."""
        try:
            self._agent._monitoring_db_link_pending_reasoning_events(self)
        except Exception as e:
            logger.warning(
                f"[Session] link_pending_reasoning_events failed for "
                f"session {self.id}: {e}"
            )

    def set(self, key: str, value: Any) -> None:
        """Set an entry to the session private data storage.

        Args:
            key (str): the entry key
            value (Any): the entry value
        """
        self._dictionary[key] = value
        try:
            self._agent._monitoring_db_store_session_variables(self)
        except Exception as e:
            logger.error(f"Failed to store session variables to the database for session {self.id}: {e}", exc_info=True)

    def get(self, key: str, default: Any = None) -> Any:
        """Get an entry of the session private data storage.

        Args:
            key (str): the entry key
            default (Any): The default value to be returned, if the dictionary does not contain the key

        Returns:
            Any: the entry value, default or None if the key does not exist
        """
        if key not in self._dictionary:
            if default is not None:
                return default
            return None
        return self._dictionary[key]

    def delete(self, key: str) -> None:
        """Delete an entry of the session private data storage.

        Args:
            key (str): the entry key
        """
        try:
            del self._dictionary[key]
        except Exception as e:
            logger.error(f"Failed to delete key '{key}' from session {self.id}: {e}", exc_info=True)
            return None
    def get_dictionary(self) -> dict[str, Any]:
        """
        Returns the private data dictionary for this session.

        Returns:
            dict[str, Any]: The session's private data storage.
        """
        return self._dictionary

    def move(self, transition: Transition) -> None:
        """Move to another agent state.

        Args:
            transition (Transition): the transition that points to the agent state to move
        """
        logger.info(transition.log())
        self._agent._monitoring_db_insert_transition(self, transition)
        if isinstance(transition.event, ReceiveTextEvent) and isinstance(transition.condition, IntentMatcher):
            self._agent._monitoring_db_insert_intent_prediction(self, self.event.predicted_intent)
        # TODO: STORE EVENT IN DB (CALL event.store_in_db())
        if any(transition.dest is global_state for global_state in self._agent.global_state_component):
            self.set("prev_state", self.current_state)
        self._current_state = transition.dest
        self._current_state.run(self)
        self.call_manage_transition()

    def reply(self, message: str) -> None:
        """An agent message (usually a reply to a user message) is sent to the session platform to show it to the user.

        Args:
            message (str): the agent reply
        """
        # Multi-platform
        self._platform.reply(self, message)

    def create_agent_connection(self, url) -> None:
        """Create a WebSocket connection to a specific WebSocket URL.

        Args:
            url (str): the WebSocket server's URL
        """
        finished = False

        def on_message(ws, payload_str):
            payload: Payload = Payload.decode(payload_str)
            if payload.action == PayloadAction.AGENT_REPLY_STR.value:
                event: ReceiveMessageEvent = ReceiveMessageEvent.create_event_from(
                    message=payload.message,
                    session=self,
                    human=False)
                self._agent.receive_event(event)
        def on_open(ws):
            nonlocal finished
            finished = True

        def on_close(ws, close_status_code, close_msg):
            del self._agent_connections[url]

        def on_error(ws, error):
            nonlocal finished
            finished = True

        ws = WebSocketApp(url, on_message=on_message, on_open=on_open, on_close=on_close, on_error=on_error)
        websocket_thread = threading.Thread(target=ws.run_forever)
        websocket_thread.start()
        self._agent_connections[url] = ws
        while not finished:
            # Wait until the connection is open
            time.sleep(0.01)

    def send_message_to_websocket(self, url: str, message: Any) -> None:
        """Send a message to a WebSocket Server, generally used to send a message to an agent through the WebSocket
        platform.

        Args:
            url (str): the WebSocket URL (i.e., the target agent's WebSocket platform URL)
            message (Any): the message to send to the WebSocket server
        """
        logger.info(f'Sending message to {url}')
        if url not in self._agent_connections:
            self.create_agent_connection(url)
        if url not in self._agent_connections:
            logger.error(f'Could not connect to {url}')
            return
        ws = self._agent_connections[url]
        payload = Payload(action=PayloadAction.AGENT_REPLY_STR,
                          message=message)
        ws.send(json.dumps(payload, cls=PayloadEncoder))

    def run_rag(self, message: str, llm_prompt: str = None, llm_name: str = None, k: int = None, num_previous_messages: int = None) -> RAGMessage:
        """Run the RAG engine.

        Args:
            message (str): the input query for the RAG engine
            llm_prompt (str): the prompt containing the instructions for the LLM to generate an answer from the
                retrieved content. If none is provided, the RAG's default value will be used
            llm_name (str): the name of the LLM to use. If none is provided, the RAG's default value will be used
            k (int): number of chunks to retrieve from the vector store. If none is provided, the RAG's default value
                will be used
            num_previous_messages (int): number of previous messages of the conversation to add to the prompt context.
                If none is provided, the RAG's default value will be used. Necessary a connection to
                :class:`~baf.db.monitoring_db.MonitoringDB`

        Returns:
            RAGMessage: the answer generated by the RAG engine
        """
        if self._agent.nlp_engine._rag is None:
            raise ValueError('Attempting to run RAG in an agent with no RAG engine.')
        return self._agent.nlp_engine._rag.run(message, self, llm_prompt, llm_name, k, num_previous_messages)
