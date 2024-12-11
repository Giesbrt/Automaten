"""TBA"""
# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

from abc import ABC

# self._output_alphabet: list[str] = []


class Node:
    def __init__(self, position: tuple[float, float], connections: set[tuple[tuple[str, ...], _ty.Self]] | None = None, *_,
                 root: bool = False, extra_info: str = "") -> None:
        self.position: tuple[float, float] = position
        self.connections: set[tuple[tuple[str, ...], _ty.Self]] = connections or set()
        self.extra_info: str = extra_info
        self.root: bool = root

    def add_to(self, transition: tuple[str, ...], node: _ty.Self) -> None:
        self.connections.add((transition, node))

    def __hash__(self) -> int:
        return hash(repr(self))

    def __repr__(self) -> str:
        return f"Node(position={self.position}, connections={self.connections}, root={self.root})"


class AutoAutomat(ABC):
    def __init__(self, kwargs: dict[str, _ty.Any], to_get: list[tuple[str, str]]):
        for name, value in kwargs.items():
            found: bool = False
            for i, (to_find, to_set) in enumerate(to_get):
                if name == to_find:
                    setattr(self, to_set, value)
                    found = True
                    break
            if found:  # i is guaranteed here
                to_get.pop(i)
        if len(to_get) != 0:
            raise RuntimeError("Not all token lists were found in loaded file")

    def activate(self, directed_cyclic_graph: Node) -> tuple[list | None, ...]:
        if not directed_cyclic_graph.root:
            raise RuntimeError("Activate failed because directed_cyclic_graph root wasn't root")


class DFAAutomat(AutoAutomat):
    def __init__(self, **token_lists: list[str]) -> None:
        self._input_alphabet: list[str] = []
        super().__init__(token_lists, [("input_alphabet", "_input_alphabet")])

    def activate(self, directed_cyclic_graph: Node) -> tuple[list | None, ...]:
        super().activate(directed_cyclic_graph)
        return (self._input_alphabet,)


if __name__ == "__main__":
    root = Node((101.0, 200.0), root=True)
    one = Node((10.0, 20.0), extra_info="is_end")
    root.add_to(("a",), one)
    one.add_to(("d",), root)

    automaton = DFAAutomat(input_alphabet=[chr(i) for i in range(97, 120)])
    transition_base = automaton.activate(root)

    print("Done")
