"""TBA"""

from __future__ import annotations
import returns.result as _result

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts


# Abstract Machine related imports
from core.modules.automaton.base.state import State
from core.modules.automaton.base._displayManager import DisplayManager


# Docs generated with Chat-GPT

class Transition(_abc.ABC, DisplayManager):
    """
    Represents a generic transition between states in an automaton. It is flexible to support
    various automata by allowing custom logic for transition conditions.

    Attributes:
        start_state (State): The state where the transition originates.
        transition_target_state (State): The state to which the transition leads.
        activation_callback (_ty.Callable or None): An optional callback triggered when the transition is activated.
    """

    def __init__(self, start_state: State, transition_target_state: State, display_name: str = "",
                 position: _ty.Tuple[float, float] = (0, 0),
                 colour: _ty.Tuple[int, int, int] = (0, 0, 0),
                 accent_colour: _ty.Tuple[int, int, int] = (255, 0, 0)) -> None:
        """
        Initializes a transition with a starting and a target state.

        Args:
            start_state (State): The state from which this transition starts.
            transition_target_state (State): The state this transition leads to.
        """
        super().__init__(display_name, position, colour, accent_colour)
        self.start_state: State = start_state
        self.transition_target_state: State = transition_target_state
        self.activation_callback: _ty.Callable or None = None

        # Automatically adds this transition to the start state's set of transitions.
        self.start_state.transitions.add(self)

    @_abc.abstractmethod
    def canTransition(self, current_input: _ty.Any) -> _result.Result:
        """
        Abstract method to determine if the transition is valid based on the input.

        This should be implemented in subclasses, as the logic for valid transitions depends
        on the type of automaton (e.g., character matching in DFAs, symbol checks in Turing machines).

        Args:
            current_input (_ty.Any): The input to evaluate for this transition.

        Returns:
            _result.Result:
                - Success: If the transition is valid.
                - Failure: If the transition is invalid.

        Raises:
            NotImplementedError: If the method is not overridden in a subclass.
        """
        raise NotImplementedError("canTransition must be implemented in a subclass.")

    def get_transition_target(self) -> State:
        """
        Retrieves the state this transition leads to.

        Returns:
            State: The target state of the transition.
        """
        return self.transition_target_state

    def get_start_state(self) -> State:
        """
        Retrieves the state where this transition originates.

        Returns:
            State: The starting state of the transition.
        """
        return self.start_state

    def set_activation_callback(self, callback: _ty.Callable) -> None:
        """
        Sets a callback function to be executed when the transition is activated.

        Args:
            callback (_ty.Callable): The function to call upon activation.
        """
        self.activation_callback = callback

    def get_activation_callback(self) -> _ty.Callable or None:
        """
        Retrieves the activation callback function, if any.

        Returns:
            _ty.Callable or None: The activation callback function.
        """
        return self.activation_callback

    def activate(self) -> None:
        """
        Triggers the activation callback, if one is set.
        """
        if self.activation_callback:
            self.activation_callback()

    def serialise_to_json(self, flags: _ty.List[str] = None) -> _ty.Dict[str, _ty.Any]:
        """
        Serialises the Transition into json format to send via the bridge
        """
        raise NotImplementedError("serialise_to_json must be implemented in a subclass.")

