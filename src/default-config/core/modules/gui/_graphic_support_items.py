from PySide6.QtCore import Qt, QPointF, QLineF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget, QGraphicsItem, QGraphicsLineItem

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