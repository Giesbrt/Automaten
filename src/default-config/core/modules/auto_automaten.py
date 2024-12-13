"""TBA"""

from serializer import DCGNode, activate_dcg_node_root

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

from abc import ABC

# self._output_alphabet: list[str] = []


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

    def activate(self, directed_cyclic_graph: DCGNode) -> tuple[list | None, ...]:
        if not directed_cyclic_graph.root:
            raise RuntimeError("Activate failed because directed_cyclic_graph root wasn't root")


class DFAAutomat(AutoAutomat):
    def __init__(self, **token_lists: list[str]) -> None:
        self._input_alphabet: list[str] = []
        super().__init__(token_lists, [("input_alphabet", "_input_alphabet")])

    def activate(self, directed_cyclic_graph: DCGNode) -> tuple[list | None, ...]:
        super().activate(directed_cyclic_graph)
        return (self._input_alphabet,)


if __name__ == "__main__":
    root = DCGNode((101.0, 200.0), root=True)
    activate_dcg_node_root(root, ([chr(i) for i in range(97, 123)], None))
    one = DCGNode((10.0, 20.0), extra_info=b"is_end")
    root.tie_to((0, "x"), one)
    one.tie_to((3, "d"), root)

    automaton = DFAAutomat(input_alphabet=root.representative_lists[0])
    transition_base = automaton.activate(root)

    print("Done")
