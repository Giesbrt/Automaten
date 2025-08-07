import math
from functools import partial

from core.backend.data.simulation import Simulation as _Simulation
from core.backend.abstract.automaton.itape import ITape as _Tape
from core.backend.data.transition import Transition as _Transition
from core.backend.data.automatonSettings import AutomatonSettings as _AutomatonSettings

from core.backend.packets.simulationPackets import SimulationStartPacket as _SimulationStartPacket
from time import sleep

from dancer.io import ActLogger

# Standard typing imports for aps
import abc as _abc
import typing as _ty


class IAutomaton(_abc.ABC):
    SIMULATION_PAUSED_SLEEP_SECONDS: float = 0.5

    def __init__(self, automaton_settings: _AutomatonSettings) -> None:
        super().__init__()
        self._automaton_settings: _AutomatonSettings = automaton_settings

        self._simulation_tape: _Tape | None = None

        self._start_state_id: int = -1
        self._state_types: _ty.Dict[int, str] = {}

        self._states: _ty.List[int] = []
        self._transitions: _ty.List[_Transition] = []

        self.logger: ActLogger = ActLogger()

    def ensure_simulation_setup(self) -> None:
        reasons = {
            "missing simulation tape": self.get_simulation_tape() is None,
            "invalid start state ID": self.get_start_state_id() < 0,
            "no states defined": not self._states,
            "no transitions defined": not self._transitions
        }

        errors = [msg for msg, condition in reasons.items() if condition]

        if errors:
            raise RuntimeError(
                f"Cannot simulate automaton of type '{self._automaton_settings.module_name}': " +
                ", ".join(errors)
            )

    @_abc.abstractmethod
    def _find_next_transition(self, from_state_id: int, condition: str) -> _Transition or None:
        pass

    @_abc.abstractmethod
    def _simulate(self, simulation: _Simulation) -> _ty.Generator[None, _ty.Any, None]:
        pass

    def simulate(self, simulation: _Simulation) -> None:
        self.ensure_simulation_setup()

        step_generator: _ty.Generator | None = None
        simulation.current_bulk = simulation.simulation_bulk_size * 2

        while not simulation.finished.get_value():
            SIMULATION_BULK_THRESHOLD: _ty.Callable[[], int] = lambda: simulation.current_bulk - simulation.simulation_bulk_size

            if simulation.paused.get_value():
                # is simulation index near bulk stop
                # self.logger.info("Checking Bulk Limit extension...")

                if simulation.step_index >= SIMULATION_BULK_THRESHOLD():
                    self.logger.info(
                        f"{simulation.step_index=}, {(SIMULATION_BULK_THRESHOLD())=}, {simulation.current_bulk=}")
                    self.logger.info(f"... Bulk Limit extension necessary! "
                                     f"simulating another Bulk ({simulation.simulation_bulk_size} steps) "
                                     f"Limit: {simulation.current_bulk} -> {simulation.current_bulk + simulation.simulation_bulk_size}")

                    simulation.current_bulk += simulation.simulation_bulk_size
                    simulation.paused.set_value(False)

                else:
                    # self.logger.info(f"... Bulk Limit extension not necessary! sleeping "
                    #                  f"{self.SIMULATION_PAUSED_SLEEP_SECONDS} seconds")

                    if self.SIMULATION_PAUSED_SLEEP_SECONDS > 0:
                        sleep(self.SIMULATION_PAUSED_SLEEP_SECONDS)
                    continue

            # Simulate one Step
            try:
                # TODO: maybe change to a single step simulation mode
                if not step_generator:
                    step_generator = self._simulate(simulation)
                else:
                    next(step_generator)
            except StopIteration:
                simulation.finish_simulation()
                return

                # Is a Bulk Limit extension especially needed? (Pointer already at threshold)
            if simulation.step_index >= SIMULATION_BULK_THRESHOLD():
                self.logger.info(f"Bulk Limit extended! "
                                 f"simulating another Bulk ({simulation.simulation_bulk_size} steps) "
                                 f"Limit: {simulation.current_bulk} -> {simulation.current_bulk + simulation.simulation_bulk_size} "
                                 f"Pointer index: {simulation.step_index}")

                simulation.current_bulk += simulation.simulation_bulk_size
                continue

            # Simulated steps exceed the Bulk Limit: extension necessary
            if len(simulation.simulation_steps) >= simulation.current_bulk:
                self.logger.info(f"Bulk limit reached! Currently: {len(simulation.simulation_steps)} Steps, "
                                 f"Limit: {simulation.current_bulk}")
                simulation.paused.set_value(True)

    def get_transition_by_id(self, transition_id: int) -> _Transition | None:
        for transition in self._transitions:
            if transition.transition_id != transition_id:
                continue
            return transition
        return None

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

    def get_automaton_settings(self) -> _AutomatonSettings:
        return self._automaton_settings

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
