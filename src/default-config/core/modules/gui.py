"""TBA"""
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QScrollBar, QLabel, QPushButton, QFrame, QLineEdit, \
    QComboBox, QCheckBox, QSpinBox, QFormLayout, QHBoxLayout, QApplication, QScroller, QScrollerProperties, QLayout,
                               QSizePolicy, QListWidget, QListWidgetItem, QGraphicsOpacityEffect, QStyledItemDelegate,
                               QDialog, QGroupBox, QFontComboBox, QToolButton, QRadioButton, QDialogButtonBox,
                               QFileDialog)
from PySide6.QtCore import QPropertyAnimation, QRect, QTimer, Qt, QEasingCurve, QSize, Signal
from PySide6.QtGui import QFont, QIcon, QWheelEvent, QPixmap, QDoubleValidator

from .quick import QNoSpacingBoxLayout, QBoxDirection

import shutil, json, sqlite3
import os.path

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts


class UnselectableDelegate(QStyledItemDelegate):
    def editorEvent(self, event, model, option, index):
        # Prevent selection of disabled items
        data = model.itemData(index)
        if Qt.ItemDataRole.UserRole in data and data[Qt.ItemDataRole.UserRole] == "disabled":
            return False
        return super().editorEvent(event, model, option, index)


class CustomComboBox(QComboBox):
    def __init__(self):
        super().__init__()
        self.setItemDelegate(UnselectableDelegate())
        self.currentIndexChanged.connect(self.handleIndexChanged)
        self.previousIndex = 0

    def handleIndexChanged(self, index):
        # If the newly selected item is disabled, revert to the previous item
        if index in range(self.count()):
            if self.itemData(index, Qt.ItemDataRole.UserRole) == "disabled":
                self.setCurrentIndex(self.previousIndex)
            else:
                self.previousIndex = index

    def setItemUnselectable(self, index):
        # Set data role to indicate item is disabled
        self.model().setData(self.model().index(index, 0), "disabled", Qt.ItemDataRole.UserRole)


class SearchWidget(QWidget):
    selectedItem = Signal(tuple)

    def __init__(self, search_results_func):
        super().__init__()
        self.initUI()
        self.search_results_func = search_results_func

    def set_search_results_func(self, new_func):
        self.search_results_func = new_func

    def sizeHint(self):
        search_bar_size_hint = self.search_bar.sizeHint()
        if self.results_list.isVisible():
            results_list_size_hint = self.results_list.sizeHint()
            # Combine the heights and take the maximum width
            combined_height = search_bar_size_hint.height() + results_list_size_hint.height()
            combined_width = max(search_bar_size_hint.width(), results_list_size_hint.width())
            return QSize(combined_width, combined_height)
        else:
            return search_bar_size_hint  # Return size hint of search_bar

    def minimumSizeHint(self):
        return self.search_bar.minimumSizeHint()

    def initUI(self):
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.on_text_changed)
        self.search_bar.returnPressed.connect(self.on_return_pressed)

        self.results_list = QListWidget(self)
        self.results_list.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Ignored)
        self.results_list.hide()
        self.results_list.itemActivated.connect(self.on_item_activated)

        layout = QVBoxLayout(self)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.results_list)
        layout.setContentsMargins(0, 0, 0, 0)  # Set margins to zero
        layout.setSpacing(0)  # Set spacing to zero

    def on_text_changed(self, text=None):
        self.results_list.clear()
        text = text or self.search_bar.text()
        if text and self.search_bar.hasFocus():
            # Assume get_search_results is a function that returns a list of tuples with the result text and icon path.
            results = self.search_results_func(text)
            for result_text, icon_path in results:
                item = QListWidgetItem(result_text)
                item.setIcon(QIcon(os.path.abspath(icon_path)))
                self.results_list.addItem(item)
            self.results_list.show()
        else:
            self.results_list.hide()

        self.adjustSize()
        self.updateGeometry()  # Notify the layout system of potential size change
        self.results_list.updateGeometry()  # Notify the layout system of potential size change
        # self.window().adjustSize()  # Adjust the size of the parent window

    def on_return_pressed(self):
        item = self.results_list.currentItem() or self.results_list.item(0)
        if item:
            self.select_item(item)

    def on_item_activated(self, item):
        self.select_item(item)

    def select_item(self, item):
        title = (self.search_bar.text(), item.text())
        print(f'Selected: {title}')
        self.search_bar.setText('')
        self.results_list.hide()
        self.selectedItem.emit(title)


class DummyViewport(QWidget):
    def __init__(self, widget, viewport):
        super().__init__()
        self.widget = widget
        self._viewport = viewport

    def width(self):
        return self._viewport.width() - self._viewport.verticalScrollBar().width()

    def height(self):
        return self._viewport.height() - self._viewport.horizontalScrollBar().height()

    def size(self):
        return QSize(self._viewport.width() - self._viewport.v_scrollbar.width(),
                     self._viewport.height() - self._viewport.h_scrollbar.height())

    def mapToGlobal(self, pos):
        return self.widget.mapToGlobal(pos)

    def grabGesture(self, gesture_type):
        return self.widget.grabGesture(gesture_type)


class CustomScrollArea(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.layout = QNoSpacingBoxLayout(QBoxDirection.TopToBottom)
        self.layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        self.setLayout(self.layout)

        # Create a content widget that will hold the scrollable content
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_widget.setLayout(self.content_layout)

        # Set the size policy of the content widget to be Ignored
        self.content_widget.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Ignored
        )

        # Set the size policy of the content layout to be Ignored
        self.content_layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)

        # Create vertical scrollbar
        self._v_scrollbar = QScrollBar()
        self._v_scrollbar.setOrientation(Qt.Orientation.Vertical)
        self._v_scrollbar.setVisible(False)

        # Create horizontal scrollbar
        self._h_scrollbar = QScrollBar()
        self._h_scrollbar.setOrientation(Qt.Orientation.Horizontal)
        self._h_scrollbar.setVisible(False)

        self.corner_widget = QWidget()
        self.corner_widget.setStyleSheet("background: transparent;")
        # self.corner_widget.setAutoFillBackground(True)

        h_scrollbar_layout = QNoSpacingBoxLayout(QBoxDirection.LeftToRight)
        h_scrollbar_layout.addWidget(self._h_scrollbar)
        h_scrollbar_layout.addWidget(self.corner_widget)
        h_scrollbar_layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)

        self.corner_widget.setFixedSize(self._v_scrollbar.width(), self._h_scrollbar.height())

        hbox = QNoSpacingBoxLayout(QBoxDirection.LeftToRight)
        hbox.addWidget(self.content_widget)
        hbox.addWidget(self._v_scrollbar)
        hbox.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)

        vbox = QNoSpacingBoxLayout(QBoxDirection.TopToBottom)
        vbox.addLayout(hbox)
        vbox.addLayout(h_scrollbar_layout)
        vbox.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)

        self.layout.addLayout(vbox)

        # Connect scrollbar value changed signal to update content widget position
        self._v_scrollbar.valueChanged.connect(self.updateContentPosition)
        self._h_scrollbar.valueChanged.connect(self.updateContentPosition)

        self._view = DummyViewport(self.content_widget, self)

        self._vert_scroll_pol = "as"
        self._hor_scroll_pol = "as"

    def viewport(self):
        return self._view

    def setWidgetResizable(self, value: bool):
        return

    def contentWidget(self):
        return self.content_widget

    def verticalScrollBar(self):
        return self._v_scrollbar

    def horizontalScrollBar(self):
        return self._h_scrollbar

    def setVerticalScrollBarPolicy(self, policy):
        if policy == Qt.ScrollBarPolicy.ScrollBarAsNeeded:
            self._vert_scroll_pol = "as"
        elif policy == Qt.ScrollBarPolicy.ScrollBarAlwaysOff:
            self._vert_scroll_pol = "off"
        else:
            self._vert_scroll_pol = "on"
        self.reload_scrollbars()
        self.content_widget.resize(self.content_widget.sizeHint())

    def setHorizontalScrollBarPolicy(self, policy):
        if policy == Qt.ScrollBarPolicy.ScrollBarAsNeeded:
            self._hor_scroll_pol = "as"
        elif policy == Qt.ScrollBarPolicy.ScrollBarAlwaysOff:
            self._hor_scroll_pol = "off"
        else:
            self._hor_scroll_pol = "on"
        self.reload_scrollbars()
        self.content_widget.resize(self.content_widget.sizeHint())

    def verticalScrollBarPolicy(self):
        if self._vert_scroll_pol == "as":
            return Qt.ScrollBarPolicy.ScrollBarAsNeeded
        elif self._vert_scroll_pol == "off":
            return Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        else:
            return Qt.ScrollBarPolicy.ScrollBarAlwaysOn

    def horizontalScrollBarPolicy(self):
        if self._hor_scroll_pol == "as":
            return Qt.ScrollBarPolicy.ScrollBarAsNeeded
        elif self._hor_scroll_pol == "off":
            return Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        else:
            return Qt.ScrollBarPolicy.ScrollBarAlwaysOn

    def updateContentPosition(self, value):
        # Update the position of the content widget based on the scrollbar values
        self.content_widget.move(-self._h_scrollbar.value(), -self._v_scrollbar.value())

    def reload_scrollbars(self):
        # print(self._v_scrollbar.value())
        # print(self._h_scrollbar.value())
        content_size = self.content_widget.sizeHint()
        content_size_2 = self.content_widget.size()

        # Check if scrollbars are needed
        if (content_size.height() > self.height() and self._vert_scroll_pol == "as") or self._vert_scroll_pol == "on":
            self._v_scrollbar.setVisible(True)
            self._v_scrollbar.setPageStep(self.height())
        else:
            self._v_scrollbar.setVisible(False)
        max_v_scroll = max(0, content_size.height() - self.height())
        self._v_scrollbar.setRange(0, max_v_scroll)

        if (content_size_2.width() > self.width() and self._hor_scroll_pol == "as") or self._hor_scroll_pol == "on":
            self._h_scrollbar.setVisible(True)
            self._h_scrollbar.setPageStep(self.width())
        else:
            self._h_scrollbar.setVisible(False)
        max_h_scroll = max(0, content_size_2.width() - self.width())
        self._h_scrollbar.setRange(0, max_h_scroll)

        if self._h_scrollbar.isVisible() and self._v_scrollbar.isVisible():
            self.corner_widget.show()
        else:
            self.corner_widget.hide()
        self.corner_widget.setFixedSize(self._v_scrollbar.width(), self._h_scrollbar.height())
        self.updateContentPosition(0)

    def resizeEvent(self, event):
        # Get the original size of the content widget
        original_content_size = self.content_widget.sizeHint()
        original_content_size.setWidth(event.size().width())

        self.recorded_default_size = original_content_size

        # Resize the content widget to match the original size
        self.content_widget.resize(original_content_size)

        #for widget in [self.content_widget.layout().itemAt(i).widget() for i in range(self.content_widget.layout().count())]:
        #    if hasattr(widget, "pixmap") and widget.pixmap():
        #        widget.resize(widget.pixmap().width(), widget.pixmap().height())

        self.reload_scrollbars()

        event.accept()

    def wheelEvent(self, event):
        # Scroll with the mouse wheel
        delta = event.angleDelta().y()
        self._v_scrollbar.setValue(self._v_scrollbar.value() - delta // 8)


class QAdvancedSmoothScrollingArea(CustomScrollArea):
    def __init__(self, parent=None, sensitivity: int = 1):
        super().__init__(parent)
        # self.setWidgetResizable(True)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.horizontalScrollBar().setSingleStep(24)
        self.verticalScrollBar().setSingleStep(24)

        # Scroll animations for both scrollbars
        self.v_scroll_animation = QPropertyAnimation(self.verticalScrollBar(), b"value")
        self.h_scroll_animation = QPropertyAnimation(self.horizontalScrollBar(), b"value")
        for anim in (self.v_scroll_animation, self.h_scroll_animation):
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            anim.setDuration(500)

        self.sensitivity = sensitivity

        # Scroll accumulators
        self.v_toScroll = 0
        self.h_toScroll = 0

        self.primary_scrollbar = "vertical"

    def set_primary_scrollbar(self, new_primary_scrollbar: _ty.Literal["vertical", "horizontal"]):
        self.primary_scrollbar = new_primary_scrollbar

    def change_scrollbar_state(self, scrollbar: _ty.Literal["vertical", "horizontal"], state: bool = False):
        state = Qt.ScrollBarPolicy.ScrollBarAsNeeded if state else Qt.ScrollBarPolicy.ScrollBarAlwaysOff

        self.setVerticalScrollBarPolicy(state)
        self.setHorizontalScrollBarPolicy(state)

    def wheelEvent(self, event: QWheelEvent):
        horizontal_event_dict = {
            "scroll_bar": self.horizontalScrollBar(),
            "animation": self.h_scroll_animation,
            "toScroll": self.h_toScroll
        }
        vertical_event_dict = {
            "scroll_bar": self.verticalScrollBar(),
            "animation": self.v_scroll_animation,
            "toScroll": self.v_toScroll
        }

        # Choose scroll bar based on right mouse button state
        if event.buttons() & Qt.MouseButton.RightButton:
            event_dict = horizontal_event_dict if self.primary_scrollbar == "vertical" else vertical_event_dict
        else:
            event_dict = vertical_event_dict if self.primary_scrollbar == "vertical" else horizontal_event_dict

        angle_delta = event.angleDelta().y()
        steps = angle_delta / 120
        pixel_step = int(event_dict.get("scroll_bar").singleStep() * self.sensitivity)

        if event_dict.get("animation").state() == QPropertyAnimation.State.Running:
            event_dict.get("animation").stop()
            event_dict["toScroll"] += event_dict.get("animation").endValue() - event_dict.get("scroll_bar").value()

        current_value = event_dict.get("scroll_bar").value()
        max_value = event_dict.get("scroll_bar").maximum()
        min_value = event_dict.get("scroll_bar").minimum()

        # Inverted scroll direction calculation
        event_dict["toScroll"] -= pixel_step * steps
        proposed_value = current_value + event_dict["toScroll"]  # Reflecting changes

        if proposed_value > max_value and steps > 0:
            event_dict["toScroll"] = 0
        elif proposed_value < min_value and steps < 0:
            event_dict["toScroll"] = 0

        new_value = current_value + event_dict["toScroll"]
        event_dict.get("animation").setStartValue(current_value)
        event_dict.get("animation").setEndValue(new_value)
        event_dict.get("animation").start()

        event.accept()  # Prevent further processing of the event


class MVMainWindow(QMainWindow):
    icons_folder: str = ""

    def __init__(self) -> None:
        super().__init__()

    def setup_gui(self) -> None:
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.window_layout = QVBoxLayout(central_widget)

        # Scroll Area
        self.scrollarea = QAdvancedSmoothScrollingArea(self, 1)
        self.scrollarea.setWidgetResizable(True)
        self.scrollarea.verticalScrollBar().setSingleStep(24)
        self.window_layout.addWidget(self.scrollarea)

        # Content widgets
        # content_widget = QWidget()
        # self.scrollarea.setWidget(content_widget)
        self.content_layout = self.scrollarea.content_layout  # QVBoxLayout(content_widget)

        # Enable kinetic scrolling
        scroller = QScroller.scroller(self.scrollarea.viewport())
        scroller.grabGesture(self.scrollarea.viewport(), QScroller.ScrollerGestureType.TouchGesture)
        scroller_properties = QScrollerProperties(scroller.scrollerProperties())
        scroller_properties.setScrollMetric(QScrollerProperties.ScrollMetric.MaximumVelocity, 0.3)
        scroller.setScrollerProperties(scroller_properties)

        # Add buttons at the end of the content, side by side
        self.buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(self.buttons_widget)
        previous_chapter_button = QPushButton("Previous")
        buttons_layout.addWidget(previous_chapter_button)
        next_chapter_button = QPushButton("Next")
        buttons_layout.addWidget(next_chapter_button)

        # Overlay
        self.overlay = QWidget(self)
        self.overlay.hide()
        self.full_search_frame = QFrame(self)
        self.full_search_frame.setObjectName("searchMenu")
        self.full_search_frame.setFixedSize(int(self.width() * 0.6), int(self.height() * 0.4))
        self.full_search_frame.move(int(self.width() * 0.2), int(self.height() * 0.3))
        self.full_search_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.full_search_frame.setAutoFillBackground(True)
        self.full_search_frame.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QFrame {
                border-radius: 15px;
            }
            QLineEdit, QPushButton, QListWidget {
                border: 2px solid gray;
                border-radius: 10px;
                padding: 10px;
                background-color: white;
                font-size: 16px;
                margin-bottom: 5px; /* Adds a bit of space between the search bar and list */
            }
            QListWidget {
                margin-top: -5px; /* Reduces space above the list, making it closer to the QLineEdit */
                min-height: 100px; /* Ensures it's always slightly elevated in appearance */
            }
            QLabel, QListWidgetItem {
                border-radius: 5px;
                padding: 5px;
                background-color: #f0f0f0;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)

        # Top layout for close button
        top_layout = QHBoxLayout()
        top_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Close button
        self.full_search_close_button = QPushButton("×")
        self.full_search_close_button.setFixedSize(42, 42)
        self.full_search_close_button.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.full_search_close_button.clicked.connect(self.end_full_search)

        # Add close button to the top layout
        top_layout.addStretch()
        top_layout.addWidget(self.full_search_close_button)

        self.full_search_layout = QVBoxLayout(self.full_search_frame)
        self.full_search_layout.addLayout(top_layout)
        self.full_search_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.full_search_widget = SearchWidget(lambda: None)  # TODO:FIX (self.perform_full_search)
        self.full_search_widget.search_bar.textChanged.disconnect()
        self.full_search_widget.search_bar.returnPressed.disconnect()
        self.full_search_widget.search_bar.returnPressed.connect(self.full_search_widget.on_text_changed)
        # TODO: self.full_search_widget.selectedItem.connect(self.handle_full_search_result)
        self.full_search_layout.addWidget(self.full_search_widget)
        self.full_search_frame.hide()

        # Add a transparent image on the top left
        self.transparent_image = QLabel(self)
        self.transparent_image.setObjectName("transparentImage")
        self.transparent_image.setPixmap(QPixmap(os.path.abspath(f"{self.icons_folder}/empty.png")))
        self.transparent_image.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        opacity = QGraphicsOpacityEffect(self.transparent_image)
        opacity.setOpacity(0.5)  # Adjust the opacity level
        self.transparent_image.setGraphicsEffect(opacity)
        self.transparent_image.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        # Search Toggle Button
        self.search_bar_toggle_button = QPushButton("^", self)
        self.search_bar_toggle_button.setFixedHeight(20)  # Set fixed height, width will be set in resizeEvent
        self.search_bar_toggle_button.move(0, 0)

        # Search Bar
        self.search_widget = SearchWidget(lambda: None)
        self.search_widget.adjustSize()
        self.search_widget.search_bar.setMinimumHeight(30)
        self.search_widget.setMinimumHeight(30)
        self.search_widget.move(0, -self.search_widget.height())  # Initially hide the search bar
        self.search_widget.setParent(self)

        # Search Bar Animation
        self.search_bar_animation = QPropertyAnimation(self.search_widget, b"geometry")
        self.search_bar_animation.setDuration(300)

        # Side Menu
        self.side_menu = QFrame(self)
        self.side_menu.setObjectName("sideMenu")
        self.side_menu.setFrameShape(QFrame.Shape.StyledPanel)
        self.side_menu.setAutoFillBackground(True)
        self.side_menu.move(int(self.width() * 2 / 3), 0)
        self.side_menu.resize(int(self.width() / 3), self.height())

        # Animation for Side Menu
        self.side_menu_animation = QPropertyAnimation(self.side_menu, b"geometry")
        self.side_menu_animation.setDuration(500)

        # Side Menu Layout & Widgets
        side_menu_layout = QFormLayout(self.side_menu)
        self.side_menu.setLayout(side_menu_layout)

        self.provider_combobox = CustomComboBox()
        provider_layout = QHBoxLayout()
        provider_layout.addWidget(QLabel("Provider:"))
        provider_layout.addWidget(self.provider_combobox)
        side_menu_layout.addRow(provider_layout)

        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Title:"))
        self.title_selector = QLineEdit()
        self.title_selector.setMinimumWidth(120)
        title_layout.addWidget(self.title_selector)
        side_menu_layout.addRow(title_layout)

        self.chapter_selector = QLineEdit()
        side_menu_layout.addRow(QLabel("Chapter:"), self.chapter_selector)
        self.chapter_selector.setValidator(QDoubleValidator(0.5, 999.5, 1))

        self.chapter_rate_selector = QLineEdit()
        side_menu_layout.addRow(QLabel("Chapter Rate:"), self.chapter_rate_selector)
        self.chapter_selector.setValidator(QDoubleValidator(0.1, 2, 1))

        self.provider_type_combobox = QComboBox(self)
        self.provider_type_combobox.addItem("Indirect", 0)
        self.provider_type_combobox.addItem("Direct", 1)
        side_menu_layout.addRow(self.provider_type_combobox, QLabel("Provider Type"))

        previous_chapter_button_side_menu = QPushButton("Previous")
        next_chapter_button_side_menu = QPushButton("Next")
        self.reload_chapter_button = QPushButton(QIcon(f"{self.icons_folder}/empty.png"), "")
        self.reload_content_button = QPushButton(QIcon(f"{self.icons_folder}/empty.png"), "")

        side_menu_buttons_layout = QHBoxLayout()
        side_menu_buttons_layout.addWidget(previous_chapter_button_side_menu)
        side_menu_buttons_layout.addWidget(next_chapter_button_side_menu)
        side_menu_buttons_layout.addWidget(self.reload_chapter_button)
        side_menu_buttons_layout.addWidget(self.reload_content_button)
        side_menu_layout.addRow(side_menu_buttons_layout)

        [side_menu_layout.addRow(QWidget()) for _ in range(3)]

        full_search_button = QPushButton("Full Search")
        side_menu_layout.addRow(full_search_button)

        [side_menu_layout.addRow(QWidget()) for _ in range(3)]

        self.hover_effect_all_checkbox = QCheckBox("Hover effect all")
        self.borderless_checkbox = QCheckBox("Borderless")
        hover_borderless_layout = QHBoxLayout()
        hover_borderless_layout.setContentsMargins(0, 0, 0, 0)
        hover_borderless_layout.addWidget(self.hover_effect_all_checkbox)
        hover_borderless_layout.addWidget(self.borderless_checkbox)
        self.acrylic_menus_checkbox = QCheckBox("Acrylic Menus")
        self.acrylic_background_checkbox = QCheckBox("Acrylic Background")
        acrylic_layout = QHBoxLayout()
        acrylic_layout.setContentsMargins(0, 0, 0, 0)
        acrylic_layout.addWidget(self.acrylic_menus_checkbox)
        acrylic_layout.addWidget(self.acrylic_background_checkbox)
        side_menu_layout.addRow(hover_borderless_layout)
        side_menu_layout.addRow(acrylic_layout)

        [side_menu_layout.addRow(QWidget()) for _ in range(3)]

        # Scale checkboxes
        self.downscale_checkbox = QCheckBox("Downscale if larger than window")
        self.upscale_checkbox = QCheckBox("Upscale if smaller than window")
        self.lazy_loading_checkbox = QCheckBox("LL")
        lazy_loading_layout = QHBoxLayout()
        lazy_loading_layout.setContentsMargins(0, 0, 0, 0)
        lazy_loading_layout.addWidget(self.upscale_checkbox)
        lazy_loading_layout.addWidget(self.lazy_loading_checkbox)
        side_menu_layout.addRow(self.downscale_checkbox)
        side_menu_layout.addRow(lazy_loading_layout)

        # SpinBox for manual width input and Apply Button
        self.manual_width_spinbox = QSpinBox()
        self.manual_width_spinbox.setRange(10, 2000)
        side_menu_layout.addRow(self.manual_width_spinbox)

        apply_manual_width_button = QPushButton("Apply Width")
        side_menu_layout.addRow(apply_manual_width_button)

        [side_menu_layout.addRow(QWidget()) for _ in range(3)]

        # Window style checkboxes
        self.hide_title_bar_checkbox = QCheckBox("Hide titlebar")
        self.hide_scrollbar_checkbox = QCheckBox("Hide Scrollbar")
        hide_layout = QHBoxLayout()
        hide_layout.setContentsMargins(0, 0, 0, 0)
        hide_layout.addWidget(self.hide_title_bar_checkbox)
        hide_layout.addWidget(self.hide_scrollbar_checkbox)
        side_menu_layout.addRow(hide_layout)
        self.stay_on_top_checkbox = QCheckBox("Stay on top")
        side_menu_layout.addRow(self.stay_on_top_checkbox)

        [side_menu_layout.addRow(QWidget()) for _ in range(3)]

        self.scroll_sensitivity_scroll_bar = QScrollBar(Qt.Orientation.Horizontal)
        self.scroll_sensitivity_scroll_bar.setMinimum(1)  # QScrollBar uses integer values
        self.scroll_sensitivity_scroll_bar.setMaximum(80)  # We multiply by 10 to allow decimal
        self.scroll_sensitivity_scroll_bar.setValue(10)  # Default value set to 1.0 (10 in this scale)
        self.scroll_sensitivity_scroll_bar.setSingleStep(1)
        self.scroll_sensitivity_scroll_bar.setPageStep(1)

        # Label to display the current sensitivity
        self.sensitivity_label = QLabel("Current Sensitivity: 1.0")
        side_menu_layout.addRow(self.sensitivity_label, self.scroll_sensitivity_scroll_bar)

        [side_menu_layout.addRow(QWidget()) for _ in range(3)]

        self.save_last_titles_checkbox = QCheckBox("Save last titles")
        side_menu_layout.addRow(self.save_last_titles_checkbox)
        export_settings_button = QPushButton("Export Settings")
        advanced_settings_button = QPushButton("Adv Settings")
        side_menu_layout.addRow(export_settings_button, advanced_settings_button)

        # Menu Button
        self.menu_button = QPushButton(QIcon(f"{self.icons_folder}/empty.png"), "", self.centralWidget())
        self.menu_button.setFixedSize(40, 40)

        # Timer to regularly check for resizing needs
        timer = QTimer(self)
        timer.start(500)

        # TODO: Connect GUI components
        # self.search_bar_toggle_button.clicked.connect(self.toggle_search_bar)
        # # Checkboxes
        # self.downscale_checkbox.toggled.connect(self.downscale_checkbox_toggled)
        # self.upscale_checkbox.toggled.connect(self.upscale_checkbox_toggled)
        # self.borderless_checkbox.toggled.connect(self.reload_borderless_setting)
        # self.acrylic_menus_checkbox.toggled.connect(self.reload_acrylic_menus_setting)
        # self.acrylic_background_checkbox.toggled.connect(self.reload_acrylic_background_setting)
        # self.hide_scrollbar_checkbox.toggled.connect(self.reload_hide_scrollbar_setting)
        # self.stay_on_top_checkbox.toggled.connect(self.reload_stay_on_top_setting)
        # self.hide_title_bar_checkbox.toggled.connect(self.reload_hide_titlebar_setting)
        # self.hover_effect_all_checkbox.toggled.connect(self.reload_hover_effect_all_setting)
        # self.save_last_titles_checkbox.toggled.connect(self.toggle_save_last_titles_checkbox)
        # # Selectors
        # self.title_selector.textChanged.connect(self.set_title)
        # self.chapter_selector.textChanged.connect(self.set_chapter)
        # self.chapter_rate_selector.textChanged.connect(self.set_chapter_rate)
        # # Menu components
        # self.menu_button.clicked.connect(self.toggle_side_menu)  # Menu
        # apply_manual_width_button.clicked.connect(self.apply_manual_content_width)  # Menu
        # previous_chapter_button.clicked.connect(self.previous_chapter)  # Menu
        # next_chapter_button.clicked.connect(self.next_chapter)  # Menu
        # self.reload_chapter_button.clicked.connect(self.reload_chapter)  # Menu
        # self.reload_content_button.clicked.connect(self.reload)  # Menu
        # previous_chapter_button_side_menu.clicked.connect(self.previous_chapter)
        # next_chapter_button_side_menu.clicked.connect(self.next_chapter)
        # advanced_settings_button.clicked.connect(self.advanced_settings)  # Menu
        # export_settings_button.clicked.connect(self.export_settings)  # Menu
        # full_search_button.clicked.connect(self.open_full_search)  # Menu
        # # Rest
        # self.provider_combobox.currentIndexChanged.connect(self.change_provider)  # Menu
        # self.provider_type_combobox.currentIndexChanged.connect(self.change_provider_type)
        # self.side_menu_animation.valueChanged.connect(self.side_menu_animation_value_changed)  # Menu
        # timer.timeout.connect(self.timer_tick)
        # self.search_bar_animation.valueChanged.connect(self.search_bar_animation_value_changed)
        # self.search_widget.selectedItem.connect(self.selected_chosen_result)
        # self.scroll_sensitivity_scroll_bar.valueChanged.connect(self.update_sensitivity)

        # Style GUI components
        self.centralWidget().setStyleSheet("background: transparent;")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.content_layout.setSpacing(0)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.menu_button.setIcon(QIcon(f"{self.icons_folder}/menu_icon.png"))
        # if self.theme == "light":
        #     self.reload_chapter_button.setIcon(QIcon(f"{self.data_folder}/reload_chapter_icon_dark.png"))
        #     self.reload_content_button.setIcon(QIcon(f"{self.data_folder}/reload_icon_dark.png"))
        # else:
        #     self.reload_chapter_button.setIcon(QIcon(f"{self.data_folder}/reload_chapter_icon_light.png"))
        #     self.reload_content_button.setIcon(QIcon(f"{self.data_folder}/reload_icon_light.png"))

    def set_overlay_visibility(self, visibility: bool = False):
        self.overlay.raise_()
        if not visibility and self.overlay.isVisible():
            self.overlay.hide()
        elif not self.overlay.isVisible():
            # Set the overlay size to match the main window size
            self.overlay.resize(self.size())
            # Ensure the overlay is positioned at the top left corner
            self.overlay.move(0, 0)
            # Set the overlay background to semi-transparent black
            self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 128);")
            self.overlay.show()

    def end_full_search(self):
        self.set_overlay_visibility(False)
        self.full_search_frame.hide()

    def set_scroll_speed(self, value: float) -> None:
        self.scrollarea.sensitivity = value


class QSmoothScrollingList(QListWidget):
    def __init__(self, parent=None, sensitivity: int = 1):
        super().__init__(parent)
        # self.setWidgetResizable(True)

        # Scroll animation setup
        self.scroll_animation = QPropertyAnimation(self.verticalScrollBar(), b"value")
        self.scroll_animation.setEasingCurve(QEasingCurve.Type.OutCubic)  # Smoother deceleration
        self.scroll_animation.setDuration(50)  # Duration of the animation in milliseconds

        self.sensitivity = sensitivity
        self.toScroll = 0  # Total amount left to scroll

    def wheelEvent(self, event: QWheelEvent):
        angle_delta = event.angleDelta().y()
        steps = angle_delta / 120  # Standard steps calculation for a wheel event
        pixel_step = int(self.verticalScrollBar().singleStep() * self.sensitivity)

        if self.scroll_animation.state() == QPropertyAnimation.State.Running:
            self.scroll_animation.stop()
            self.toScroll += self.scroll_animation.endValue() - self.verticalScrollBar().value()

        current_value = self.verticalScrollBar().value()
        max_value = self.verticalScrollBar().maximum()
        min_value = self.verticalScrollBar().minimum()

        # Adjust scroll direction and calculate proposed scroll value
        self.toScroll -= pixel_step * steps
        proposed_value = current_value + self.toScroll

        # Prevent scrolling beyond the available range
        if proposed_value > max_value and steps > 0:
            self.toScroll = 0
        elif proposed_value < min_value and steps < 0:
            self.toScroll = 0

        new_value = current_value + self.toScroll
        self.scroll_animation.setStartValue(current_value)
        self.scroll_animation.setEndValue(new_value)
        self.scroll_animation.start()
        self.toScroll = 0
        event.accept()  # Mark the event as handled


class AdvancedSettingsDialog(QDialog):
    def __init__(self, parent=None, current_settings: dict = None, default_settings: dict = None, master=None,
                 available_themes=None):
        super().__init__(parent, Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowTitleHint)

        if default_settings is None:
            self.default_settings = {"recent_titles": [],
                                     "themes": {"light": "light_light", "dark": "dark", "font": "Segoe UI"},
                                     "settings_file_path": "",
                                     "settings_file_mode": "overwrite",
                                     "misc": {"auto_export": False, "num_workers": 10}}
        else:
            self.default_settings = default_settings
        if current_settings is None:
            current_settings = self.default_settings
        self.current_settings = current_settings
        self.selected_settings = None
        self.master = master

        if available_themes is None:
            available_themes = ('light', 'light_light', 'dark', 'light_dark', 'modern', 'old', 'default')
        self.available_themes = tuple(self._format_theme_name(theme_name) for theme_name in available_themes)

        self.setWindowTitle("Advanced Settings")
        self.resize(600, 300)

        self.mainLayout = QVBoxLayout()
        self.setLayout(self.mainLayout)

        # Recent Titles List
        self.recentTitlesGroupBox = QGroupBox("Recent Titles", self)
        self.recentTitlesLayout = QVBoxLayout(self.recentTitlesGroupBox)
        self.recentTitlesList = QSmoothScrollingList(self.recentTitlesGroupBox)
        self.recentTitlesList.itemActivated.connect(self.selected_title)
        self.recentTitlesList.verticalScrollBar().setSingleStep(1)
        self.recentTitlesLayout.addWidget(self.recentTitlesList)
        self.mainLayout.addWidget(self.recentTitlesGroupBox)

        # Theme Selection
        self.themeGroupBox = QGroupBox("Styling", self)
        self.themeLayout = QFormLayout(self.themeGroupBox)
        self.lightThemeComboBox = QComboBox(self.themeGroupBox)
        self.darkThemeComboBox = QComboBox(self.themeGroupBox)
        self.lightThemeComboBox.addItems(self.available_themes)
        self.darkThemeComboBox.addItems(self.available_themes)
        self.fontComboBox = QFontComboBox(self.themeGroupBox)
        self.fontComboBox.currentFontChanged.connect(self.change_font)
        self.themeLayout.addRow(QLabel("Light Mode Theme:"), self.lightThemeComboBox)
        self.themeLayout.addRow(QLabel("Dark Mode Theme:"), self.darkThemeComboBox)
        self.themeLayout.addRow(QLabel("Font:"), self.fontComboBox)
        self.mainLayout.addWidget(self.themeGroupBox)

        # Settings File Handling
        self.fileHandlingGroupBox = QGroupBox("Settings File Handling", self)
        self.fileHandlingLayout = QVBoxLayout(self.fileHandlingGroupBox)
        self.fileLocationLineEdit = QLineEdit(self.fileHandlingGroupBox)
        self.fileLocationLineEdit.setPlaceholderText("File Location")
        self.fileLocationToolButton = QToolButton(self.fileHandlingGroupBox)
        self.fileLocationToolButton.setText("...")
        self.fileLocationToolButton.clicked.connect(self.get_file_location)
        self.fileLocationLayout = QHBoxLayout()
        self.fileLocationLayout.addWidget(self.fileLocationLineEdit)
        self.fileLocationLayout.addWidget(self.fileLocationToolButton)
        self.overwriteRadioButton = QRadioButton("Overwrite", self.fileHandlingGroupBox)
        self.modifyRadioButton = QRadioButton("Modify", self.fileHandlingGroupBox)
        self.createNewRadioButton = QRadioButton("Create New", self.fileHandlingGroupBox)
        self.overwriteRadioButton.setChecked(True)
        self.loadSettingsPushButton = QPushButton("Load Settings File")
        self.loadSettingsPushButton.clicked.connect(self.load_settings_file)
        last_layout = QNoSpacingBoxLayout(QBoxDirection.LeftToRight)
        last_layout.addWidget(self.createNewRadioButton)
        last_layout.addStretch()
        last_layout.addWidget(self.loadSettingsPushButton)
        self.fileHandlingLayout.addLayout(self.fileLocationLayout)
        self.fileHandlingLayout.addWidget(self.overwriteRadioButton)
        self.fileHandlingLayout.addWidget(self.modifyRadioButton)
        self.fileHandlingLayout.addLayout(last_layout)
        self.mainLayout.addWidget(self.fileHandlingGroupBox)

        # Auto-Export and Workers
        self.miscSettingsGroupBox = QGroupBox("Miscellaneous Settings", self)
        self.miscSettingsLayout = QFormLayout(self.miscSettingsGroupBox)
        self.autoExportCheckBox = QCheckBox("Enable Auto-Export", self.miscSettingsGroupBox)
        self.workersSpinBox = QSpinBox(self.miscSettingsGroupBox)
        self.workersSpinBox.setRange(1, 20)
        self.workersSpinBox.setValue(10)
        self.miscSettingsLayout.addRow(self.autoExportCheckBox)
        self.miscSettingsLayout.addRow(QLabel("Number of Full-Search Workers:"), self.workersSpinBox)
        self.mainLayout.addWidget(self.miscSettingsGroupBox)

        self.load_settings(self.current_settings)

        # Buttons for actions
        self.buttonsLayout = QHBoxLayout()

        self.revertLastButton = QPushButton("Revert to Last Saved", self)
        self.defaultButton = QPushButton("Revert to Default", self)
        self.buttonsLayout.addWidget(self.revertLastButton)
        self.buttonsLayout.addWidget(self.defaultButton)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.buttonsLayout.addWidget(self.buttonBox)

        self.mainLayout.addLayout(self.buttonsLayout)

        # Connect revert buttons
        self.revertLastButton.clicked.connect(self.revert_last_saved)
        self.defaultButton.clicked.connect(self.revert_to_default)

        QTimer.singleShot(10, self.fix_size)

    def fix_size(self):
        self.setFixedSize(self.size())

    def selected_title(self, item):
        name = item.text()
        if not self.master.settings.is_open:
            self.master.settings.connect()
        self.reject()
        self.master.set_overlay_visibility(False)
        self.master.selected_chosen_result(name, toggle_search_bar=False)
        self.master.toggle_side_menu()

    def get_file_location(self):
        file_path, _ = QFileDialog.getSaveFileName(self, 'Choose/Save File', self.fileLocationLineEdit.text(),
                                                  'DataBase Files (*.db);;Json Files (*.json *.yaml *.yml)',
                                                  'Json Files (*.json *.yaml *.yml)'
                                                   if self.fileLocationLineEdit.text().endswith((".json", ".yaml", ".yml"))
                                                   else 'DataBase Files (*.db)')
        if not file_path:  # No file was selected
            return
        self.fileLocationLineEdit.setText(file_path)

    def load_settings_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Choose File', self.fileLocationLineEdit.text(),
                                                  'DataBase Files (*.db);;Json Files (*.json *.yaml *.yml)',
                                                  'Json Files (*.json *.yaml *.yml)'
                                                   if self.fileLocationLineEdit.text().endswith((".json", ".yaml", ".yml"))
                                                   else 'DataBase Files (*.db)')
        if not file_path:  # No file was selected
            return

        if file_path.endswith(".db"):
            self.replace_database(file_path)
        elif file_path.endswith((".json", ".yaml")):
            self.import_settings_from_json(file_path)

        if not self.master.settings.is_open:
            self.master.settings.connect()
        self.master.reload_window_title()
        self.master.reload_gui()
        self.reject()

    def replace_database(self, new_db_path):
        """Replace the existing settings database with a new one."""
        temp_path = os.path.join(self.master._data_folder, "temp_data.db")
        try:
            # Safely attempt to replace the database
            shutil.copyfile(new_db_path, temp_path)
            os.remove(os.path.join(self.master._data_folder, "data.db"))
            shutil.move(temp_path, os.path.join(self.master._data_folder, "data.db"))
        except Exception as e:
            print(f"Failed to replace the database: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def import_settings_from_json(self, json_path):
        """Import settings from a JSON file into the SQLite database."""
        try:
            with open(json_path, 'r') as file:
                settings_data = json.load(file).get("settings")

            db_path = os.path.join(self.master._data_folder, "data.db")
            connection = sqlite3.connect(db_path)
            cursor = connection.cursor()

            # Assuming the table and columns for settings already exist and are named appropriately
            for dic in settings_data:
                key, value = dic["key"], dic["value"]
                cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))

            connection.commit()
        except json.JSONDecodeError:
            print("Invalid JSON file.")
        except Exception as e:
            print(f"Error while importing settings from JSON: {e}")
        finally:
            cursor.close()
            connection.close()

    def _format_theme_name(self, theme_name: str):
        """
        Formats the theme name by adding parentheses if needed and appending ' Theme' if the name includes 'light' or 'dark'.

        Args:
        theme (str): The theme name.

        Returns:
        str: The formatted theme name.
        """
        # Add parentheses to the first word if there are more than 2
        formatted_name = ("(" if "_" in theme_name else "") + theme_name.replace("_", ") ", 1).replace("_", " ").title()

        # Append 'Theme' if 'light' or 'dark' is part of the theme name
        if "light" in theme_name or "dark" in theme_name:
            formatted_name += " Theme"

        return formatted_name

    def load_settings(self, settings: dict):
        self.recentTitlesList.clear()
        recent_titles = settings.get("recent_titles")
        recent_titles.reverse()
        self.recentTitlesList.addItems((' '.join(word[0].upper() + word[1:] if word else '' for word in title.split()) for title in recent_titles))

        light_theme = settings.get("themes").get("light")
        dark_theme = settings.get("themes").get("dark")
        self.lightThemeComboBox.setCurrentText(self._format_theme_name(light_theme))
        self.darkThemeComboBox.setCurrentText(self._format_theme_name(dark_theme))
        self.fontComboBox.setCurrentText(settings.get("themes").get("font"))

        self.fileLocationLineEdit.setText(settings.get("settings_file_path", ""))

        sett_mode = settings.get("settings_file_mode")
        if sett_mode == "overwrite":
            self.overwriteRadioButton.setChecked(True)
            self.modifyRadioButton.setChecked(False)
            self.createNewRadioButton.setChecked(False)
        elif sett_mode == "modify":
            self.overwriteRadioButton.setChecked(False)
            self.modifyRadioButton.setChecked(True)
            self.createNewRadioButton.setChecked(False)
        else:
            self.overwriteRadioButton.setChecked(False)
            self.modifyRadioButton.setChecked(False)
            self.createNewRadioButton.setChecked(True)

        self.autoExportCheckBox.setChecked(settings.get("misc").get("auto_export") is True)
        self.workersSpinBox.setValue(settings.get("misc").get("num_workers"))

    def revert_last_saved(self):
        # Logic to revert settings to the last saved state
        self.load_settings(self.current_settings)

    def revert_to_default(self):
        # Logic to reset settings to their defaults
        self.load_settings(self.default_settings)

    def change_font(self, font):
        base_font_size = 8
        dpi = self.parent().app.primaryScreen().logicalDotsPerInch()
        scale_factor = dpi / 96
        scaled_font_size = base_font_size * scale_factor
        font = QFont(self.fontComboBox.currentText(), scaled_font_size)

        self.setFont(font)
        for child in self.findChildren(QWidget):
            child.setFont(font)
        self.update()
        self.repaint()

    def _save_theme(self, theme_display_name):
        stripped_theme_name = theme_display_name.lstrip("(").lower().replace(") ", "_")
        if "light" in stripped_theme_name or "dark" in stripped_theme_name:
            stripped_theme_name = stripped_theme_name.removesuffix(" theme")
        return stripped_theme_name.replace(" ", "_")

    def accept(self):
        # Collect all settings here for processing
        self.selected_settings = {
            "recent_titles": list(reversed([self.recentTitlesList.item(x).text().lower() for x in range(self.recentTitlesList.count())])),
            "themes": {
                "light": self._save_theme(self.lightThemeComboBox.currentText()),
                "dark": self._save_theme(self.darkThemeComboBox.currentText()),
                "font": self.fontComboBox.currentText()},
            "settings_file_path": self.fileLocationLineEdit.text(),
            "settings_file_mode": "overwrite" if self.overwriteRadioButton.isChecked() else "modify" if self.modifyRadioButton.isChecked() else "create_new",
            "misc": {"auto_export": self.autoExportCheckBox.isChecked(),
                     "num_workers": self.workersSpinBox.value()}}

        super().accept()

    def reject(self):
        super().reject()
