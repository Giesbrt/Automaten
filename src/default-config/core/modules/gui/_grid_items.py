import numpy as np
from PySide6.QtCore import Qt, QPointF, QLineF, QRectF, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import QWidget, QGraphicsItem, QGraphicsItemGroup, QGraphicsDropShadowEffect, QStyle, \
    QGraphicsLineItem, QStyleOptionGraphicsItem

from automaton.UIAutomaton import UiState, UiTransition
from ._graphic_items import StateGraphicsItem, LabelGraphicsItem, TransitionGraphicsItem, \
    StateConnectionGraphicsItem, TokenButton, TokenListFrame, TransitionFunctionItem

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts



class StateItem(QGraphicsItemGroup):
    def __init__(self, ui_state: 'UiState', size: int, default_selection_color: QColor, parent: QGraphicsItem | None = None) -> None:
        """Initializes a state group with a graphical representation and interaction elements.
        :param x: The x-coordinate of the state.
        :param y: The y-coordinate of the state.
        :param width: The width of the state.
        :param height: The height of the state.
        :param number: The state's identifier.
        :param default_color: The default color of the state.
        :param default_selection_color: The color used when the state is selected.
        :param parent: The parent graphics item, defaults to None.
        """
        super().__init__(parent)

        self.setSelected(False)
        self.setAcceptHoverEvents(True)
        self.setCacheMode(QGraphicsItem.CacheMode.ItemCoordinateCache)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemSendsScenePositionChanges, True)

        self.ui_state: 'UiState' = ui_state

        self.position = self.ui_state.get_position()
        self.color = self.ui_state.get_colour()
        self.display_text = self.ui_state.get_display_text()
        self.state_type: _ty.Literal['default', 'start', 'end'] = self.ui_state.get_type()

        self.size: int = size

        self.selection_color = default_selection_color
        self.connected_transitions: list['TransitionItemOld'] = []
        self.connection_points: list['StateConnectionGraphicsItem'] = []

        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(20)
        self.shadow.setOffset(0)

        self.state: 'StateGraphicsItem' = StateGraphicsItem(self.position[0], self.position[1], size, self.color, self)
        self.addToGroup(self.state)
        self.label: 'LabelGraphicsItem' = LabelGraphicsItem(self.display_text, self)
        self.label.setParentItem(self)

        self.connection_positions: dict[str, tuple[float, float, QColor]] = self.create_connection_positions(
            self.state.rect())
        self.create_connection_points()

        self.update_shadow_effect()
        self.update_label_position()

    def get_ui_state(self) -> 'UiState':
        """Retrieves the UI state representation of this state.

        :return: The UI state.
        """
        return self.ui_state

    def set_display_text(self, name: str) -> None:
        """Sets the display name of the state.

        :param name: The new name for the state.
        """
        self.label.setPlainText(name)
        self.get_ui_state().set_display_text(name)

    def set_size(self, size: float) -> None:
        """Sets the size of the state while keeping it centered.

        :param size: The new size of the state.
        """
        old_rect: QRectF = self.state.rect()

        center_x: float = old_rect.x() + old_rect.width() / 2
        center_y: float = old_rect.y() + old_rect.height() / 2

        new_x: float = center_x - size / 2
        new_y: float = center_y - size / 2
        new_rect: QRectF = QRectF(new_x, new_y, size, size)
        self.state.setRect(new_rect)
        self.size = size

        for transition in self.connected_transitions:
            transition.update_position()

    def set_color(self, color: QColor) -> None:
        """Sets the color of the state.

        :param color: The new color of the state.
        """
        self.state.setBrush(color)
        self.get_ui_state().set_colour(color)

    def set_arrow_head_size(self, size: int) -> None:
        """Sets the arrow head size for all connected transitions.

        :param size: The new arrow head size.
        """
        for line in self.connected_transitions:
            line.arrow_size = size

    def set_state_type(self, state_type: _ty.Literal['default', 'start', 'end']):
        """Updates the type of the state

        :param state_type: The new state type
        """
        self.state_type = state_type
        self.get_ui_state().set_type(state_type)
        self.state.update(self.state.rect())

    def get_size(self) -> int:
        """Gets the current size of the state.

        :return: The size of the state.
        """
        return self.size

    def get_color(self) -> QColor:
        """Gets the color of the state.

        :return: The state's color.
        """
        return self.get_ui_state().get_colour()

    def get_type(self) -> _ty.Literal['default', 'start', 'end']:
        """Gets the type of the state.

        :return: The state's type as a literal.
        """
        return self.get_ui_state().get_type()

    def get_connected_transitions(self) -> _ty.List['Transition']:
        """Gets the list of transitions connected to this state.

        :return: A list of Transition objects.
        """
        return self.connected_transitions

    def update_ui_state(self, color: QColor, position: tuple[float, float], display_text: str,
                        node_type: _ty.Literal['default', 'start', 'end']) -> None:
        """Updates the UI state with new parameters.

        :param color: The new color.
        :param position: The new position as a tuple (x, y).
        :param display_text: The new display text.
        :param node_type: The state type ('default', 'start', or 'end').
        """
        ui_state = self.get_ui_state()

        ui_state.set_colour(color)
        ui_state.set_position(position)
        ui_state.set_display_text(display_text)
        ui_state.set_type(node_type)

    def create_connection_points(self) -> None:
        """Creates and adds connection points to the state."""
        for direction, value in self.connection_positions.items():
            connection_point = StateConnectionGraphicsItem(value[0], value[1], value[2], direction[0], direction[2:], self)
            self.connection_points.append(connection_point)
            self.addToGroup(connection_point)

    @staticmethod
    def create_connection_positions(rect: QRectF) -> dict[str, tuple[float, float, QColor]]:
        """Creates connection positions for the state.

        :param rect: The bounding rectangle of the state.
        :return: A dictionary mapping connection identifiers to a tuple (x, y, color).
        """
        connection_positions: dict[str, tuple[float, float, QColor]] = {
            'n_in': (rect.left() + rect.width() * 0.4, rect.top(), QColor('darkRed')),
            'n_out': (rect.left() + rect.width() * 0.6, rect.top(), QColor('darkGreen')),
            'e_in': (rect.right(), rect.top() + rect.height() * 0.4, QColor('darkRed')),
            'e_out': (rect.right(), rect.top() + rect.height() * 0.6, QColor('darkGreen')),
            's_out': (rect.left() + rect.width() * 0.4, rect.bottom(), QColor('darkGreen')),
            's_in': (rect.left() + rect.width() * 0.6, rect.bottom(), QColor('darkRed')),
            'w_out': (rect.left(), rect.top() + rect.height() * 0.4, QColor('darkGreen')),
            'w_in': (rect.left(), rect.top() + rect.height() * 0.6, QColor('darkRed'))
        }
        return connection_positions

    def add_transition(self, transition: 'Transition') -> None:
        """Adds a transition to the state's list of connected transitions.

        :param transition: The Transition object to add.
        """
        self.connected_transitions.append(transition)

    def activate(self) -> None:
        """Activates the state, marking it as selected and updating its UI state."""
        self.setSelected(True)
        self.ui_state.set_active(True)

    def deactivate(self) -> None:
        """Deactivates the state, removing its selection and updating its UI state."""
        self.setSelected(False)
        self.ui_state.set_active(False)

    def update_shadow_effect(self) -> None:
        """Updates the shadow effect based on the selection state of the state."""
        if self.isSelected():
            self.shadow.setColor(self.selection_color)
        else:
            self.shadow.setColor(QColor('black'))

        for item in self.childItems():
            if isinstance(item, StateGraphicsItem):
                item.setGraphicsEffect(self.shadow)

    def update_label_position(self) -> None:
        """Updates the position of the state's label to keep it centered."""
        rect_center: QPointF = self.state.rect().center()
        label_width: float = self.label.boundingRect().width()
        label_height: float = self.label.boundingRect().height()
        label_x: float = rect_center.x() - label_width / 2
        label_y: float = rect_center.y() - label_height / 2
        self.label.setPos(label_x, label_y)

    def itemChange(self, change, value):
        """Handles changes to the state item, such as selection or position changes.

        :param change: The type of change.
        :param value: The new value associated with the change.
        :return: The processed value after the change.
        """
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            result = super().itemChange(change, value)
            QTimer.singleShot(0, self.update_shadow_effect)
            return result
        if change == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
            self.update_label_position()
            for transition in self.connected_transitions:
                transition.update_position()
            for connection_point in self.connection_points:
                connection_point.update_position()
        return super().itemChange(change, value)

    def paint(self, painter, option, widget=...):
        """Paints the state group without drawing the selection state.

        :param painter: The QPainter object used for drawing.
        :param option: The style options for the item.
        :param widget: The widget on which the item is painted, defaults to None.
        """
        option.state = option.state & ~QStyle.StateFlag.State_Selected
        super().paint(painter, option, widget)


class TransitionItem(QGraphicsItemGroup):
    def __init__(self, ui_transition: 'UiTransition', ui_automaton: 'UiAutomaton', transition_sections: int,
                 start_point, end_point, start_state, end_state, parent: QGraphicsItem | None = None) -> None:
        super().__init__(parent)

        self.ui_transition: 'UiTransition' = ui_transition
        self.ui_automaton: 'UiAutomaton' = ui_automaton

        self.transition_line_item = TransitionGraphicsItem(start_point, end_point, start_state, end_state, self)
        self.transition_function_item = TransitionFunctionItem(self.ui_automaton, self.transition_line_item, transition_sections, self)

        start_state.add_transition(self)
        end_state.add_transition(self)

        self.addToGroup(self.transition_line_item)
        self.addToGroup(self.transition_function_item)

        self.update_position()

    def get_ui_automaton(self) -> 'UiAutomaton':
        """Retrieves the UI automaton object associated with this transition.

        :return: The UI automaton object.
        """
        return self.ui_automaton

    def get_ui_transition(self) -> 'UiTransition':
        """Retrieves the UI transition object associated with this transition.

        :return: The UI transition object.
        """
        return self.ui_transition

    def set_ui_transition(self, ui_transition) -> None:
        """Sets the UI transition object associated with this transition.

        :param ui_transition: The UI transition object.
        """
        self.ui_transition = ui_transition

    def set_condition(self, condition: _ty.List[str]) -> None:
        """Sets the condition of the transition.

        :param condition: A list of strings representing the condition.
        """
        self.get_ui_transition().set_condition(condition)

    def update_position(self) -> None:

        print('udpate position')
        # transition_line_item
        start_scene = self.transition_line_item.start_point.mapToScene(self.transition_line_item.start_point.boundingRect().center())
        end_scene = self.transition_line_item.end_point.mapToScene(self.transition_line_item.end_point.boundingRect().center())

        start_local = self.mapFromScene(start_scene)
        end_local = self.mapFromScene(end_scene)

        self.transition_line_item.setLine(QLineF(start_local, end_local))

        line = QLineF(start_scene, end_scene)
        self.transition_line_item.setPos(0, 0)

        angle = np.arctan2(line.dy(), line.dx())
        self.transition_line_item.arrow_head = self.transition_line_item.calculate_arrow_head(end_scene, angle)

        # transition_function_item
        center = self.transition_line_item.get_center(start_scene, end_scene)

        button_size = self.transition_function_item.token_button_frame.size()
        token_list_size = self.transition_function_item.token_list_frame.size()

        button_x = center.x() - button_size.width() / 2
        button_y = center.y() - button_size.height() / 2
        self.transition_function_item.token_button_frame.setPos(button_x, button_y)

        token_list_x = center.x() - token_list_size.width() / 2
        token_list_y = button_y + button_size.height() + 5
        self.transition_function_item.token_list_frame.setPos(token_list_x, token_list_y)
