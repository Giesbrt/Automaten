"""Everything regarding the infinite grids items"""
from PySide6.QtWidgets import (QWidget, QStyleOptionGraphicsItem, QGraphicsItem, QGraphicsEllipseItem, QGraphicsWidget,
                               QGraphicsTextItem, QGraphicsItemGroup, QGraphicsLineItem, QStyle)
from PySide6.QtGui import QPainter, QCursor, QFont, QPen, QColor
from PySide6.QtCore import QRect, QRectF, Qt, QPointF

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts


"""
Please remember to type hint :)
"""


class MyItem(QGraphicsWidget):
    def __init__(self, node_item):
        super().__init__(parent=None)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsSelectable, True)

        self.offset: QPointF | None = None

    def boundingRect(self) -> QRect:
        return QRect(0, 0, 30, 30)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = ...) -> None:
        r = QRect(0, 0, 30, 30)
        painter.drawRect(r)

    def mouseMoveEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
        self.moveBy(event.pos().x() - self.offset.x(), event.pos().y() - self.offset.y())


class Label(QGraphicsTextItem):
    """TBA"""
    def __init__(self, text: str, parent: QGraphicsItem | None = None) -> None:
        super().__init__(parent)
        self.setPlainText(text)
        self.setDefaultTextColor(Qt.GlobalColor.black)
        self.setFont(QFont('Arial', 24, QFont.Weight.Bold))  # Needs to be changeable, idk yet how


class Condition(QGraphicsEllipseItem):
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

        self.connected_lines: list["ConnectionLine"] = []

        self.setBrush(color)
        self.setPen(Qt.PenStyle.NoPen)

        self.setSelected(False)

    def add_line(self, line: "ConnectionLine") -> None:
        """TBA"""
        self.connected_lines.append(line)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None):
        if self.isSelected():
            self.setPen(QPen(Qt.GlobalColor.red, 3, Qt.PenStyle.DotLine))
        else:
            self.setPen(Qt.PenStyle.NoPen)
        super().paint(painter, option, widget)


class ConnectionLine(QGraphicsLineItem):
    """TBA"""
    def __init__(self, start_item: Condition, end_item: Condition, parent: QGraphicsItem | None = None) -> None:
        super().__init__(parent)
        self.start_item: Condition = start_item
        self.end_item: Condition = end_item
        self.setPen(QPen(QColor('black'), 2))
        self.start_item.add_line(self)
        self.end_item.add_line(self)
        self.update_line()

    def update_line(self) -> None:
        """TBA"""
        start_pos: QPointF = self.start_item.sceneBoundingRect().center()
        end_pos: QPointF = self.end_item.sceneBoundingRect().center()
        self.setLine(start_pos.x(), start_pos.y(), end_pos.x(), end_pos.y())


class ConditionGroup(QGraphicsItemGroup):
    """TBA"""
    def __init__(self, x: float, y: float, width: int, height: int, number: int, color: Qt.GlobalColor,
                 parent: QGraphicsItem | None = None) -> None:
        super().__init__(parent)
        self.setFlags(QGraphicsItemGroup.GraphicsItemFlag.ItemIsMovable | QGraphicsItemGroup.GraphicsItemFlag.ItemIsSelectable)

        self.condition: Condition = Condition(x, y, width, height, color, self)
        self.label: Label = Label(f'q{number}', self)
        self.update_label_position()

        self.addToGroup(self.condition)
        self.addToGroup(self.label)

    def activate(self) -> None:
        """TBA"""
        self.condition.setSelected(True)

    def deactivate(self) -> None:
        """TBA"""
        self.condition.setSelected(False)

    def update_label_position(self) -> None:
        """TBA"""
        rect: QRectF = self.condition.rect()
        label_width: float = self.label.boundingRect().width()
        label_height: float = self.label.boundingRect().height()
        label_x: float = rect.x() + (rect.width() - label_width) / 2
        label_y: float = rect.y() + (rect.height() - label_height) / 2
        self.label.setPos(label_x, label_y)

    def set_name(self, name: str) -> None:
        """TBA"""
        self.label.setPlainText(name)
        self.update_label_position()

    def set_size(self, size: float) -> None:
        """TBA"""
        old_rect: QRectF = self.condition.rect()

        center_x: float = old_rect.x() + old_rect.width() / 2
        center_y: float = old_rect.y() + old_rect.height() / 2

        new_x: float = center_x - size / 2
        new_y: float = center_y - size / 2
        new_rect: QRectF = QRectF(new_x, new_y, size, size)
        self.condition.setRect(new_rect)
        self.update_label_position()

    def set_color(self, color: Qt.GlobalColor) -> None:
        """TBA"""
        self.condition.setBrush(color)

    def paint(self, painter, option, widget = ...):
        option.state = option.state & ~QStyle.StateFlag.State_Selected
        super().paint(painter, option, widget)
