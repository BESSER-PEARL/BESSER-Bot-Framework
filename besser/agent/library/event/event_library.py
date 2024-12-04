"""
The collection of preexisting events.

Events are functions embedded in :class:`~besser.agent.core.transition.Transition` that, when called and return a `True`
value, trigger the transitions.
"""

from typing import Any, Callable, TYPE_CHECKING

from besser.agent.core.intent.intent import Intent

if TYPE_CHECKING:
    from besser.agent.core.session import Session


def auto(session: 'Session', event_params: dict) -> bool:
    """This event always returns True.

    Args:
        session (Session): the current user session
        event_params (dict): the event parameters

    Returns:
        bool: always true
    """
    return True


def intent_matched(session: 'Session', event_params: dict) -> bool:
    """This event checks if 2 intents are the same, used for intent matching checking.

    Args:
        session (Session): the current user session
        event_params (dict): the event parameters

    Returns:
        bool: True if the 2 intents are the same, false otherwise
    """
    if session.flags['predicted_intent']:
        target_intent: Intent = event_params['intent']
        matched_intent: Intent = session.predicted_intent.intent
        return target_intent.name == matched_intent.name


def variable_matches_operation(session: 'Session', event_params: dict) -> bool:
    """This event checks if for a specific comparison operation, using a stored session value
    and a given target value, returns true.

    Args:
        session (Session): the current user session
        event_params (dict): the event parameters

    Returns:
        bool: True if the comparison operation of the given values returns true
    """
    var_name: str = event_params['var_name']
    target_value: Any = event_params['target']
    operation: Callable[[Any, Any], bool] = event_params['operation']
    current_value: Any = session.get(var_name)
    return operation(current_value, target_value)


def file_received(session: 'Session', event_params: dict) -> bool:
    """This event only returns True if a user just sent a file.

    Args:
        session (Session): the current user session
        event_params (dict): the event parameters

    Returns:
        bool: True if the user has sent a file and (if specified) the received file type corresponds to the allowed
        types as defined in "allowed_types"
    """
    if session.flags['file']:
        if "allowed_types" in event_params.keys():
            if session.file.type in event_params["allowed_types"] or session.file.type == event_params["allowed_types"]:
                return True
            return False
        return True
    return False
