from core.modules.automaton.automatonSimulator import AutomatonSimulator
from returns import result as _result

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts


def error(*args, **kwargs):
    print("error", args, kwargs)


def simulation_step_result(step):
    print("step", step)


if __name__ == '__main__':
    data = {
        "id": "giesbrt:dfa",
        "input": ["a", "b", "b", 'a'],
        "content": [
            {
                "name": "XYZ",  # Index 0 ist immer die Start-Status
                "type": "default",
                "transitions": [
                    {
                        "to": 1,
                        "condition": "a",  # Für TM und Mealy die Argumente mit '|' trennen
                        "id": 0
                    }
                    ,
                    {
                        "to": 0,
                        "condition": "b",
                        "id": 1
                    }
                ]
            },
            {
                "name": "AAA",
                "type": "end",
                "transitions": [
                    {
                        "to": 1,
                        "condition": "a",
                        "id": 2
                    },
                    {
                        "to": 0,
                        "condition": "b",
                        "id": 3
                    }
                ]
            }
        ]
    }

    # data = {
    #     "id": "custom:dfa",
    #     "input": list(str(input("input >> ")).split(",")),
    #     "content": [
    #         {
    #             "name": "XYZ",  # Start-Zustand
    #             "type": "default",
    #             "transitions": [
    #                 {
    #                     "to": 1,
    #                     "condition": "a",
    #                     "id": 0
    #                 },
    #                 {
    #                     "to": 2,
    #                     "condition": "b",
    #                     "id": 1
    #                 }
    #             ]
    #         },
    #         {
    #             "name": "q1",
    #             "type": "default",
    #             "transitions": [
    #                 {
    #                     "to": 2,
    #                     "condition": "a",
    #                     "id": 2
    #                 },
    #                 {
    #                     "to": 0,
    #                     "condition": "b",
    #                     "id": 3
    #                 }
    #             ]
    #         },
    #         {
    #             "name": "End",
    #             "type": "end",  # End-Zustand
    #             "transitions": [
    #                 {
    #                     "to": 0,
    #                     "condition": "a",
    #                     "id": 4
    #                 },
    #                 {
    #                     "to": 1,
    #                     "condition": "b",
    #                     "id": 5
    #                 }
    #             ]
    #         }
    #     ]
    # }

    i = 0

    while i < 1:
        i += 1
        simulator = AutomatonSimulator(data, simulation_step_result, error)
        result = simulator.run()
        state_list = [i.get_name() for i in simulator.automaton.get_states()]
        print(result)
        if isinstance(result, _result.Failure) or state_list != ['XYZ', 'AAA']:
            print("BREAK", state_list)
            break

    print(i)
