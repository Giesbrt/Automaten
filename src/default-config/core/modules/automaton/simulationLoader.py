"""TBA"""
from returns import result as _result

# Abstract Machine related imports
from core.modules.automaton.automatonBridge import AutomatonBridge
from core.modules.automaton.base.automaton import Automaton as BaseAutomaton
from core.modules.automaton.automatonProvider import AutomatonProvider
from core.modules.automaton.UiBridge import UiBridge

from queue import Queue

from aplustools.io import ActLogger
from serializer import Serializer
from core.modules.storage import JSONAppStorage

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts


class SimulationLoader:

    def __init__(self, json_app_storage: JSONAppStorage):
        super().__init__()
        # App storage access
        self.app_storage: JSONAppStorage = json_app_storage
        loaded_max_restart_counter: int = self.app_storage.retrieve("simulation_loader_max_restart_counter", int)

        self.restart_counter: int = 0
        self.max_restart_counter: int = loaded_max_restart_counter or 5  # set default of 5 if the config could not be read

        self.error_callback: _ty.Callable or None = None
        self.error_cache: Queue[str] = Queue()

        self.automaton: AutomatonBridge = None

    def set_error_callback(self, callback: _ty.Callable) -> None:
        self.error_callback = callback

    def get_error_callback(self) -> _ty.Callable or None:
        return self.error_callback

    def save_automaton(self, file_path: str) -> _result.Result:
        automaton_implementation: BaseAutomaton = self.automaton.get_implementation()
        serialisation_result: _result.Result = Serializer.serialise(automaton_implementation, file_path)

        return serialisation_result

    def load_automaton(self, file_path: str) -> _result.Result:
        deserialization_result: _result.Result = Serializer.load(file_path)
        if not isinstance(deserialization_result, _result.Success):
            return deserialization_result

        loaded_automaton = deserialization_result.value_or(None)
        if loaded_automaton is None:
            log_message: str = "Could not load automaton: Automaton is None"
            ActLogger().error(log_message)
            return _result.Failure(log_message)

        if not isinstance(loaded_automaton, BaseAutomaton):
            log_message: str = f"Loaded automaton is not recognised as an automaton: {type(loaded_automaton).__name__}"
            ActLogger().error(log_message)
            return _result.Failure(log_message)

        automaton_bridge: AutomatonBridge = AutomatonBridge(loaded_automaton)
        self.automaton = automaton_bridge
        self.__reset_temp_data()

        log_message: str = f"Loaded automaton of type {type(loaded_automaton).__name__}"
        ActLogger().info(log_message)
        return _result.Success(log_message)

    def init_automaton(self, automaton_type: str) -> None:
        automaton_provider: AutomatonProvider = AutomatonProvider(automaton_type)
        automaton_implementation: BaseAutomaton = automaton_provider.get_automaton_base()()
        self.automaton = AutomatonBridge(automaton_implementation)
        ActLogger().info(f"Initialised new {automaton_type}-Automaton")

        self.__reset_temp_data()

    def __reset_temp_data(self) -> None:
        self.restart_counter = 0
        self.error_cache = Queue()

    def serialise_automaton_to_bridge(self) -> None:
        from core.modules.automaton.base.state import State
        from core.modules.automaton.base.transition import Transition

        serialised_update: _ty.Dict[str, _ty.Any] = {}

        # serialisation
        for state in self.automaton.get_states():
            state: State = state
            if not state.is_active():
                continue

            serialised_update["state"] = {}
            serialised_update["state"]["id"] = self.automaton.get_state_index(state)
            serialised_update["state"]["is_active"] = state.is_active()

        for transition in self.automaton.get_transitions():
            transition: Transition = transition
            if not transition.is_active():
                continue

            serialised_update["transition"] = {}
            serialised_update["transition"]["id"] = self.automaton.get_transition_index(transition)
            serialised_update["transition"]["is_active"] = transition.is_active()

        serialised_update["automaton"] = {}
        serialised_update["automaton"]["input"] = list(self.automaton.get_input())
        serialised_update["automaton"]["pointer_index"] = self.automaton.get_current_index()
        serialised_update["automaton"]["output"] = self.automaton.get_current_return_value()

        # push to bridge
        UiBridge().add_simulation_item(serialised_update)

    def handle_bridge(self) -> None:  # Todo get data from bridge and handle it
        pass

    def simulate(self) -> _result.Result:  # Todo handle return value
        try:
            return_result = self.automaton.simulate_one_step()
            self.serialise_automaton_to_bridge()

            while return_result is None:
                return_result = self.automaton.simulate_one_step()
                self.serialise_automaton_to_bridge()

        except Exception as e:
            log_message: str = (f"An error occurred whilst trying to simulate an "
                                f"{self.automaton.get_implementation_name()}: {str(e)}")
            self.__handle_failure(log_message, self.simulate)
            return _result.Failure(log_message)

    def get_restart_counter(self) -> int:
        return self.restart_counter

    def __handle_failure(self, log_message: str, action: _ty.Callable = None) -> None:
        self.restart_counter += 1
        ActLogger().error(log_message)
        self.error_cache.put(log_message)

        if self.restart_counter < self.max_restart_counter:
            if action is not None:
                action()
            return

        # notify the user that the module is broken
        self.error_callback()
