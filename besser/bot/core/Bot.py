import logging
import threading
from uuid import UUID

from besser.bot.core.entity.Entity import Entity
from besser.bot.core.intent.Intent import Intent
from besser.bot.exceptions.exceptions import DuplicatedStateError, DuplicatedIntentError, DuplicatedEntityError, \
    DuplicatedInitialStateError, InitialStateNotFound
from besser.bot.platforms.Platform import Platform
from besser.bot.core.Session import Session
from besser.bot.core.State import State
from besser.bot.nlp.NLPEngine import NLPEngine
from besser.bot.platforms.telegram.TelegramPlatform import TelegramPlatform
from besser.bot.platforms.websocket.WebSocketPlatform import WebSocketPlatform

from configparser import ConfigParser


class Bot:

    def __init__(self, name):
        self.name: str = name
        self.properties: dict[str, object] = {}
        self.sessions: dict[str, Session] = {}
        self.states: list[State] = []
        self.intents: list[Intent] = []
        self.entities: list[Entity] = []
        self.platforms: list[Platform] = []
        self.nlp_engine = NLPEngine(self)
        self.config: ConfigParser = ConfigParser()

    def load_properties(self, path: str):
        self.config.read(path)

    def new_state(self, name, initial=False):
        new_state = State(self, name, initial)
        if new_state in self.states:
            raise DuplicatedStateError(self, new_state)
        if initial and self.initial_state():
            raise DuplicatedInitialStateError(self, self.initial_state(), new_state)
        self.states.append(new_state)
        return new_state

    def add_intent(self, intent: Intent):
        if intent in self.intents:
            raise DuplicatedIntentError(self, intent)
        self.intents.append(intent)
        return intent

    def new_intent(self, name, training_sentences, parameters=None):
        if parameters is None:
            parameters = []
        new_intent = Intent(name, training_sentences, parameters)
        if new_intent in self.intents:
            raise DuplicatedIntentError(self, new_intent)
        self.intents.append(new_intent)
        return new_intent

    def add_entity(self, entity: Entity):
        if entity in self.intents:
            raise DuplicatedEntityError(self, entity)
        self.entities.append(entity)
        return entity

    def new_entity(self, name, base_entity=False, entries=None):
        if entries is None:
            entries = {}
        new_entity = Entity(name, base_entity, entries)
        if new_entity in self.entities:
            raise DuplicatedEntityError(self, new_entity)
        self.entities.append(new_entity)
        return new_entity

    def initial_state(self) -> State:
        for state in self.states:
            if state.initial:
                return state
        return None

    def run(self):
        if not self.initial_state():
            raise InitialStateNotFound(self)
        self.nlp_engine.initialize()
        logging.info(f'{self.name} training started')
        self.train()
        logging.info(f'{self.name} training finished')
        for server in self.platforms:
            thread = threading.Thread(target=server.run)
            thread.start()
        idle = threading.Event()
        idle.wait()

    def reset(self, session_id):
        session = self.sessions[session_id]
        # TODO: CHECK SESSION ALREADY EXISTS?
        new_session = Session(session_id, self, session.platform, self.initial_state())
        self.sessions[session_id] = new_session
        logging.info(f'{self.name} restarted')
        new_session.current_state.run(new_session)
        return new_session

    def receive_message(self, session_id, message):
        session = self.sessions[session_id]
        session.set_message(message)
        session.set_predicted_intent(self.nlp_engine.predict_intent(session))
        session.current_state.receive_intent(session)

    def move(self, session, transition):
        logging.info(transition.log())
        session.current_state = transition.dest
        session.current_state.run(session)

    def set_global_fallback_body(self, body):
        for state in self.states:
            state.set_fallback_body(body)

    def train(self):
        self.nlp_engine.train()

    def get_session(self, session_id):
        if session_id in self.sessions:
            return self.sessions[session_id]
        else:
            return None

    def new_session(self, session_id: UUID, server):
        if session_id not in self.sessions:
            session = Session(session_id, self, server, self.initial_state())
            self.sessions[session_id] = session
            session.current_state.run(session)
            return session
        else:
            pass
            # TODO: HANDLE EXCEPTION

    def delete_session(self, session_id):
        del self.sessions[session_id]

    def use_websocket_platform(self, use_ui: bool = True):
        websocket_server = WebSocketPlatform(self, use_ui)
        websocket_server.initialize()
        self.platforms.append(websocket_server)
        return websocket_server

    def use_telegram_platform(self):
        telegram_server = TelegramPlatform(self)
        telegram_server.initialize()
        self.platforms.append(telegram_server)
        return telegram_server
