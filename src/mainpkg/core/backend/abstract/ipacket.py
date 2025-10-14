import uuid as _uuid4

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts


class IPacket(_abc.ABC):
    def __init__(self):
        self._packet_id: _uuid4.UUID = _uuid4.uuid4()

    def get_packet_id(self) -> _uuid4.UUID:
        return self._packet_id

    def set_packet_id(self, packet_id: _uuid4.UUID) -> None:
        self._packet_id = packet_id

