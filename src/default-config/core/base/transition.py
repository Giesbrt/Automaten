"""TBA"""

from __future__ import annotations
import returns.result as _result

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts


# Abstract Machine related imports
from core.base.state import State


# Docs generated with Chat-GPT

class Transition:
    """
    Represents a generic transition between states in an automaton. This class is designed to be
    flexible and abstract, allowing it to be adapted to different types of automata, such as
    deterministic finite automata (DFA), Turing machines, and Mealy machines.

    Note:
        Unlike more specific transition implementations, this class does not include a fixed
        `accepted_char` attribute or similar predefined condition. This omission ensures flexibility
        for automata that may rely on more complex or varied transition conditions (e.g., reading
        and writing symbols on a Turing machine tape, generating output in a Mealy machine, or
        handling epsilon transitions in NFAs).

    Attributes:
        start_state (State):
            The state from which the transition originates.

        transition_target_state (State):
            The state that the automaton moves to when this transition is triggered.

    Methods:
        __init__(start_state: State, transition_target_state: State) -> None:
            Initializes the transition with the start state and target state.

        canTransition(current_input: _ty.Any) -> _result.Result:
            Abstract method to determine if the transition can occur based on the current input.
            This method must be implemented in subclasses.

        get_transition_target() -> State:
            Returns the target state of this transition.

        get_start_state() -> State:
            Returns the starting state of this transition.
    """

    def __init__(self, start_state: State, transition_target_state: State) -> None:
        """
        Initializes the transition with the start state and target state.

        Args:
            start_state (State):
                The state from which the transition originates.

            transition_target_state (State):
                The state to transition to when this transition is triggered.
        """
        self.start_state: State = start_state
        self.transition_target_state: State = transition_target_state

        self.activation_callback: _ty.Callable or None = None

        # Adds this Transition automatically to the start state
        self.start_state.transitions.add(self)

    def canTransition(self, current_input: _ty.Any) -> _result.Result:
        """
        Abstract method to check if the transition can occur based on the current input.

        This method should be implemented in subclasses to define custom transition conditions,
        which might involve single characters (as in DFAs), tape symbols (as in Turing machines),
        or input-output pairs (as in Mealy machines).

        Args:
            current_input (_ty.Any):
                The input being processed (e.g., a character, tape symbol, etc.).

        Returns:
            _result.Result:
                Indicates whether the transition can occur.

        Raises:
            NotImplementedError:
                If the method is not implemented in a subclass.
        """
        raise NotImplementedError("canTransition must be implemented in a subclass.")

    def get_transition_target(self) -> State:
        """
        Returns the target state of this transition.

        Returns:
            State:
                The state that this transition leads to.
        """
        return self.transition_target_state

    def get_start_state(self) -> State:
        """
        Returns the starting state of this transition.

        Returns:
            State:
                The state where this transition originates from.
        """
        return self.start_state

    def set_activation_callback(self, callback: _ty.Callable) -> None:
        self.activation_callback = callback

    def get_activation_callback(self) -> _ty.Callable or None:
        return self.activation_callback

    def activate(self) -> None:
        if self.activation_callback:
            self.activation_callback()
