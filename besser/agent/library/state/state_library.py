"""
The collection of preexisting states and bodies.
"""

from besser.agent.core.session import Session


def default_body(session: Session) -> None:
    """
    The default body of a state. Does nothing.

    Used when no body is defined in a state.

    Used as a reference for bodies method signatures.

    Args:
        session (Session): the current user session
    """
    pass


def default_fallback_body(session: Session) -> None:
    """
    The default fallback body of a state.

    Used when no fallback body is defined in a state.

    Used as a reference for fallback bodies method signatures.

    Args:
        session (Session): the current user session
    """
    session.reply("Sorry, I didn't get it")
