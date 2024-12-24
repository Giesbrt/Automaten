"""Everything regarding the infinite grids items"""
from PySide6.QtWidgets import (QWidget, QStyleOptionGraphicsItem, QGraphicsItem, QGraphicsEllipseItem, QGraphicsWidget,
                               QGraphicsTextItem)
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
    def __init__(self, parent=None):
        super().__init__(parent)

    def mousePressEvent(self, event):
        if isinstance(self.parentItem(), Condition):
            self.parentItem().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if isinstance(self.parentItem(), Condition):
            self.parentItem().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if isinstance(self.parentItem(), Condition):
            self.parentItem().mouseReleaseEvent(event)


class Condition(QGraphicsEllipseItem):
    def __init__(self, x: float, y: float, width: int, height: int, color: Qt.GlobalColor, parent: QWidget | None = None):
        super().__init__(QRectF(x, y, width, height), parent=parent)
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.setBrush(color)
        self.setPen(Qt.PenStyle.NoPen)

        self.label = Label(self)
        self.label.setPlainText('q1')
        self.label.setFont(QFont('Arial', 24, QFont.Weight.Bold))
        self.label.setDefaultTextColor(Qt.GlobalColor.black)
        self.update_label_position()

        self.setSelected(False)

    def activate(self):
        self.setPen(QPen(QColor('red'), 3))
        self.setSelected(True)

    def deactivate(self):
        self.setPen(Qt.PenStyle.NoPen)
        self.setSelected(False)

    def update_label_position(self):
        rect = self.rect()
        label_width = self.label.boundingRect().width()
        label_height = self.label.boundingRect().height()
        label_x = rect.x() + (rect.width() - label_width) / 2
        label_y = rect.y() + (rect.height() - label_height) / 2
        self.label.setPos(label_x, label_y)

    def set_name(self, name: str) -> None:
        self.label.setPlainText(name)
        self.update_label_position()

    def set_size(self, size) -> None:
        self.setRect(QRectF(self.rect().x(), self.rect().y(), size, size))
        self.update_label_position()

    def set_color(self, color: Qt.GlobalColor):
        self.setBrush(color)
        self.setPen(Qt.PenStyle.NoPen)

    def mousePressEvent(self, event):
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        self.old_pos = event.scenePos()

    def mouseMoveEvent(self, event):
        delta = event.scenePos() - self.old_pos
        self.moveBy(delta.x(), delta.y())
        self.old_pos = event.scenePos()

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
