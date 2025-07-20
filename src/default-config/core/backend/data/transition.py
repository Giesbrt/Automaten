from dataclasses import dataclass

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts


@dataclass
class Transition:
    transition_id: int

    from_state_id: int
    to_state_id: int

    condition: _ty.List[str]
