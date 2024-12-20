"""TBA"""
from PySide6.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsRectItem, QWidget, QFormLayout, QFrame,
                               QGraphicsItem, QGraphicsEllipseItem, QGraphicsWidget, QPushButton,
                               QStyleOptionGraphicsItem, QMainWindow, QStackedLayout, QMessageBox)
from PySide6.QtCore import Qt, QPointF, QRect, QRectF, QPropertyAnimation
from PySide6.QtGui import QPainter, QWheelEvent, QMouseEvent, QCursor, QIcon

from aplustools.io.qtquick import QNoSpacingBoxLayout, QBoxDirection, QQuickBoxLayout, QQuickMessageBox
from aplustools.package.timid import TimidTimer

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts


class MyItem(QGraphicsWidget):
    def __init__(self, node_item):
        super().__init__(parent=None)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.setFlag(QGraphicsWidget.ItemIsMovable, True)
        self.setFlag(QGraphicsWidget.ItemIsSelectable, True)

        self.offset : QPointF = None

    def boundingRect(self) -> QRectF:
        return QRect(0,0,30,30)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = ...) -> None:
        r = QRect(0, 0, 30, 30)
        painter.drawRect(r)

    def mouseMoveEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
        self.moveBy(event.pos().x() - self.offset.x(), event.pos().y() - self.offset.y())


class GridView(QGraphicsView):
    """TBA"""
    def __init__(self, parent: QWidget | None = None, grid_size: int = 100, start_x: int = 50, start_y: int = 50,
                 fixed_objects: list[tuple[float, float, QGraphicsItem]] | None = None) -> None:
        super().__init__(parent=parent)
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

        self._grid_size: int = grid_size
        self._offset: QPointF = QPointF(start_x * grid_size, start_y * grid_size)

        self.scene().setSceneRect(-10000, -10000, 20000, 20000)
        self._objects: list[QGraphicsRectItem] = []

        # Center object (input)
        center_rect = QGraphicsRectItem(0, 0, self._grid_size, self._grid_size)
        center_rect.setBrush(Qt.GlobalColor.red)
        center_rect.setPen(Qt.PenStyle.NoPen)
        self._objects.append(center_rect)

        if fixed_objects is not None:
            for (x, y, item) in fixed_objects:
                item.setPos(x * self._grid_size, y * self._grid_size)
                self._objects.append(item)
        for obj in self._objects:  # Can be combined
            self.scene().addItem(obj)

        self.zoom_level: float = 1  # Zoom parameters
        self.zoom_step: float = 0.1
        self.min_zoom: float = 0.2
        self.max_zoom: float = 5.0

        # Panning attributes
        self._is_panning: bool = False
        self._pan_start: QPointF = QPointF(0, 0)

    def drawBackground(self, painter: QPainter, rect: QRect | QRectF) -> None:  # Overwrite
        """Draw an infinite grid."""
        left = int(rect.left()) - (int(rect.left()) % self._grid_size)
        top = int(rect.top()) - (int(rect.top()) % self._grid_size)

        line_t = float | int
        lines: list[tuple[line_t, line_t, line_t, line_t]] = []
        for x in range(left, int(rect.right()), self._grid_size):
            lines.append((x, rect.top(), x, rect.bottom()))
        for y in range(top, int(rect.bottom()), self._grid_size):
            lines.append((rect.left(), y, rect.right(), y))

        painter.setPen(Qt.GlobalColor.lightGray)
        for line in lines:
            painter.drawLine(*line)

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Zoom in and out with the mouse wheel."""
        if event.angleDelta().y() > 0:
            zoom_factor = 1 + self.zoom_step
        else:
            zoom_factor = 1 - self.zoom_step

        new_zoom: float = self.zoom_level * zoom_factor
        if self.min_zoom <= new_zoom <= self.max_zoom:
            self.scale(zoom_factor, zoom_factor)
            self.zoom_level = new_zoom

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Start panning on right or middle mouse button click."""
        if event.button() in (Qt.MouseButton.RightButton, Qt.MouseButton.MiddleButton):
            self._is_panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._is_panning:
            delta = event.position() - self._pan_start

            # Only process significant deltas
            if abs(delta.x()) > 2 or abs(delta.y()) > 2:
                self.horizontalScrollBar().setValue(
                    self.horizontalScrollBar().value() - int(delta.x())
                )
                self.verticalScrollBar().setValue(
                    self.verticalScrollBar().value() - int(delta.y())
                )
                self._pan_start = event.position()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Stop panning on mouse button release."""
        if event.button() in (Qt.MouseButton.RightButton, Qt.MouseButton.MiddleButton):
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)


class DBMainWindowInterface(QMainWindow):
    """TBA"""
    icons_dir: str

    def __init__(self) -> None:
        super().__init__(parent=None)

    def setup_gui(self) -> None:
        """
        Configure the main graphical user interface (GUI) elements of the MV application.

        This method sets up various widgets, layouts, and configurations required for the
        main window interface. It is called after initialization and prepares the interface
        for user interaction.

        Note:
            This method is intended to be overridden by subclasses with application-specific
            GUI components.
        """
        raise NotImplementedError

    def set_scroll_speed(self, value: float) -> None:
        raise NotImplementedError


class Panel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)


class UserPanel(Panel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.content_layout = QNoSpacingBoxLayout(QBoxDirection.TopToBottom)
        self.setLayout(self.content_layout)
        # Define positions of fixed objects with their respective QGraphicsItems
        fixed_positions = [
            (10, 10, QGraphicsRectItem(0, 0, 100, 100)),  # A rectangle at (10, 10)
            (100, 100, QGraphicsEllipseItem(0, 0, 150, 150)),  # A circle at (100, 100)
            (20, 50, QGraphicsRectItem(0, 0, 75, 75)),  # A smaller rectangle at (20, 50)
            (50, 20, QGraphicsEllipseItem(0, 0, 50, 100)),  # An ellipse at (50, 20)
        ]

        # Customize appearance of the objects if necessary
        for _, _, item in fixed_positions:
            item.setBrush(Qt.GlobalColor.blue)  # Set the fill color to blue
            item.setPen(Qt.PenStyle.NoPen)  # Remove the border
        self.grid_view = GridView(grid_size=100, start_x=50, start_y=50, fixed_objects=fixed_positions)
        self.content_layout.addWidget(self.grid_view)

        # Side Menu
        self.side_menu = QFrame(self)
        self.side_menu.setObjectName("sideMenu")
        self.side_menu.setFrameShape(QFrame.Shape.StyledPanel)
        self.side_menu.setAutoFillBackground(True)

        # Animation for Side Menu
        self.side_menu_animation = QPropertyAnimation(self.side_menu, b"geometry")
        self.side_menu_animation.setDuration(500)

        # Side Menu Layout & Widgets
        side_menu_layout = QFormLayout(self.side_menu)
        self.side_menu.setLayout(side_menu_layout)

        # Menu Button
        self.menu_button = QPushButton(QIcon(), "", self)
        self.menu_button.setFixedSize(40, 40)

        self.menu_button.setIcon(QIcon())

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
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)


class DBMainWindow(DBMainWindowInterface):
    icons_dir: str

    def setup_gui(self) -> None:
        # Central Widget
        central_widget = QWidget()
        # self.setCentralWidget(central_widget)
        # self.window_layout = QQuickBoxLayout(QBoxDirection.LeftToRight, parent=central_widget)

        self.user_panel = UserPanel(parent=self)
        # self.window_layout.addWidget(self.user_panel)
        self.user_panel.setGeometry(0, 0, self.width(), self.height())

        # Animation for Side Menu
        self.user_panel_animation = QPropertyAnimation(self.user_panel, b"geometry")
        self.user_panel_animation.setDuration(500)

        self.settings_panel = SettingsPanel(parent=self)
        # self.window_layout.addWidget(self.settings_panel)
        self.settings_panel.setGeometry(self.width(), 0, self.width(), self.height())

        # Animation for Side Menu
        self.settings_panel_animation = QPropertyAnimation(self.settings_panel, b"geometry")
        self.settings_panel_animation.setDuration(500)
        self.timer = TimidTimer()
        self.timer.interval(1, count="inf", callback=self.switch_panel)

    def switch_panel(self):
        print("Switching ...")
        # self.user_panel.setGeometry(-self.width(), 0, self.width(), self.height())
        # self.settings_panel.setGeometry(0, 0, self.width(), self.height())
        # return
        width = self.width()
        height = self.height()

        user_panel_hidden_value = QRect(-width, 0, width, height)
        shown_panel_end_value = QRect(0, 0, width, height)
        settings_panel_hidden_value = QRect(width, 0, width, height)

        if self.settings_panel.x() == 0:
            print("To user")
            # self.user_panel_animation.setStartValue(user_panel_hidden_value)
            # self.user_panel_animation.setEndValue(shown_panel_end_value)
            # self.settings_panel_animation.setStartValue(shown_panel_end_value)
            # self.settings_panel_animation.setEndValue(settings_panel_hidden_value)
            self.user_panel.setGeometry(shown_panel_end_value)
            self.settings_panel.setGeometry(settings_panel_hidden_value)
        else:
            print("To sett")
            # self.user_panel_animation.setStartValue(shown_panel_end_value)
            # self.user_panel_animation.setEndValue(user_panel_hidden_value)
            # self.settings_panel_animation.setStartValue(settings_panel_hidden_value)
            # self.settings_panel_animation.setEndValue(shown_panel_end_value)
            self.user_panel.setGeometry(user_panel_hidden_value)
            self.settings_panel.setGeometry(shown_panel_end_value)
        # self.user_panel_animation.start()
        # self.settings_panel_animation.start()

    def popup(self, title: str, text: str, description: str, icon: QMessageBox.Icon = QMessageBox.Icon.Information,
              buttons: list[QMessageBox.StandardButton] | QMessageBox.StandardButton = QMessageBox.StandardButton.Ok,
              default_button: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok) -> QMessageBox.StandardButton:
        msg_box = QQuickMessageBox(self, icon, title, text, description,
                                   standard_buttons=buttons,
                                   default_button=default_button)
        return msg_box.exec()

    def set_scroll_speed(self, value: float) -> None:
        return
