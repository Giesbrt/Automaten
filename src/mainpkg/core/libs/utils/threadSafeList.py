import threading

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts

_T = _ty.TypeVar('_T')


class ThreadSafeList(_ty.Generic[_T]):
    def __init__(self, starting_list=None):
        if starting_list is None:
            starting_list = []

        self._list: _ty.List[_T] = starting_list
        self._lock = threading.Lock()

    def append(self, item: _T):
        with self._lock:
            self._list.append(item)

    def get(self, index: int) -> _T:
        with self._lock:
            return self._list[index]

    def __len__(self) -> int:
        with self._lock:
            return len(self._list)

    def __iter__(self) -> _ty.Iterator[_T]:
        with self._lock:
            return iter(self._list.copy())  # defensive copy für sicheren Zugriff

    def pop(self) -> _T:
        with self._lock:
            return self._list.pop()

    def __getitem__(self, index):
        with self._lock:
            return self._list[index]

    def __setitem__(self, index, value):
        with self._lock:
            self._list[index] = value

    def __repr__(self):
        with self._lock:
            return repr(self._list)

    def __str__(self):
        with self._lock:
            return str(self._list)



