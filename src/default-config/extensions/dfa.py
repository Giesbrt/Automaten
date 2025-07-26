from pprint import pprint

from core.backend.abstract.automaton import iautomaton
from core.backend.data import transition
from core.backend.data.automatonSettings import AutomatonSettings as _AutomatonSettings
from core.backend.data.simulation import Simulation
from core.backend.default.defaultTape import DefaultTape


class DFA(iautomaton.IAutomaton):

    def __init__(self) -> None:
        super().__init__(_AutomatonSettings("DFA",
                                            "Deterministic Finite Automaton",
                                            "Scotch",
                                            [([], True)],
                                            [0]))

    def _find_next_transition(self, from_state_id: int, condition: str) -> transition.Transition | None:
        suitable_transitions = list(filter(lambda tr: tr.from_state_id == from_state_id and
                                                      tr.condition[0] == condition, self.get_transitions()))
        if not suitable_transitions:
            return None

        if len(suitable_transitions) > 1:
            print(suitable_transitions)
            raise ValueError("A DFA is deterministic and therefore can not have multiple identical transitions!")

        found_transition: transition.Transition = suitable_transitions[0]
        return found_transition

    def simulate(self, simulation: Simulation) -> None:
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
            next_transition: transition.Transition = self._find_next_transition(current_state_id, input_char)

            if not next_transition:
                print("no next transition found")
                simulation.finish_simulation(False, "No next Transition found!")
                return

            current_state_id = next_transition.to_state_id

            self.get_simulation_tape().right()
            simulation.add_step([next_transition.transition_id],
                                [current_state_id],
                                {current_state_id: self.get_state_type(current_state_id)},
                                self.get_simulation_tape())

        # Simulation finished
        simulation.finish_simulation()

    def __repr__(self):
        return f"DFA({self._states=}, {self._transitions=})"


if __name__ == '__main__':
    dfa = DFA()
    simulation = Simulation(None)

    dfa.set_states([0, 1])
    dfa.set_start_state_id(0)

    dfa.set_state_type(1, "end")

    t00 = transition.Transition(0, 0, 0, ["a"])
    t01 = transition.Transition(1, 0, 1, ["b"])

    t10 = transition.Transition(2, 1, 0, ["a"])
    t11 = transition.Transition(3, 1, 1, ["b"])
    dfa.set_transitions([t00, t01, t10, t11])

    dfa.set_simulation_tape(DefaultTape(["b", "a", "b", "b"]))

    dfa.simulate(simulation)

    pprint(simulation)

    print("Replay...")
    for i, step in enumerate(simulation.simulation_steps):
        output: DefaultTape = step["complete_output"]
        state_id = step["active_states"]

        print(i + 1, [output.get_tape()[k] for k in output.get_tape().keys()], f"State: {state_id[0] + 1}")
        print(i + 1, f"  {' ' * 5 * output.get_pointer()}^")
