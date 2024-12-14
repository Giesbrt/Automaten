"""TBA"""
from multiprocessing.shared_memory import SharedMemory
from multiprocessing.synchronize import Lock as MPLock
from multiprocessing import Lock, Process
from enum import Enum
import ctypes
import struct

from aplustools.io.env import auto_repr

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts


@auto_repr
class SharedReference:
    """Shared reference to memory and a lock. It can get pickled and send between processes"""
    def __init__(self, struct_format: str, shm_name: str, lock: MPLock) -> None:
        self.struct_format: str = struct_format
        self.shm_name: str = shm_name
        self.lock: MPLock = lock


class SharedStruct:
    """Shared memory through processes"""
    def __init__(self, struct_format: str, create: bool = False, shm_name: str | None = None,
                 *_, overwrite_mp_lock: MPLock | None = None) -> None:
        self._struct_format: str = struct_format
        self._struct_size: int = struct.calcsize(struct_format)

        if isinstance(overwrite_mp_lock, MPLock):
            self._lock: MPLock = overwrite_mp_lock
        else:
            self._lock: MPLock = Lock()

        if create:  # Create a new, shared memory segment
            self._shm: SharedMemory = SharedMemory(create=True, size=self._struct_size)
        else:  # Attach to an existing shared memory segment
            if shm_name is None:
                raise ValueError("shm_name must be provided, when create=False")
            self._shm: SharedMemory = SharedMemory(name=shm_name)
        self._shm_name: str = self._shm.name  # Store the shared memory name for reference
        self._is_locked: bool = False  # Track whether the lock is manually set

    def set_data(self, *values) -> None:
        """
        Set data in the shared memory structure.

        :param values: Values to set, matching the struct format.
        """
        if len(values) != len(self._struct_format.replace(" ", "")):
            raise ValueError("Number of values must match the struct format")
        if not self._is_locked:
            with self._lock:
                packed_data = struct.pack(self._struct_format, *values)
                self._shm.buf[:self._struct_size] = packed_data
        else:  # Lock is already held by set_lock
            packed_data = struct.pack(self._struct_format, *values)
            self._shm.buf[:self._struct_size] = packed_data

    def get_data(self) -> tuple[_ty.Any, ...]:
        """
        Get data from the shared memory structure.

        :return: Tuple of values unpacked from the shared memory.
        """
        if not self._is_locked:
            with self._lock:
                packed_data = self._shm.buf[:self._struct_size]
                return struct.unpack(self._struct_format, packed_data)
        else:  # Lock is already held by set_lock
            packed_data = self._shm.buf[:self._struct_size]
            return struct.unpack(self._struct_format, packed_data)

    def set_field(self, index: int, value: _ty.Any) -> None:
        """
        Set a single field in the shared memory structure.

        :param index: Index of the field to set (starting from 0).
        :param value: The value to set, matching the struct format at the specified index.
        """
        format_parts = self._struct_format.replace(" ", "")

        if index < 0 or index >= len(format_parts):
            raise IndexError("Field index out of range")

        # Calculate offset for the field based on the format
        offset = sum(struct.calcsize(fmt) for fmt in format_parts[:index])
        field_format = format_parts[index]
        field_size = struct.calcsize(field_format)

        if not self._is_locked:
            with self._lock:
                packed_field = struct.pack(field_format, value)
                self._shm.buf[offset:offset + field_size] = packed_field
        else:  # Lock is already held by set_lock
            packed_field = struct.pack(field_format, value)
            self._shm.buf[offset:offset + field_size] = packed_field

    def get_field(self, index: int) -> _ty.Any:
        """
        Get a single field from the shared memory structure.

        :param index: Index of the field to get (starting from 0).
        :return: The value of the field, unpacked based on the struct format.
        """
        format_parts = self._struct_format.replace(" ", "")

        if index < 0 or index >= len(format_parts):
            raise IndexError("Field index out of range")

        offset = sum(struct.calcsize(fmt) for fmt in format_parts[:index])
        field_format = format_parts[index]
        field_size = struct.calcsize(field_format)

        if not self._is_locked:
            with self._lock:
                packed_field = self._shm.buf[offset:offset + field_size]
                return struct.unpack(field_format, packed_field)[0]
        else:  # Lock is already held by set_lock
            packed_field = self._shm.buf[offset:offset + struct.calcsize(field_format)]
            return struct.unpack(field_format, packed_field)[0]

    def reference(self) -> SharedReference:
        """References this shared struct in a simpler data structure"""
        return SharedReference(self._struct_format, self._shm_name, self._lock)

    @classmethod
    def from_reference(cls, ref: SharedReference) -> _ty.Self:
        """Loads a shared struct obj from a shared reference"""
        return cls(ref.struct_format, False, ref.shm_name, overwrite_mp_lock=ref.lock)

    def close(self) -> None:
        """
        Close the shared memory segment.
        """
        self._shm.close()

    def unlink(self) -> None:
        """
        Unlock the shared memory segment (only call this if you own the memory).
        """
        self._shm.unlink()

    def set_lock(self) -> None:
        """Sets the lock for multiple operations."""
        self._lock.acquire()
        self._is_locked = True

    def unset_lock(self) -> None:
        """Unsets the lock."""
        if self._is_locked:
            self._lock.release()
            self._is_locked = False

    def __enter__(self) -> _ty.Self:
        self.set_lock()
        return self

    def __exit__(self, exc_type: _ty.Type[BaseException] | None, exc_val: BaseException | None,
                 exc_tb: BaseException | None) -> bool | None:
        self.unset_lock()
        # If an exception occurred, propagate it by returning False (default behavior).
        return False  # Exception will propagate to the caller

    def __repr__(self) -> str:
        return (f"SharedStruct(struct_format='{self._struct_format}', struct_size={self._struct_size}, "
                f"shm_name='{self._shm_name}', is_locked={self._is_locked})")


class ABType(Enum):
    """Types the autobahn supports"""
    # Padding byte (no associated type, used to align data)
    pad_byte: None = "x"
    # Single character (1-byte)
    char: bytes = "c"

    int8 = "b"
    uint8 = "B"
    int16 = "h"
    uint16 = "H"
    int32 = "i"
    uint32 = "I"
    int64 = "q"
    uint64 = "Q"

    boolean = "?"

    single_float = "f"
    double_float = "d"
    uncounted_string = "s"
    counted_string = "p"
    pointer = "P"


class Autobahn:
    """Serves as a bridge between the gui and the backend"""
    values: dict[str, tuple[ABType, _ty.Any]] = {
        "automat_loader_code": (ABType.uint8, 0),  # GUI->AutomatLoader (ALC)
        "gui_code": (ABType.uint8, 0),  # AutomatLoader->GUI (GIC)
    }

    def __init__(self, process_type: _ty.Literal["parent", "child"], optional_reference: SharedReference | None = None):
        self._shared_struct = SharedStruct(
            "".join([value[0].value for value in self.values.values()]),
            process_type == "parent",
            optional_reference.shm_name if optional_reference is not None else None,
            overwrite_mp_lock=optional_reference.lock if optional_reference is not None else None
        )
        self._keys = tuple(self.values.keys())
        self._values = tuple(self.values.values())
        for (name, (bridge_type, initial_value)) in self.values.items():
            self.set(name, initial_value)
        self.lock = self._shared_struct  # But don't tell anyone

    def set(self, name: str, value: _ty.Any) -> None:
        self._shared_struct.set_field(self._keys.index(name), value)

    def get(self, name: str) -> _ty.Any:
        return self._shared_struct.get_field(self._keys.index(name))

    def __enter__(self) -> _ty.Self:
        self._shared_struct.set_lock()
        return self

    def __exit__(self, exc_type: _ty.Type[BaseException] | None, exc_val: BaseException | None,
                 exc_tb: BaseException | None) -> bool | None:
        self._shared_struct.unset_lock()
        # If an exception occurred, propagate it by returning False (default behavior).
        return False  # Exception will propagate to the caller


if __name__ == "__main__":
    autobahn = Autobahn("parent")

    with autobahn:
        print(autobahn.get("automat_loader_code"))
        print(autobahn.get("gui_code"))

    shared_struct = SharedStruct("iif", create=True)
    ref = shared_struct.reference()
    ss2 = SharedStruct.from_reference(ref)

    print(shared_struct, ss2, ref)
