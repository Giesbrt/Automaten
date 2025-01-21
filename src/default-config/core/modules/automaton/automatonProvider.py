"""TBA"""

# Abstract Machine related imports
from core.extensions.DFA import DFAAutomaton, DFAState, DFATransition
from core.modules.automaton.TM import TMAutomaton, TMState, TMTransition
from core.modules.automaton.mealy import mealyAutomaton, mealyState, mealyTransition

from aplustools.io import ActLogger

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts

# Docs generated with Github Copilot


class AutomatonProvider:
    registered_automatons: _ty.Dict[str, _ty.Dict[str, _ty.Callable]] = {}

    def __init__(self, automaton_type: str) -> None:
        self.automaton_type: str = automaton_type

        # registered Automatons
        self.register_automaton('dfa', DFAAutomaton, DFAState, DFATransition)
        self.register_automaton('tm', TMAutomaton.TMAutomaton, TMState.TMState, TMTransition.TMTransition)
        self.register_automaton("mealy", mealyAutomaton.MealyAutomaton, mealyState.MealyState, mealyTransition.MealyTransition)

    def set_automaton_type(self, new_type: str) -> None:
        """Set the type of the automaton
        
        :param new_type: The new type of the automaton
        :return: None
        """
        self.automaton_type = new_type

    def get_automaton_type(self) -> str:
        """Get the type of the automaton
        
        :return: The type of the automaton
        """
        return self.automaton_type

    def register_automaton(self, name: str, base: _ty.Callable, state: _ty.Callable, transition: _ty.Callable) -> None:
        """Register a new automaton
        
        :param name: The name of the automaton
        :param base: The base class of the automaton
        :param state: The state class of the automaton
        :param transition: The transition class of the automaton
        :return: None
        """
        if name.lower() in self.registered_automatons:
            return

        automaton_data: _ty.Dict[str, _ty.Callable] = {'base': base,
                                                       'state': state,
                                                       'transition': transition}
        self.registered_automatons[name.lower()] = automaton_data
        ActLogger().info(f"Registered new {name.lower()}-Automaton")

    def get_automaton_base(self) -> _ty.Callable:
        """Get the base class of the automaton
        
        :return: The base class of the automaton
        """
        return self.registered_automatons[self.automaton_type]['base']

    def get_automaton_state(self) -> _ty.Callable:
        """Get the state class of the automaton
        
        :return: The state class of the automaton
        """
        return self.registered_automatons[self.automaton_type]['state']

    def get_automaton_transition(self) -> _ty.Callable:
        """Get the transition class of the automaton
        
        :return: The transition class of the automaton
        """
        return self.registered_automatons[self.automaton_type]['transition']

    def is_automaton(self) -> bool:
        """Check if the automaton is registered
        
        :return: True if the automaton is registered, False otherwise"""
        return self.automaton_type in self.registered_automatons
