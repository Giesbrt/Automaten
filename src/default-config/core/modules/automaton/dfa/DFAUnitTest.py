import unittest
import returns.result as _result

# Abstract Machine related imports
from DFAState import DFAState
from DFATransition import DFATransition
from DFAAutomaton import DFAAutomaton

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts


class DFAUnitTest(unittest.TestCase):

    def test_if_transition_is_added_to_state(self):
        s1: DFAState = DFAState("q0")
        s1f1: DFATransition = DFATransition(s1, s1, 'a')
        s1f2: DFATransition = DFATransition(s1, s1, 'b')

        self.assertEqual(len(s1.get_transitions()), 2)

    def test_check_if_the_implementation_of_the_DFA_works_as_expected(self):
        dfa: DFAAutomaton = DFAAutomaton()

        s1: DFAState = DFAState("q0")
        s2: DFAState = DFAState("q1")

        s1f1: DFATransition = DFATransition(s1, s1, 'a')
        s1f2: DFATransition = DFATransition(s1, s2, 'b')

        s2f1: DFATransition = DFATransition(s2, s1, 'a')
        s2f2: DFATransition = DFATransition(s2, s2, 'b')

        dfa.states.add(s1)
        dfa.states.add(s2)

        dfa.set_start_state(s1)
        dfa.set_end_states({s2})

        dfa.set_word("aab")

        dfa_result: _result.Result = dfa.simulate()
        print(dfa_result._inner_value)
        self.assertEqual(type(_result.Success(None)), type(dfa_result))


if __name__ == '__main__':
    unittest.main()
