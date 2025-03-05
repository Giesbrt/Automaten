from returns import result as _result
#from aplustools.io import ActLogger
import sys
import os


# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts
#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# Abstract Machine related imports
from automaton.base.automaton import Automaton as BaseAutomaton
from automaton.base.state import State as BaseState
from automaton.base.transition import Transition as BaseTransition
from automaton.base.settings import Settings as BaseSettings
# Comments generated with Chat-GPT

class TmSettings(BaseSettings):

    def __init__(self):
        super().__init__("tm", "turing machine", "Fa4953",
                         [[], ['L', 'R', 'H']], [True, False], [0, 0, 1],
                         {'Default': "Ellipse: ((180.0, 180.0), 180.0, 180.0), 6#000000##00000000;",
                          'Start': "Ellipse: ((180.0, 180.0), 180.0, 180.0), 6#000000##00000000;Polygon: ((80.0, 160.0), (230.0, 160.0), (230.0, 130.0), (280.0, 180.0), (230.0, 230.0), (230.0, 200.0), (80.0, 200.0)), 0#ff0000##ff0000;",
                          'End': "Ellipse: ((180.0, 180.0), 180.0, 180.0), 6#000000##00000000;Ellipse: ((180.0, 180.0), 153.0, 153.0), 2#000000##00000000;"})


class TMState(BaseState):
    """
    Represents a state in a Turing Machine (TM).

    This class extends the base `State` class, providing additional functionality
    to handle transitions in the context of a Turing Machine. It supports determining
    valid transitions based on the current input character.

    Attributes:
        Inherits all attributes from the `BaseState` class, including:
        - `state_name` (str): The unique name of the state.
        - `transitions` (_ty.Set[BaseTransition]): A set of transitions associated with this state.
        - `activation_callback` (_ty.Optional[_ty.Callable]): An optional callback executed when the state is activated.
    """

    def __init__(self, name: str) -> None:
        """
        Initializes a state for the Turing Machine with a given name.

        Args:
            name (str): The name of the state.
        """
        super().__init__(name)

    def find_transition(self, current_input_char: str) -> _result.Result:
        """
        Identifies a valid transition based on the current input character.

        This method iterates through the transitions associated with the state,
        checks which transition can process the given input character, and resolves
        deterministically to one valid transition.

        Args:
            current_input_char (str): The character currently being processed by the Turing Machine.

        Returns:
            _result.Result:
                - Success: Contains the target state of a valid transition and any associated condition.
                - Failure: If no valid transition exists for the given input character.

        Behavior:
            - If a transition is valid for the input character, it is activated (optional behavior),
              and the target state is returned.
            - If no valid transitions are found, a failure result is returned.
        """
        transition_functions: _ty.Set[BaseTransition] = self.get_transitions()

        for function in transition_functions:
            # Check if the transition is valid for the current input character
            if not isinstance(function.canTransition(current_input_char), _result.Success):
                continue

            # Activate the transition (if applicable)
            function.activate()
            result_condition = function.canTransition(current_input_char)
            condition = result_condition.unwrap()

            # Return the target state and the condition
            return _result.Success((function.get_transition_target(), condition))

        # If no valid transitions exist, return a failure result
        return _result.Failure(f"No transition found for state {self.get_name()}!")

class TMTransition(BaseTransition):
    """
    Represents a transition between two states in a Turing Machine (TM).

    A transition is defined by a condition that specifies when the transition can occur,
    as well as the actions to be performed (writing a character and moving the head)
    if the transition is taken.

    Attributes:
        condition_char (str): 
            A string that defines the transition's condition in the format `input|write|move`.
            - `input`: The character that must match the input for the transition to occur.
            - `write`: The character to write on the tape.
            - `move`: The head movement direction ("L" for left, "R" for right, "H" for halt).
        start_state (BaseState): 
            The state where the transition originates.
        transition_target_state (BaseState): 
            The state where the transition leads.
    """

    def __init__(self, start_state: BaseState, transition_target_state: BaseState, condition_char: list) -> None:
        """
        Initializes a transition with the start state, target state, and condition details.

        Args:
            start_state (BaseState): The state where the transition originates.
            transition_target_state (BaseState): The state where the transition leads.
            condition_char (str): 
                A string in the format `input|write|move` specifying the input condition, 
                character to write, and head movement direction.
        """
        super().__init__(start_state, transition_target_state, condition_char)
        self.condition_char: list = condition_char

    def canTransition(self, current_input: _ty.Any) -> _result.Result:
        """
        Determines if the transition is valid for the given input and returns the associated actions.

        This method splits the `condition_char` into its components (`input|write|move`) and checks
        if the `input` part matches the current input. If the transition is valid, it returns the 
        character to write and the head movement direction.

        Args:
            current_input (_ty.Any): The current input character to evaluate.

        Returns:
            _result.Result:
                - Success: If the transition is valid, returns a tuple `(to_write, head_move)` where:
                    - `to_write` (str): The character to write on the tape.
                    - `head_move` (str): The direction to move the head ("L", "R", or "H").
                - Failure: If the transition is invalid, returns an error message.
        """

        condition_parts = self.condition_char
        if condition_parts[0] == current_input or condition_parts[0] == "_":
            to_write = condition_parts[1]  # Character to write
            head_move = condition_parts[2]  # Direction to move the head
            return _result.Success((to_write, head_move))  # Transition can occur
        
        return _result.Failure(f"Cannot transition with input {str(current_input)}!")  # Invalid transition


class TMAutomaton(BaseAutomaton):
    """
    Represents a Turing Machine Automaton (TMA).

    A Turing Machine is a theoretical computational model capable of simulating any algorithm.
    It processes an input word on an infinite tape (or bounded tape for Linear Bounded Automata),
    using a finite set of states, transitions, and symbols. The machine can move its head left
    or right, modify tape symbols, and decide whether to halt in an accepting state.

    Attributes:
        memoryTape (dict):
            The tape used by the Turing Machine to process input.

        head (int):
            The current position of the machine's read/write head on the tape.

        current_char (str):
            The current symbol being processed on the tape.

        LBAutomaton (bool):
            Flag indicating whether the machine operates as a Linear Bounded Automaton.

        end_states (_ty.Set[TMState]):
            A set of accepting (end) states for the Turing Machine.

    Methods:
        __init__():
            Initializes the Turing Machine with an empty tape, no end states, and a default mode.

        set_mode(mode: str):
            Sets the operational mode of the automaton (e.g., LBAutomaton).

        set_input(new_word: str) -> None:
            Loads a new input word onto the tape and resets the head position.

        get_input() -> str:
            Retrieves the input word from the tape.

        right() -> None:
            Moves the machine's head to the right and updates the current character.

        left() -> None:
            Moves the machine's head to the left and updates the current character.

        write() -> None:
            Writes the current character to the tape at the head's position.

        set_end_states(new_end_states: _ty.Set[TMState]) -> None:
            Sets the accepting (end) states for the Turing Machine.

        get_end_states() -> _ty.Set[TMState]:
            Retrieves the set of accepting (end) states.

        next_state() -> None:
            Processes a transition based on the current state and input character.

        save(file_path: str) -> bool:
            Placeholder for saving the Turing Machine configuration to a file. (To be implemented)

        load(file_path: str) -> bool:
            Placeholder for loading the Turing Machine configuration from a file. (To be implemented)

        simulate() -> _result.Result:
            Runs the Turing Machine simulation on the input tape and returns the result of acceptance or rejection.

        simulate_one_step() -> _result.Result:
            Executes one step of the Turing Machine simulation and returns the result of acceptance or rejection.
    """

    def __init__(self) -> None:
        """
        Initializes a Turing Machine Automaton (TMA) instance.

        This constructor initializes the machine with:
        - An empty memory tape.
        - No accepting (end) states.
        - The head positioned at the start of the tape.
        - A default operational mode (non-linear bounded).

        It also ensures that the base automaton properties, such as states and transitions, are initialized.
        """
        super().__init__()
        self.memoryTape: str = {}
        self.head: int = 0
        self.current_char: str = ""
        self.LBAutomaton: bool = False
        self.output_alphabet = []
        self.input_alphabet = []
        self.end_states: _ty.Set[TMState] = set()

    def set_mode(self, mode):
        """
        Sets the operational mode of the Turing Machine.

        Args:
            mode (str): The mode of the automaton. "LBAutomaton" enables linear bounded constraints.
        """
        if mode == "LBAutomaton":
            self.LBAutomaton = True
        else:
            self.LBAutomaton = False

    def set_input(self, new_word: str) -> None:
        """
        Loads a new input word onto the tape and resets the head position.

        Args:
            new_word (str): The string of characters to be loaded onto the tape.
        """
        for key, char in enumerate(new_word):
            self.memoryTape[key] = char
        self.head = 0
        self.current_char = self.memoryTape[self.head]

    def get_current_state(self):
        return super().get_current_state()

    def get_input(self) -> str:
        """
        Retrieves the input word from the memory tape.

        Returns:
            str: The reconstructed word from the tape.
        """
        return "".join(self.memoryTape.get(i, "B") for i in range(min(self.memoryTape.keys()), max(self.memoryTape.keys()) + 1))
    def set_input_alphabet(self, alphabet: _ty.Any) -> None:
        """
        Abstract method to set the input alphabet for the automaton.

        Args:
            alphabet (_ty.Any): The input alphabet to be set for the automaton.
        """
        self.input_alphabet = alphabet

    def set_output_alphabet(self, alphabet: _ty.Any) -> None:
        """
        Abstract method to set the output alphabet for the automaton.

        Args:
            alphabet (_ty.Any): The output alphabet to be set for the automaton.
        """
        self.output_alphabet = alphabet

    def get_input_alphabet(self) -> _ty.Any:
        """
        Abstract method to get the input alphabet for the automaton.

        Returns:
            _ty.Any: The input alphabet for the automaton.
        """
        return self.input_alphabet

    def get_output_alphabet(self) -> _ty.Any:
        """
        Abstract method to get the output alphabet for the automaton.

        Returns:
            _ty.Any: The output alphabet for the automaton.
        """
        return self.output_alphabet

    def right(self) -> None:
        """
        Moves the machine's head to the right and updates the current character.

        If the tape at the new position is empty, a blank symbol is added unless operating
        as a Linear Bounded Automaton.

        Returns:
            _result.Failure: If the head attempts to move beyond the bounds in LBA mode.
        """
        self.head += 1
        if self.head in self.memoryTape:
            self.current_char = self.memoryTape[self.head]
        elif not self.LBAutomaton:
            self.memoryTape[self.head] = "B"
            self.current_char = self.memoryTape[self.head]
            print(self.memoryTape)
        else:
            return _result.Failure("You can't go further, your automaton is linear bounded!")

    def left(self) -> None:
        """
        Moves the machine's head to the left and updates the current character.

        If the tape at the new position is empty, a blank symbol is added unless operating
        as a Linear Bounded Automaton.

        Returns:
            _result.Failure: If the head attempts to move beyond the bounds in LBA mode.
        """
        self.head -= 1
        if self.head in self.memoryTape:
            self.current_char = self.memoryTape[self.head]
        elif not self.LBAutomaton:
            self.memoryTape[self.head] = "B"
            self.current_char = self.memoryTape[self.head]
        else:
            return _result.Failure("You can't go further, your automaton is linear bounded!")

    def write(self) -> None:
        """
        Writes the current character to the tape at the head's position.
        """
        if self.current_char != "B":
            self.memoryTape[self.head] = self.current_char
        else:
            del self.memoryTape[self.head]

    def set_end_states(self, new_end_states: _ty.Set[TMState]) -> None:
        """
        Sets the accepting (end) states for the Turing Machine.

        If any of the new end states are not already part of the automaton's states, they are added.

        Args:
            new_end_states (_ty.Set[TMState]): A set of states to mark as accepting states.
        """
        for state in new_end_states:
            if state not in self.get_states():
                self.states.add(state)

        self.end_states = new_end_states

    def get_end_states(self) -> _ty.Set[TMState]:
        """
        Retrieves the set of accepting (end) states for the Turing Machine.

        Returns:
            _ty.Set[TMState]: A set containing all the machine's accepting states.
        """
        return self.end_states

    def next_state(self) -> None:
        """
        Processes a transition based on the current state and input character.

        Uses the `find_transition` method of the current state to determine the appropriate transition.
        If no valid transition is found or the target state is invalid, the machine halts.

        Returns:
            None: If the machine halts due to an invalid state or transition.
        """
        transition_result: _result.Result = self.current_state.find_transition(self.current_char)
        if not isinstance(transition_result, _result.Success):
            return _result.Failure("There's no possible transition")
        
        target_state, condition = transition_result.unwrap()

        transition: TMState = target_state
        if not transition or transition not in self.states:
            return  _result.Failure("Invalid target state!") 

        self.current_state = transition
        print(self.current_state)
        return condition

    def next_location(self, callback=None):
        """
        Executes a callback function to move the head or process a transition.

        Args:
            callback (callable, optional): A function to execute for the next operation.

        Notes:
            If no callback is set, the function attempts to use the "choose_function" attribute.
        """
        if not hasattr(self, "choose_function"):
            print("Attribute 'choose_function' has not been set.")
            if callback:
                self.choose_function = callback
            else:
                print("No callback provided.")
                return
        else:
            self.choose_function()
            delattr(self, "choose_function")

    def simulate(self) -> _result.Result:
        """
        Runs the Turing Machine simulation on the input tape.

        The simulation begins at the start state and processes tape symbols based on transition rules.
        It writes to the tape, moves the head, and halts when a halting condition is met. The result
        depends on whether the machine ends in an accepting state.

        Returns:
            _result.Result:
                - Success: If the machine halts in an accepting state.
                - Failure: If the machine halts in a non-accepting state or encounters an error.

        Notes:
            If no start state is set or the start state is not part of the automaton's states,
            an error is logged and the simulation returns a failure.
        """
        if not self.start_state:
            #ActLogger().error("Tried to start simulation of TM-Automaton without start state!")
            return _result.Failure("No start state found")

        if self.start_state not in self.states:
            #ActLogger().error("Tried to start simulation of TM-Automaton without start state in automaton states!")
            return _result.Failure("Start state not in automaton states")

        self.current_state = self.start_state
        self.current_state.activate()

        while True:
            condition = self.next_state()  # Transition to the next state.
            if isinstance(condition, _result.Failure):
                return condition
            if isinstance(condition, tuple) and len(condition) == 2:
                self.current_char = condition[0] 
            else:
                return _result.Failure("There is no condition!")
            if self.current_char != "_":
                self.write()
            if condition[1] == "L":
                self.left()
            elif condition[1] == "R":
                self.right()
            elif condition[1] == "H":
                break

            self.current_char = self.memoryTape[self.head]
            self.current_state.activate()  # Activate the current state (if such behavior is defined).

        if self.current_state in self.end_states:
            return _result.Success("Automaton terminated in an end state!")
        return _result.Failure("Automaton failed to terminate in an end state!")

    def simulate_one_step(self) -> _result.Result:
        """
        Executes one step of the Turing Machine simulation.

        Processes the current tape symbol, transitions to the next state, updates the tape if needed,
        and moves the head based on the transition rule. The machine halts if a halting condition
        is reached during the step.

        Returns:
            _result.Result:
                - Success: If the machine halts in an accepting state during the step.
                - Failure: If the machine halts in a non-accepting state or encounters an error.

        Notes:
            If no start state is set or the start state is not part of the automaton's states,
            an error is logged and the simulation returns a failure.
        """
        for state in self.states:
            state.deactivate()
        for transition in self.transitions:
            transition.deactivate()
        if not self.start_state:
            #ActLogger().error("Tried to start simulation of DFA-Automaton without start state!")
            return _result.Failure("No start state found")

        if self.start_state not in self.states:
            #ActLogger().error("Tried to start simulation of DFA-Automaton without start state in automaton states!")
            return _result.Failure("Start state not in automaton states")

        if self.current_state is None:
            self.current_state = self.start_state
            self.current_state.activate()


        condition = self.next_state()  # Transition to the next state.
        if isinstance(condition, _result.Failure):
            return condition
        if isinstance(condition, tuple) and len(condition) == 2:
            self.current_char = condition[0] 
            self.write()
        else: 
            return _result.Failure("There is no condition.")
        if condition[1] == "L":
            self.left()
        if condition[1] == "R":
            self.right()
        if condition[1] == "H":
            if self.current_state in self.end_states:
                return _result.Success("Automaton terminated in an end state!")
            return _result.Failure("Automaton failed to terminate in an end state!")

    def add_state(self, state: BaseState, state_type: str) -> None:
        self.states.add(state)
        match state_type.lower():
            case "end":
                self.end_states.add(state)
            case "default":
                pass
                

    def get_current_index(self) -> int:
        return self.head

    def get_current_return_value(self) -> _ty.Any:
        return self.memoryTape



