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

    uiAutomaton = UiAutomaton("mealy", "Fa4953", states_with_design)

    # States
    stateA = UiState(None, None, "q0", "default")
    stateB = UiState(None, None, "q1", "default")
    uiAutomaton.add_state(stateA)
    uiAutomaton.add_state(stateB)

    # Transitions
    transitionAA = UiTransition(stateA, "n", stateA, "n", ["b", "b"])
    transitionAB = UiTransition(stateA, "n", stateB, "n", ["a", "a"])

    transitionBA = UiTransition(stateB, "n", stateA, "n", ["b", "b"])
    transitionBB = UiTransition(stateB, "n", stateB, "n", ["a", "a"])

    uiAutomaton.add_transition(transitionAA)
    uiAutomaton.add_transition(transitionAB)
    uiAutomaton.add_transition(transitionBA)
    uiAutomaton.add_transition(transitionBB)

    print([(uiAutomaton.get_transition_index(j), i, j.get_condition()) for i, j in
           enumerate(iter(uiAutomaton.get_transitions()))])

    # Simulation
    print(uiAutomaton.simulate(["a", "b", "b", "a"], None))
    print("-- SIMULATION SEND --")
    bridge = UiBridge()

    # sleep(2)
    while not uiAutomaton.is_simulation_data_available() and not uiAutomaton.has_bridge_updates():
        continue

    print([(uiAutomaton.get_transition_index(j), i, j.get_condition()) for i, j in enumerate(iter(uiAutomaton.get_transitions()))])

    print(f"-- SIMULATION DATA AVAILABLE  ({bridge.get_simulation_queue().qsize()} steps)--")

    # Check for erros
    while uiAutomaton.has_bridge_updates():
        uiAutomaton.handle_bridge_updates()

    while uiAutomaton.has_simulation_data():
        while uiAutomaton.has_bridge_updates():
            uiAutomaton.handle_bridge_updates()

        print("Output: ", uiAutomaton.handle_simulation_updates())
        for i in uiAutomaton.get_states():
            if not i.is_active():
                continue
            print("(state) Actually active:", i.get_display_text())

        for i in uiAutomaton.get_transitions():
            if not i.is_active():
                continue
            print("(transition) Actually active:", uiAutomaton.get_transition_index(i))
        print("--")

    print("-- SIMULATION FINISHED --")
    backend_stop_event.set()
    exit(0)
