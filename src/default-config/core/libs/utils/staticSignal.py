# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts

T = _ty.TypeVar('T')


class StaticSignal(_ty.Generic[T]):
    _callback_queue: _ty.List[_ty.Any] = []

    def __init__(self, callback: _ts.FunctionType | None = None) -> None:
        self._callback: _ts.FunctionType = callback

    def connect(self, callback: _ts.FunctionType | None) -> None:
        self._callback = callback

    def disconnect(self) -> None:
        self._callback = None

    def emit(self, *args, **kwargs) -> _ty.Any:
        if self._callback is None:
            raise ValueError("Can not emit a callback which is none")

        callback = lambda: self._callback(*args, **kwargs)
        self._callback_queue.append(callback)

    def invoke_methods(self):
        if not self._callback_queue:
            return

        self._callback_queue[0]()
