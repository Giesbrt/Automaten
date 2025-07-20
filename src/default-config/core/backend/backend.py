import threading as _threading

from core.backend.backendHandler import BackendHandler as _BackendHandler
from core.backend.packets.packetManager import PacketManager as _PacketManager
from core.backend.abstract.ipacket import IPacket as _IPacket

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts


class _Backend:
    def __init__(self, *args, **kwargs):
        # store persistent data
        ...

    def run_infinite(self, stop_event: _threading.Event):  # running in the backend thread
        backend_handler: _BackendHandler = _BackendHandler(self)
        packet_manager: _PacketManager = _PacketManager()

        while not stop_event.is_set():
            packet: _IPacket = packet_manager.get_backend_packets()
            if packet:
                backend_handler.handle_packet(packet)

BackendType: _ty.Type[_Backend] = _Backend


def start_backend(*args, **kwargs) -> _Backend:
    return _Backend(*args, **kwargs)
