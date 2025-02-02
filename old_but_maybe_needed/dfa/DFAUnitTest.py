import unittest
import returns.result as _result

# Abstract Machine related imports
# from DFAState import DFAState
# from DFATransition import DFATransition
# from DFAAutomaton import DFAAutomaton

from core.extensions.DFA import DFATransition, DFAState, DFAAutomaton

# Standard typing imports for aps


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

        s1f1: DFATransition = DFATransition(s1, s1, ['a'])
        s1f2: DFATransition = DFATransition(s1, s2, ['b'])

        s2f1: DFATransition = DFATransition(s2, s1, ['a'])
        s2f2: DFATransition = DFATransition(s2, s2, ['b'])

        dfa.states.add(s1)
        dfa.states.add(s2)

        dfa.set_start_state(s1)
        dfa.add_state(s2, "end")

        dfa.set_input("aab")

        dfa_result: _result.Result = None
        while dfa_result is None:
            dfa_result = dfa.simulate_one_step()
        print(dfa_result._inner_value)
        self.assertEqual(type(_result.Success(None)), type(dfa_result))

    def test_check_if_single_simulation_mode_works(self):
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
        dfa.add_state(s2, "end")

        dfa.set_input("aab")

        i = 1
        simulation_return = dfa.simulate_one_step()
        while simulation_return is None:
            simulation_return = dfa.simulate_one_step()
            i += 1

        self.assertEqual(len(dfa.get_input()), i - 1)  # -1 because the last call is the end call (end of loop)


if __name__ == '__main__':
    unittest.main()
