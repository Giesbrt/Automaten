"""TBA"""
import threading

from core.modules.storage import JSONAppStorage, MultiUserDBStorage
from .abstract import BackendInterface
from core.modules.automaton.simulationLoader import SimulationLoader

# Whatever

simple_storage: JSONAppStorage or None = None
extended_storage: MultiUserDBStorage or None = None


class _Backend(BackendInterface):
    def run_infinite(self, backend_stop_event: threading.Event) -> None:
        """
        Used to actually start the backend. The gui will launch this in a separate thread.
        """
        import time
        while not backend_stop_event.is_set():
            time.sleep(0.1)
            if 1 == 0:
                print("WE ARE HERE")  # @Adalfarus, brauchst du das?

            if False:  # Deactivated
                simulation_loader: SimulationLoader = SimulationLoader(simple_storage)  # TODO: is simple_storage None?
                simulation_loader.handle_bridge()

    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)


def start(simple_stor: JSONAppStorage, extended_stor: MultiUserDBStorage) -> BackendInterface:
    global simple_storage
    global extended_storage

    inst = _Backend()  # You can save as file attr, or do other config stuff.
    simple_storage = simple_stor
    extended_storage = extended_stor
    return inst
