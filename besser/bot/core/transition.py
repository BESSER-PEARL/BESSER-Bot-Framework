from typing import Callable, TYPE_CHECKING

from besser.bot.core.intent.intent import Intent
from besser.bot.library.event.event_library import auto, intent_matched

if TYPE_CHECKING:
    from besser.bot.core.state import State


class Transition:
    """A bot transition from one state (source) to another (destination).

    A transition is triggered when an event occurs.

    Args:
        name (str): the transition name
        source (State): the source state of the transition (from where it is triggered)
        dest (State): the destination state of the transition (where the bot moves to)
        event (Callable[..., bool]): the event that triggers the transition
        event_params (dict): the parameters associated to the event

    Attributes:
        name (str): The transition name
        source (State): The source state of the transition (from where it is triggered)
        dest (State): The destination state of the transition (where the bot moves to)
        event (Callable[..., bool]): The event that triggers the transition
        event_params (dict): The parameters associated to the event
    """

    def __init__(
            self,
            name: str,
            source: 'State',
            dest: 'State',
            event: Callable[..., bool],
            event_params: dict
    ):
        self.name: str = name
        self.source: 'State' = source
        self.dest: 'State' = dest
        self.event: Callable[..., bool] = event
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
        else:
            return f"{self.event.__name__}: [{self.source.name}] --> [{self.dest.name}]"

    def is_intent_matched(self, intent: Intent) -> bool:
        """For `intent-matching` transitions, check if the given intent matches with the transition's expected intent
        (stored in the transition event parameters).

        If the transition event is not `intent-matching`, return false.

        Args:
            intent (Intent): the target intent

        Returns:
            bool: true if the transition's intent matches with the
            target one, false otherwise
        """
        if self.event == intent_matched:
            target_intent = self.event_params['intent']
            return self.event(target_intent, intent)
        return False

    def is_auto(self) -> bool:
        """Check if the transition event is `auto` (i.e. a transition that does not need any event to be triggered).

        Returns:
            bool: true if the transition's intent matches with the
            target one, false
        """
        return self.event == auto
