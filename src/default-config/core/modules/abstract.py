"""Abstract api interfaces for everything"""
import math
import threading

from PySide6.QtWidgets import QWidget, QApplication, QMainWindow
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts


class MainWindowInterface:
    """TBA"""
    icons_folder: str = ""
    popups: list[_ty.Any] = []  # Basically anything that isn't the main window, but a window
    app: QApplication | None = None

    class AppStyle:
        """QApp Styles"""
        Windows11 = 'windows11'
        WindowsVista = 'windowsvista'
        Windows = 'Windows'
        Fusion = 'Fusion'
        Default = None

    def __new__(cls, *args, **kwargs):
        raise Exception("This class can't be initialized; it is just an Interface.")

    def setup_gui(self) -> None:
        """
        Configure the main graphical user interface (GUI) elements of the MV application.

        This method sets up various widgets, layouts, and configurations required for the
        main window interface. It is called after initialization and prepares the interface
        for user interaction.

        Note:
            This method is intended to be overridden by subclasses with application-specific
            GUI components.
        """
        raise NotImplementedError

    def set_window_icon(self, absolute_path_to_icon: str) -> None:
        raise NotImplementedError

    def set_window_title(self, title: str) -> None:
        raise NotImplementedError

    def set_window_geometry(self, x: int, y: int, height: int, width: int) -> None:
        raise NotImplementedError

    def set_window_dimensions(self, height: int, width: int) -> None:
        raise NotImplementedError

    def reload_panels(self) -> None:
        raise NotImplementedError

    def create_popup(self, of_what: QWidget, window_flags: Qt.WindowType) -> int:  # Return the popup-index
        raise NotImplementedError

    def destroy_popup(self, index) -> None:  # Remove popup by index
        raise NotImplementedError

    def button_popup(self, title: str, text: str, description: str,
                     icon: _ty.Literal["Information", "Critical", "Question", "Warning", "NoIcon"],
                     buttons: list[str], default_button: str, checkbox: str | None = None) -> tuple[str | None, bool]:
        raise NotImplementedError

    def set_theme_to_singular(self, theme_str: str, widget_or_window: QWidget) -> None:
        """Applies a theme string to a singular object"""
        raise NotImplementedError

    def set_global_theme(self, theme_str: str, base: str | None = None) -> None:
        raise NotImplementedError

    def internal_obj(self) -> QMainWindow:
        raise NotImplementedError

    def start(self) -> None:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError


class BackendInterface:
    """The backend entry point"""

    def __new__(cls, *args, **kwargs):
        raise Exception("This class can't be initialized; it is just an Interface.")

    def run_infinite(self, backend_stop_event: threading.Event) -> None:
        """
        Used to actually start the backend. The gui will launch this in a separate thread.
        """
        ...


class BackendInstructionManager:
    @staticmethod
    def load_file(file_path: str) -> _ty.Dict[str, _ty.Any]:
        pass

    @staticmethod
    def save_file(file_path: str) -> ...:
        pass


class GuiInstructionManager:
    @staticmethod
    def load_automaton():  ## Todo implement
        pass

# Todo add ui automaton interface
#
# def __new__(cls, *args, **kwargs):
#        raise Exception("This class can't be initialized; it is just an Interface.")
#
#
