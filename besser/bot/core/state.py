import inspect
import logging
import traceback

from besser.bot.library.event.event_library import auto, intent_matched
from besser.bot.exceptions.exceptions import BodySignatureError, DuplicatedIntentMatchingTransitionError, \
    StateNotFound, IntentNotFound, DuplicatedAutoTransitionError
from besser.bot.core.transition import Transition
from besser.bot.library.intent.intent_library import fallback_intent
from besser.bot.library.state.state_library import default_fallback_body, default_body


class State:

    def __init__(self, bot, name: str, initial=False):
        self._bot = bot
        self._name = name
        self._initial = initial
        self._body = default_body
        self._fallback_body = default_fallback_body
        self._transition_counter = 0
        self.intents = []
        self.transitions = []

    @property
    def bot(self):
        return self._bot
    
    @property
    def name(self):
        return self._name
    
    @property
    def initial(self):
        return self._initial

    def __eq__(self, other):
        if type(other) is type(self):
            return self._name == other.name and self._bot.name == other.bot.name
        else:
            return False

    def __hash__(self):
        return hash((self._name, self._bot.name))

    def _t_name(self):
        self._transition_counter += 1
        return f"t_{self._transition_counter}"

    def set_body(self, body):
        body_signature = inspect.signature(body)
        body_template_signature = inspect.signature(default_body)
        if body_signature.parameters != body_template_signature.parameters:
            raise BodySignatureError(self._bot, self, body, body_template_signature, body_signature)
        self._body = body

    def set_fallback_body(self, body):
        body_signature = inspect.signature(body)
        body_template_signature = inspect.signature(default_fallback_body)
        if body_signature.parameters != body_template_signature.parameters:
            raise BodySignatureError(self._bot, self, body, body_template_signature, body_signature)
        self._fallback_body = body

    def when_event_go_to(self, event, dest, event_params: dict):
        if event == intent_matched:
            # TODO: CHECK isinstance(obj, Intent)
            # TODO: handle exceptions
            intent = event_params['intent']
            self.intents.append(intent)
        self.transitions.append(Transition(name=self._t_name(), source=self, dest=dest, event=event,
                                           event_params=event_params))

    def go_to(self, dest):
        for transition in self.transitions:
            if transition.is_auto():
                raise DuplicatedAutoTransitionError(self._bot, self)
        self.transitions.append(Transition(name=self._t_name(), source=self, dest=dest, event=auto, event_params={}))

    def when_intent_matched_go_to(self, intent, dest):
        if intent in self.intents:
            raise DuplicatedIntentMatchingTransitionError(self, intent)
        if intent not in self._bot.intents:
            raise IntentNotFound(self._bot, intent)
        if dest not in self._bot.states:
            raise StateNotFound(self._bot, dest)
        event_params = {'intent': intent}
        self.intents.append(intent)
        self.transitions.append(Transition(name=self._t_name(), source=self, dest=dest, event=intent_matched,
                                           event_params=event_params))

    def receive_intent(self, session):
        classification = session.predicted_intent
        if classification is None:
            logging.error("Something went wrong, no intent was predicted")
            return
        auto_transition = None
        for transition in self.transitions:
            if transition.is_intent_matched(classification.intent):
                session.move(transition)
                return
            if transition.is_auto():
                auto_transition = transition
        if auto_transition:
            # When no intent is matched, but there is an auto transition, move through it
            session.move(auto_transition)
            return
        if classification.intent == fallback_intent:
            logging.info(f"[{self._name}] Running fallback body {self._fallback_body.__name__}")
            try:
                self._fallback_body(session)
            except Exception as _:
                logging.error(f"An error occurred while executing '{self._body.__name__}' of state '{self._name}' in "
                              f"bot '{self._bot.name}'. See the attached exception:")
                traceback.print_exc()
        return

    def _check_next_transition(self, session):
        # TODO: Check conditional transitions
        for transition in self.transitions:
            if transition.event == auto:
                session.move(transition)
                return

    def run(self, session):
        logging.info(f"[{self._name}] Running body {self._body.__name__}")
        try:
            self._body(session)
        except Exception as _:
            logging.error(f"An error occurred while executing '{self._body.__name__}' of state '{self._name}' in bot '"
                          f"{self._bot.name}'. See the attached exception:")
            traceback.print_exc()
        self._check_next_transition(session)
