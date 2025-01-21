import threading
from core.modules.automaton.UiBridge import UiBridge
from core.modules.automaton_loader import start
from time import sleep


backend_stop_event: threading.Event = threading.Event()

backend = start(None, None)
backend_thread = threading.Thread(target=backend.run_infinite, args=(backend_stop_event,))
backend_thread.start()

data = {
    "action": "SIMULATION",
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

print("Push")
bridge: UiBridge = UiBridge()
bridge.add_backend_item(data)

print("Sleep 2")
sleep(2)
print("Continue")

while True:
    if not bridge.has_simulation_items():
        backend_stop_event.set()
        print("-- END --")
        exit(0)

    print(bridge.get_simulation_task(), "data")
    bridge.complete_simulation_task()
