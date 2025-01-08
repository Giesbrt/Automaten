"""TBA"""

# Abstract Machine related imports
from core.modules.automaton.dfa import DFAAutomaton, DFAState, DFATransition
from core.modules.automaton.TM import TMAutomaton, TMState, TMTransition

from aplustools.io import ActLogger

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts


class AutomatonProvider:
    registered_automatons: _ty.Dict[str, _ty.Dict[str, _ty.Callable]] = {}

    def __init__(self, automaton_type: str) -> None:
        self.automaton_type: str = automaton_type

        # registered Automatons
        self.register_automaton('dfa', DFAAutomaton.DFAAutomaton, DFAState.DFAState, DFATransition.DFATransition)
        self.register_automaton('tm', TMAutomaton.TMAutomaton, TMState.TMState, TMTransition.TMTransition)

    def set_automaton_type(self, new_type: str) -> None:
        self.automaton_type = new_type

    def get_automaton_type(self) -> str:
        return self.automaton_type

    def register_automaton(self, name: str, base: _ty.Callable, state: _ty.Callable, transition: _ty.Callable) -> None:
        if name.lower() in self.registered_automatons:
            return

        automaton_data: _ty.Dict[str, _ty.Callable] = {'base': base,
                                                       'state': state,
                                                       'transition': transition}
        self.registered_automatons[name.lower()] = automaton_data
        ActLogger().info(f"Registered new {name.lower()}-Automaton")

    def get_automaton_base(self) -> _ty.Callable:
        return self.registered_automatons[self.automaton_type]['base']

    def get_automaton_state(self) -> _ty.Callable:
        return self.registered_automatons[self.automaton_type]['state']

    def get_automaton_transition(self) -> _ty.Callable:
        return self.registered_automatons[self.automaton_type]['transition']

    def is_automaton(self) -> bool:
        return self.automaton_type in self.registered_automatons
