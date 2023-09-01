import logging
import threading
from typing import Callable

from besser.bot.core.entity.entity import Entity
from besser.bot.core.entity.entity_entry import EntityEntry
from besser.bot.core.intent.intent import Intent
from besser.bot.core.intent.intent_parameter import IntentParameter
from besser.bot.exceptions.exceptions import DuplicatedStateError, DuplicatedIntentError, DuplicatedEntityError, \
    DuplicatedInitialStateError, InitialStateNotFound
from besser.bot.platforms.platform import Platform
from besser.bot.core.session import Session
from besser.bot.core.state import State
from besser.bot.nlp.nlp_engine import NLPEngine
from besser.bot.platforms.telegram.telegram_platform import TelegramPlatform
from besser.bot.platforms.websocket.websocket_platform import WebSocketPlatform

from configparser import ConfigParser


class Bot:
    """
    The bot class.

    :param name: the bot's name
    :type name: str

    :ivar str _name: the bot name
    :ivar list[Platform] _platforms: the bot platforms
    :ivar NLPEngine _nlp_engine: the bot NLP engine
    :ivar ConfigParser _config: the bot configuration parameters
    :ivar dict[str, Session] _sessions: the bot sessions
    :ivar list[State] states: the bot states
    :ivar list[Intent] intents: the bot intents
    :ivar list[Entity] entities: the bot entities
    """

    def __init__(self, name: str):
        self._name: str = name
        self._platforms: list[Platform] = []
        self._nlp_engine = NLPEngine(self)
        self._config: ConfigParser = ConfigParser()
        self._sessions: dict[str, Session] = {}
        self.states: list[State] = []
        self.intents: list[Intent] = []
        self.entities: list[Entity] = []

    @property
    def name(self):
        """
        Get the bot name.

        :return: The bot name
        """
        return self._name

    @property
    def nlp_engine(self):
        """
        Get the bot NLP engine.

        :return: The bot NLP engine
        """
        return self._nlp_engine

    @property
    def config(self):
        """
        Get the bot configuration parameters.

        :return: The bot configuration parameters
        """
        return self._config

    def load_properties(self, path: str) -> None:
        """
        Read a properties file and store its properties in the bot configuration.

        An example properties file, `config.ini`:

        .. literalinclude:: ../../../besser/bot/test/examples/config.ini


        :param path: the path to the properties file
        :type path: str
        :return:
        :rtype:
        """
        self._config.read(path)

    def new_state(self, name: str, initial: bool = False) -> State:
        """
        Create a new state in the bot.

        :param name: the state name. It must be unique in the bot.
        :type name: str
        :param initial: weather the state is initial or not. A bot must have 1 initial state.
        :type initial: bool
        :return: the state
        :rtype: State
        """
        new_state = State(self, name, initial)
        if new_state in self.states:
            raise DuplicatedStateError(self, new_state)
        if initial and self.initial_state():
            raise DuplicatedInitialStateError(self, self.initial_state(), new_state)
        self.states.append(new_state)
        return new_state

    def add_intent(self, intent: Intent) -> Intent:
        """
        Add an intent to the bot.

        :param intent: the intent to add
        :type intent: Intent
        :return: the added intent
        :rtype: Intent
        """
        if intent in self.intents:
            raise DuplicatedIntentError(self, intent)
        # TODO: Check entity is in self.entities
        self.intents.append(intent)
        return intent

    def new_intent(self,
                   name: str,
                   training_sentences: list[str],
                   parameters: list[IntentParameter] or None = None
                   ) -> Intent:
        """
        Create a new intent in the bot.

        :param name: the intent name. It must be unique in the bot
        :type name: str
        :param training_sentences: the intent's training sentences
        :type training_sentences: list[str]
        :param parameters:
        :type parameters: list[IntentParameter] or None
        :return: the intent
        :rtype: Intent
        """
        new_intent = Intent(name, training_sentences, parameters)
        if new_intent in self.intents:
            raise DuplicatedIntentError(self, new_intent)
        self.intents.append(new_intent)
        return new_intent

    def add_entity(self, entity: Entity) -> Entity:
        """
        Add an entity to the bot.

        :param entity: the entity to add
        :type entity: Entity
        :return: the added entity
        :rtype: Entity
        """
        if entity in self.entities:
            raise DuplicatedEntityError(self, entity)
        # TODO: Check entity is in self.entities
        self.entities.append(entity)
        return entity

    def new_entity(self,
                   name: str,
                   base_entity: bool = False,
                   entries: list[EntityEntry] or None = None
                   ) -> Entity:
        """
        Create a new entity in the bot.

        :param name: the entity name. It must be unique in the bot
        :type name: str
        :param base_entity: weather the entity is a base entity or not (i.e. a custom entity)
        :type base_entity: bool
        :param entries: the entity entries
        :type entries: list[EntityEntry]
        :return: the entity
        :rtype: Entity
        """
        new_entity = Entity(name, base_entity, entries)
        if new_entity in self.entities:
            raise DuplicatedEntityError(self, new_entity)
        self.entities.append(new_entity)
        return new_entity

    def initial_state(self) -> State or None:
        """
        Get the bot's initial state. It can be None if it has not been set.

        :return: the initial state of the bot, if exists
        :rtype: State or None
        """
        for state in self.states:
            if state.initial:
                return state
        return None

    def run(self) -> None:
        """
        Start the execution of the bot.

        The bot is idle until a user connects, a session is created and the initial state starts running.

        :return:
        :rtype:
        """
        if not self.initial_state():
            raise InitialStateNotFound(self)
        self._nlp_engine.initialize()
        logging.info(f'{self._name} training started')
        self._train()
        logging.info(f'{self._name} training finished')
        for server in self._platforms:
            thread = threading.Thread(target=server.run)
            thread.start()
        idle = threading.Event()
        idle.wait()

    def reset(self, session_id: str) -> Session:
        """
        Reset the bot current state and memory for the specified session. Then, restart the bot again for this session.

        :param session_id: the session to reset
        :type session_id: str
        :return: the reset session
        :rtype: Session
        """
        session = self._sessions[session_id]
        # TODO: Raise exception SessionNotFound
        new_session = Session(session_id, self, session.platform)
        self._sessions[session_id] = new_session
        logging.info(f'{self._name} restarted')
        new_session.current_state.run(new_session)
        return new_session

    def receive_message(self, session_id: str, message: str) -> None:
        """
        Receive a message from a specific session.

        Receiving a message starts the process of inferring the message's intent and acting properly
        (e.g. transition to another state, store something in memory, etc.)

        :param session_id: the session that sends the message to the bot
        :type session_id: str
        :param message: the message sent to the bot
        :type message: str
        :return:
        :rtype:
        """
        session = self._sessions[session_id]
        # TODO: Raise exception SessionNotFound
        session.message = message
        session.predicted_intent = self._nlp_engine.predict_intent(session)
        session.current_state.receive_intent(session)

    def set_global_fallback_body(self, body: Callable[[Session], None]) -> None:
        """
        Set the fallback body for all bot states.

        The fallback body is a state's callable function that will be run whenever necessary to handle unexpected
        scenarios (e.g. when no intent is matched, the current state's fallback is run). This method simply sets the
        same fallback body to all bot states.

        See also: :func:`~besser.bot.core.state.State.set_fallback_body`

        :param body: the fallback body
        :type body: Callable[[Session], None]
        :return:
        :rtype:
        """
        for state in self.states:
            state.set_fallback_body(body)

    def _train(self) -> None:
        """
        Train the bot. The bot training is done before its execution.

        :return:
        :rtype:
        """
        self._nlp_engine.train()

    def get_session(self, session_id: str) -> Session or None:
        """
        Get a bot session.

        :param session_id: the session id
        :type session_id: str
        :return: the session, if exists, or None
        :rtype: Session or None
        """
        if session_id in self._sessions:
            return self._sessions[session_id]
        else:
            # TODO: Raise exception SessionNotFound
            return None

    def new_session(self, session_id: str, platform: Platform) -> Session:
        """
        Create a new session for the bot.

        :param session_id: the session id
        :type session_id: str
        :param platform: the platform where the session is to be created and used
        :type platform: Platform
        :return: the session
        :rtype: Session
        """
        if session_id in self._sessions:
            # TODO: Raise exception
            pass
        if platform not in self._platforms:
            # TODO: Raise exception
            pass
        session = Session(session_id, self, platform)
        self._sessions[session_id] = session
        session.current_state.run(session)
        return session

    def delete_session(self, session_id: str) -> None:
        """
        Delete an existing bot session.

        :param session_id: the session id
        :type session_id: str
        :return:
        :rtype:
        """
        del self._sessions[session_id]

    def use_websocket_platform(self, use_ui: bool = True) -> WebSocketPlatform:
        """
        Use the :class:`~besser.bot.platforms.websocket.websocket_platform.WebSocketPlatform` on this bot.

        :param use_ui: if true, the default UI will be run to use this platform
        :type use_ui: bool
        :return: the websocket platform
        :rtype: WebSocketPlatform
        """
        websocket_platform = WebSocketPlatform(self, use_ui)
        self._platforms.append(websocket_platform)
        return websocket_platform

    def use_telegram_platform(self) -> TelegramPlatform:
        """
        Use the :class:`~besser.bot.platforms.telegram.telegram_platform.TelegramPlatform` on this bot.

        :return: the telegram platform
        :rtype: TelegramPlatform
        """
        telegram_platform = TelegramPlatform(self)
        self._platforms.append(telegram_platform)
        return telegram_platform
