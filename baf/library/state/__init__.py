"""Library of predefined state bodies and state-factory helpers.

Import ``new_reasoning_state`` (and any future predefined-state factories)
directly from this package::

    from baf.library.state import new_reasoning_state
"""

from baf.library.state.reasoning_state_library import (
    new_reasoning_state,
    reasoning_body,
)
from baf.library.state.state_library import (
    default_body,
    default_fallback_body,
)

__all__ = [
    "default_body",
    "default_fallback_body",
    "new_reasoning_state",
    "reasoning_body",
]
