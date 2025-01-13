
# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts

T = _ty.TypeVar('T')


class OrderedSet(_ty.Generic[T]):
    def __init__(self, iterable: _ty.Iterable = None) -> None:
        self._items: list[T] = []
        self._seen: set[T] = set()
        if iterable:
            for item in iterable:
                self.add(item)

    def add(self, item: T) -> None:
        if item not in self._seen:
            self._items.append(item)
            self._seen.add(item)

    def discard(self, item: T) -> None:
        if item in self._seen:
            self._items.remove(item)
            self._seen.remove(item)

    def remove(self, item: T) -> None:
        if item not in self._seen:
            raise KeyError(f"{item} not in OrderedSet")
        self.discard(item)

    def clear(self) -> None:
        self._items.clear()
        self._seen.clear()

    def get_index(self, item: T) -> int:
        return self._items.index(item)

    def get_by_index(self, index: int) -> T:
        return self._items[index]

    def to_list(self) -> list[T]:
        return self._items

    def to_set(self) -> set[T]:
        return self._seen

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def __contains__(self, item: T):
        return item in self._seen

    def __repr__(self):
        return f"OrderedSet({self._items})"

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return self._items == other._items
        return False

    def __or__(self, other):
        if not isinstance(other, (OrderedSet, set)):
            return NotImplemented
        return OrderedSet(self._items + [item for item in other if item not in self])

    def __and__(self, other):
        if not isinstance(other, (OrderedSet, set)):
            return NotImplemented
        return OrderedSet(item for item in self if item in other)

    def __sub__(self, other):
        if not isinstance(other, (OrderedSet, set)):
            return NotImplemented
        return OrderedSet(item for item in self if item not in other)

    def __xor__(self, other):
        if not isinstance(other, (OrderedSet, set)):
            return NotImplemented
        return OrderedSet(item for item in self if item not in other).union(
            item for item in other if item not in self)
