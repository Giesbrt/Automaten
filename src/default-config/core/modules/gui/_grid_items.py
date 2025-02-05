"""Everything regarding the infinite grids items"""
from PySide6.QtWidgets import (QStyleOptionGraphicsItem, QGraphicsItem, QGraphicsEllipseItem, QGraphicsWidget,
                               QGraphicsTextItem, QGraphicsItemGroup, QGraphicsLineItem, QStyle, QLineEdit, QHBoxLayout,
                               QWidget, QGraphicsProxyWidget, QGraphicsDropShadowEffect)
from PySide6.QtGui import QPainter, QFont, QPen, QColor, QPolygonF, QKeyEvent, QTextCursor, QRegularExpressionValidator
from PySide6.QtCore import QRectF, Qt, QPointF, QLineF, QPropertyAnimation, QEasingCurve

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
                 selected_color: Qt.GlobalColor, parent: QGraphicsItem | None = None) -> None:
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
        self.selected_color = selected_color

        self.glow_effect = QGraphicsDropShadowEffect()
        self.glow_effect.setBlurRadius(20)
        self.glow_effect.setColor(self.selected_color)
        self.glow_effect.setOffset(0)
        self.setGraphicsEffect(self.glow_effect)

        self.setBrush(color)
        self.setPen(Qt.PenStyle.NoPen)

        self.setSelected(True)

    def setSelected(self, value: bool) -> None:
        super().setSelected(value)
        self.update(self.rect())

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None):
        """
        Paint the state as an ellipse, changing its border when selected.
        """
        if self.isSelected():
            self.glow_effect.setColor(self.selected_color)
        else:
            self.glow_effect.setColor(Qt.GlobalColor.black)
        self.update()
        painter.drawEllipse(self.boundingRect())
        option.state = option.state & ~QStyle.StateFlag.State_Selected
        super().paint(painter, option, widget)


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

    def grow(self):
        """
        Increase the size of the connection point when hovered.
        """
        new_rect = self.rect().adjusted(-5, -5, 5, 5)
        self.setRect(new_rect)
        self.is_hovered = True

    def shrink(self):
        """
        Restore the original size of the connection point when not hovered.
        """
        new_rect = self.rect().adjusted(5, 5, -5, -5)
        self.setRect(new_rect)
        self.is_hovered = False

    def paint(self, painter, option, widget=None):
        for key, values in self.parentItem().create_connection_positions(self.parentItem().state.rect()).items():
            if f'{self.get_direction()}_{self.get_flow()}' == key:
                self.setRect(QRectF(values[0] - 5, values[1] - 5, 10, 10))
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
            tf_width = self.transition_function.size().width()
            tf_height = self.transition_function.size().height()

            self.transition_function.setPos(center.x() - tf_width / 2, center.y() - tf_height / 2)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None) -> None:
        """
        Render the transition line and arrow head on the scene.
        """
        super().paint(painter, option, widget)
        if self.arrow_head:
            painter.setBrush(QColor(0, 10, 33))
            painter.drawPolygon(self.arrow_head)


class Section(QLineEdit):
    def __init__(self, section_width: int, handle_function, parent=None) -> None:
        super().__init__(parent)
        self.setMaxLength(1)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(section_width, section_width)

        validator = QRegularExpressionValidator('[A-Z]')
        self.setValidator(validator)

        self.textChanged.connect(handle_function)

        self.setStyleSheet(f"""
            Section {{
                border: 1px solid #3498db;
                border-radius: 4px;
                background-color: rgba(25, 92, 137, 0.5);
                font-size: {section_width // 1.5}px;
                font-weight: bold;
                color: #ffffff;
                selection-background-color: #2980b9;
            }}
            Section:focus {{
                border: 1px solid #2980b9;
                background-color: rgba(52, 152, 219, 0.2);
            }}
        """)


class MultiSectionLineEdit(QWidget):
    def __init__(self, sections: int, set_condition=None, parent=None) -> None:
        """
        Initialize the multi-section line edit widget.

        Args:
            sections (int): The number of input sections.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.sections = sections
        self.set_condition = set_condition
        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(2)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.fields = []
        self.section_width = 30
        self.spacing = self.layout.spacing()
        self._create_fields()
        self._adjust_size()

    def _create_fields(self) -> None:
        """
        Create and configure the input fields for each section.

        Each field is set to accept a single uppercase character.
        """
        for _ in range(self.sections):
            field = Section(self.section_width, self._handle_text_change, self)
            field.setObjectName('section')
            self.fields.append(field)
            self.layout.addWidget(field)

    def _adjust_size(self) -> None:
        """
        Adjust the widget size based on the number of sections and spacing.

        This ensures that the widget's fixed size properly fits all input fields.
        """
        total_width = (self.section_width * self.sections) + self.spacing * (self.sections - 1)
        total_height = self.section_width
        self.setFixedSize(total_width, total_height)

    def _handle_text_change(self) -> None:
        """
        Handle the text change event in the input fields.

        When text is entered in a field, focus is automatically moved to the next field.
        """
        for i, field in enumerate(self.fields):
            if field.text() and i < len(self.fields) - 1:
                self.fields[i + 1].setFocus()

        if all(field.text() for field in self.fields):
            if self.set_condition:
                self.set_condition(self.get_text())

    def set_text(self, text: str) -> None:
        """
        Set the text for the multi-section input fields.

        Args:
            text (str): The text to set. Each character is assigned to a field sequentially.
        """
        for i, char in enumerate(text):
            if i < len(self.fields):
                self.fields[i].setText(char)

    def get_text(self) -> _ty.List[str]:
        """
        Retrieve the concatenated text from all input fields.

        Returns:
            _ty.List[str]: The combined text from each section.
        """
        return [field.text() for field in self.fields]


class TransitionFunction(QGraphicsProxyWidget):
    def __init__(self, sections: int, transition: Transition, parent=None) -> None:
        """
        Initialize the transition function widget.

        Args:
            sections (int): The number of input sections for the transition function.
            parent (QGraphicsItem | None, optional): The parent graphics item. Defaults to None.
        """
        super().__init__(parent)

        self.transition = transition
        self.line_edit = MultiSectionLineEdit(sections, self.set_condition)
        self.setWidget(self.line_edit)

    def set_condition(self, condition: _ty.List[str]) -> None:
        """
        Retrieve the transition function as a concatenated string.

        Returns:
            str: The transition function text extracted from the input fields.
        """
        self.transition.get_ui_transition().set_condition(condition)
        print(self.transition.get_ui_transition())


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
                 default_selected_color: Qt.GlobalColor, parent: QGraphicsItem | None = None) -> None:
        """
        Initialize a state group with a graphical representation and interaction elements.

        Args:
            x (float): The x-coordinate of the state.
            y (float): The y-coordinate of the state.
            width (int): The width of the state.
            height (int): The height of the state.
            number (int): The state's identifier.
            default_color (Qt.GlobalColor): The default color of the state.
            default_selected_color (Qt.GlobalColor): The default color of selection.
            parent (QGraphicsItem | None, optional): The parent graphics item. Defaults to None.
        """
        super().__init__(parent)
        self.ui_state = UiState(
            colour = default_color,
            position = (x, y),
            display_text = f'q{number}',
            node_type = 'default'
        )

        # self.create_glow_effect()
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)

        self.state: State = State(x, y, width, height, default_color, default_selected_color, self)
        self.label: Label = Label(f'q{number}', self)
        self.update_label_position()

        self.addToGroup(self.state)
        self.addToGroup(self.label)

        self.size: int = width
        self.connected_transitions: list[Transition] = []
        self.connection_points: list[ConnectionPoint] = []
        rect: QRectF = self.state.rect()
        self.connection_positions: dict[str, tuple[float, float, Qt.GlobalColor]] = self.create_connection_positions(rect)
        self.create_connection_points()

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

    def set_condition(self, condition: _ty.List[str]):
        pass

    def get_size(self) -> int:
        return self.size

    def get_color(self) -> Qt.GlobalColor:
        return self.get_ui_state().get_colour()

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
        self.state.setSelected(True)
        self.ui_state.set_active(True)

    def deactivate(self) -> None:
        """
        Deactivate the state, removing its selection and updating its UI status.
        """
        self.state.setSelected(False)
        self.ui_state.set_active(False)

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

    def mouseMoveEvent(self, event) -> None:
        super().mouseMoveEvent(event)
        for line in self.connected_transitions:
            line.update_position()

    def paint(self, painter, option, widget = ...):
        option.state = option.state & ~QStyle.StateFlag.State_Selected
        super().paint(painter, option, widget)
        self.update_label_position()