"""
This module defines the SignalBus class, a singleton for signal-based communication
between GridView and UiAutomaton using PySide6 signals.
"""
from PySide6.QtCore import Signal, QObject

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

