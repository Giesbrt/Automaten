"""TBA"""

import json
from queue import Queue

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts


class UiBridge:
    _ui_queue: Queue[_ty.Dict[str, str]] = Queue()
    _backend_queue: Queue[_ty.Dict[str, str]] = Queue()

    # Ui
    def get_ui_queue(self) -> Queue[_ty.Dict[str, str]]:
        return self._ui_queue

    def get_ui_task(self) -> _ty.Dict[str, str] or None:
        return self._ui_queue.get_nowait()

    def add_ui_current_item(self, item: _ty.Dict[str, str]) -> None:
        self._ui_queue.put(item)

    def complete_ui_task(self) -> None:
        self._ui_queue.task_done()

    def has_ui_items(self) -> bool:
        return self._ui_queue.empty()

    # Backend
    def get_backend_queue(self) -> Queue[_ty.Dict[str, str]]:
        return self._backend_queue

    def get_backend_task(self) -> _ty.Dict[str, str] or None:
        return self._backend_queue.get_nowait()

    def add_backend_item(self, item: _ty.Dict[str, str]) -> None:
        self._backend_queue.put(item)

    def complete_backend_task(self) -> None:
        self._backend_queue.task_done()

    def has_backend_items(self) -> bool:
        return self._backend_queue.empty()
