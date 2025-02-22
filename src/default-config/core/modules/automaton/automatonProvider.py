"""TBA"""

from aplustools.io import ActLogger
from utils.errorCache import ErrorCache

# Standard typing imports for aps
import typing as _ty
import types as _ts

# Abstract Machine related
from core.modules.automaton.base.automaton import Automaton as BaseAutomaton
from core.modules.automaton.base.state import State as BaseState
from core.modules.automaton.base.transition import Transition as BaseTransition
from core.modules.automaton.base.settings import Settings as BaseSettings

from extensions.DFA import DFAState, DFATransition, DFAAutomaton, DFASettings


#from extensions.TM import TMAutomaton, TMState, TMTransition, TmSettings  TODO: Use loader, TM currently has an import error
#from extensions.mealy import MealyState, MealyTransition, MealyAutomaton


# Docs generated with GitHub Copilot


class AutomatonProvider:
    registered_automatons: _ty.Dict[str, _ty.Dict[str, _ty.Callable]] = {}

    def __init__(self, automaton_type: str, test_mode: bool = False) -> None:
        if automaton_type is not None:
            self.automaton_type: str = automaton_type.lower()
        else:
            self.automaton_type: str = "N/A"

        # registered Automatons
        if test_mode:
            self.register_automaton('dfa', DFAAutomaton, DFAState, DFATransition)
            # self.register_automaton('tm', TMAutomaton, TMState, TMTransition)
            # self.register_automaton("mealy", MealyAutomaton, MealyState, MealyTransition)

    def load_from_dict(self, loaded_automatons: _ty.Dict[str, _ty.List[_ty.Callable]], override: bool = False) -> None:
        """ Loads the required automatons classes from a dictionary

        :param loaded_automatons: {'Automaton': [Automaton, State, Transition]}
        :param override: Should the previous registration be overruled
        :return: None
        """
        # TODO rework?
        # 0: base; 1: State; 2: Transition
        for key in list(loaded_automatons.keys()):
            data = loaded_automatons[key]
            # print(data)

            automaton: BaseAutomaton | None = None
            state: BaseState | None = None
            transition: BaseTransition | None = None
            settings: BaseSettings | None = None

            for automaton_class in data:
                automaton = self._check_for_classes(automaton_class, automaton, BaseAutomaton)
                state = self._check_for_classes(automaton_class, state, BaseState)
                transition = self._check_for_classes(automaton_class, transition, BaseTransition)
                settings = self._check_for_classes(automaton_class, settings, BaseSettings)

            integrity_check: _ty.List[bool] = [automaton is not None, state is not None,
                                               transition is not None, settings is not None]

            if not all(integrity_check):
                ErrorCache().error(f"Failed to load {key}-automaton!",
                                   f"Could not load {key}-Automaton due to a class mismatching!\n "
                                   f"{automaton}, {state}, {transition}, {settings}", True)
                return

            self.register_automaton(key, automaton, state, transition, override)

    def _check_for_classes(self, check_object: _ty.Any, class_variable: _ty.Any | None, class_type: type) -> _ty.Any:
        if class_variable is None and issubclass(check_object, class_type):
            return check_object

        return class_variable

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

    def register_automaton(self, name: str, base: BaseAutomaton, state: BaseState, transition: BaseTransition,
                           override: bool = False) -> None:
        """Register a new automaton
        
        :param name: The name of the automaton
        :param base: The base class of the automaton
        :param state: The state class of the automaton
        :param transition: The transition class of the automaton
        :param override: Should the previous registration be overruled
        :return: None
        """
        if name.lower() in self.registered_automatons and not override:
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
