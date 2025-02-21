import json
from queue import Queue
from utils.staticContainer import StaticContainer
from utils.staticSignal import Signal

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts


# Docs generated with Chat-GPT

class UiBridge:
    """
    UiBridge is a queue provider that acts as an interface between the Simulation and the backend.
    It facilitates the exchange of JSON-formatted data (represented as Python dictionaries) between these components.

    This class manages two separate queues:
    1. Simulation Queue: Handles tasks sent from the backend to the Simulation.
    2. Backend Queue: Handles tasks sent from the Simulation to the backend.

    Methods are provided to interact with these queues, including adding items, retrieving items, and checking queue states.
    """

    # Queues for Simulation and Backend communication
    _ui_queue: Queue[_ty.Dict[str, str]] = Queue()
    _backend_queue: Queue[_ty.Dict[str, str]] = Queue()
    _simulation_queue: Queue[_ty.Dict[str, str]] = Queue()

    _simulation_data_ready: StaticContainer[bool] = StaticContainer(False)
    _data_ready_signal: StaticContainer[Signal[_ty.Callable]] = StaticContainer(None)

    # data ready
    def set_signal(self, signal: Signal[_ty.Callable]) -> None:
        self._data_ready_signal.set_value(signal)

    def get_signal(self) -> Signal[_ty.Callable]:
        return self._data_ready_signal.get_value()

    # ui-related methods
    def get_ui_queue(self) -> Queue[_ty.Dict[str, str]]:
        """
        Retrieve the Simulation queue.

        Returns:
            Queue[_ty.Dict[str, str]]: The queue for Simulation tasks.
        """
        return self._ui_queue

    def get_ui_task(self) -> _ty.Dict[str, str] or None:
        """
        Retrieve the next task from the Simulation queue without blocking.

        Returns:
            _ty.Dict[str, str] or None: The next task from the Simulation queue, or None if the queue is empty.
        """
        return self._ui_queue.get_nowait()

    def add_ui_item(self, item: _ty.Dict[str, str]) -> None:
        """
        Add a new task to the Simulation queue.

        Args:
            item (_ty.Dict[str, str]): The task to be added to the Simulation queue.
        """
        self._ui_queue.put(item)

    def complete_ui_task(self) -> None:
        """
        Mark the current task in the Simulation queue as complete.

        This method should be called after processing a task from the Simulation queue.
        """
        self._ui_queue.task_done()

    def has_ui_items(self) -> bool:
        """
        Check if the Simulation queue has items.

        Returns:
            bool: True if the Simulation queue is empty, False otherwise.
        """
        return not self._ui_queue.empty()

    def clear_ui_queue(self) -> None:
        """
        This method clears the ui queue.
        """
        self._ui_queue.queue.clear()

    # Simulation-related methods
    def get_simulation_queue(self) -> Queue[_ty.Dict[str, str]]:
        """
        Retrieve the Simulation queue.

        Returns:
            Queue[_ty.Dict[str, str]]: The queue for Simulation tasks.
        """
        return self._simulation_queue

    def get_simulation_task(self) -> _ty.Dict[str, str] or None:
        """
        Retrieve the next task from the Simulation queue without blocking.

        Returns:
            _ty.Dict[str, str] or None: The next task from the Simulation queue, or None if the queue is empty.
        """
        return self._simulation_queue.get_nowait()

    def add_simulation_item(self, item: _ty.Dict[str, str]) -> None:
        """
        Add a new task to the Simulation queue.

        Args:
            item (_ty.Dict[str, str]): The task to be added to the Simulation queue.
        """
        self._simulation_queue.put(item)

    def complete_simulation_task(self) -> None:
        """
        Mark the current task in the Simulation queue as complete.

        This method should be called after processing a task from the Simulation queue.
        """
        self._simulation_queue.task_done()

    def has_simulation_items(self) -> bool:
        """
        Check if the Simulation queue has items.

        Returns:
            bool: True if the Simulation queue is empty, False otherwise.
        """
        return not self._simulation_queue.empty()

    def clear_simulation_queue(self) -> None:
        """
        This method clears the simulation queue.
        """
        self._simulation_queue.queue.clear()

    def is_simulation_data_ready(self) -> bool:
        """
        Returns an integrity-status for the simulation data
        :return: True, if the simulation data is deemed ready
        """
        if not self._simulation_data_ready.has_value():
            return False
        return self._simulation_data_ready.get_value()

    def set_simulation_data_status(self, status: bool) -> None:
        """
        Sets a new status for the simulation data
        :param status: bool
        :return: None
        """
        self._simulation_data_ready.set_value(status)

    # Backend-related methods
    def get_backend_queue(self) -> Queue[_ty.Dict[str, str]]:
        """
        Retrieve the backend queue.

        Returns:
            Queue[_ty.Dict[str, str]]: The queue for backend tasks.
        """
        return self._backend_queue

    def get_backend_task(self) -> _ty.Dict[str, str] or None:
        """
        Retrieve the next task from the backend queue without blocking.

        Returns:
            _ty.Dict[str, str] or None: The next task from the backend queue, or None if the queue is empty.
        """
        return self._backend_queue.get_nowait()

    def add_backend_item(self, item: _ty.Dict[str, str]) -> None:
        """
        Add a new task to the backend queue.

        Args:
            item (_ty.Dict[str, str]): The task to be added to the backend queue.
        """
        self._backend_queue.put(item)

    def complete_backend_task(self) -> None:
        """
        Mark the current task in the backend queue as complete.

        This method should be called after processing a task from the backend queue.
        """
        self._backend_queue.task_done()

    def has_backend_items(self) -> bool:
        """
        Check if the backend queue has items.

        Returns:
            bool: True if the backend queue is empty, False otherwise.
        """
        return not self._backend_queue.empty()
