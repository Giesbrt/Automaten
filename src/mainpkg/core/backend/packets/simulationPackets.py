from core.backend.abstract.ipacket import IPacket as _IPacket
from core.backend.abstract.automaton.itape import ITape as _ITape
from core.backend.data.simulation import Simulation as _Simulation
from core.backend.data.transition import Transition as _Transition


import uuid as _uuid4

# Standard typing imports for aps
import typing as _ty


class SimulationStartPacket(_IPacket):

    def __init__(self, state_ids: _ty.List[_ty.Tuple[int, str]],
                 start_state_id: int,
                 transition_ids_with_data: _ty.List[_Transition],
                 input_tape: _ITape,
                 automaton_type: str,
                 notification_callback: _ty.Callable,
                 simulation_bulk_size: int = 100):
        super().__init__()

        self._state_ids: _ty.List[_ty.Tuple[int, str]] = state_ids
        self._start_state_id: int = start_state_id
        self._transition_ids_with_data: _ty.List[_Transition] = transition_ids_with_data
        self._input_tape: _ITape = input_tape
        self._automaton_type: str = automaton_type

        self._notification_callback: _ty.Callable = notification_callback
        self._simulation_bulk_size: int = simulation_bulk_size

    def get_state_ids(self) -> _ty.List[_ty.Tuple[int, str]]:
        return self._state_ids

    def set_state_ids(self, state_ids: _ty.List[_ty.Tuple[int, str]]) -> None:
        self._state_ids = state_ids

    def get_start_state_id(self) -> int:
        return self._start_state_id

    def set_start_state_id(self, start_state_id: int) -> None:
        self._start_state_id = start_state_id

    def get_transition_ids_with_data(self) -> _ty.List[_Transition]:
        return self._transition_ids_with_data

    def set_transition_ids_with_data(self, transition_ids_with_data: _ty.List[_Transition]) -> None:
        self._transition_ids_with_data = transition_ids_with_data

    def get_input_tape(self) -> _ITape:
        return self._input_tape

    def set_input_tape(self, input_tape: _ITape) -> None:
        self._input_tape = input_tape

    def get_automaton_type(self) -> str:
        return self._automaton_type

    def set_automaton_type(self, automaton_type: str) -> None:
        self._automaton_type = automaton_type

    def get_notification_callback(self) -> _ty.Callable:
        return self._notification_callback

    def set_notification_callback(self, callback: _ty.Callable) -> None:
        self._notification_callback = callback

    def get_simulation_bulk_size(self) -> int:
        return self._simulation_bulk_size

    def set_simulation_bulk_size(self, bulk: int) -> None:
        self._simulation_bulk_size = bulk


# DEPRECATED
class SimulationDataPacket(_IPacket):  # Currently unused (removed in future update?)

    def __init__(self, regarding_packet: _uuid4, simulation: _Simulation):
        super().__init__()

        self._regarding_packet: _uuid4 = regarding_packet
        self._simulation: _Simulation = simulation

    def get_regarding_packet(self) -> _uuid4:
        return self._regarding_packet

    def set_regarding_packet(self, regarding_packet: _uuid4) -> None:
        self._regarding_packet = regarding_packet

    def get_simulation(self) -> _Simulation:
        return self._simulation

    def set_simulation(self, simulation: _Simulation) -> None:
        self._simulation = simulation

    def __repr__(self):
        return f"SimulationDataPacket({self._regarding_packet=}, {self._simulation=})"
