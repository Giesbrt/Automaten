"""Panels of the gui"""
import logging
import os

from PySide6.QtWidgets import (QWidget, QListWidget, QStackedLayout, QFrame, QSpacerItem, QSizePolicy, QLabel,
                               QFormLayout, QLineEdit, QFontComboBox, QKeySequenceEdit, QCheckBox,
                               QSlider, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QScrollArea,
                               QHBoxLayout, QColorDialog, QComboBox, QMenu, QSpinBox, QDoubleSpinBox, QListWidgetItem)
from PySide6.QtCore import Qt, QPropertyAnimation, QRect, QLocale, Signal, QParallelAnimationGroup, QTimer
from PySide6.QtGui import QColor, QIcon, QPen, QKeySequence, QFont
from automaton.base.QAutomatonInputWidget import QAutomatonInputOutput

# from aplustools.io.qtquick import QNoSpacingBoxLayout, QBoxDirection, QQuickBoxLayout
# from aplustools.io.env import SystemTheme
from dancer.qt import QNoSpacingBoxLayout, QBoxDirection, QQuickBoxLayout
from dancer.system import SystemTheme

from automaton.base.QAutomatonInputWidget import QFlowLayout
from storage import AppSettings
# from utils.IOManager import IOManager
from dancer.io import IOManager
from painter import PainterStr

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts



class Panel(QWidget):
    """Baseclass for all Panels"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)


class StateMenu(QFrame):
    def __init__(self, ui_automaton, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAutoFillBackground(True)

        self.ui_automaton = ui_automaton

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
        # self.type_input.addItems(list(design_typ.values()))
        self.type_input.currentTextChanged.connect(self.change_state_type)

        self.settings = AppSettings()
        self.settings.automaton_type_changed.connect(lambda _: (
            self.type_input.clear(),
            self.type_input.addItems(list(self.ui_automaton.get_state_types_with_design().keys()))
        ))

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
        state_type: _ty.Literal['default', 'start', 'end'] = self.type_input.currentText()
        if self.state is not None:
            self.state.set_state_type(state_type)

    def on_current_item_changed(self, current: QTableWidgetItem | QComboBox, previous: QTableWidgetItem | QComboBox | None) -> None:
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

    token_update_signal: Signal = Signal(list)

    def __init__(self, grid_view: 'AutomatonInteractiveGridView', ui_automaton, parent=None):
        super().__init__(parent)

        self.grid_view = grid_view
        self.ui_automaton = ui_automaton
        self.token_lists: _ty.Tuple[_ty.List[str], _ty.List[str]] = [[], []]

        self.play_button = None
        self.stop_button = None
        self.next_button = None
        self.token_list_box = None

        self.setup_ui()
        self.adjustSize()

    def setup_ui(self):
        """Sets the UI-interface"""
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

    def show_context_menu(self, pos):
        """Shows the menu with a right-click"""
        menu = QMenu(self)
        delete_action = menu.addAction('Delete selected item')
        action = menu.exec_(self.token_list_box.mapToGlobal(pos))

        if action == delete_action:
            self.remove_token(self.token_list_box.currentText().strip(), self.token_list_box.currentIndex())

    def add_token(self) -> None:
        """Adds a token to the token_lists"""

        self.token_lists = self.ui_automaton.get_token_lists()
        token = self.token_list_box.currentText().strip()

        if token.isalnum():
            if not token in self.token_lists[0]:
                self.ui_automaton.get_token_lists()[0].append(token)
                token_lists = [self.ui_automaton.get_token_lists()[0] if v else self.ui_automaton.get_token_lists()[i] for i, v in enumerate(self.ui_automaton.get_is_changeable_token_list())]
                self.ui_automaton.set_token_lists(token_lists)
                self.grid_view.update_token_lists()
                self.token_update_signal.emit(self.ui_automaton.get_token_lists()[0])
            QTimer.singleShot(0, lambda: self.token_list_box.setCurrentText(''))
        else:
            IOManager().warning('No whitespace or special characters allowed!', '', True, False)

    def remove_token(self, token, token_index: int = None) -> None:
        """Remove a given token by its index

        :param token: The token to be deleted
        :param token_index: The token_index
        """
        self.token_list_box.removeItem(token_index)
        self.ui_automaton.set_token_lists(self.ui_automaton.get_token_lists()[0].remove(token))
        self.grid_view.update_token_lists()
        self.token_update_signal.emit(self.ui_automaton.get_token_lists()[0])

    def update_token_lists(self, token_lists: _ty.List[_ty.List[str]]) -> None:
        """Updates the token_list_box

        :param token_lists: The new token lists"""
        self.token_lists = token_lists
        self.token_list_box.clear()
        self.token_list_box.addItems(token_lists[0])


class UserPanel(Panel):
    """The main panel to be shown"""
    def __init__(self, ui_automaton: 'UiAutomaton', parent: QWidget | None = None) -> None:
        super().__init__(parent)
        from ._grids import AutomatonInteractiveGridView
        self.settings = AppSettings()
        main_layout = QNoSpacingBoxLayout(QBoxDirection.TopToBottom, apply_layout_to=self)

        self.grid_view = AutomatonInteractiveGridView(ui_automaton)  # Get values from settings
        self.setShowScrollbars(not self.settings.get_hide_scrollbars())
        self.settings.hide_scrollbars_changed.connect(lambda y: self.setShowScrollbars(not y))
        main_layout.addWidget(self.grid_view)

        # Info Menu
        self.info_menu_button = QPushButton(self)
        self.info_menu_button.setFixedSize(40, 40)
        self.info_menu = QFrame(self)
        self.info_menu.setFrameShape(QFrame.Shape.StyledPanel)
        self.info_menu.setAutoFillBackground(True)
        self.info_menu_animation = QPropertyAnimation(self.info_menu, b'geometry')
        self.info_menu_animation.setDuration(500)

        if not self.settings.get_auto_open_tutorial_tab():
            width = max(200, int(self.width() / 4))
            height = self.height()
            self.info_menu.setGeometry(-width, 0, width, height)

        self.info_menu_layout = QVBoxLayout(self.info_menu)
        search_label = QLabel("Suchen:", self.info_menu)
        search_field = QLineEdit(self.info_menu)
        search_field.textChanged.connect(self.search_items)
        self.info_menu_layout.addWidget(search_label)
        self.info_menu_layout.addWidget(search_field)
        self.items_list = QListWidget(self)
        self.populate_items_list()
        self.info_menu_layout.addWidget(self.items_list)

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
        # self.input_frame.setFixedHeight(28 + 20)

        self.input_frame_animation = QPropertyAnimation(self.input_frame, b'geometry')
        self.input_frame_animation.setDuration(500)

        # Control Menu
        self.control_menu = ControlMenu(self.grid_view, ui_automaton, self)
        self.control_menu_animation = QPropertyAnimation(self.control_menu, b'geometry')
        self.control_menu_animation.setDuration(500)

        # Condition Edit Menu
        self.state_menu = StateMenu(ui_automaton, self)
        self.state_menu_animation = QPropertyAnimation(self.state_menu, b'geometry')
        self.state_menu_animation.setDuration(500)

        # Connect signals
        self.info_menu_animation.valueChanged.connect(self.side_menu_animation_value_changed)  # Menu
        self.info_menu_button.clicked.connect(self.toggle_side_menu)  # Menu
        self.hide_button.clicked.connect(self.toggle_hide_input)

        if self.settings.get_auto_hide_input_widget():
            self.hide_input_ding = True
            self.input_frame.setFixedHeight(28 + 20)
            self.hide_button.setText("Show Input/Output")
        else:
            self.hide_input_ding = False

    def search_items(self, text):
        """Search items in the list"""
        for i in range(self.items_list.count()):
            item = self.items_list.item(i)
            widget = self.items_list.itemWidget(item)
            button = widget.findChild(QPushButton) if widget else None
            if button:
                title = button.text().split("▼")[0].strip()
                item.setHidden(text.lower() not in title.lower())

    def populate_items_list(self):
        """Populate the list with example items"""
        example_items = [
            {"title": "Zustand einfügen", "description": "Doppelklick auf die Oberfläche mit der linken Maustaste"},
            {"title": "Zustand anpassen", "description": "Klicke den anzupassenden Zustand an. Auf dem rechts aufgehendem Seiten Panel kannst du:\n- Name \n- Farbe und Größe ändern"},
            {"title": "Zustände verbinden", "description": "Klicke auf den grünen Punkt am Zustand den du verbinden möchtest. Klicke dann auf einer der Roten Punkte des zu verbinden Zustands."},
            {"title": "Design ändern", "description": "Gehe in die Settings (oben rechts) und klicke auf Design. Hier kannst du zwischen den zur Verfügung stehenden Designs wählen."},
            {"title": "Datei laden", "description": "Gehe auf File und wähle Open, oder benutze den Shortcut: Ctrl+O."},
            {"title": "Datei speichern", "description": "Gehe auf File und wähle Save, oder benutze den Shortcut: Ctrl+S."},
            {"title": "Schriftart ändern", "description": "Gehe in die Settings (oben rechts) und klicke auf Design. Wähle eine beliebige Schriftart aus."},
            {"title": "Zoom in/ out", "description": "Gehe auf View oder benutze die Shortcuts Ctrl++/ Ctrl--."},
            {"title": "Shortcuts ändern", "description": "Gehe in die Settings und in General können die Shorcuts geändert werden."},
            {"title": "Sartzustand", "description": "Auf den Zustand klicken der Startzustand werden soll, wähle bei Type im Seiten Panel: Start"},
            {"title": "Endzustand", "description": "Auf den Zustand klicken der Endzustand werden soll, wähle bei Type im Seitenpanel: End"},
        ]

        for item_data in example_items:
            title = item_data["title"]
            description = item_data["description"]
            widget = QWidget()
            layout = QVBoxLayout(widget)

            button = QPushButton(f"{title} ▼", self.info_menu)
            button.setCheckable(True)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            description_label = QLabel(description)
            description_label.setWordWrap(True)
            description_label.setVisible(False)

            # The maximum width of the label is adjusted to the menu here
            max_width = self.info_menu.width() - 20
            description_label.setMaximumWidth(max_width)

            layout.addWidget(button)
            layout.addWidget(description_label)
            widget.setLayout(layout)

            list_item = QListWidgetItem(self.items_list)
            list_item.setSizeHint(widget.sizeHint())
            self.items_list.addItem(list_item)
            self.items_list.setItemWidget(list_item, widget)

            # Link with Lambda corrected
            button.toggled.connect(lambda checked, label=description_label, item=list_item, w=widget: label.setVisible(checked) or item.setSizeHint(w.sizeHint()))

            # Saves the widget for later size updates
            list_item.widget_ref = widget


        def toggle_description(self, checked, label: QLabel, list_item: QListWidgetItem, widget: QWidget):
            """Beschreibung für ein einzelnes Item ein-/ausblenden"""
            label.setVisible(checked)
            list_item.setSizeHint(widget.sizeHint())


            button.toggled.connect(toggle_description)

            list_item = QListWidgetItem(self.items_list)
            list_item.setSizeHint(widget.sizeHint())
            self.items_list.addItem(list_item)
            self.items_list.setItemWidget(list_item, widget)

            # Saves the widget for later updating of the width
            list_item.widget_ref = widget

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

    def deposition_input_widget(self):
        self.input_frame.layout().removeWidget(self.input_widget)
        self.input_widget.deleteLater()
        self.input_widget = None

    def refresh_tokens_input_widget(self, token_lists: _ty.List[str] | None = None):
        if token_lists is None:
            token_lists = self.control_menu.token_lists[0]
        self.input_widget.set_input_tokens(token_lists)

    def position_input_widget(self, input_widget: _ty.Type[QAutomatonInputOutput]):
        if self.input_widget:
            return

        self.input_widget = input_widget(parent=self)
        self.input_frame.layout().addWidget(self.input_widget)

        self.control_menu.token_update_signal.connect(self.input_widget.set_input_tokens)
        # Update existing tokens
        self.refresh_tokens_input_widget()
        if self.hide_input_ding:
            self.hide_input_ding = False
            self.input_widget.hide()
        elif self.input_widget.isHidden():
            self.toggle_hide_input()

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
            end_value = QRect(0, 0, width, height)
        else:
            start_value = QRect(0, 0, width, height)
            end_value = QRect(-width, 0, width, height)

        self.info_menu_animation.setStartValue(start_value)
        self.info_menu_animation.setEndValue(end_value)
        self.info_menu_animation.start()

    def toggle_condition_edit_menu(self, to_state: bool) -> None:
        width = min(300, int(self.width() / 4))
        # print("WIDTH", width)
        height = self.height()
        c_menu_width = self.control_menu.width()
        c_menu_height = self.control_menu.height()
        self.state_menu.visible = not self.state_menu.visible

        if to_state:
            state_start = QRect(self.width(), 0, width, height)
            state_end = QRect(self.width() - width, 0, width, height)
            control_start = QRect(self.width() - width - 10, 10, width, c_menu_height)
            control_end = QRect(self.width() - width - self.state_menu.width() - 10, 10, width, c_menu_height)
            input_start = QRect(self.width() - width - 10, 20 + self.control_menu.height(), width, self.input_frame.height())
            input_end = QRect(self.width() - width - self.state_menu.width() - 10, 20 + self.control_menu.height(), width, self.input_frame.height())
        else:
            state_start = QRect(self.width() - width, 0, width, height)
            state_end = QRect(self.width(), 0, width, height)
            control_start = QRect(self.width() - width - self.state_menu.width() - 10, 10, width, c_menu_height)
            control_end = QRect(self.width() - width - 10, 10, width, c_menu_height)
            input_start = QRect(self.width() - width - self.state_menu.width() - 10, 20 + self.control_menu.height(), width, self.input_frame.height())
            input_end = QRect(self.width() - width - 10, 20 + self.control_menu.height(), width, self.input_frame.height())

        self.state_menu_animation.setStartValue(state_start)
        self.state_menu_animation.setEndValue(state_end)
        self.control_menu_animation.setStartValue(control_start)
        self.control_menu_animation.setEndValue(control_end)
        self.input_frame_animation.setStartValue(input_start)
        self.input_frame_animation.setEndValue(input_end)

        animation_group = QParallelAnimationGroup(self)
        animation_group.addAnimation(self.state_menu_animation)
        animation_group.addAnimation(self.control_menu_animation)
        animation_group.addAnimation(self.input_frame_animation)
        animation_group.start()

    # Window Methods
    def resizeEvent(self, event):
        """Wird aufgerufen, wenn das Fenster seine Größe ändert"""
        height = self.height()
        width = max(200, int(self.width() / 4))

        if self.input_widget is not None:
            width = max(200, min(300, int(self.width() / 4)))
            self.input_frame.setGeometry(self.width() - width - 15, self.control_menu.height() + 10, width, self.input_widget.sizeHint().height() + self.hide_button.height())
            self.control_menu.setFixedWidth(width)
        else:
            self.input_frame.setGeometry(self.width() - width - 15, self.control_menu.height() + 10, width, self.hide_button.height() + 20)

        if self.info_menu.x() < 0:
            self.info_menu.setGeometry(-width, 0, width, height)
            self.info_menu_button.move(width + 40, 20)
        else:
            self.info_menu.setGeometry(1, 0, width, height)
            self.info_menu_button.move(40, 20)

        if self.state_menu.visible:
            self.state_menu.setGeometry(self.width() - width, 0, width, height)
        else:
            self.state_menu.setGeometry(self.width(), 0, width, height)

        if self.state_menu.visible:
            self.control_menu.setGeometry(self.width() - self.control_menu.width() - self.state_menu.width() - 20, 5,
                                        self.control_menu.width(), self.control_menu.height())
        else:
            self.control_menu.setGeometry(self.width() - self.control_menu.width() - 15, 5,
                                        self.control_menu.width(), self.control_menu.height())

        self.update_menu_button_position()


        max_label_width = width - 20
        for i in range(self.items_list.count()):
            item = self.items_list.item(i)
            widget = self.items_list.itemWidget(item)
            if widget:
                label = widget.findChild(QLabel)
                if label:
                    label.setMaximumWidth(max_label_width)

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
    manual_update_check = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setLayout(QQuickBoxLayout(QBoxDirection.TopToBottom))

        self.settings = AppSettings()

        # Main content layout
        main_content = QQuickBoxLayout(QBoxDirection.LeftToRight)
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("font-size: 14pt;")
        self.list_widget.setFixedWidth(200)
        self.list_widget.addItems(["General", "Design", "Performance", "Advanced"])
        main_content.addWidget(self.list_widget)

        # Stacked layout for settings pages
        self.stacked_layout = QStackedLayout(self)

        # Create pages with titles and vertical layouts (slots)
        # [Reset to Defaults on every page]
        self.general_panel = self.create_general_page()
        self.design_panel = self.create_design_page()
        self.performance_panel = self.create_performance_page()
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
        self.language_dropdown.setEnabled(False)
        rows.append(("Language and Localization", self.language_dropdown))

        rows.append(("Shortcuts: ", None))
        shortcuts_layout_frame = QFrame()
        sc_frame_layout = QQuickBoxLayout(QBoxDirection.TopToBottom, 4, (9, 0, 0, 0), apply_layout_to=shortcuts_layout_frame)
        shortcuts_layout = QFlowLayout()
        shortcuts_widget = QFrame()
        shortcuts_widget.setLayout(shortcuts_layout)
        shortcuts_scroll_area = QScrollArea(parent=self)
        shortcuts_scroll_area.setWidget(shortcuts_widget)
        shortcuts_scroll_area.setWidgetResizable(True)
        sc_frame_layout.addWidget(shortcuts_scroll_area)

        shortcuts: dict[str, str] = {
            "file_new": self.settings.get_file_new_shortcut(),
            "file_open": self.settings.get_file_open_shortcut(),
            "file_save": self.settings.get_file_save_shortcut(),
            "file_save_as": self.settings.get_file_save_as_shortcut(),
            "file_close": self.settings.get_file_close_shortcut(),
            "simulation_start": self.settings.get_simulation_start_shortcut(),
            "simulation_step": self.settings.get_simulation_step_shortcut(),
            "simulation_halt": self.settings.get_simulation_halt_shortcut(),
            "simulation_end": self.settings.get_simulation_end_shortcut(),
            "states_cut": self.settings.get_states_cut_shortcut(),
            "states_copy": self.settings.get_states_copy_shortcut(),
            "states_paste": self.settings.get_states_paste_shortcut(),
            "states_delete": self.settings.get_states_delete_shortcut(),
            "zoom_in": self.settings.get_zoom_in_shortcut(),
            "zoom_out": self.settings.get_zoom_out_shortcut(),
            "zoom_reset": self.settings.get_zoom_reset_shortcut(),
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

        rows.append(("", shortcuts_layout_frame))

        update_frame = QFrame()
        update_layout = QQuickBoxLayout(QBoxDirection.LeftToRight, 9, (0, 0, 0, 0), apply_layout_to=update_frame)
        check_for_update_button = QPushButton("Check for update")
        check_for_update_button.clicked.connect(self.manual_update_check.emit)
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
        show_update_error_checkbox = QCheckBox()
        show_update_error_checkbox.setChecked(self.settings.get_show_update_timeout())
        show_update_error_checkbox.checkStateChanged.connect(lambda: (self.settings.set_show_update_timeout(show_update_error_checkbox.isChecked())))
        self.settings.show_update_timeout_changed.connect(show_update_error_checkbox.setChecked)
        rows.append(("Show update timeout: ", show_update_error_checkbox))
        show_update_error_checkbox = QCheckBox()
        show_update_error_checkbox.setChecked(self.settings.get_show_update_error())
        show_update_error_checkbox.checkStateChanged.connect(lambda: (self.settings.set_show_update_error(show_update_error_checkbox.isChecked())))
        self.settings.show_update_error_changed.connect(show_update_error_checkbox.setChecked)
        rows.append(("Show update error: ", show_update_error_checkbox))
        ask_to_reopen_last_file_checkbox = QCheckBox()
        ask_to_reopen_last_file_checkbox.setChecked(self.settings.get_ask_to_reopen_last_file())
        ask_to_reopen_last_file_checkbox.checkStateChanged.connect(lambda: (self.settings.set_ask_to_reopen_last_file(ask_to_reopen_last_file_checkbox.isChecked())))
        self.settings.ask_to_reopen_last_file_changed.connect(ask_to_reopen_last_file_checkbox.setChecked)
        rows.append(("Ask to reopen last file: ", ask_to_reopen_last_file_checkbox))
        auto_open_tutorial_tab_checkbox = QCheckBox()
        auto_open_tutorial_tab_checkbox.setChecked(self.settings.get_auto_open_tutorial_tab())
        auto_open_tutorial_tab_checkbox.checkStateChanged.connect(lambda: (self.settings.set_auto_open_tutorial_tab(auto_open_tutorial_tab_checkbox.isChecked())))
        rows.append(("Auto open tutorial tab: ", auto_open_tutorial_tab_checkbox))
        auto_hide_input_widget_checkbox = QCheckBox()
        auto_hide_input_widget_checkbox.setChecked(self.settings.get_auto_hide_input_widget())
        auto_hide_input_widget_checkbox.checkStateChanged.connect(lambda: (self.settings.set_auto_hide_input_widget(auto_hide_input_widget_checkbox.isChecked())))
        rows.append(("Auto hide input widget: ", auto_hide_input_widget_checkbox))
        use_safe_file_access = QCheckBox()
        use_safe_file_access.setChecked(True)
        use_safe_file_access.setEnabled(False)
        rows.append(("Use safe file access: ", use_safe_file_access))

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
        from dancer.qts import Style, Theme
        design_panel = QWidget()
        layout = QQuickBoxLayout(QBoxDirection.TopToBottom, apply_layout_to=design_panel)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        title_label = QLabel("Design")
        title_label.setStyleSheet("font-size: 18pt;")
        layout.addWidget(title_label)

        rows: list[tuple[str, QWidget | None]] = []

        window_icon_set_dropdown = QComboBox()
        base_icon_set_dir = self.settings.get_window_icon_sets_path().replace(":", os.getcwd(), 1)
        for sub in os.listdir(base_icon_set_dir):
            subpath = os.path.join(base_icon_set_dir, sub)
            if os.path.isdir(subpath):
                icon_path: str = os.path.join(subpath, "logo-nobg.png")
                if os.path.exists(icon_path):
                    name: str = os.path.basename(subpath)
                    window_icon_set_dropdown.addItem(QIcon(icon_path), name.replace("_", " ").title())
                    if name == self.settings.get_window_icon_set():
                        window_icon_set_dropdown.setCurrentIndex(window_icon_set_dropdown.count() - 1)
        window_icon_set_dropdown.currentIndexChanged.connect(lambda: self.settings.set_window_icon_set(window_icon_set_dropdown.currentText().lower().replace(" ", "_")))
        rows.append(("Window Icon: ", window_icon_set_dropdown))

        window_title_template_edit = QLineEdit(self.settings.get_window_title_template())
        window_title_template_edit.textChanged.connect(lambda: self.settings.set_window_title_template(window_title_template_edit.text()))
        rows.append(("Window Title Template: ", window_title_template_edit))

        font_edit = QFontComboBox(currentFont=QFont(self.settings.get_font()))
        font_edit.currentIndexChanged.connect(lambda: self.settings.set_font(font_edit.currentText()))
        rows.append(("Font: ", font_edit))

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

        light_theme, light_style = self.settings.get_theming(SystemTheme.LIGHT).split("/", maxsplit=1)
        dark_theme, dark_style = self.settings.get_theming(SystemTheme.DARK).split("/", maxsplit=1)

        # raise Exception(f"{light_theme, light_style, dark_theme, dark_style}")

        self.name_to_theme: dict[str, Theme] = {}
        self.theme_styles: dict[Theme, list[Style]] = {}
        for file in os.listdir(os.path.join(os.getcwd(), "data", "styling", "themes")):
            if not file.endswith(".qth"):
                continue
            author, name = file.removesuffix(".qth").split("_", maxsplit=1)
            theme_name = f"{author}::{name}"
            theme = Theme.get_loaded_theme(theme_name)
            if theme is None:  # Theme isn't loaded due to error
                continue
            self.light_theme_dropdown.addItem(theme_name)
            self.dark_theme_dropdown.addItem(theme_name)
            self.name_to_theme[theme_name] = theme
            self.theme_styles[theme] = Style.get_loaded_styles(theme)
            # if theme_name == light_theme:
            #     self.light_theme_dropdown.setCurrentIndex(self.light_theme_dropdown.count() - 1)
            # elif theme_name == dark_theme:
            #     self.dark_theme_dropdown.setCurrentIndex(self.dark_theme_dropdown.count() - 1)

        self.light_theme_dropdown.currentTextChanged.connect(lambda: (
            self.populate_style_dropdown(self.light_theme_dropdown.currentText(), self.light_style_dropdown.currentText(), self.light_style_dropdown),
            # self.settings.set_theming(SystemTheme.LIGHT, f"{self.light_theme_dropdown.currentText()}/{self.light_style_dropdown.currentText()}")
        ))
        self.light_style_dropdown.currentTextChanged.connect(
            lambda: self.settings.set_theming(SystemTheme.LIGHT, f"{self.light_theme_dropdown.currentText()}/{self.light_style_dropdown.currentText().lower().replace(' ', '_')}")
        )
        self.dark_theme_dropdown.currentTextChanged.connect(lambda: (
            self.populate_style_dropdown(self.dark_theme_dropdown.currentText(), self.dark_style_dropdown.currentText(), self.dark_style_dropdown),
            # self.settings.set_theming(SystemTheme.DARK, f"{self.dark_theme_dropdown.currentText()}/{self.dark_style_dropdown.currentText()}")
        ))
        self.dark_style_dropdown.currentTextChanged.connect(
            lambda: self.settings.set_theming(SystemTheme.DARK, f"{self.dark_theme_dropdown.currentText()}/{self.dark_style_dropdown.currentText().lower().replace(' ', '_')}")
        )
        self.light_theme_dropdown.setCurrentText(light_theme)
        self.populate_style_dropdown(self.light_theme_dropdown.currentText(), light_style, self.light_style_dropdown)
        self.dark_theme_dropdown.setCurrentText(dark_theme)
        self.populate_style_dropdown(self.dark_theme_dropdown.currentText(), dark_style, self.dark_style_dropdown)

        self.state_bg_color_button: QPushButton = QPushButton("Choose Color", self)
        self.state_bg_color_button.clicked.connect(self.open_color_dialog)
        rows.append(("Default state background: ", self.state_bg_color_button))

        hide_scrollbars_checkbox = QCheckBox()
        hide_scrollbars_checkbox.setChecked(self.settings.get_hide_scrollbars())
        hide_scrollbars_checkbox.checkStateChanged.connect(lambda: (self.settings.set_hide_scrollbars(hide_scrollbars_checkbox.isChecked())))
        rows.append(("Hide scrollbars: ", hide_scrollbars_checkbox))

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
        color: QColor = QColorDialog.getColor(initial=QColor(self.settings.get_default_state_background_color()), parent=self, title="Choose a color")
        if color.isValid():
            self.settings.set_default_state_background_color(color.name(QColor.NameFormat.HexArgb))

    def populate_style_dropdown(self, theme_name: str, wanted_style: str, dropdown: QComboBox):
        dropdown.clear()
        print("POPULATING", theme_name, wanted_style, self.theme_styles[self.name_to_theme[theme_name]])
        for style in self.theme_styles[self.name_to_theme[theme_name]]:
            style_name = style.get_style_name()
            dropdown.addItem(style_name)
            if style_name.lower().replace(" ", "_") == wanted_style.lower().replace(" ", "_"):
                dropdown.setCurrentIndex(dropdown.count() - 1)

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

    def create_advanced_page(self) -> QWidget:
        advanced_panel = QWidget()
        layout = QQuickBoxLayout(QBoxDirection.TopToBottom, apply_layout_to=advanced_panel)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        title_label = QLabel("Advanced")
        title_label.setStyleSheet("font-size: 18pt;")
        layout.addWidget(title_label)

        rows: list[tuple[str, QWidget | None]] = []

        clear_testing_cache_button = QPushButton("Clear")
        clear_testing_cache_button.setEnabled(False)
        rows.append(("Automaton testing cache: ", clear_testing_cache_button))
        hide_titlebar_checkbox = QCheckBox()
        hide_titlebar_checkbox.setChecked(self.settings.get_hide_titlebar())
        hide_titlebar_checkbox.checkStateChanged.connect(lambda: (
            self.settings.set_hide_titlebar(hide_titlebar_checkbox.isChecked()),
            self.list_widget.setCurrentRow(3)
        ))
        rows.append(("Hide titlebar: ", hide_titlebar_checkbox))
        stay_on_top_checkbox = QCheckBox()
        stay_on_top_checkbox.setChecked(self.settings.get_stay_on_top())
        stay_on_top_checkbox.checkStateChanged.connect(lambda: (
            self.settings.set_stay_on_top(stay_on_top_checkbox.isChecked()),
            self.list_widget.setCurrentRow(3)
        ))
        rows.append(("Stay on top: ", stay_on_top_checkbox))
        save_window_dimensions_checkbox = QCheckBox()
        save_window_dimensions_checkbox.setChecked(self.settings.get_save_window_dimensions())
        save_window_dimensions_checkbox.checkStateChanged.connect(lambda: self.settings.set_save_window_dimensions(save_window_dimensions_checkbox.isChecked()))
        rows.append(("Save window dimensions: ", save_window_dimensions_checkbox))
        save_window_position_checkbox = QCheckBox()
        save_window_position_checkbox.setChecked(self.settings.get_save_window_position())
        save_window_position_checkbox.checkStateChanged.connect(lambda: self.settings.set_save_window_position(save_window_position_checkbox.isChecked()))
        rows.append(("Save window position: ", save_window_position_checkbox))
        update_check_request_timeout_spinbox = QDoubleSpinBox(decimals=1, minimum=0.1, maximum=10.0, singleStep=0.1, value=self.settings.get_update_check_request_timeout())
        update_check_request_timeout_spinbox.valueChanged.connect(lambda: self.settings.set_update_check_request_timeout(update_check_request_timeout_spinbox.value()))
        rows.append(("Update check request timeout: ", update_check_request_timeout_spinbox))
        max_timer_tick_handled_events_spinbox = QSpinBox(minimum=0, maximum=20, singleStep=1, value=self.settings.get_max_timer_tick_handled_events())
        max_timer_tick_handled_events_spinbox.valueChanged.connect(lambda: self.settings.set_max_timer_tick_handled_events(max_timer_tick_handled_events_spinbox.value()))
        rows.append(("Max timer tick handled events: ", max_timer_tick_handled_events_spinbox))

        rows.append(("Developer Options: ", None))
        dev_ops_frame = QFrame()
        dev_ops_layout = QQuickBoxLayout(QBoxDirection.TopToBottom, 9, (9, 0, 0, 0), apply_layout_to=dev_ops_frame)
        logging_layout = QQuickBoxLayout(QBoxDirection.LeftToRight, 9, (0, 0, 0, 0))
        logging_layout.addWidget(QLabel("Logging mode: "))
        logging_mode_dropdown = QComboBox()
        logging_mode_dropdown.addItems(["DEBUG", "INFO", "WARN", "WARNING", "ERROR"])
        logging_mode_dropdown.setCurrentText(self.settings.get_logging_mode())
        logging_mode_dropdown.currentTextChanged.connect(lambda: self.settings.set_logging_mode(logging_mode_dropdown.currentText()))
        self.settings.logging_mode_changed.connect(logging_mode_dropdown.setCurrentText)
        logging_layout.addWidget(logging_mode_dropdown)
        dev_ops_layout.addLayout(logging_layout)
        open_logs_folder_button = QPushButton("Open logs folder")
        open_logs_folder_button.clicked.connect(lambda: os.system(f"explorer.exe {os.path.join(os.getcwd(), 'data', 'logs')}"))
        dev_ops_layout.addWidget(open_logs_folder_button)
        open_config_folder_button = QPushButton("Open config folder")
        open_config_folder_button.clicked.connect(lambda: os.system(f"explorer.exe {os.path.join(os.getcwd(), 'config')}"))
        dev_ops_layout.addWidget(open_config_folder_button)

        plugins_layout = QQuickBoxLayout(QBoxDirection.LeftToRight, 9, (0, 0, 0, 0))
        plugins_layout.addWidget(QLabel("Plugins: "))
        plugins_layout.addWidget(QPushButton("Load from disk"))
        load_from_github_button = QPushButton("Load from GitHub")
        load_from_github_button.setEnabled(False)
        plugins_layout.addWidget(load_from_github_button)
        dev_ops_layout.addLayout(plugins_layout)
        rows.append(("", dev_ops_frame))

        warn_of_new_plugins_checkbox = QCheckBox()
        warn_of_new_plugins_checkbox.setChecked(self.settings.get_warn_of_new_plugins())
        warn_of_new_plugins_checkbox.checkStateChanged.connect(lambda: self.settings.set_warn_of_new_plugins(warn_of_new_plugins_checkbox.isChecked()))
        rows.append(("Warn of new plugins: ", warn_of_new_plugins_checkbox))

        auto_open_tutorial_tab = QCheckBox()
        auto_open_tutorial_tab.setChecked(False)
        auto_open_tutorial_tab.setEnabled(False)
        rows.append(("Run plugins in separate process (not as efficient): ", auto_open_tutorial_tab))

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
        self.stacked_layout.addWidget(self.advanced_panel)
        self.list_widget.currentRowChanged.connect(self.stacked_layout.setCurrentIndex)
        self.list_widget.setCurrentRow(0)  # So an item is selected by default
