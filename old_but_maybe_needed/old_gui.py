"""TBA"""
from PySide6.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsRectItem, QWidget, QFormLayout, QFrame,
                               QGraphicsItem, QGraphicsEllipseItem, QGraphicsWidget, QPushButton,
                               QStyleOptionGraphicsItem, QMainWindow, QStackedLayout, QMessageBox, QSpinBox, QLineEdit,
                               QComboBox, QSlider, QGraphicsTextItem)
from PySide6.QtCore import (Qt, QPointF, QRect, QRectF, QPropertyAnimation, QPoint, Signal, QParallelAnimationGroup,
                            Property, QVariantAnimation, QEasingCurve, QTimer)
from PySide6.QtGui import QPainter, QWheelEvent, QMouseEvent, QCursor, QIcon, QPen, QColor, QDrag, QFont
from PySide6.QtOpenGLWidgets import QOpenGLWidget

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


class Label(QGraphicsTextItem):
    def __init__(self, parent=None):
        super().__init__(parent)

    def mousePressEvent(self, event):
        if isinstance(self.parentItem(), Condition):
            self.parentItem().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if isinstance(self.parentItem(), Condition):
            self.parentItem().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if isinstance(self.parentItem(), Condition):
            self.parentItem().mouseReleaseEvent(event)


class Condition(QGraphicsEllipseItem):

    def __init__(self, x: float, y: float, width: int, height: int, color: Qt.GlobalColor, parent: QWidget | None = None):
        super().__init__(QRectF(x, y, width, height), parent=parent)
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.setBrush(color)
        self.setPen(Qt.PenStyle.NoPen)

        self.label = Label(self)
        self.label.setPlainText('q1')
        self.label.setFont(QFont('Arial', 24, QFont.Bold))
        self.label.setDefaultTextColor(Qt.GlobalColor.black)
        self.update_label_position()

        self.setSelected(False)

    def activate(self):
        self.setPen(QPen(QColor('red'), 3))
        self.setSelected(True)

    def deactivate(self):
        self.setPen(Qt.PenStyle.NoPen)
        self.setSelected(False)

    def update_label_position(self):
        rect = self.rect()
        label_width = self.label.boundingRect().width()
        label_height = self.label.boundingRect().height()
        label_x = rect.x() + (rect.width() - label_width) / 2
        label_y = rect.y() + (rect.height() - label_height) / 2
        self.label.setPos(label_x, label_y)

    def set_name(self, name: str) -> None:
        self.label.setPlainText(name)
        self.update_label_position()

    def set_size(self, size) -> None:
        self.setRect(QRectF(self.rect().x(), self.rect().y(), size, size))
        self.update_label_position()

    def set_color(self, color: Qt.GlobalColor):
        self.setBrush(color)
        self.setPen(Qt.PenStyle.NoPen)

    def mousePressEvent(self, event):
        self.setCursor(Qt.ClosedHandCursor)
        self.old_pos = event.scenePos()

    def mouseMoveEvent(self, event):
        delta = event.scenePos() - self.old_pos
        self.moveBy(delta.x(), delta.y())
        self.old_pos = event.scenePos()

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.ArrowCursor)


class GridView(QGraphicsView):
    """TBA"""
    def __init__(self, parent: QWidget | None = None, grid_size: int = 100, start_x: int = 50, start_y: int = 50,
                 fixed_objects: list[tuple[float, float, QGraphicsItem]] | None = None) -> None:
        super().__init__(parent=parent)
        # self.setViewport(QOpenGLWidget())  # Use OpenGL for rendering?
        self.setCacheMode(QGraphicsView.CacheModeFlag.CacheBackground)
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

    def newCondition(self, pos):
        new_condition = Condition(pos.x() - self._grid_size / 2, pos.y() - self._grid_size / 2,
                                  self._grid_size, self._grid_size, Qt.GlobalColor.lightGray)
        self.scene().addItem(new_condition)

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

    def is_item_at(self, pos: QPoint) -> QGraphicsItem:
        scene_pos = self.mapToScene(pos)
        item = self.scene().itemAt(scene_pos, self.transform())
        return item

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Start panning on right or middle mouse button click."""
        if event.button() in (Qt.MouseButton.RightButton, Qt.MouseButton.MiddleButton):
            self._is_panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.is_item_at(event.pos())
            if isinstance(item, Condition):
                if hasattr(self.parent(), 'toggle_condition_edit_menu'):
                    self.parent().toggle_condition_edit_menu()
                    self.parent().condition_edit_menu.set_token_lists(item)
                    self.parent().condition_edit_menu.name_changed.connect(item.set_name)
                    self.parent().condition_edit_menu.color_changed.connect(item.set_color)
                    self.parent().condition_edit_menu.size_changed.connect(item.set_size)
                item.activate()
            """if item:
                if not item.isSelected():
                    item.activate()
                else:
                    item.deactivate()
                print(item.isSelected())"""
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.is_item_at(event.pos()):
                global_pos = event.pos()
                scene_pos = self.mapToScene(global_pos)
                self.newCondition(scene_pos)
        super().mouseDoubleClickEvent(event)

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
        self.resetCachedContent()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Stop panning on mouse button release."""
        if event.button() in (Qt.MouseButton.RightButton, Qt.MouseButton.MiddleButton):
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)


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

        # Condition Edit Menu
        self.condition_edit_menu = ConditionEditMenu(self)
        self.condition_edit_menu.setGeometry(200, 0, 300, self.height())

        # Animation for Side Menu
        self.side_menu_animation = QPropertyAnimation(self.side_menu, b"geometry")
        self.side_menu_animation.setDuration(500)

        # Animation for Condition Edit Menu
        self.condition_edit_menu_animation = QPropertyAnimation(self.condition_edit_menu, b'geometry')
        self.condition_edit_menu_animation.setDuration(500)

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

    def toggle_condition_edit_menu(self):
        width = max(200, int(self.width() / 4))
        height = self.height()

        if self.condition_edit_menu.x() >= self.width():
            start_value = QRect(self.width(), 0, width, height)
            end_value = QRect(self.width() - width, 0, width, height)
        else:
            start_value = QRect(self.width() - width, 0, width, height)
            end_value = QRect(self.width(), 0, width, height)

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

        self.name_input = QLineEdit(self)
        self.name_input.setText('Placeholder')
        self.name_input.textEdited.connect(self.on_name_changed)

        # Beispiel: Eingabefelder für Einstellungen
        self.color_input = QComboBox(self)
        self.color_input.addItems(('Red', 'Green', 'Blue', 'Yellow', 'Orange', 'Purple', 'Cyan'))
        self.color_input.currentTextChanged.connect(self.on_color_changed)

        self.size_input = QSlider(Qt.Horizontal, self)
        self.size_input.setRange(150, 450)
        self.size_input.setValue(150)
        self.size_input.valueChanged.connect(self.on_size_changed)

        # Füge Widgets zum Layout hinzu
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

    def set_condition(self, condition: Condition) -> None:
        self.condition = condition

    def on_name_changed(self, name: str) -> None:
        self.name_changed.emit(name)

    def on_color_changed(self, color: str) -> None:
        self.color_changed.emit(self.color_mapping.get(color))

    def on_size_changed(self, size: int) -> None:
        self.size_changed.emit(size)


class SettingsPanel(Panel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("background-color: rgba(0, 40, 158, 0.33);")
