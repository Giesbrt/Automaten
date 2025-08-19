
import typing as _ty
import ctypes

class CircularBuffer:
    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be > 0")
        self._capacity = capacity
        self._array: ctypes.Array[ctypes.py_object] = (ctypes.py_object * capacity)()
        self._current_idx: int = 0
        self._head: int = -1
        self._count: int = 0

    def append(self, elem: _ty.Any) -> None:
        idx: int = (self._head + 1) % self._capacity
        self._array[idx] = ctypes.py_object(elem)
        self._current_idx += 1
        self._count = min(self._count + 1, self._capacity)
        self._head = idx

    def __getitem__(self, item: int) -> _ty.Any:
        offset: int = self._current_idx - item
        actual_idx: int = self._head - offset + 1
        if 0 > offset > self._capacity or self._count <= abs(actual_idx) or actual_idx < 0:
            raise IndexError()
        return self._array[actual_idx]


if __name__ == "__main__":
    buff = CircularBuffer(30)
    for i in range(120):
        buff.append(i * 10)

    for i in range(100):
        try:
            print(i, buff[i])
        except IndexError:
            print("IE", i)
