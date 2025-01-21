"""Everything regarding the infinite grid"""
import numpy as np
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsItem, QWidget, QGraphicsEllipseItem, QMenu
from PySide6.QtGui import QPainter, QWheelEvent, QMouseEvent, QColor, QAction
from PySide6.QtCore import QRect, QRectF, Qt, QPointF, QPoint

from core.modules.automaton.base.transition import Transition
from core.modules.automaton.base.state import State
from core.modules.automaton.UIAutomaton import UiState, UiTransition, UiAutomaton

from ._grid_items import State, StateGroup, Label, ConnectionPoint, TempTransition, Transition
from ._panels import UserPanel

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
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)

        if scene is not None:
            self.setScene(scene)

        self.grid_size: int = grid_size

        self.horizontalScrollBar().valueChanged.connect(self.resetCachedContent)
        self.verticalScrollBar().valueChanged.connect(self.resetCachedContent)

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


class AutomatonInteractiveGridView(InteractiveGridView):
    """TBA"""
    def __init__(self) -> None:  # TODO: Please remember to type hint :)
        super().__init__()
        self._counter: int = 0
        self._last_active: State | None = None
        self._temp_line: TempTransition | None = None
        self._start_ellipse: ConnectionPoint | None = None

    def get_mapped_position(self, item: QGraphicsItem) -> any:
        scene_pos = item.mapToScene(item.boundingRect().center())
        return self.mapFromScene(scene_pos)

    def get_item_at(self, pos: QPoint) -> QGraphicsItem:
        scene_pos: QPointF = self.mapToScene(pos)
        return self.scene().itemAt(scene_pos, self.transform())

    def new_state(self, pos: QPointF) -> None:
        """TBA"""
        new_state = StateGroup(pos.x() - self.grid_size / 2,
                               pos.y() - self.grid_size / 2,
                               self.grid_size, self.grid_size,
                               self._counter, Qt.GlobalColor.lightGray)
        self.scene().addItem(new_state)
        self._counter += 1

    def delete_item(self):
        print('delete')

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Start panning on right or middle mouse button click."""
        if event.button() == Qt.MouseButton.RightButton:
            if self._temp_line:
                self.scene().removeItem(self._temp_line)
                self._start_ellipse, self._temp_line = None, None
            if isinstance(self.get_item_at(event.pos()), (State, Label)):
                # Erstelle das Kontextmenü
                context_menu = QMenu(self)
                delete_action = QAction("Löschen", self)
                delete_action.triggered.connect(self.delete_item)
                context_menu.addAction(delete_action)

                # Zeige das Menü an
                context_menu.exec(event.globalPos())

        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.button() == Qt.MouseButton.LeftButton:
            clicked_point = self.mapToScene(event.pos())

            item = self.get_item_at(QPoint(int(clicked_point.x()), int(clicked_point.y())))
            if isinstance(item, State | Label):
                if item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable:
                    item.setSelected(not item.isSelected())
        elif event.button() == Qt.MouseButton.LeftButton:
            self.left_button_click(event)
        super().mousePressEvent(event)

    def left_button_click(self, event: QMouseEvent):
        item = self.get_item_at(event.pos())
        parent: QWidget = self.parent()
        if not isinstance(parent, UserPanel):
            return

        current_parent_item = None
        if isinstance(item, (State, Label, StateGroup)):
            item.parentItem().setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            if isinstance(item, StateGroup):
                current_parent_item = item
            elif item.parentItem() and isinstance(item.parentItem(), StateGroup):
                current_parent_item = item.parentItem()

        if isinstance(item, ConnectionPoint):
            # print('Rot' if item.brush().color() == Qt.GlobalColor.darkRed and isinstance(item, AnchorPoint) else 'Grün')
            if item.brush().color() == Qt.GlobalColor.darkGreen:
                item.parentItem().setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
                self._start_ellipse = item
                return

        if isinstance(item, (State, Label, StateGroup)):
            if self._start_ellipse and self._temp_line:
                start_point: ConnectionPoint = self._start_ellipse
                min_distance = float('inf')
                closest_point: ConnectionPoint | None = None
                for point in current_parent_item.connection_points:
                    if point.flow == 'in':
                        distance = np.sqrt((self.get_mapped_position(point).x() - self.get_mapped_position(start_point).x()) ** 2
                                           + (self.get_mapped_position(point).y() - self.get_mapped_position(start_point).y()) ** 2)
                        if distance < min_distance:
                            min_distance: float = distance
                            closest_point = point
                if closest_point:
                    self.scene().removeItem(self._temp_line)
                    self._start_ellipse, self._temp_line = None, None
                    transition = Transition(start_point, closest_point, start_point)
                    print(transition.get_ui_transition())
                return

        if self._last_active is not None:
            last_parent_item = (self._last_active if isinstance(self._last_active, StateGroup)
                                else self._last_active.parentItem())
            if last_parent_item is not None and isinstance(last_parent_item,
                                                           StateGroup) and last_parent_item != current_parent_item:
                parent.condition_edit_menu.name_changed.disconnect()
                parent.condition_edit_menu.color_changed.disconnect()
                parent.condition_edit_menu.size_changed.disconnect()
                last_parent_item.deactivate()

        if isinstance(current_parent_item, (StateGroup)):
            parent.toggle_condition_edit_menu(True)
            parent.condition_edit_menu.set_condition(item)
            parent.condition_edit_menu.name_changed.connect(current_parent_item.set_name)
            parent.condition_edit_menu.color_changed.connect(current_parent_item.set_color)
            parent.condition_edit_menu.size_changed.connect(current_parent_item.set_size)
            current_parent_item.activate()
        else:
            if parent.condition_edit_menu.x() < parent.width():
                parent.toggle_condition_edit_menu(False)

        self._last_active = current_parent_item if current_parent_item else item

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """TBA"""
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.get_item_at(event.pos()):
                global_pos: QPoint = event.pos()
                scene_pos: QPointF = self.mapToScene(global_pos)
                self.new_state(scene_pos)
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        if self._start_ellipse:
            mouse_pos = self.mapToScene(event.pos())
            if not self._temp_line:
                self._temp_line = TempTransition(self._start_ellipse, mouse_pos, self._start_ellipse)
            mouse_x = mouse_pos.x()
            mouse_y = mouse_pos.y()
            ell_x = self.get_mapped_position(self._start_ellipse).x()
            ell_y = self.get_mapped_position(self._start_ellipse).y()
            if ell_x < mouse_x:
                mouse_x -= 2
            elif ell_x > mouse_x:
                mouse_x += 2
            if ell_y < mouse_y:
                mouse_y -= 2
            elif ell_y > mouse_y:
                mouse_y += 2
            self._temp_line.update_transition(QPointF(mouse_x, mouse_y))
        super().mouseMoveEvent(event)

