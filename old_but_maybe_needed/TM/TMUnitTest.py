# Modulpfad konfigurieren
#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from old_but_maybe_needed.TM.TMAutomaton import TMAutomaton
from old_but_maybe_needed.TM.TMState import TMState
from old_but_maybe_needed.TM.TMTransition import TMTransition
from returns import result as _result

import unittest

class TestTMAutomaton(unittest.TestCase):

    def setUp(self):
        # Initialisierung der Turing-Maschine und Zustände
        self.state_q0 = TMState("q0")
        self.state_q1 = TMState("q1")
        self.state_q2 = TMState("q2")

        self.tm = TMAutomaton()
        self.tm.set_states({self.state_q0, self.state_q1, self.state_q2})
        self.tm.set_start_state(self.state_q0)
        self.tm.set_end_states({self.state_q2})

        t1 = TMTransition(self.state_q0, self.state_q1, "0|X|R")
        t3 = TMTransition(self.state_q0, self.state_q0, "1|Y|R")
        t2 = TMTransition(self.state_q1, self.state_q2, "1|Y|H")
        t4 = TMTransition(self.state_q1, self.state_q1, "0|X|H")
        self.tm.set_transitions({t1, t2, t3, t4})

        self.tm.set_input("01")
        self.tm.set_input_alphabet({"0", "1"})
        self.tm.set_output_alphabet({"X", "Y"})

    def test_simulate_acceptance(self):
        result = self.tm.simulate()
        self.assertIsInstance(result, _result.Success)
        self.assertEqual(self.tm.get_current_state(), self.state_q2)
        self.assertEqual(self.tm.get_input(), "XY")

    def test_simulate_rejection(self):
        self.tm.set_input("10")
        result = self.tm.simulate()
        self.assertIsInstance(result, _result.Failure)
        self.assertEqual(self.tm.get_current_state(), self.state_q1)
        self.assertEqual(self.tm.get_input(), "YXB")

    def test_simulate_one_step(self):
        self.tm.set_input("01")
        self.tm.simulate_one_step()
        self.assertEqual(self.tm.get_current_state(), self.state_q1)
        self.assertEqual(self.tm.get_input(), "X1")

        result = self.tm.simulate_one_step()
        self.assertIsInstance(result, _result.Success)
        self.assertEqual(self.tm.get_current_state(), self.state_q2)
        self.assertEqual(self.tm.get_input(), "XY")

if __name__ == '__main__':
    unittest.main()