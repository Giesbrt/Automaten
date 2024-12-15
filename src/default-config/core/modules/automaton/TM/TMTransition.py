from returns import result as _result

# Abstract Machine related imports
from core.modules.automaton.base.state import State as BaseState
from core.modules.automaton.base.transition import Transition as BaseTransition

# Standard typing imports for advanced functionality
import collections.abc as _a
import typing as _ty
import types as _ts

class TMTransition(BaseTransition):
    """
    Represents a transition between two states in a Turing Machine (TM).

    A transition is defined by a condition that specifies when the transition can occur,
    as well as the actions to be performed (writing a character and moving the head)
    if the transition is taken.

    Attributes:
        condition_char (str): 
            A string that defines the transition's condition in the format `input|write|move`.
            - `input`: The character that must match the input for the transition to occur.
            - `write`: The character to write on the tape.
            - `move`: The head movement direction ("L" for left, "R" for right, "H" for halt).
        start_state (BaseState): 
            The state where the transition originates.
        transition_target_state (BaseState): 
            The state where the transition leads.
    """

    def __init__(self, start_state: BaseState, transition_target_state: BaseState, condition_char: str) -> None:
        """
        Initializes a transition with the start state, target state, and condition details.

        Args:
            start_state (BaseState): The state where the transition originates.
            transition_target_state (BaseState): The state where the transition leads.
            condition_char (str): 
                A string in the format `input|write|move` specifying the input condition, 
                character to write, and head movement direction.
        """
        super().__init__(start_state, transition_target_state)
        self.condition_char: str = condition_char

    def canTransition(self, current_input: _ty.Any) -> _result.Result:
        """
        Determines if the transition is valid for the given input and returns the associated actions.

        This method splits the `condition_char` into its components (`input|write|move`) and checks
        if the `input` part matches the current input. If the transition is valid, it returns the 
        character to write and the head movement direction.

        Args:
            current_input (_ty.Any): The current input character to evaluate.

        Returns:
            _result.Result:
                - Success: If the transition is valid, returns a tuple `(to_write, head_move)` where:
                    - `to_write` (str): The character to write on the tape.
                    - `head_move` (str): The direction to move the head ("L", "R", or "H").
                - Failure: If the transition is invalid, returns an error message.
        """
        condition_parts = self.condition_char.split('|')
        if condition_parts[0] == current_input:
            to_write = condition_parts[1]  # Character to write
            head_move = condition_parts[2]  # Direction to move the head
            return _result.Success((to_write, head_move))  # Transition can occur
        
        return _result.Failure(f"Cannot transition with input {str(current_input)}!")  # Invalid transition