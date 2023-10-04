"""
The collection of preexisting events.

Events are functions embedded in :class:`~besser.bot.core.transition.Transition` that, when called and return a `True`
value, trigger the transitions.
"""

import operator
from typing import Any

from besser.bot.core.intent.intent import Intent


def auto() -> bool:
    """This event always returns True."""
    return True


def intent_matched(target_intent: Intent, matched_intent: Intent) -> bool:
    """
    This event checks if 2 intents are the same, used for intent matching checking.

    Args:
        target_intent (Intent): the target intent
        matched_intent (Intent): the intent that was matched from a user input

    Returns:
        bool: True if the 2 intents are the same, false otherwise
    """
    return target_intent.name == matched_intent.name


def session_operation_matched(current_value: Any, operation: operator, target_value: Any) -> bool:
    """
    This event checks if for a specific comparison operation, using a stored session value
    and a given target value, returns true.

    Args:
        current_value (Any): the stored value
        operation (operator): the comparison operation to be used
        target_value (Any): the target value to compare to

    Returns:
        bool: True if the comparison operation of the given values returns true
    """
    return operation(current_value, target_value)
