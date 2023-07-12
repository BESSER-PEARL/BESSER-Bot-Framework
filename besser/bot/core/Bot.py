import logging

from besser.bot.core.RequestDispatcher import RequestDispatcher
from besser.bot.core.intent.Intent import Intent
from besser.bot.exceptions.exceptions import DuplicatedStateError, DuplicatedIntentError, DuplicatedEntityError, \
    DuplicatedInitialStateError, InitialStateNotFound
from besser.bot.core.Session import Session
from besser.bot.core.State import State

from besser.bot.core.entity.Entity import Entity
from besser.bot.nlp.NLPEngine import NLPEngine


class Bot:

    def __init__(self, name):
        self.name: str = name
        self.properties: dict[str, object] = {}
        self.states: list[State] = []
        self.intents: list[Intent] = []
        self.entities: list[Entity] = []
        self.request_dispatcher: RequestDispatcher = RequestDispatcher(self)
        self.sessions: dict[str, Session] = {}
        self.nlp_engine = NLPEngine(self)

    def load_properties(self, path: str):
        # TODO: Load self.properties dict from file
        return None

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
        self.request_dispatcher.run()  # Runs in another thread
        logging.info(f'{self.name} deployed and ready to use')

    def reset(self, user_id):
        # TODO: CHECK SESSION ALREADY EXISTS?
        session = Session(user_id, self.initial_state())
        self.sessions[user_id] = session
        session.current_state.run(session)
        session.update_history()
        return session

    def receive_message(self, user_id, message):
        session = self.get_session(user_id)
        session.clear_answer()
        session.set_message(message)
        session.set_predicted_intent(self.nlp_engine.predict_intent(session))
        session.current_state.receive_intent(session)
        session.update_history()
        return session

    def move(self, session, transition):
        logging.info(transition.log())
        session.current_state = transition.dest
        session.current_state.run(session)

    def set_global_fallback_body(self, body):
        for state in self.states:
            state.set_fallback_body(body)

    def train(self):
        self.nlp_engine.train()

    def get_session(self, user_id):
        if user_id in self.sessions:
            return self.sessions[user_id]
        else:
            return None

    def new_session(self, user_id):
        if user_id not in self.sessions:
            session = Session(user_id, self.initial_state())
            self.sessions[user_id] = session
            session.current_state.run(session)
            session.update_history()
            return session
        else:
            pass
            # TODO: HANDLE EXCEPTION
