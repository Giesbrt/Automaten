"""Everything regarding the infinite grid"""
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsItem, QWidget, QGraphicsEllipseItem
from PySide6.QtGui import QPainter, QWheelEvent, QMouseEvent
from PySide6.QtCore import QRect, QRectF, Qt, QPointF, QPoint

from ._grid_items import Condition

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts


class StaticGridView(QGraphicsView):
    """A static view for observing a QGraphicsScene without interaction."""
    def __init__(self, grid_size: int, scene: QGraphicsScene | None = None,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self.setCacheMode(QGraphicsView.CacheModeFlag.CacheBackground)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

        if scene is not None:
            self.setScene(scene)

        self.grid_size: int = grid_size

    def drawBackground(self, painter: QPainter, rect: QRect | QRectF) -> None:  # Overwrite
        """Draw an infinite grid."""
        left = int(rect.left()) - (int(rect.left()) % self.grid_size)
        top = int(rect.top()) - (int(rect.top()) % self.grid_size)

        line_t = float | int
        lines: list[tuple[line_t, line_t, line_t, line_t]] = []
        for x in range(left, int(rect.right()), self.grid_size):
            lines.append((x, rect.top(), x, rect.bottom()))
        for y in range(top, int(rect.bottom()), self.grid_size):
            lines.append((rect.left(), y, rect.right(), y))

        painter.setPen(Qt.GlobalColor.lightGray)
        for line in lines:
            painter.drawLine(*line)

    def setViewPosition(self, position: tuple[float, float]) -> None:
        """
        Sets the viewport's position within the scene.

        param position: Position to set to
        returns: If the scene was large enough
        """
        self.centerOn(QPointF(*position))

    def setScale(self, scale: float = 1.0) -> None:
        raise NotImplementedError


class InteractiveGridView(StaticGridView):
    """Represents an interactable GridView, it creates its own scene"""
    def __init__(self, grid_size: int = 100, scene_rect: tuple[int, int, int, int] = (-10_000, -10_000, 20_000, 20_000),
                 zoom_level: float = 1.0, zoom_step: float = 0.1, min_zoom: float = 0.2, max_zoom: float = 5.0,
                 parent: QWidget | None = None) -> None:
        super().__init__(grid_size, None, parent)
        self.setScene(QGraphicsScene(self))
        self.scene().setSceneRect(QRect(*scene_rect))

        # Center object (input)
        center_rect = QGraphicsEllipseItem(0, 0, self.grid_size, self.grid_size)
        center_rect.setBrush(Qt.GlobalColor.red)
        center_rect.setPen(Qt.PenStyle.NoPen)
        self.scene().addItem(center_rect)

        # Zoom parameters
        self.zoom_level: float = zoom_level
        self.zoom_step: float = zoom_step
        self.min_zoom: float = min_zoom
        self.max_zoom: float = max_zoom

        # Panning attributes
        self._is_panning: bool = False
        self._pan_start: QPointF = QPointF(0.0, 0.0)

    def setSceneRect(self, rect: tuple[int, int, int, int]):
        self.scene().setSceneRect(QRect(*rect))

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


"""
Please remember to type hint :)
"""
class AutomatonInteractiveGridView(InteractiveGridView):
    def newCondition(self, pos):
        new_condition = Condition(pos.x() - self.grid_size / 2, pos.y() - self.grid_size / 2,
                                  self.grid_size, self.grid_size, Qt.GlobalColor.lightGray)
        self.scene().addItem(new_condition)

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
                    self.parent().condition_edit_menu.set_condition(item)
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
