"""TBA"""
from returns import result as _result

# Abstract Machine related imports
from core.base.state import State as BaseState
from core.base.transition import Transition as BaseTransition

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts


# Docs generated with Chat-GPT

class DFATransition(BaseTransition):
    """
    Represents a transition between two states in a Deterministic Finite Automaton (DFA).

    A transition is valid if the current input character matches the transition's
    condition character. This class defines the `canTransition` method to check
    if the transition can occur based on the input.

    Attributes:
        condition_char (str): The character that must match the input for the transition to occur.
        start_state (BaseState): The state where the transition originates.
        transition_target_state (BaseState): The state where the transition leads.
    """

    def __init__(self, start_state: BaseState, transition_target_state: BaseState, condition_char: str) -> None:
        """
        Initializes a transition with the start state, target state, and the input character condition.

        Args:
            start_state (BaseState): The state where the transition originates.
            transition_target_state (BaseState): The state where the transition leads.
            condition_char (str): The input character that triggers this transition.
        """
        super().__init__(start_state, transition_target_state)
        self.condition_char: str = condition_char

    def canTransition(self, current_input: _ty.Any) -> _result.Result:
        """
        Checks whether the transition is valid for the given input character.

        This method compares the current input character with the condition character
        to determine if the transition can occur.

        Args:
            current_input (_ty.Any): The current input character to check.

        Returns:
            _result.Result:
                - Success: If the transition can occur (the input matches the condition).
                - Failure: If the transition cannot occur (the input does not match the condition).
        """
        if self.condition_char == current_input:
            return _result.Success(None)  # Transition can occur
        return _result.Failure(f"Can not transition with input {str(current_input)}!")  # Invalid transition