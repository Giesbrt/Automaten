from core.backend.abstract.automaton import iautomaton
from core.backend.data import transition
from core.backend.data.simulation import Simulation
from core.backend.default.defaultTape import DefaultTape
from time import perf_counter
from core.backend.data.automatonSettings import AutomatonSettings as _AutomatonSettings

from pprint import pprint


class TM(iautomaton.IAutomaton):

    def __init__(self) -> None:
        super().__init__(_AutomatonSettings("TM",
                                            "Turing Machine",
                                            "Scotch",
                                            [([], True), (["L", "R", "H"], False)],
                                            [0, 0, 1]))

    def _find_next_transition(self, from_state_id: int, condition: str) -> transition.Transition | None:
        suitable_transitions = list(filter(lambda tr: tr.from_state_id == from_state_id and
                                                      tr.condition[0] == condition, self.get_transitions()))
        if not suitable_transitions:
            return None

        if len(suitable_transitions) > 1:
            print(suitable_transitions)
            raise ValueError("A TM is deterministic and therefore can not have multiple identical transitions!")

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

        while not simulation.finished.get_value() and (
                list(filter(
                    lambda tr:
                    # There have to be transitions from this state...
                    tr.from_state_id == current_state_id and

                    # ...and the transitions should not point to this state and not move the pointer
                    not (tr.from_state_id == current_state_id and
                         tr.to_state_id == current_state_id and
                         str(tr.condition[2].lower()) == "h"),
                    self.get_transitions()))
        ):

            input_char: str = self.get_simulation_tape().read()
            next_transition: transition.Transition = self._find_next_transition(current_state_id, input_char)

            if not next_transition:
                print("no next transition found")
                break
            current_state_id = next_transition.to_state_id
            self.get_simulation_tape().write(next_transition.condition[1])

            # movement
            match next_transition.condition[2].lower():
                case "r":
                    self.get_simulation_tape().right()
                case "l":
                    self.get_simulation_tape().left()
                case "h":
                    self.get_simulation_tape().hold()
                case _:
                    print("unknown movement")

            simulation.add_step([next_transition.transition_id],
                                [current_state_id],
                                {current_state_id: self.get_state_type(current_state_id)},
                                self.get_simulation_tape())

        # Simulation finished
        simulation.finished.set_value(True)


if __name__ == '__main__':
    # Turingmaschine und Simulation vorbereiten
    tm = TM()
    simulation = Simulation(None)

    # Zustände
    tm.set_states([0, 1, 2, 3, 4, 5])
    tm.set_start_state_id(0)
    tm.set_state_type(5, "end")

    t00 = transition.Transition(0, 0, 5, ["0", "0", "H"])
    t01 = transition.Transition(1, 0, 1, ["1", "0", "R"])
    t02 = transition.Transition(2, 1, 1, ["1", "1", "R"])
    t03 = transition.Transition(3, 1, 2, ["0", "0", "R"])
    t04 = transition.Transition(4, 2, 2, ["1", "1", "R"])
    t05 = transition.Transition(5, 2, 3, ["0", "1", "L"])
    t06 = transition.Transition(6, 3, 3, ["1", "1", "L"])
    t07 = transition.Transition(7, 3, 4, ["0", "0", "L"])
    t08 = transition.Transition(8, 4, 4, ["1", "1", "L"])
    t09 = transition.Transition(9, 4, 0, ["0", "1", "R"])
    tm.set_transitions([t00, t01, t02, t03, t04, t05, t06, t07, t08, t09])

    # Eingabeband: ["1", "1", "1"]
    tm.set_simulation_tape(DefaultTape(["1", "1", "0", "0", "0"], can_exceed_length=True))

    # Simulation starten
    start = perf_counter()
    tm.simulate(simulation)
    end = perf_counter()

    print(f"simulated in {end - start}ms")

    # Ergebnis anzeigen
    pprint(simulation)

    print("Replay...")
    for i, step in enumerate(simulation.simulation_steps):
        output: DefaultTape = step["complete_output"]
        state_id = step["active_states"]

        print(i + 1, [output.get_tape()[k] for k in output.get_tape().keys()], f"State: {state_id[0] + 1}")
        print(i + 1, f"  {' ' * 5 * output.get_pointer()}^")
