from core.backend.loader.automatonProvider import AutomatonProvider as _AutomatonProvider
from core.backend.abstract.automaton.itape import ITape as _ITape
from core.backend.data.automatonSettings import AutomatonSettings as _AutomatonSettings
from core.backend.abstract.automaton.iautomaton import IAutomaton as _IAutomaton
from core.backend.data.simulation import Simulation as _Simulation
from core.backend.data.transition import Transition as _Transition

from core.backend.abstract.ipacket import IPacket as _IPacket
from core.backend.packets.simulationPackets import SimulationStartPacket as _SimulationStartPacket
from core.backend.packets.packetManager import PacketManager as _PacketManager

from dancer.io import ActLogger

# Standard typing imports for aps
import typing as _ty
import types as _ts


class UIAutomaton:
    def __init__(self, automaton_type: str) -> None:
        super().__init__()
        self._logger: ActLogger = ActLogger()

        self._automaton_type: str = automaton_type
        self._automaton_provider: _AutomatonProvider = _AutomatonProvider()

        automaton_classes: _ty.Dict[_ty.Type[
            _IAutomaton | _AutomatonSettings], _IAutomaton | _AutomatonSettings] | None = self._automaton_provider.get_automaton(
            self._automaton_type)
        if automaton_classes is None:
            raise ModuleNotFoundError(f"Could not find automaton of type {self._automaton_type}")

        # Settings
        self._automaton_settings: _AutomatonSettings = automaton_classes[_AutomatonSettings]
        self._token_lists: _ty.List[_ty.Tuple[_ty.List[str], bool]] = self._automaton_settings.token_lists
        self._transition_description_layout: _ty.List[int] = self._automaton_settings.transition_description_layout
        self._state_types: _ty.List[str] = self._automaton_settings.state_types

        # States & Transitions
        self._states: _ty.Dict[int, str] = {}
        self._start_state_id: int = -1

        self._transitions: _ty.List[_Transition] = []

    # State
    def add_state(self, state_id: int, state_type: str) -> None:
        self.modify_state(state_id, state_type)

    def remove_state(self, state_id: int) -> None:
        if state_id not in self._states:
            return
        del self._states[state_id]

    def modify_state(self, state_id: int, state_type: str) -> None:
        if state_type not in self._state_types:
            return
        self._states[state_id] = state_type

    @property
    def start_state_id(self) -> int:
        return self._start_state_id

    @start_state_id.setter
    def start_state_id(self, value: int) -> None:
        self._start_state_id = value

    # Transition
    def add_transition(self, transition: _Transition) -> None:
        # prevent transitions with the same id
        transitions = list(filter(lambda t: t.transition_id == transition.transition_id, self._transitions))
        if transitions:
            return
        self._transitions.append(transition)

    def get_transition(self, transition_id: int) -> _Transition:
        for transition in self._transitions:
            if transition.transition_id != transition_id:
                continue
            return transition

    def remove_transition(self, transition_id: int) -> None:
        for transition in self._transitions:
            if transition.transition_id != transition_id:
                continue
            self._transitions.remove(transition)
            return

    # General
    def simulate(self, input_tape: _ITape) -> None:
        state_ids: _ty.List[_ty.Tuple[int, str]] = [(state_id, self._states[state_id]) for state_id in self._states]

        error: str = f"Can send a simulation packet: "
        if not state_ids:
            self._logger.info(error + "No states present")
            return

        if not self._transitions:
            self._logger.info(error + "No transitions present")
            return

        if self.start_state_id < 0:
            self._logger.info(error + "No start state set")
            return

        if not input_tape:
            self._logger.info(error + "input_tape can not be None or empty")
            return

        start_packet: _IPacket = _SimulationStartPacket(state_ids,
                                                        self.start_state_id,
                                                        self._transitions,
                                                        input_tape,
                                                        self._automaton_type,
                                                        self._handle_simulation)

        packet_manager: _PacketManager = _PacketManager()
        packet_manager.send_backend_packet(start_packet)

    def _handle_simulation(self, simulation: _Simulation) -> None:
        print("handle")

        # TODO TEMP CODE

        print("Replay...")
        for i, step in enumerate(simulation.simulation_steps):
            output = step["complete_output"]
            state_id = step["active_states"]

            print(i + 1, [output.get_tape()[k] for k in output.get_tape().keys()], f"State: {state_id[0] + 1}")
            print(i + 1, f"  {' ' * 5 * output.get_pointer()}^")

        if simulation.finished.get_value():
            print(f"Simulation finished: {simulation.simulation_end_cause.get_value()}")
