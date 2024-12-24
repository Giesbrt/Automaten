import json
from queue import Queue

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts


# Docs generated with Chat-GPT

class UiBridge:
    """
    UiBridge is a queue provider that acts as an interface between the UI and the backend.
    It facilitates the exchange of JSON-formatted data (represented as Python dictionaries) between these components.

    This class manages two separate queues:
    1. UI Queue: Handles tasks sent from the backend to the UI.
    2. Backend Queue: Handles tasks sent from the UI to the backend.

    Methods are provided to interact with these queues, including adding items, retrieving items, and checking queue states.
    """

    # Queues for UI and Backend communication
    _ui_queue: Queue[_ty.Dict[str, str]] = Queue()
    _backend_queue: Queue[_ty.Dict[str, str]] = Queue()

    # UI-related methods
    def get_ui_queue(self) -> Queue[_ty.Dict[str, str]]:
        """
        Retrieve the UI queue.

        Returns:
            Queue[_ty.Dict[str, str]]: The queue for UI tasks.
        """
        return self._ui_queue

    def get_ui_task(self) -> _ty.Dict[str, str] or None:
        """
        Retrieve the next task from the UI queue without blocking.

        Returns:
            _ty.Dict[str, str] or None: The next task from the UI queue, or None if the queue is empty.
        """
        return self._ui_queue.get_nowait()

    def add_ui_item(self, item: _ty.Dict[str, str]) -> None:
        """
        Add a new task to the UI queue.

        Args:
            item (_ty.Dict[str, str]): The task to be added to the UI queue.
        """
        self._ui_queue.put(item)

    def complete_ui_task(self) -> None:
        """
        Mark the current task in the UI queue as complete.

        This method should be called after processing a task from the UI queue.
        """
        self._ui_queue.task_done()

    def has_ui_items(self) -> bool:
        """
        Check if the UI queue has items.

        Returns:
            bool: True if the UI queue is empty, False otherwise.
        """
        return self._ui_queue.empty()

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
        return self._backend_queue.empty()
