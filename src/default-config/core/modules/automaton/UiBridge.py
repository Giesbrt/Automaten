"""TBA"""

import json
from core.modules.utils.singleton import singleton

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts


@singleton
class UiBridge:
    def __init__(self) -> None:
        self.ui_queue: _ty.List[_ty.Dict[str, str]] = []
        self.backend_queue: _ty.List[_ty.Dict[str, str]] = []

    # Ui
    def get_ui_queue(self) -> _ty.List[_ty.Dict[str, str]]:
        return self.ui_queue

    def get_ui_current_queue_item(self) -> _ty.Dict[str, str] or None:
        if not self.ui_queue:
            return None
        return self.ui_queue[0]

    def add_ui_queue_item(self, item: _ty.Dict[str, str]) -> None:
        self.ui_queue.append(item)

    def remove_ui_current_queue_item(self) -> None:
        if not self.ui_queue:
            return
        self.ui_queue.pop(0)

    def has_ui_items(self) -> bool:
        return len(self.ui_queue) > 0

    # Backend
    def get_backend_queue(self) -> _ty.List[_ty.Dict[str, str]]:
        return self.backend_queue

    def get_backend_current_queue_item(self) -> _ty.Dict[str, str] or None:
        if not self.backend_queue:
            return None
        return self.backend_queue[0]

    def add_backend_queue_item(self, item: _ty.Dict[str, str]) -> None:
        self.backend_queue.append(item)

    def remove_backend_current_queue_item(self) -> None:
        if not self.backend_queue:
            return
        self.backend_queue.pop(0)

    def has_backend_items(self) -> bool:
        return len(self.backend_queue) > 0
