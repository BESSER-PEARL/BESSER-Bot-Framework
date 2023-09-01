from besser.bot.library.event.event_library import intent_matched, auto
from besser.bot.core.intent.intent import Intent

from typing import Callable, TYPE_CHECKING
if TYPE_CHECKING:
    from besser.bot.core.state import State


class Transition:
    """
    A bot transition from one state (source) to another (destination).

    A transition is triggered when an event occurs.

    :param name: the transition name
    :type name: str
    :param source: the source state of the transition (from where it is triggered)
    :type source: State
    :param dest: the destination state of the transition (where the bot moves to)
    :type dest: State
    :param event: the event that triggers the transition
    :type event: Callable[..., bool]
    :param event_params: the parameters associated to the event
    :type event_params: dict

    :ivar str name: the transition name
    :ivar State source: the source state of the transition (from where it is triggered)
    :ivar State dest: the destination state of the transition (where the bot moves to)
    :ivar Callable[..., bool] event: the event that triggers the transition
    :ivar dict event_params: the parameters associated to the event
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
        """
        Create a log message for the transition. Useful when transitioning from one state to another to track the bot
        state.

        Example: `intent_matched (hello_intent): [state_0] --> [state_1]`

        :return: the log message
        :rtype: str
        """
        if self.event == intent_matched:
            return f"{self.event.__name__} ({self.event_params['intent'].name}): [{self.source.name}] --> " \
                   f"[{self.dest.name}]"
        elif self.event == auto:
            return f"{self.event.__name__}: [{self.source.name}] --> [{self.dest.name}]"

    def is_intent_matched(self, intent: Intent) -> bool:
        """
        For `intent-matching` transitions, check if the given intent matches with the transition's expected intent
        (stored in the transition event parameters).
        If the transition event is not `intent-matching`, return false.

        :param intent: the target intent
        :type intent: Intent
        :return: true if the transition's intent matches with the target one, false otherwise
        :rtype: bool
        """
        if self.event == intent_matched:
            target_intent = self.event_params['intent']
            return self.event(target_intent, intent)
        return False

    def is_auto(self) -> bool:
        """
        Check if the transition event is `auto` (i.e. a transition that does not need any event to be triggered).

        :return: true if the transition's intent matches with the target one, false
        :rtype: bool
        """
        return self.event == auto
