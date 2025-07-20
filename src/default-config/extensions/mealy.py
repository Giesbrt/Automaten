from core.backend.abstract.automaton import iautomaton, isettings
from core.backend.data.simulation import Simulation as _Simulation
from core.backend.data.transition import Transition as _Transition


class Settings(isettings.IAutomatonSettings):
    pass

    def __init__(self):
        super().__init__("mealy",
                         "Mealy-Machine",
                         "Scotch",
                         [([], True)],
                         [0, 0],
                         None,
                         ["default"])


class Mealy(iautomaton.IAutomaton):

    def _find_next_transition(self, from_state_id: int, condition: str) -> _Transition | None:
        suitable_transitions = list(filter(lambda tr: tr.from_state_id == from_state_id and
                                                      tr.condition[0] == condition, self.get_transitions()))
        if not suitable_transitions:
            return None

        if len(suitable_transitions) > 1:
            print(suitable_transitions)
            raise ValueError("A TM is deterministic and therefore can not have multiple identical transitions!")

        found_transition: _Transition = suitable_transitions[0]
        return found_transition

    def simulate(self, simulation: _Simulation) -> None:
        if not self.can_simulate():
            print("can not simulate")
            return

        current_state_id: int = self.get_start_state_id()
        simulation.add_step([],
                            [current_state_id],
                            {current_state_id: self.get_state_type(current_state_id)},
                            self.get_simulation_tape())

        while not self.get_simulation_tape().is_at_end() and not simulation.finished.get_value():
            input_char: str = self.get_simulation_tape().read()
            next_transition: _Transition = self._find_next_transition(current_state_id, input_char)

            if not next_transition:
                print("no next transition found")
                break
            current_state_id = next_transition.to_state_id

            self.get_simulation_tape().write(next_transition.condition[1])
            self.get_simulation_tape().right()
            simulation.add_step([next_transition.transition_id],
                                [current_state_id],
                                {current_state_id: self.get_state_type(current_state_id)},
                                self.get_simulation_tape())

        # Simulation finished
        simulation.finished.set_value(True)

    def __repr__(self):
        return f"MEALY({self._states=}, {self._transitions=})"


if __name__ == '__main__':
    from core.backend.default.defaultTape import DefaultTape
    from pprint import pprint

    mealy = Mealy()
    simulation = _Simulation(None)

    mealy.set_states([0, 1, 2])
    mealy.set_start_state_id(0)

    t00 = _Transition(0, 0, 0, ["0", "1"])

    t01 = _Transition(1, 0, 1, ["1", "1"])
    t10 = _Transition(2, 1, 0, ["1", "0"])

    t12 = _Transition(3, 1, 2, ["0", "0"])
    t22 = _Transition(4, 2, 2, ["1", "0"])

    t20 = _Transition(5, 2, 0, ["0", "1"])

    mealy.set_transitions([t00, t01, t10, t12, t22, t20])

    mealy.set_simulation_tape(DefaultTape(list("01")))

    mealy.simulate(simulation)

    pprint(simulation)

    print("Replay...")
    for i, step in enumerate(simulation.simulation_steps):
        output: DefaultTape = step["complete_output"]
        state_id = step["active_states"]

        print(i + 1, [output.get_tape()[k] for k in output.get_tape().keys()], f"State: {state_id[0] + 1}")
        print(i + 1, f"  {' ' * 5 * output.get_pointer()}^")


