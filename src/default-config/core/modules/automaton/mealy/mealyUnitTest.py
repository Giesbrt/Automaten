import sys
import os

from mealyAutomaton import MealyAutomaton
from mealyState import MealyState
from mealyTransition import MealyTransition
from returns import result as _result

import unittest

class TestMealyAutomaton(unittest.TestCase):

    def setUp(self):
        # Initialisierung der Mealy-Maschine und Zustände
        self.state_q0 = MealyState("q0")
        self.state_q1 = MealyState("q1")

        self.M = MealyAutomaton()
        self.M.set_states({self.state_q0, self.state_q1})
        self.M.set_start_state(self.state_q0)

        t1 = MealyTransition(self.state_q0, self.state_q0, "Apfel", "Obst")
        t2 = MealyTransition(self.state_q0, self.state_q1, "Paprika", "Gemüse")
        t3 = MealyTransition(self.state_q1, self.state_q1, "Paprika", "Gemüse")
        t4 = MealyTransition(self.state_q1, self.state_q0, "Apfel", "Obst")
        self.M.set_transitions({t1, t2})

        self.M.set_input(["Paprika", "Apfel"])
        self.M.set_input_alphabet({"Apfel", "Paprika"})
        self.M.set_output_alphabet({"Obst", "Gemüse"})

    def test_simulate(self):
        result = self.M.simulate()
        self.assertIsInstance(result, _result.Success)
        self.assertEqual(self.M.get_current_state(), self.state_q0)
        self.assertEqual(self.M.get_output(), "Obst")

    def test_simulate_one_step(self):
        result = self.M.simulate_one_step()
        self.assertIsInstance(result, _result.Success)
        self.assertEqual(self.M.get_current_state(), self.state_q1)
        self.assertEqual(self.M.get_output(), "Gemüse")
        result = self.M.simulate_one_step()
        self.assertIsInstance(result, _result.Success)
        self.assertEqual(self.M.get_current_state(), self.state_q0)
        self.assertEqual(self.M.get_output(), "Obst")

if __name__ == '__main__':
    unittest.main()