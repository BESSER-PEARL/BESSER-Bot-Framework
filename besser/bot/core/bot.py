import logging
import operator
import threading
from configparser import ConfigParser
from typing import Any, Callable, get_type_hints

from besser.bot.core.message import Message
from besser.bot.core.transition import Transition
from besser.bot.db import DB_MONITORING
from besser.bot.db.monitoring_db import MonitoringDB
from besser.bot.core.entity.entity import Entity
from besser.bot.core.intent.intent import Intent
from besser.bot.core.intent.intent_parameter import IntentParameter
from besser.bot.core.property import Property
from besser.bot.core.processors.processor import Processor
from besser.bot.core.session import Session
from besser.bot.core.state import State
from besser.bot.core.file import File
from besser.bot.exceptions.exceptions import BotNotTrainedError, DuplicatedEntityError, DuplicatedInitialStateError, \
    DuplicatedIntentError, DuplicatedStateError, InitialStateNotFound
from besser.bot.nlp.intent_classifier.intent_classifier_configuration import IntentClassifierConfiguration, \
    SimpleIntentClassifierConfiguration
from besser.bot.nlp.nlp_engine import NLPEngine
from besser.bot.platforms.platform import Platform
from besser.bot.platforms.telegram.telegram_platform import TelegramPlatform
from besser.bot.platforms.websocket.websocket_platform import WebSocketPlatform


class Bot:
    """The bot class.

    Args:
        name (str): The bot's name

    Attributes:
        _name (str): The bot name
        _platforms (list[Platform]): The bot platforms
        _platforms_threads (list[threading.Thread]): The threads where the platforms are run
        _nlp_engine (NLPEngine): The bot NLP engine
        _config (ConfigParser): The bot configuration parameters
        _default_ic_config (IntentClassifierConfiguration): the intent classifier configuration used by default for the
            bot states
        _sessions (dict[str, Session]): The bot sessions
        _trained (bool): Whether the bot has been trained or not. It must be trained before it starts its execution.
        _monitoring_db (MonitoringDB): The monitoring component of the bot that communicates with a database to store
            usage information for later visualization or analysis
        states (list[State]): The bot states
        intents (list[Intent]): The bot intents
        entities (list[Entity]): The bot entities
        global_initial_states (list[State, Intent]): List of tuples of initial global states and their triggering intent
        global_state_component (dict[State, list[State]]): Dictionary of global state components, where key is initial
            global state and values is set of states in corresponding global component
        processors (list[Processors]): List of processors used by the bot
    """

    def __init__(self, name: str):
        self._name: str = name
        self._platforms: list[Platform] = []
        self._platforms_threads: list[threading.Thread] = []
        self._nlp_engine = NLPEngine(self)
        self._config: ConfigParser = ConfigParser()
        self._default_ic_config: IntentClassifierConfiguration = SimpleIntentClassifierConfiguration()
        self._sessions: dict[str, Session] = {}
        self._trained: bool = False
        self._monitoring_db: MonitoringDB = None
        self.states: list[State] = []
        self.intents: list[Intent] = []
        self.entities: list[Entity] = []
        self.global_initial_states: list[tuple[State, Intent]] = []
        self.global_state_component: dict[State, list[State]] = dict()
        self.processors: list[Processor] = []

    @property
    def name(self):
        """str: The bot name."""
        return self._name

    @property
    def nlp_engine(self):
        """NLPEngine: The bot NLP engine."""
        return self._nlp_engine

    @property
    def config(self):
        """ConfigParser: The bot configuration parameters."""
        return self._config

    def load_properties(self, path: str) -> None:
        """Read a properties file and store its properties in the bot configuration.

        An example properties file, `config.ini`:

        .. literalinclude:: ../../../../besser/bot/test/examples/config.ini

        Args:
            path (str): the path to the properties file
        """
        self._config.read(path)

    def get_property(self, prop: Property) -> Any:
        """Get a bot property's value

        Args:
            prop (Property): the property to get its value

        Returns:
            Any: the property value, or None
        """
        if prop.type == str:
            getter = self._config.get
        elif prop.type == bool:
            getter = self._config.getboolean
        elif prop.type == int:
            getter = self._config.getint
        elif prop.type == float:
            getter = self._config.getfloat
        else:
            return None
        return getter(prop.section, prop.name, fallback=prop.default_value)

    def set_property(self, prop: Property, value: Any):
        """Set a bot property.

        Args:
            prop (Property): the property to set
            value (Any): the property value
        """
        if (value is not None) and (not isinstance(value, prop.type)):
            raise TypeError(f"Attempting to set the bot property '{prop.name}' in section '{prop.section}' with a "
                            f"{type(value)} value: {value}. The expected property value type is {prop.type}")
        if prop.section not in self._config.sections():
            self._config.add_section(prop.section)
        self._config.set(prop.section, prop.name, str(value))

    def set_default_ic_config(self, ic_config: IntentClassifierConfiguration):
        """Set the default intent classifier configuration.

        Args:
            ic_config (IntentClassifierConfiguration): the intent classifier configuration
        """
        self._default_ic_config = ic_config

    def new_state(self,
                  name: str,
                  initial: bool = False,
                  ic_config: IntentClassifierConfiguration or None = None
                  ) -> State:
        """Create a new state in the bot.

        Args:
            name (str): the state name. It must be unique in the bot.
            initial (bool): whether the state is initial or not. A bot must have 1 initial state.
            ic_config (IntentClassifierConfiguration or None): the intent classifier configuration for the state.
                If None is provided, the bot's default one will be assigned to the state.

        Returns:
            State: the state
        """
        if not ic_config:
            ic_config = self._default_ic_config
        new_state = State(self, name, initial, ic_config)
        if new_state in self.states:
            raise DuplicatedStateError(self, new_state)
        if initial and self.initial_state():
            raise DuplicatedInitialStateError(self, self.initial_state(), new_state)
        self.states.append(new_state)
        return new_state

    def add_intent(self, intent: Intent) -> Intent:
        """Add an intent to the bot.

        Args:
            intent (Intent): the intent to add

        Returns:
            Intent: the added intent
        """
        if intent in self.intents:
            raise DuplicatedIntentError(self, intent)
        # TODO: Check entity is in self.entities
        self.intents.append(intent)
        return intent

    def new_intent(self,
                   name: str,
                   training_sentences: list[str] or None = None,
                   parameters: list[IntentParameter] or None = None,
                   description: str or None = None,
                   ) -> Intent:
        """Create a new intent in the bot.

        Args:
            name (str): the intent name. It must be unique in the bot
            training_sentences (list[str] or None): the intent's training sentences
            parameters (list[IntentParameter] or None): the intent parameters, optional
            description (str or None): a description of the intent, optional

        Returns:
            Intent: the intent
        """
        new_intent = Intent(name, training_sentences, parameters, description)
        if new_intent in self.intents:
            raise DuplicatedIntentError(self, new_intent)
        self.intents.append(new_intent)
        return new_intent

    def add_entity(self, entity: Entity) -> Entity:
        """Add an entity to the bot.

        Args:
            entity (Entity): the entity to add

        Returns:
            Entity: the added entity
        """
        if entity in self.entities:
            raise DuplicatedEntityError(self, entity)
        self.entities.append(entity)
        return entity

    def new_entity(self,
                   name: str,
                   base_entity: bool = False,
                   entries: dict[str, list[str]] or None = None,
                   description: str or None = None
                   ) -> Entity:
        """Create a new entity in the bot.

        Args:
            name (str): the entity name. It must be unique in the bot
            base_entity (bool): whether the entity is a base entity or not (i.e. a custom entity)
            entries (dict[str, list[str]] or None): the entity entries
            description (str or None): a description of the entity, optional

        Returns:
            Entity: the entity
        """
        new_entity = Entity(name, base_entity, entries, description)
        if new_entity in self.entities:
            raise DuplicatedEntityError(self, new_entity)
        self.entities.append(new_entity)
        return new_entity

    def initial_state(self) -> State or None:
        """Get the bot's initial state. It can be None if it has not been set.

        Returns:
            State or None: the initial state of the bot, if exists
        """
        for state in self.states:
            if state.initial:
                return state
        return None

    def _init_global_states(self) -> None:
        """Initialise the global states and add the necessary transitions.

        Go through all the global states and add transitions to every state to jump to the global states.
        Also add the transition to jump back to the previous state once the global state component
        has been completed. 
        """
        if self.global_initial_states:
            global_state_follow_up = []
            for global_state_tuple in self.global_initial_states:
                global_state = global_state_tuple[0]
                for state in self.global_state_component[global_state]:
                    global_state_follow_up.append(state)
            for global_state_tuple in self.global_initial_states:
                global_state = global_state_tuple[0]
                for state in self.states:
                    if (not any(state.name is global_init_state[0].name for global_init_state in self.global_initial_states)
                            and state not in global_state_follow_up):
                        if state.transitions and not state.transitions[0].is_auto():
                            state.when_intent_matched_go_to(global_state_tuple[1], global_state)
                            self.global_state_component[global_state][-1].when_variable_matches_operation_go_to(
                                var_name="prev_state", operation=operator.eq, target=state, dest=state)
            self.global_initial_states.clear()

    def _run_platforms(self) -> None:
        """Stop the execution of the bot platforms"""
        for platform in self._platforms:
            thread = threading.Thread(target=platform.run)
            self._platforms_threads.append(thread)
            thread.start()

    def _stop_platforms(self) -> None:
        for platform, thread in zip(self._platforms, self._platforms_threads):
            platform.stop()
            thread.join()
        self._platforms_threads = []

    def run(self, train: bool = True, sleep: bool = True) -> None:
        """Start the execution of the bot.

        Args:
            train (bool): whether to train the bot or not
            sleep (bool): whether to sleep after running the bot or not, which means that this function will not return
        """
        if train:
            self.train()
        if not self._trained:
            raise BotNotTrainedError(self)
        if self.get_property(DB_MONITORING):
            if not self._monitoring_db:
                self._monitoring_db = MonitoringDB()
            self._monitoring_db.connect_to_db(self)
            if self._monitoring_db.connected:
                self._monitoring_db.initialize_db()
        self._run_platforms()
        if sleep:
            idle = threading.Event()
            while True:
                try:
                    idle.wait(1)
                except BaseException as e:
                    self.stop()
                    logging.info(f'{self._name} execution finished due to {e.__class__.__name__}')
                    break

    def stop(self) -> None:
        """Stop the bot execution."""
        logging.info(f'Stopping bot {self._name}')
        self._stop_platforms()
        if self.get_property(DB_MONITORING) and self._monitoring_db.connected:
            self._monitoring_db.close_connection()

    def reset(self, session_id: str) -> Session or None:
        """Reset the bot current state and memory for the specified session. Then, restart the bot again for this session.

        Args:
            session_id (str): the session to reset

        Returns:
            Session or None: the reset session, or None if the provided session_id does not exist
        """
        if session_id not in self._sessions:
            return None
        session = self._sessions[session_id]
        new_session = Session(session_id, self, session.platform)
        self._sessions[session_id] = new_session
        logging.info(f'{self._name} restarted by user {session_id}')
        new_session.current_state.run(new_session)
        return new_session

    def receive_message(self, session_id: str, message: str) -> None:
        """Receive a message from a specific session.

        Receiving a message starts the process of inferring the message's intent and acting properly
        (e.g. transition to another state, store something in memory, etc.)

        Args:
            session_id (str): the session that sends the message to the bot
            message (str): the message sent to the bot
        """
        session = self._sessions[session_id]
        # TODO: Raise exception SessionNotFound
        message = self.process(session=session, message=message, is_user_message=True)
        session.message = message
        logging.info(f'Received message: {message}')
        session.predicted_intent = self._nlp_engine.predict_intent(session)
        logging.info(f'Detected intent: {session.predicted_intent.intent.name}')
        self._monitoring_db_insert_intent_prediction(session)
        for parameter in session.predicted_intent.matched_parameters:
            logging.info(f"Parameter '{parameter.name}': {parameter.value}, info = {parameter.info}")
        session.current_state.receive_intent(session)

    def receive_file(self, session_id: str, file: File) -> None:
        """Receive a file from a specific session.


        Args:
            session_id (str): the session that sends the message to the bot
            file (File): the file sent to the bot
        """
        session = self._sessions[session_id]
        # TODO: Raise exception SessionNotFound
        # keep previous message here? 
        file = self.process(session=session, message=file, is_user_message=True)
        session.message = file.name
        session.file = file
        logging.info('Received file')
        session.current_state.receive_file(session)

    def process(self, session: Session, message: Any, is_user_message: bool) -> Any:
        """Runs the bot processors in a message.

        Only processors that process messages of the same type as the given message will be run.
        If the message to process is a user message, only processors that process user messages will be run.
        If the message to process is a bot message, only processors that process bot messages will be run.

        Args:
            session (Session): the current session
            message (Any): the message to be processed
            is_user_message (bool): indicates whether the message is a user message (True) or a bot message (False)

        Returns:
            Any: the processed message
        """
        for processor in self.processors:
            method_return_type = get_type_hints(processor.process).get('return')
            if method_return_type is not None and isinstance(message, method_return_type):
                if (processor.bot_messages and not is_user_message) or (processor.user_messages and is_user_message):
                    message = processor.process(session=session, message=message)
        return message

    def set_global_fallback_body(self, body: Callable[[Session], None]) -> None:
        """Set the fallback body for all bot states.

        The fallback body is a state's callable function that will be run whenever necessary to handle unexpected
        scenarios (e.g. when no intent is matched, the current state's fallback is run). This method simply sets the
        same fallback body to all bot states.

        See also:
            :func:`~besser.bot.core.state.State.set_fallback_body`

        Args:
            body (Callable[[Session], None]): the fallback body
        """
        for state in self.states:
            state.set_fallback_body(body)

    def train(self) -> None:
        """Train the bot.

        The bot training is done before its execution.
        """
        if not self.initial_state():
            raise InitialStateNotFound(self)
        self._init_global_states()
        self._nlp_engine.initialize()
        logging.info(f'{self._name} training started')
        self._nlp_engine.train()
        logging.info(f'{self._name} training finished')
        self._trained = True

    def _get_session(self, session_id: str) -> Session or None:
        """Get a bot session.

        Args:
            session_id (str): the session id

        Returns:
            Session or None: the session, if exists, or None
        """
        if session_id in self._sessions:
            return self._sessions[session_id]
        else:
            return None

    def _new_session(self, session_id: str, platform: Platform) -> Session:
        """Create a new session for the bot.

        Args:
            session_id (str): the session id
            platform (Platform): the platform where the session is to be created and used

        Returns:
            Session: the session
        """
        if session_id in self._sessions:
            # TODO: Raise exception
            pass
        if platform not in self._platforms:
            # TODO: Raise exception
            pass
        session = Session(session_id, self, platform)
        self._sessions[session_id] = session
        self._monitoring_db_insert_session(session)
        session.current_state.run(session)
        return session

    def get_or_create_session(self, session_id: str, platform: Platform) -> Session:
        session = self._get_session(session_id)
        if session is None:
            session = self._new_session(session_id, platform)
        return session

    def delete_session(self, session_id: str) -> None:
        """Delete an existing bot session.

        Args:
            session_id (str): the session id
        """
        del self._sessions[session_id]

    def use_websocket_platform(self, use_ui: bool = True) -> WebSocketPlatform:
        """Use the :class:`~besser.bot.platforms.websocket.websocket_platform.WebSocketPlatform` on this bot.

        Args:
            use_ui (bool): if true, the default UI will be run to use this platform

        Returns:
            WebSocketPlatform: the websocket platform
        """
        websocket_platform = WebSocketPlatform(self, use_ui)
        self._platforms.append(websocket_platform)
        return websocket_platform

    def use_telegram_platform(self) -> TelegramPlatform:
        """Use the :class:`~besser.bot.platforms.telegram.telegram_platform.TelegramPlatform` on this bot.

        Returns:
            TelegramPlatform: the telegram platform
        """
        telegram_platform = TelegramPlatform(self)
        self._platforms.append(telegram_platform)
        return telegram_platform

    def _monitoring_db_insert_session(self, session: Session) -> None:
        """Insert a session record into the monitoring database.

        Args:
            session (Session): the session of the current user
        """
        if self.get_property(DB_MONITORING) and self._monitoring_db.connected:
            # Not in thread since we must ensure it is added before running a state (the chat table needs the session)
            self._monitoring_db.insert_session(session)

    def _monitoring_db_insert_intent_prediction(self, session: Session) -> None:
        """Insert an intent prediction record into the monitoring database.

        Args:
            session (Session): the session of the current user
        """
        if self.get_property(DB_MONITORING) and self._monitoring_db.connected:
            thread = threading.Thread(target=self._monitoring_db.insert_intent_prediction, args=(session, session.current_state,))
            thread.start()

    def _monitoring_db_insert_transition(self, session: Session, transition: Transition) -> None:
        """Insert a transition record into the monitoring database.

        Args:
            session (Session): the session of the current user
        """
        if self.get_property(DB_MONITORING) and self._monitoring_db.connected:
            thread = threading.Thread(target=self._monitoring_db.insert_transition, args=(session, transition))
            thread.start()

    def _monitoring_db_insert_chat(self, session: Session, message: Message) -> None:
        """Insert a message record into the monitoring database.

        Args:
            session (Session): the session of the current user
        """
        if self.get_property(DB_MONITORING) and self._monitoring_db.connected:
            thread = threading.Thread(target=self._monitoring_db.insert_chat, args=(session, message))
            thread.start()
