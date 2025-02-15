from core.modules.serializer import serialize, deserialize
from core.modules.automaton.UIAutomaton import UiAutomaton, UiState, UiTransition
from PySide6.QtGui import QColor
from pprint import pprint

states_with_design: dict = {"end": "Circle: ((180.0, 180.0), 162.0), 2##000000;",
                                "default": ""}

tokens: list[str] = ["a", "b"]
changeable_token_list: list[bool] = [True]
transition_pattern: list[int] = [0]

uiAutomaton = UiAutomaton("dfa", "Giesbrt", states_with_design)
# States
stateA = UiState(QColor(255, 0, 0), (0.0, 0.0), "q0", "default")
stateB = UiState(QColor(0, 255, 0), (0.0, 0.0), "q1", "end")

uiAutomaton.add_state(stateA)
uiAutomaton.add_state(stateB)
# Transitions
transitionAA = UiTransition(stateA, "n", stateA, "n", [tokens[1], ])
transitionAB = UiTransition(stateA, "n", stateB, "n", [tokens[0], ])
transitionBA = UiTransition(stateB, "n", stateA, "n", [tokens[1], ])
transitionBB = UiTransition(stateB, "n", stateB, "n", [tokens[0], ])

uiAutomaton.add_transition(transitionAB)
uiAutomaton.add_transition(transitionAA)
uiAutomaton.add_transition(transitionBA)
uiAutomaton.add_transition(transitionBB)

uiAutomaton.set_token_lists([tokens])
uiAutomaton.set_is_changeable_token_list(changeable_token_list)
uiAutomaton.set_transition_pattern(transition_pattern)

serialised = serialize(uiAutomaton)
pprint(serialised)

deserialized = deserialize(serialised)
print(deserialized == uiAutomaton)
