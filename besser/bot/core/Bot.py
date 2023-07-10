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
        self.session: Session = Session()
        self.current_state: State = None  # TODO: MOVE TO SESSION
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
        self.current_state = self.initial_state()
        self.request_dispatcher.run()  # Runs in another thread
        self.current_state.run()
        self.session.update_history()
        logging.info(f'{self.name} deployed and ready to use')

    def reset(self):
        self.session = Session()
        self.current_state = self.initial_state()
        self.current_state.run()
        self.session.update_history()

    def receive_message(self):
        self.session.set_predicted_intent(self.nlp_engine.predict_intent())
        self.current_state.receive_intent()

    def move(self, transition):
        logging.info(transition.log())
        self.current_state = transition.dest
        self.current_state.run()

    def set_global_fallback_body(self, body):
        for state in self.states:
            state.set_fallback_body(body)

    def train(self):
        self.nlp_engine.train()
