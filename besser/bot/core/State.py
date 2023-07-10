import inspect
import logging
import traceback

from besser.bot.library.event.EventLibrary import auto, intent_matched
from besser.bot.exceptions.exceptions import BodySignatureError, DuplicatedIntentMatchingTransitionError, \
    StateNotFound, IntentNotFound, DuplicatedAutoTransitionError
from besser.bot.core.Transition import Transition
from besser.bot.library.intent.IntentLibrary import fallback_intent
from besser.bot.library.state.StateLibrary import default_fallback_body, body_template


class State:

    def __init__(self, bot, name: str, initial=False):
        self.bot = bot
        self.name = name
        self.initial = initial
        self.body = None
        self.intents = []
        self.transitions = []
        self.transition_counter = 0
        self.fallback_body = default_fallback_body

    def __eq__(self, other):
        if type(other) is type(self):
            return self.name == other.name and self.bot.name == other.bot.name
        else:
            return False

    def __hash__(self):
        return hash((self.name, self.bot.name))

    def get_intent(self, name: str):
        for intent in self.intents:
            if intent.name == name:
                return intent
        return None

    def t_name(self):
        self.transition_counter += 1
        return f"t_{self.transition_counter}"

    def set_body(self, body):
        body_signature = inspect.signature(body)
        body_template_signature = inspect.signature(body_template)
        if body_signature.parameters != body_template_signature.parameters:
            raise BodySignatureError(self.bot, self, body, body_template_signature, body_signature)
        self.body = body

    def set_fallback_body(self, body):
        body_signature = inspect.signature(body)
        body_template_signature = inspect.signature(default_fallback_body)
        if body_signature.parameters != body_template_signature.parameters:
            raise BodySignatureError(self.bot, self, body, body_template_signature, body_signature)
        self.fallback_body = body

    def when_event_go_to(self, event, dest, event_params: dict):
        if event == intent_matched:
            # TODO: CHECK isinstance(obj, Intent)
            # TODO: handle exceptions
            intent = event_params['intent']
            self.intents.append(intent)
        self.transitions.append(Transition(name=self.t_name(), source=self, dest=dest, event=event,
                                           event_params=event_params))

    def go_to(self, dest):
        for transition in self.transitions:
            if transition.is_auto():
                raise DuplicatedAutoTransitionError(self.bot, self)
        self.transitions.append(Transition(name=self.t_name(), source=self, dest=dest, event=auto, event_params={}))

    def when_intent_matched_go_to(self, intent, dest):
        if intent in self.intents:
            raise DuplicatedIntentMatchingTransitionError(self, intent)
        if intent not in self.bot.intents:
            raise IntentNotFound(self.bot, intent)
        if dest not in self.bot.states:
            raise StateNotFound(self.bot, dest)
        event_params = {'intent': intent}
        self.intents.append(intent)
        self.transitions.append(Transition(name=self.t_name(), source=self, dest=dest, event=intent_matched,
                                           event_params=event_params))

    def receive_intent(self):
        classification = self.bot.session.get_predicted_intent()
        if classification is None:
            self.bot.session.put_answer("Something went wrong, no intent was predicted")
            return
        auto_transition = None
        for transition in self.transitions:
            if transition.is_intent_matched(classification.intent):
                self.bot.move(transition)
                return
            if transition.is_auto():
                auto_transition = transition
        if auto_transition:
            # When no intent is matched, but there is an auto transition, move through it
            self.bot.move(auto_transition)
            return
        if classification.intent == fallback_intent:
            logging.info(f"[{self.name}] Running fallback body {self.fallback_body.__name__}")
            try:
                self.fallback_body(self.bot.session)
            except Exception as _:
                logging.error(f"An error occurred while executing '{self.body.__name__}' of state '{self.name}' in bot "
                              f"'{self.bot.name}'. See the attached exception:")
                traceback.print_exc()
        return

    def check_next_transition(self):
        # TODO: Check conditional transitions
        for transition in self.transitions:
            if transition.event == auto:
                self.bot.move(transition)
                return

    def run(self):
        logging.info(f"[{self.name}] Running body {self.body.__name__}")
        try:
            self.body(self.bot.session)
        except Exception as _:
            logging.error(f"An error occurred while executing '{self.body.__name__}' of state '{self.name}' in bot '{self.bot.name}'. See the attached exception:")
            traceback.print_exc()
        self.check_next_transition()
