from aplustools.io import ActLogger

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
        """ Connects the signal to a callback

        :param callback: the callback to be stored in the signal
        :return: None
        """
        self._callback = callback

    def _to_cache(self, data: _ty.Callable) -> None:
        """ Adds the signal callable to the queue or

        :param data: the signal callback
        :return: None
        """
        if self._add_to_cache and self._cache is not None:
            self._cache.add_emitted_callback(data)
            return

        data()

    def disconnect(self) -> None:
        """ Disconnects the callback and the signal

        :return: None
        """
        self._callback = None

    def emit(self, *args, **kwargs) -> None:
        """ Emits the stored callback

        :param args: arguments
        :param kwargs: key word arguments
        :return: None
        """
        ActLogger().debug("Emitted signal")
        if self._callback is None:
            raise ValueError("Can not emit a callback which is none")

        callback: _ty.Callable = lambda: self._callback(*args, **kwargs)
        self._to_cache(callback)


class SignalCache:
    _callback_queue: _ty.List[_ty.Callable] = []

    def __init__(self) -> None:
        pass

    def add_emitted_callback(self, callback: _ty.Callable) -> None:
        """ Adds a signal to the queue

        :param callback: the signal
        :return: None
        """
        self._callback_queue.append(callback)

    def has_elements(self) -> bool:
        """ Returns if the cache has signals stored

        :return: True, if signals stored
        """
        return len(self._callback_queue) > 0

    def invoke(self, amount: _ty.Literal["all", "first"] = "first") -> None:
        """ Invokes stored signals

        :param amount: ["all", "first"] -> how many methods should be invoked
        :return: None
        """
        if not self.has_elements():
            return

        ActLogger().debug("Invoking methods")

        match amount:
            case "all":
                for i in self._callback_queue:
                    i()
                    self._callback_queue.remove(i)

            case "first":
                self._callback_queue[0]()
                self._callback_queue.pop(0)

            case _:
                return
