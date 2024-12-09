"""TBA"""
from returns import result as _result

# Abstract Machine related imports
from core.base.state import State as BaseState
from core.base.transition import Transition as BaseTransition

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts


class DFAState(BaseState):

    def __init__(self, name: str) -> None:
        super().__init__(name)

    def find_transition(self, current_input_char: str) -> _result.Result:
        """
            Abstract method to find a transition based on the current input character.

            This method should be implemented in child classes to define the logic
            for selecting the appropriate transition.

            Args:
                current_input_char (str): The current input character for the state machine.

            Returns:
                Result: A `Result` instance representing the found transition or an error if no
                        valid transition exists.
        """
        transition_functions: _ty.Set[BaseTransition] = self.get_transitions()

        for function in transition_functions:
            if not isinstance(function.canTransition(current_input_char), _result.Success):
                continue
            function.activate()
            return _result.Success(function.get_transition_target())

        return _result.Failure(f"No transition found for state {self.get_name()}!")


