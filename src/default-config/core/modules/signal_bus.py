"""
This module defines the SignalBus class, a singleton for signal-based communication
between GridView and UiAutomaton using PySide6 signals.
"""
from dataclasses import dataclass
from PySide6.QtCore import Signal, QObject

import typing as _ty

@dataclass
class AutomatonEvent:
    is_loaded: bool
    token_list: _ty.List[str] = None

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

    automaton_changed = Signal(AutomatonEvent)

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

    def emit_automaton_changed(self, is_loaded: bool, token_list: _ty.List[str]=None):
        event = AutomatonEvent(is_loaded=is_loaded, token_list=token_list)
        self.automaton_changed.emit(event)

