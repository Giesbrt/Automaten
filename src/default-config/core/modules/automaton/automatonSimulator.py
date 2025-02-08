from returns import result as _result
from aplustools.io import ActLogger

from core.modules.automaton.automatonBridge import AutomatonBridge
from core.modules.automaton.base.automaton import Automaton as BaseAutomaton
from core.modules.automaton.automatonProvider import AutomatonProvider

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts
import traceback

# Docs generated with Github Copilot


class AutomatonSimulator:
    def __init__(self, simulation_request: _ty.Dict[str, _ty.Any],
                 simulation_result_callback: _ty.Callable,
                 error_callable: _ty.Callable):
        super().__init__()

        self._simulation_request: _ty.Dict[str, _ty.Any] = simulation_request
        self._simulation_result_callback: _ty.Callable = simulation_result_callback
        self._error_callable: _ty.Callable = error_callable

        self.automaton: AutomatonBridge | None = None

    def run(self) -> _result.Result:
        """Run the automaton simulation
        
        :return: The result of the simulation"""
        self._build_automaton()

        automaton_input: _ty.List[_ty.Any] = self._simulation_request["input"]
        self.automaton.set_input(automaton_input)
        print(self.automaton.get_input())

        return self._simulate()

    def _init_automaton(self, automaton_type: str) -> bool:
        """Initialise the automaton
        
        :param automaton_type: The type of automaton to initialise
        :return: True if the automaton was initialised successfully, False otherwise
        """
        automaton_provider: AutomatonProvider = AutomatonProvider(automaton_type)
        if not automaton_provider.is_automaton():
            ActLogger().error(f"Could not recognise automaton of type {automaton_type}")
            return False

        automaton_implementation: BaseAutomaton = automaton_provider.get_automaton_base()()
        self.automaton = AutomatonBridge(automaton_implementation)
        ActLogger().info(f"Initialised new {automaton_type}-Automaton")
        return True

    def _build_automaton(self) -> _result.Result:
        """Build the automaton
        
        :return: The result of the build
        """
        serialised_automaton: _ty.Dict[str, _ty.Any] = self._simulation_request

        # Accepts format, displayed in automaten.json
        id_string: str = serialised_automaton['id']  # author:automaton_type
        split_id_string: _ty.List[str] = id_string.split(':')
        automaton_type: str = split_id_string[1]

        # does the requested automaton exist?
        success: bool = self._init_automaton(automaton_type)
        print(success)
        if not success:
            log_message: str = f"Could not recognise automaton of type {automaton_type}"
            ActLogger().error(log_message)
            return _result.Failure(log_message)

        automaton_provider: AutomatonProvider = AutomatonProvider(automaton_type)
        raw_state = automaton_provider.get_automaton_state()

        content: _ty.List[_ty.Dict[str, _ty.Any]] = serialised_automaton['content']

        transitions: _ty.List[_ty.Tuple[int, _ty.Dict[str, _ty.Any]]] = []

        temp_states: _ty.Dict[int, _ty.Any] = {}

        for i, state in enumerate(content):

            # Create a state
            state_name: str = state['name']
            state_type: str = state["type"]

            specific_state = raw_state(state_name)
            self.automaton.add_state(specific_state, state_type)
            temp_states[i] = specific_state

            # handle start state
            if i == 0:
                self.automaton.set_start_state(specific_state)
                ActLogger().info(f"Start State set to state {state_name}")

            # Handle transition
            transition_data: _ty.List[_ty.Any] = state['transitions']
            for transition in transition_data:
                # Copy the transition and add a field "from" which is the id of the current node
                modified: _ty.Dict[str, _ty.Any] = transition
                modified["from"] = i
                transitions.append((modified["id"], modified.copy()))

        # Create transitions
        raw_transition = automaton_provider.get_automaton_transition()

        # sort transitions
        transitions = sorted(transitions, key=lambda x: x[0])
        for i, transition in transitions:
            to_state: int = transition["to"]
            from_state: int = transition["from"]
            condition: _ty.List[_ty.Any] = transition["condition"]

            start_state = temp_states[from_state]
            end_state = temp_states[to_state]
            specific_transition = raw_transition(start_state, end_state, condition)

            start_state.add_transition(specific_transition)
            automaton_transition_set: _ty.Set = self.automaton.get_transitions(True)
            automaton_transition_set.add(specific_transition)
            self.automaton.set_transitions(automaton_transition_set)

    def _serialise_automaton_to_bridge(self) -> None:
        """Serialise the automaton to the bridge
        
        :return: None
        """
        serialised_update: _ty.Dict[str, _ty.Any] = {}

        # serialisation
        for state in self.automaton.get_states():
            if not state.is_active():
                continue

            serialised_update["state"] = {}
            serialised_update["state"]["id"] = self.automaton.get_state_index(state)
            serialised_update["state"]["is_active"] = state.is_active()

        for transition in self.automaton.get_transitions():
            if not transition.is_active():
                continue

            serialised_update["transition"] = {}
            serialised_update["transition"]["id"] = self.automaton.get_transition_index(transition)
            serialised_update["transition"]["is_active"] = transition.is_active()

        serialised_update["automaton"] = {}
        serialised_update["automaton"]["input"] = list(self.automaton.get_input())
        serialised_update["automaton"]["pointer_index"] = self.automaton.get_current_index()
        serialised_update["automaton"]["output"] = self.automaton.get_current_return_value()
        serialised_update["type"] = "SIMULATION_UPDATE"

        if "state" not in serialised_update:  # or "transition" not in serialised_update:
            # return
            serialised_update["state"] = {}
            serialised_update["state"]["id"] = 0  # assume that index 0 is the start state
            serialised_update["state"]["is_active"] = True

        # push to bridge
        self._simulation_result_callback(serialised_update)

    def _serialise_simulation_result(self, automaton_result: _result.Result) -> None:
        """Serialise the simulation result
        
        :param automaton_result: The result of the simulation
        :return: None
        """
        serialisation_update: _ty.Dict[str, _ty.Any] = {}

        if automaton_result is None:
            return

        serialisation_update["type"] = "SIMULATION_RESULT"
        serialisation_update["success"] = isinstance(automaton_result, _result.Success)
        serialisation_update["message"] = automaton_result._inner_value or "No message provided!"
        self._simulation_result_callback(serialisation_update)

    def _simulate(self) -> _result.Result:
        """Simulate the automaton
        
        :return: The result of the simulation
        """
        try:

            return_result = None
            i = 0
            while return_result is None:
                self._serialise_automaton_to_bridge()
                return_result = self.automaton.simulate_one_step()
                i += 1

            self._serialise_simulation_result(return_result)
            return return_result

        except Exception as e:
            log_message: str = (f"An error occurred whilst trying to simulate an "
                                f"{self.automaton.get_implementation_name()}: {str(e)}")

            ActLogger().error(log_message)
            traceback_message: str = traceback.format_exc()

            error: _ty.Dict[str, _ty.Any] = {}
            error["type"] = f"SIMULATION_ERROR: {str(e)}"
            error["message"] = traceback_message
            error["success"] = False
            self._error_callable(error, "ui", ["simulation"])

            # Error packet for simulation_queue
            simulation_error: _ty.Dict[str, _ty.Any] = {}
            simulation_error["type"] = "SIMULATION_RESULT"
            simulation_error["success"] = False
            simulation_error["message"] = f"An error occurred {str(e)}\n{traceback_message}"
            self._error_callable(simulation_error, "simulation")

            return _result.Failure(log_message)
