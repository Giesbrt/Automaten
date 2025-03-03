"""TBA"""
import os

from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QPushButton, QCheckBox, QWidget, QDialog, \
    QVBoxLayout, QLabel, QMenu
from PySide6.QtGui import QIcon, QAction, QDesktopServices, QFont, QColor, QPalette
from PySide6.QtCore import QRect, QSize, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QUrl, Qt, Signal

from aplustools.io.qtquick import QQuickMessageBox

from core.modules.abstractions import IMainWindow
from ._panels import UserPanel, SettingsPanel

# Standard typing imports for aps
import re as _re
import typing as _ty


class AutomatonSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0, 128))
        self.setAutoFillBackground(True)
        self.setPalette(palette)

        # self.singleton_observer = SingletonObserver()

        layout = QVBoxLayout(self)

        title = QLabel("Choose a Automatontype:")
        title.setStyleSheet("color: white; font-size: 18px;")
        layout.addWidget(title)

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

        widget = self.parent().ui_automaton.get_input_widget()
        self.parent().user_panel.position_input_widget(widget)

        self.accept()


class MainWindow(QMainWindow, IMainWindow):
    save_file_signal: Signal(str) = Signal(str)
    open_file_signal: Signal(str) = Signal(str)
    settings_changed = Signal(dict[str, dict[str, str]])

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
        self.recent_files = []
        super().__init__(parent=None)
        # self.statusBar().showMessage("Statusbar")

    def setup_gui(self, ui_automaton: 'UiAutomaton') -> None:
        self.ui_automaton = ui_automaton

        self.settings_button = QPushButton(parent=self)
        self.menu_bar = self.menuBar()
        self.user_panel = UserPanel(ui_automaton, parent=self)
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

        self.switch_panel_simple()  # So they are ordered correctly

        file_menu = self.menuBar().addMenu("File")
        new_action = QAction('New', self)
        new_action.triggered.connect(self.user_panel.grid_view.empty_scene)
        file_menu.addAction(new_action)
        open_action = QAction("Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        self.recent_menu = QMenu("Open Recent", self)
        file_menu.addMenu(self.recent_menu)
        self.update_recent_files_menu()
        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        save_action = QAction("Save as", self)
        # save_action.setShortcut("Ctrl+G")
        save_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_action)
        exit_action = QAction("Close", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
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
        cut_action.setShortcut("Ctrl+X")
        edit_menu.addAction(cut_action)
        copy_action = QAction("Copy", self)
        copy_action.setShortcut("Ctrl+C")
        edit_menu.addAction(copy_action)
        paste_action = QAction("Paste", self)
        paste_action.setShortcut("Ctrl+V")
        edit_menu.addAction(paste_action)

        view_menu = self.menuBar().addMenu("View")
        zoom_in_action = QAction("Zoom in", self)
        zoom_in_action.setShortcut("Ctrl++")  # QKeySequence.ZoomIn
        view_menu.addAction(zoom_in_action)
        zoom_out_action = QAction("Zoom out", self)
        zoom_out_action.setShortcut("Ctrl+-")  # QKeySequence.ZoomOut
        view_menu.addAction(zoom_out_action)
        restore_default_zoom_action = QAction("Restore default zoom", self)
        restore_default_zoom_action.setShortcut("Ctrl+0")
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

    def set_recently_opened_files(self, recently_opened_files: list[str]) -> None:
        self.recent_files = recently_opened_files

    def get_recently_opened_files(self) -> list[str]:
        return self.recent_files

    def update_recent_files_menu(self):
        """Refreshes the Open Recent menu with updated file list."""
        self.recent_menu.clear()
        print("RECENT", self.recent_files)
        if not self.recent_files:
            self.recent_menu.addAction("No Recent Files").setEnabled(False)
        else:
            for file in self.recent_files:
                action = QAction(os.path.basename(file), self)
                action.triggered.connect(lambda checked, f=file: self.open_recent_file(f))
                self.recent_menu.addAction(action)

    def get_automaton_type(self) -> str:
        return self.automaton_type

    def open_file(self):
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
        dialog = AutomatonSelectionDialog(self)

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

        # self.singleton_observer = SingletonObserver()
        # if not self.singleton_observer.get('is_loaded'):
        print(self.ui_automaton.get_states() and self.ui_automaton.get_transitions())
        if not (self.ui_automaton.get_states() and self.ui_automaton.get_transitions()):
            if not self.show_automaton_selection():
                self.close()

    def close(self) -> None:
        QMainWindow.close(self)
