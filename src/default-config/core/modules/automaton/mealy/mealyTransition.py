from returns import result as _result
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../base')))
# Abstract Machine related imports
from state import State as BaseState
from transition import Transition as BaseTransition

# Standard typing imports for advanced functionality
import collections.abc as _a
import typing as _ty
import types as _ts

# Comments generated with Chat-GPT

class MealyTransition(BaseTransition):
    """
    Represents a transition between two states in a Mealy Machine.

    A transition is defined by a condition that specifies when the transition can occur,
    as well as the output to be produced if the transition is taken.

    Attributes:
        condition_input (any):
            The input symbol or condition required for the transition to occur.
        start_state (BaseState):
            The state where the transition originates.
        transition_target_state (BaseState):
            The state where the transition leads.
        output (any):
            The output associated with the transition when it is taken.
    """

    def __init__(self, start_state: BaseState, transition_target_state: BaseState, condition: any, output: any) -> None:
        """
        Initializes a transition with the start state, target state, and condition details.

        Args:
            start_state (BaseState): The state where the transition originates.
            transition_target_state (BaseState): The state where the transition leads.
            condition (any): The condition required for the transition to occur.
            output (any): The output produced when the transition is taken.
        """
        super().__init__(start_state, transition_target_state)
        self.condition_input: any = condition
        self.output: any = output

    def get_condition(self):
        """
        Retrieves the condition associated with the transition.

        Returns:
            any: The condition required for the transition to occur.
        """
        return self.condition_input

    def canTransition(self, current_input: _ty.Any) -> _result.Result:
        """
        Determines if the transition is valid for the given input and returns the associated output.

        This method checks if the transition condition matches the current input. If the transition
        is valid, it returns the associated output.

        Args:
            current_input (_ty.Any): The current input symbol to evaluate.

        Returns:
            _result.Result:
                - Success: If the transition is valid, returns the output associated with the transition.
                - Failure: If the transition is invalid, returns an error message.
        """

        if self.condition_input == current_input or self.condition_input == "_":
            output = self.output  # Output
            return _result.Success(output)  # Transition can occur
        
        return _result.Failure(f"Cannot transition with input {str(current_input)}!")  # Invalid transition