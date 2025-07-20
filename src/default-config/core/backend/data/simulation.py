from dataclasses import dataclass, field
from core.backend.abstract.automaton.itape import ITape as _Tape
from core.libs.utils.staticSignal import Signal as _Signal
from core.libs.utils.threadSafeList import ThreadSafeList
from core.libs.utils.staticContainer import StaticContainer
import uuid as _uuid4

# Standard typing imports for aps
import typing as _ty


@dataclass  # Why not use a database (multiple users)?
class Simulation:
    simulation_notification_signal: _Signal
    simulation_id: _uuid4.UUID = field(default_factory=_uuid4.uuid4)
    finished: StaticContainer[bool] = field(default_factory=lambda: StaticContainer(False))
    paused: StaticContainer[bool] = field(default_factory=lambda: StaticContainer(False))
    step_index: int = field(default=0)
    # simulation_steps: _ty.List[_ty.Dict[str, _ty.Any]] = field(default_factory=list)
    simulation_steps: ThreadSafeList[_ty.Dict[str, _ty.Any]] = field(default_factory=ThreadSafeList)
    """
    'active_transitions' = ['transition_ids']
    'active_states' = ['state_ids']
    'complete_output' = Tape('current simulation tape')
    """

    def add_step(self, active_transitions: _ty.List[int],
                 active_states: _ty.List[int],
                 state_type: _ty.Dict[int, str],
                 complete_output: _Tape):
        self.simulation_steps.append({"active_transitions": active_transitions,
                                      "active_states": active_states,
                                      "state_type": state_type,
                                      "complete_output": complete_output.copy()})

        # self._notify()  # Remove for poc_one_callback.py, add for poc_step_callback.py

    def _notify(self) -> None:
        if self.simulation_notification_signal is not None:
            self.simulation_notification_signal.emit(self)  # self

    def copy(self, keep_uuid: bool = False) -> "Simulation":
        copied = Simulation(
            simulation_notification_signal=self.simulation_notification_signal.copy(),
            simulation_id=_uuid4.uuid4() if not keep_uuid else self.simulation_id,  # neue ID bei Kopie
            finished=self.finished,
            paused=self.paused,
            simulation_steps=ThreadSafeList([step.copy() for step in self.simulation_steps])
        )
        return copied



