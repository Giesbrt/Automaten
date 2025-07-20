from core.backend.abstract.ipacket import IPacket as _IPacket
from core.libs.utils.threadSafeList import ThreadSafeList
from queue import Queue

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts


class PacketManager:
    _backend_packet: Queue[_IPacket] = Queue()
    _frontend_packet: Queue[_IPacket] = Queue()

    def __init__(self):
        super().__init__()

    def send_backend_packet(self, packet: _IPacket) -> None:
        self._backend_packet.put(packet)

    def send_frontend_packet(self, packet: _IPacket) -> None:
        self._frontend_packet.put(packet)

    def has_backend_packets(self) -> bool:
        return not self._backend_packet.empty()

    def has_frontend_packets(self) -> bool:
        return not self._frontend_packet.empty()

    def get_backend_packets(self) -> _IPacket | None:
        if not self.has_backend_packets():
            return None

        return self._backend_packet.get_nowait()

    def get_frontend_packets(self) -> _IPacket | None:
        if not self.has_frontend_packets():
            return None

        return self._frontend_packet.get_nowait()

