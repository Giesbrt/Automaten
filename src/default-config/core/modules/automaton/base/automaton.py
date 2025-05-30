import returns.result as _result
import json

# Abstract Machine related imports
from automaton.base.state import State
from automaton.base.transition import Transition

from utils.OrderedSet import OrderedSet

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts


# Docs generated with Chat-GPT

class Automaton(_abc.ABC):
    """
    Represents a generic automaton. This class serves as the foundation for different types of
    automata (such as DFAs, Mealy automaton, Turing machines, etc.), and it manages the states and transitions
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

        get_end_states() -> _ty.Set[State]:
            Returns the set of all end states in the automaton.

        set_end_states(new_end_states: _ty.Set) -> None:
            Sets a new set of end states for the automaton.

        get_states() -> _ty.Set[State]:
            Returns the set of all states in the automaton.

        get_transitions(scrape_transitions: bool = True) -> _ty.Set[Transition]:
            Returns the set of all transitions in the automaton. If `scrape_transitions` is True, transitions are
            scraped from the states.

        __scrape_all_transitions() -> None:
            Scrapes all transitions from the states and stores them in the automaton's transitions set.

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
            Abstract method that must be implemented in subclasses to simulate the automaton's behavior.

        simulate_one_step() -> _result.Result:
            Abstract method that must be implemented in subclasses to simulate one step of the automaton's behavior.

        set_input(automaton_input: _ty.Any) -> None:
            Abstract method to set the input for the automaton.

        get_input() -> _ty.Any:
            Abstract method to get the current input for the automaton.

        set_input_alphabet(alphabet: _ty.Any) -> None:
            Abstract method to set the input alphabet for the automaton.

        set_output_alphabet(alphabet: _ty.Any) -> None:
            Abstract method to set the output alphabet for the automaton.

        get_input_alphabet() -> _ty.Any:
            Abstract method to get the input alphabet for the automaton.

        get_output_alphabet() -> _ty.Any:
            Abstract method to get the output alphabet for the automaton.
    """

    def __init__(self) -> None:
        """
        Initializes an automaton with no states, transitions, or current state.

        This constructor initializes an empty set of states and transitions, and sets the current and start
        states to `None`. These will need to be populated through methods like `set_states`, `set_transitions`,
        and `set_start_state` before the automaton can be executed.
        """

        self.states: OrderedSet[State] = OrderedSet()
        self.transitions: OrderedSet[Transition] = OrderedSet()

        self.current_state: State | None = None
        self.start_state: State | None = None
        self.end_states: _ty.Set[State] = set()

    def get_states(self) -> OrderedSet[State]:
        """
        Returns the set of all states in the automaton.

        Returns:
            _ty.Set[State]: A set containing all states that are part of the automaton.
        """
        return self.states

    def get_transitions(self, scrape_transitions: bool = True) -> OrderedSet[Transition]:
        """
        Returns the set of all transitions in the automaton. If `scrape_transitions` is set to True, it will
        scrape transitions from the states.

        Args:
            scrape_transitions (bool): If True, transitions will be scraped from the states.

        Returns:
            _ty.Set[Transition]: A set containing all transitions in the automaton.
        """
        if scrape_transitions:
            self.__scrape_all_transitions()
        return self.transitions

    def __scrape_all_transitions(self) -> None:
        """
        Scrapes all transitions from the states and stores them in the automaton's transitions set.
        """
        transition_set: OrderedSet[Transition] = OrderedSet()

        for state in self.get_states():
            for transition in state.get_transitions():
                transition_set.add(transition)
        self.set_transitions(transition_set)

    def get_current_state(self) -> State:
        """
        Returns the current state of the automaton.

        Returns:
            State: The state the automaton is currently in.
        """
        return self.current_state

    def get_start_state(self) -> State:
        """
        Returns the start state of the automaton.

        Returns:
            State: The state where the automaton begins execution.
        """
        return self.start_state

    def set_start_state(self, new_start_state: State) -> None:
        """
        Sets a new start state for the automaton.

        Args:
            new_start_state (State): The state to be set as the start state.
        """
        self.start_state = new_start_state

    def set_states(self, new_states: OrderedSet[State]) -> None:
        """
        Sets a new set of states for the automaton.

        Args:
            new_states (_ty.Set[State]): A set of all states to be used in the automaton.
        """
        self.states = new_states

    @_abc.abstractmethod
    def add_state(self, state: State, state_type: str) -> None:
        """
        Abstract method to add a new state to the automaton.

        This Method should add a new state to the automaton, according to the state type.
        E.g. you add a new state to the automaton with the type "end". This state should be added to the end states.
        
        Args:
            state (State): The new state to be added.
            state_type (str): The type of the state being added.
        """
        raise NotImplementedError("add_state must be implemented in a subclass.")

    def get_state_by_id(self, state_id: int) -> State:
        """
        Returns the state with the given ID.
        
        Args:
            state_id (int): The ID of the state to retrieve.
            
        Returns:
            State: The state with the given ID.
        """
        for i, state in enumerate(iter(self.states)):
            if i != state_id:
                continue

            return state

    def get_transition_by_id(self, transition_id: int) -> Transition:
        """
        Returns the transition with the given ID.
        
        Args:
            transition_id (int): The ID of the transition to retrieve.
        
        Returns:
            Transition: The transition with the given ID.
        """
        for i, transition in enumerate(iter(self.transitions)):
            if i != transition_id:
                continue

            return transition

    def set_transitions(self, new_transitions: OrderedSet[Transition]) -> None:
        """
        Sets a new set of transitions for the automaton.

        Args:
            new_transitions (_ty.Set[Transition]): A set of all transitions that define how the automaton
            moves between states.
        """
        self.transitions = new_transitions

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
            _result.Result: The result of the simulation for the step.

        Raises:
            NotImplementedError:
                If this method is not implemented in a subclass.
        """
        raise NotImplementedError("simulate_one_step must be implemented in a subclass.")

    @_abc.abstractmethod
    def set_input(self, automaton_input: _ty.Any) -> None:
        """
        Abstract method to set the input for the automaton.

        Args:
            automaton_input (_ty.Any): The input to be set for the automaton.
        """
        raise NotImplementedError("set_input must be implemented in a subclass.")

    def get_input(self) -> _ty.Any:
        """
        Abstract method to get the current input for the automaton.

        Returns:
            _ty.Any: The current input for the automaton.
        """
        raise NotImplementedError("get_input must be implemented in a subclass.")

    def get_state_index(self, state: State) -> int:
        """
        Returns the index of the state in the automaton.
        
        Args:
            state (State): The state to find the index of.
            
        Returns:
            int: The index of the state in the automaton.
        """
        for i, s in enumerate(self.get_states()):
            if s is not state:
                continue
            return i
        return 0

    def get_transition_index(self, transition: Transition) -> int:
        """
        Returns the index of the transition in the automaton.
        
        Args:
            transition (Transition): The transition to find the index of.
            
        Returns:
            int: The index of the transition in the automaton.
        """
        for i, t in enumerate(self.get_transitions()):
            if t is not transition:
                continue
            return i
        return 0

    @_abc.abstractmethod
    def get_current_index(self) -> int:
        """
        Returns the current index where the pointer (on the input sequence) is located

        Returns:
            int: current index of the pointer
        """
        raise NotImplementedError("get_current_index must be implemented in a subclass.")

    @_abc.abstractmethod
    def get_current_return_value(self) -> _ty.Any:
        """
        Returns the last return value of the automaton after one step of simulation

        Returns:
            _ty.Any: The return value
        """
        raise NotImplementedError("get_current_return_value must be implemented in a subclass.")

    def delete_state(self, state: "State") -> None:
        """
        Deletes a state from the automaton.
        
        Args:
            state (State): The state to delete.
        """
        if state not in self.states:
            return
        self.states.remove(state)

        _transition_copy: OrderedSet[Transition] = self.get_transitions()
        for transition in _transition_copy:
            if not transition.get_start_state() == state and not transition.get_transition_target() == state:
                continue
            self.transitions.remove(transition)
            del transition

        self.get_transitions(True)  # Update the Transitions set

    def delete_transition(self, transition: "Transition") -> None:
        """
        Deletes a transition from the automaton.
        
        Args:
            transition (Transition): The transition to delete.
        """
        if transition not in self.get_transitions():
            return

        transition_start_state: State = transition.get_start_state()
        transition_start_state.remove_transition(transition)

        self.transitions.remove(transition)
        del transition

        self.get_transitions(True)  # Update the Transitions set
