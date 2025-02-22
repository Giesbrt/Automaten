"""Everything regarding the infinite grid"""
import numpy as np
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsItem, QWidget, QGraphicsEllipseItem, QMenu
from PySide6.QtGui import QPainter, QWheelEvent, QMouseEvent, QAction, QColor
from PySide6.QtCore import QRect, QRectF, Qt, QPointF, QPoint, Signal, QTimer

# from core.modules.automaton.base.transition import Transition
# from core.modules.automaton.base.state import State

from ._grid_items import State, StateGroup, Label, ConnectionPoint, TempTransition, Transition, TransitionFunction
from ._panels import UserPanel
from ..signal_bus import SignalBus, AutomatonEvent, SingletonObserver
from ..automaton.UIAutomaton import UiAutomaton, UiState, UiTransition

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

    MAX_TOTAL_UPDATE_FPS: int = 15

    def __init__(self, grid_size: int = 100, scene_rect: tuple[int, int, int, int] = (-10_000, -10_000, 20_000, 20_000),
                 zoom_level: float = 1.0, zoom_step: float = 0.05, min_zoom: float = 0.5, max_zoom: float = 2.0,
                 parent: QWidget | None = None) -> None:
        super().__init__(grid_size, None, parent)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setScene(QGraphicsScene(self))
        self.scene().setSceneRect(QRect(*scene_rect))

        # Center object (input)
        center_rect = QGraphicsEllipseItem(0, 0, self.grid_size, self.grid_size)
        center_rect.setBrush(QColor('red'))
        center_rect.setPen(Qt.PenStyle.NoPen)
        self.scene().addItem(center_rect)

        # Zoom parameters
        self.zoom_level: float = zoom_level
        self.zoom_step: float = zoom_step
        self.min_zoom: float = min_zoom
        self.max_zoom: float = max_zoom

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
            self._pending_zoom *= zoom_factor  # Accumulate zoom requests
            self.zoom_level = new_zoom
            if abs(self._pending_zoom - 1.0) > 0.1:
                self.scale(self._pending_zoom, self._pending_zoom)
                self._pending_zoom = 1.0
        print(f"Zoom Level: {self.zoom_level}, Pending Zoom: {self._pending_zoom}, New Zoom: {new_zoom}, Zoom Factor: {zoom_factor}")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.RightButton:  # Start panning the view
            self._is_panning = True
            self._previous_pan = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._is_panning:
            self._pan_delta += (event.position() - self._previous_pan)
            self._previous_pan = event.position()

            # Only process significant deltas
            if abs(self._pan_delta.x()) > 16 or abs(self._pan_delta.y()) > 16:
                self.horizontalScrollBar().setValue(
                    self.horizontalScrollBar().value() - int(self._pan_delta.x())
                )
                self.verticalScrollBar().setValue(
                    self.verticalScrollBar().value() - int(self._pan_delta.y())
                )
                self._pan_delta = QPointF(0.0, 0.0)
            # self.resetCachedContent()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Stop panning on mouse button release."""
        if event.button() == Qt.MouseButton.RightButton:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def apply_pending_updates(self) -> None:
        """Apply batched pan and zoom updates."""
        if self._pending_zoom != 1.0:
            print("Applying pending zoom", self._pending_zoom)
            self.scale(self._pending_zoom, self._pending_zoom)
            self._pending_zoom = 1.0

        self.horizontalScrollBar().setValue(
            self.horizontalScrollBar().value() - int(self._pan_delta.x())
        )
        self.verticalScrollBar().setValue(
            self.verticalScrollBar().value() - int(self._pan_delta.y())
        )
        self._pan_delta = QPointF(0.0, 0.0)


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
    set_transition_pattern: Signal = Signal()
    get_states: Signal = Signal()
    get_transitions: Signal = Signal()
    get_automaton_type: Signal = Signal()
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

    set_is_changeable_token_list: Signal = Signal(list)

    add_state: Signal = Signal(UiState)
    add_transition: Signal = Signal(UiTransition)
    delete_state: Signal = Signal(UiState)
    delete_transition: Signal = Signal(UiTransition)

    def __init__(self, default_color: QColor=QColor('white'), default_selection_color: QColor=QColor('red')) -> None:
        """Initialize the automaton grid view.

        :param default_color (QColor): The default color of the states.
        """
        super().__init__()
        self.automaton_type: str | None = None
        self.token_list: _ty.Tuple[_ty.List[str], _ty.List[str]] = [[], ['L', 'R', 'H']]
        self.loaded_automaton: bool | None = None
        self._counter: int = 0
        self._last_active: State | None = None
        self._last_hovered: StateGroup | None = None
        self._temp_line: TempTransition | None = None
        self._start_ellipse: ConnectionPoint | None = None
        self._last_connection_point: ConnectionPoint | None = None
        self._default_color: QColor = default_color
        self._default_selection_color: QColor = default_selection_color

        self.signal_bus = SignalBus()
        self.signal_bus.send_response.connect(self.handle_response)
        self.signal_bus.automaton_changed.connect(self.set_loaded_automaton)

        self.singleton_observer = SingletonObserver()
        self.singleton_observer.subscribe('token_list', self.set_token_list)
        self.singleton_observer.subscribe('automaton_type', self.set_automaton_type)

    def request_method(self, method_name, *args, **kwargs):
        # print(f'GridView: Anfrage an {method_name}')
        self.signal_bus.request_method.emit(method_name, args, kwargs)

    def handle_response(self, method_name, response):
        """Empfängt das Ergebnis und gibt es aus."""
        # print(f"GridView: Antwort von {method_name} -> {response}")

        if method_name == 'get_states':
            self.render_states(response)
        elif method_name == 'get_transitions':
            self.render_transitions(response)
        elif method_name == 'get_token_lists':
            self.set_token_list(response)
        """elif method_name == 'get_automaton_type':
            print(response)"""

    def render_ui_automaton(self):
        """Renders the UiAutomaton"""
        self.request_method('get_states')
        self.request_method('get_transitions')
        self.request_method('get_token_lists')

    def render_states(self, states):
        """Renders the StateGroups"""
        for state in states:
            self.create_state_from_automaton(state)

    def render_transitions(self, transitions):
        """Renders the Transitions"""
        for transition in transitions:
            self.create_transition_from_automaton(transition)

    def _setup_automaton_view(self) -> None:
        """
        Configure settings based on the selected automaton type.
        This method sets the number of sections required in a transition function.
        """
        if self.automaton_type == 'DFA':
            self._automaton_settings: dict = {
                'transition_sections': 1,
                'transition_pattern': []
            }
        elif self.automaton_type == 'Mealy':
            self._automaton_settings: dict = {
                'transition_sections': 2
            }
        elif self.automaton_type == 'TM':
            self._automaton_settings: dict = {
                'transition_sections': 3
            }

    def set_loaded_automaton(self, value: AutomatonEvent):
        self.loaded_automaton = value.is_loaded

    def set_token_list(self, token_list: _ty.Tuple[_ty.List[str], _ty.List[str]]) -> None:
        """Set the token list in GridView & UiAutomaton,
        updates all TransitionFunctions

        :param token_list: The new token list
        """
        self.token_list = token_list
        self.update_all_transition_functions()
        self.set_is_changeable_token_list.emit([True, False])

    def update_all_transition_functions(self):
        """Updates all TransitionFunction to the new token_list"""
        for item in self.scene().items():
            if isinstance(item, TransitionFunction):
                item.update_token_list(self.token_list)

    def set_automaton_type(self, automaton_type) -> None:
        """
        Set a new automaton type and update the view accordingly.

        Args:
            automaton_type (str): The new automaton type.
        """
        self.automaton_type = automaton_type
        self._setup_automaton_view()

        if self.loaded_automaton:
            self.render_ui_automaton()

    def get_token_list(self) -> _ty.Tuple[_ty.List[str], _ty.List[str]]:
        return self.token_list

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

    def add_item_to_token_list(self, token: str) -> None:
        if token not in self.token_list[0]:
            self.token_list[0].append(token)

    def remove_item_from_token_list(self, token: str) -> None:
        if token in self.token_list[0]:
            self.token_list[0].remove(token)

    def create_state_from_automaton(self, state: UiState):
        color: QColor = state.get_colour()
        position: tuple[float, float] = state.get_position()
        display_text: str = state.get_display_text()
        state_type: _ty.Literal['default', 'start', 'end'] = state.get_type()
        is_active: bool = state.is_active()

        state_group = StateGroup(position[0],
                                 position[1],
                                 self.grid_size, self.grid_size,
                                 display_text, color, self._default_selection_color)
        self.scene().addItem(state_group)
        state_group.set_state_type(state_type)
        state_group.update_shadow_effect() # Todo: States disable after adding
        state_group.update_label_position()

    def create_transition_from_automaton(self, ui_transition: UiTransition):
        from_state: UiState = ui_transition.get_from_state()
        from_connection_point: _ty.Literal['n', 's', 'e', 'w'] = ui_transition.get_from_state_connecting_point()
        to_state: UiState = ui_transition.get_to_state()
        to_connection_point: _ty.Literal['n', 's', 'e', 'w'] = ui_transition.get_to_state_connecting_point()
        condition: _ty.List[str] = ui_transition.get_condition()

        start_state, end_state = None, None
        start_point, end_point = None, None
        for state in self.scene().items():
            if isinstance(state, StateGroup):
                # print(f'UiState: {state.get_ui_state()} \nfrom_state: {from_state} \nto_state: {to_state}\n')
                if state.get_ui_state() == from_state:
                    start_state: StateGroup = state
                elif state.get_ui_state() == to_state:
                    end_state: StateGroup = state
        if start_state and end_state:
            for connection_point in start_state.connection_points:
                if connection_point.get_flow() == 'out' and connection_point.get_direction() == from_connection_point:
                    start_point: ConnectionPoint = connection_point
            for connection_point in end_state.connection_points:
                if connection_point.get_flow() == 'in' and connection_point.get_direction() == to_connection_point:
                    end_point: ConnectionPoint = connection_point
            if start_point and end_point:
                transition = Transition(start_point, end_point, end_state)
                transition_function = TransitionFunction(self.get_token_list(), self._automaton_settings['transition_sections'], transition)
                transition.set_transition_function(transition_function)
                transition_function.set_condition(condition)
                transition.update_position()
                self.scene().addItem(transition_function)

    def create_state(self, pos: QPointF, display_text=None) -> None:
        """
        Create a new state at the given position.

        Args:
            pos (QPointF): The position where the new state should be created.
        """
        state = StateGroup(pos.x() - self.grid_size / 2,
                           pos.y() - self.grid_size / 2,
                           self.grid_size, self.grid_size,
                           self._counter if display_text is None else display_text,
                           self._default_color, self._default_selection_color)
        self.add_state.emit(state.get_ui_state())
        self.scene().addItem(state)
        parent: UserPanel = self.parent()
        parent.toggle_condition_edit_menu(True)
        parent.state_menu.set_state(state)
        parent.state_menu.connect_methods()
        self._last_active = state
        self._counter += 1

    def create_transition(self, start_point, end_point, state_group):
        transition: Transition = Transition(start_point, end_point, state_group)
        self.add_transition.emit(transition.get_ui_transition())
        transition_function: TransitionFunction = TransitionFunction(self.get_token_list(),
                                                                     self._automaton_settings['transition_sections'],
                                                                     transition)
        transition.set_transition_function(transition_function)
        transition.update_position()
        self.scene().addItem(transition_function)

    def remove_transition(self, transition: 'Transition') -> None:
        transition.start_state.connected_transitions.remove(transition)
        transition.end_state.connected_transitions.remove(transition)
        self.scene().removeItem(transition)
        self.scene().removeItem(transition.get_transition_function())

    def remove_item(self, item: QGraphicsItem) -> None:
        """
        Remove an item from the scene.

        Args:
            item (QGraphicsItem): The item to remove.
        """
        if isinstance(item, TempTransition):
            self.scene().removeItem(item)

        elif isinstance(item, StateGroup):
            item.deactivate()
            for transition in list(item.get_connected_transitions()):
                self.remove_transition(transition)
            self.scene().removeItem(item)
            self.delete_state.emit(item.get_ui_state())

        elif isinstance(item, Transition):
            self.remove_transition(item)
            self.delete_transition.emit(item.get_ui_transition())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Handle mouse press events for interaction with the automaton.

        - Middle-click opens a context menu for deleting states.
        - Right-click starts panning.
        - Left-click selects/moves items or starts a transition.

        Args:
            event (QMouseEvent): The mouse event.
        """
        if event.button() == Qt.MouseButton.RightButton:
            item: State | Label | ConnectionPoint = self.get_item_at(event.pos())

            if self._temp_line:
                self.scene().removeItem(self._temp_line)
                self._start_ellipse, self._temp_line = None, None

            if isinstance(item, (State, Label)):
                context_menu = QMenu(self)
                delete_action = QAction("Delete", self)
                delete_action.triggered.connect(lambda: self.remove_item(self.get_item_group(item)))
                context_menu.addAction(delete_action)
                context_menu.exec(event.globalPos())
                return
            elif isinstance(item, Transition):
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
                    self.create_transition(start_point, closest_point, self.get_item_group(item))
                return

        if self._last_active is not None:
            last_parent_item = self.get_item_group(self._last_active)
            if last_parent_item != current_parent_item:
                parent.state_menu.disconnect_methods()
                last_parent_item.deactivate()

        if isinstance(item, State | Label) and not parent.state_menu.isVisible():
            parent.toggle_condition_edit_menu(True)
            parent.state_menu.set_state(current_parent_item)
            parent.state_menu.connect_methods()
            current_parent_item.activate()
        elif isinstance(item, State | Label) and parent.state_menu.isVisible():
            parent.state_menu.set_state(current_parent_item)
            parent.state_menu.connect_methods()
            current_parent_item.activate()
        else:
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
            self._last_connection_point = item
        elif not isinstance(item, ConnectionPoint):
            if self._last_connection_point:
                self._last_connection_point = None

        if isinstance(item, State | Label | ConnectionPoint):
            for connection_point in self.get_item_group(item).connection_points:
                connection_point.is_hovered = True
                self._last_hovered = self.get_item_group(item)
        elif self._last_hovered and not isinstance(item, State | Label):
            for connection_point in self._last_hovered.connection_points:
                connection_point.is_hovered = False

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
