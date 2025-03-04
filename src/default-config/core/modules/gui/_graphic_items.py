from PySide6.QtCore import Qt, QPointF, QLineF, QRectF, Signal, QMargins
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QPolygonF, QBrush
from PySide6.QtWidgets import QWidget, QGraphicsItem, QGraphicsTextItem, QGraphicsEllipseItem, QGraphicsWidget, \
    QStyleOptionGraphicsItem, QGraphicsLineItem, QListWidget, QLineEdit, QVBoxLayout, \
    QGraphicsProxyWidget, QGraphicsRectItem, QGraphicsSceneMouseEvent, QGraphicsSceneHoverEvent, QPushButton, \
    QHBoxLayout

from ._graphic_support_items import FrameWidgetItem
from painter import PainterStr, StrToPainter
from storage import AppSettings

# Standard typing imports for aps
from functools import partial
import collections.abc as _a
import typing as _ty
import types as _ts
import numpy as np


class StateGraphicsItem(QGraphicsEllipseItem):
    """Represents a state in a state diagram as a circular graphical element.

    This class provides visual and interactive behavior for a state,
    including movement and selection.
    """
    def __init__(self, x: float, y: float, size: int, color: QColor,
                 parent: QGraphicsItem | None = None) -> None:
        """Initializes the state with default properties.

        :param x: The x-coordinate of the state.
        :param y: The y-coordinate of the state.
        :param size: The size of the state.
        :param color: The fill color of the state.
        :param parent: The parent graphics item, defaults to None.
        """
        super().__init__(QRectF(x, y, size, size), parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsMovable, True)
        self.x: float = x
        self.y: float = y
        self.width: int = size
        self.height: int = size
        self.color: QColor = color

        self.setBrush(QColor(self.color))
        self.setPen(Qt.PenStyle.NoPen)

        self.default_painter_str: PainterStr = PainterStr(
            "Ellipse: ((180.0, 180.0), 180.0, 180.0), 6#000000##00000000;")
        self.end_painter_str: PainterStr = PainterStr(
            "Ellipse: ((180.0, 180.0), 180.0, 180.0), 6#000000##00000000;Ellipse: ((180.0, 180.0), 153.0, 153.0), 2#000000##00000000;")
        self.start_painter_str: PainterStr = PainterStr(
            "Polygon: ((80.0, 160.0), (230.0, 160.0), (230.0, 130.0), (280.0, 180.0), (230.0, 230.0), (230.0, 200.0), (80.0, 200.0)), 0#ff0000##ff0000;")

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
            str_painter.draw_painter_str(self.default_painter_str)
        elif state_type == "end":
            str_painter.draw_painter_str(self.end_painter_str)
        elif state_type == "start":
            str_painter.draw_painter_str(self.start_painter_str)
        painter.restore()


class StateConnectionGraphicsItem(QGraphicsEllipseItem):
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

    def update_position(self):
        for key, values in self.parentItem().create_connection_positions(self.parentItem().state.rect()).items():
            if f'{self.get_direction()}_{self.get_flow()}' == key:
                self.setRect(QRectF(values[0] - self._size / 2, values[1] - self._size / 2, self._size, self._size))
                if self.is_hovered and self.get_flow() == 'out':
                    self.setRect(QRectF(values[0] - self._hovered_size / 2, values[1] - self._hovered_size / 2,
                                        self._hovered_size, self._hovered_size))

    def paint(self, painter, option, widget=None):
        """Paints the connection point and adjusts its size when hovered.

        :param painter: The QPainter object used for drawing.
        :param option: The style options for the item.
        :param widget: The widget on which the item is painted, defaults to None.
        """
        self.update_position()
        super().paint(painter, option, widget)


class LabelGraphicsItem(QGraphicsTextItem):
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
        self.settings = AppSettings()
        self.setFont(QFont(self.settings.get_font(), 24, QFont.Weight.Bold))
        self.settings.font_changed.connect(lambda: self.setFont(QFont(self.settings.get_font(), 24, QFont.Weight.Bold)))

    def paint(self, painter, option, widget=None):
        """Paints the label and updates its text from the parent's UI state.

        :param painter: The QPainter object used for drawing.
        :param option: The style options for the item.
        :param widget: The widget on which the item is painted, defaults to None.
        """
        super().paint(painter, option, widget)

class TransitionGraphicsItem(QGraphicsLineItem):
    """TBA"""
    def __init__(self, start_point, end_point, start_state, end_state,
                 parent: QGraphicsItem | None = None) -> None:
        """Initializes a Transition between two connection points.

        :param start_point: The starting connection point.
        :param end_point: The ending connection point.
        :param parent: The parent graphics item, defaults to None.
        """
        super().__init__(parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent)

        self.start_point: 'StateConnectionGraphicsItem' = start_point
        self.end_point: 'StateConnectionGraphicsItem' = end_point

        self.start_state: 'StateItem' = start_state
        self.end_state: 'StateItem' = end_state

        self.arrow_size: int = 10
        self.arrow_head: QPolygonF | None = None

        self.setPen(QPen(QColor(0, 10, 33), 4))

    def get_ui_transition(self) -> 'UiTransition':
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

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None) -> None:
        """Renders the transition line and arrow head.

        :param painter: The QPainter object used for drawing.
        :param option: The style options for the graphics item.
        :param widget: The widget on which the item is painted, defaults to None.
        """
        super().paint(painter, option, widget)
        if self.arrow_head:
            painter.setBrush(QColor(0, 0, 0))
            painter.drawPolygon(self.arrow_head)


class TokenButton(QPushButton):
    """The token button to open the selection menu"""
    def __init__(self, text: str, toggle_token_selection_list, button_index: int, parent: QWidget = None) -> None:
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
        ''')


class TokenButtonFrame(QGraphicsProxyWidget):
    """The token button frame to """

    all_token_set: Signal = Signal(list)

    def __init__(self, token_list_frame, sections: int, parent: QWidget = None) -> None:
        """Initializes the token selection button container.

        :param token_list_frame: The associated token selection list.
        :param sections: The number of token sections/buttons.
        :param parent: The parent graphics item, defaults to None.
        """
        super().__init__(parent)
        self.token_list_frame = token_list_frame
        self.sections = sections
        self.token_buttons: _ty.List[TokenButton] = []

        container = self._create_container()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        for i in range(self.sections):
            token_button = TokenButton('...', self.toggle_token_selection_list, i, container)
            layout.addWidget(token_button)
            self.token_buttons.append(token_button)
            if i < self.sections - 1:
                layout.addWidget(self._create_separator(container))

        container.setLayout(layout)
        self.setWidget(container)

    @staticmethod
    def _create_container() -> QWidget:
        """Creates the container widget for token buttons.

        :return: A new container widget.
        """
        return FrameWidgetItem(
            bg_color=QColor("white"),
            border_color=QColor("lightgray"),
            border_radius=2,
            border_width=1
        )

    @staticmethod
    def _create_separator(parent: QWidget) -> QWidget:
        """Creates a separator widget.

        :param parent: The parent widget for the separator.
        :return: A configured separator widget.
        """
        separator = QWidget(parent)
        separator.setFixedWidth(1)
        separator.setStyleSheet('background-color: black;')
        return separator

    def set_token(self, values: _ty.Tuple[int, str]) -> None:
        """Sets the token text for a specified button and checks if all tokens are filled.

        :param values: A tuple containing the button index and the new text.
        """
        index, text = values
        self.token_buttons[index].setText(text)
        self.check_all_tokens_filled()

    def set_condition(self, condition: _ty.List[str]) -> None:
        """Sets the condition for each token button.

        :param condition: A list of tokens representing the condition.
        """
        for i, token in enumerate(condition):
            if i < len(self.token_buttons):
                self.token_buttons[i].setText(token)

    def toggle_token_selection_list(self, button_index: int) -> None:
        """Toggles the visibility of the token selection list for the given button.

        :param button_index: The index of the token button.
        """
        self.token_list_frame.set_visible(not self.token_list_frame.isVisible(), button_index)
        return self.token_list_frame

    def check_all_tokens_filled(self) -> None:
        """Checks if all token buttons have a non-placeholder token and emits a signal if so."""
        if all(button.text() != '...' for button in self.token_buttons):
            tokens = [button.text() for button in self.token_buttons]
            self.all_token_set.emit(tokens)


class TokenListFrame(QGraphicsProxyWidget):

    token_selected: Signal(tuple) = Signal(tuple)

    def __init__(self, token_list: _ty.Tuple[_ty.List[str], _ty.List[str]], parent: QWidget = None) -> None:
        """Initializes the token selection list widget.

        :param token_list: A list of tokens to display.
        :param parent: The parent graphics item, defaults to None.
        """
        super().__init__(parent)
        self.token_lists: _ty.Tuple[_ty.List[str], _ty.List[str]] = token_list
        self.button_index: _ty.Union[int, None] = None

        container = FrameWidgetItem(bg_color=QColor("white"), border_color=QColor("white"), border_radius=10, border_width=0)
        container.setFixedSize(100, 150)

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

    def set_visible(self, visible: bool, button_index: int = None) -> None:
        """Sets the visibility of the token selection list.

        :param visible: True to show the list, False to hide.
        :param button_index: The index of the button triggering the action, defaults to None.
        """
        self.setVisible(visible)
        self.button_index = button_index
        if self.token_lists:
            self.update_token_lists(self.token_lists)

    def show_list(self, button_index: int) -> None:
        self.setVisible(True)
        self.button_index = button_index
        if self.token_lists:
            self.update_token_lists(self.token_lists)

    def hide_list(self):
        self.setVisible(False)

    def update_token_lists(self, token_lists: _ty.Tuple[_ty.List[str], _ty.List[str]]) -> None:
        """Updates the token list with view on the automaton type

        :param token_lists: The new token list
        """
        self.token_lists = token_lists
        self.list_widget.clear()

        if self.button_index is None or self.button_index in [0, 1]:
            tokens_to_show = self.token_lists[0]
        elif self.button_index == 2:
            tokens_to_show = self.token_lists[1]
        else:
            tokens_to_show = self.token_lists[0]
        self.list_widget.addItems(tokens_to_show)

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


class TransitionFunctionItem(QGraphicsProxyWidget):
    def __init__(self, ui_automaton, transition, sections, parent=None) -> None:
        """Initializes the transition function widget.

        :param ui_automaton: The central ui automaton
        :param sections: The number of sections for token selection.
        :param transition: The transition associated with this function.
        :param parent: The parent graphics item, defaults to None.
        """
        super().__init__(parent)

        self.ui_automaton = ui_automaton
        self.token_lists = self.ui_automaton.get_token_lists()

        self.transition_item: 'TransitionItem' = self.parentItem()

        self.token_list_frame = TokenListFrame(self.token_lists, self)
        self.token_button_frame = TokenButtonFrame(self.token_list_frame, sections, self)

        self._setup_signals()

    def _setup_signals(self):
        """Connects signals to the corresponding slots."""
        self.token_list_frame.token_selected.connect(self.token_button_frame.set_token)
        self.token_button_frame.all_token_set.connect(self.set_condition)

    def set_condition(self, condition: _ty.List[str]) -> None:
        """Sets the condition of the transition and updates the UI elements.

        :param condition: A list of the currently selected tokens.
        """
        self.token_button_frame.set_condition(condition)
        self.transition_item.get_ui_transition().set_condition(condition)

    def update_token_list(self, token_lists: tuple[list[str], list[str]]) -> None:
        """Updates the token list and replaces invalid tokens in the condition."""
        print(token_lists)
        self.token_lists = token_lists
        self.token_list_frame.update_token_lists(token_lists)
