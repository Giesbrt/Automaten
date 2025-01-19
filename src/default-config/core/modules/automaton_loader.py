"""TBA"""
import threading
import time

from core.modules.storage import JSONAppStorage, MultiUserDBStorage
from .abstract import IBackend
from core.modules.automaton.simulationLoader import SimulationLoader
from .automaton.UiBridge import UiBridge

# Whatever

simple_storage: JSONAppStorage or None = None
extended_storage: MultiUserDBStorage or None = None
uibridge: UiBridge or None = None


class _Backend(IBackend):
    def run_infinite(self, backend_stop_event: threading.Event) -> None:
        """
        Used to actually start the backend. The gui will launch this in a separate thread.
        """
        while not backend_stop_event.is_set():
            time.sleep(0.1)
            simulation_loader: SimulationLoader = SimulationLoader(simple_storage, uibridge)  # TODO: is simple_storage None?
            simulation_loader.handle_bridge() # TODO: Try to yield so we can check if the thread should terminate
            print("Backend Tick")

    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)


def start(simple_stor: JSONAppStorage, extended_stor: MultiUserDBStorage, bridge: UiBridge) -> IBackend:
    global simple_storage
    global extended_storage
    global uibridge

    inst = _Backend()  # You can save as file attr, or do other config stuff.
    simple_storage = simple_stor
    extended_storage = extended_stor
    uibridge = bridge
    return inst
