"""Everything regarding the infinite grids items"""
from PySide6.QtWidgets import (QStyleOptionGraphicsItem, QGraphicsItem, QGraphicsEllipseItem, QGraphicsWidget,
                               QGraphicsTextItem, QGraphicsItemGroup, QGraphicsLineItem, QStyle, QLineEdit, QHBoxLayout,
                               QWidget, QGraphicsProxyWidget, QGraphicsDropShadowEffect, QVBoxLayout,
                               QListWidget, QPushButton)
from PySide6.QtGui import QPainter, QFont, QPen, QColor, QPolygonF, QPainterPath
from PySide6.QtCore import QRectF, Qt, QPointF, QLineF, Signal

from functools import partial

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts
import numpy as np

from core.modules.automaton.UIAutomaton import UiState, UiTransition
from core.modules.painter import StrToPainter


class Label(QGraphicsTextItem):
    """
    A text label for displaying the name of a state in a state diagram.

    This class represents a label that is automatically updated to reflect
    the display text of its parent state.
    """
    def __init__(self, text: str, parent: QGraphicsItem | None = None) -> None:
        """Initializes the label with default styling.

        :param text: The initial text to display.
        :param parent: The parent graphics item, defaults to None.
        """
        super().__init__(parent)
        self.setPlainText(text)
        self.setDefaultTextColor(QColor('black'))
        self.setFont(QFont('Arial', 24, QFont.Weight.Bold))  # Needs to be changeable, idk yet how

    def paint(self, painter, option, widget=None):
        """Paints the label and updates its text from the parent's UI state.

        :param painter: The QPainter object used for drawing.
        :param option: The style options for the item.
        :param widget: The widget on which the item is painted, defaults to None.
        """
        super().paint(painter, option, widget)
        # self.setPlainText(self.parentItem().ui_state.get_display_text())


class State(QGraphicsEllipseItem):
    """
    Represents a state in a state diagram as a circular graphical element.

    This class provides visual and interactive behavior for a state,
    including movement and selection.
    """
    def __init__(self, x: float, y: float, width: int, height: int, color: QColor,
                 parent: QGraphicsItem | None = None) -> None:
        """Initializes the state with default properties.

        :param x: The x-coordinate of the state.
        :param y: The y-coordinate of the state.
        :param width: The width of the state.
        :param height: The height of the state.
        :param color: The fill color of the state.
        :param parent: The parent graphics item, defaults to None.
        """
        super().__init__(QRectF(x, y, width, height), parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsMovable, True)
        self.x: float = x
        self.y: float = y
        self.width: int = width
        self.height: int = height
        self.color: QColor = color

        self.setBrush(QColor(self.color))
        self.setPen(Qt.PenStyle.NoPen)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None):
        """Paints the state as an ellipse and adds an inner circle if the state type is 'end'.

        :param painter: The QPainter object used for drawing.
        :param option: The style options for the item.
        :param widget: The widget on which the item is painted, defaults to None.
        """
        state_type = self.parentItem().get_type()

        painter.save()
        painter.setBrush(self.brush())
        painter.drawEllipse(self.boundingRect())
        # Create StrToPainter instance
        center: QPointF = self.boundingRect().center()
        str_painter = StrToPainter(painter, center, min(self.boundingRect().width(), self.boundingRect().height()))
        # print("BR", self.boundingRect(), center)
        if state_type == "default":
            str_painter.draw_string("Ellipse: ((180.0, 180.0), 180.0, 180.0), 6#000000##00000000;")
        elif state_type == "end":
            str_painter.draw_string("Ellipse: ((180.0, 180.0), 180.0, 180.0), 6#000000##00000000;Ellipse: ((180.0, 180.0), 153.0, 153.0), 2#000000##00000000;")
        painter.restore()


class ConnectionPoint(QGraphicsEllipseItem):
    """
    Represents a connection point on a state for transitions.

    This class defines points on a state where transitions can start or end.
    Connection points are color-coded and can change size when hovered.
    """
    def __init__(self, x: float, y: float, color: QColor,
                 direction: _ty.Literal['n', 's', 'e', 'w'],
                 flow: _ty.Literal['in', 'out'],
                 parent: QGraphicsItem | None = None) -> None:
        """Initializes a connection point.

        :param x: The x-coordinate of the connection point.
        :param y: The y-coordinate of the connection point.
        :param color: The color of the connection point.
        :param direction: The direction the point faces ('n', 's', 'e', 'w').
        :param flow: The flow type ('in' or 'out').
        :param parent: The parent graphics item, defaults to None.
        """
        super().__init__(QRectF(x - 5, y - 5, 10, 10), parent)
        self.direction: _ty.Literal['n', 's', 'e', 'w'] = direction
        self.flow: _ty.Literal['in', 'out'] = flow

        self.is_hovered = False
        self._size = 10
        self._hovered_size = 15

        self.setAcceptHoverEvents(True)
        self.setBrush(QColor(color))
        self.setPen(Qt.PenStyle.NoPen)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)

    def get_direction(self) -> _ty.Literal['n', 's', 'e', 'w']:
        """Gets the direction of the connection point.

        :return: The direction as a literal ('n', 's', 'e', 'w').
        """
        return self.direction

    def get_flow(self) -> _ty.Literal['in', 'out']:
        """Gets the flow type of the connection point.

        :return: The flow type as a literal ('in' or 'out').
        """
        return self.flow

    def paint(self, painter, option, widget=None):
        """Paints the connection point and adjusts its size when hovered.

        :param painter: The QPainter object used for drawing.
        :param option: The style options for the item.
        :param widget: The widget on which the item is painted, defaults to None.
        """
        # return
        for key, values in self.parentItem().create_connection_positions(self.parentItem().state.rect()).items():
            if f'{self.get_direction()}_{self.get_flow()}' == key:
                self.setRect(QRectF(values[0] - self._size / 2, values[1] - self._size / 2, self._size, self._size))
                if self.is_hovered and self.get_flow() == 'out':
                    self.setRect(QRectF(values[0] - self._hovered_size / 2, values[1] - self._hovered_size / 2, self._hovered_size, self._hovered_size))

        super().paint(painter, option, widget)


class Transition(QGraphicsLineItem):
    """TBA"""
    def __init__(self, start_point: ConnectionPoint, end_point: ConnectionPoint, parent: QGraphicsItem | None = None) -> None:
        """Initializes a Transition between two connection points.

        :param start_point: The starting connection point.
        :param end_point: The ending connection point.
        :param parent: The parent graphics item, defaults to None.
        """
        super().__init__(parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent)

        self.start_point: ConnectionPoint = start_point
        self.end_point: ConnectionPoint = end_point

        self.start_state: StateGroup = self.start_point.parentItem()
        self.end_state: StateGroup = self.end_point.parentItem()

        self.ui_transition = UiTransition(
            from_state = self.start_state.get_ui_state(),
            from_state_connecting_point = start_point.get_direction(),
            to_state = self.end_state.get_ui_state(),
            to_state_connecting_point = end_point.get_direction(),
            condition = []
        )

        self.start_state.add_transition(self)
        self.end_state.add_transition(self)

        self.transition_function: TransitionFunction | None = None
        self.arrow_size: int = 10
        self.arrow_head: QPolygonF | None = None

        self.setPen(QPen(QColor(0, 10, 33), 4))
        self.update_position()

    def set_transition(self, condition: _ty.List[str]):
        """Sets the condition of the transition.

        :param condition: A list of strings representing the condition.
        """
        self.ui_transition.set_condition(condition)

    def set_transition_function(self, transition_function) -> None:
        """Sets the transition function associated with this transition.

        :param transition_function: The widget or function representing the transition function.
        """
        self.transition_function = transition_function

    def get_transition_function(self) -> 'TransitionFunction':
        """Retrieves the transition function associated with this transition.

        :return: The transition function.
        """
        return self.transition_function

    def get_ui_transition(self) -> UiTransition:
        """Retrieves the UI transition object associated with this transition.

        :return: The UI transition object.
        """
        return self.ui_transition

    @staticmethod
    def get_center(p1: QPointF, p2: QPointF) -> QPointF:
        """Calculates the center point between two given points.

        :param p1: The first point.
        :param p2: The second point.
        :return: The center point as a QPointF.
        """
        return QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)

    def calculate_arrow_head(self, end_scene_pos: QPointF, angle: float) -> QPolygonF:
        """Calculates the arrow head polygon for the transition line.

        :param end_scene_pos: The end point of the transition in scene coordinates.
        :param angle: The angle of the line in radians.
        :return: A QPolygonF representing the arrow head.
        """
        arrow_p1 = end_scene_pos - QPointF(
            np.cos(angle + np.pi / 6) * self.arrow_size,
            np.sin(angle + np.pi / 6) * self.arrow_size
        )
        arrow_p2 = end_scene_pos - QPointF(
            np.cos(angle - np.pi / 6) * self.arrow_size,
            np.sin(angle - np.pi / 6) * self.arrow_size
        )

        return QPolygonF([
            self.mapFromScene(arrow_p1),
            self.mapFromScene(end_scene_pos),
            self.mapFromScene(arrow_p2)
        ])

    def update_position(self) -> None:
        """Updates the position of the transition line and arrow head.

        This method recalculates the start and end points, updates the connecting line,
        computes the angle for the arrow head, and centers the transition function if set.
        """
        start_scene_pos = self.start_point.mapToScene(self.start_point.boundingRect().center())
        end_scene_pos = self.end_point.mapToScene(self.end_point.boundingRect().center())

        start_local = self.mapFromScene(start_scene_pos)
        end_local = self.mapFromScene(end_scene_pos)

        self.setLine(QLineF(start_local, end_local))

        line = QLineF(start_scene_pos, end_scene_pos)
        self.setPos(0, 0)

        angle = np.arctan2(line.dy(), line.dx())
        self.arrow_head = self.calculate_arrow_head(end_scene_pos, angle)

        if self.transition_function:
            center = self.get_center(start_scene_pos, end_scene_pos)

            button_size = self.transition_function.token_buttons.size()
            token_list_size = self.transition_function.token_list.size()

            button_x = center.x() - button_size.width() / 2
            button_y = center.y() - button_size.height() / 2
            self.transition_function.token_buttons.setPos(button_x, button_y)

            gap = 5

            token_list_x = center.x() - token_list_size.width() / 2
            token_list_y = button_y + button_size.height() + gap
            self.transition_function.token_list.setPos(token_list_x, token_list_y)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None) -> None:
        """Renders the transition line and arrow head.

        :param painter: The QPainter object used for drawing.
        :param option: The style options for the graphics item.
        :param widget: The widget on which the item is painted, defaults to None.
        """
        super().paint(painter, option, widget)
        if self.arrow_head:
            painter.setBrush(QColor(0, 10, 33))
            painter.drawPolygon(self.arrow_head)


class RoundedFrameWidget(QWidget):
    """
    Dieses Widget zeichnet einen Rahmen mit abgerundeten Ecken und
    füllt nur den inneren, abgegrenzten Bereich mit der Hintergrundfarbe.
    """
    def __init__(self, parent=None, bg_color=QColor("white"), border_color=QColor("white"), border_radius=2, border_width=1):
        """Initializes the rounded frame widget.

        :param parent: The parent widget, defaults to None.
        :param bg_color: The background color, defaults to white.
        :param border_color: The border color, defaults to white.
        :param border_radius: The radius of the rounded corners.
        :param border_width: The width of the border.
        """
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._bg_color = bg_color
        self._border_color = border_color
        self._border_radius = border_radius
        self._border_width = border_width

    def paintEvent(self, event):
        """Handles the paint event to draw the rounded frame.

        :param event: The paint event.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        half_border_width = self._border_width // 2
        adjusted_rect = rect.adjusted(half_border_width, half_border_width,
                                      -half_border_width, -half_border_width)
        path = QPainterPath()
        path.addRoundedRect(adjusted_rect, self._border_radius, self._border_radius)
        painter.fillPath(path, self._bg_color)
        pen = QPen(self._border_color, self._border_width)
        painter.setPen(pen)
        painter.drawPath(path)


class TokenButton(QPushButton):
    def __init__(self, text: str, toggle_token_selection_list, button_index: int, parent=None):
        """Initializes the token button.

        :param text: The initial text of the button.
        :param toggle_token_selection_list: The callback to toggle the token selection list.
        :param button_index: The index of the button.
        :param parent: The parent widget, defaults to None.
        """
        super().__init__(text, parent)
        self.button_index = button_index
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.clicked.connect(partial(toggle_token_selection_list, self.button_index))
        self.setStyleSheet('''
            QPushButton {
                color: black; 
                padding: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: yellow;
            }
        ''')


class TokenSelectionButton(QGraphicsProxyWidget):

    all_token_set: Signal(list) = Signal(list)

    def __init__(self, token_list, sections, parent=None):
        """Initializes the token selection button container.

        :param token_list: The associated token selection list.
        :param sections: The number of token sections/buttons.
        :param parent: The parent graphics item, defaults to None.
        """
        super().__init__(parent)
        self.token_list = token_list
        self.sections = sections

        self.token_buttons = []

        container = RoundedFrameWidget(
            bg_color=QColor("white"),
            border_color=QColor("lightgray"),
            border_radius=2,
            border_width=1
        )

        layout = QHBoxLayout(container)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        for i in range(self.sections):
            token_button = TokenButton('...', self.toggle_token_selection_list, i, container)
            layout.addWidget(token_button)
            if (self.sections == 2 and i == 0) or (self.sections == 3 and i == 0) or (self.sections == 3 and i == 1):
                seperator = QWidget(container)
                seperator.setFixedWidth(1)
                seperator.setStyleSheet('background-color: black;')
                layout.addWidget(seperator)
            self.token_buttons.append(token_button)

        container.setLayout(layout)
        self.setWidget(container)

    def set_token(self, values: tuple[int, str]) -> None:
        """Sets the token text for a specified button and checks if all tokens are filled.

        :param values: A tuple containing the button index and the new text.
        """
        self.token_buttons[values[0]].setText(values[1])
        self.check_all_tokens_filled()

    def set_condition(self, condition: _ty.List[str]):
        for i, token in enumerate(condition):
            self.token_buttons[i].setText(token)

    def toggle_token_selection_list(self, button_index: int) -> None:
        """Toggles the visibility of the token selection list for the given button.

        :param button_index: The index of the token button.
        """
        self.token_list.set_visible(not self.token_list.isVisible(), button_index)

    def check_all_tokens_filled(self) -> None:
        """Checks if all token buttons have a non-placeholder token and emits a signal if so."""
        if all(button.text() != '...' for button in self.token_buttons):
            tokens = [button.text() for button in self.token_buttons]
            # print(tokens)
            self.all_token_set.emit(tokens)


class TokenSelectionList(QGraphicsProxyWidget):

    token_selected: Signal(tuple) = Signal(tuple)

    def __init__(self, token_list: _ty.List[str], parent=None):
        """Initializes the token selection list widget.

        :param token_list: A list of tokens to display.
        :param parent: The parent graphics item, defaults to None.
        """
        super().__init__(parent)
        self.token_list: _ty.List[str] = token_list
        self.button_index: int | None = None

        container = RoundedFrameWidget(bg_color=QColor("white"),
                                       border_color=QColor("white"),
                                       border_radius=10,
                                       border_width=0)
        container.setFixedWidth(100)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(0)

        self.search_bar = QLineEdit(container)
        self.search_bar.setPlaceholderText("Search ...")
        self.search_bar.setStyleSheet('''
            QLineEdit {
                border: none; 
                padding: 5px; 
                font-size: 14px; 
                background: transparent; 
                color: black;
            }
        ''')
        layout.addWidget(self.search_bar)

        self.search_separator = QWidget(container)
        self.search_separator.setFixedHeight(2)
        self.search_separator.setStyleSheet("background-color: #6666ff;")
        layout.addWidget(self.search_separator)

        self.list_widget = QListWidget(container)
        self.list_widget.addItems(self.token_list)
        self.list_widget.setStyleSheet('''
            QListWidget { 
                border: none; 
                background: transparent; 
            }
            QListWidget::item { 
                color: black; 
                padding: 8px; 
                border-bottom: 1px solid #cccccc; 
            }
            QListWidget::item:hover {
                background-color: lightblue;
            }
        ''')
        layout.addWidget(self.list_widget)

        container.setLayout(layout)
        self.setWidget(container)

        self.search_bar.textChanged.connect(self.filter_tokens)
        self.list_widget.itemClicked.connect(self.item_clicked)

        self.set_visible(False)

    def set_visible(self, visible: bool, button_index: int=None) -> None:
        """Sets the visibility of the token selection list.

        :param visible: True to show the list, False to hide.
        :param button_index: The index of the button triggering the action, defaults to None.
        """
        self.button_index = button_index
        self.setVisible(visible)

    def update_token_list(self, token_list: _ty.List[str]) -> None:
        """Updates the token list with view on the automaton type

        :param token_list: The new token list
        """
        self.list_widget.clear()

        if len(token_list) > 1:
            self.list_widget.addItems(token_list[0])
        else:
            self.list_widget.addItems(token_list)

    def filter_tokens(self, text) -> None:
        """Filters the token list based on the search text.

        :param text: The search text used to filter tokens.
        """
        filter_text = text.lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(filter_text not in item.text().lower())

    def item_clicked(self, item) -> None:
        """Handles the event when a token is clicked in the list.

        :param item: The clicked list item.
        """
        token = item.text()
        self.token_selected.emit((self.button_index, token))


class TransitionFunction(QGraphicsProxyWidget):
    def __init__(self, tokens, sections, transition, parent=None) -> None:
        """Initializes the transition function widget.

        :param tokens: A list of tokens for the transition function.
        :param sections: The number of sections for token selection.
        :param transition: The transition associated with this function.
        :param parent: The parent graphics item, defaults to None.
        """
        super().__init__(parent)
        self.tokens = tokens
        self.transition = transition
        self.sections = sections

        self.token_list = TokenSelectionList(self.tokens, self)
        self.token_buttons = TokenSelectionButton(self.token_list, self.sections, self)

        self._setup_signals()

    def _setup_signals(self):
        """Verbindet Signale mit den entsprechenden Slots."""
        self.token_list.token_selected.connect(self.token_buttons.set_token)
        self.token_buttons.all_token_set.connect(self.set_condition)

    def set_condition(self, condition: list[str]) -> None:
        """Setzt die Bedingung der Transition und aktualisiert die UI-Elemente.

        :param condition: Eine Liste der aktuell gewählten Tokens.
        """
        validated_condition = self._validate_condition(condition)
        self.transition.get_ui_transition().set_condition(validated_condition)
        self.token_buttons.set_condition(validated_condition)

    def _validate_condition(self, condition: list[str]) -> list[str]:
        """Überprüft und ersetzt ungültige Tokens in der Bedingung.

        Falls ein Token nicht mehr existiert, wird es durch ein Platzhalter-Token ersetzt.
        """
        valid_condition = []
        for token in condition:
            if token in self.tokens:
                valid_condition.append(token)
        return valid_condition

    def update_token_list(self, new_token_list: list[str]) -> None:
        """Aktualisiert die Token-Liste und ersetzt ungültige Tokens in der Bedingung."""
        self.tokens = new_token_list
        self.token_list.update_token_list(new_token_list)

        current_condition = self.token_buttons.token_buttons
        new_condition = self._validate_condition([btn.text() for btn in current_condition])

        self.set_condition(new_condition)


class TempTransition(QGraphicsLineItem):
    def __init__(self, start_item: ConnectionPoint, end_point: QPointF, parent: QGraphicsItem | None = None) -> None:
        """Initializes a temporary transition line.

        :param start_item: The starting connection point.
        :param end_point: The initial end position as a QPointF.
        :param parent: The parent graphics item, defaults to None.
        """
        super().__init__(parent)
        self.start_item: ConnectionPoint = start_item
        self.setPen(QPen(QColor('white'), 3))
        self.update_transition(end_point)

    def update_transition(self, end_point: QPointF) -> None:
        """Updates the temporary transition line to a new end point.

        :param end_point: The new end position as a QPointF.
        """
        start_scene_pos = self.start_item.mapToScene(self.start_item.boundingRect().center())
        start_local = self.mapFromScene(start_scene_pos)
        end_local = self.mapFromScene(end_point)
        self.setLine(QLineF(start_local, end_local))


class StateGroup(QGraphicsItemGroup):
    def __init__(self, x: float, y: float, width: int, height: int, number: int | str, default_color: QColor,
                 default_selection_color: QColor, parent: QGraphicsItem | None = None) -> None:
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

        self.setCacheMode(QGraphicsItem.CacheMode.ItemCoordinateCache)

        self.setSelected(False)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemSendsScenePositionChanges, True)

        self.size: int = width
        self.selection_color = default_selection_color
        self.state_type: _ty.Literal['default', 'start', 'end'] = 'default'
        self.connected_transitions: list['Transition'] = []
        self.connection_points: list['ConnectionPoint'] = []

        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(20)
        self.shadow.setOffset(0)

        self.ui_state = UiState(
            colour = default_color,
            position = (x, y),
            display_text = f'q{number}' if isinstance(number, int) else number,
            node_type = self.get_type()
        )

        self.state: State = State(x, y, width, height, default_color, self)
        self.addToGroup(self.state)
        self.label: Label = Label(f'q{number}' if isinstance(number, int) else number, self)
        self.label.setParentItem(self)

        self.connection_positions: dict[str, tuple[float, float, QColor]] = self.create_connection_positions(self.state.rect())
        self.create_connection_points()

        self.update_shadow_effect()
        self.update_label_position()

    def set_name(self, name: str) -> None:
        """Sets the display name of the state.

        :param name: The new name for the state.
        """
        self.ui_state.set_display_text(name)

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
        self.get_ui_state().set_type(state_type)
        self.state_type = state_type
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
        return self.state_type

    def get_ui_state(self) -> UiState:
        """Retrieves the UI state representation of this state.

        :return: The UI state.
        """
        return self.ui_state

    def get_connected_transitions(self) -> _ty.List['Transition']:
        """Gets the list of transitions connected to this state.

        :return: A list of Transition objects.
        """
        return self.connected_transitions

    def update_ui_state(self, color: QColor, position: tuple[float, float], display_text: str, node_type: _ty.Literal['default', 'start', 'end']) -> None:
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

    def add_transition(self, transition: Transition) -> None:
        """Adds a transition to the state's list of connected transitions.

        :param transition: The Transition object to add.
        """
        self.connected_transitions.append(transition)

    def create_connection_points(self) -> None:
        """Creates and adds connection points to the state."""
        for direction, value in self.connection_positions.items():
            connection_point = ConnectionPoint(value[0], value[1], value[2], direction[0], direction[2:], self)
            self.connection_points.append(connection_point)
            self.addToGroup(connection_point)

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
            self.shadow.setColor(QColor('black'))
        else:
            self.shadow.setColor(self.selection_color)

        for item in self.childItems():
            if isinstance(item, State):
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
            self.update_shadow_effect()
        if change == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
            self.update_label_position()
            for transition in self.connected_transitions:
                transition.update_position()
        return super().itemChange(change, value)

    def paint(self, painter, option, widget = ...):
        """Paints the state group without drawing the selection state.

        :param painter: The QPainter object used for drawing.
        :param option: The style options for the item.
        :param widget: The widget on which the item is painted, defaults to None.
        """
        option.state = option.state & ~QStyle.StateFlag.State_Selected
        super().paint(painter, option, widget)