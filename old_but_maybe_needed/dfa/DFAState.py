"""TBA"""
import json

from returns import result as _result

# Abstract Machine related imports
from automaton.base.state import State as BaseState
from automaton.base.transition import Transition as BaseTransition

# Standard typing imports for aps
import typing as _ty

from aplustools.io import ActLogger


# Docs generated with Chat-GPT

class DFAState(BaseState):
    """
    Represents a state in a Deterministic Finite Automaton (DFA).

    This class extends the base `State` class, adding functionality to handle
    transitions based on the DFA's deterministic nature.

    Attributes:
        Inherits all attributes from the `BaseState` class, including:
        - `state_name` (str): The name of the state.
        - `transitions` (_ty.Set[BaseTransition]): A set of transitions associated with the state.
        - `activation_callback` (_ty.Callable or None): An optional callback executed upon state activation.
    """

    def __init__(self, name: str) -> None:
        """
        Initializes a DFA state with a given name.

        Args:
            name (str): The name of the DFA state.
        """
        super().__init__(name)

    def find_transition(self, current_input_char: str) -> _result.Result:
        """
        Finds a transition based on the current input character.

        This method iterates through all transitions associated with the state and selects
        the one that is valid for the given input character. If multiple valid transitions
        exist, it uses the deterministic nature of the DFA to resolve to one.

        Args:
            current_input_char (str): The current input character for the DFA.

        Returns:
            _result.Result:
                - Success: Contains the target state of the valid transition.
                - Failure: If no valid transition exists for the given input character.
        """
        transition_functions: _ty.Set[BaseTransition] = self.get_transitions()

        for function in transition_functions:
            # Check if the transition is valid for the input character
            if not isinstance(function.canTransition(current_input_char), _result.Success):
                continue

            # Activate the transition (optional behavior)
            function.activate()

            # Return the target state of the valid transition
            return _result.Success(function.get_transition_target())

        # If no valid transition is found, return a failure result
        return _result.Failure(f"No transition found for state {self.get_name()}!")
