"""TBA"""
from returns import result as _result

# Abstract Machine related imports
from core.base.state import State as BaseState
from core.base.transition import Transition as BaseTransition

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts


class DFATransition(BaseTransition):

    def __init__(self, start_state: BaseState, transition_target_state: BaseState, condition_char: str) -> None:
        super().__init__(start_state, transition_target_state)

        self.condition_char: str = condition_char

    def canTransition(self, current_input: _ty.Any) -> _result.Result:
        if self.condition_char == current_input:
            return _result.Success(None)
        return _result.Failure(f"Can not transition with input {str(current_input)}!")


