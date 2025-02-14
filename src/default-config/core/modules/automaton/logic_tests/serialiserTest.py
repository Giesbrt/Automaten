from core.modules.serializer import serialize, deserialize
from core.modules.automaton.UIAutomaton import UiAutomaton, UiState, UiTransition
from pprint import pprint

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

serialised = serialize(uiAutomaton)
pprint(serialised)

deserialized = deserialize(serialised)
print(deserialized == uiAutomaton)
