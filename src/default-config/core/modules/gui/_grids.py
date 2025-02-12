"""Everything regarding the infinite grid"""
import numpy as np
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsItem, QWidget, QGraphicsEllipseItem, QMenu, \
    QGraphicsTextItem, QGraphicsProxyWidget
from PySide6.QtGui import QPainter, QWheelEvent, QMouseEvent, QColor, QAction
from PySide6.QtCore import QRect, QRectF, Qt, QPointF, QPoint, Signal

# from core.modules.automaton.base.transition import Transition
# from core.modules.automaton.base.state import State

from ._grid_items import State, StateGroup, Label, ConnectionPoint, TempTransition, Transition, TransitionFunction, \
    TokenSelectionButton
from ._panels import UserPanel

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

from ..automaton.UIAutomaton import UiAutomaton, UiState, UiTransition


class StaticGridView(QGraphicsView):
    """A static view for observing a QGraphicsScene without interaction."""
    def __init__(self, grid_size: int, scene: QGraphicsScene | None = None,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self.setCacheMode(QGraphicsView.CacheModeFlag.CacheBackground)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
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
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
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
    """
    A specialized interactive grid view for automaton visualization.

    This class extends `InteractiveGridView` to support different types
    of automata, handling states, transitions, and user interactions.
    """
    get_start_state: Signal = Signal()
    get_state_types_with_design: Signal = Signal()
    set_state_types_with_design: Signal = Signal()
    get_author: Signal = Signal()
    get_token_lists: Signal = Signal()
    get_is_changeable_token_list: Signal = Signal()
    get_transition_pattern: Signal = Signal()
    set_token_lists: Signal = Signal()
    set_is_changeable_token_list: Signal = Signal()
    set_transition_pattern: Signal = Signal()
    get_states: Signal = Signal()
    get_transitions: Signal = Signal()
    get_name: Signal = Signal()
    set_start_state: Signal = Signal()
    get_state_by_id: Signal = Signal()
    get_state_index: Signal = Signal()
    get_transition_index: Signal = Signal()
    get_transition_by_id: Signal = Signal()
    simulate: Signal = Signal()
    handle_simulation_updates: Signal = Signal()
    handle_bridge_updates: Signal = Signal()
    has_simulation_data: Signal = Signal()
    has_bridge_updates: Signal = Signal()
    is_simulation_data_available: Signal = Signal()


    add_state: Signal = Signal(UiState)
    add_transition: Signal = Signal(UiTransition)
    delete_state: Signal = Signal(UiState)
    delete_transition: Signal = Signal(UiTransition)

    def __init__(self, default_color: Qt.GlobalColor=Qt.GlobalColor.white,
                 default_selection_color: Qt.GlobalColor=Qt.GlobalColor.red) -> None:
        """
        Initialize the automaton grid view.

        Args:
            default_color (Qt.GlobalColor): The default color of the states.
        """
        super().__init__()
        self.automaton_type: str | None = None
        self._counter: int = 0
        self._last_active: State | None = None
        self._temp_line: TempTransition | None = None
        self._default_color: Qt.GlobalColor = default_color
        self._start_ellipse: ConnectionPoint | None = None
        self._last_connection_point: ConnectionPoint | None = None
        self._default_selection_color: Qt.GlobalColor = default_selection_color

    def _setup_automaton_view(self) -> None:
        """
        Configure settings based on the selected automaton type.
        This method sets the number of sections required in a transition function.
        """
        if self.automaton_type == 'Deterministic Finite Automaton (DFA)':
            self._automaton_settings: dict = {
                'transition_sections': 1
            }
        elif self.automaton_type == 'Mealy-Machine (MM)':
            self._automaton_settings: dict = {
                'transition_sections': 2
            }
        elif self.automaton_type == 'Turing Machine (TM)':
            self._automaton_settings: dict = {
                'transition_sections': 3
            }

    def set_automaton_type(self, automaton_type) -> None:
        """
        Set a new automaton type and update the view accordingly.

        Args:
            automaton_type (str): The new automaton type.
        """
        self.automaton_type = automaton_type
        # print(self.automaton_type)
        self._setup_automaton_view()

    def get_mapped_position(self, item: QGraphicsItem) -> any:
        """
        Get the mapped scene position of a given item.

        Args:
            item (QGraphicsItem): The item whose position is needed.

        Returns:
            QPoint: The mapped position in the grid view.
        """
        scene_pos = item.mapToScene(item.boundingRect().center())
        return self.mapFromScene(scene_pos)

    def get_item_at(self, pos: QPoint) -> QGraphicsItem:
        """
        Retrieve the item at a given position.

        Args:
            pos (QPoint): The position in the grid view.

        Returns:
            QGraphicsItem: The item at the given position, if any.
        """
        scene_pos: QPointF = self.mapToScene(pos)
        return self.scene().itemAt(scene_pos, self.transform())

    def get_item_group(self, item: State | Label | ConnectionPoint) -> StateGroup:
        """
        Retrieve the parent `StateGroup` of a given item.

        Args:
            item (State | Label | ConnectionPoint): The item whose group is needed.

        Returns:
            StateGroup: The parent group of the item.
        """
        while not isinstance(item, StateGroup):
            item: State | StateGroup = item.parentItem()
        return item

    def create_state(self, pos: QPointF) -> None:
        """
        Create a new state at the given position.

        Args:
            pos (QPointF): The position where the new state should be created.
        """
        state = StateGroup(pos.x() - self.grid_size / 2,
                           pos.y() - self.grid_size / 2,
                           self.grid_size, self.grid_size,
                           self._counter, self._default_color, self._default_selection_color)
        self.scene().addItem(state)
        self.add_state.emit(state.get_ui_state())
        parent: UserPanel = self.parent()
        parent.toggle_condition_edit_menu(True)
        parent.state_menu.set_state(state)
        parent.state_menu.connect_methods()
        self._last_active = state
        self._counter += 1
        # print('finished')

    def remove_item(self, item: QGraphicsItem) -> None:
        """
        Remove an item from the scene.

        Args:
            item (QGraphicsItem): The item to remove.
        """
        # self.ui_automaton.delete_state(state_group.get_ui_state())
        # print(item.childItems())
        if isinstance(item, StateGroup):
            for transition in item.connected_transitions:
                self.scene().removeItem(transition)
                self.scene().removeItem(transition.get_transition_function())
            self.delete_state.emit(item.get_ui_state())
        elif isinstance(item, Transition):
            self.scene().removeItem(item)
            self.scene().removeItem(item.get_transition_function())
            self.delete_transition.emit(item.get_ui_transition())
        else:
            self.scene().removeItem(item)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Handle mouse press events for interaction with the automaton.

        - Middle-click opens a context menu for deleting states.
        - Right-click starts panning.
        - Left-click selects/moves items or starts a transition.

        Args:
            event (QMouseEvent): The mouse event.
        """
        """if event.button() == Qt.MouseButton.MiddleButton:
            # Remove temporary transition line if right-clicked
            if self._temp_line:
                self.scene().removeItem(self._temp_line)
                self._start_ellipse, self._temp_line = None, None
            item: QGraphicsItem = self.get_item_at(event.pos())
            if isinstance(item, (State, Label)):
                # Context menu for deleting a state
                context_menu = QMenu(self)
                delete_action = QAction("Delete", self)
                delete_action.triggered.connect(lambda: self.remove_item(self.get_item_group(item)))
                context_menu.addAction(delete_action)
                context_menu.exec(event.globalPos())"""

        if event.button() == Qt.MouseButton.RightButton:
            if self._temp_line:
                self.scene().removeItem(self._temp_line)
                self._start_ellipse, self._temp_line = None, None
            item: State | Label | ConnectionPoint = self.get_item_at(event.pos())
            if isinstance(item, (State, Label)):
                # Context menu for deleting a state
                context_menu = QMenu(self)
                delete_action = QAction("Delete", self)
                delete_action.triggered.connect(lambda: self.remove_item(self.get_item_group(item)))
                context_menu.addAction(delete_action)
                context_menu.exec(event.globalPos())
                return
            # Start panning the view
            self._is_panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.button() == Qt.MouseButton.LeftButton:
            # clicked_point = self.mapToScene(event.pos())
            item_group = self.get_item_group(self.get_item_at(event.pos()))
            if isinstance(item_group, StateGroup):
                if item_group.state.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable:
                    item_group.setSelected(not item_group.isSelected())

        elif event.button() == Qt.MouseButton.LeftButton:
            self.left_button_click(event)

        super().mousePressEvent(event)

    def left_button_click(self, event: QMouseEvent):
        """
        Handle left mouse button clicks for selection, movement, and transitions.

        Args:
            event (QMouseEvent): The mouse event.
        """
        item = self.get_item_at(event.pos())
        parent: QWidget = self.parent()
        if not isinstance(parent, UserPanel):
            return

        current_parent_item = None
        if isinstance(item, State | Label):
            item.parentItem().setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            current_parent_item = self.get_item_group(item)

        # Handling connection points and transitions
        if isinstance(item, ConnectionPoint) and item.flow == 'out':
            item.parentItem().setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            self._start_ellipse = item
            return

        # Handling state selection and transitions
        if isinstance(item, State | Label):
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
                    self.remove_item(self._temp_line)
                    self._start_ellipse, self._temp_line = None, None
                    transition = Transition(start_point, closest_point, self.get_item_group(item))
                    self.add_transition.emit(transition.get_ui_transition())
                    transition_function = TransitionFunction(['Apfel', 'Birne', 'Orange', 'Blaubeere', 'Aubergine', 'Erdbeere'], transition) # self._automaton_settings['transition_sections']
                    transition.set_transition_function(transition_function)
                    transition.update_position()
                    # transition_function.update_transition_function()
                    self.scene().addItem(transition_function)
                return

        if self._last_active is not None:
            last_parent_item = self.get_item_group(self._last_active)
            if last_parent_item != current_parent_item:
                parent.state_menu.disconnect_methods()
                last_parent_item.deactivate()
        elif not isinstance(item, State | Label | ConnectionPoint):
            ...

        if isinstance(item, State | Label):
            parent.toggle_condition_edit_menu(True)
            parent.state_menu.set_state(current_parent_item)
            parent.state_menu.connect_methods()
            current_parent_item.activate()
        else:
            # transition.get_transition_function().close_token_selection_list()
            if parent.state_menu.x() < parent.width():
                parent.toggle_condition_edit_menu(False)

        self._last_active = current_parent_item

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """
        Handle double-click events to create new states.

        Args:
            event (QMouseEvent): The mouse event.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.get_item_at(event.pos()):
                global_pos: QPoint = event.pos()
                scene_pos: QPointF = self.mapToScene(global_pos)
                self.create_state(scene_pos)
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        """
        Handle mouse movement events for hovering effects and temporary transitions.

        Args:
            event (QMouseEvent): The mouse event.
        """
        item = self.get_item_at(event.pos())
        if isinstance(item, ConnectionPoint) and item.flow == 'out' and not item.is_hovered:
            item.grow()
            self._last_connection_point = item
        elif not isinstance(item, ConnectionPoint):
            if self._last_connection_point:
                self._last_connection_point.shrink()
                self._last_connection_point = None

        # Handling temporary transition drawing
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
