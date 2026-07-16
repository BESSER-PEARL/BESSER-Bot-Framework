"""
The collection of preexisting Conditions.

A condition can be embedded in a :class:`~baf.core.transition.transition.Transition` so that when it is
satisfied, the transition will be triggered (given that the other transition conditions are satisfied as well)
"""

from functools import partial
from typing import Callable, Any

from baf.core.intent.intent import Intent
from baf.core.transition.condition import Condition
from baf.library.transition.condition_functions import intent_matched, variable_matches_operation, form_submitted


class IntentMatcher(Condition):
    """A condition that checks if an incoming intent matches a predefined intent.

    Args:
        intent (Intent): the target intent

    Attributes:
        _intent (Intent): the target intent
    """

    def __init__(self, intent: Intent):

        super().__init__(partial(intent_matched, params={'intent': intent}))
        self._intent: Intent = intent

    def __str__(self):
        return f"Intent Matching - {self._intent.name}"


class VariableOperationMatcher(Condition):
    """A condition that checks if (variable operator target_value) is satisfied. For instance, "age > 18".

    Args:
        var_name (str): the name of the variable to evaluate. The variable must exist in the user session
        operation (Callable[[Any, Any], bool]): the operation to apply to the variable and the target value. It
            gets as arguments the variable and the target value, and returns a boolean value
        target (Any): the target value to compare with the variable

    Attributes:
        _var_name (str): the name of the variable to evaluate. The variable must exist in the user session
        _operation (Callable[[Any, Any], bool]): the operation to apply to the variable and the target value. It
            gets as arguments the variable and the target value, and returns a boolean value
        _target (Any): the target value to compare with the variable
    """

    def __init__(
            self,
            var_name: str,
            operation: Callable[[Any, Any], bool],
            target: Any
    ):
        super().__init__(
            partial(
                variable_matches_operation,
                params={
                    'var_name': var_name, 'operation': operation, 'target': target
                }
            )
        )
        self._var_name: str = var_name
        self._operation: Callable[[Any, Any], bool] = operation
        self._target: Any = target

    def __str__(self):
        return f"{self._var_name} " \
               f"{self._operation.__name__} " \
               f"{self._target}"


class FormSubmitMatcher(Condition):
    """A condition that checks if the current event is a GUI form submission.

    Optionally filters by a specific GUI message id (``form_id``).

    Args:
        form_id (str or None): the message id of the GUI whose form submissions should trigger the
            transition. If None, any form submission matches.

    Attributes:
        _form_id (str or None): the target form id, or None to match any form submission
    """

    def __init__(self, form_id: str = None):
        super().__init__(partial(form_submitted, params={'form_id': form_id}))
        self._form_id: str = form_id

    def __str__(self):
        if self._form_id:
            return f"Form Submit Matching - {self._form_id}"
        return "Form Submit Matching"
