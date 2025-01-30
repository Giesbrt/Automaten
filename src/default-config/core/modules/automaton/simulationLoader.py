"""TBA"""
from returns import result as _result

# Abstract Machine related imports
from core.modules.automaton.automatonSimulator import AutomatonSimulator
from core.modules.automaton.UiBridge import UiBridge

from queue import Queue

from aplustools.io import ActLogger
from core.modules.storage import JSONAppStorage

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts

# Docs generated with Github Copilot


class SimulationLoader:

    def __init__(self, json_app_storage: JSONAppStorage):
        super().__init__()
        # App storage access
        self._app_storage: JSONAppStorage = json_app_storage

        self._bridge: UiBridge = UiBridge()

    def _push_simulation_to_bridge(self, item: _ty.Dict[str, _ty.Any]) -> None:
        """Push a simulation item to the bridge
        
        :param item: The item to push
        :return: None
        """
        ActLogger().info("Pushed simulation packet to bridge.")
        self._bridge.add_simulation_item(item)

    def _push_error_to_bridge(self, error: _ty.Dict[str, _ty.Any]) -> None:
        """Push an error to the bridge
        
        :param error: The error to push
        :return: None
        """
        # Todo
        ActLogger().error("Received an Error from automaton simulation, can not push to bridge due to it being not implemented. Error: " + str(error))

    def handle_bridge(self) -> None:
        """Handle the bridge requests
        
        :return: None
        """
        if not self._bridge.has_backend_items():
            return

        bridge_data: _ty.Dict[str, _ty.Any] = self._bridge.get_backend_task()

        try:
            match (str(bridge_data["action"]).lower()):
                case "simulation":

                    automaton_simulator: AutomatonSimulator = AutomatonSimulator(simulation_request=bridge_data,
                                                                                 simulation_result_callback=self._push_simulation_to_bridge,
                                                                                 error_callable=self._push_error_to_bridge)
                    result: _result.Result = automaton_simulator.run()
                    ActLogger().info(f"Finished automaton simulation, result: " + (result._inner_value or "Could not cache the simulation result."))

        except Exception as e:
            error_packet: _ty.Dict[str, _ty.Any] = {}
            ActLogger().error(f"An error occurred whilst handling bridge requests")

            error_packet["type"] = "ERROR"
            error_packet["message"] = str(e)
            self._push_error_to_bridge(error_packet)

        self._bridge.complete_backend_task()


