# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts

T = _ty.TypeVar('T')


class Signal(_ty.Generic[T]):
    def __init__(self, callback: _ts.FunctionType | None = None, add_to_cache: bool = True) -> None:
        self._callback: _ts.FunctionType = callback
        self._add_to_cache: bool = add_to_cache

        self._cache: SignalCache | None = None
        if self._add_to_cache:
            self._cache: SignalCache = SignalCache()

    def connect(self, callback: _ts.FunctionType | None) -> None:
        self._callback = callback

    def _to_cache(self, data: _ty.Callable) -> None:
        if self._add_to_cache and self._cache is not None:
            self._cache.add_emitted_callback(data)
            return

        data()

    def disconnect(self) -> None:
        self._callback = None

    def emit(self, *args, **kwargs) -> None:
        if self._callback is None:
            raise ValueError("Can not emit a callback which is none")

        callback: _ty.Callable = lambda: self._callback(*args, **kwargs)
        self._to_cache(callback)


class SignalCache:
    _callback_queue: _ty.List[_ty.Callable] = []

    def __init__(self) -> None:
        pass

    def add_emitted_callback(self, callback: _ty.Callable) -> None:
        self._callback_queue.append(callback)

    def has_elements(self) -> bool:
        return len(self._callback_queue) > 0

    def invoke(self, amount: _ty.Literal["all", "first"] = "first") -> None:
        if not self.has_elements():
            return

        match amount:
            case "all":
                for i in self._callback_queue:
                    i()

            case "first":
                self._callback_queue[0]()

            case _:
                return
