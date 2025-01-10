from typing import TypeVar, Generic

T = TypeVar('T')


class OrderedSet(Generic[T]):
    def __init__(self, iterable=None):
        self.items = []
        self.seen = set()
        if iterable:
            for item in iterable:
                self.add(item)

    def add(self, item: T):
        if item not in self.seen:
            self.items.append(item)
            self.seen.add(item)

    def discard(self, item: T):
        if item in self.seen:
            self.items.remove(item)
            self.seen.remove(item)

    def remove(self, item: T):
        if item not in self.seen:
            raise KeyError(f"{item} not in OrderedSet")
        self.discard(item)

    def clear(self):
        self.items.clear()
        self.seen.clear()

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    def __contains__(self, item: T):
        return item in self.seen

    def __repr__(self):
        return f"OrderedSet({self.items})"

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return self.items == other.items
        return False

    def __or__(self, other):
        if not isinstance(other, (OrderedSet, set)):
            return NotImplemented
        return OrderedSet(self.items + [item for item in other if item not in self])

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
            item for item in other if item not in self
        )
