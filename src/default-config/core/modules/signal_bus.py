"""
This module defines the SignalBus class, a singleton for signal-based communication
between GridView and UiAutomaton using PySide6 signals.
"""
import threading
from dataclasses import dataclass
from PySide6.QtCore import Signal, QObject

import typing as _ty

class SignalBus(QObject):
    """
    A singleton class for signal-based communication between GridView and UiAutomaton.

    Signals:
    - `request_method(str, tuple, dict)`: Requests a method call with arguments.
    - `send_response(str, object)`: Sends a response with a result.

    Ensures consistent signal handling across components.
    """

    request_method = Signal(str, tuple, dict)
    send_response = Signal(str, object)

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return
        super().__init__()

        self._initialized = True


class SingletonObserver:
    _instance = None
    _lock = threading.Lock()
    _state: _ty.Dict[str, any] = {}
    _observers: _ty.Dict[str, _ty.List[_ty.Callable]] = {}

    def __new__(cls):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __del__(self):
        with self._lock:
            self.__class__._instance = None

    @classmethod
    def reset_instance(cls):
        with cls._lock:
            cls._instance = None

    @classmethod
    def set(cls, key: str, value: any) -> None:
        with cls._lock:
            cls._state[key] = value
            cls._notify(key, value)

    @classmethod
    def get(cls, key: str) -> any:
        return cls._state.get(key)

    @classmethod
    def subscribe(cls, key: str, callback: _ty.Callable) -> None:
        with cls._lock:
            cls._observers.setdefault(key, []).append(callback)

    @classmethod
    def _notify(cls, key: str, value: any) -> None:
        for callback in cls._observers.get(key, []):
            callback(value)