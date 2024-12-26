"""TBA"""
from PySide6.QtWidgets import QWidget, QMainWindow, QMessageBox, QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import QRect, QSize, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup

from aplustools.io.qtquick import QQuickMessageBox

from ..abstract import MainWindowInterface
from ._panels import Panel, UserPanel, SettingsPanel

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts


class MainWindow(MainWindowInterface, QMainWindow):
    linked: bool = False

    def __new__(cls, *args, **kwargs):
        return QMainWindow.__new__(cls,)

    def __init__(self) -> None:
        self.user_panel: UserPanel | None = None
        self.settings_panel: SettingsPanel | None = None
        self.user_panel_animation: QPropertyAnimation | None = None
        self.settings_panel_animation: QPropertyAnimation | None = None
        self.panel_animation_group: QParallelAnimationGroup | None = None
        super().__init__(parent=None)

    def setup_gui(self) -> None:
        self.user_panel = UserPanel(parent=self)
        self.settings_panel = SettingsPanel(parent=self)

        # Animation for Panels
        self.user_panel_animation = QPropertyAnimation(self.user_panel, b"geometry")
        self.settings_panel_animation = QPropertyAnimation(self.settings_panel, b"geometry")
        for animation in (self.user_panel_animation, self.settings_panel_animation):
            animation.setDuration(500)
            animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.panel_animation_group = QParallelAnimationGroup()
        self.panel_animation_group.addAnimation(self.user_panel_animation)
        self.panel_animation_group.addAnimation(self.settings_panel_animation)

        self.user_panel.settings_button.clicked.connect(self.switch_panel)
        self.settings_panel.back_button.clicked.connect(self.switch_panel)
        self.switch_panel_simple()  # So they are ordered correctly

    def set_window_icon(self, absolute_path_to_icon: str) -> None:
        self.setWindowIcon(QIcon(absolute_path_to_icon))

    def set_window_title(self, title: str) -> None:
        self.setWindowTitle(title)

    def set_window_geometry(self, x: int, y: int, height: int, width: int) -> None:
        self.setGeometry(QRect(x, y, height, width))

    def set_window_dimensions(self, height: int, width: int) -> None:
        self.resize(QSize(height, width))

    def switch_panel_simple(self):
        width = self.width()
        height = self.height()

        user_panel_hidden_value = QRect(-width, 0, width, height)
        shown_panel_end_value = QRect(0, 0, width, height)
        settings_panel_hidden_value = QRect(width, 0, width, height)

        if self.settings_panel.x() == 0:
            self.user_panel.setGeometry(shown_panel_end_value)
            self.settings_panel.setGeometry(settings_panel_hidden_value)
        else:
            self.user_panel.setGeometry(user_panel_hidden_value)
            self.settings_panel.setGeometry(shown_panel_end_value)

    def reload_panels(self) -> None:
        width = self.width()
        height = self.height()

        user_panel_hidden_value = QRect(-width, 0, width, height)
        shown_panel_end_value = QRect(0, 0, width, height)
        settings_panel_hidden_value = QRect(width, 0, width, height)

        if self.settings_panel.x() == 0:
            self.user_panel.setGeometry(user_panel_hidden_value)
            self.settings_panel.setGeometry(shown_panel_end_value)
        else:
            self.user_panel.setGeometry(shown_panel_end_value)
            self.settings_panel.setGeometry(settings_panel_hidden_value)

    def set_global_theme(self, theme_str: str, base: str | None = None) -> None:
        self.setStyleSheet(theme_str)
        if base is not None:
            self.app.setStyle(base)

    def switch_panel(self):
        width = self.width()
        height = self.height()

        user_panel_hidden_value = QRect(-width, 0, width, height)
        shown_panel_end_value = QRect(0, 0, width, height)
        settings_panel_hidden_value = QRect(width, 0, width, height)

        if self.settings_panel.x() == 0:
            self.user_panel_animation.setStartValue(user_panel_hidden_value)
            self.user_panel_animation.setEndValue(shown_panel_end_value)
            self.settings_panel_animation.setStartValue(shown_panel_end_value)
            self.settings_panel_animation.setEndValue(settings_panel_hidden_value)
        else:
            self.user_panel_animation.setStartValue(shown_panel_end_value)
            self.user_panel_animation.setEndValue(user_panel_hidden_value)
            self.settings_panel_animation.setStartValue(settings_panel_hidden_value)
            self.settings_panel_animation.setEndValue(shown_panel_end_value)
        self.panel_animation_group.start()

    def popup(self, title: str, text: str, description: str, icon: QMessageBox.Icon = QMessageBox.Icon.Information,
              buttons: list[QMessageBox.StandardButton] | QMessageBox.StandardButton = QMessageBox.StandardButton.Ok,
              default_button: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok) -> QMessageBox.StandardButton:
        msg_box = QQuickMessageBox(self, icon, title, text, description,
                                   standard_buttons=buttons,
                                   default_button=default_button)
        return msg_box.exec()

    def set_scroll_speed(self, value: float) -> None:
        return

    def start(self) -> None:
        self.show()
        self.raise_()

    def close(self) -> None:
        QMainWindow.close(self)
