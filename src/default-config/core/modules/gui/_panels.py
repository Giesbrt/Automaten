"""Panels of the gui"""
from PySide6.QtWidgets import (QWidget, QListWidget, QStackedLayout, QFrame, QSpacerItem, QSizePolicy, QLabel,
                               QFormLayout, QLineEdit, QComboBox,
                               QSlider, QPushButton)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QRect
from PySide6.QtGui import QColor, QIcon

from aplustools.io.qtquick import QNoSpacingBoxLayout, QBoxDirection, QQuickBoxLayout

from ._grid_items import StateGroup

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
        # self.close_button.connect()

        self.name_input = QLineEdit(self)
        self.name_input.setText('q0')
        self.name_input.textEdited.connect(self.on_name_changed)

        # Beispiel: Eingabefelder für Einstellungen
        self.color_input = QComboBox(self)
        self.color_input.addItems(('None', 'Red', 'Green', 'Blue', 'Yellow', 'Orange', 'Purple', 'Cyan'))
        self.color_input.currentTextChanged.connect(self.on_color_changed)

        self.size_input = QSlider(Qt.Orientation.Horizontal, self)
        self.size_input.setRange(100, 450)
        self.size_input.setValue(100)
        self.size_input.valueChanged.connect(self.on_size_changed)

        # Füge Widgets zum Layout hinzu
        self.add_row_fixed_width('Name:', self.name_input)
        self.add_row_fixed_width('Color:', self.color_input)
        self.add_row_fixed_width('Size:', self.size_input)
        self.layout.addRow(self.close_button)

        self.setLayout(self.layout)

        self.color_mapping = {
            "None": Qt.GlobalColor.gray,
            "Red": Qt.GlobalColor.red,
            "Green": Qt.GlobalColor.green,
            "Blue": Qt.GlobalColor.blue,
            "Yellow": Qt.GlobalColor.yellow,
            "Orange": QColor(255, 165, 0),
            "Purple": QColor(128, 0, 128),
            "Cyan": Qt.GlobalColor.cyan
        }

        self.setStyleSheet("""
            QFrame {
                border-radius: 10px;
                padding: 5px;
            }

            QLineEdit {
                background-color: #333;      /* Dunkelgrauer Hintergrund für das Eingabefeld */
                border: 1px solid #444;      /* Dünner Rand */
                border-radius: 5px;          /* Abgerundete Ecken */
                color: white;                /* Weiße Schrift */
                padding: 5px;
                min-width: 150px;
            }

            QLineEdit:focus {
                border: 1px solid #0078d4;   /* Blaue Umrandung, wenn fokussiert */
            }

            QComboBox {
                background-color: #333;
                border: 1px solid #444;
                border-radius: 5px;
                color: white;
                padding: 5px;
                min-width: 150px;
            }

            QComboBox:focus {
                border: 1px solid #0078d4;
            }

            QSlider {
                background-color: #555;      /* Dunkler Hintergrund */
                border-color: #333;
                border-radius: 5px;
            }

            QSlider::handle:horizontal {
                background: #0078d4;         /* Blaue Schieberegler */
                border-radius: 5px;
                width: 15px;
                margin-top: -5px;
                margin-bottom: -5px;
            }

            QPushButton {
                background-color: #0078d4;    /* Blaue Hintergrundfarbe */
                color: white;                 /* Weiße Schrift */
                border: none;                 /* Kein Rand */
                border-radius: 5px;           /* Abgerundete Ecken */
                padding: 10px 20px;
            }

            QPushButton:hover {
                background-color: #005bb5;    /* Dunkleres Blau beim Hover */
            }

            QPushButton:pressed {
                background-color: #003f87;    /* Noch dunkleres Blau, wenn der Button gedrückt wird */
            }

            QFormLayout {
                row-wrap: true;
                spacing: 5px;
            }
        """)

    def add_row_fixed_width(self, name: str, widget: QWidget):
        label = QLabel(name, self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFixedWidth(min(50, 100))
        self.layout.addRow(label, widget)

    def set_condition(self, condition: StateGroup) -> None:
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
        from ._grids import AutomatonInteractiveGridView
        self.setLayout(QNoSpacingBoxLayout(QBoxDirection.TopToBottom))
        self.grid_view = AutomatonInteractiveGridView()  # Get values from settings
        self.layout().addWidget(self.grid_view)

        # Side Menu
        self.side_menu = QFrame(self)
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

        # Settings button
        self.settings_button = QPushButton(parent=self)
        self.settings_button.setFixedSize(40, 40)

        # Connect signals
        self.side_menu_animation.valueChanged.connect(self.side_menu_animation_value_changed)  # Menu
        self.menu_button.clicked.connect(self.toggle_side_menu)  # Menu
        # TODO: SETTINGS
        # - Automaton loader settings

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
        if self.condition_edit_menu.x() + width <= self.width():
            self.condition_edit_menu.setGeometry(self.width() - width, 0, width, height)
        else:
            new_x = self.width() - width
            if new_x < 0:
                new_x = 0
            self.condition_edit_menu.setGeometry(new_x, 0, width, height)
        self.update_menu_button_position()
        self.settings_button.move(self.width() - 60, 20)

        super().resizeEvent(event)


class SettingsPanel(Panel):
    """The settings panel"""
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("background-color: rgba(0, 40, 158, 0.33); font-size: 16pt;")

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
        self.general_panel = self.create_settings_page("General")
        self.display_panel = self.create_settings_page("Design", extra_widgets=self.create_display_page_widgets())
        self.network_panel = self.create_settings_page("Security")
        self.privacy_panel = self.create_settings_page("Privacy")

        # Add panels to the stacked layout
        self.stacked_layout.addWidget(self.general_panel)
        self.stacked_layout.addWidget(self.display_panel)
        self.stacked_layout.addWidget(self.network_panel)
        self.stacked_layout.addWidget(self.privacy_panel)

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
