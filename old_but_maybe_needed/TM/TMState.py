from returns import result as _result
import sys
import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../base')))
# Abstract Machine related imports
from core.modules.automaton.base.state import State as BaseState
from core.modules.automaton.base.transition import Transition as BaseTransition

# Standard typing imports for advanced functionality
import collections.abc as _a
import typing as _ty
import types as _ts

# Comments generated with Chat-GPT

class TMState(BaseState):
    """
    Represents a state in a Turing Machine (TM).

    This class extends the base `State` class, providing additional functionality
    to handle transitions in the context of a Turing Machine. It supports determining
    valid transitions based on the current input character.

    Attributes:
        Inherits all attributes from the `BaseState` class, including:
        - `state_name` (str): The unique name of the state.
        - `transitions` (_ty.Set[BaseTransition]): A set of transitions associated with this state.
        - `activation_callback` (_ty.Optional[_ty.Callable]): An optional callback executed when the state is activated.
    """

    def __init__(self, name: str) -> None:
        """
        Initializes a state for the Turing Machine with a given name.

        Args:
            name (str): The name of the state.
        """
        super().__init__(name)

    def find_transition(self, current_input_char: str) -> _result.Result:
        """
        Identifies a valid transition based on the current input character.

        This method iterates through the transitions associated with the state,
        checks which transition can process the given input character, and resolves
        deterministically to one valid transition.

        Args:
            current_input_char (str): The character currently being processed by the Turing Machine.

        Returns:
            _result.Result:
                - Success: Contains the target state of a valid transition and any associated condition.
                - Failure: If no valid transition exists for the given input character.

        Behavior:
            - If a transition is valid for the input character, it is activated (optional behavior),
              and the target state is returned.
            - If no valid transitions are found, a failure result is returned.
        """
        transition_functions: _ty.Set[BaseTransition] = self.get_transitions()

        for function in transition_functions:
            # Check if the transition is valid for the current input character
            if not isinstance(function.canTransition(current_input_char), _result.Success):
                continue

            # Activate the transition (if applicable)
            function.activate()
            result_condition = function.canTransition(current_input_char)
            condition = result_condition.unwrap()

            # Return the target state and the condition
            return _result.Success((function.get_transition_target(), condition))

        # If no valid transitions exist, return a failure result
        return _result.Failure(f"No transition found for state {self.get_name()}!")