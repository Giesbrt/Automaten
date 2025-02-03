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


class StateMenu(QFrame):
    name_changed = Signal(str)
    color_changed = Signal(QColor)
    size_changed = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAutoFillBackground(True)

        self.visible = False
        self.state = None
        # Layout für das Menü
        self.layout = QFormLayout(self)

        self.close_button = QPushButton('Close', self)
        self.close_button.clicked.connect(lambda: self.parentWidget().toggle_condition_edit_menu(False))

        self.name_input = QLineEdit(self)
        # self.name_input.setText('q0')

        self.color_mapping = {
            'None': Qt.GlobalColor.gray,
            'Red': Qt.GlobalColor.red,
            'Green': Qt.GlobalColor.green,
            'Blue': Qt.GlobalColor.blue,
            'Yellow': Qt.GlobalColor.yellow,
            'Orange': QColor(255, 165, 0),
            'Purple': QColor(128, 0, 128),
            'Cyan': Qt.GlobalColor.cyan
        }

        # Beispiel: Eingabefelder für Einstellungen
        self.color_input = QComboBox(self)
        self.color_input.addItems((color for color in self.color_mapping.keys()))
        # ('None', 'Red', 'Green', 'Blue', 'Yellow', 'Orange', 'Purple', 'Cyan')

        self.size_input = QSlider(Qt.Orientation.Horizontal, self)
        self.size_input.setRange(100, 450)
        self.size_input.setValue(100)

        # Füge Widgets zum Layout hinzu
        self.add_row_fixed_width('Name:', self.name_input)
        self.add_row_fixed_width('Color:', self.color_input)
        self.add_row_fixed_width('Size:', self.size_input)
        self.layout.addRow(self.close_button)

        self.setLayout(self.layout)

    def set_state(self, state: StateGroup) -> None:
        self.state = state
        self.set_parameters()

    def set_parameters(self):
        # print('set parameters')
        self.name_input.setText(self.state.label.toPlainText())
        searched_color: Qt.GlobalColor = self.state.get_ui_state().get_colour()
        key = next((key for key, color in self.color_mapping.items() if searched_color == color))
        self.color_input.setCurrentText(key)
        self.size_input.setValue(self.state.get_size())

    def add_row_fixed_width(self, name: str, widget: QWidget) -> None:
        label = QLabel(name, self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFixedWidth(min(50, 100))
        self.layout.addRow(label, widget)

    def connect_methods(self) -> None:
        self.name_input.textEdited.connect(self.state.set_name)
        self.color_input.currentTextChanged.connect(lambda: self.state.set_color(self.color_mapping.get(self.color_input.currentText())))
        self.size_input.valueChanged.connect(self.state.set_size)

    def disconnect_methods(self) -> None:
        self.name_input.textEdited.disconnect()
        self.color_input.currentTextChanged.disconnect()
        self.size_input.valueChanged.disconnect()


class UserPanel(Panel):
    """The main panel to be shown"""
    def __init__(self, automaton_type: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        from ._grids import AutomatonInteractiveGridView
        self.setLayout(QNoSpacingBoxLayout(QBoxDirection.TopToBottom))
        self.grid_view = AutomatonInteractiveGridView(automaton_type)  # Get values from settings
        self.layout().addWidget(self.grid_view)

        # Side Menu
        self.side_menu = QFrame(self)
        self.side_menu.setFrameShape(QFrame.Shape.StyledPanel)
        self.side_menu.setAutoFillBackground(True)
        # Animation for Side Menu
        self.side_menu_animation = QPropertyAnimation(self.side_menu, b"geometry")
        self.side_menu_animation.setDuration(500)

        # Condition Edit Menu
        self.state_menu = StateMenu(self)
        self.state_menu.setGeometry(self.parent().width(), 0, 300, self.height())
        # Animation for Condition Edit Menu
        self.state_menu_animation = QPropertyAnimation(self.state_menu, b'geometry')
        self.state_menu_animation.setDuration(500)

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
        self.state_menu.visible = not self.state_menu.visible

        if to_state:
            start_value = QRect(self.width(), 0, width, height)
            end_value = QRect(self.width() - width, 0, width, height)
        else:
            start_value = QRect(self.width() - width, 0, width, height)
            end_value = QRect(self.width(), 0, width, height)

        if (self.state_menu.x() >= self.width() and to_state
                or self.state_menu.x() < self.width() and not to_state):
            self.state_menu_animation.setStartValue(start_value)
            self.state_menu_animation.setEndValue(end_value)
            self.state_menu_animation.start()

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
        print(self.state_menu.visible)
        if self.state_menu.visible:
            self.state_menu.setGeometry(self.width() - width, 0, width, height)
        else:
            self.state_menu.setGeometry(self.width(), 0, width, height)
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
        # [Reset to Defaults on every page]
        self.general_panel = self.create_settings_page("General")
        #  - Clear Automaton testing cache
        # Shortcuts:
        #  - Change shortcuts
        #  - Enable/Disable shortcuts
        # Updates:
        #  - Enable automatic updates
        #  - Check for updates manually/ automatically (the .exe file)
        #  - Download updates in the background
        # Language and Localization:
        #  - Select app language
        #  - Region specific formatting (e.g. date/time, number formats)?
        # Notifications:
        #  - Enable / disable system notifications
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
        #  -> enable encryption of save files?
        #   -> app password (auto logoff)?
        self.privacy_panel = self.create_settings_page("Privacy")
        # Data Collection:
        #  - Opt in or out of data collection
        #  - View collected data
        #  - Clear data collection cache
        # Ad Preferences: --> Fake ads
        #  - Disable personalized ads
        #  - Clear ads cache
        self.advanced_panel = self.create_settings_page("Advanced")
        # Debugging:
        #  - Set logging mode
        #  - Open logs folder
        # Developer Options:
        #  - Experimental features
        #  - Load selected plugin
        #  -> Install plugins from e.g. Github

        # Add panels to the stacked layout
        self.stacked_layout.addWidget(self.general_panel)
        self.stacked_layout.addWidget(self.design_panel)
        self.stacked_layout.addWidget(self.security_panel)
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
