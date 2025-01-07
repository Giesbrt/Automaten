"""TBA"""
import math

from PySide6.QtWidgets import QWidget, QApplication, QMainWindow
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts


class PainterColor:
    ColorSpace = QColor.Spec
    Color = Qt.GlobalColor

    def __init__(self, r: int, g: int, b: int, a: int = 255) -> None:
        """
        Initialize the PainterColor with a color representation.

        :param r: R component of the color (0-255)
        :param g: G component of the color (0-255)
        :param b: B component of the color (0-255)
        :param a: A component of the color (0-255)
        """
        self._color_space: QColor.Spec = QColor.Spec.Rgb
        self._qcolor = QColor.fromRgb(r, g, b, a)

    def get_color_space(self) -> ColorSpace:
        return self._color_space

    @classmethod
    def from_qcolor(cls, qcolor: QColor) -> _ty.Self:
        inst = cls(0, 0, 0, 0)
        inst._qcolor = qcolor
        inst._color_space = qcolor.spec()
        return inst

    @classmethod
    def from_color(cls, global_color: Qt.GlobalColor) -> _ty.Self:
        return cls.from_qcolor(QColor(global_color))

    @classmethod
    def from_string(cls, color_str: str) -> _ty.Self:
        color = QColor.fromString(color_str)
        return cls.from_qcolor(color)

    def convert_to(self, color_space: ColorSpace = ColorSpace.Rgb) -> _ty.Self:
        return self.from_qcolor(self._qcolor.convertTo(color_space))

    def as_rgb(self) -> tuple[int, int, int]:
        """
        Return the color as an RGB tuple in the given or current color space.

        :return: tuple[R, G, B]
        """
        return self.as_rgba()[:3]

    def as_rgba(self) -> tuple[int, int, int, int]:
        """
        Return the color as an RGBA tuple in the given or current color space.

        :return: tuple[R, G, B, A]
        """
        color = self._qcolor.convertTo(QColor.Spec.Rgb)
        return color.red(), color.green(), color.blue(), color.alpha()

    def as_hex(self) -> str:
        """
        Return the color as a hexadecimal string in the given or current color space.

        :return: Hexadecimal string
        """
        color = self._qcolor.convertTo(QColor.Spec.Rgb)
        return color.name(QColor.NameFormat.HexArgb if color.alpha() < 255 else QColor.NameFormat.HexRgb)

    def as_css_rgb(self) -> str:
        """
        Return the color as a CSS rgb() string in the given or current color space.

        :return: CSS rgb() string
        """
        r, g, b = self.as_rgb()
        return f"rgb({r}, {g}, {b})"

    def as_css_rgba(self) -> str:
        """
        Return the color as a CSS rgba() string in the given or current color space.

        :return: CSS rgba() string
        """
        r, g, b, a = self.as_rgba()
        alpha = a / 255
        return f"rgba({r}, {g}, {b}, {alpha:.2f})"

    def __repr__(self) -> str:
        return f"PainterColor({self._qcolor}, {self._color_space})"


class _PainterCoord:
    """Represents a coordinate that can be loaded from multiple different coordinate representations"""
    def __init__(self, diameter_scale: float) -> None:
        self._diameter: float = diameter_scale
        self._radius: float = diameter_scale / 2
        self._x: float = 0
        self._y: float = 0

    def get_point(self) -> tuple[float, float]:
        """Returns the calculated absolute point"""
        return self._x, self._y

    def relative_to_absolute(self, rel_x: float, rel_y: float) -> tuple[float, float]:
        """
        Convert relative Cartesian to Cartesian, starting at the top left.

        :param rel_x: Relative x
        :param rel_y: Relative y
        :return: tuple[float, float]
        """
        return rel_x + self._radius, rel_y + self._radius

    def polar_to_cartesian(self, angle_deg: float, radius_scalar: float) -> tuple[float, float]:
        """
        Convert polar coordinates to Cartesian, starting at the top left.

        :param angle_deg: Angle in degrees
        :param radius_scalar: Relative radius (0 to 1)
        :return: tuple[float, float]
        """
        radius_scaled: float = self._radius * radius_scalar
        angle_rad: float = math.radians(angle_deg)
        x: float = 0 + radius_scaled * math.cos(angle_rad)
        y: float = 0 - radius_scaled * math.sin(angle_rad)
        return self.relative_to_absolute(x, y)

    def load_from_cartesian(self, rel_x: float, rel_y: float) -> _ty.Self:
        """
        Loads internal absolute x and y from relative coordinates from the center of the circle.
        :param rel_x: Relative x-coordinate
        :param rel_y: Relative y-coordinate
        """
        self._x, self._y = self.relative_to_absolute(rel_x, rel_y)
        return self

    def load_from_polar(self, angel_deg: float, radius_scalar: float) -> _ty.Self:
        """
        Loads internal absolute x and y from polar coordinates.
        :param angel_deg: Angle in degrees (counter-clock wise)
        :param radius_scalar: Radius scalar (0-1)
        """
        self._x, self._y = self.polar_to_cartesian(angel_deg, min(1.0, radius_scalar))
        return self

    def __str__(self) -> str:
        return f"({self._x}, {self._y})"


PainterCoordT = _PainterCoord
PainterLineT = tuple[PainterCoordT, PainterCoordT]
PainterCircleT = tuple[PainterCoordT, float]
PainterArcT = tuple[float, float]


class PainterToStr:
    """Converts Painter commands to a string that can be shared between threads"""
    def __init__(self, diameter_scale: float = 360.0) -> None:
        self._diameter: float = diameter_scale
        self._radius: float = diameter_scale / 2
        self._curr_style_str: str = ""

    def coord(self) -> _PainterCoord:
        """Get a coordinate type linked to this PainterToStr instance"""
        return _PainterCoord(self._diameter)

    def radius(self) -> float:
        """TBA"""
        return self._radius

    def line(self, line: PainterLineT, thickness: int = 1, color: PainterColor | None = None) -> None:
        """
        Draw a line from one angle to another within a radius range.

        :param line: tuple[PainterCoordT, PainterCoordT]
        :param thickness: int
        :param color: PainterColor
        """
        if color is None:
            color = PainterColor(0, 0, 0)

        (start_point, end_point) = line
        self._curr_style_str += f"Line: ({start_point}, {end_point}), {thickness}{color.as_hex()};"

    def arc(self, base_circle: PainterCircleT, arc: PainterArcT, thickness: int = 1, color: PainterColor | None = None
            ) -> None:
        """
        Draw an arc within the circle canvas.

        :param base_circle: tuple[PainterCoordT, radius scalar (0 to 1)]
        :param arc: tuple[Starting angle in degrees, Span angle in degrees]
        :param thickness: int
        :param color: PainterColor
        """
        if color is None:
            color = PainterColor(0, 0, 0)

        (base_point, radius_scalar) = base_circle
        (start_deg, end_deg) = arc
        radius_scaled = min(1.0, radius_scalar) * self._radius
        self._curr_style_str += (f"Arc: ({base_point}, {radius_scaled}), ({start_deg}, {end_deg}), "
                                 f"{thickness}#{color.as_hex()};")

    def circle(self, circle: PainterCircleT, thickness: int = 1, color: PainterColor | None = None) -> None:
        """
        Draw a circle.

        :param circle: tuple[PainterCoordT, radius scalar (0 to 1)]
        :param thickness: int
        :param color: PainterColor
        """
        if color is None:
            color = PainterColor(0, 0, 0)

        (base_point, radius_scalar) = circle
        radius_scaled = min(1.0, radius_scalar) * self._radius
        self._curr_style_str += f"Circle: ({base_point}, {radius_scaled}), {thickness}#{color.as_hex()};"

    def base_rect(self, base_circle: PainterCircleT, top_left_deg: float, bottom_right_deg: float,
                  thickness: int = 1, color: PainterColor | None = None) -> None:
        """
        Draw a rectangle based on circular references.

        :param base_circle: tuple[PainterCoordT, radius scalar (0 to 1)]
        :param top_left_deg: float, the top left deg for the point of the rectangle
        :param bottom_right_deg: float, the top right deg for the point of the rectangle
        :param thickness: int
        :param color: PainterColor
        """
        if color is None:
            color = PainterColor(0, 0, 0)

        (base_point, radius_scalar) = base_circle
        base_x, base_y = base_point.get_point()
        scaled_x = base_x - self._diameter
        scaled_y = base_y - self._diameter
        rel_tl_x, rel_tl_y = self.coord().polar_to_cartesian(top_left_deg, min(1.0, radius_scalar))
        rel_br_x, rel_br_y = self.coord().polar_to_cartesian(bottom_right_deg, min(1.0, radius_scalar))
        self._curr_style_str += f"Rect: (({rel_tl_x + scaled_x}, {rel_tl_y + scaled_y}), ({rel_br_x + scaled_x}, {rel_br_y + scaled_y})), {thickness}#{color.as_hex()};"

    def rect(self, top_left_point: PainterCoordT, bottom_right_point: PainterCoordT,
             thickness: int = 1, color: PainterColor | None = None) -> None:
        """
        Draw a rectangle based on circular references.

        :param top_left_point: PainterCoordT, the top left point of the rectangle
        :param bottom_right_point: PainterCoordT, the top left point of the rectangle
        :param thickness: int
        :param color: PainterColor
        """
        if color is None:
            color = PainterColor(0, 0, 0)

        self._curr_style_str += f"Rect: ({top_left_point}, {bottom_right_point}), {thickness}#{color.as_hex()};"

    def base_polygon(self, base_circle: PainterCircleT, degs: list[float], thickness: int = 1,
                     color: PainterColor | None = None) -> None:
        """
        Draw a polygon using polar coordinates.

        :param base_circle: tuple[PainterCoordT, radius scalar (0 to 1)]
        :params degs: list[float], the degs for the points of the polygon
        :param thickness: int
        :param color: PainterColor
        """
        if color is None:
            color = PainterColor(0, 0, 0)

        (base_point, radius_scalar) = base_circle
        base_x, base_y = base_point.get_point()
        scaled_x = base_x - self._diameter
        scaled_y = base_y - self._diameter

        points: list[tuple[float, float]] = []
        for deg in degs:
            rel_x, rel_y = self.coord().polar_to_cartesian(deg, min(1.0, radius_scalar))
            points.append((rel_x + scaled_x, rel_y + scaled_y))
        self._curr_style_str += f"Polygon: ({', '.join(str(x) for x in points)}), {thickness}#{color.as_hex()};"

    def polygon(self, points: list[PainterCoordT], thickness: int = 1, color: PainterColor | None = None) -> None:
        """
        Draw a polygon using polar coordinates.

        :param points: list[PainterCoordT]
        :param thickness: int
        :param color: PainterColor
        """
        if color is None:
            color = PainterColor(0, 0, 0)

        self._curr_style_str += f"Polygon: ({', '.join(str(x) for x in points)}), {thickness}#{color.as_hex()};"

    def text(self, start_point: PainterCoordT, text: str, bold: bool = False, italic: bool = False,
             underline: bool = False, strikethrough: bool = False, color: PainterColor | None = None) -> None:
        """
        Draw text from a specific start point.

        :param start_point: PainterCoordT
        :param text: The text to draw
        :param bold: bool
        :param italic: bool
        :param underline: bool
        :param strikethrough: bool
        :param color: PainterColor
        """
        if color is None:
            color = PainterColor(0, 0, 0)

        empty_flag: int = 0
        for i, flag in enumerate((bold, italic, underline, strikethrough)):
            empty_flag |= (1 if flag else 0) << i

        self._curr_style_str += f"Text: {start_point} ,('{text}', {empty_flag}#{color.as_hex()})"

    def clean_out_style_str(self) -> str:
        """Returns the current style string and then resets it"""
        result: str = self._curr_style_str
        self._curr_style_str = ""
        return result


class StrToPainter:
    def __init__(self, painter, center, diameter):
        self.painter = painter
        self.center = center
        self.diameter = diameter
        self.radius = diameter / 2

        # Set clipping path for circular drawing
        clip_path = QPainterPath()
        clip_path.addEllipse(QRectF(center.x() - self.radius, center.y() - self.radius, diameter, diameter))
        self.painter.setClipPath(clip_path)

    def polar_to_cartesian(self, angle_deg, radius):
        """
        Convert polar coordinates to Cartesian.

        :param angle_deg: Angle in degrees
        :param radius: Radius relative to the diameter (0 to 1)
        :return: QPointF
        """
        radius_scaled = radius * self.radius
        angle_rad = math.radians(angle_deg)
        x = self.center.x() + radius_scaled * math.cos(angle_rad)
        y = self.center.y() - radius_scaled * math.sin(angle_rad)
        return QPointF(x, y)

    def line(self, start_angle, end_angle, radius_range):
        """
        Draw a line from one angle to another within a radius range.

        :param start_angle: Starting angle in degrees
        :param end_angle: Ending angle in degrees
        :param radius_range: Tuple (start_radius, end_radius) where values are relative to diameter (0 to 1)
        """
        start_radius, end_radius = radius_range
        start_point = self.polar_to_cartesian(start_angle, start_radius)
        end_point = self.polar_to_cartesian(end_angle, end_radius)

        self.painter.drawLine(start_point, end_point)

    def arc(self, start_angle, span_angle, radius):
        """
        Draw an arc within the circle canvas.

        :param start_angle: Starting angle in degrees
        :param span_angle: Span angle in degrees
        :param radius: Radius relative to the diameter (0 to 1)
        """
        radius_scaled = radius * self.radius
        rect = QRectF(
            self.center.x() - radius_scaled, self.center.y() - radius_scaled,
            radius_scaled * 2, radius_scaled * 2
        )
        self.painter.drawArc(rect, int(start_angle * 16), int(span_angle * 16))

    def circle(self, radius, brush=None, pen=None):
        """
        Draw a circle.

        :param radius: Radius relative to the diameter (0 to 1)
        :param brush: Optional QBrush for filling the circle
        :param pen: Optional QPen for the circle outline
        """
        radius_scaled = radius * self.radius
        if brush:
            self.painter.setBrush(brush)
        if pen:
            self.painter.setPen(pen)

        rect = QRectF(
            self.center.x() - radius_scaled, self.center.y() - radius_scaled,
            radius_scaled * 2, radius_scaled * 2
        )
        self.painter.drawEllipse(rect)

    def rectangle(self, start_angle, end_angle, radius_range):
        """
        Draw a rectangle based on circular references.

        :param start_angle: Starting angle in degrees
        :param end_angle: Ending angle in degrees
        :param radius_range: Tuple (start_radius, end_radius) where values are relative to diameter (0 to 1)
        """
        start_radius, end_radius = radius_range
        top_left = self.polar_to_cartesian(start_angle, start_radius)
        bottom_right = self.polar_to_cartesian(end_angle, end_radius)

        rect = QRectF(top_left, bottom_right)
        self.painter.drawRect(rect)

    def polygon(self, points):
        """
        Draw a polygon using polar coordinates.

        :param points: List of tuples [(angle1, radius1), (angle2, radius2), ...],
                       where angles are in degrees and radii are relative to the diameter (0 to 1).
        """
        polygon = QPainterPath()

        if points:
            # Convert the first point and move to it
            first_point = self.polar_to_cartesian(points[0][0], points[0][1])
            polygon.moveTo(first_point)

            # Convert and draw lines to subsequent points
            for angle, radius in points[1:]:
                point = self.polar_to_cartesian(angle, radius)
                polygon.lineTo(point)

            # Close the polygon
            polygon.closeSubpath()

        self.painter.drawPath(polygon)

    def text(self, angle, radius, text):
        """
        Draw text at a specific angle and radius.

        :param angle: Angle in degrees
        :param radius: Radius relative to the diameter (0 to 1)
        :param text: The text to draw
        """
        position = self.polar_to_cartesian(angle, radius)
        self.painter.drawText(position, text)

    def scale(self, factor):
        """
        Scale the canvas by a factor.

        :param factor: Scaling factor
        """
        self.diameter *= factor
        self.radius = self.diameter / 2

    def set_pen(self, pen):
        """
        Set the pen for drawing.

        :param pen: QPen object
        """
        self.painter.setPen(pen)

    def set_brush(self, brush):
        """
        Set the brush for filling shapes.

        :param brush: QBrush object
        """
        self.painter.setBrush(brush)


if __name__ == "__main__":
    obj = PainterToStr()
    obj.line((obj.coord().load_from_polar(102, 0.3), obj.coord().load_from_polar(230, 1.0)),
             color=PainterColor(245, 22, 1, 0))
    obj.arc((obj.coord().load_from_cartesian(180, 180), 0.9), (0, 360), 2, PainterColor(0, 255, 0))
    obj.circle((obj.coord().load_from_cartesian(180, 180), 0.9), 3, PainterColor(255, 0, 0))
    print(obj.clean_out_style_str())
    obj.base_rect((obj.coord().load_from_cartesian(180, 180), 1.0), 80, 270)
    obj.rect(obj.coord().load_from_polar(80, 1.0), obj.coord().load_from_polar(270, 1.0))
    print(obj.clean_out_style_str())
    obj.base_polygon((obj.coord().load_from_cartesian(180, 180), 1.0), [80.0, 270.0])
    obj.polygon([obj.coord().load_from_polar(80, 1.0), obj.coord().load_from_polar(270, 1.0)])
    print(obj.clean_out_style_str())
    obj.text(obj.coord().load_from_polar(80, 0.5), "MyText", True, False, True, True,
             PainterColor.from_color(PainterColor.Color.white))
    print(obj.clean_out_style_str())

    # Demonstration
    painter = PainterToStr(diameter_scale=360.0)

    center: PainterCoordT = painter.coord().load_from_cartesian(0, 0)
    top: PainterCoordT = painter.coord().load_from_cartesian(0, -painter.radius())
    bottom: PainterCoordT = painter.coord().load_from_cartesian(0, painter.radius())
    left: PainterCoordT = painter.coord().load_from_cartesian(-painter.radius(), 0)
    right: PainterCoordT = painter.coord().load_from_cartesian(painter.radius(), 0)

    # Polar coordinates specify a point's location using:
    #  radius: Distance from the origin.
    #  angle_deg: Angle measured from the positive x-axis (0°) counterclockwise.
    #      ____
    #    /      \
    #    |      | <--- This is 0 degrees, from there on if you count 90 in the counter clockwise dir you're at the top
    #    \_____/
    center_2: PainterCoordT = painter.coord().load_from_polar(0, 0)
    top_2: PainterCoordT = painter.coord().load_from_polar(90, 1.0)
    bottom_2: PainterCoordT = painter.coord().load_from_polar(270, 1.0)
    left_2: PainterCoordT = painter.coord().load_from_polar(180, 1.0)
    right_2: PainterCoordT = painter.coord().load_from_polar(0, 1.0)

    print(f"{center} || {center_2}\n{top} || {top_2}\n{bottom} || {bottom_2}\n{left} || {left_2}\n{right} || {right_2}")

    # Red cross
    painter.line((top, bottom), thickness=10, color=PainterColor.from_color(PainterColor.Color.red))
    painter.line((left, right), thickness=10, color=PainterColor.from_color(PainterColor.Color.red))

    # Output result
    print(f"Fehler zustand design (red cross): {painter.clean_out_style_str()}")

    # Draw Circle
    smaller_radius: float = 0.9
    painter.circle((center, smaller_radius), thickness=2, color=PainterColor(0, 0, 0))
    print(f"Endzustand (Smaller Circle) design: {painter.clean_out_style_str()}")
