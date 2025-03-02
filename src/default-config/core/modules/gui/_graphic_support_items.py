from PySide6.QtCore import Qt, QPointF, QLineF, QRectF, Signal, QEvent, QSizeF, QMargins
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QFont, QPolygonF, QBrush
from PySide6.QtWidgets import QWidget, QGraphicsItem, QGraphicsTextItem, QGraphicsEllipseItem, QGraphicsWidget, \
    QStyleOptionGraphicsItem, QGraphicsLineItem, QListWidget, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout, \
    QGraphicsProxyWidget, QGraphicsItemGroup, QGraphicsSceneMouseEvent, QGraphicsRectItem, QGraphicsLinearLayout, \
    QGraphicsLayoutItem

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

class TempTransitionItem(QGraphicsLineItem):
    def __init__(self, start_item: 'StateConnectionGraphicsItem', end_point: QPointF, parent: QGraphicsItem | None = None) -> None:
        """Initializes a temporary transition line.

        :param start_item: The starting connection point.
        :param end_point: The initial end position as a QPointF.
        :param parent: The parent graphics item, defaults to None.
        """
        super().__init__(parent)
        self.start_item: 'StateConnectionGraphicsItem' = start_item
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

class FrameWidgetItem(QWidget):
    """
        Dieses Widget zeichnet einen Rahmen mit abgerundeten Ecken und
        füllt nur den inneren, abgegrenzten Bereich mit der Hintergrundfarbe.
        """

    def __init__(self, parent=None, bg_color=QColor("white"), border_color=QColor("white"), border_radius=2,
                 border_width=1):
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


class _DirectionalLayout:
    """The default directional layout"""
    def __init__(self, margins: tuple[int, int, int, int] = (9, 9, 9, 9), spacing: int = 9):
        self._margins: tuple[int, int, int, int] = margins  # left, top, right, bottom
        self._spacing: int = spacing
        self._rect: QRectF = QRectF(0, 0, 0, 0)
        self._children: list[QGraphicsWidget | _ty.Type[_ty.Self] | None] = []
        self._children_sizes: list[int] = []
        self._working_rect = self._rect.marginsRemoved(QMargins(*self._margins))

    @property
    def margins(self) -> tuple[int, int, int, int]:
        """The outer margins of the Directional Layout"""
        return self._margins

    @margins.setter
    def margins(self, new_margins: tuple[int, int, int, int]):
        self._margins = new_margins
        self._working_rect = self._rect.marginsRemoved(QMargins(*self._margins))
        self.reposition()

    @property
    def spacing(self) -> int:
        """The spacing between individual widgets in the layout"""
        return self._spacing

    @spacing.setter
    def spacing(self, new_spacing: int):
        self._spacing = new_spacing
        self.reposition()

    @property
    def rect(self) -> QRectF:
        """The rectangle of the current layout"""
        return self._rect

    def add_widget(self, widget: QGraphicsWidget | None, size: int = 1):
        """Add a widget with a set size"""
        if not isinstance(widget, _DirectionalLayout):
            self._children.append(widget)
            self._children_sizes.append(size)
            self.reposition()
        else:
            raise ValueError(f"Widget must be a widget, not {widget.__class__.__name__}")

    def add_layout(self, layout: _ty.Type[_ty.Self], size: int = 1):
        """Add a layout with a set size"""
        if isinstance(layout, _DirectionalLayout):
            self._children.append(layout)
            self._children_sizes.append(size)
            self.reposition()
        else:
            raise ValueError(f"Layout must be a layout, not {layout.__class__.__name__}")

    def add_stretch(self, size: int = 1):
        """Add an empty widget with a set size"""
        self._children.append(None)
        self._children_sizes.append(size)
        self.reposition()

    def setRect(self, rect: QRectF | tuple[int, int, int, int]) -> None:
        """Resizes the rect of the layout to a new rect and repositions all children within it"""
        self._rect = rect if not isinstance(rect, tuple) else QRectF(*rect)
        self._working_rect = self._rect.marginsRemoved(QMargins(*self._margins))
        self.reposition()

    def reposition(self):
        """Repositions all widgets within the DirectionalLayout"""
        pass

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None):
        """Draws all widgets within the DirectionalLayout"""
        for child in self._children:
            if child is not None:
                child.paint(painter, option)


class VerticalLayout(_DirectionalLayout):
    def reposition(self):
        total_size = sum(self._children_sizes)
        y_offset = self._working_rect.y()
        available_height = self._working_rect.height() - (self._spacing * max(0, len(self._children) - 1))

        for child, size in zip(self._children, self._children_sizes):
            height = (size / total_size) * available_height
            if child:
                child_rect = QRectF(self._working_rect.x(), y_offset, self._working_rect.width(), height)
                child.setRect(child_rect)
            y_offset += height + self._spacing


class HorizontalLayout(_DirectionalLayout):
    def reposition(self):
        total_size = sum(self._children_sizes)
        x_offset = self._working_rect.x()
        available_width = self._working_rect.width() - (self._spacing * max(0, len(self._children) - 1))

        for child, size in zip(self._children, self._children_sizes):
            width = (size / total_size) * available_width
            if child:
                size = min(width, self._working_rect.height())
                missing_x = (width - size) / 2
                missing_y = (self._working_rect.height() - size) / 2
                child_rect = QRectF(x_offset + missing_x, self._working_rect.y() + missing_y, size, size)
                child.setRect(child_rect)
            x_offset += width + self._spacing
