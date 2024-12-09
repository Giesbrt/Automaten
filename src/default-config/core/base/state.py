"""TBA"""

from __future__ import annotations
import returns.result as _result
import typing as _ty

if _ty.TYPE_CHECKING:
    from core.base.transition import Transition


class State:
    """
    Represents a state within an automaton. This class serves as a blueprint for defining the behavior
    of individual states in a state machine.
    """

    def __init__(self, name: str) -> None:
        self.transitions: _ty.Set[Transition] = set()
        self.state_name: str = name

        self.activation_callback: _ty.Callable or None = None

    def get_name(self) -> str:
        """
        Retrieves the name of the state.

        Returns:
            str: The name of the state.
        """
        return self.state_name

    def get_transitions(self) -> _ty.Set["Transition"]:  # Use forward reference
        """
        Returns the set of transitions associated with this state.

        Returns:
            _ty.Set[Transition]: A set of transitions for this state.
        """
        return self.transitions

    def find_transition(self, current_input_char: str) -> _result.Result:
        """
        Abstract method to find a transition based on the current input character.

        Args:
            current_input_char (str): The current input character for the state machine.

        Returns:
            Result: A `Result` instance representing the found transition or an error if no
                    valid transition exists.

        Raises:
            NotImplementedError: If the method is not implemented in the child class.
        """
        raise NotImplementedError("find_transition must be implemented in a subclass.")

    def set_activation_callback(self, callback: _ty.Callable) -> None:
        self.activation_callback = callback

    def get_activation_callback(self) -> _ty.Callable or None:
        return self.activation_callback

    def activate(self) -> None:
        if self.activation_callback:
            self.activation_callback()
