import inspect
import logging
import traceback

from besser.bot.core.intent.intent import Intent
from besser.bot.core.session import Session
from besser.bot.library.event.event_library import auto, intent_matched
from besser.bot.exceptions.exceptions import BodySignatureError, DuplicatedIntentMatchingTransitionError, \
    StateNotFound, IntentNotFound, DuplicatedAutoTransitionError, ConflictingAutoTransitionError
from besser.bot.core.transition import Transition
from besser.bot.library.intent.intent_library import fallback_intent
from besser.bot.library.state.state_library import default_fallback_body, default_body

from typing import Callable, TYPE_CHECKING

from besser.bot.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction

if TYPE_CHECKING:
    from besser.bot.core.bot import Bot


class State:
    """The State core component of a bot.

    The bot relies on a state machine to define its execution logic. Each state can run a set of actions, and the bot
    can navigate to other states through transitions that are triggered when events occur (e.g. an intent is matched).

    Args:
        bot (Bot): the bot the state belongs to
        name (str): the state's name
        initial (bool): weather the state is initial or not

    Attributes:
        _bot (Bot): The bot the state belongs to
        _name (str): The state name
        _initial (bool): Weather the state is initial or not
        _body (Callable[[Session], None]): The state body. It is a callable that takes as argument a
            :class:`~besser.bot.core.session.Session`. It will be run whenever the bot moves to this state.
        _fallback_body (Callable[[Session], None]): The state fallback body. It is a callable that takes as argument a
            :class:`~besser.bot.core.session.Session`. It will be run whenever the bot tries to move to another state,
            but it can't (e.g. an intent is matched but none of the current state's transitions are triggered on that
            intent)
        _transition_counter (int): Count the number of transitions of this state. Used to name the transitions.
        intents (list[Intent]): The state intents, i.e. those that can be matched from a specific state
        transitions (list[Transition]): The state's transitions to other states
    """

    def __init__(
            self,
            bot: 'Bot',
            name: str,
            initial: bool = False
    ):
        self._bot: 'Bot' = bot
        self._name: str = name
        self._initial: bool = initial
        self._body: Callable[[Session], None] = default_body
        self._fallback_body: Callable[[Session], None] = default_fallback_body
        self._transition_counter: int = 0
        self.intents: list[Intent] = []
        self.transitions: list[Transition] = []

    @property
    def bot(self):
        """Bot: The state's bot."""
        return self._bot
    
    @property
    def name(self):
        """str: The state name"""
        return self._name
    
    @property
    def initial(self):
        """bool: The initial status of the state (initial or non-initial)."""
        return self._initial

    def __eq__(self, other):
        if type(other) is type(self):
            return self._name == other.name and self._bot.name == other.bot.name
        else:
            return False

    def __hash__(self):
        return hash((self._name, self._bot.name))

    def _t_name(self):
        """Name generator for transitions. Transition names are generic and enumerated. On each call, a new name is
        generated and the transition counter is incremented for the next name.

        Returns:
            str: a name for the next transition
        """
        self._transition_counter += 1
        return f"t_{self._transition_counter}"

    def set_body(self, body: Callable[[Session], None]) -> None:
        """Set the state body.

        Args:
            body (Callable[[Session], None]): the body
        """
        body_signature = inspect.signature(body)
        body_template_signature = inspect.signature(default_body)
        if body_signature.parameters != body_template_signature.parameters:
            raise BodySignatureError(self._bot, self, body, body_template_signature, body_signature)
        self._body = body

    def set_fallback_body(self, body: Callable[[Session], None]):
        """Set the state fallback body.

        Args:
            body (Callable[[Session], None]): the fallback body
        """
        body_signature = inspect.signature(body)
        body_template_signature = inspect.signature(default_fallback_body)
        if body_signature.parameters != body_template_signature.parameters:
            raise BodySignatureError(self._bot, self, body, body_template_signature, body_signature)
        self._fallback_body = body

    def when_event_go_to(self, event: Callable[..., bool], dest: 'State', event_params: dict) -> None:
        """Create a new transition on this state.

        When the bot is in a state and a state's transition event occurs, the bot will move to the destination state
        of the transition.

        Args:
            event (Callable[..., bool]): the transition event
            dest (State): the destination state
            event_params (dict): the parameters associated to the event
        """
        for transition in self.transitions:
            if transition.event.is_auto():
                raise ConflictingAutoTransitionError(self._bot, self)
        if event == intent_matched:
            # TODO: CHECK isinstance(obj, Intent)
            # TODO: handle exceptions
            intent = event_params['intent']
            self.intents.append(intent)
        self.transitions.append(Transition(name=self._t_name(), source=self, dest=dest, event=event,
                                           event_params=event_params))

    def go_to(self, dest: 'State') -> None:
        """Create a new `auto` transition on this state.

        This transition needs no event to be triggered, which means that when the bot moves to a state 
        that has an `auto` transition, the bot will move to the transition's destination state 
        unconditionally without waitng for user input. This transition cannot be combined with other 
        transitions.

        Args:
            dest (State): the destination state
        """
        if self.transitions:
            raise ConflictingAutoTransitionError(self._bot, self)
        self.transitions.append(Transition(name=self._t_name(), source=self, dest=dest, event=auto, event_params={}))

    def when_intent_matched_go_to(self, intent: Intent, dest: 'State') -> None:
        """Create a new `intent matching` transition on this state.

        When the bot is in a state and an intent is received (the intent is predicted from a user message),
        if the transition event is to receive this particular intent, the bot will move to the transition's destination
        state.

        Args:
            intent (Intent): the transition intent
            dest (State): the destination state
        """
        if intent in self.intents:
            raise DuplicatedIntentMatchingTransitionError(self, intent)
        if intent not in self._bot.intents:
            raise IntentNotFound(self._bot, intent)
        if dest not in self._bot.states:
            raise StateNotFound(self._bot, dest)
        for transition in self.transitions:
            if transition.is_auto():
                raise ConflictingAutoTransitionError(self._bot, self)
        event_params = {'intent': intent}
        self.intents.append(intent)
        self.transitions.append(Transition(name=self._t_name(), source=self, dest=dest, event=intent_matched,
                                           event_params=event_params))
    
    def when_no_intent_matched_go_to(self, dest: 'State') -> None:
        """Create a new `no intent matching` transition on this state.

        When the bot is in a state and no fitting intent is received (the intent is predicted from a user message), 
        the bot will move to the transition's destination
        state. If no other transition is specified, the bot will wait for a user message regardless.

        Args:
            dest (State): the destination state
        """
        event_params = {'intent': fallback_intent}
       # self.intents.append(fallback_intent)
        if dest not in self._bot.states:
            raise StateNotFound(self._bot, dest)
        for transition in self.transitions:
            if transition.is_auto():
                raise ConflictingAutoTransitionError(self._bot, self)
        self.transitions.append(Transition(name=self._t_name(), source=self, dest=dest, event=intent_matched,
                                           event_params=event_params))   

    def receive_intent(self, session: Session) -> None:
        """Receive an intent from a user session (which is predicted from the user message).

        When receiving an intent it looks for the state's transition whose trigger event is to match that intent.
        The fallback body is run when the received intent does not match any transition intent (i.e. fallback intent).

        Args:
            session (Session): the user session that sent the message
        """
        predicted_intent: IntentClassifierPrediction = session.predicted_intent
        if predicted_intent is None:
            logging.error("Something went wrong, no intent was predicted")
            return
        auto_transition = None
        for transition in self.transitions:
            if transition.is_intent_matched(predicted_intent.intent):
                session.move(transition)
                return
            if transition.is_auto():
                auto_transition = transition
        if auto_transition:
            # When no intent is matched, but there is an auto transition, move through it
            session.move(auto_transition)
            return
        if predicted_intent.intent == fallback_intent:
            # When no intent is matched (i.e. intent == fallback_intent), run the fallback body of the state
            logging.info(f"[{self._name}] Running fallback body {self._fallback_body.__name__}")
            try:
                self._fallback_body(session)
            except Exception as _:
                logging.error(f"An error occurred while executing '{self._body.__name__}' of state '{self._name}' in "
                              f"bot '{self._bot.name}'. See the attached exception:")
                traceback.print_exc()

    def _check_next_auto_transition(self, session: Session) -> None:
        """Check weather the first defined transition of the state is an `auto` transition, and if so, move to its
        destination state.

        This method is intended to be called after running the body of a state.

        Args:
            session (Session): the user session
        """
        # TODO: Check conditional transitions
        if self.transitions[0].is_auto():
            session.move(self.transitions[0])

    def run(self, session: Session) -> None:
        """Run the state (i.e. its body). After running the body, check if the first defined transition of the state is
        an `auto` transition, and if so, move to its destination state.

        Args:
            session (Session): the user session
        """
        logging.info(f"[{self._name}] Running body {self._body.__name__}")
        try:
            self._body(session)
        except Exception as _:
            logging.error(f"An error occurred while executing '{self._body.__name__}' of state '{self._name}' in bot '"
                          f"{self._bot.name}'. See the attached exception:")
            traceback.print_exc()
        self._check_next_auto_transition(session)
