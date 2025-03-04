"""TBA"""
import os

from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QPushButton, QCheckBox, QWidget, QDialog, \
    QVBoxLayout, QLabel, QMenu
from PySide6.QtGui import QIcon, QAction, QDesktopServices, QFont, QColor, QPalette
from PySide6.QtCore import QRect, QSize, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QUrl, Qt, Signal

from aplustools.io.qtquick import QQuickMessageBox

from abstractions import IMainWindow
from storage import AppSettings
from automaton.UiSettingsProvider import UiSettingsProvider
from ._panels import UserPanel, SettingsPanel

# Standard typing imports for aps
import re as _re
import typing as _ty


class AutomatonSelectionDialog(QDialog):
    def __init__(self, grid_view, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)

        self.grid_view = grid_view

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0, 128))
        self.setAutoFillBackground(True)
        self.setPalette(palette)

        self._settings = AppSettings()

        layout = QVBoxLayout(self)

        title = QLabel("Choose a Automatontype:")
        title.setStyleSheet("color: white; font-size: 18px;")
        layout.addWidget(title)

        self.ui_settings_provider = UiSettingsProvider()
        settings = self.ui_settings_provider.get_loaded_settings()

        types = ["Deterministic Finite Automaton (DFA)", "Mealy-Machine (Mealy)", "Turing Machine (TM)"]
        self.buttons = {}

        for automaton_type in types:
            button = QPushButton(automaton_type)
            button.clicked.connect(self.select_type)
            layout.addWidget(button)
            self.buttons[automaton_type] = button

        self.selected_type = None

    def select_type(self):
        button = self.sender()
        if button:
            self.selected_type = _re.findall(r'\((.*?)\)', button.text())
        self.parent().ui_automaton.set_automaton_type(self.selected_type[0])
        self.grid_view._setup_automaton_view(self.selected_type[0])
        widget = self.parent().ui_automaton.get_input_widget()
        self.parent().user_panel.position_input_widget(widget)

        self.accept()


class MainWindow(QMainWindow, IMainWindow):
    save_file_signal: Signal(str) = Signal(str)
    open_file_signal: Signal(str) = Signal(str)
    settings_changed = Signal(dict[str, dict[str, str]])
    manual_update_check: Signal

    def __init__(self) -> None:
        self.file_path: str = ''
        self.settings_button: QPushButton | None = None
        self.menu_bar: None = None
        self.user_panel: UserPanel | None = None
        self.settings_panel: SettingsPanel | None = None
        self.user_panel_animation: QPropertyAnimation | None = None
        self.settings_panel_animation: QPropertyAnimation | None = None
        self.panel_animation_group: QParallelAnimationGroup | None = None
        self.automaton_type: str | None = None
        super().__init__(parent=None)
        # self.statusBar().showMessage("Statusbar")

    def setup_gui(self, ui_automaton: 'UiAutomaton') -> None:
        self.settings = AppSettings()
        self.ui_automaton = ui_automaton

        self.settings_button = QPushButton(parent=self)
        self.menu_bar = self.menuBar()
        self.user_panel = UserPanel(ui_automaton, parent=self)
        self.settings_panel = SettingsPanel(parent=self)
        self.manual_update_check = self.settings_panel.manual_update_check

        # Animation for Panels
        self.user_panel_animation = QPropertyAnimation(self.user_panel, b"geometry")
        self.settings_panel_animation = QPropertyAnimation(self.settings_panel, b"geometry")
        for animation in (self.user_panel_animation, self.settings_panel_animation):
            animation.setDuration(500)
            animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.panel_animation_group = QParallelAnimationGroup()
        self.panel_animation_group.addAnimation(self.user_panel_animation)
        self.panel_animation_group.addAnimation(self.settings_panel_animation)

        self.switch_panel_simple()  # So they are ordered correctly

        file_menu = self.menuBar().addMenu("File")
        new_action = QAction('New', self)
        new_action.setShortcut(self.settings.get_file_new_shortcut())
        self.settings.file_new_shortcut_changed.connect(new_action.setShortcut)
        new_action.triggered.connect(self.user_panel.grid_view.empty_scene)
        file_menu.addAction(new_action)

        open_action = QAction("Open", self)
        open_action.setShortcut(self.settings.get_file_open_shortcut())
        self.settings.file_open_shortcut_changed.connect(open_action.setShortcut)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        self.recent_menu = QMenu("Open Recent", self)
        file_menu.addMenu(self.recent_menu)
        save_action = QAction("Save", self)
        save_action.setShortcut(self.settings.get_file_save_shortcut())
        self.settings.file_save_shortcut_changed.connect(save_action.setShortcut)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save as", self)
        save_as_action.setShortcut(self.settings.get_file_save_as_shortcut())
        self.settings.file_save_as_shortcut_changed.connect(save_as_action.setShortcut)
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        exit_action = QAction("Close", self)
        exit_action.setShortcut(self.settings.get_file_close_shortcut())
        self.settings.file_close_shortcut_changed.connect(exit_action.setShortcut)
        exit_action.triggered.connect(self.ui_automaton.unload)
        file_menu.addAction(exit_action)

        # simulation_menu = self.menuBar().addMenu("Simulation")
        # start_action = QAction("Start", self)
        # start_action.setShortcut("Ctrl+G")
        # simulation_menu.addAction(start_action)
        # single_step_action = QAction("Single Step", self)
        # single_step_action.setCheckable(True)
        # simulation_menu.addAction(single_step_action)
        # step_action = QAction("Step", self)
        # step_action.setShortcut("Ctrl+T")
        # simulation_menu.addAction(step_action)
        # stop_action = QAction("Stop", self)
        # stop_action.setShortcut("Ctrl+Y")
        # simulation_menu.addAction(stop_action)

        edit_menu = self.menuBar().addMenu("Edit")
        cut_action = QAction("Cut", self)
        cut_action.setShortcut(self.settings.get_states_cut_shortcut())
        self.settings.states_cut_shortcut_changed.connect(cut_action.setShortcut)
        edit_menu.addAction(cut_action)

        copy_action = QAction("Copy", self)
        copy_action.setShortcut(self.settings.get_states_copy_shortcut())
        self.settings.states_copy_shortcut_changed.connect(copy_action.setShortcut)
        edit_menu.addAction(copy_action)

        paste_action = QAction("Paste", self)
        paste_action.setShortcut(self.settings.get_states_paste_shortcut())
        self.settings.states_paste_shortcut_changed.connect(paste_action.setShortcut)
        edit_menu.addAction(paste_action)

        delete_action = QAction("Delete", self)
        delete_action.setShortcut(self.settings.get_states_delete_shortcut())
        self.settings.states_delete_shortcut_changed.connect(delete_action.setShortcut)
        edit_menu.addAction(delete_action)

        view_menu = self.menuBar().addMenu("View")
        zoom_in_action = QAction("Zoom in", self)
        zoom_in_action.setShortcut(self.settings.get_zoom_in_shortcut())  # QKeySequence.ZoomIn
        self.settings.zoom_in_shortcut_changed.connect(zoom_in_action.setShortcut)
        zoom_in_action.triggered.connect(lambda: self.user_panel.grid_view.zoom(1.1))
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom out", self)
        zoom_out_action.setShortcut(self.settings.get_zoom_out_shortcut())  # QKeySequence.ZoomOut
        self.settings.zoom_out_shortcut_changed.connect(zoom_out_action.setShortcut)
        zoom_out_action.triggered.connect(lambda: self.user_panel.grid_view.zoom(0.9))
        view_menu.addAction(zoom_out_action)

        restore_default_zoom_action = QAction("Restore default zoom", self)
        restore_default_zoom_action.setShortcut("Ctrl+0")
        restore_default_zoom_action.triggered.connect(self.user_panel.grid_view.reset_zoom)
        view_menu.addAction(restore_default_zoom_action)
        # status_bar_action = QAction("Status bar", self)
        # status_bar_action.setCheckable(True)
        # view_menu.addAction(status_bar_action)

        help_menu = self.menuBar().addMenu("Help")
        report_action = QAction("Report Issue", self)
        report_action.triggered.connect(self.report_issue)
        help_menu.addAction(report_action)
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        # settings_menu = self.menuBar().addMenu("Settings")
        # settings_action = QAction("Open Settings", self)
        # settings_action.triggered.connect(self.switch_panel)
        # settings_menu.addAction(settings_action)
        self.settings_button.setObjectName("settings_button")
        self.settings_button.setFixedSize(22, 22)
        self.settings_button.clicked.connect(self.switch_panel)
        self.menuBar().setCornerWidget(self.settings_button, Qt.Corner.TopRightCorner)

        self.menuBar().setFixedHeight(30)

        # self.settings.hide_titlebar_changed.connect(self.update_hide_titlebar)
        # self.update_hide_titlebar(self.settings.get_hide_titlebar())
        # self.settings.stay_on_top_changed.connect(self.update_stay_on_top)
        # self.update_stay_on_top(self.settings.get_stay_on_top())
        self.update_recent_files_menu()
        self.settings.recent_files_changed.connect(lambda _: self.update_recent_files_menu())

    def update_hide_titlebar(self, flag: bool) -> None:
        if self.isVisible():
            do_show = True
        else:
            do_show = False
        if flag:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        else:
            self.setWindowFlags(
                self.windowFlags() & ~Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowSystemMenuHint | Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowMaximizeButtonHint)
        if do_show:
            self.show()

    def update_stay_on_top(self, flag: bool) -> None:
        if self.isVisible():
            do_show = True
        else:
            do_show = False
        if flag:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(
                self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowSystemMenuHint | Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowMaximizeButtonHint)
        if do_show:
            self.show()

    def setStyleSheet(self, styleSheet, /):
        super().setStyleSheet(styleSheet)
        self.user_panel.grid_view.reset_cache()

    def update_recent_files_menu(self):
        """Refreshes the Open Recent menu with updated file list."""
        self.recent_menu.clear()
        recent_files = self.settings.get_recent_files()
        if not recent_files:
            self.recent_menu.addAction("No Recent Files").setEnabled(False)
        else:
            for file in recent_files:
                action = QAction(os.path.basename(file), self)
                action.triggered.connect(lambda checked, f=file: (
                    self.user_panel.grid_view.empty_scene(),
                    self.open_file_signal.emit(f)
                ))
                self.recent_menu.addAction(action)

    def get_automaton_type(self) -> str:
        return self.automaton_type

    def open_file(self):
        print("DE", self.user_panel.grid_view.scene().items())
        if self.file_path == "" and self.user_panel.grid_view.scene().items():
            save_selection = self.button_popup(title='Unsaved changes',
                                                text='Do you want to save your changes? \nYour changes will be lost if you don´t save them.',
                                                description='',
                                                icon='Warning',
                                                buttons=['Save', 'Don´t save', 'Cancel'],
                                                default_button='Save')
            if save_selection[0] == 'Save':
                self.save_file()
            elif save_selection[0] == 'Don´t save':
                pass
            elif save_selection[0] == 'Cancel':
                return
        file_dialog = QFileDialog(self)
        self.file_path, _ = file_dialog.getOpenFileName(
            self, "Open File", filter="JSON (*.json);;YAML (*.yml, *.yaml);;Binary (*.au);;All Files (*)"
        )
        if self.file_path:
            self.user_panel.grid_view.empty_scene()
            self.open_file_signal.emit(self.file_path)
            QMessageBox.information(self, "File Opened", f"You opened: {self.file_path}")

    def save_file(self):
        if self.file_path != "":
            self.save_file_signal.emit(self.file_path)
        else:
            self.save_file_as()

    def save_file_as(self):
        file_dialog = QFileDialog(self)
        self.file_path, _ = file_dialog.getSaveFileName(
            self, "Save File", filter="JSON (*.json);;YAML (*.yml, *.yaml);;Binary (*.au)")
        if self.file_path:
            self.save_file_signal.emit(self.file_path)
            QMessageBox.information(self, "File Saved", f"File saved to: {self.file_path}")

    def show_about(self):
        QMessageBox.about(self, "[N.E.F.S] About", "N.E.F.S' Simulator.\nThe meaning of this abbreviation has long been lost to time. Rumor has it though, that it stands for the names of the creators and something about glucose.")

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
        height = self.height() - menubar_bottom  # - self.statusBar().height()
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

    def set_font(self, font_str: str) -> None:
        font = QFont(font_str)
        self.setFont(font)
        for child in self.findChildren(QWidget):
            child.setFont(font)
        self.update()
        self.repaint()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.switch_panel()

    def internal_obj(self) -> QMainWindow:
        return self

    def resizeEvent(self, event):
        self.reload_panels()

    def show_automaton_selection(self) -> bool:
        dialog = AutomatonSelectionDialog(self.user_panel.grid_view, self)

        overlay = QWidget(self)
        overlay.setGeometry(self.rect())
        overlay.setStyleSheet("background-color: rgba(0, 0, 0, 150);")
        overlay.show()

        result = dialog.exec()

        overlay.deleteLater()

        if result == QDialog.DialogCode.Accepted:
            self.automaton_type = dialog.selected_type
            return True
        return False

    def start(self) -> None:
        self.show()
        self.raise_()

        print(bool(self.ui_automaton.get_states()) and bool(self.ui_automaton.get_transitions()))
        if not (bool(self.ui_automaton.get_states()) and bool(self.ui_automaton.get_transitions())):
            if not self.show_automaton_selection():
                self.close()

    def close(self) -> None:
        QMainWindow.close(self)
