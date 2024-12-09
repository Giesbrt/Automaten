"""TBA"""
from returns import result as _result
from aplustools.io import ActLogger

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

# Abstract Machine related imports
from DFAState import DFAState
from core.base.automaton import Automaton as BaseAutomaton
from core.base.transition import Transition as BaseTransition


class DFAAutomaton(BaseAutomaton):

    def __init__(self) -> None:
        super().__init__()
        self.word: str = ""
        self.char_index: int = 0
        self.current_char: str = ""

        self.end_states: _ty.Set[DFAState] = set()

    def set_word(self, new_word: str) -> None:
        self.word = new_word
        self.current_char = self.word[self.char_index]

    def next_char(self) -> None:
        self.char_index += 1
        # clamp self.char_index between 0 and len(self.word) -1
        self.current_char = self.word[max(0, min(self.char_index, len(self.word) - 1))]

    def set_end_states(self, new_end_states: _ty.Set[DFAState]) -> None:
        for item in new_end_states:
            if item in self.get_states():
                continue
            self.states.add(item)

        self.end_states = new_end_states

    def get_end_states(self) -> _ty.Set:
        return self.end_states

    def next_state(self) -> None:
        transition_result: _result.Result = self.current_state.find_transition(self.current_char)

        if not isinstance(transition_result, _result.Success):
            return

        transition: DFAState = transition_result.value_or(None)
        if not transition or transition not in self.states:
            return

        self.current_state = transition

    def save(self, file_path: str) -> bool:
        pass

    def load(self, file_path: str) -> bool:
        pass

    def simulate(self) -> _result.Result:  # Todo adjust to future display of simulation (Einzelschrittmodus)
        if not self.start_state:
            ActLogger().error("Tried to start simulation of DFA-Automaton without start state!")
            return _result.Failure("No start state found")

        if self.start_state not in self.states:
            ActLogger().error("Tried to start simulation of DFA-Automaton without start state in automaton states!")
            return _result.Failure("Start state not in automaton states")

        self.current_state = self.start_state
        while True:
            self.next_state()
            self.current_state.activate()
            self.next_char()

            if self.char_index >= len(self.word):
                break

        if self.current_state in self.end_states:
            return _result.Success("Automaton terminated in an end state!")
        return _result.Failure("Automaton failed to terminate in an end state!")
