"""TBA"""

import returns.result as _result

# Abstract Machine related imports
from core.base.state import State
from core.base.transition import Transition

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts


# Docs generated with Chat-GPT

class Automaton(_abc.ABC):
    """
    Represents a generic automaton. This class serves as the foundation for different types of
    automata (such as DFAs, Mealy-automaton, Turing machines, etc.), and it manages the states and transitions
    that define the automaton's behavior.

    Note:
        This class is abstract and intended to be subclassed for specific types of automata. The
        `simulate`, `save`, and `load` methods must be implemented in subclasses to define the specific
        behavior of the automaton's simulation and persistence.

    Attributes:
        states (_ty.Set[State]):
            A set of all states in the automaton.

        transitions (_ty.Set[Transition]):
            A set of all transitions between states in the automaton.

        current_state (State):
            The current state of the automaton. This is the state the automaton is in during execution.

        start_state (State):
            The start state from which the automaton begins its execution.

    Methods:
        __init__() -> None:
            Initializes an automaton with no states, transitions, or current state.

        get_states() -> _ty.Set[State]:
            Returns the set of all states in the automaton.

        get_transitions() -> _ty.Set[Transition]:
            Returns the set of all transitions in the automaton.

        get_current_state() -> State:
            Returns the current state of the automaton.

        get_start_state() -> State:
            Returns the start state of the automaton.

        set_start_state(new_start_state: State) -> None:
            Sets a new start state for the automaton.

        set_states(new_states: _ty.Set[State]) -> None:
            Sets a new set of states for the automaton.

        set_transitions(new_transitions: _ty.Set[Transition]) -> None:
            Sets a new set of transitions for the automaton.

        simulate() -> _result.Result:
            Abstract method that must be implemented in subclasses to simulate the automaton's behavior
            based on its transitions and input. The simulation logic differs based on the type of automaton.

        simulate_one_step() -> _result.Result:
            Abstract method that must be implemented in subclasses to simulate one step of the automaton's behavior
            based on its transitions and input. The simulation logic differs based on the type of automaton.

        save(file_path: str) -> bool:
            Abstract method to save the automaton's configuration to a file. Must be implemented in subclasses.

        load(file_path: str) -> bool:
            Abstract method to load an automaton's configuration from a file. Must be implemented in subclasses.
    """

    def __init__(self) -> None:  # TODO input alphabet?
        """
        Initializes an automaton with no states, transitions, or current state.

        This constructor initializes an empty set of states and transitions, as well as setting the
        current and start states to `None`. These will need to be populated through methods like
        `set_states`, `set_transitions`, and `set_start_state` before the automaton can be executed.

        Attributes after initialization:
            states (set): An empty set of states.
            transitions (set): An empty set of transitions.
            current_state (None): The automaton's current state is not defined yet.
            start_state (None): The automaton's start state is not defined yet.
        """
        self.states: _ty.Set[State] = set()
        self.transitions: _ty.Set = set()

        self.current_state: State = None
        self.start_state: State = None

    def get_states(self) -> _ty.Set:
        """
        Returns the set of all states in the automaton.

        Returns:
            _ty.Set[State]: A set containing all states that are part of the automaton.
        """
        return self.states

    def get_transitions(self) -> _ty.Set:
        """
        Returns the set of all transitions in the automaton.

        Returns:
            _ty.Set[Transition]: A set containing all transitions between states in the automaton.
        """
        return self.transitions

    def get_current_state(self) -> State:
        """
        Returns the current state of the automaton.

        The current state reflects the automaton's position in its execution.

        Returns:
            State: The state the automaton is currently in.
        """
        return self.current_state

    def get_start_state(self) -> State:
        """
        Returns the start state of the automaton.

        The start state is where the automaton begins its execution.

        Returns:
            State: The state where the automaton begins execution.
        """
        return self.start_state

    def set_start_state(self, new_start_state: State) -> None:
        """
        Sets a new start state for the automaton.

        This method assigns a specific state as the starting point for the automaton's execution.
        This is typically called before the automaton starts processing any input.

        Args:
            new_start_state (State): The state to be set as the start state.
        """
        self.start_state = new_start_state

    def set_states(self, new_states: _ty.Set) -> None:
        """
        Sets a new set of states for the automaton.

        This method allows the user to define the complete set of states that the automaton can be in.
        It is typically called during the initial configuration of the automaton.

        Args:
            new_states (_ty.Set[State]): A set of all states to be used in the automaton.
        """
        self.states = new_states

    def set_transitions(self, new_transitions: _ty.Set) -> None:
        """
        Sets a new set of transitions for the automaton.

        This method defines all the state-to-state transitions the automaton can take. These transitions
        are used by the automaton to determine how it moves from one state to another during execution.

        Args:
            new_transitions (_ty.Set[Transition]): A set of all transitions that define how the automaton
            moves between states.
        """
        self.transitions = new_transitions

    @_abc.abstractmethod
    def simulate(self) -> _result.Result:
        """
        Abstract method that must be implemented in subclasses to simulate the automaton's behavior.

        The simulation behavior depends on the type of automaton. For example:
        - In a DFA, the simulation would process input and determine the next state based on the
          current state and input symbol.
        - In a Turing machine, the simulation would involve moving along the tape, reading and writing symbols.
        - In a Mealy machine, the simulation might produce outputs while transitioning between states.

        Returns:
            _result.Result: The _result of the simulation. This could indicate whether the automaton successfully
            accepted or rejected an input, or it could represent some other outcome specific to the type of automaton.

        Raises:
            NotImplementedError:
                If this method is not implemented in a subclass.
        """
        raise NotImplementedError("simulate must be implemented in a subclass.")

    @_abc.abstractmethod
    def simulate_one_step(self) -> _result.Result:
        """
        Abstract method that must be implemented in subclasses to simulate one step of the automaton's behavior.

        The simulation behavior depends on the type of automaton. For example:
        - In a DFA, the simulation would process input and determine the next state based on the
          current state and input symbol.
        - In a Turing machine, the simulation would involve moving along the tape, reading and writing symbols.
        - In a Mealy machine, the simulation might produce outputs while transitioning between states.

        Returns:
            _result.Result: The _result of the simulation. This could indicate whether the automaton successfully
            accepted or rejected an input, or it could represent some other outcome specific to the type of automaton.

        Raises:
            NotImplementedError:
                If this method is not implemented in a subclass.
        """
        raise NotImplementedError("simulate must be implemented in a subclass.")

    @_abc.abstractmethod
    def save(self, file_path: str) -> bool:
        """
        Abstract method to save the automaton's configuration to a file.

        This method should be implemented in subclasses to serialize the automaton's states, transitions,
        and other relevant attributes into a file format (e.g., JSON, XML, or a custom format).

        Args:
            file_path (str): The path of the file where the automaton's configuration will be saved.

        Returns:
            bool: True if the save operation is successful, False otherwise.

        Raises:
            NotImplementedError:
                If this method is not implemented in a subclass.
        """
        raise NotImplementedError("save must be implemented in a subclass.")

    @staticmethod
    def load(file_path: str) -> bool:
        """
        Abstract method to load an automaton's configuration from a file.

        This method should be implemented in subclasses to deserialize the automaton's configuration
        from a file format (e.g., JSON, XML, or a custom format).

        Args:
            file_path (str): The path of the file from which the automaton's configuration will be loaded.

        Returns:
            bool: True if the load operation is successful, False otherwise.

        Raises:
            NotImplementedError:
                If this method is not implemented in a subclass.
        """
        raise NotImplementedError("load must be implemented in a subclass.")
