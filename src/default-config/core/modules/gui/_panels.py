"""Panels of the gui"""
from PySide6.QtWidgets import QWidget

from aplustools.io.qtquick import QNoSpacingBoxLayout, QBoxDirection

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts


class Panel(QWidget):
    """Baseclass for all Panels"""
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)


class UserPanel(Panel):
    """The main panel to be shown"""
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setLayout(QNoSpacingBoxLayout(QBoxDirection.TopToBottom))
