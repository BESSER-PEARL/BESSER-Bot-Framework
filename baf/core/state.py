import inspect
import traceback
from collections import deque
from typing import Any, Callable, TYPE_CHECKING, Union

from baf.core.transition.event import Event
from baf.core.transition.transition import Transition
from baf.core.transition.transition_builder import TransitionBuilder
from baf.library.intent.intent_library import fallback_intent
from baf.library.transition.events.base_events import ReceiveTextEvent, ReceiveFileEvent, WildcardEvent, ReceiveJSONEvent, GUIEvent
from baf.library.transition.conditions import IntentMatcher, VariableOperationMatcher, FormSubmitMatcher
from baf.core.transition.condition import Condition
from baf.core.intent.intent import Intent
from baf.core.session import Session
from baf.exceptions.exceptions import BodySignatureError, DuplicatedIntentMatchingTransitionError, \
    IntentNotFound
from baf.exceptions.logger import logger
from baf.library.transition.condition_functions import file_type
from baf.library.state.state_library import default_body, default_fallback_body
from baf.nlp.intent_classifier.intent_classifier_configuration import IntentClassifierConfiguration, \
    SimpleIntentClassifierConfiguration

if TYPE_CHECKING:
    from baf.core.agent import Agent


class State:
    """The State core component of an agent.

    The agent relies on a state machine to define its execution logic. Each state can run a set of actions, and the agent
    can navigate to other states through transitions that are triggered when events occur (e.g. an intent is matched).

    Args:
        agent (Agent): the agent the state belongs to
        name (str): the state's name
        initial (bool): whether the state is initial or not
        ic_config (IntentClassifierConfiguration): the intent classifier configuration of the state

    Attributes:
        _agent (Agent): The agent the state belongs to
        _name (str): The state name
        _initial (bool): Whether the state is initial or not
        _body (Callable[[Session], None]): The state body. It is a callable that takes as argument a
            :class:`~baf.core.session.Session`. It will be run whenever the agent moves to this state.
        _fallback_body (Callable[[Session], None]): The state fallback body. It is a callable that takes as argument a
            :class:`~baf.core.session.Session`. It will be run whenever the agent tries to move to another state,
            but it can't (e.g. an intent is matched but none of the current state's transitions are triggered on that
            intent)
        _ic_config (IntentClassifierConfiguration): the intent classifier configuration of the state
        _transition_counter (int): Count the number of transitions of this state. Used to name the transitions.
        intents (list[Intent]): The state intents, i.e. those that can be matched from a specific state
        transitions (list[Transition]): The state's transitions to other states
    """

    def __init__(
            self,
            agent: 'Agent',
            name: str,
            initial: bool = False,
            ic_config: IntentClassifierConfiguration or None = None
    ):
        self._agent: 'Agent' = agent
        self._name: str = name
        self._initial: bool = initial
        self._body: Callable[[Session], None] = default_body
        self._fallback_body: Callable[[Session], None] = default_fallback_body
        if not ic_config:
            ic_config = SimpleIntentClassifierConfiguration()
        self._ic_config: IntentClassifierConfiguration = ic_config
        self._transition_counter: int = 0
        self.intents: list[Intent] = []
        self.transitions: list[Transition] = []

    @property
    def agent(self):
        """Agent: The state's agent."""
        return self._agent

    @property
    def name(self):
        """str: The state name"""
        return self._name

    @property
    def initial(self):
        """bool: The initial status of the state (initial or non-initial)."""
        return self._initial

    @property
    def ic_config(self):
        """IntentClassifierConfiguration: the intent classifier configuration of the state."""
        return self._ic_config

    def __eq__(self, other):
        if type(other) is type(self):
            return self._name == other.name and self._agent.name == other.agent.name
        else:
            return False

    def __hash__(self):
        return hash((self._name, self._agent.name))

    def _t_name(self):
        """Name generator for transitions. Transition names are generic and enumerated. On each call, a new name is
        generated and the transition counter is incremented for the next name.

        Returns:
            str: a name for the next transition
        """
        self._transition_counter += 1
        return f"t_{self._transition_counter}"

    def set_global(self, intent: Intent):
        """Set state as globally accessible state.

        Args:
            intent (Intent): the intent that should trigger the jump to the global state
        """
        self.agent.global_initial_states.append((self, intent))
        self.agent.global_state_component[self] = [self]
        # Check whether the states from the global component are already in the list
        # Currently only works for linear states
        transitions = self.transitions
        while transitions:
            transition = transitions[0]
            if transition not in self.agent.global_state_component[self]:
                self.agent.global_state_component[self].append(transition.dest)
            transitions = transition.dest.transitions

    def set_body(self, body: Callable[[Session], None]) -> None:
        """Set the state body.

        Args:
            body (Callable[[Session], None]): the body
        """
        body_signature = inspect.signature(body)
        body_template_signature = inspect.signature(default_body)
        if body_signature.parameters != body_template_signature.parameters:
            raise BodySignatureError(self._agent, self, body, body_template_signature, body_signature)
        self._body = body

    def body(self, func: Callable[[Session], None]) -> Callable[[Session], None]:
        """Decorator to set the state body.

        Usage::

            @state.body
            def my_body(session: Session):
                ...

        Args:
            func (Callable[[Session], None]): the body function

        Returns:
            Callable[[Session], None]: the body function unchanged
        """
        self.set_body(func)
        return func

    def set_fallback_body(self, body: Callable[[Session], None]):
        """Set the state fallback body.

        Args:
            body (Callable[[Session], None]): the fallback body
        """
        body_signature = inspect.signature(body)
        body_template_signature = inspect.signature(default_fallback_body)
        if body_signature.parameters != body_template_signature.parameters:
            raise BodySignatureError(self._agent, self, body, body_template_signature, body_signature)
        self._fallback_body = body

    def _check_global_state(self, dest: 'State'):
        """Add state to global state component if condition is met.

        If the previous state is a global state, add this state to the component's list
        of the global state.

        Args:
            dest (State): the destination state
        """
        if any(self in global_state for global_state in self.agent.global_initial_states):
            self.agent.global_state_component[self].append(dest)
            return
        for global_state in self.agent.global_state_component:
            if self in self.agent.global_state_component[global_state]:
                self.agent.global_state_component[global_state].append(dest)

    def when_event(self, event: Event or None = None) -> TransitionBuilder:
        """Start the definition of an "event matching" transition on this state.

        Args:
            event (Event): the target event for the transition to be triggered. If none, any event can trigger this
                transition.
        Returns:
            TransitionBuilder: the transition builder
        """
        if not event:
            event = WildcardEvent()
        return TransitionBuilder(source=self, event=event)

    def when_condition(
            self,
            function: Union[
                Callable[[Session], bool],
                Callable[[Session, dict], bool]
            ],
            params: dict = None
    ) -> TransitionBuilder:
        """Start the definition of a "condition matching" transition on this state.

        Args:
            function (Union[Callable[[Session], bool], Callable[[Session, dict], bool]]): the condition function to add
                to the transition. Allowed function arguments are (:class:`~baf.core.session.Session`) or
                (:class:`~baf.core.session.Session`, dict) to add parameters within the dict argument. The
                function must return a boolean value
            params (dict, optional): the parameters for the condition function, necessary if the function has
                (:class:`~baf.core.session.Session`, dict) arguments
        Returns:
            TransitionBuilder: the transition builder
        """
        return TransitionBuilder(source=self, event=None).with_condition(function, params)

    def when_intent_matched(self, intent: Intent) -> TransitionBuilder:
        """Start the definition of an "intent matching" transition on this state.

        Args:
            intent (Intent): the target intent for the transition to be triggered

        Returns:
            TransitionBuilder: the transition builder
        """
        if intent in self.intents:
            raise DuplicatedIntentMatchingTransitionError(self, intent)
        if intent not in self._agent.intents:
            raise IntentNotFound(self._agent, intent)
        self.intents.append(intent)
        event: ReceiveTextEvent = ReceiveTextEvent()
        condition: Condition = IntentMatcher(intent)
        transition_builder: TransitionBuilder = TransitionBuilder(source=self, event=event, condition=condition)
        return transition_builder

    def go_to(self, dest: 'State') -> None:
        """Create a new `auto` transition on this state.

        This transition needs no event nor condition to be triggered, which means that when the agent moves to a state
        that has an `auto` transition, the agent will move to the transition's destination state. This transition cannot
        be combined with other transitions.

        Args:
            dest (State): the destination state
        """

        transition_builder: TransitionBuilder = TransitionBuilder(source=self, event=None, condition=None)
        transition_builder.go_to(dest)

    def when_no_intent_matched(self) -> TransitionBuilder:
        event: ReceiveTextEvent = ReceiveTextEvent()
        condition: Condition = IntentMatcher(fallback_intent)
        transition_builder: TransitionBuilder = TransitionBuilder(source=self, event=event, condition=condition)
        return transition_builder

    def when_variable_matches_operation(
            self,
            var_name: str,
            operation: Callable[[Any, Any], bool],
            target: Any,
    ) -> TransitionBuilder:
        """Start the definition of a "variable matching operator" transition on this state.

        This transition evaluates if (variable operator target_value) is satisfied. For instance, "age > 18".

        Args:
            var_name (str): the name of the variable to evaluate. The variable must exist in the user session
            operation (Callable[[Any, Any], bool]): the operation to apply to the variable and the target value. It
                gets as arguments the variable and the target value, and returns a boolean value
            target (Any): the target value to compare with the variable

        Returns:
            TransitionBuilder: the transition builder
        """
        condition: Condition = VariableOperationMatcher(var_name, operation, target)
        transition_builder: TransitionBuilder = TransitionBuilder(source=self, condition=condition)
        return transition_builder

    def when_file_received(self, allowed_types: list[str] or str = None) -> TransitionBuilder:
        """Start the definition of a "file received" transition on this state.

        Args:
            allowed_types (list[str] or str): the file types to consider for this transition. List of strings or just 1
                string are valid values

        Returns:
            TransitionBuilder: the transition builder
        """
        event = ReceiveFileEvent()
        if allowed_types:
            params = {'allowed_types': allowed_types}
        else:
            params = {}
        transition_builder: TransitionBuilder = TransitionBuilder(source=self, event=event)
        transition_builder.with_condition(function=file_type, params=params)
        return transition_builder

    def when_form_submitted(self, form_id: str = None) -> TransitionBuilder:
        """Start the definition of a "form submitted" transition on this state.

        Triggered when the user submits a GUI form. If ``form_id`` is provided, only submissions
        from the GUI with that message id will trigger the transition; otherwise any form
        submission will match.

        Args:
            form_id (str, optional): the message id of the :class:`~baf.core.gui.agent_gui.AgentGUI`
                whose form submissions should trigger this transition. Use ``agent_gui.id`` to
                obtain the id of a specific GUI. If None, any form submission triggers this
                transition.

        Returns:
            TransitionBuilder: the transition builder
        """
        event: GUIEvent = GUIEvent()
        condition: FormSubmitMatcher = FormSubmitMatcher(form_id)
        return TransitionBuilder(source=self, event=event, condition=condition)

    def check_transitions(self, session: Session) -> None:
        """Check the state transitions and triggers the one that is satisfied.

        When checking transition, the priority is based on transition order.

        For a given transition expecting an event to happen, the first event matching will be used (and removed from the
        session queue of events).

        If a user message event is received but does not match the transition, run the fallback body (and the event is
        removed from the session queue of events)

        Args:
            session (Session): the current session
        """
        last_event = session.event
        run_fallback = False
        for i, next_transition in enumerate(self.transitions):
            if next_transition.is_event():
                # TODO: Decide policy to remove events
                fallback_deque = deque()
                while session.events:
                    session.event = session.events.pop()
                    if isinstance(session.event, ReceiveTextEvent):
                        session.event.predict_intent(session)
                    elif isinstance(session.event, ReceiveJSONEvent) and session.event.contains_message:
                        session.event.predict_intent(session)
                    if next_transition.evaluate(session, session.event):
                        session.move(next_transition)
                        # TODO: Make this configurable (we can consider remove all the previously checked events)
                        session.events.extend(fallback_deque)  # We restore the queue but with the matched event removed
                        return
                    if (isinstance(session.event, ReceiveTextEvent) and session.event.human) or (isinstance(session.event, ReceiveJSONEvent) and session.event.contains_message and session.event.human):
                        # There is a ReceiveTextEvent or ReceiveJSONEvent (with message) and we couldn't match any transition so far
                        run_fallback = True
                        if i < len(self.transitions)-1:
                            # We only append ReceiveTextEvent or ReceiveJSONEvent (human with message) if we didn't finish checking all transitions
                            fallback_deque.appendleft(session.event)
                    else:
                        fallback_deque.appendleft(session.event)
                session.events.extend(fallback_deque)
            else:
                if next_transition.is_condition_true(session):
                    session.move(next_transition)
                    return
        if run_fallback:
            # There was one or more transitions with ReceiveMessageEvent and one ReceiveMessageEvent (human)
            # that didn't match any transition
            self._agent._monitoring_db_insert_intent_prediction(session, session.event.predicted_intent)  # insert fallback intent in DB
            logger.info(f"[{self._name}] Running fallback body {self._fallback_body.__name__}")
            try:
                self._fallback_body(session)
            except Exception as _:
                logger.error(f"An error occurred while executing '{self._fallback_body.__name__}' of state"
                            f"'{self._name}' in agent '{self._agent.name}'. See the attached exception:")
                traceback.print_exc()
        session.event = last_event

    def run(self, session: Session) -> None:
        """Run the state body.

        Args:
            session (Session): the user session
        """
        logger.info(f"[{self._name}] Running body {self._body.__name__}")
        try:
            self._body(session)
        except Exception as _:
            logger.error(f"An error occurred while executing '{self._body.__name__}' of state '{self._name}' in agent '"
                         f"{self._agent.name}'. See the attached exception:")
            traceback.print_exc()
        # Reset current event
        # session.event = None  # If we remove the event, if there is an automatic or condition-based transition, we lose the event
