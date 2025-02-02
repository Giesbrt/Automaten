"""TBA"""
from returns import result as _result
from aplustools.io import ActLogger

# Standard typing imports for aps
import typing as _ty

# Abstract Machine related imports
from old_but_maybe_needed.dfa.DFAState import DFAState
from core.modules.automaton.base.automaton import Automaton as BaseAutomaton

from core.modules.automaton.base.state import State


# Docs generated with Chat-GPT

class DFAAutomaton(BaseAutomaton):
    """
    Represents a Deterministic Finite Automaton (DFA).

    A DFA is a type of automaton used to recognize patterns in strings based on a finite set of
    states, transitions, and an alphabet. The DFA begins in a start state, reads characters from
    an input word, and transitions between states based on the current state and input character.
    The simulation determines whether the word is accepted or rejected based on whether the
    automaton terminates in an end state.

    Attributes:
        word (str):
            The input word to be processed by the automaton.

        char_index (int):
            Tracks the current position in the input word.

        current_char (str):
            The current character being processed from the input word.

        end_states (_ty.Set[DFAState]):
            A set of accepting (end) states for the automaton.

    Methods:
        __init__():
            Initializes the DFA with empty states, transitions, and input word.

        set_word(new_word: str) -> None:
            Sets a new input word for the automaton to process.

        get_word() -> str:
            Retrieves the input word for the automaton to process.

        next_char() -> None:
            Advances the automaton to the next character in the input word.

        next_state() -> None:
            Processes a transition based on the current state and input character.

        save(file_path: str) -> bool:
            Placeholder for saving the DFA configuration to a file. (To be implemented)

        load(file_path: str) -> bool:
            Placeholder for loading the DFA configuration from a file. (To be implemented)

        simulate() -> _result.Result:
            Runs the DFA simulation on the input word and returns the result of acceptance or rejection.

        simulate_one_step() -> _result.Result:
            Runs one step of the DFA simulation on the input word and returns the result of acceptance or rejection.
    """

    def __init__(self) -> None:
        """
        Initializes a Deterministic Finite Automaton (DFA) instance.

        This constructor initializes the DFA with:
        - An empty input word.
        - No accepting (end) states.
        - A character index set to the beginning of the word.
        - The current character set to an empty string.

        It also ensures that the base automaton properties, such as states and transitions, are initialized.
        """
        super().__init__()
        self.word: list = []
        self.char_index: int = 0
        self.current_char: str = ""

        self._input_alphabet = []
        self._output_alphabet = []
        self._end_states: _ty.Set[State] = set()

    def set_input(self, automaton_input: _ty.Any) -> None:
        """
        Sets a new input word for the DFA to process.

        Args:
            automaton_input (str): The string of characters to be processed by the automaton.
        """
        self.word = list(automaton_input)
        self.char_index = 0
        self.current_char = self.word[self.char_index] if self.word else ""

    def get_input(self) -> _ty.Any:
        return self.word

    def next_char(self) -> None:
        """
        Advances the DFA to the next character in the input word.

        If the end of the word is reached, the character index is clamped to the word's bounds.
        """
        self.char_index += 1
        self.current_char = self.word[max(0, min(self.char_index, len(self.word) - 1))]

    def next_state(self) -> _result.Result:
        """
        Transitions the DFA to the next state based on the current state and input character.

        Uses the `find_transition` method of the current state to determine the appropriate transition.
        If no valid transition is found or the target state is invalid, the automaton halts.
        """
        transition_result: _result.Result = self.current_state.find_transition(self.current_char)

        if not isinstance(transition_result, _result.Success):
            return _result.Failure("No valid transition found!")      # No valid transition found.

        transition: DFAState = transition_result.value_or(None)
        if not transition or transition not in self.states:
            return _result.Failure("Invalid target state!")  # Invalid target state.

        self.current_state = transition
        return _result.Success(None)

    def simulate(self) -> _result.Result:
        """
        Runs the DFA simulation on the input word.

        The simulation begins at the start state and processes each character in the input word,
        transitioning between states based on the DFA's transition rules. If the DFA ends in an
        accepting state after processing the entire word, it returns a success result. Otherwise,
        it returns a failure result.

        Returns:
            _result.Result:
                - Success: If the DFA terminates in an accepting state.
                - Failure: If the DFA fails to terminate in an accepting state.

        Notes:
            If no start state is set or the start state is not part of the automaton's states,
            an error is logged and the simulation returns a failure.
        """
        if not self.start_state:
            ActLogger().error("Tried to start simulation of DFA-Automaton without start state!")
            return _result.Failure("No start state found")

        if self.start_state not in self.states:
            ActLogger().error("Tried to start simulation of DFA-Automaton without start state in automaton states!")
            return _result.Failure("Start state not in automaton states")

        self.current_state = self.start_state
        self.current_state.activate()

        while True:
            result: _result.Result = self.next_state()  # Transition to the next state.
            if not isinstance(result, _result.Success):
                ActLogger().error(result.value_or("Failed to cache error message!"))
                return result

            self.next_char()  # Move to the next character in the input.
            self.current_state.activate()  # Activate the current state (if such behavior is defined).

            if self.char_index >= len(self.word):
                break  # Stop simulation when the end of the word is reached.

        if self.current_state in self._end_states:
            return _result.Success("Automaton terminated in an end state!")
        return _result.Failure("Automaton failed to terminate in an end state!")

    def simulate_one_step(self) -> _result.Result:
        """
        Runs one step of the DFA simulation on the input word.

        The simulation begins at the start state and processes each character in the input word,
        transitioning between states based on the DFA's transition rules. If the DFA ends in an
        accepting state after processing the entire word, it returns a success result. Otherwise,
        it returns a failure result.

        Returns:
            _result.Result:
                - Success: If the DFA terminates in an accepting state.
                - Failure: If the DFA fails to terminate in an accepting state.

        Notes:
            If no start state is set or the start state is not part of the automaton's states,
            an error is logged and the simulation returns a failure.
        """
        if self.char_index >= len(self.word):
            if self.current_state in self._end_states:
                return _result.Success("Automaton terminated in an end state!")
            return _result.Failure("Automaton failed to terminate in an end state!")

        if not self.start_state:
            ActLogger().error("Tried to start simulation of DFA-Automaton without start state!")
            return _result.Failure("No start state found")

        if self.start_state not in self.states:
            ActLogger().error("Tried to start simulation of DFA-Automaton without start state in automaton states!")
            return _result.Failure("Start state not in automaton states")

        # loop die alle states und transitions deaktiviert (state#deactivate())
        for state in self.get_states():
            state.deactivate()

        for transition in self.get_transitions():
            transition.deactivate()

        if self.current_state is None:
            self.current_state = self.start_state
            self.current_state.activate()

        result: _result.Result = self.next_state()  # Transition to the next state.
        if not isinstance(result, _result.Success):
            ActLogger().error(result.value_or("Failed to cache error message!"))
            return result

        self.next_char()  # Move to the next character in the input.
        self.current_state.activate()  # Activate the current state (if such behavior is defined).

    def set_input_alphabet(self, alphabet: _ty.Any) -> None:
        self._input_alphabet = alphabet

    def set_output_alphabet(self, alphabet: _ty.Any) -> None:
        self._output_alphabet = alphabet

    def get_input_alphabet(self) -> _ty.Any:
        return self._input_alphabet

    def get_output_alphabet(self) -> _ty.Any:
        return self._output_alphabet

    def get_current_return_value(self) -> _ty.Any:
        """
        Returns the last return value of the automaton after one step of simulation

        Returns:
            _ty.Any: The return value
        """
        return None  # None due to the lack of return values in a dfa automaton

    def get_current_index(self) -> int:
        """
        Returns the current index where the pointer (on the input sequence) is located

        Returns:
            int: current index of the pointer
        """
        return self.char_index

    def add_state(self, state: State, state_type: str) -> None:
        self.states.add(state)
        match state_type:
            case "end":
                self._end_states.add(state)

            case "default":
                pass







