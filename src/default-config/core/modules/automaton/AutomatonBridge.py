"""TBA"""

import returns.result as _result

# Abstract Machine related imports
from core.modules.automaton.base.state import State
from core.modules.automaton.base.transition import Transition
from core.modules.automaton.base.automaton import Automaton

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts


#  TODO: File is WIP

class AutomatonBridge:
    def __init__(self, automaton_impl: Automaton) -> None:
        self.automaton_impl: Automaton = automaton_impl

    def set_implementation(self, automaton_impl: Automaton) -> None:
        self.automaton_impl = automaton_impl

    def get_states(self) -> _ty.Set:
        """
        Returns the set of all states in the automaton.

        Returns:
            _ty.Set[State]: A set containing all states that are part of the automaton.
        """
        return self.automaton_impl.get_states()

    def get_transitions(self) -> _ty.Set:
        """
        Returns the set of all transitions in the automaton.

        Returns:
            _ty.Set[Transition]: A set containing all transitions between states in the automaton.
        """
        return self.automaton_impl.get_transitions()

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

    def set_states(self, new_states: _ty.Set) -> None:
        """
        Sets a new set of states for the automaton.

        This method allows the user to define the complete set of states that the automaton can be in.
        It is typically called during the initial configuration of the automaton.

        Args:
            new_states (_ty.Set[State]): A set of all states to be used in the automaton.
        """
        self.automaton_impl.set_states(new_states)

    def set_transitions(self, new_transitions: _ty.Set) -> None:
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
        self.automaton_impl.set_input(automaton_input)

    def get_input(self) -> _ty.Any:
        return self.automaton_impl.get_input()

    def set_input_alphabet(self, alphabet: _ty.Any) -> None:
        self.automaton_impl.set_input_alphabet(alphabet)

    def set_output_alphabet(self, alphabet: _ty.Any) -> None:
        self.automaton_impl.set_output_alphabet(alphabet)

    def get_input_alphabet(self) -> _ty.Any:
        return self.automaton_impl.get_input_alphabet()

    def get_output_alphabet(self) -> _ty.Any:
        return self.automaton_impl.get_output_alphabet()
