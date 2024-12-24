"""TBA"""

import returns.result as _result
import json

# Abstract Machine related imports
from core.modules.automaton.base.state import State
from core.modules.automaton.base.transition import Transition

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
        `simulate`, `serialise`, and `load` methods must be implemented in subclasses to define the specific
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
    """

    def __init__(self) -> None:
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
        self.end_states: _ty.Set[State] = set()

    def get_end_states(self) -> _ty.Set:
        """
        Returns the set of all end-states in the automaton.

        Returns:
            _ty.Set[State]: A set containing all end-states that are part of the automaton.
        """
        return self.end_states

    def set_end_states(self, new_end_states: _ty.Set) -> None:
        """
        Sets a new set of end states for the automaton.

        Args:
            new_end_states (State): The states to be set as the end states.
        """
        self.end_states = new_end_states

    def get_states(self) -> _ty.Set:
        """
        Returns the set of all states in the automaton.

        Returns:
            _ty.Set[State]: A set containing all states that are part of the automaton.
        """
        return self.states

    def get_transitions(self, scrape_transitions: bool = True) -> _ty.Set:
        if scrape_transitions:
            self.__scrape_all_transitions()
        return self.transitions

    def __scrape_all_transitions(self) -> None:
        transition_set: _ty.Set[Transition] = set()

        for state in self.get_states():
            for transition in state.get_transitions():
                transition_set.add(transition)
        self.set_transitions(transition_set)

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
    @DeprecationWarning
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
    def set_input(self, automaton_input: _ty.Any) -> None:
        raise NotImplementedError("set_input must be implemented in a subclass.")

    def get_input(self) -> _ty.Any:
        raise NotImplementedError("get_input must be implemented in a subclass.")

    @_abc.abstractmethod
    def set_input_alphabet(self, alphabet: _ty.Any) -> None:
        raise NotImplementedError("set_input_alphabet must be implemented in a subclass.")

    @_abc.abstractmethod
    def set_output_alphabet(self, alphabet: _ty.Any) -> None:
        raise NotImplementedError("set_output_alphabet must be implemented in a subclass.")

    @_abc.abstractmethod
    def get_input_alphabet(self) -> _ty.Any:
        raise NotImplementedError("get_input_alphabet must be implemented in a subclass.")

    @_abc.abstractmethod
    def get_output_alphabet(self) -> _ty.Any:
        raise NotImplementedError("get_output_alphabet must be implemented in a subclass.")

    def serialise_to_json(self) -> _ty.Dict[str, _ty.Any]:
        """
        Serialises the automaton into json format to send via the bridge
        """
        serialised: _ty.Dict[str, _ty.Any] = {}

        # serialise states
        serialised_states: _ty.List[_ty.Dict[str, _ty.Any]] = []
        for state in self.get_states():
            # special state
            flag_list: _ty.List[str] = []

            if state is self.start_state:
                # start_state
                flag_list.append("start_state")

            if state in self.get_end_states():
                # end_state
                flag_list.append("end_state")

            serialised_data: _ty.Dict[str, _ty.Any] = state.serialise_to_json(flag_list)
            serialised_states.append(serialised_data)

        # serialise transitions
        serialised_transitions: _ty.List[_ty.Dict[str, _ty.Any]] = []
        for transition in self.get_transitions():
            # special state
            flag_list: _ty.List[str] = []

            serialised_data: _ty.Dict[str, _ty.Any] = transition.serialise_to_json(flag_list)
            serialised_transitions.append(serialised_data)

        serialised["object"] = serialised_states + serialised_transitions
        return serialised
