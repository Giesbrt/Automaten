# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts


class ITape(_abc.ABC):

    @_abc.abstractmethod
    def copy(self) -> 'ITape':
        pass

    @_abc.abstractmethod
    def move_to_beginning(self) -> None:
        pass
