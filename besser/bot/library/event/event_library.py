"""
The collection of preexisting events.

Events are functions embedded in :class:`~besser.bot.core.transition.Transition` that, when called and return a `True`
value, trigger the transitions.
"""

import operator
from typing import Any, TYPE_CHECKING

from besser.bot.core.intent.intent import Intent

if TYPE_CHECKING:
    from besser.bot.core.session import Session


def auto() -> bool:
    """This event always returns True."""
    return True


def intent_matched(session: 'Session', event_params: dict) -> bool:
    """
    This event checks if 2 intents are the same, used for intent matching checking.

    Args:
        session (Session): the current user session
        event_params (dict): the event parameters

    Returns:
        bool: True if the 2 intents are the same, false otherwise
    """
    target_intent: Intent = event_params['intent']
    matched_intent: Intent = session.predicted_intent.intent
    return target_intent.name == matched_intent.name


def session_operation_matched(session: 'Session', event_params: dict) -> bool:
    """
    This event checks if for a specific comparison operation, using a stored session value
    and a given target value, returns true.

    Args:
        session (Session): the current user session
        event_params (dict): the event parameters

    Returns:
        bool: True if the comparison operation of the given values returns true
    """
    var_name: str = event_params['var_name']
    target_value: Any = event_params['target']
    operation: operator = event_params['operation']
    current_value: Any = session.get(var_name)
    return operation(current_value, target_value)
