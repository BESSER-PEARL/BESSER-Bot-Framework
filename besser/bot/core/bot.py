import logging
import operator
import threading
from configparser import ConfigParser
from typing import Any, Callable

from besser.bot.core.entity.entity import Entity
from besser.bot.core.intent.intent import Intent
from besser.bot.core.intent.intent_parameter import IntentParameter
from besser.bot.core.property import Property
from besser.bot.core.session import Session
from besser.bot.core.state import State
from besser.bot.exceptions.exceptions import BotNotTrainedError, DuplicatedEntityError, DuplicatedInitialStateError, \
    DuplicatedIntentError, DuplicatedStateError, InitialStateNotFound
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
        _sessions (dict[str, Session]): The bot sessions
        _trained (bool): Weather the bot has been trained or not. It must be trained before it starts its execution.
        states (list[State]): The bot states
        intents (list[Intent]): The bot intents
        entities (list[Entity]): The bot entities
        global_initial_states (list[State, Intent]): List of tuples of initial global states and their triggering intent
        global_state_component (dict[State, list[State]]): Dictionary of global state components, where key is initial
            global state and values is set of states in corresponding global component
    """

    def __init__(self, name: str):
        self._name: str = name
        self._platforms: list[Platform] = []
        self._platforms_threads: list[threading.Thread] = []
        self._nlp_engine = NLPEngine(self)
        self._config: ConfigParser = ConfigParser()
        self._sessions: dict[str, Session] = {}
        self._trained: bool = False
        self.states: list[State] = []
        self.intents: list[Intent] = []
        self.entities: list[Entity] = []
        self.global_initial_states: list[tuple[State, Intent]] = []
        self.global_state_component: dict[State, list[State]] = dict()

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
        self._config.set(prop.section, prop.name, value)

    def new_state(self, name: str, initial: bool = False) -> State:
        """Create a new state in the bot.

        Args:
            name (str): the state name. It must be unique in the bot.
            initial (bool): weather the state is initial or not. A bot must have 1 initial state.

        Returns:
            State: the state
        """
        new_state = State(self, name, initial)
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
                   training_sentences: list[str],
                   parameters: list[IntentParameter] or None = None
                   ) -> Intent:
        """Create a new intent in the bot.

        Args:
            name (str): the intent name. It must be unique in the bot
            training_sentences (list[str]): the intent's training sentences
            parameters (list[IntentParameter] or None)

        Returns:
            Intent: the intent
        """
        new_intent = Intent(name, training_sentences, parameters)
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
                   entries: dict[str, list[str]] or None = None
                   ) -> Entity:
        """Create a new entity in the bot.

        Args:
            name (str): the entity name. It must be unique in the bot
            base_entity (bool): weather the entity is a base entity or not (i.e. a custom entity)
            entries (dict[str, list[str]] or None): the entity entries

        Returns:
            Entity: the entity
        """
        new_entity = Entity(name, base_entity, entries)
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
            train (bool): weather to train the bot or not
            sleep (bool): weather to sleep after running the bot or not, which means that this function will not return
        """
        if train:
            self.train()
        if not self._trained:
            raise BotNotTrainedError(self)
        self._run_platforms()
        if sleep:
            idle = threading.Event()
            idle.wait()

    def stop(self) -> None:
        """Stop the bot execution."""
        self._stop_platforms()

    def reset(self, session_id: str) -> Session:
        """Reset the bot current state and memory for the specified session. Then, restart the bot again for this session.

        Args:
            session_id (str): the session to reset

        Returns:
            Session: the reset session
        """
        session = self._sessions[session_id]
        # TODO: Raise exception SessionNotFound
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
        session.message = message
        session.predicted_intent = self._nlp_engine.predict_intent(session)
        session.current_state.receive_intent(session)

    def set_global_fallback_body(self, body: Callable[[Session], None]) -> None:
        """Set the fallback body for all bot states.

        The fallback body is a state's callable function that will be run whenever necessary to handle unexpected
        scenarios (e.g. when no intent is matched, the current state's fallback is run). This method simply sets the
        same fallback body to all bot states.

        See also: :func:`~besser.bot.core.state.State.set_fallback_body`

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

    def get_session(self, session_id: str) -> Session or None:
        """Get a bot session.

        Args:
            session_id (str): the session id

        Returns:
            Session or None: the session, if exists, or None
        """
        if session_id in self._sessions:
            return self._sessions[session_id]
        else:
            # TODO: Raise exception SessionNotFound
            return None

    def new_session(self, session_id: str, platform: Platform) -> Session:
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
        session.current_state.run(session)
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
