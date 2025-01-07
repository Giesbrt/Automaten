"""TBA"""

from __future__ import annotations
import returns.result as _result

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts

# Abstract Machine related imports
if _ty.TYPE_CHECKING:
    from core.modules.automaton.base.transition import Transition


# Docs generated with Chat-GPT

class State(_abc.ABC):
    """
    Represents a state within an automaton.

    A state is a fundamental component of a state machine, defining its behavior when
    transitioning to other states and optionally performing actions upon activation.

    Attributes:
        _transitions (_ty.Set[Transition]):
            A set of transitions associated with this state. These define how the
            automaton moves to other states based on input.

        _state_name (str):
            The name of the state. This is typically used for identification.

        _activation_callback (_ty.Callable or None):
            An optional callable function that is executed when the state is activated.
            This can be used to trigger specific actions or side effects during state
            transitions.

    Methods:
        __init__(name: str) -> None:
            Initializes the state with a name and an empty set of transitions.

        get_name() -> str:
            Retrieves the name of the state.

        get_transitions() -> _ty.Set[Transition]:
            Returns the set of transitions associated with this state.

        find_transition(current_input_char: str) -> _result.Result:
            Abstract method to find a transition based on the current input character.
            Must be implemented by subclasses.

        set_activation_callback(callback: _ty.Callable) -> None:
            Sets the activation callback function for this state.

        get_activation_callback() -> _ty.Callable or None:
            Retrieves the current activation callback function.

        activate() -> None:
            Executes the activation callback function, if it exists.
    """

    def __init__(self, name: str) -> None:
        """
        Initializes a state with a name and an empty set of _transitions.

        Args:
            name (str): The name of the state, typically used for identification.

        Attributes after initialization:
            - `_transitions`: An empty set of _transitions.
            - `state_name`: The provided name for the state.
            - `activation_callback`: Set to `None` initially.
        """
        self._transitions: _ty.Set[Transition] = set()
        self._state_name: str = name
        self._activation_callback: _ty.Callable or None = None

        self._is_active: bool = False  # If the State is currently in use

    def set_name(self, new_name: str) -> None:
        """
        Sets the new name for this state.

        Args:
            new_name (str): The new name for the state
        """
        self._state_name = new_name

    def get_name(self) -> str:
        """
        Retrieves the name of the state.

        Returns:
            str: The name of the state.
        """
        return self._state_name

    def get_transitions(self) -> _ty.Set["Transition"]:  # Use forward reference
        """
        Returns the set of _transitions associated with this state.

        Returns:
            _ty.Set[Transition]: A set of _transitions for this state.
        """
        return self._transitions

    def add_transition(self, new_transition: "Transition") -> None:
        self._transitions.add(new_transition)

    def remove_transition(self, old_transition: "Transition") -> None:
        self._transitions.remove(old_transition)

    @_abc.abstractmethod
    def find_transition(self, current_input_char: str) -> _result.Result:
        """
        Abstract method to find a transition based on the current input character.

        Args:
            current_input_char (str): The current input character for the state machine.

        Returns:
            _result.Result:
                - Success: If a valid transition is found.
                - Failure: If no valid transition exists.

        Raises:
            NotImplementedError: If the method is not implemented in the child class.
        """
        raise NotImplementedError("find_transition must be implemented in a subclass.")

    def set_activation_callback(self, callback: _ty.Callable) -> None:
        """
        Sets the activation callback function for this state.

        The callback function is executed whenever the state is activated. This is useful
        for triggering actions or side effects during the automaton's operation.

        Args:
            callback (_ty.Callable): A callable function to set as the activation callback.
        """
        self._activation_callback = callback

    def get_activation_callback(self) -> _ty.Callable or None:
        """
        Retrieves the current activation callback function.

        Returns:
            _ty.Callable or None: The activation callback function, or `None` if no callback
            is set.
        """
        return self._activation_callback

    def activate(self) -> None:
        """
        Executes the activation callback function, if it exists.

        This method is called when the state is activated as part of the automaton's
        execution. If no callback is set, the method does nothing.
        """
        if self._activation_callback:
            self._activation_callback()

        self._is_active = True

    def deactivate(self) -> None:
        self._is_active = False

    def is_active(self) -> bool:
        return self._is_active

