from core.backend.abstract.ipacket import IPacket as _IPacket
from core.backend.abstract.automaton.iautomaton import IAutomaton as _IAutomaton
from core.backend.data.simulation import Simulation as _Simulation
from core.backend.packets import simulationPackets as _packets
from core.backend.packets.packetManager import PacketManager as _PacketManager
from core.libs.utils.staticSignal import Signal as _Signal
from core.backend.loader.automatonProvider import AutomatonProvider as _AutomatonProvider

from time import perf_counter
# from aplustools.io import ActLogger
from dancer.io import ActLogger

# Standard typing imports for aps
import typing as _ty
import types as _ts


class BackendHandler:
    def __init__(self, backend) -> None:
        self._backend = backend
        self._packet_manager: _PacketManager = _PacketManager()

        self._logger: ActLogger = ActLogger()

    def handle_packet(self, packet: _IPacket) -> None:
        match type(packet):
            case _packets.SimulationStartPacket:
                # Build automaton and simulate given input
                packet: _packets.SimulationStartPacket = packet

                simulation_signal: _Signal = _Signal(packet.get_notification_callback())
                simulation: _Simulation = _Simulation(simulation_signal)

                data_packet: _packets.SimulationDataPacket = _packets.SimulationDataPacket(packet.get_packet_id(),
                                                                                           simulation.copy())
                self._packet_manager.send_frontend_packet(data_packet)
                simulation._notify()  # add for poc_one_callback.py, remove for poc_step_callback.py

                automaton_provider: _AutomatonProvider = _AutomatonProvider()
                automaton_type: str = packet.get_automaton_type().lower()
                automaton_impls: _ty.Dict[_ts.ModuleType, _ts.ModuleType] | None = automaton_provider.get_automaton(automaton_type)

                if automaton_impls is None:
                    error: str = f"ERROR: could not fetch automaton implementation for automaton {automaton_type}"
                    self._logger.error(error)
                    raise ValueError(error)

                automaton_impl: type[_IAutomaton] = automaton_impls[_IAutomaton]

                automaton: _IAutomaton = automaton_impl()
                automaton._from_packet(packet)

                start = perf_counter()
                automaton.simulate(simulation)
                end = perf_counter()

                self._logger.info(f"Simulated {automaton_type}-Automaton in {(end - start) * 1000}ms")

            case _:
                self._logger.warning(f"Unknown packet type {type(packet)}")
                return
