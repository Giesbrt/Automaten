"""TBA"""

import returns.result as _result

# Abstract Machine related imports
from core.modules.automaton.base.state import State
from core.modules.automaton.base.transition import Transition
from core.modules.automaton.base.automaton import Automaton

from core.utils.OrderedSet import OrderedSet

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts

# Docs generated with Github Copilot / ChatGPT

class AutomatonBridge:
    def __init__(self, automaton_impl: Automaton) -> None:
        self.automaton_impl: Automaton = automaton_impl

    def set_implementation(self, automaton_impl: Automaton) -> None:
        """
        Sets the implementation of the automaton.
        
        Args:
            automaton_impl (Automaton): The implementation of the automaton.
        """
        self.automaton_impl = automaton_impl

    def get_implementation(self) -> Automaton:
        """
        Returns the implementation of the automaton.
        
        Returns:
            Automaton: The implementation of the automaton.
        """
        return self.automaton_impl

    def get_implementation_name(self) -> str:
        """
        Returns the name of the class that implements the automaton.
        
        Returns:
            str: The name of the class that implements the automaton.
        """
        class_type: type = type(self.automaton_impl)
        class_name: str = class_type.__name__
        return class_name

    def get_states(self) -> OrderedSet:
        """
        Returns the set of all states in the automaton.

        Returns:
            _ty.Set[State]: A set containing all states that are part of the automaton.
        """
        return self.automaton_impl.get_states()

    def get_transitions(self, scrape_transition: bool = True) -> OrderedSet:
        """
        Returns the set of all transitions in the automaton.

        Returns:
            _ty.Set[Transition]: A set containing all transitions between states in the automaton.
        """
        return self.automaton_impl.get_transitions(scrape_transition)

    def get_current_state(self) -> State:
        """
        Returns the current state of the automaton.

        The current state reflects the automaton's position in its execution.

        Returns:
            State: The state the automaton is currently in.
        """
        return self.automaton_impl.get_current_state()

    def get_start_state(self) -> State:
        """
        Returns the start state of the automaton.

        The start state is where the automaton begins its execution.

        Returns:
            State: The state where the automaton begins execution.
        """
        return self.automaton_impl.get_start_state()

    def set_start_state(self, new_start_state: State) -> None:
        """
        Sets a new start state for the automaton.

        This method assigns a specific state as the starting point for the automaton's execution.
        This is typically called before the automaton starts processing any input.

        Args:
            new_start_state (State): The state to be set as the start state.
        """
        self.automaton_impl.set_start_state(new_start_state)

    def set_states(self, new_states: OrderedSet) -> None:
        """
        Sets a new set of states for the automaton.

        This method allows the user to define the complete set of states that the automaton can be in.
        It is typically called during the initial configuration of the automaton.

        Args:
            new_states (_ty.Set[State]): A set of all states to be used in the automaton.
        """
        self.automaton_impl.set_states(new_states)

    def set_transitions(self, new_transitions: OrderedSet) -> None:
        """
        Sets a new set of transitions for the automaton.

        This method defines all the state-to-state transitions the automaton can take. These transitions
        are used by the automaton to determine how it moves from one state to another during execution.

        Args:
            new_transitions (_ty.Set[Transition]): A set of all transitions that define how the automaton
            moves between states.
        """
        self.automaton_impl.set_transitions(new_transitions)

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
        """
        return self.automaton_impl.simulate()

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
        """
        return self.automaton_impl.simulate_one_step()

    def set_input(self, automaton_input: _ty.Any) -> None:
        """
        Sets the input for the automaton.
        
        Args:
            automaton_input (Any): The input to be processed by the automaton.
        """
        self.automaton_impl.set_input(automaton_input)

    def get_input(self) -> _ty.Any:
        """
        Returns the input currently set for the automaton.
        
        Returns:
            Any: The input currently set for the automaton.
        """
        return self.automaton_impl.get_input()

    def get_state_index(self, state: State) -> int:
        """
        Returns the index of a state in the automaton.
        
        Args:
            state (State): The state for which the index is requested.
        
        Returns:
            int: The index of the state in the automaton.
        """
        return self.automaton_impl.get_state_index(state)

    def get_transition_index(self, transition: Transition) -> int:
        """
        Returns the index of a transition in the automaton.
        
        Args:
            transition (Transition): The transition for which the index is requested.
            
        Returns:
            int: The index of the transition in the automaton.
        """
        return self.automaton_impl.get_transition_index(transition)

    def get_current_index(self) -> int:
        """
        Returns the index of the current state in the automaton.

        This method provides the index of the state that the automaton is currently in.

        Returns:
            int: The index of the current state in the automaton.
        """
        return self.automaton_impl.get_current_index()

    def get_current_return_value(self) -> _ty.Any:
        """
        Returns the return value of the automaton.
        """
        return self.automaton_impl.get_current_return_value()

    def delete_state(self, state: "State") -> None:
        """
        Delete a state from the automaton.
        
        Args:
            state (State): The state to be deleted.
        """
        self.automaton_impl.delete_state(state)

    def delete_transition(self, transition: "Transition") -> None:
        """
        Delete a transition from the automaton.
        
        Args:
            transition (Transition): The transition to be deleted.
        """
        self.automaton_impl.delete_transition(transition)

    def add_state(self, state: State, state_type: str) -> None:
        """
        Add a state to the automaton.
        
        Args:
            state (State): The state to be added.
            state_type (str): The type of the state.
        """
        self.automaton_impl.add_state(state, state_type)

    def get_state_by_id(self, state_id: int) -> State:
        """
        Get a state by its ID.
        
        Args:
            state_id (int): The ID of the state.
            
        Returns:
            State: The state with the given ID.
        """
        return self.automaton_impl.get_state_by_id(state_id)

    def get_transition_by_id(self, transition_id: int) -> Transition:
        """
        Get a transition by its ID.
        
        Args:
            transition_id (int): The ID of the transition.
        
        Returns:
            Transition: The transition with the given ID.
        """
        return self.automaton_impl.get_transition_by_id(transition_id)
