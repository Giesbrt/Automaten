from returns import result as _result
import sys
import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../base')))
# Abstract Machine related imports
from automaton.base.state import State as BaseState
from automaton.base.transition import Transition as BaseTransition
from automaton.base.automaton import Automaton as BaseAutomaton
# Standard typing imports for advanced functionality
import collections.abc as _a
import typing as _ty
import types as _ts
from automaton.base.settings import Settings as BaseSettings


# Comments generated with Chat-GPT

class MealySettings(BaseSettings):

    def __init__(self):
        super().__init__("mealy", "mealy automaton", "Fa4953",
                         [[], []], [True, True], [0, 1],
                         {'Default': "Ellipse: ((180.0, 180.0), 180.0, 180.0), 6#000000##00000000;",
                                                    'Start': "Ellipse: ((180.0, 180.0), 180.0, 180.0), 6#000000##00000000;Polygon: ((80.0, 160.0), (230.0, 160.0), (230.0, 130.0), (280.0, 180.0), (230.0, 230.0), (230.0, 200.0), (80.0, 200.0)), 0#ff0000##ff0000;"})


class MealyState(BaseState):
    """
    Represents a state in a Mealy Machine.

    This class extends the base `State` class, providing additional functionality
    to handle transitions in the context of a Mealy Machine. It supports determining
    valid transitions based on the current input symbol.

    Attributes:
        Inherits all attributes from the `BaseState` class, including:
        - `state_name` (str): The unique name of the state.
        - `transitions` (_ty.Set[BaseTransition]): A set of transitions associated with this state.
        - `activation_callback` (_ty.Optional[_ty.Callable]): An optional callback executed when the state is activated.
    """

    def __init__(self, name: str) -> None:
        """
        Initializes a state for the Mealy Machine with a given name.

        Args:
            name (str): The name of the state.
        """
        super().__init__(name)

    def find_transition(self, current_input: any) -> _result.Result:
        """
        Identifies a valid transition based on the current input symbol.

        This method iterates through the transitions associated with the state,
        checks which transition can process the given input symbol, and resolves
        deterministically to one valid transition.

        Args:
            current_input (any): The symbol currently being processed by the Mealy Machine.

        Returns:
            _result.Result:
                - Success: Contains the target state of a valid transition and any associated output.
                - Failure: If no valid transition exists for the given input symbol.

        Behavior:
            - If a transition is valid for the input symbol, it is activated (optional behavior),
              and the target state along with the output is returned.
            - If no valid transitions are found, a failure result is returned.
        """
        transition_functions: _ty.Set[BaseTransition] = self.get_transitions()

        for function in transition_functions:
            # Check if the transition is valid for the current input symbol
            if not isinstance(function.canTransition(current_input), _result.Success):
                continue

            # Activate the transition (if applicable)
            function.activate()
            result_output = function.canTransition(current_input)
            output = result_output.unwrap()

            # Return the target state and the output
            return _result.Success((function.get_transition_target(), output))

        # If no valid transitions exist, return a failure result
        return _result.Failure(f"No transition found for state {self.get_name()}!")


class MealyTransition(BaseTransition):
    """
    Represents a transition between two states in a Mealy Machine.

    A transition is defined by a condition that specifies when the transition can occur,
    as well as the output to be produced if the transition is taken.

    Attributes:
        condition_input (any):
            The input symbol or condition required for the transition to occur.
        start_state (BaseState):
            The state where the transition originates.
        transition_target_state (BaseState):
            The state where the transition leads.
        output (any):
            The output associated with the transition when it is taken.
    """

    def __init__(self, start_state: BaseState, transition_target_state: BaseState, condition: any) -> None:
        """
        Initializes a transition with the start state, target state, and condition details.

        Args:
            start_state (BaseState): The state where the transition originates.
            transition_target_state (BaseState): The state where the transition leads.
            condition (any): The condition required for the transition to occur.
            output (any): The output produced when the transition is taken.
        """
        super().__init__(start_state, transition_target_state, condition)
        self.condition_input: any = condition[0]
        self.output: any = condition[1]

    def get_condition(self):
        """
        Retrieves the condition associated with the transition.

        Returns:
            any: The condition required for the transition to occur.
        """
        return self.condition_input

    def canTransition(self, current_input: _ty.Any) -> _result.Result:
        """
        Determines if the transition is valid for the given input and returns the associated output.

        This method checks if the transition condition matches the current input. If the transition
        is valid, it returns the associated output.

        Args:
            current_input (_ty.Any): The current input symbol to evaluate.

        Returns:
            _result.Result:
                - Success: If the transition is valid, returns the output associated with the transition.
                - Failure: If the transition is invalid, returns an error message.
        """

        if self.condition_input == current_input or self.condition_input == "_":
            output = self.output  # Output
            return _result.Success(output)  # Transition can occur

        return _result.Failure(f"Cannot transition with input {str(current_input)}!")  # Invalid transition


#from aplustools.io import ActLogger
class MealyAutomaton(BaseAutomaton):
    """
    Represents a Mealy Automaton.

    A Mealy automaton is a finite-state machine where the output is determined by the current state
    and the current input. It consists of states, transitions, an input alphabet, and an output alphabet.

    Attributes:
        input (list):
            The input sequence to be processed by the automaton.

        input_index (int):
            Tracks the current position in the input sequence.

        current_input (any):
            The current input element being processed.

        input_alphabet (list):
            The set of allowable inputs for the automaton.

        output_alphabet (list):
            The set of possible outputs for the automaton.

        output (any):
            The current output generated by the automaton.

    Methods:
        __init__():
            Initializes the Mealy automaton with empty states, transitions, and alphabets.

        set_input(input: list) -> None:
            Sets a new input sequence for the automaton to process.

        get_input() -> any:
            Retrieves the current input sequence.

        set_input_alphabet(alphabet: list) -> None:
            Sets the input alphabet for the automaton.

        get_input_alphabet() -> list:
            Retrieves the input alphabet for the automaton.

        set_output_alphabet(alphabet: list) -> None:
            Sets the output alphabet for the automaton.

        get_output_alphabet() -> list:
            Retrieves the output alphabet for the automaton.

        next_input() -> None:
            Advances the automaton to the next input in the sequence.

        next_state() -> _result.Result:
            Transitions the automaton to the next state based on the current state and input.

        simulate() -> _result.Result:
            Runs the automaton simulation on the input sequence.

        simulate_one_step() -> _result.Result:
            Executes a single step of the automaton simulation.
    """

    def __init__(self) -> None:
        """
        Initializes a Mealy automaton instance.

        This constructor sets up:
        - An empty input sequence.
        - Input and output alphabets as empty lists.
        - The input index set to the beginning of the sequence.
        - The output initialized to None.
        """
        super().__init__()
        self.input_alphabet: list = []
        self.output_alphabet: list = []
        self.input: list = []
        self.input_index: int = 0
        self.output: any = None
        self.current_input = None

    def set_input(self, input: list) -> None:
        """
        Sets a new input sequence for the automaton to process.

        Args:
            input (list): The sequence of inputs to be processed by the automaton.
        """
        self.input = input
        self.input_index = 0
        if not self.input:
            self.current_input = None
        else:
            self.current_input = self.input[self.input_index]

    def get_input(self) -> _ty.Any:
        """
        Retrieves the current input sequence.

        Returns:
            any: The input sequence currently set for the automaton.
        """
        return self.input

    def get_output(self) -> _ty.Any:
        return self.output

    def set_input_alphabet(self, alphabet: _ty.Any) -> None:
        """
        Sets the input alphabet for the automaton.

        Args:
            alphabet (list): The allowable set of input symbols.
        """
        self.input_alphabet = alphabet

    def set_output_alphabet(self, alphabet: _ty.Any) -> None:
        """
        Sets the output alphabet for the automaton.

        Args:
            alphabet (list): The allowable set of output symbols.
        """
        self.output_alphabet = alphabet

    def get_input_alphabet(self) -> _ty.Any:
        """
        Retrieves the input alphabet for the automaton.

        Returns:
            list: The set of input symbols for the automaton.
        """
        return self.input_alphabet

    def get_output_alphabet(self) -> _ty.Any:
        """
        Retrieves the output alphabet for the automaton.

        Returns:
            list: The set of output symbols for the automaton.
        """
        return self.output_alphabet

    def next_input(self) -> None:
        """
        Advances the automaton to the next input in the sequence.

        Updates the current input element and ensures the input index remains within bounds.
        """
        self.input_index += 1
        if self.input_index < len(self.input):
            self.current_input = self.input[self.input_index]
        else:
            self.current_input = None  # End of input sequence.

    def next_state(self) -> _result.Result:
        """
        Transitions the automaton to the next state based on the current state and input.

        Uses the `find_transition` method of the current state to determine the appropriate transition.
        If no valid transition is found or the target state is invalid, the automaton halts.

        Returns:
            _result.Result: The output generated during the transition or a failure message.
        """
        transition_result: _result.Result = self.current_state.find_transition(self.current_input)

        if not isinstance(transition_result, _result.Success):
            return _result.Failure("No valid transition found!")

        state, output = transition_result.value_or((None, None))

        transition: MealyState = state
        if not transition or transition not in self.states:
            return _result.Failure("Invalid target state!")

        self.current_state = transition
        return output

    def simulate(self) -> _result.Result:
        """
        Runs the automaton simulation on the input sequence.

        The simulation starts at the initial state and processes each input element, transitioning
        between states based on the automaton's transition rules. The output is generated during
        each transition.

        Returns:
            _result.Result:
                - Success: If the simulation completes without errors.
                - Failure: If an error occurs during the simulation.

        Notes:
            If no start state is set or the start state is not part of the automaton's states,
            an error is logged, and the simulation returns a failure.
        """
        if not self.start_state:
            #ActLogger().error("Tried to start simulation of Mealy Automaton without a start state!")
            return _result.Failure("No start state found")

        if self.start_state not in self.states:
            #ActLogger().error("Tried to start simulation of Mealy Automaton without start state in automaton states!")
            return _result.Failure("Start state not in automaton states")

        self.current_state = self.start_state
        self.current_state.activate()

        while self.input_index < len(self.input):
            output = self.next_state()
            if isinstance(output, _result.Failure):
                return output
            self.output = output
            print(self.output)
            self.next_input()
            self.current_state.activate()

        return _result.Success("Simulation finished successfully :)")

    def simulate_one_step(self) -> _result.Result:
        """
        Executes a single step of the automaton simulation.

        Transitions the automaton to the next state based on the current input and state. The output
        is generated during the transition.

        Returns:
            _result.Result:
                - Success: If the step completes without errors.
                - Failure: If an error occurs during the step.

        Notes:
            If no start state is set or the start state is not part of the automaton's states,
            an error is logged, and the simulation step returns a failure.
        """
        if self.input_index >= len(self.input):
            return _result.Success("End of input sequence reached :)")

        if not self.start_state:
            #ActLogger().error("Tried to start simulation of Mealy Automaton without a start state!")
            return _result.Failure("No start state found")

        if self.start_state not in self.states:
            #ActLogger().error("Tried to start simulation of Mealy Automaton without start state in automaton states!")
            return _result.Failure("Start state not in automaton states")

        for state in self.states:
            state.deactivate()

        for transition in self.transitions:
            transition.deactivate()

        if self.current_state is None:
            self.current_state = self.start_state
            self.current_state.activate()

        output = self.next_state()
        if isinstance(output, _result.Failure):
            return output

        self.output = output
        self.next_input()
        self.current_state.activate()

    def add_state(self, state: MealyState, state_type: str) -> None:
        self.states.add(state)
        match state_type.lower():
            case "end":
                self.end_states.add(state)
            case "default":
                pass

    def get_current_index(self) -> int:
        return self.input_index

    def get_current_return_value(self) -> _ty.Any:
        return self.output
