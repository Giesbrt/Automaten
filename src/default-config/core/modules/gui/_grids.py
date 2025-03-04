"""Everything regarding the infinite grid"""
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsItem, QWidget, QGraphicsRectItem, QMenu, \
    QGraphicsDropShadowEffect
from PySide6.QtGui import QPainter, QWheelEvent, QMouseEvent, QAction, QColor, QPen, QCursor
from PySide6.QtCore import QRect, QRectF, Qt, QPointF, QPoint, Signal, QTimer

# from automaton.base.transition import Transition
# from automaton.base.state import State

from ._grid_items import StateItem, TransitionItem
from ._graphic_items import TransitionFunctionItem, TokenListFrame, TokenButtonFrame, TokenButton, StateGraphicsItem, StateConnectionGraphicsItem, LabelGraphicsItem, TransitionGraphicsItem
from ._graphic_support_items import TempTransitionItem
from ._panels import UserPanel
from automaton.UIAutomaton import UiState, UiTransition
from storage import AppSettings

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts
import numpy as np
import math


class StaticGridView(QGraphicsView):
    """A static view for observing a QGraphicsScene without interaction."""
    def __init__(self, grid_size: int, scene: QGraphicsScene | None = None,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self.setCacheMode(QGraphicsView.CacheModeFlag.CacheBackground)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.BoundingRectViewportUpdate)
        # self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontSavePainterState, True)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True)

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

        painter.setPen(QColor('lightgray'))
        for line in lines:
            painter.drawLine(*line)

    def getViewPosition(self) -> QPointF:
        return self.mapToScene(self.viewport().rect().center() + QPoint(1, 1))

    def setViewPosition(self, position: QPointF) -> None:
        """
        Sets the viewport's position within the scene.

        param position: Position to set to
        returns: If the scene was large enough
        """
        self.centerOn(position)

    def setScale(self, scale: float = 1.0) -> None:
        raise NotImplementedError


class InteractiveGridView(StaticGridView):
    """Represents an interactable GridView, it creates its own scene"""

    MAX_TOTAL_UPDATE_FPS: int = 15

    def __init__(self, grid_size: int = 100, scene_rect: tuple[int, int, int, int] = (-10_000, -10_000, 20_000, 20_000),
                 starting_zoom_level: float = 1.0, zoom_step: float = 0.05, min_zoom: float = 0.1, max_zoom: float = 2.0,
                 parent: QWidget | None = None) -> None:
        super().__init__(grid_size, None, parent)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setScene(QGraphicsScene(self))
        self.scene().setSceneRect(QRect(*scene_rect))

        # Zoom parameters
        self.zoom_step: float = zoom_step
        self.min_zoom: float = min_zoom
        self.max_zoom: float = max_zoom
        self._zoom_level: float = starting_zoom_level

        # Panning attributes
        self._is_panning: bool = False
        self._previous_pan: QPointF = QPointF(0.0, 0.0)
        self._pan_delta: QPointF = QPointF(0.0, 0.0)
        self._pending_zoom: float = 1.0

        # Timer for limiting updates
        self._update_timer = QTimer(self)
        self._update_timer.setInterval(1000 // self.MAX_TOTAL_UPDATE_FPS)  # Max FPS update rate
        self._update_timer.timeout.connect(self.apply_pending_updates)
        self._update_timer.start()

    def get_zoom_level(self) -> float:
        """
        Gets the current zoom level, 1.0 means no zoom
        """
        return self._zoom_level

    def set_zoom_level(self, new_zoom_level: float) -> None:
        """
        Sets the current zoom level to a new value, 1.0 means no zoom
        """
        self._zoom_to(1 / self._zoom_level * new_zoom_level)

    def setSceneRect(self, rect: tuple[int, int, int, int]):
        self.scene().setSceneRect(QRect(*rect))

    def _zoom_to(self, pending_zoom: float) -> None:
        if pending_zoom == 1.0:
            return None
        last_point: QPointF = self.mapToScene(self.mapFromGlobal(QCursor.pos()))
        self.scale(pending_zoom, pending_zoom)
        point: QPointF = self.mapToScene(self.mapFromGlobal(QCursor.pos()))

        movement_vector: QPointF = last_point - point

        self.translateViewPosition(-movement_vector)
        self._pending_zoom = 1.0

    def zoom(self, zoom_factor: float) -> None:
        if zoom_factor < 0:
            return None
        new_zoom: float = self._zoom_level * zoom_factor
        if self.min_zoom <= new_zoom <= self.max_zoom:
            self._pending_zoom *= zoom_factor  # Accumulate zoom requests
            self._zoom_level = new_zoom
            self._zoom_to(self._pending_zoom)

    def reset_zoom(self) -> None:
        # zoom_factor = 1.0 / self._zoom_level
        self._zoom_level = 1.0
        self._pending_zoom = 1.0
        self.resetTransform()

    def reset_cache(self) -> None:
        self.resetCachedContent()

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Zoom in and out with the mouse wheel."""
        if event.angleDelta().y() > 0:
            zoom_factor = 1 + self.zoom_step
        else:
            zoom_factor = 1 - self.zoom_step

        new_zoom: float = self._zoom_level * zoom_factor
        if self.min_zoom <= new_zoom <= self.max_zoom:
            self._pending_zoom *= zoom_factor  # Accumulate zoom requests
            self._zoom_level = new_zoom
            if abs(self._pending_zoom - 1.0) > 0.1:
                self._zoom_to(self._pending_zoom)
                self._pending_zoom = 1.0

    def translateViewPosition(self, position: QPointF) -> None:
        self.translate(position.x(), position.y())

    def translateViewPositionWithScaling(self, position: QPointF) -> None:
        self.translate(position.x() / self._zoom_level, position.y() / self._zoom_level)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        # print("MPE", event, self._is_panning)
        if event.button() == Qt.MouseButton.RightButton and not self._is_panning:  # Start panning the view
            self._is_panning = True
            self._previous_pan = event.position()
            # print("Setting cursor to Fist")
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._is_panning:
            self._pan_delta += (event.position() - self._previous_pan)
            self._previous_pan = event.position()

            # Only process significant deltas
            if abs(self._pan_delta.x()) > 8 or abs(self._pan_delta.y()) > 8:
                self.translateViewPositionWithScaling(self._pan_delta)
                # self.horizontalScrollBar().setValue(
                #     self.horizontalScrollBar().value() - int(self._pan_delta.x())
                # )
                # self.verticalScrollBar().setValue(
                #     self.verticalScrollBar().value() - int(self._pan_delta.y())
                # )
                self._pan_delta = QPointF(0.0, 0.0)
            # self.resetCachedContent()
            #self.mapFromGlobal()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Stop panning on mouse button release."""
        # print("MRE", event, self._is_panning)
        if event.button() == Qt.MouseButton.RightButton and self._is_panning:
            self._is_panning = False
            # print("Setting cursor to Arrow")
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def apply_pending_updates(self) -> None:
        """Apply batched pan and zoom updates."""
        if self._pending_zoom != 1.0:

            self._zoom_to(self._pending_zoom)
            self._pending_zoom = 1.0

        if self._pan_delta != QPointF(0, 0):
            # print(self._pan_delta, self.get_zoom_level())
            self.translateViewPositionWithScaling(self._pan_delta)
            self._pan_delta = QPointF(0.0, 0.0)


class AutomatonInteractiveGridView(InteractiveGridView):
    """
    A specialized interactive grid view for automaton visualization.

    This class extends `InteractiveGridView` to support different types
    of automata, handling states, transitions, and user interactions.
    """
    def __init__(self, ui_automaton: 'UiAutomaton', default_color: QColor=QColor('white'), default_selection_color: QColor=QColor('red')) -> None:
        """Initialize the automaton grid view.

        :param default_color (QColor): The default color of the states.
        """
        super().__init__()
        self.ui_automaton: 'UiAutomaton' = ui_automaton
        self.automaton_type: str | None = self.ui_automaton.get_automaton_type()
        self.token_lists: _ty.Tuple[_ty.List[str], _ty.List[str]] = self.ui_automaton.get_token_lists()
        self.settings = AppSettings()
        self._counter: int = 0
        self._last_active: StateGraphicsItem | None = None
        self._last_hovered: StateItem | None = None
        self._temp_line: TempTransitionItem | None = None
        self._start_ellipse: StateConnectionGraphicsItem | None = None
        self._last_connection_point: StateConnectionGraphicsItem | None = None
        self._last_token_list: TokenListFrame | None = None
        self._highlighted_state_item: StateItem | None = None
        self._highlighted_transition_item: TransitionItem | None = None
        self._default_color: QColor = QColor.fromString(self.settings.get_default_state_background_color())
        self.settings.default_state_background_color_changed.connect(lambda x: setattr(self, "_default_color", x))
        self._default_selection_color: QColor = default_selection_color

        self.settings.automaton_type_changed.connect(self._setup_automaton_view)

    def get_ui_automaton(self) -> 'UiAutomaton':
        """Returns the UiAutomaton

        :return: The UiAutomaton
        """
        return self.ui_automaton

    def load_automaton_from_file(self) -> None:
        """Loads the UiAutomaton"""
        self.automaton_type = self.get_ui_automaton().get_automaton_type()
        self._setup_automaton_view()
        self.get_ui_automaton().set_transition_pattern(self._automaton_settings['transition_pattern'])

        for state in self.ui_automaton.get_states():
            self.create_state_from_automaton(state)
        for transition in self.ui_automaton.get_transitions():
            self.create_transition_from_automaton(transition)

        self.update_token_lists()
        self.get_ui_automaton().set_is_changeable_token_list([True, False])

    def _setup_automaton_view(self, automaton_type: str | None = None) -> None:
        """
        Configure settings based on the selected automaton type.
        This method sets the number of sections required in a transition function.
        """
        if automaton_type:
            self.automaton_type = automaton_type
        if self.automaton_type.lower() == 'dfa':
            self._automaton_settings: dict = {
                'transition_sections': 1,
                'transition_pattern': [0]
            }
        elif self.automaton_type.lower() == 'mealy':
            self._automaton_settings: dict = {
                'transition_sections': 2,
                'transition_pattern': [0, 0]
            }
        elif self.automaton_type.lower() == 'tm':
            self._automaton_settings: dict = {
                'transition_sections': 3,
                'transition_pattern': [0, 0, 1]
            }

    def set_automaton_type(self, automaton_type: str):
        """Sets the automaton-type"""
        self.automaton_type = self.get_ui_automaton().get_automaton_type()

    def update_token_lists(self):
        """Updates all TransitionFunction to the new token_list"""
        self.token_lists = self.get_ui_automaton().get_token_lists()

        for item in self.scene().items():
            if isinstance(item, TransitionFunctionItem):
                item.update_token_list(self.token_lists)

    def get_active_state(self, active_state: 'UiState') -> StateItem | None:
        """Returns the active state item

        :param active_state: The active state
        :return: The active state item
        """
        for item in self.scene().items():
            if isinstance(item, StateItem):
                active_state._is_active = False
                if item.get_ui_state() == active_state:
                    return item

    def get_active_transition(self, active_transition: 'UiTransition') -> TransitionItem | None:
        """Returns the active transition item

        :param active_transition: The active transition
        :return: The active transition item"""
        for item in self.scene().items():
            if isinstance(item, TransitionItem):
                active_transition._is_active = False
                if item.get_ui_transition().get_from_state() == active_transition.get_from_state():
                    pass
                if item.get_ui_transition() == active_transition:
                    return item

    def get_token_list(self) -> _ty.Tuple[_ty.List[str], _ty.List[str]]:
        """Get the current token list.

        :return: The current token list
        """
        return self.token_lists

    def get_mapped_position(self, item: QGraphicsItem) -> any:
        """Get the mapped scene position of a given item.

        :param item: The item whose position is needed.
        """
        scene_pos = item.mapToScene(item.boundingRect().center())
        return self.mapFromScene(scene_pos)

    def get_item_at(self, pos: QPoint) -> QGraphicsItem:
        """Retrieve the item at a given position.

        :param pos: The position in the grid view.
        """
        scene_pos: QPointF = self.mapToScene(pos)
        return self.scene().itemAt(scene_pos, self.transform())

    def get_item_group(self, item: StateGraphicsItem | LabelGraphicsItem | StateConnectionGraphicsItem) -> StateItem:
        """Retrieve the parent `StateGroup` of a given item.

        :param item: The item whose group is needed.
        """
        while not isinstance(item, StateItem):
            item: StateGraphicsItem | StateItem = item.parentItem()
        return item

    def highlight_state_item(self, state_item: 'StateItem') -> None:
        """Highlights the specified StateItem and removes the highlight from previously highlighted items.

        :param state_item: The StateItem to highlight.
        """
        if self._highlighted_state_item and self._highlighted_state_item != state_item:
            self.unhighlight_state_item()
        self._highlighted_state_item = state_item
        self._highlighted_state_item.highlight()

    def unhighlight_state_item(self) -> None:
        """Removes the highlight from the currently highlighted StateItem."""
        if self._highlighted_state_item:
            self._highlighted_state_item.unhighlight()
            self._highlighted_state_item = None

    def highlight_transition_item(self, transition_item: 'TransitionItem') -> None:
        """Highlights the specified TransitionItem and removes the highlight from previously highlighted items.

        :param transition_item: The TransitionItem to highlight.
        """
        if self._highlighted_transition_item and self._highlighted_transition_item != transition_item:
            self.unhighlight_transition_item()
        self._highlighted_transition_item = transition_item
        self._highlighted_transition_item.highlight()

    def unhighlight_transition_item(self) -> None:
        """Removes the highlight from the currently highlighted TransitionItem."""
        if self._highlighted_transition_item:
            self._highlighted_transition_item.unhighlight()
            self._highlighted_transition_item = None

    def reset_all_highlights(self) -> None:
        """Removes all highlights (StateItem and TransitionItem)."""
        self.unhighlight_state_item()
        self.unhighlight_transition_item()

    def add_item_to_token_list(self, token: str) -> None:
        if token not in self.token_lists[0]:
            self.token_lists[0].append(token)

    def remove_item_from_token_list(self, token: str) -> None:
        if token in self.token_lists[0]:
            self.token_lists[0].remove(token)

    def create_state_from_automaton(self, ui_state: UiState) -> None:
        state_item = StateItem(ui_state, self.ui_automaton, self.grid_size, self._default_selection_color)
        self.scene().addItem(state_item)
        state_item.update_shadow_effect()
        state_item.update_label_position()

    def create_transition_from_automaton(self, ui_transition: UiTransition) -> None:
        """Creates a TransitionItem from the given UiTransition"""
        from_state: UiState = ui_transition.get_from_state()
        from_connection_point: _ty.Literal['n', 's', 'e', 'w'] = ui_transition.get_from_state_connecting_point()
        to_state: UiState = ui_transition.get_to_state()
        to_connection_point: _ty.Literal['n', 's', 'e', 'w'] = ui_transition.get_to_state_connecting_point()
        condition: _ty.List[str] = ui_transition.get_condition()

        start_state, end_state, start_point, end_point = None, None, None, None
        for state in self.scene().items():
            if isinstance(state, StateItem):
                if state.get_ui_state() == from_state:
                    start_state: StateItem = state
                if state.get_ui_state() == to_state:
                    end_state: StateItem = state
        if start_state and end_state:
            for connection_point in start_state.connection_points:
                if connection_point.get_flow() == 'out' and connection_point.get_direction() == from_connection_point:
                    start_point: StateConnectionGraphicsItem = connection_point
            for connection_point in end_state.connection_points:
                if connection_point.get_flow() == 'in' and connection_point.get_direction() == to_connection_point:
                    end_point: StateConnectionGraphicsItem = connection_point
            if start_point and end_point:
                transition_item = TransitionItem(ui_transition, self.ui_automaton,
                                                 self._automaton_settings['transition_sections'],
                                                 start_point, end_point, start_state, end_state)
                transition_item.update_position()
                transition_item.set_condition(condition)
                self.scene().addItem(transition_item)

    def create_state(self, pos: QPointF, display_text=None) -> None:
        """Create a new state at the given position.

        :param pos: The position where the new state should be created.
        :param display_text: The displayed text if a automaton was loaded
        """
        if not display_text:
            display_text = f'q{self._counter}' if isinstance(self._counter, int) else self._counter

        ui_state = UiState(self._default_color, (pos.x() - self.grid_size / 2, pos.y() - self.grid_size / 2), display_text, 'default')
        state_item = StateItem(ui_state, self.ui_automaton, self.grid_size, self._default_selection_color)

        self.ui_automaton.add_state(state_item.get_ui_state())
        self.scene().addItem(state_item)

        parent: UserPanel = self.parent()
        parent.toggle_condition_edit_menu(True)
        parent.state_menu.set_state(state_item)
        parent.state_menu.connect_methods()

        self._last_active = state_item
        self._counter += 1

    def create_transition(self, start_point, end_point):
        """Creates a new transition from the start_point to the end_point

        :param start_point: The start point of the transition
        :param end_point: The end point of the transition
        """
        start_state = start_point.parentItem()
        end_state = end_point.parentItem()

        ui_transition = UiTransition(start_state.get_ui_state(), start_point.get_direction(), end_state.get_ui_state(), end_point.get_direction(), [])
        transition_item = TransitionItem(ui_transition, self.ui_automaton, self._automaton_settings['transition_sections'],
                                         start_point, end_point, start_state, end_state)
        transition_item.update_position()

        self.ui_automaton.add_transition(transition_item.get_ui_transition())
        self.scene().addItem(transition_item)

    def empty_scene(self):
        """Empties the whole scene"""
        for item in self.scene().items():
            self.scene().removeItem(item)

    def remove_transition(self, transition_item: 'TransitionItem') -> None:
        """Removes the given transition

        :param transition_item: The transition"""
        transition_item.transition_line_item.start_state.connected_transitions.remove(transition_item)
        transition_item.transition_line_item.end_state.connected_transitions.remove(transition_item)
        self.scene().removeItem(transition_item)

    def remove_item(self, item: QGraphicsItem) -> None:
        """Remove an item from the scene.

        :param item: The item to remove.
        """
        if isinstance(item, TempTransitionItem):
            self.scene().removeItem(item)

        elif isinstance(item, StateItem):
            item.deactivate()
            for transition in list(item.get_connected_transitions()):
                self.remove_transition(transition)
            self.scene().removeItem(item)
            self.get_ui_automaton().delete_state(item.get_ui_state())

        elif isinstance(item, TransitionItem):
            self.remove_transition(item)
            self.get_ui_automaton().delete_transition(item.get_ui_transition())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events for interaction with the automaton.

        - Right-click starts panning.
        - Right-click on a StateItem or a TransitionItem opens a context menu for deleting states.
        - Left-click selects/moves items or starts a transition.

        :param event: The mouse event.
        """
        if event.button() == Qt.MouseButton.RightButton:
            item: StateGraphicsItem | LabelGraphicsItem | StateConnectionGraphicsItem = self.get_item_at(event.pos())

            if self._temp_line:
                self.scene().removeItem(self._temp_line)
                self._start_ellipse, self._temp_line = None, None

            if isinstance(item, (StateGraphicsItem, LabelGraphicsItem)):
                context_menu = QMenu(self)
                delete_action = QAction("Delete", self)
                delete_action.triggered.connect(lambda: self.remove_item(self.get_item_group(item)))
                context_menu.addAction(delete_action)
                context_menu.exec(event.globalPos())
                return
            elif isinstance(item, TransitionItem):
                context_menu = QMenu(self)
                delete_action = QAction('Delete', self)
                delete_action.triggered.connect(lambda: self.remove_item(item))
                context_menu.addAction(delete_action)
                context_menu.exec(event.globalPos())
                return
            else:
                super().mousePressEvent(event)
                return

        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.button() == Qt.MouseButton.LeftButton:
            # clicked_point = self.mapToScene(event.pos())
            item_group = self.get_item_group(self.get_item_at(event.pos()))
            if isinstance(item_group, StateItem):
                if item_group.state.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable:
                    item_group.setSelected(not item_group.isSelected())

        elif event.button() == Qt.MouseButton.LeftButton:
            self.left_button_click(event)

        super().mousePressEvent(event)

    def left_button_click(self, event: QMouseEvent):
        """Handle left mouse button clicks for selection, movement, and transitions.

        :param event: The mouse event.
        """
        item = self.get_item_at(event.pos())
        parent: QWidget = self.parent()
        if not isinstance(parent, UserPanel):
            return

        current_parent_item = None
        if isinstance(item, StateGraphicsItem | LabelGraphicsItem):
            item.parentItem().setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            current_parent_item = self.get_item_group(item)

        # Handling connection points and transitions
        if isinstance(item, StateConnectionGraphicsItem) and item.flow == 'out':
            item.parentItem().setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            self._start_ellipse = item
            return

        # Handling state selection and transitions
        if isinstance(item, StateGraphicsItem | LabelGraphicsItem):
            if self._start_ellipse and self._temp_line:
                start_point: StateConnectionGraphicsItem = self._start_ellipse
                min_distance = float('inf')
                closest_point: StateConnectionGraphicsItem | None = None
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
                    self.create_transition(start_point, closest_point) # , self.get_item_group(item)
                return

        if self._last_active is not None:
            last_parent_item = self.get_item_group(self._last_active)
            if last_parent_item != current_parent_item:
                parent.state_menu.disconnect_methods()
                last_parent_item.deactivate()

        if isinstance(item, StateGraphicsItem | LabelGraphicsItem) and parent.state_menu.x() >= parent.width():
            parent.toggle_condition_edit_menu(True)
            parent.state_menu.set_state(current_parent_item)
            parent.state_menu.connect_methods()
            current_parent_item.activate()
        elif isinstance(item, StateGraphicsItem | LabelGraphicsItem) and parent.state_menu.x() < parent.width():
            parent.state_menu.set_state(current_parent_item)
            parent.state_menu.connect_methods()
            current_parent_item.activate()
        else:
            if parent.state_menu.x() < parent.width():
                parent.toggle_condition_edit_menu(False)

        self._last_active = current_parent_item

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """Handle double-click events to create new states.

        :param event: The mouse event.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.get_item_at(event.pos()):
                global_pos: QPoint = event.pos()
                scene_pos: QPointF = self.mapToScene(global_pos)
                self.create_state(scene_pos)
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse movement events for hovering effects and temporary transitions.

        :param event: The mouse event.
        """
        item = self.get_item_at(event.pos())

        if isinstance(item, StateConnectionGraphicsItem) and item.flow == 'out' and not item.is_hovered:
            self._last_connection_point = item
        elif not isinstance(item, StateConnectionGraphicsItem):
            if self._last_connection_point:
                self._last_connection_point = None

        if isinstance(item, StateGraphicsItem | LabelGraphicsItem | StateConnectionGraphicsItem):
            for connection_point in self.get_item_group(item).connection_points:
                connection_point.is_hovered = True
                self._last_hovered = self.get_item_group(item)
        elif self._last_hovered and not isinstance(item, StateGraphicsItem | LabelGraphicsItem):
            for connection_point in self._last_hovered.connection_points:
                connection_point.is_hovered = False

        # Handling temporary transition drawing
        if self._start_ellipse:
            mouse_pos = self.mapToScene(event.pos())
            if not self._temp_line:
                self._temp_line = TempTransitionItem(self._start_ellipse, mouse_pos, self._start_ellipse)
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
