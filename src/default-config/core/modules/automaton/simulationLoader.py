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

    def load_automaton(self, serialised_automaton: _ty.Dict[str, _ty.Any]) -> _result.Result:
        # Accepts format, displayed in automaten.json
        id_string: str = serialised_automaton['id']  # author:automaton_type
        split_id_string: _ty.List[str] = id_string.split(':')
        automaton_type: str = split_id_string[1]

        # does the requested automaton exist?
        success: bool = self.init_automaton(automaton_type)
        if not success:
            log_message: str = f"Could not recognise automaton of type {automaton_type}"
            ActLogger().error(log_message)
            return _result.Failure(log_message)

        automaton_provider: AutomatonProvider = AutomatonProvider(automaton_type)
        raw_state = automaton_provider.get_automaton_state()

        content: _ty.List[_ty.Dict[str, _ty.Any]] = serialised_automaton['content']

        transitions: _ty.List[_ty.Dict[str, _ty.Any]] = []

        for i, state in enumerate(content):
            # Create a state
            state_name: str = state['name']
            state_type: str = state["type"]

            specific_state = raw_state(state_name)
            self.automaton.add_state(specific_state, state_type)
            # todo handle start state

            # Handle transition
            transition_data: _ty.List[_ty.Any] = state['transitions']
            for transition in transition_data:
                # Copy the transition and add a field "from" which is the id of the current node
                modified: _ty.Dict[str, _ty.Any] = transition
                modified["from"] = i
                transitions.append(modified)

            # Create transitions
            raw_transition = automaton_provider.get_automaton_transition()
            for transition in transitions:
                to_state: int = transition["to"]
                from_state: int = transition["from"]
                condition: str = transition["condition"]

                start_state = self.automaton.get_state_by_id(to_state)
                end_state = self.automaton.get_state_by_id(from_state)
                transition = raw_transition(start_state, end_state, condition)

                start_state.add_transition(transition)
                self.automaton.get_transitions(True)



    def init_automaton(self, automaton_type: str) -> bool:
        automaton_provider: AutomatonProvider = AutomatonProvider(automaton_type)
        if not automaton_provider.is_automaton():
            ActLogger().error(f"Could not recognise automaton of type {automaton_type}")
            return False

        automaton_implementation: BaseAutomaton = automaton_provider.get_automaton_base()()
        self.automaton = AutomatonBridge(automaton_implementation)
        ActLogger().info(f"Initialised new {automaton_type}-Automaton")

        self.__reset_temp_data()
        return True

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
