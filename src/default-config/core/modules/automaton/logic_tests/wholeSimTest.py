import threading
from core.modules.automaton.UiBridge import UiBridge
from core.modules.automaton_loader import start
from core.modules.automaton.UIAutomaton import UiAutomaton, UiState, UiTransition
from time import sleep

if __name__ == '__main__':

    # Backend
    backend_stop_event: threading.Event = threading.Event()

    backend = start(None, None)
    backend_thread = threading.Thread(target=backend.run_infinite, args=(backend_stop_event,))
    backend_thread.start()

    states_with_design: dict = {"end": "Circle: ((180.0, 180.0), 162.0), 2##000000;",
                                "default": ""}

    uiAutomaton = UiAutomaton("dfa", "Giesbrt", states_with_design)

    # States
    stateA = UiState(None, None, "q0", "default")
    stateB = UiState(None, None, "q1", "end")
    uiAutomaton.add_state(stateA)
    uiAutomaton.add_state(stateB)

    # Transitions
    transitionAA = UiTransition(stateA, "n", stateA, "n", ["b", ])
    transitionAB = UiTransition(stateA, "n", stateB, "n", ["a", ])

    transitionBA = UiTransition(stateB, "n", stateA, "n", ["b", ])
    transitionBB = UiTransition(stateB, "n", stateB, "n", ["a", ])

    uiAutomaton.add_transition(transitionAB)
    uiAutomaton.add_transition(transitionAA)
    uiAutomaton.add_transition(transitionBA)
    uiAutomaton.add_transition(transitionBB)

    # Simulation
    uiAutomaton.simulate(["a", "b", "b", "a"])
    bridge = UiBridge()

    sleep(2)

    while bridge.has_simulation_items():
        print("Output: ", uiAutomaton.handle_simulation_updates())
        for i in uiAutomaton.get_states():
            if not i.is_active():
                continue
            print("(state) Actually active:", i.get_display_text())

        for i in uiAutomaton.get_transitions():
            if not i.is_active():
                continue
            print("(transition) Actually active:", uiAutomaton.get_transition_index(i))

    backend_stop_event.set()
    exit(0)
