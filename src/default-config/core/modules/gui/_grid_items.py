"""Everything regarding the infinite grids items"""
from PySide6.QtStateMachine import QStateMachine, QState
from PySide6.QtWidgets import (QStyleOptionGraphicsItem, QGraphicsItem, QGraphicsEllipseItem, QGraphicsWidget,
                               QGraphicsTextItem, QGraphicsItemGroup, QGraphicsLineItem, QStyle, QLineEdit, QHBoxLayout,
                               QWidget, QGraphicsProxyWidget, QGraphicsDropShadowEffect, QVBoxLayout,
                               QListWidget, QPushButton)
from PySide6.QtGui import QPainter, QFont, QPen, QColor, QPolygonF, QPainterPath
from PySide6.QtCore import QRectF, Qt, QPointF, QLineF, Signal

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts
import numpy as np

from core.modules.automaton.UIAutomaton import UiState, UiTransition


class Label(QGraphicsTextItem):
    """
    A text label for displaying the name of a state in a state diagram.

    This class represents a label that is automatically updated to reflect
    the display text of its parent state.
    """
    def __init__(self, text: str, parent: QGraphicsItem | None = None) -> None:
        """
        Initialize the label with default styling.

        Args:
            text (str): The initial text to display.
            parent (QGraphicsItem | None, optional): The parent graphics item. Defaults to None.
        """
        super().__init__(parent)
        self.setPlainText(text)
        self.setDefaultTextColor(Qt.GlobalColor.black)
        self.setFont(QFont('Arial', 24, QFont.Weight.Bold))  # Needs to be changeable, idk yet how

    def paint(self, painter, option, widget=None):
        """
        Paint the label, ensuring it reflects the parent's display text.
        """
        super().paint(painter, option, widget)
        self.setPlainText(self.parentItem().ui_state.get_display_text())


class State(QGraphicsEllipseItem):
    """
    Represents a state in a state diagram as a circular graphical element.

    This class provides visual and interactive behavior for a state,
    including movement and selection.
    """
    def __init__(self, x: float, y: float, width: int, height: int, color: Qt.GlobalColor,
                 parent: QGraphicsItem | None = None) -> None:
        """
        Initialize the state with default properties.

        Args:
            x (float): The x-coordinate of the state.
            y (float): The y-coordinate of the state.
            width (int): The width of the state.
            height (int): The height of the state.
            color (Qt.GlobalColor): The fill color of the state.
            parent (QGraphicsItem | None, optional): The parent graphics item. Defaults to None.
        """
        super().__init__(QRectF(x, y, width, height), parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsMovable, True)
        self.x: float = x
        self.y: float = y
        self.width: int = width
        self.height: int = height

        self.setBrush(color)
        self.setPen(Qt.PenStyle.NoPen)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None):
        """
        Paint the state as an ellipse, changing its border when selected.
        """
        state_type = self.parentItem().get_type()

        painter.save()
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.setBrush(self.brush() if state_type == 'default' or state_type == 'start' else Qt.BrushStyle.NoBrush)
        painter.drawEllipse(self.boundingRect())
        painter.restore()

        if state_type == 'end':
            painter.save()
            inner_margin = 5
            inner_rect = self.boundingRect().adjusted(inner_margin, inner_margin, -inner_margin, -inner_margin)
            painter.setBrush(Qt.GlobalColor.white)
            painter.drawEllipse(inner_rect)
            painter.restore()


class ConnectionPoint(QGraphicsEllipseItem):
    """
    Represents a connection point on a state for transitions.

    This class defines points on a state where transitions can start or end.
    Connection points are color-coded and can change size when hovered.
    """
    def __init__(self, x: float, y: float, color: Qt.GlobalColor,
                 direction: _ty.Literal['n', 's', 'e', 'w'],
                 flow: _ty.Literal['in', 'out'],
                 parent: QGraphicsItem | None = None) -> None:
        """
        Initialize a connection point.

        Args:
            x (float): The x-coordinate of the connection point.
            y (float): The y-coordinate of the connection point.
            color (Qt.GlobalColor): The color of the connection point.
            direction (Literal['n', 's', 'e', 'w']): The direction the point faces.
            flow (Literal['in', 'out']): Whether the connection point is an input or output.
            parent (QGraphicsItem | None, optional): The parent graphics item. Defaults to None.
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
        """
        Get the direction of the connection point.

        Returns:
            Literal['n', 's', 'e', 'w']: The direction of the connection point.
        """
        return self.direction

    def get_flow(self) -> _ty.Literal['in', 'out']:
        """
        Get the flow type of the connection point.

        Returns:
            Literal['in', 'out']: The flow type of the connection point.
        """
        return self.flow

    def paint(self, painter, option, widget=None):
        for key, values in self.parentItem().create_connection_positions(self.parentItem().state.rect()).items():
            if f'{self.get_direction()}_{self.get_flow()}' == key:
                self.setRect(QRectF(values[0] - self._size / 2, values[1] - self._size / 2, self._size, self._size))
                if self.is_hovered and self.get_flow() == 'out':
                    self.setRect(QRectF(values[0] - self._hovered_size / 2, values[1] - self._hovered_size / 2, self._hovered_size, self._hovered_size))

        super().paint(painter, option, widget)


class Transition(QGraphicsLineItem):
    """TBA"""
    def __init__(self, start_point: ConnectionPoint, end_point: ConnectionPoint, parent: QGraphicsItem | None = None) -> None:
        """
        Initialize a Transition between two connection points.

        Args:
            start_point (ConnectionPoint): The connection point of the start state.
            end_point (ConnectionPoint): The connection point of the end state.
            parent (QGraphicsItem | None, optional): The parent graphics item. Defaults to None.
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

        self.transition_function = None
        self.arrow_size: int = 10
        self.arrow_head: QPolygonF | None = None

        self.setPen(QPen(QColor(0, 10, 33), 4))
        self.update_position()

    def set_transition_function(self, transition_function) -> None:
        """
        Set the transition function associated with this transition.

        Args:
            transition_function: The widget or function representing the transition function.
        """
        self.transition_function = transition_function

    def get_transition_function(self):
        return self.transition_function

    def set_transition(self, condition: _ty.List[str]):
        self.ui_transition.set_condition(condition)

    def get_ui_transition(self) -> UiTransition:
        """
        Retrieve the UI transition object associated with this transition.

        Returns:
            UiTransition: The UI representation of the transition.
        """
        return self.ui_transition

    def get_center(self, p1: QPointF, p2: QPointF) -> QPointF:
        """
        Calculate the center point between two given points.

        Args:
            p1 (QPointF): The first point.
            p2 (QPointF): The second point.

        Returns:
            QPointF: The center point between p1 and p2.
        """
        return QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)

    def calculate_arrow_head(self, end_scene_pos: QPointF, angle: float) -> QPolygonF:
        """
        Calculate the arrow head polygon for the transition line.

        Args:
            end_scene_pos (QPointF): The end point of the transition in scene coordinates.
            angle (float): The angle of the line in radians.

        Returns:
            QPolygonF: The polygon representing the arrow head.
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
        """
        Update the position of the transition line and arrow head.

        This method recalculates the positions of the start and end points,
        updates the line connecting them, computes the angle for the arrow head,
        and if a transition function is set, centers it along the line.
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

            button_size = self.transition_function.button.size()
            # label_size = self.transition_function.label.size()
            token_list_size = self.transition_function.token_list.size()

            button_x = center.x() - button_size.width() / 2
            button_y = center.y() - button_size.height() / 2
            self.transition_function.button.setPos(button_x, button_y)

            gap = 5
            """label_x = center.x() - label_size.width() / 2
            label_y = button_y - gap - label_size.height()
            self.transition_function.label.setPos(label_x, label_y)"""

            token_list_x = center.x() - token_list_size.width() / 2
            token_list_y = button_y + button_size.height() + gap
            self.transition_function.token_list.setPos(token_list_x, token_list_y)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None) -> None:
        """
        Render the transition line and arrow head on the scene.
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
    def __init__(self, parent=None, bg_color=QColor("white"),
                 border_color=QColor("white"), border_radius=2, border_width=1):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._bg_color = bg_color
        self._border_color = border_color
        self._border_radius = border_radius
        self._border_width = border_width

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        # Verkleinere den zu zeichnenden Bereich, damit der Rand nicht abgeschnitten wird:
        half_border_width = self._border_width // 2
        adjusted_rect = rect.adjusted(half_border_width, half_border_width,
                                      -half_border_width, -half_border_width)
        path = QPainterPath()
        path.addRoundedRect(adjusted_rect, self._border_radius, self._border_radius)
        # Fülle nur innerhalb des abgegrenzten, abgerundeten Bereichs:
        painter.fillPath(path, self._bg_color)
        pen = QPen(self._border_color, self._border_width)
        painter.setPen(pen)
        painter.drawPath(path)


class TokenButton(QPushButton):
    def __init__(self, text: str, toggle_token_selection_list, parent=None):
        super().__init__(text, parent)

        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        self.clicked.connect(toggle_token_selection_list)

        self.setStyleSheet('''
            QPushButton {
                color: black; 
                padding: 8px;
                border: none;
            }
            QPushButton:hover {
                border: 1px solid red;
            }
        ''')


class TokenSelectionButton(QGraphicsProxyWidget):
    def __init__(self, token_list_widget, sections, parent=None):
        super().__init__(parent)
        # Verwende ein kleineres RoundedFrameWidget für einen kompakten Button:
        self.token_list = token_list_widget
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
            token_button = TokenButton('...', self.toggle_token_selection_list, container)
            layout.addWidget(token_button)
            if (self.sections == 2 and i == 0) or (self.sections == 3 and i == 0) or (self.sections == 3 and i == 1):
                seperator = QWidget(container)
                seperator.setFixedWidth(1)
                seperator.setStyleSheet('background-color: black;')
                layout.addWidget(seperator)
            self.token_buttons.append(token_button)

        container.setLayout(layout)
        self.setWidget(container)

    def toggle_token_selection_list(self):
        self.token_list.setVisible(not self.token_list.isVisible())


class TokenSelectionList(QGraphicsProxyWidget):
    """
    Dieses Widget zeigt:
      - Ein oben angeordnetes, beschreibbares Suchfeld,
      - Einen dicken, farblich abgesetzten horizontalen Separator direkt unterhalb des Suchfelds
      - Eine scrollbare Liste, in der die Items durch dünne, über die gesamte Breite gehende Trennlinien voneinander
        unterteilt sind.
    Das gesamte Widget ist in einem RoundedFrameWidget eingebettet, sodass die Ecken abgerundet sind.
    """
    token_selected = Signal(list)

    def __init__(self, tokens, parent=None):
        super().__init__(parent)
        self.tokens = tokens
        self.selected_tokens = []

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
        self.list_widget.addItems(self.tokens)
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
        ''')
        layout.addWidget(self.list_widget)

        container.setLayout(layout)
        self.setWidget(container)

        self.search_bar.textChanged.connect(self.filter_tokens)
        self.list_widget.itemClicked.connect(self.item_clicked)

        self.setVisible(False)

    def filter_tokens(self, text):
        filter_text = text.lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(filter_text not in item.text().lower())

    def item_clicked(self, item):
        token = item.text()
        if token not in self.selected_tokens:
            self.selected_tokens.append(token)
        self.token_selected.emit(self.selected_tokens)


class TransitionFunction(QGraphicsProxyWidget):
    def __init__(self, tokens, sections, transition, parent=None) -> None:
        super().__init__(parent)
        self.tokens = tokens
        self.transition = transition
        self.sections = sections
        # Erstelle die einzelnen Elemente:
        # self.label = TokenSelectionLabel(self)
        self.token_list = TokenSelectionList(self.tokens, self)
        self.button = TokenSelectionButton(self.token_list, self.sections, self)

        # self.token_list.token_selected.connect(self.label.update_text)

    def close_token_selection_list(self) -> None:
        self.token_list.setVisible(False)

    def set_condition(self, condition):
        self.transition.get_ui_transition().set_condition(condition)


class TempTransition(QGraphicsLineItem):
    def __init__(self, start_item: ConnectionPoint, end_point: QPointF, parent: QGraphicsItem | None = None) -> None:
        """
        Initialize a temporary transition.

        Args:
            start_item (ConnectionPoint): The starting connection point.
            end_point (QPointF): The initial end position.
            parent (QGraphicsItem | None, optional): The parent graphics item. Defaults to None.
        """
        super().__init__(parent)
        self.start_item: ConnectionPoint = start_item
        self.setPen(QPen(Qt.GlobalColor.white, 3))
        self.update_transition(end_point)

    def update_transition(self, end_point: QPointF) -> None:
        """
        Update the temporary transition line to a new end point.

        Args:
            end_point (QPointF): The new end position of the transition.
        """
        start_scene_pos = self.start_item.mapToScene(self.start_item.boundingRect().center())
        start_local = self.mapFromScene(start_scene_pos)
        end_local = self.mapFromScene(end_point)
        self.setLine(QLineF(start_local, end_local))


class StateGroup(QGraphicsItemGroup):
    def __init__(self, x: float, y: float, width: int, height: int, number: int, default_color: Qt.GlobalColor,
                 default_selection_color: Qt.GlobalColor, parent: QGraphicsItem | None = None) -> None:
        """
        Initialize a state group with a graphical representation and interaction elements.

        Args:
            x (float): The x-coordinate of the state.
            y (float): The y-coordinate of the state.
            width (int): The width of the state.
            height (int): The height of the state.
            number (int): The state's identifier.
            default_color (Qt.GlobalColor): The default color of the state.
            default_selection_color (Qt.GlobalColor): The default color of selection.
            parent (QGraphicsItem | None, optional): The parent graphics item. Defaults to None.
        """
        super().__init__(parent)

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
            display_text = f'q{number}',
            node_type = 'default'
        )

        self.state: State = State(x, y, width, height, default_color, self)
        self.addToGroup(self.state)
        self.label: Label = Label(f'q{number}', self)
        self.label.setParentItem(self)

        self.connection_positions: dict[str, tuple[float, float, Qt.GlobalColor]] = self.create_connection_positions(self.state.rect())
        self.create_connection_points()

        self.update_shadow_effect()
        self.update_label_position()

    def set_name(self, name: str) -> None:
        """
        Set the name of the state.

        Args:
            name (str): The new name of the state.
        """
        self.ui_state.set_display_text(name)

    def set_size(self, size: float) -> None:
        """
        Set the size of the state while keeping it centered.

        Args:
            size (float): The new size of the state.
        """
        old_rect: QRectF = self.state.rect()

        center_x: float = old_rect.x() + old_rect.width() / 2
        center_y: float = old_rect.y() + old_rect.height() / 2

        new_x: float = center_x - size / 2
        new_y: float = center_y - size / 2
        new_rect: QRectF = QRectF(new_x, new_y, size, size)
        print(new_rect)
        self.state.setRect(new_rect)
        self.size = size

        for transition in self.connected_transitions:
            transition.update_position()

    def set_color(self, color: Qt.GlobalColor) -> None:
        """
        Set the color of the state.

        Args:
            color (Qt.GlobalColor): The new color of the state.
        """
        self.state.setBrush(color)
        self.get_ui_state().set_colour(color)

    def set_arrow_head_size(self, size: int) -> None:
        """
        Set the size of the arrowheads for all connected transitions.

        Args:
            size (int): The new arrowhead size.
        """
        for line in self.connected_transitions:
            line.arrow_size = size

    def get_size(self) -> int:
        return self.size

    def get_color(self) -> Qt.GlobalColor:
        return self.get_ui_state().get_colour()

    def get_type(self) -> _ty.Literal['default', 'start', 'end']:
        return self.state_type

    def get_ui_state(self) -> UiState:
        """
        Retrieve the UI state representation of this state.

        Returns:
            UiState: The UI representation of the state.
        """
        return self.ui_state

    def create_connection_positions(self, rect: QRectF) -> dict[str, tuple[float, float, Qt.GlobalColor]]:
        """
        Create connection positions for the state.

        Args:
            rect (QRectF): The bounding rectangle of the state.

        Returns:
            dict[str, tuple[float, float, Qt.GlobalColor]]: A dictionary mapping
            connection points to their positions and colors.
        """
        connection_positions: dict[str, tuple[float, float, Qt.GlobalColor]] = {
            'n_in': (rect.left() + rect.width() * 0.4, rect.top(), Qt.GlobalColor.darkRed),
            'n_out': (rect.left() + rect.width() * 0.6, rect.top(), Qt.GlobalColor.darkGreen),
            'e_in': (rect.right(), rect.top() + rect.height() * 0.4, Qt.GlobalColor.darkRed),
            'e_out': (rect.right(), rect.top() + rect.height() * 0.6, Qt.GlobalColor.darkGreen),
            's_out': (rect.left() + rect.width() * 0.4, rect.bottom(), Qt.GlobalColor.darkGreen),
            's_in': (rect.left() + rect.width() * 0.6, rect.bottom(), Qt.GlobalColor.darkRed),
            'w_out': (rect.left(), rect.top() + rect.height() * 0.4, Qt.GlobalColor.darkGreen),
            'w_in': (rect.left(), rect.top() + rect.height() * 0.6, Qt.GlobalColor.darkRed)
        }
        return connection_positions

    def add_transition(self, transition: Transition) -> None:
        """
        Add a transition to the state's list of connected transitions.

        Args:
            transition (Transition): The transition to be added.
        """
        self.connected_transitions.append(transition)

    def create_connection_points(self) -> None:
        """
        Create and add connection points to the state.
        """
        for direction, value in self.connection_positions.items():
            connection_point = ConnectionPoint(value[0], value[1], value[2], direction[0], direction[2:], self)
            self.connection_points.append(connection_point)
            self.addToGroup(connection_point)

    def activate(self) -> None:
        """
        Activate the state, marking it as selected and updating its UI status.
        """
        self.setSelected(True)
        self.ui_state.set_active(True)

    def deactivate(self) -> None:
        """
        Deactivate the state, removing its selection and updating its UI status.
        """
        self.setSelected(False)
        self.ui_state.set_active(False)

    def change_type(self, state_type: str):
        self.state_type = state_type
        self.state.update(self.state.rect())

    def update_shadow_effect(self) -> None:
        if self.isSelected():
            self.shadow.setColor(Qt.GlobalColor.black)
        else:
            self.shadow.setColor(self.selection_color)

        for item in self.childItems():
            if isinstance(item, State):
                item.setGraphicsEffect(self.shadow)

    def update_label_position(self) -> None:
        """
        Update the position of the state's label to keep it centered.
        """
        rect_center: QPointF = self.state.rect().center()
        label_width: float = self.label.boundingRect().width()
        label_height: float = self.label.boundingRect().height()
        label_x: float = rect_center.x() - label_width / 2
        label_y: float = rect_center.y() - label_height / 2
        self.label.setPos(label_x, label_y)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            self.update_shadow_effect()
        if change == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
            self.update_label_position()
            for transition in self.connected_transitions:
                transition.update_position()
        return super().itemChange(change, value)

    def paint(self, painter, option, widget = ...):
        option.state = option.state & ~QStyle.StateFlag.State_Selected
        super().paint(painter, option, widget)