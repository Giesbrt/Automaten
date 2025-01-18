"""TBA"""
from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QPushButton, QCheckBox
from PySide6.QtGui import QIcon, QAction, QDesktopServices
from PySide6.QtCore import QRect, QSize, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QUrl

from aplustools.io.qtquick import QQuickMessageBox
from aplustools.io.env import ImplInterface

from ..abstract import IMainWindow
from ._panels import Panel, UserPanel, SettingsPanel

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts


class MainWindow(QMainWindow, IMainWindow, ImplInterface):
    linked: bool = False

    # def __new__(cls, *args, **kwargs):
    #     return QMainWindow.__new__(cls,)

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

        file_menu = self.menuBar().addMenu("File")
        open_action = QAction("Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        exit_action = QAction("Close", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        simulation_menu = self.menuBar().addMenu("Simulation")
        start_action = QAction("Start", self)
        start_action.setShortcut("Ctrl+G")
        simulation_menu.addAction(start_action)
        single_step_action = QAction("Single Step", self)
        single_step_action.setCheckable(True)
        simulation_menu.addAction(single_step_action)
        step_action = QAction("Step", self)
        step_action.setShortcut("Ctrl+T")
        simulation_menu.addAction(step_action)
        stop_action = QAction("Stop", self)
        stop_action.setShortcut("Ctrl+Y")
        simulation_menu.addAction(stop_action)

        edit_menu = self.menuBar().addMenu("Edit")
        cut_action = QAction("Cut", self)
        cut_action.setShortcut("Ctrl+X")
        edit_menu.addAction(cut_action)
        copy_action = QAction("Copy", self)
        copy_action.setShortcut("Ctrl+C")
        edit_menu.addAction(copy_action)
        paste_action = QAction("Paste", self)
        paste_action.setShortcut("Ctrl+V")
        edit_menu.addAction(paste_action)

        help_menu = self.menuBar().addMenu("Help")
        report_action = QAction("Report Issue", self)
        report_action.triggered.connect(self.report_issue)
        help_menu.addAction(report_action)
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        self.menuBar().setFixedHeight(30)

    def open_file(self):
        file_dialog = QFileDialog(self)
        file_path, _ = file_dialog.getOpenFileName(
            self, "Open File", filter="JSON (*.json);;YAML (*.yml, *.yaml);;Binary (*.au);;All Files (*)"
        )
        if file_path:
            QMessageBox.information(self, "File Opened", f"You opened: {file_path}")

    def save_file(self):
        file_dialog = QFileDialog(self)
        file_path, _ = file_dialog.getSaveFileName(
            self, "Save File", filter="JSON (*.json);;YAML (*.yml, *.yaml);;Binary (*.au)")
        if file_path:
            QMessageBox.information(self, "File Saved", f"File saved to: {file_path}")

    def show_about(self):
        QMessageBox.about(self, "About", "This is a PySide6 Menu Bar Example.")

    def report_issue(self):
        QDesktopServices.openUrl(QUrl("https://github.com/Giesbrt/Automaten/issues/new?template=Blank%20issue"))

    def set_window_icon(self, absolute_path_to_icon: str) -> None:
        self.setWindowIcon(QIcon(absolute_path_to_icon))

    def set_window_title(self, title: str) -> None:
        self.setWindowTitle(title)

    def set_window_geometry(self, x: int, y: int, height: int, width: int) -> None:
        self.setGeometry(QRect(x, y, height, width))

    def set_window_dimensions(self, height: int, width: int) -> None:
        self.resize(QSize(height, width))

    def switch_panel_simple(self):
        menubar_bottom = self.menuBar().height()
        width = self.width()
        height = self.height() - menubar_bottom
        top = menubar_bottom

        user_panel_hidden_value = QRect(-width, top, width, height)
        shown_panel_end_value = QRect(0, top, width, height)
        settings_panel_hidden_value = QRect(width, top, width, height)

        if self.settings_panel.x() == 0:
            self.user_panel.setGeometry(shown_panel_end_value)
            self.settings_panel.setGeometry(settings_panel_hidden_value)
        else:
            self.user_panel.setGeometry(user_panel_hidden_value)
            self.settings_panel.setGeometry(shown_panel_end_value)

    def reload_panels(self) -> None:
        menubar_bottom = self.menuBar().height()
        width = self.width()
        height = self.height() - menubar_bottom
        top = menubar_bottom

        user_panel_hidden_value = QRect(-width, top, width, height)
        shown_panel_end_value = QRect(0, top, width, height)
        settings_panel_hidden_value = QRect(width, top, width, height)

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
        menubar_bottom = self.menuBar().height()
        width = self.width()
        height = self.height() - menubar_bottom
        top = menubar_bottom

        user_panel_hidden_value = QRect(-width, top, width, height)
        shown_panel_end_value = QRect(0, top, width, height)
        settings_panel_hidden_value = QRect(width, top, width, height)

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

    def button_popup(self, title: str, text: str, description: str,
                     icon: _ty.Literal["Information", "Critical", "Question", "Warning", "NoIcon"],
                     buttons: list[str], default_button: str, checkbox: str | None = None) -> tuple[str | None, bool]:
        if checkbox is not None:
            checkbox = QCheckBox(checkbox)
        msg_box = QQuickMessageBox(self, getattr(QMessageBox.Icon, icon), title, text,
                                   checkbox=checkbox, standard_buttons=None, default_button=None)
        button_map: dict[str, QPushButton] = {}
        for button_str in buttons:
            button = QPushButton(button_str)
            button_map[button_str] = button
            msg_box.addButton(button, QMessageBox.ButtonRole.ActionRole)
        custom_button = button_map.get(default_button)
        if custom_button is not None:
            msg_box.setDefaultButton(custom_button)
        msg_box.setDetailedText(description)

        clicked_button: int = msg_box.exec()

        checkbox_checked = False
        if checkbox is not None:
            checkbox_checked = checkbox.isChecked()

        for button_text, button_obj in button_map.items():
            if msg_box.clickedButton() == button_obj:
                return button_text, checkbox_checked
        return None, checkbox_checked

    def set_scroll_speed(self, value: float) -> None:
        return

    def internal_obj(self) -> QMainWindow:
        return self

    def start(self) -> None:
        self.show()
        self.raise_()

    def close(self) -> None:
        QMainWindow.close(self)
