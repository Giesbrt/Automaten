"""Panels of the gui"""
from PySide6.QtWidgets import (QWidget, QListWidget, QStackedLayout, QFrame, QSpacerItem, QSizePolicy, QLabel,
                               QFormLayout, QLineEdit,
                               QSlider, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
                               QHBoxLayout, QColorDialog, QComboBox, QMenu)
from PySide6.QtCore import Qt, QPropertyAnimation, QRect, QEvent, Signal, QParallelAnimationGroup, QTimer
from PySide6.QtGui import QColor, QIcon, QPen, QAction

from aplustools.io.qtquick import QNoSpacingBoxLayout, QBoxDirection, QQuickBoxLayout

from ._grid_items import StateGroup
from ..signal_bus import SingletonObserver

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

        self.singleton_observer = SingletonObserver()
        # self.singleton_observer.subscribe('token_lists', print('hallo'))

        self.visible: bool = False
        self.state: StateGroup | None = None
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

    def set_state(self, state: StateGroup) -> None:
        self.state: StateGroup = state
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
            target_item: QTableWidgetItem = QTableWidgetItem(f'{transition.get_ui_transition().get_from_state().get_display_text()} - {transition.get_ui_transition().get_to_state().get_display_text()}')
            target_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            target_item.setData(Qt.ItemDataRole.UserRole, transition)

            token_list = self.singleton_observer.get('token_lists')
            condition_edit: QComboBox = QComboBox()
            condition_edit.addItems(token_list[0] if token_list else [])
            condition_edit.setItemData(Qt.ItemDataRole.UserRole, transition)

            self.transitions_table.setItem(i, 0, target_item)
            self.transitions_table.setCellWidget(i, 1, condition_edit)

    def add_row_fixed_width(self, name: str, widget: QWidget) -> None:
        label = QLabel(name, self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFixedWidth(min(50, 100))
        self.layout.addRow(label, widget)

    def change_state_type(self):
        state_type: _ty.Literal['default', 'start', 'end'] = self.type_input.currentText().lower()
        if state_type == 'start':
            self.singleton_observer.set('start_state', self.state.get_ui_state())
        self.state.set_state_type(state_type)

    def on_current_item_changed(self, current: QTableWidgetItem | QComboBox, previous: QTableWidgetItem | QComboBox | None) -> None:
        if previous:
            previous.data(Qt.ItemDataRole.UserRole).setPen(QPen(QColor('black'), 4))
        current.data(Qt.ItemDataRole.UserRole).setPen(QPen(QColor('red'), 4))

    def connect_methods(self) -> None:
        self.name_input.textEdited.connect(self.state.set_name)
        self.size_input.valueChanged.connect(self.state.set_size)

    def disconnect_methods(self) -> None:
        self.name_input.textEdited.disconnect()
        self.size_input.valueChanged.disconnect()


class ControlMenu(QFrame):
    def __init__(self, grid_view: 'AutomatonInteractiveGridView', parent=None):
        super().__init__(parent)
        self.singleton_observer = SingletonObserver()
        self.singleton_observer.subscribe('token_lists', self.update_token_list)

        self.grid_view = grid_view
        self.token_list: _ty.Tuple[_ty.List[str], _ty.List[str]] = self.grid_view.get_token_list()

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
        self.next_button = QPushButton(self)

        self.stop_button.setEnabled(False)

        self.token_list_box = QComboBox(self)
        self.token_list_box.setEditable(True)
        self.token_list_box.addItems(self.token_list[0])
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

        self.singleton_observer.set('token_lists', self.token_list)

    def show_context_menu(self, pos):
        """Zeigt das Kontextmenü bei Rechtsklick"""
        menu = QMenu(self)
        delete_action = menu.addAction("Ausgewähltes Element löschen")
        action = menu.exec_(self.token_list_box.mapToGlobal(pos))

        if action == delete_action:
            self.remove_token(self.token_list_box.currentText().strip(), self.token_list_box.currentIndex())

    def add_token(self):
        token = self.token_list_box.currentText().strip()
        if not token in self.token_list[0]:
            self.token_list_box.addItem(token)
        QTimer.singleShot(0, lambda: self.token_list_box.setCurrentText(''))
        self.token_list[0].append(token)

        self.singleton_observer.set('token_lists', self.token_list)

    def remove_token(self, token, token_index: int=None):
        self.token_list_box.removeItem(token_index)
        self.token_list[0].remove(token)

        self.singleton_observer.set('token_lists', self.token_list)

    def update_token_list(self, token_list: _ty.List[str]):
        self.token_list_box.clear()

        if isinstance(self.token_list, list) and self.token_list and all(isinstance(item, list) for item in self.token_list):
            self.token_list_box.addItems(token_list[0])
        else:
            self.token_list_box.addItems(token_list)

    def handle_automaton_changed(self, event: 'AutomatonEvent'):
        if event.is_loaded:
            self.token_list = event.token_list_box
            self.update_token_list(self.token_list)
        else:
            self.token_list = []
            self.update_token_list([])


class UserPanel(Panel):
    """The main panel to be shown"""
    def __init__(self, automaton_type: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        from ._grids import AutomatonInteractiveGridView
        self.setLayout(QNoSpacingBoxLayout(QBoxDirection.TopToBottom))

        # self.token_list: _ty.List[str] = ['Apfel', 'Birne', 'Orange', 'Blaubeere', 'Aubergine', 'Erdbeere']

        self.grid_view = AutomatonInteractiveGridView()  # Get values from settings
        self.layout().addWidget(self.grid_view)

        # Menu Button
        self.menu_button = QPushButton(self)
        self.menu_button.setFixedSize(40, 40)

        # Settings button
        # self.settings_button = QPushButton(self)
        # self.settings_button.setFixedSize(40, 40)

        # Control Menu
        self.control_menu = ControlMenu(self.grid_view, self)
        # Animation for Control Menu
        self.control_menu_animation = QPropertyAnimation(self.control_menu, b'geometry')
        self.control_menu_animation.setDuration(500)

        # Side Menu
        self.side_menu = QFrame(self)
        self.side_menu.setFrameShape(QFrame.Shape.StyledPanel)
        self.side_menu.setAutoFillBackground(True)
        # Animation for Side Menu
        self.side_menu_animation = QPropertyAnimation(self.side_menu, b'geometry')
        self.side_menu_animation.setDuration(500)

        # Condition Edit Menu
        self.state_menu = StateMenu(self)
        self.state_menu.setGeometry(self.parent().width(), 0, 300, self.height())
        # Animation for Condition Edit Menu
        self.state_menu_animation = QPropertyAnimation(self.state_menu, b'geometry')
        self.state_menu_animation.setDuration(500)

        # Connect signals
        self.side_menu_animation.valueChanged.connect(self.side_menu_animation_value_changed)  # Menu
        self.menu_button.clicked.connect(self.toggle_side_menu)  # Menu
        # TODO: SETTINGS
        # - Automaton loader settings

    def set_token_list(self, token_list: _ty.List[str]):
        self.token_list = token_list

    def get_token_list(self) -> _ty.List[str]:
        return self.token_list

    def update_menu_button_position(self, preset_value: int | None = None):
        if not preset_value:
            preset_value = self.side_menu.x()
        self.menu_button.move(preset_value + self.side_menu.width(), 20)

    def side_menu_animation_value_changed(self, value: QRect):
        self.update_menu_button_position(value.x())

    def toggle_side_menu(self):
        width = max(200, int(self.width() / 4))
        height = self.height()

        if self.side_menu.x() < 0:
            start_value = QRect(-width, 0, width, height)
            end_value = QRect(0, 0, width, height)
        else:
            start_value = QRect(0, 0, width, height)
            end_value = QRect(-width, 0, width, height)

        self.side_menu_animation.setStartValue(start_value)
        self.side_menu_animation.setEndValue(end_value)
        self.side_menu_animation.start()

    def toggle_condition_edit_menu(self, to_state: bool) -> None:
        width = max(200, int(self.width() / 4))
        height = self.height()
        c_menu_width = self.control_menu.width()
        c_menu_height = self.control_menu.height()
        self.state_menu.visible = not self.state_menu.visible

        if to_state:
            state_start = QRect(self.width(), 0, width, height)
            state_end = QRect(self.width() - width, 0, width, height)
            control_start = QRect(self.width() - c_menu_width - 20, 20, c_menu_width, c_menu_height)
            control_end = QRect(self.width() - c_menu_width - self.state_menu.width() - 20, 20, c_menu_width, c_menu_height)
        else:
            state_start = QRect(self.width() - width, 0, width, height)
            state_end = QRect(self.width(), 0, width, height)
            control_start = QRect(self.width() - c_menu_width - self.state_menu.width() - 20, 20, c_menu_width, c_menu_height)
            control_end = QRect(self.width() - c_menu_width - 20, 20, c_menu_width, c_menu_height)

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
        if self.side_menu.x() < 0:
            self.side_menu.setGeometry(-width, 0, width, height)
            self.menu_button.move(width + 40, 20)  # Update the position of the menu button
        else:
            self.side_menu.setGeometry(0, 0, width, height)
            self.menu_button.move(40, 20)  # Update the position of the menu button
        if self.state_menu.visible:
            self.state_menu.setGeometry(self.width() - width, 0, width, height)
        else:
            self.state_menu.setGeometry(self.width(), 0, width, height)
        if self.state_menu.visible:
            self.control_menu.setGeometry(self.width() - self.control_menu.width() - self.state_menu.width() - 20, 20, self.control_menu.width(), self.control_menu.height())
        else:
            self.control_menu.setGeometry(self.width() - self.control_menu.width() - 20, 20, self.control_menu.width(), self.control_menu.height())
        self.update_menu_button_position()
        # self.settings_button.move(self.width() - 60, 100)

        super().resizeEvent(event)


class SettingsPanel(Panel):
    """The settings panel"""
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        # self.setStyleSheet("background-color: rgba(0, 40, 158, 0.33); font-size: 16pt;")

        self.setLayout(QQuickBoxLayout(QBoxDirection.TopToBottom))

        # Top bar with back button
        top_bar = QQuickBoxLayout(QBoxDirection.LeftToRight)
        self.back_button = QPushButton("Back")
        self.back_button.setFixedSize(80, 30)  # Example size
        top_bar.addWidget(self.back_button)
        top_bar.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.layout().addLayout(top_bar)

        # Main content layout
        main_content = QQuickBoxLayout(QBoxDirection.LeftToRight)
        self.list_widget = QListWidget()
        self.list_widget.setFixedWidth(200)  # Example width, ~1/5 of the width
        self.list_widget.addItems(["General", "Design", "Security", "Privacy"])
        main_content.addWidget(self.list_widget)

        # Stacked layout for settings pages
        self.stacked_layout = QStackedLayout()

        # Create pages with titles and vertical layouts (slots)
        # [Reset to Defaults on every page]
        self.general_panel = self.create_settings_page("General")
        #  - Clear Automaton testing cache
        # Shortcuts:
        #  - Change shortcuts
        #  - Enable/Disable shortcuts
        # Updates:
        #  - Check for updates manually/ automatically
        # Language and Localization:
        #  - Select app language
        # Startup options:
        #  - Open last used file on startup
        #  - Launch at system startup
        self.design_panel = self.create_settings_page("Design", extra_widgets=self.create_display_page_widgets())
        # Themes:
        #  - Select light, dark theme
        #  - User created styles through gui with example of finished product visible as the color picker window
        # Accessibility:
        #  - High-contrast mode?
        #  - Automaton scaling
        #  - Ui Scaling (Font too)
        #  - Larger icons?
        # Font Options:
        #  - Font Family
        # Animations:
        #  - Enable/Disable animations
        # Tutorials:
        #  - Auto open tutorials tab (default "on")
        # Scaling
        #  - enable/disable automatic scaling
        # Defaults:
        #  - Default state background color
        #  - Transition func seperator (default "/")
        self.security_panel = self.create_settings_page("Security")
        #  - Warn of new plugins
        #  - Run plugin only in a separate process (Not as efficient)
        # Save files:
        #  - Use safe file access to prevent corruption
        self.advanced_panel = self.create_settings_page("Advanced")
        # Debugging:
        #  - Set logging mode
        #  - Open logs folder
        # Developer Options:
        #  - Load selected plugin
        #  -> Install plugins from e.g. Github for now no!

        # Add panels to the stacked layout
        # import time
        # time.sleep(10)
        # self.stacked_layout.addWidget(self.general_panel)
        # self.stacked_layout.addWidget(self.design_panel)
        # self.stacked_layout.addWidget(self.security_panel)
        # self.stacked_layout.addWidget(self.privacy_panel)
        # import time
        # time.sleep(10)

        main_content.addLayout(self.stacked_layout)
        self.layout().addLayout(main_content)

        self.list_widget.currentRowChanged.connect(self.stacked_layout.setCurrentIndex)
        self.list_widget.setCurrentRow(0)  # So an item is selected by default

    def create_settings_page(self, title: str, extra_widgets: list[QWidget] = None) -> QWidget:
        """Creates a settings page with a title and vertical layout."""
        page = QWidget()
        layout = QQuickBoxLayout(QBoxDirection.TopToBottom)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Add title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 18pt;")
        layout.addWidget(title_label)

        # Add extra widgets if provided
        if extra_widgets:
            for widget in extra_widgets:
                frame = QFrame()
                frame.setStyleSheet("""
                    QFrame {
                        border: 2px solid #00289E;
                        border-radius: 8px;
                        margin: 10px;
                        padding: 10px;
                        background-color: white;
                    }
                """)
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