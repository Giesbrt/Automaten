"""Panels of the gui"""
import os

from PySide6.QtWidgets import (QWidget, QListWidget, QStackedLayout, QFrame, QSpacerItem, QSizePolicy, QLabel,
                               QFormLayout, QLineEdit, QFontComboBox, QKeySequenceEdit, QCheckBox,
                               QSlider, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
                               QHBoxLayout, QColorDialog, QComboBox, QMenu, QSpinBox, QDoubleSpinBox)
from PySide6.QtCore import Qt, QPropertyAnimation, QRect, QLocale, Signal, QParallelAnimationGroup, QTimer
from PySide6.QtGui import QColor, QIcon, QPen, QKeySequence
from automaton.base.QAutomatonInputWidget import QAutomatonInputOutput

from aplustools.io.qtquick import QNoSpacingBoxLayout, QBoxDirection, QQuickBoxLayout

from pyside import QFlowLayout
from storage import AppSettings
from utils.IOManager import IOManager

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts


class Panel(QWidget):
    """Baseclass for all Panels"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)


class StateMenu(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAutoFillBackground(True)

        # self.singleton_observer = SingletonObserver()

        self.visible: bool = False
        self.state: 'StateItem' | None = None
        self.token_list: _ty.List[str] | None = None
        self.selected_color: QColor = QColor(52, 152, 219)

        main_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        header_layout: QHBoxLayout = QHBoxLayout()
        self.close_button = QPushButton("✕", self)
        self.close_button.setFixedSize(24, 24)
        self.close_button.clicked.connect(lambda: self.parentWidget().toggle_condition_edit_menu(False))

        self.title_label: QLabel = QLabel("State Management", self)
        # self.title_label.setStyleSheet("font-weight: bold; font-size: 16px;")

        header_layout.addWidget(self.close_button, alignment=Qt.AlignmentFlag.AlignLeft)
        header_layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignLeft)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        form_layout: QFormLayout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setHorizontalSpacing(10)
        form_layout.setVerticalSpacing(8)

        self.name_input: QLineEdit = QLineEdit(self)
        self.name_input.setPlaceholderText("State name")

        self.color_button: QPushButton = QPushButton("Choose Color", self)
        self.color_button.clicked.connect(self.open_color_dialog)
        self.color_button.setStyleSheet(f"background-color: {self.selected_color.name()}; color: #cb2821;")

        self.size_input: QSlider = QSlider(Qt.Orientation.Horizontal, self)
        self.size_input.setRange(100, 450)
        self.size_input.setValue(100)

        self.type_input: QComboBox = QComboBox(self)
        self.type_input.addItems(["Default", "Start", "End"])
        self.type_input.currentTextChanged.connect(self.change_state_type)

        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Color:", self.color_button)
        form_layout.addRow("Size:", self.size_input)
        form_layout.addRow("Type:", self.type_input)

        main_layout.addLayout(form_layout)

        self.transitions_table: QTableWidget = QTableWidget(self)
        self.transitions_table.setColumnCount(2)
        self.transitions_table.setHorizontalHeaderLabels(["From-To", "Condition"])
        self.transitions_table.horizontalHeader().setStretchLastSection(True)
        self.transitions_table.verticalHeader().setVisible(False)
        self.transitions_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.transitions_table.setMinimumHeight(120)
        self.transitions_table.currentItemChanged.connect(self.on_current_item_changed)
        main_layout.addWidget(self.transitions_table)

        self.setLayout(main_layout)

    def open_color_dialog(self):
        color: QColor = QColorDialog.getColor(initial=self.selected_color, parent=self, title="Choose a color")
        if color.isValid():
            self.selected_color = color
            self.color_button.setStyleSheet(f"background-color: {color.name()}; color: #000;")
            if self.state is not None:
                self.state.set_color(color)

    def set_state(self, state: 'StateItem') -> None:
        self.state: 'StateItem' = state
        self.set_parameters()

    def set_parameters(self):
        self.name_input.setText(self.state.label.toPlainText())
        searched_color: QColor = self.state.get_ui_state().get_colour()
        self.color_button.setStyleSheet(f'background-color: {QColor(searched_color).name()}; color: #000;')
        self.size_input.setValue(self.state.get_size())
        self.type_input.setCurrentText(self.state.get_type().capitalize())

        transitions = self.state.connected_transitions
        self.transitions_table.setRowCount(len(transitions))
        for i, transition in enumerate(transitions):
            target_item: QTableWidgetItem = QTableWidgetItem(
                f'{transition.get_ui_transition().get_from_state().get_display_text()} - {transition.get_ui_transition().get_to_state().get_display_text()}')
            target_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            target_item.setData(Qt.ItemDataRole.UserRole, transition)

            # token_list = self.singleton_observer.get('token_lists')
            condition_edit: QComboBox = QComboBox()
            # condition_edit.addItems(token_list[0] if token_list else [])
            # condition_edit.setItemData(Qt.ItemDataRole.UserRole, transition)

            self.transitions_table.setItem(i, 0, target_item)
            self.transitions_table.setCellWidget(i, 1, condition_edit)

    def add_row_fixed_width(self, name: str, widget: QWidget) -> None:
        label = QLabel(name, self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFixedWidth(min(50, 100))
        self.layout.addRow(label, widget)

    def change_state_type(self):
        state_type: _ty.Literal['default', 'start', 'end'] = self.type_input.currentText().lower()
        # if state_type == 'start':
        #     self.singleton_observer.set('start_state', self.state.get_ui_state())
        self.state.set_state_type(state_type)

    def on_current_item_changed(self, current: QTableWidgetItem | QComboBox,
                                previous: QTableWidgetItem | QComboBox | None) -> None:
        if previous:
            previous.data(Qt.ItemDataRole.UserRole).setPen(QPen(QColor('black'), 4))
        current.data(Qt.ItemDataRole.UserRole).setPen(QPen(QColor('red'), 4))

    def connect_methods(self) -> None:
        self.name_input.textEdited.connect(self.state.set_display_text)
        self.size_input.valueChanged.connect(self.state.set_size)

    def disconnect_methods(self) -> None:
        self.name_input.textEdited.disconnect()
        self.size_input.valueChanged.disconnect()


class ControlMenu(QFrame):
    def __init__(self, grid_view: 'AutomatonInteractiveGridView', parent=None):
        super().__init__(parent)
        # self.singleton_observer = SingletonObserver()
        # self.singleton_observer.subscribe('token_lists', self.update_token_lists)

        self.grid_view = grid_view
        self.token_lists: _ty.Tuple[_ty.List[str], _ty.List[str]] = [[], []]

        self.init_ui()
        self.adjustSize()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        main_layout.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        self.play_button = QPushButton(self)
        self.stop_button = QPushButton(self)
        self.stop_button.setEnabled(False)
        self.next_button = QPushButton(self)

        self.token_list_box = QComboBox(self)
        self.token_list_box.setEditable(True)
        self.token_list_box.lineEdit().returnPressed.connect(self.add_token)
        self.token_list_box.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.token_list_box.customContextMenuRequested.connect(self.show_context_menu)

        button_layout.addWidget(self.play_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.next_button)
        button_layout.addWidget(self.token_list_box)

        main_layout.addLayout(button_layout)
        main_layout.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.setLayout(main_layout)

        # self.singleton_observer.set('token_lists', self.token_lists)

    def show_context_menu(self, pos):
        """Zeigt das Kontextmenü bei Rechtsklick"""
        menu = QMenu(self)
        delete_action = menu.addAction("Ausgewähltes Element löschen")
        action = menu.exec_(self.token_list_box.mapToGlobal(pos))

        if action == delete_action:
            self.remove_token(self.token_list_box.currentText().strip(), self.token_list_box.currentIndex())

    def add_token(self):
        token = self.token_list_box.currentText().strip()
        if token.isalnum():
            if not token in self.token_lists[0]:
                self.token_list_box.addItem(token)
            QTimer.singleShot(0, lambda: self.token_list_box.setCurrentText(''))
            self.token_lists[0].append(token)
            # self.singleton_observer.set('token_lists', self.token_lists)
        else:
            IOManager().warning('No whitespace or special characters allowed!', '', True, False)

    def remove_token(self, token, token_index: int = None):
        self.token_list_box.removeItem(token_index)
        self.token_lists[0].remove(token)

        # self.singleton_observer.set('token_lists', self.token_lists)

    def update_token_lists(self, token_lists: _ty.List[_ty.List[str]]):
        self.token_lists = token_lists
        self.token_list_box.clear()
        self.token_list_box.addItems(token_lists[0])

    """def handle_automaton_changed(self, event: 'AutomatonEvent'):
        if event.is_loaded:
            self.token_lists = event.token_list_box
            self.update_token_list(self.token_lists)
        else:
            self.token_lists = [[], []]
            self.update_token_list(self.token_lists)"""


class UserPanel(Panel):
    """The main panel to be shown"""
    def __init__(self, ui_automaton: 'UiAutomaton', parent: QWidget | None = None) -> None:
        super().__init__(parent)
        from ._grids import AutomatonInteractiveGridView
        main_layout = QNoSpacingBoxLayout(QBoxDirection.TopToBottom, apply_layout_to=self)

        self.grid_view = AutomatonInteractiveGridView(ui_automaton)  # Get values from settings
        main_layout.addWidget(self.grid_view)

        # Info Menu
        self.info_menu_button = QPushButton(self)
        self.info_menu_button.setFixedSize(40, 40)
        self.info_menu = QFrame(self)
        self.info_menu.setFrameShape(QFrame.Shape.StyledPanel)
        self.info_menu.setAutoFillBackground(True)
        self.info_menu_animation = QPropertyAnimation(self.info_menu, b'geometry')
        self.info_menu_animation.setDuration(500)

        # Input/Output
        self.input_frame: QFrame = QFrame(self)
        self.input_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.input_frame_layout = QNoSpacingBoxLayout(QBoxDirection.TopToBottom)
        self.input_frame.setLayout(self.input_frame_layout)
        self.input_widget: QAutomatonInputOutput | None = None
        top_layout = QQuickBoxLayout(QBoxDirection.RightToLeft)
        self.hide_button = QPushButton("Show Input/Output")
        top_layout.addWidget(self.hide_button)
        self.input_frame_layout.addLayout(top_layout)

        # Control Menu
        self.control_menu = ControlMenu(self.grid_view, self)
        self.control_menu_animation = QPropertyAnimation(self.control_menu, b'geometry')
        self.control_menu_animation.setDuration(500)

        # Condition Edit Menu
        self.state_menu = StateMenu(self)
        self.state_menu_animation = QPropertyAnimation(self.state_menu, b'geometry')
        self.state_menu_animation.setDuration(500)

        # Connect signals
        self.info_menu_animation.valueChanged.connect(self.side_menu_animation_value_changed)  # Menu
        self.info_menu_button.clicked.connect(self.toggle_side_menu)  # Menu
        self.hide_button.clicked.connect(self.toggle_hide_input)

        # TODO: SETTINGS
        # - Automaton loader settings

    def setShowScrollbars(self, flag: bool) -> None:
        if flag:
            policy = Qt.ScrollBarPolicy.ScrollBarAsNeeded
        else:
            policy = Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        self.grid_view.setVerticalScrollBarPolicy(policy)
        self.grid_view.setHorizontalScrollBarPolicy(policy)

    def setAutoShowInfoMenu(self, flag: bool) -> None:
        self.auto_show_info_menu = flag

    #def setStartingZoomLevel(self):

    def toggle_hide_input(self):
        if self.input_widget is None:
            return
        if self.input_widget.isVisible():
            self.input_widget.hide()
            self.input_frame.setFixedHeight(self.hide_button.height() + 20)
            self.hide_button.setText("Show Input/Output")
        else:
            self.input_widget.show()
            self.input_frame.setFixedHeight(self.input_widget.sizeHint().height() + self.hide_button.height())
            self.hide_button.setText("Hide Input/Output")

    def position_input_widget(self, input_widget: _ty.Type[QAutomatonInputOutput]):
        self.input_widget = input_widget(parent=self)
        self.input_frame.layout().addWidget(self.input_widget)
        #self.input_widget.raise_()
        #if True:  # Disabled
        #    return
        # print(input_widget.x(), input_widget.y(), input_widget.width(), input_widget.height())

        # width = 200
        # height = 100
        # x = self.width() - width
        # y = self.height()
        #
        # # Ändere die Geometrie des Widgets
        # self.input_widget.setGeometry(x, y, width, height)
        # print(self.input_widget.x(), self.input_widget.y(), self.input_widget.width(), self.input_widget.height())
        # self.layout().addWidget(input_widget)
        # input_widget.repaint()


    def set_token_list(self, token_list: _ty.List[str]):
        self.token_list = token_list

    def get_token_list(self) -> _ty.List[str]:
        return self.token_list

    def update_menu_button_position(self, preset_value: int | None = None):
        if not preset_value:
            preset_value = self.info_menu.x()
        self.info_menu_button.move(preset_value + self.info_menu.width(), 20)

    def side_menu_animation_value_changed(self, value: QRect):
        self.update_menu_button_position(value.x())

    def toggle_side_menu(self):
        width = max(200, int(self.width() / 4))
        height = self.height()

        if self.info_menu.x() < 0:
            start_value = QRect(-width, 0, width, height)
            end_value = QRect(1, 0, width, height)
        else:
            start_value = QRect(1, 0, width, height)
            end_value = QRect(-width, 0, width, height)

        self.info_menu_animation.setStartValue(start_value)
        self.info_menu_animation.setEndValue(end_value)
        self.info_menu_animation.start()

    def toggle_condition_edit_menu(self, to_state: bool) -> None:
        width = min(300, int(self.width() / 4))
        print("WIDTH", width)
        height = self.height()
        c_menu_width = self.control_menu.width()
        c_menu_height = self.control_menu.height()
        self.state_menu.visible = not self.state_menu.visible

        if to_state:
            state_start = QRect(self.width(), 0, width, height)
            state_end = QRect(self.width() - width, 0, width, height)
            control_start = QRect(self.width() - width - 10, 10, width, c_menu_height)
            control_end = QRect(self.width() - width - self.state_menu.width() - 10, 10, width,
                                c_menu_height)
        else:
            state_start = QRect(self.width() - width, 0, width, height)
            state_end = QRect(self.width(), 0, width, height)
            control_start = QRect(self.width() - width - self.state_menu.width() - 10, 10, width,
                                  c_menu_height)
            control_end = QRect(self.width() - width - 10, 10, width, c_menu_height)

        self.state_menu_animation.setStartValue(state_start)
        self.state_menu_animation.setEndValue(state_end)
        self.control_menu_animation.setStartValue(control_start)
        self.control_menu_animation.setEndValue(control_end)

        animation_group = QParallelAnimationGroup(self)
        animation_group.addAnimation(self.state_menu_animation)
        animation_group.addAnimation(self.control_menu_animation)
        animation_group.start()

    # Window Methods
    def resizeEvent(self, event):
        height = self.height()
        width = max(200, int(self.width() / 4))
        # self.state_menu.setGeometry(self.width(), 0, 300, self.height())

        if self.input_widget is not None:
            # Ändere die Geometrie des Widgets
            width = max(200, min(300, int(self.width() / 4)))
            self.input_frame.setGeometry(self.width() - width - 15, self.control_menu.height() + 10, width, self.input_widget.sizeHint().height() + self.hide_button.height())
            self.control_menu.setFixedWidth(width)
        else:
            self.input_frame.setGeometry(self.width() - width - 15, self.control_menu.height() + 10, width, self.hide_button.height() + 20)

        """if self.info_menu.x() == 0 and not self.auto_show_info_menu:
            self.info_menu.setGeometry(-width, 0, width, height)
            self.info_menu_button.move(width + 40, 20)  # Update the position of the menu button"""

        if self.info_menu.x() < 0:
            self.info_menu.setGeometry(-width, 0, width, height)
            self.info_menu_button.move(width + 40, 20)  # Update the position of the menu button
        else:
            self.info_menu.setGeometry(1, 0, width, height)
            self.info_menu_button.move(40, 20)  # Update the position of the menu button
        if self.state_menu.visible:
            self.state_menu.setGeometry(self.width() - width, 0, width, height)
        else:
            self.state_menu.setGeometry(self.width(), 0, width, height)
        if self.state_menu.visible:
            self.control_menu.setGeometry(self.width() - self.control_menu.width() - self.state_menu.width() - 20, 5,
                                          self.control_menu.width(), self.control_menu.height())
        else:
            self.control_menu.setGeometry(self.width() - self.control_menu.width() - 15, 5, self.control_menu.width(),
                                          self.control_menu.height())
        self.update_menu_button_position()
        # self.settings_button.move(self.width() - 60, 100)

        super().resizeEvent(event)


class LanguageDropdown(QComboBox):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)
        # Get available locales
        locales = QLocale.matchingLocales(QLocale.AnyLanguage, QLocale.AnyScript, QLocale.AnyCountry)

        # Create a set to store unique language names
        unique_languages = {}

        for locale in locales:
            language_name = locale.nativeLanguageName().capitalize().strip()

            if language_name and language_name not in unique_languages:
                unique_languages[language_name] = locale  # Store the first occurrence

        # Sort languages alphabetically
        sorted_languages = sorted(unique_languages.items(), key=lambda x: x[0])

        # Populate the combo box
        for name, locale in sorted_languages:
            self.addItem(name, locale)


class PresetSlider(QFrame):
    preset_changed = Signal(str)

    def __init__(self, presets: list[str], preset_values: dict[str, str], parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self._layout: QHBoxLayout = QHBoxLayout(self)
        self._layout.setSpacing(2)
        self._layout.setContentsMargins(5, 5, 5, 5)

        self._preset_buttons: dict[str, QPushButton] = {}
        self._presets: list[str] = presets
        self._preset_values: dict[str, str] = preset_values
        self._last_button: str | None = None

        for i, preset in enumerate(self._presets):
            btn = QPushButton(preset)
            btn.setCheckable(True)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            btn.setObjectName("preset_button")
            btn.clicked.connect(lambda checked, p=preset: self._set_preset(p, True))
            self._layout.addWidget(btn)
            self._preset_buttons[preset] = btn

    def _set_preset(self, preset: str, do_signal: bool) -> None:
        if self._last_button is not None and self._last_button == preset:
            self._preset_buttons[preset].setChecked(True)
            return None
        self._last_button = preset
        for btn in self._preset_buttons.values():
            btn.setChecked(False)
        self._preset_buttons[preset].setChecked(True)

        update_rate = self._preset_values[preset]
        if not do_signal:
            return None
        self.preset_changed.emit(update_rate)

    def set_preset(self, preset: str) -> None:
        self._set_preset(preset, False)


class SettingsPanel(Panel):
    """The settings panel"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setLayout(QQuickBoxLayout(QBoxDirection.TopToBottom))

        self.settings = AppSettings()

        # Main content layout
        main_content = QQuickBoxLayout(QBoxDirection.LeftToRight)
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("font-size: 14pt;")
        self.list_widget.setFixedWidth(200)
        self.list_widget.addItems(["General", "Design", "Performance", "Security", "Advanced"])
        main_content.addWidget(self.list_widget)

        # Stacked layout for settings pages
        self.stacked_layout = QStackedLayout(self)

        # Create pages with titles and vertical layouts (slots)
        # [Reset to Defaults on every page]
        self.general_panel = self.create_general_page()
        self.design_panel = self.create_design_page()
        self.performance_panel = self.create_performance_page()
        self.security_panel = self.create_security_page()
        self.advanced_panel = self.create_advanced_page()

        main_content.addLayout(self.stacked_layout)
        self.layout().addLayout(main_content)

    def create_general_page(self) -> QWidget:
        general_panel = QWidget()
        layout = QQuickBoxLayout(QBoxDirection.TopToBottom, apply_layout_to=general_panel)

        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        title_label = QLabel("General")
        title_label.setStyleSheet("font-size: 18pt;")
        layout.addWidget(title_label)

        rows: list[tuple[str, QWidget | None]] = []

        self.language_dropdown = LanguageDropdown()
        rows.append(("Language and Localization", self.language_dropdown))

        rows.append(("Shortcuts: ", None))
        shortcuts_frame = QFrame()
        sc_frame = QQuickBoxLayout(QBoxDirection.TopToBottom, 4, (9, 0, 0, 0), apply_layout_to=shortcuts_frame)
        shortcuts_layout = QFlowLayout()
        sc_frame.addLayout(shortcuts_layout)

        shortcuts: dict[str, str] = {
            "file_open": self.settings.get_file_open_shortcut(),
            "file_save": self.settings.get_file_save_shortcut(),
            "file_close": self.settings.get_file_close_shortcut(),
            "simulation_start": self.settings.get_simulation_start_shortcut(),
            "simulation_step": self.settings.get_simulation_step_shortcut(),
            "simulation_halt": self.settings.get_simulation_halt_shortcut(),
            "simulation_end": self.settings.get_simulation_end_shortcut(),
            "states_cut": self.settings.get_states_cut_shortcut(),
            "states_copy": self.settings.get_states_copy_shortcut(),
            "states_paste": self.settings.get_states_paste_shortcut(),
        }
        shortcut_widgets: list[tuple[str, QKeySequenceEdit, QCheckBox]] = []

        def _create_lambda(name: str, shortcut_key_sequence_edit: QKeySequenceEdit):
            return lambda: (
                shortcut_key_sequence_edit.setKeySequence(QKeySequence("")),
                shortcut_key_sequence_edit.setEnabled(not shortcut_key_sequence_edit.isEnabled()),
                getattr(self.settings, f"set_{name}_shortcut")("")
            )
        def _create_lambda_2(name: str, shortcut_key_sequence_edit: QKeySequenceEdit):
            return lambda: (
                getattr(self.settings, f"set_{name}_shortcut")(shortcut_key_sequence_edit.keySequence().toString())
            )

        for name, current_shortcut in shortcuts.items():
            formatted_name = name.replace("_", " ").title()
            shortcut_frame = QFrame()
            shortcut_layout = QQuickBoxLayout(QBoxDirection.LeftToRight, 9, (0, 0, 0, 0),
                                              apply_layout_to=shortcut_frame)
            shortcut_layout.addWidget(QLabel(f"{formatted_name}: "))
            shortcut_key_sequence_edit = QKeySequenceEdit(QKeySequence(current_shortcut), parent=self, maximumSequenceLength=1)
            shortcut_key_sequence_edit.editingFinished.connect(_create_lambda_2(name, shortcut_key_sequence_edit))
            shortcut_layout.addWidget(shortcut_key_sequence_edit)
            shortcut_checkbox = QCheckBox(parent=self)
            shortcut_checkbox.setChecked(True)
            shortcut_checkbox.checkStateChanged.connect(_create_lambda(name, shortcut_key_sequence_edit))
            if current_shortcut == "":
                shortcut_checkbox.setChecked(False)
            shortcut_layout.addWidget(shortcut_checkbox)
            shortcut_widgets.append((name, shortcut_key_sequence_edit, shortcut_checkbox))
            shortcuts_layout.addWidget(shortcut_frame)

        rows.append(("", shortcuts_frame))

        update_frame = QFrame()
        update_layout = QQuickBoxLayout(QBoxDirection.LeftToRight, 9, (0, 0, 0, 0), apply_layout_to=update_frame)
        check_for_update_button = QPushButton("Check for update")
        update_layout.addWidget(check_for_update_button)
        check_for_updates_checkbox = QCheckBox("AutoCheck")
        check_for_updates_checkbox.setChecked(self.settings.get_auto_check_for_updates())
        check_for_updates_checkbox.checkStateChanged.connect(lambda: (self.settings.set_auto_check_for_updates(check_for_updates_checkbox.isChecked())))
        update_layout.addWidget(check_for_updates_checkbox)
        rows.append(("Updates: ", update_frame))

        show_no_update_info_checkbox = QCheckBox()
        show_no_update_info_checkbox.setChecked(self.settings.get_show_no_update_info())
        show_no_update_info_checkbox.checkStateChanged.connect(lambda: (self.settings.set_show_no_update_info(show_no_update_info_checkbox.isChecked())))
        self.settings.show_no_update_info_changed.connect(show_no_update_info_checkbox.setChecked)
        rows.append(("Show no update info: ", show_no_update_info_checkbox))
        show_update_info_checkbox = QCheckBox()
        show_update_info_checkbox.setChecked(self.settings.get_show_update_info())
        show_update_info_checkbox.checkStateChanged.connect(lambda: (self.settings.set_show_update_info(show_update_info_checkbox.isChecked())))
        self.settings.show_update_info_changed.connect(show_update_info_checkbox.setChecked)
        rows.append(("Show update info: ", show_update_info_checkbox))
        show_update_timeout_checkbox = QCheckBox()
        show_update_timeout_checkbox.setChecked(self.settings.get_show_update_timeout())
        show_update_timeout_checkbox.checkStateChanged.connect(lambda: (self.settings.set_show_update_timeout(show_update_timeout_checkbox.isChecked())))
        self.settings.show_update_timeout_changed.connect(show_update_timeout_checkbox.setChecked)
        rows.append(("Show update timeout: ", show_update_timeout_checkbox))
        ask_to_reopen_last_file_checkbox = QCheckBox()
        ask_to_reopen_last_file_checkbox.setChecked(self.settings.get_ask_to_reopen_last_file())
        ask_to_reopen_last_file_checkbox.checkStateChanged.connect(lambda: (self.settings.set_ask_to_reopen_last_file(ask_to_reopen_last_file_checkbox.isChecked())))
        self.settings.ask_to_reopen_last_file_changed.connect(ask_to_reopen_last_file_checkbox.setChecked)
        rows.append(("Ask to reopen last file: ", ask_to_reopen_last_file_checkbox))
        auto_open_tutorial_tab_checkbox = QCheckBox()
        auto_open_tutorial_tab_checkbox.setChecked(self.settings.get_auto_open_tutorial_tab())
        auto_open_tutorial_tab_checkbox.checkStateChanged.connect(lambda: (self.settings.set_auto_open_tutorial_tab(auto_open_tutorial_tab_checkbox.isChecked())))
        rows.append(("Auto open tutorial tab: ", auto_open_tutorial_tab_checkbox))

        for name, widget in rows:
            frame = QFrame()
            frame_layout = QQuickBoxLayout(QBoxDirection.LeftToRight, 9, (9, 0, 0, 0))
            if name != "":
                frame_layout.addWidget(QLabel(name))
            if widget is not None:
                frame_layout.addWidget(widget)
            frame.setLayout(frame_layout)
            layout.addWidget(frame)
        return general_panel

    def create_design_page(self) -> QWidget:
        design_panel = QWidget()
        layout = QQuickBoxLayout(QBoxDirection.TopToBottom, apply_layout_to=design_panel)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        title_label = QLabel("Design")
        title_label.setStyleSheet("font-size: 18pt;")
        layout.addWidget(title_label)

        rows: list[tuple[str, QWidget | None]] = []

        self.window_icon_set_dropdown = QComboBox()
        base_icon_set_dir = os.path.join(os.getcwd(), "data", "assets", "app_icons")
        for sub in os.listdir(base_icon_set_dir):
            subpath = os.path.join(base_icon_set_dir, sub)
            if os.path.isdir(subpath):
                icon_path: str = os.path.join(subpath, "logo-nobg.png")
                if os.path.exists(icon_path):
                    name: str = os.path.basename(subpath)
                    self.window_icon_set_dropdown.addItem(QIcon(icon_path), name.title())
                    if name == "shelline":
                        self.window_icon_set_dropdown.setCurrentIndex(self.window_icon_set_dropdown.count() - 1)
        rows.append(("Window Icon: ", self.window_icon_set_dropdown))

        self.window_title_template_edit = QLineEdit("E.F.S $version$version_add $title [INDEV]")
        rows.append(("Window Title Template: ", self.window_title_template_edit))

        self.font_edit = QFontComboBox()
        rows.append(("Font: ", self.font_edit))

        rows.append(("Theming: ", None))
        theming_frame = QFrame()
        theming_layout = QQuickBoxLayout(QBoxDirection.TopToBottom, 9, (9, 0, 0, 0), apply_layout_to=theming_frame)
        light_layout = QQuickBoxLayout(QBoxDirection.LeftToRight, 9, (0, 0, 0, 0))
        light_layout.addWidget(QLabel("Light: "))
        self.light_theme_dropdown = QComboBox()
        self.light_style_dropdown = QComboBox()
        light_layout.addWidget(self.light_theme_dropdown, stretch=7)
        light_layout.addWidget(QLabel("/"))
        light_layout.addWidget(self.light_style_dropdown, stretch=5)
        theming_layout.addLayout(light_layout)

        dark_layout = QQuickBoxLayout(QBoxDirection.LeftToRight, 9, (0, 0, 0, 0))
        dark_layout.addWidget(QLabel("Dark: "))
        self.dark_theme_dropdown = QComboBox()
        self.dark_style_dropdown = QComboBox()
        dark_layout.addWidget(self.dark_theme_dropdown, stretch=7)
        dark_layout.addWidget(QLabel("/"))
        dark_layout.addWidget(self.dark_style_dropdown, stretch=5)
        theming_layout.addLayout(dark_layout)
        rows.append(("", theming_frame))

        self.state_bg_color_button: QPushButton = QPushButton("Choose Color", self)
        self.state_bg_color_button.clicked.connect(self.open_color_dialog)
        rows.append(("Default state background: ", self.state_bg_color_button))

        rows.append(("Hide scrollbars: ", QCheckBox()))

        for name, widget in rows:
            frame = QFrame()
            frame_layout = QQuickBoxLayout(QBoxDirection.LeftToRight, 9, (9, 0, 0, 0))
            if name != "":
                frame_layout.addWidget(QLabel(name))
            if widget is not None:
                frame_layout.addWidget(widget)
            frame.setLayout(frame_layout)
            layout.addWidget(frame)
        return design_panel

    def open_color_dialog(self):
        color: QColor = QColorDialog.getColor(initial=Qt.GlobalColor.white, parent=self, title="Choose a color")
        if color.isValid():
            self.selected_color = color

    def create_performance_page(self) -> QWidget:
        performance_panel = QWidget()
        layout = QQuickBoxLayout(QBoxDirection.TopToBottom, apply_layout_to=performance_panel)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        title_label = QLabel("Performance")
        title_label.setStyleSheet("font-size: 18pt;")
        layout.addWidget(title_label)

        rows: list[tuple[str, QWidget | None]] = []

        preset_slider = PresetSlider(["Low", "Medium", "High", "Ultra", "Custom"],
                                     {"Low": "Low", "Medium": "Medium", "High": "High", "Ultra": "Ultra", "Custom": "Custom"})
        preset_slider.set_preset("Low")
        preset_slider.preset_changed.connect(lambda v: print("Preset", v))
        rows.append(("", preset_slider))

        for name, widget in rows:
            frame = QFrame()
            frame_layout = QQuickBoxLayout(QBoxDirection.LeftToRight, 9, (9, 0, 0, 0))
            if name != "":
                frame_layout.addWidget(QLabel(name))
            if widget is not None:
                frame_layout.addWidget(widget)
            frame.setLayout(frame_layout)
            layout.addWidget(frame)
        return performance_panel

    def create_security_page(self) -> QWidget:
        security_panel = QWidget()
        layout = QQuickBoxLayout(QBoxDirection.TopToBottom, apply_layout_to=security_panel)

        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        title_label = QLabel("Security")
        title_label.setStyleSheet("font-size: 18pt;")
        layout.addWidget(title_label)

        rows: list[tuple[str, QWidget | None]] = []

        rows.append(("Warn of new plugins: ", QCheckBox()))
        auto_open_tutorial_tab = QCheckBox()
        auto_open_tutorial_tab.setChecked(False)
        auto_open_tutorial_tab.setEnabled(False)
        rows.append(("Run plugins in separate process (not as efficient): ", auto_open_tutorial_tab))
        rows.append(("Use safe file access: ", QCheckBox()))

        for name, widget in rows:
            frame = QFrame()
            frame_layout = QQuickBoxLayout(QBoxDirection.LeftToRight, 9, (9, 0, 0, 0))
            if name != "":
                frame_layout.addWidget(QLabel(name))
            if widget is not None:
                frame_layout.addWidget(widget)
            frame.setLayout(frame_layout)
            layout.addWidget(frame)
        return security_panel

    def create_advanced_page(self) -> QWidget:
        advanced_panel = QWidget()
        layout = QQuickBoxLayout(QBoxDirection.TopToBottom, apply_layout_to=advanced_panel)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        title_label = QLabel("Advanced")
        title_label.setStyleSheet("font-size: 18pt;")
        layout.addWidget(title_label)

        rows: list[tuple[str, QWidget | None]] = []

        rows.append(("Automaton testing cache: ", QPushButton("Clear")))
        rows.append(("Hide titlebar: ", QCheckBox()))
        rows.append(("Stay on top: ", QCheckBox()))
        rows.append(("Save window dimensions: ", QCheckBox()))
        rows.append(("Save window position: ", QCheckBox()))
        rows.append(("Update check request timeout: ", QDoubleSpinBox(decimals=1, minimum=0.0, maximum=10.0, singleStep=0.1, value=2.0)))
        rows.append(("Max timer tick handled events: ", QSpinBox(minimum=0, maximum=20, singleStep=1, value=5)))

        rows.append(("Developer Options: ", None))
        dev_ops_frame = QFrame()
        dev_ops_layout = QQuickBoxLayout(QBoxDirection.TopToBottom, 9, (9, 0, 0, 0), apply_layout_to=dev_ops_frame)
        logging_layout = QQuickBoxLayout(QBoxDirection.LeftToRight, 9, (0, 0, 0, 0))
        logging_layout.addWidget(QLabel("Logging mode: "))
        logging_layout.addWidget(QComboBox())
        dev_ops_layout.addLayout(logging_layout)
        dev_ops_layout.addWidget(QPushButton("Open logs folder"))
        dev_ops_layout.addWidget(QPushButton("Open config folder"))

        plugins_layout = QQuickBoxLayout(QBoxDirection.LeftToRight, 9, (0, 0, 0, 0))
        plugins_layout.addWidget(QLabel("Plugins: "))
        plugins_layout.addWidget(QPushButton("Load from disk"))
        load_from_github_button = QPushButton("Load from GitHub")
        load_from_github_button.setEnabled(False)
        plugins_layout.addWidget(load_from_github_button)
        dev_ops_layout.addLayout(plugins_layout)
        rows.append(("", dev_ops_frame))

        for name, widget in rows:
            frame = QFrame()
            frame_layout = QQuickBoxLayout(QBoxDirection.LeftToRight, 9, (9, 0, 0, 0))
            if name != "":
                frame_layout.addWidget(QLabel(name))
            if widget is not None:
                frame_layout.addWidget(widget)
            frame.setLayout(frame_layout)
            layout.addWidget(frame)
        return advanced_panel

    def create_settings_page(self, title: str, extra_widgets: list[QWidget] = None) -> QWidget:
        """Creates a settings page with a title and vertical layout."""
        page = QWidget()
        layout = QQuickBoxLayout(QBoxDirection.TopToBottom)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Add title
        title_label = QLabel(title)
        # title_label.setStyleSheet("font-size: 18pt;")
        layout.addWidget(title_label)

        # Add extra widgets if provided
        if extra_widgets:
            for widget in extra_widgets:
                frame = QFrame()
                # frame.setStyleSheet("""
                #     QFrame {
                #         border: 2px solid #00289E;
                #         border-radius: 8px;
                #         margin: 10px;
                #         padding: 10px;
                #         background-color: white;
                #     }
                # """)
                frame_layout = QQuickBoxLayout(QBoxDirection.TopToBottom)
                frame_layout.addWidget(widget)
                frame.setLayout(frame_layout)
                layout.addWidget(frame)

        page.setLayout(layout)
        return page

    def create_display_page_widgets(self) -> list[QWidget]:
        """Creates specific widgets for the display settings page."""
        widgets = []

        # App Icon setting
        app_icon_label = QLabel("App Icon:")
        app_icon_label.setStyleSheet("font-size: 14pt;")
        app_icon_input = QLineEdit()
        app_icon_input.setPlaceholderText("Enter app icon path or URL")
        app_icon_layout = QQuickBoxLayout(QBoxDirection.TopToBottom)
        app_icon_layout.addWidget(app_icon_label)
        app_icon_layout.addWidget(app_icon_input)

        app_icon_widget = QWidget()
        app_icon_widget.setLayout(app_icon_layout)
        widgets.append(app_icon_widget)

        # Item Scale setting
        item_scale_label = QLabel("Item Scale:")
        item_scale_label.setStyleSheet("font-size: 14pt;")
        item_scale_slider = QSlider(Qt.Orientation.Horizontal)
        item_scale_slider.setMinimum(1)
        item_scale_slider.setMaximum(100)
        item_scale_slider.setValue(50)  # Default value
        item_scale_layout = QQuickBoxLayout(QBoxDirection.TopToBottom)
        item_scale_layout.addWidget(item_scale_label)
        item_scale_layout.addWidget(item_scale_slider)

        item_scale_widget = QWidget()
        item_scale_widget.setLayout(item_scale_layout)
        widgets.append(item_scale_widget)

        return widgets

    def showEvent(self, event, /):
        # Add panels to the stacked layout
        self.stacked_layout.addWidget(self.general_panel)
        self.stacked_layout.addWidget(self.design_panel)
        self.stacked_layout.addWidget(self.performance_panel)
        self.stacked_layout.addWidget(self.security_panel)
        self.stacked_layout.addWidget(self.advanced_panel)
        self.list_widget.currentRowChanged.connect(self.stacked_layout.setCurrentIndex)
        self.list_widget.setCurrentRow(0)  # So an item is selected by default
