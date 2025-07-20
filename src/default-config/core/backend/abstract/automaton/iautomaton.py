from core.backend.data.simulation import Simulation as _Simulation
from core.backend.abstract.automaton.itape import ITape as _Tape
from core.backend.data.transition import Transition as _Transition

from core.backend.packets.simulationPackets import SimulationStartPacket as _SimulationStartPacket

# Standard typing imports for aps
import abc as _abc
import typing as _ty

DATA: _ty.Dict[str, float | _ty.List[str]] = {"VERSION": 1.0,
                                              "REQUIRED_PARAMETER_TYPES": []}


class IAutomaton(_abc.ABC):
    def __init__(self):
        super().__init__()

        self._simulation_tape: _Tape or None = None

        self._start_state_id: int = -1
        self._state_types: _ty.Dict[int, str] = {}

        self._states: _ty.List[int] = []
        self._transitions: _ty.List[_Transition] = []

    def can_simulate(self) -> bool:
        return (self.get_simulation_tape() is not None and
                self.get_start_state_id() >= 0 and
                self._states and self._transitions)

    @_abc.abstractmethod
    def simulate(self, simulation: _Simulation) -> None:
        pass

    @_abc.abstractmethod
    def _find_next_transition(self, from_state_id: int, condition: str) -> _Transition or None:
        pass

    def get_transition_by_id(self, transition_id: int) -> _Transition:
        for transition in self._transitions:
            if transition.transition_id != transition_id:
                continue
            return transition

    def get_simulation_tape(self) -> _Tape or None:
        return self._simulation_tape

    def set_simulation_tape(self, value: _Tape or None) -> None:
        self._simulation_tape = value

    def get_start_state_id(self) -> int:
        return self._start_state_id

    def set_start_state_id(self, value: int) -> None:
        self._start_state_id = value

    def get_state_types(self) -> _ty.Dict[int, str]:
        return self._state_types

    def get_state_type(self, state_id: int) -> str:
        return self._state_types[state_id]

    def set_state_types(self, value: _ty.Dict[int, str]) -> None:
        self._state_types = value

    def set_state_type(self, state_id: int, value: str) -> None:
        self._state_types[state_id] = value

    def get_states(self) -> _ty.List[int]:
        return self._states

    def set_states(self, value: _ty.List[int]) -> None:
        for state in value:
            self.add_state(state, "default")

    def add_state(self, state_id: int, state_type: str = "default") -> None:
        if self.get_start_state_id() <= 0:
            self.set_start_state_id(state_id)

        self._states.append(state_id)
        self._state_types[state_id] = state_type

    def get_transitions(self) -> _ty.List[_Transition]:
        return self._transitions

    def set_transitions(self, value: _ty.List[_Transition]) -> None:
        self._transitions = value

    def add_transition(self, transition: _Transition) -> None:
        self._transitions.append(transition)

    def _from_packet(self, packet: _SimulationStartPacket) -> None:
        self._states.clear()
        self._transitions.clear()
        self._state_types.clear()

        for state_id, state_type in packet.get_state_ids():
            self.add_state(state_id, state_type)

        self.set_start_state_id(packet.get_start_state_id())

        for transition_data in packet.get_transition_ids_with_data():
            self.add_transition(transition_data)

        simulation_input: _Tape = packet.get_input_tape()
        simulation_input.move_to_beginning()
        self.set_simulation_tape(simulation_input)
