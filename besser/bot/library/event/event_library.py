"""
The collection of preexisting events.

Events are functions embedded in :class:`~besser.bot.core.transition.Transition` that, when called and return a `True`
value, trigger the transitions.
"""

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
