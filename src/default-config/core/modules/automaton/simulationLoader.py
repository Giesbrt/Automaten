"""TBA"""
from returns import result as _result

# Abstract Machine related imports
from core.modules.automaton.automatonBridge import AutomatonBridge
from core.modules.automaton.base.automaton import Automaton as BaseAutomaton
from core.modules.automaton.automatonProvider import AutomatonProvider
from core.modules.automaton.UiBridge import UiBridge

from queue import Queue

from aplustools.io import ActLogger
from serializer import Serializer
from core.modules.storage import JSONAppStorage

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts


class SimulationLoader:

    def __init__(self, json_app_storage: JSONAppStorage):
        super().__init__()
        # App storage access
        self.app_storage: JSONAppStorage = json_app_storage
        loaded_max_restart_counter: int = self.app_storage.retrieve("simulation_loader_max_restart_counter", int)

        self.max_restart_counter: int = loaded_max_restart_counter or 5  # set default of 5 if the config could not be read

    def handle_bridge(self) -> None:  # Todo get data from bridge and handle it
        pass
