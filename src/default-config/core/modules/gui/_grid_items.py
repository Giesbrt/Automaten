"""Everything regarding the infinite grids items"""
from PySide6.QtWidgets import (QStyleOptionGraphicsItem, QGraphicsItem, QGraphicsEllipseItem, QGraphicsWidget,
                               QGraphicsTextItem, QGraphicsItemGroup, QGraphicsLineItem, QStyle)
from PySide6.QtGui import QPainter, QFont, QPen, QColor, QPolygonF, QKeyEvent
from PySide6.QtCore import QRectF, Qt, QPointF, QLineF

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts
import numpy as np

from core.modules.automaton.UIAutomaton import UiState, UiTransition


class Label(QGraphicsTextItem):
    """TBA"""
    def __init__(self, text: str, parent: QGraphicsItem | None = None) -> None:
        super().__init__(parent)
        self.setPlainText(text)
        self.setDefaultTextColor(Qt.GlobalColor.black)
        self.setFont(QFont('Arial', 24, QFont.Weight.Bold))  # Needs to be changeable, idk yet how

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)

        self.setPlainText(self.parentItem().ui_state.get_display_text())


class State(QGraphicsEllipseItem):
    """TBA"""
    def __init__(self, x: float, y: float, width: int, height: int, color: Qt.GlobalColor,
                 parent: QGraphicsItem | None = None) -> None:
        super().__init__(QRectF(x, y, width, height), parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsMovable, True)
        self.x: float = x
        self.y: float = y
        self.width: int = width
        self.height: int = height

        self.setBrush(color)
        self.setPen(Qt.PenStyle.NoPen)

        self.setSelected(False)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None):
        if self.isSelected():
            self.setPen(QPen(Qt.GlobalColor.red, 3, Qt.PenStyle.DotLine))
        else:
            self.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(self.boundingRect())
        super().paint(painter, option, widget)


class ConnectionPoint(QGraphicsEllipseItem):
    def __init__(self, x: float, y: float, color: Qt.GlobalColor,
                 direction: _ty.Literal['n', 's', 'e', 'w'],
                 flow: _ty.Literal['in', 'out'],
                 parent: QGraphicsItem | None = None) -> None:
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
        return self.direction

    def get_flow(self) -> _ty.Literal['in', 'out']:
        return self.flow

    def grow(self):
        new_rect = self.rect().adjusted(-5, -5, 5, 5)
        self.setRect(new_rect)
        self.is_hovered = True

    def shrink(self):
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
        super().__init__(parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent)

        self.start_point: ConnectionPoint = start_point
        self.end_point: ConnectionPoint = end_point

        self.start_state: StateGroup = self.start_point.parentItem()
        self.end_state: StateGroup = self.end_point.parentItem()

        self.ui_transition = UiTransition(
            from_state = start_point.parentItem().get_ui_state(),
            from_state_connecting_point = start_point.get_direction(),
            to_state = end_point.parentItem().get_ui_state(),
            to_state_connecting_point = end_point.get_direction(),
            condition = ['a']
        )

        self.start_state.add_transition(self)
        self.end_state.add_transition(self)

        self.line = None
        self.arrow_size: int = 10

        self.setPen(QPen(Qt.GlobalColor.black, 4))
        # self.update_transition()

    def get_ui_transition(self) -> UiTransition:
        return self.ui_transition

    def update_transition(self) -> None:
        start_scene_pos = self.start_point.mapToScene(self.start_point.boundingRect().center())
        end_scene_pos = self.end_point.mapToScene(self.end_point.boundingRect().center())

        start_local = self.mapFromScene(start_scene_pos)
        end_local = self.mapFromScene(end_scene_pos)

        self.setLine(QLineF(start_local, end_local))

    def paint(self, painter, option, widget=None):
        start_scene_pos = self.start_point.mapToScene(self.start_point.boundingRect().center())
        end_scene_pos = self.end_point.mapToScene(self.end_point.boundingRect().center())

        self.line = QLineF(start_scene_pos, end_scene_pos)
        self.setLine(self.line)

        # print(self.line.dy(), self.line.dx())

        angle = np.atan2(self.line.dy(),self.line.dx())

        arrow_p1 = self.line.p2() - QPointF(np.cos(angle + np.pi / 6) * self.arrow_size,
                                            np.sin(angle + np.pi / 6) * self.arrow_size)
        arrow_p2 = self.line.p2() - QPointF(np.cos(angle - np.pi / 6) * self.arrow_size,
                                            np.sin(angle - np.pi / 6) * self.arrow_size)

        # print(arrow_p1, arrow_p2, start_local, end_local, angle)

        arrow_head = QPolygonF([self.mapToScene(arrow_p2), self.mapToScene(self.line.p2()), self.mapToScene(arrow_p1)])

        # Zeichne die Pfeilspitze
        painter.setPen(self.pen())
        painter.drawLine(self.line)
        painter.setBrush(self.pen().color())
        painter.drawPolygon(arrow_head)


class TransitionLineEdit(QGraphicsTextItem):
    def __init__(self, pos: QPointF, text: str, parent: QGraphicsItem | None = None) -> None:
        super().__init__(text, parent)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        print(self.parentItem().__dict__)

        self.setPos(self.mapToScene(self.parentItem().line.center()))

        self.setFocus()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.clearFocus()
        else:
            super().keyPressEvent(event)


class TempTransition(QGraphicsLineItem):
    def __init__(self, start_item: ConnectionPoint, end_point: QPointF, parent: QGraphicsItem | None = None) -> None:
        super().__init__(parent)
        self.start_item: ConnectionPoint = start_item
        self.setPen(QPen(Qt.GlobalColor.white, 3))
        self.update_transition(end_point)

    def update_transition(self, end_point: QPointF) -> None:
        start_scene_pos = self.start_item.mapToScene(self.start_item.boundingRect().center())
        start_local = self.mapFromScene(start_scene_pos)
        end_local = self.mapFromScene(end_point)
        self.setLine(QLineF(start_local, end_local))


class StateGroup(QGraphicsItemGroup):
    """TBA"""
    def __init__(self, x: float, y: float, width: int, height: int, number: int, color: Qt.GlobalColor,
                 parent: QGraphicsItem | None = None) -> None:
        super().__init__(parent)
        self.ui_state = UiState(
            colour = Qt.GlobalColor.gray,
            position = (x, y),
            display_text = f'q{number}',
            node_type = 'default'
        )

        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)  # Aktiviere Hover-Events für die Gruppe

        self.state: State = State(x, y, width, height, color, self)
        self.label: Label = Label(f'q{number}', self)
        self.update_label_position()

        self.addToGroup(self.state)
        self.addToGroup(self.label)

        self.connected_lines: list[Transition] = []
        self.connection_points: list[ConnectionPoint] = []
        rect: QRectF = self.state.rect()
        self.connection_positions: dict[str, tuple[float, float, Qt.GlobalColor]] = self.create_connection_positions(rect)
        self.create_connection_points()

    def create_connection_positions(self, rect: QRectF):
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

    def get_ui_state(self) -> UiState:
        return self.ui_state

    def add_transition(self, line: Transition) -> None:
        """TBA"""
        self.connected_lines.append(line)

    def create_connection_points(self) -> None:
        rect: QRectF = self.state.rect()
        connections: dict[str, tuple[float, float, Qt.GlobalColor]] = {
            'n_in': (rect.left() + rect.width() * 0.4, rect.top(), Qt.GlobalColor.darkRed),
            'n_out': (rect.left() + rect.width() * 0.6, rect.top(), Qt.GlobalColor.darkGreen),
            'e_in': (rect.right(), rect.top() + rect.height() * 0.4, Qt.GlobalColor.darkRed),
            'e_out': (rect.right(), rect.top() + rect.height() * 0.6, Qt.GlobalColor.darkGreen),
            's_out': (rect.left() + rect.width() * 0.4, rect.bottom(), Qt.GlobalColor.darkGreen),
            's_in': (rect.left() + rect.width() * 0.6, rect.bottom(), Qt.GlobalColor.darkRed),
            'w_out': (rect.left(), rect.top() + rect.height() * 0.4, Qt.GlobalColor.darkGreen),
            'w_in': (rect.left(), rect.top() + rect.height() * 0.6, Qt.GlobalColor.darkRed)
        }

        for direction, value in connections.items():
            connection_point = ConnectionPoint(value[0], value[1], value[2], direction[0], direction[2:], self)
            self.connection_points.append(connection_point)
            self.addToGroup(connection_point)

    def activate(self) -> None:
        """TBA"""
        self.state.setSelected(True)
        self.ui_state.set_active(True)

    def deactivate(self) -> None:
        """TBA"""
        self.state.setSelected(False)
        self.ui_state.set_active(False)

    def update_label_position(self) -> None:
        """TBA"""
        rect_center: QPointF = self.state.rect().center()
        label_width: float = self.label.boundingRect().width()
        label_height: float = self.label.boundingRect().height()
        label_x: float = rect_center.x() - label_width / 2
        label_y: float = rect_center.y() - label_height / 2
        self.label.setPos(label_x, label_y)

    def set_name(self, name: str) -> None:
        """TBA"""
        self.ui_state.set_display_text(name)
        self.update_label_position()

    def set_size(self, size: float) -> None:
        """TBA"""
        old_rect: QRectF = self.state.rect()

        center_x: float = old_rect.x() + old_rect.width() / 2
        center_y: float = old_rect.y() + old_rect.height() / 2

        new_x: float = center_x - size / 2
        new_y: float = center_y - size / 2
        new_rect: QRectF = QRectF(new_x, new_y, size, size)
        self.state.setRect(new_rect)
        self.update_label_position()

    def set_color(self, color: Qt.GlobalColor) -> None:
        """TBA"""
        self.state.setBrush(color)

    def mouseMoveEvent(self, event) -> None:
        super().mouseMoveEvent(event)
        # for line in self.connected_lines:
        #     line.update_transition()

    def paint(self, painter, option, widget = ...):
        option.state = option.state & ~QStyle.StateFlag.State_Selected
        super().paint(painter, option, widget)
        self.update_label_position()
