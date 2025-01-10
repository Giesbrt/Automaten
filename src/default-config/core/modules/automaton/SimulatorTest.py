from automatonSimulator import AutomatonSimulator
from returns import result as _result

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts


def error():
    print("error")


def simulation_step_result(step):
    print("step", step)


if __name__ == '__main__':
    data = {
        "id": "giesbrt:dfa",
        "input": ["a", "b", "b", 'a'],
        "content": [
            {
                "name": "q0",  # Index 0 ist immer die Start-Status
                "type": "default",
                "transitions": [
                    {
                        "to": 1,
                        "condition": "a"  # Für TM und Mealy die Argumente mit '|' trennen
                    }
                    ,
                    {
                        "to": 0,
                        "condition": "b"
                    }
                ]
            },
            {
                "name": "q1",
                "type": "end",
                "transitions": [
                    {
                        "to": 1,
                        "condition": "a"
                    },
                    {
                        "to": 0,
                        "condition": "b"
                    }
                ]
            }
        ]
    }

    i = 0

    while i < 1:
        i += 1
        simulator = AutomatonSimulator(data, simulation_step_result, 2, error)
        result = simulator.run()
        print(result)
        if isinstance(result, _result.Failure):
            print("BREAK")
            break

    print(i)
