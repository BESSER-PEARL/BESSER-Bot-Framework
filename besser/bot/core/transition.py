import logging
import traceback
from typing import Callable, TYPE_CHECKING

from besser.bot.library.event.event_library import auto, intent_matched, variable_matches_operation

if TYPE_CHECKING:
    from besser.bot.core.session import Session
    from besser.bot.core.state import State


class Transition:
    """A bot transition from one state (source) to another (destination).

    A transition is triggered when an event occurs.

    Args:
        name (str): the transition name
        source (State): the source state of the transition (from where it is triggered)
        dest (State): the destination state of the transition (where the bot moves to)
        event (Callable[[Session, dict], bool]): the event that triggers the transition
        event_params (dict): the parameters associated to the event

    Attributes:
        name (str): The transition name
        source (State): The source state of the transition (from where it is triggered)
        dest (State): The destination state of the transition (where the bot moves to)
        event (Callable[[Session, dict], bool]): The event that triggers the transition
        event_params (dict): The parameters associated to the event
    """

    def __init__(
            self,
            name: str,
            source: 'State',
            dest: 'State',
            event: Callable[['Session', dict], bool],
            event_params: dict
    ):
        self.name: str = name
        self.source: 'State' = source
        self.dest: 'State' = dest
        self.event: Callable[['Session', dict], bool] = event
        self.event_params: dict = event_params

    def log(self) -> str:
        """Create a log message for the transition. Useful when transitioning from one state to another to track the bot
        state.

        Example: `intent_matched (hello_intent): [state_0] --> [state_1]`

        Returns:
            str: the log message
        """
        if self.event == intent_matched:
            return f"{self.event.__name__} ({self.event_params['intent'].name}): [{self.source.name}] --> " \
                   f"[{self.dest.name}]"
        elif self.event == auto:
            return f"{self.event.__name__}: [{self.source.name}] --> [{self.dest.name}]"
        elif self.event == variable_matches_operation:
            return f"({self.event_params['var_name']} " \
                   f"{self.event_params['operation'].__name__} " \
                   f"{self.event_params['target']}): " \
                   f"[{self.source.name}] --> [{self.dest.name}]"
        else:
            return f"{self.event.__name__}: [{self.source.name}] --> [{self.dest.name}]"

    def is_intent_matched(self, session: 'Session') -> bool:
        """For `intent-matching` transitions, check if the predicted intent (stored in the given session) matches with
        the transition's expected intent (stored in the transition event parameters).

        If the transition event is not `intent_matched`, return false.

        Args:
            session (Session): the session in which the to be compared value is stored

        Returns:
            bool: true if the transition's intent matches with the target one, false otherwise
        """
        if self.event == intent_matched:
            return self.is_event_true(session)
        return False

    def is_variable_matching_operation(self, session: 'Session') -> bool:
        """For `session-value-comparison` transitions, check if the given operation on a stored session 
        value and a given target value (stored in the transition event parameters) returns true.

        If the transition event is not `variable_matches_operation`, return false.

        Args:
            session (Session): the session in which the value to be compared is stored

        Returns:
            bool: true if the operation on stored and target values returns true, false otherwise
        """
        if self.event == variable_matches_operation:
            return self.is_event_true(session)
        return False

    def is_event_true(self, session: 'Session') -> bool:
        """Given a session, returns true if the event associated to the transition returns true, and false otherwise.
        (Applicable to any event)

        Args:
            session (Session): the session in which some user data can be stored and used within the event

        Returns:
            bool: true if the transition's event returned true, false otherwise
        """
        try:
            return self.event(session, self.event_params)
        except Exception as e:
            logging.error(f"An error occurred while executing '{self.event.__name__}' event from state "
                          f"'{self.source.name}'. See the attached exception:")
            traceback.print_exc()
        return False

    def is_auto(self) -> bool:
        """Check if the transition event is `auto` (i.e. a transition that does not need any event to be triggered).

        Returns:
            bool: true if the transition's intent matches with the
            target one, false
        """
        return self.event == auto
