"""TBA"""
# Std Lib imports
import threading
import time

# Third party imports

# Internal imports
from abstractions import IBackend, IAppSettings
from automaton.simulationLoader import SimulationLoader

# Standard typing imports for aps
import typing as _ty

settings: IAppSettings


class _Backend(IBackend):
    def __init__(self) -> None:
        ...

    def run_infinite(self, backend_stop_event: threading.Event) -> None:
        """
        Used to actually start the backend. The gui will launch this in a separate thread.
        """
        if settings is None:
            raise RuntimeError("Backend start function has not been called yet")
        simulation_loader: SimulationLoader = SimulationLoader(settings)
        while not backend_stop_event.is_set():
            time.sleep(0.1)
            simulation_loader.handle_bridge()

    def __new__(cls, *args, **kwargs) -> _ty.Self:
        return object.__new__(cls)


def start_backend(app_settings: IAppSettings) -> IBackend:
    """TBA"""
    global settings

    inst = _Backend()  # You can save as file attr, or do other config stuff.
    settings = app_settings
    return inst
