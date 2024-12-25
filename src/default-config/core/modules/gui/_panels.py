"""Panels of the gui"""
from PySide6.QtWidgets import (QWidget, QListWidget, QStackedLayout, QFrame, QSpacerItem, QSizePolicy, QLabel,
                               QFormLayout, QLineEdit, QComboBox,
                               QSlider, QPushButton)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QRect
from PySide6.QtGui import QColor, QIcon

from aplustools.io.qtquick import QNoSpacingBoxLayout, QBoxDirection, QQuickBoxLayout

from ._grid_items import ConditionGroup
from ._grids import AutomatonInteractiveGridView

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts


class Panel(QWidget):
    """Baseclass for all Panels"""
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)


class ConditionEditMenu(QFrame):
    name_changed = Signal(str)
    color_changed = Signal(QColor)
    size_changed = Signal(int)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setAutoFillBackground(True)

        self.condition = None

        # Layout für das Menü
        self.layout = QFormLayout(self)

        self.close_button = QPushButton('Close', self)

        self.name_input = QLineEdit(self)
        self.name_input.setText('q0')
        self.name_input.textEdited.connect(self.on_name_changed)

        # Beispiel: Eingabefelder für Einstellungen
        self.color_input = QComboBox(self)
        self.color_input.addItems(('Red', 'Green', 'Blue', 'Yellow', 'Orange', 'Purple', 'Cyan'))
        self.color_input.currentTextChanged.connect(self.on_color_changed)

        self.size_input = QSlider(Qt.Orientation.Horizontal, self)
        self.size_input.setRange(100, 450)
        self.size_input.setValue(100)
        self.size_input.valueChanged.connect(self.on_size_changed)

        # Füge Widgets zum Layout hinzu
        self.layout.addRow(self.close_button)
        self.layout.addRow('Name:', self.name_input)
        self.layout.addRow('Color:', self.color_input)
        self.layout.addRow('Size:', self.size_input)

        self.setLayout(self.layout)

        self.color_mapping = {
            "Red": Qt.GlobalColor.red,
            "Green": Qt.GlobalColor.green,
            "Blue": Qt.GlobalColor.blue,
            "Yellow": Qt.GlobalColor.yellow,
            "Orange": QColor(255, 165, 0),
            "Purple": QColor(128, 0, 128),
            "Cyan": Qt.GlobalColor.cyan
        }

    def set_condition(self, condition: ConditionGroup) -> None:
        self.condition = condition

    def on_name_changed(self, name: str) -> None:
        self.name_changed.emit(name)

    def on_color_changed(self, color: str) -> None:
        self.color_changed.emit(self.color_mapping.get(color))

    def on_size_changed(self, size: int) -> None:
        self.size_changed.emit(size)


class UserPanel(Panel):
    """The main panel to be shown"""
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setLayout(QNoSpacingBoxLayout(QBoxDirection.TopToBottom))
        self.grid_view = AutomatonInteractiveGridView()  # Get values from settings
        self.layout().addWidget(self.grid_view)

        # Side Menu
        self.side_menu = QFrame(self)
        self.side_menu.setObjectName("sideMenu")
        self.side_menu.setFrameShape(QFrame.Shape.StyledPanel)
        self.side_menu.setAutoFillBackground(True)
        # Animation for Side Menu
        self.side_menu_animation = QPropertyAnimation(self.side_menu, b"geometry")
        self.side_menu_animation.setDuration(500)

        # Condition Edit Menu
        self.condition_edit_menu = ConditionEditMenu(self)
        self.condition_edit_menu.setGeometry(self.parent().width(), 0, 300, self.height())
        # Animation for Condition Edit Menu
        self.condition_edit_menu_animation = QPropertyAnimation(self.condition_edit_menu, b'geometry')
        self.condition_edit_menu_animation.setDuration(500)

        # Menu Button
        self.menu_button = QPushButton(QIcon(), "", self)
        self.menu_button.setFixedSize(40, 40)

        # Connect signals
        self.side_menu_animation.valueChanged.connect(self.side_menu_animation_value_changed)  # Menu
        self.menu_button.clicked.connect(self.toggle_side_menu)  # Menu

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
        """True: opened Sidepanel, False: closed Sidepanel"""
        width = max(200, int(self.width() / 4))
        height = self.height()

        if to_state:
            start_value = QRect(self.width(), 0, width, height)
            end_value = QRect(self.width() - width, 0, width, height)
        else:
            start_value = QRect(self.width() - width, 0, width, height)
            end_value = QRect(self.width(), 0, width, height)

        if (self.condition_edit_menu.x() >= self.width() and to_state
                or self.condition_edit_menu.x() < self.width() and not to_state):
            self.condition_edit_menu_animation.setStartValue(start_value)
            self.condition_edit_menu_animation.setEndValue(end_value)
            self.condition_edit_menu_animation.start()

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
        self.update_menu_button_position()

        super().resizeEvent(event)


class SettingsPanel(Panel):
    """The settings panel"""
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("background-color: rgba(0, 40, 158, 0.33);")

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
        self.list_widget.addItems(["General", "Display", "Network", "Privacy", "About"])
        main_content.addWidget(self.list_widget)

        # Stacked layout for settings pages
        self.stacked_layout = QStackedLayout()

        # Example settings panels
        self.general_panel = QLabel("General Settings Panel")
        self.display_panel = QLabel("Display Settings Panel")
        self.network_panel = QLabel("Network Settings Panel")
        self.privacy_panel = QLabel("Privacy Settings Panel")
        self.about_panel = QLabel("About Panel")

        # Add panels to the stacked layout
        self.stacked_layout.addWidget(self.general_panel)
        self.stacked_layout.addWidget(self.display_panel)
        self.stacked_layout.addWidget(self.network_panel)
        self.stacked_layout.addWidget(self.privacy_panel)
        self.stacked_layout.addWidget(self.about_panel)

        main_content.addLayout(self.stacked_layout)
        self.layout().addLayout(main_content)

        self.list_widget.currentRowChanged.connect(self.stacked_layout.setCurrentIndex)
        self.list_widget.setCurrentRow(0)  # So an item is selected by default
