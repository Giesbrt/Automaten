"""TBA"""
from returns import result as _result
from aplustools.io import ActLogger

# Standard typing imports for aps
import typing as _ty

# Abstract Machine related imports
from DFAState import DFAState
from core.modules.automaton.base.automaton import Automaton as BaseAutomaton


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

        set_end_states(new_end_states: _ty.Set[DFAState]) -> None:
            Sets the accepting (end) states for the automaton.

        get_end_states() -> _ty.Set[DFAState]:
            Retrieves the set of accepting (end) states.

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
        self.word: str = ""
        self.char_index: int = 0
        self.current_char: str = ""

        self.end_states: _ty.Set[DFAState] = set()

    def set_word(self, new_word: str) -> None:
        """
        Sets a new input word for the DFA to process.

        Args:
            new_word (str): The string of characters to be processed by the automaton.
        """
        self.word = new_word
        self.char_index = 0
        self.current_char = self.word[self.char_index] if self.word else ""

    def get_word(self) -> str:
        return self.word

    def next_char(self) -> None:
        """
        Advances the DFA to the next character in the input word.

        If the end of the word is reached, the character index is clamped to the word's bounds.
        """
        self.char_index += 1
        self.current_char = self.word[max(0, min(self.char_index, len(self.word) - 1))]

    def set_end_states(self, new_end_states: _ty.Set[DFAState]) -> None:
        """
        Sets the accepting (end) states for the DFA.

        If any of the new end states are not already part of the automaton's states, they are added.

        Args:
            new_end_states (_ty.Set[DFAState]): A set of states to mark as accepting states.
        """
        for state in new_end_states:
            if state not in self.get_states():
                self.states.add(state)

        self.end_states = new_end_states

    def get_end_states(self) -> _ty.Set[DFAState]:
        """
        Retrieves the set of accepting (end) states for the DFA.

        Returns:
            _ty.Set[DFAState]: A set containing all the DFA's accepting states.
        """
        return self.end_states

    def next_state(self) -> None:
        """
        Transitions the DFA to the next state based on the current state and input character.

        Uses the `find_transition` method of the current state to determine the appropriate transition.
        If no valid transition is found or the target state is invalid, the automaton halts.
        """
        transition_result: _result.Result = self.current_state.find_transition(self.current_char)

        if not isinstance(transition_result, _result.Success):
            return  # No valid transition found.

        transition: DFAState = transition_result.value_or(None)
        if not transition or transition not in self.states:
            return  # Invalid target state.

        self.current_state = transition

    def serialise(self, file_path: str) -> bool:
        """
        Placeholder for saving the DFA configuration to a file.

        Args:
            file_path (str): The path where the DFA configuration will be saved.

        Returns:
            bool: False since the method is not yet implemented.
        """
        # TODO: Implement saving logic for DFA.
        return False

    @staticmethod
    def load(file_path: str) -> bool:
        """
        Placeholder for loading the DFA configuration from a file.

        Args:
            file_path (str): The path to the file containing the DFA configuration.

        Returns:
            bool: False since the method is not yet implemented.
        """
        # TODO: Implement loading logic for DFA.
        return False

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
            self.next_state()  # Transition to the next state.
            self.next_char()   # Move to the next character in the input.
            self.current_state.activate()  # Activate the current state (if such behavior is defined).

            if self.char_index >= len(self.word):
                break  # Stop simulation when the end of the word is reached.

        if self.current_state in self.end_states:
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
            if self.current_state in self.end_states:
                return _result.Success("Automaton terminated in an end state!")
            return _result.Failure("Automaton failed to terminate in an end state!")

        if not self.start_state:
            ActLogger().error("Tried to start simulation of DFA-Automaton without start state!")
            return _result.Failure("No start state found")

        if self.start_state not in self.states:
            ActLogger().error("Tried to start simulation of DFA-Automaton without start state in automaton states!")
            return _result.Failure("Start state not in automaton states")

        if self.current_state is None:
            self.current_state = self.start_state
            self.current_state.activate()

        self.next_state()  # Transition to the next state.
        self.next_char()  # Move to the next character in the input.
        self.current_state.activate()  # Activate the current state (if such behavior is defined).




