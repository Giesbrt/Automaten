"""TBA"""
import math
import re

from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtCore import Qt, QRectF, QPointF

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts


class PainterColor:
    ColorSpace = QColor.Spec
    Color = Qt.GlobalColor

    def __init__(self, r: int = 0, g: int = 0, b: int = 0, a: int = 255) -> None:
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
PainterEllipseT = tuple[PainterCoordT, float, float]
PainterArcT = tuple[float, float]


class PainterToStr:
    """Converts Painter commands to a string"""
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

    def line(self, line: PainterLineT, thickness: int = 1, color: PainterColor = PainterColor(a=0)) -> None:
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

    def arc(self, base_ellipse: PainterEllipseT, arc: PainterArcT, fill_color: PainterColor = PainterColor(a=0),
            border_thickness: int = 0, border_color: PainterColor | None = None) -> None:
        """
        Draw an arc within the circle canvas.

        :param base_ellipse: tuple[PainterCoordT, x_radius scalar (0 to 1), y_radius scalar (0 to 1)]
        :param arc: tuple[Starting angle in degrees, Span angle in degrees]
        :param fill_color: PainterColor
        :param border_thickness: int
        :param border_color: PainterColor | None
        """
        if border_color is None:
            border_color = fill_color
        (base_point, x_radius_scalar, y_radius_scalar) = base_ellipse
        (start_deg, end_deg) = arc
        x_radius_scaled = min(1.0, x_radius_scalar) * self._radius
        y_radius_scaled = min(1.0, y_radius_scalar) * self._radius
        self._curr_style_str += (f"Arc: ({base_point}, {x_radius_scaled}, {y_radius_scaled}), ({start_deg}, {end_deg}), "
                                 f"{border_thickness}{border_color.as_hex()}#{fill_color.as_hex()};")

    def ellipse(self, ellipse: PainterEllipseT, fill_color: PainterColor = PainterColor(a=0), border_thickness: int = 0,
                border_color: PainterColor | None = None) -> None:
        """
        Draw an ellipse.

        :param ellipse: tuple[PainterCoordT, x_radius scalar (0 to 1), y_radius scalar (0 to 1)]
        :param fill_color: PainterColor
        :param border_thickness: int
        :param border_color: PainterColor | None
        """
        if border_color is None:
            border_color = fill_color
        (base_point, x_radius_scalar, y_radius_scalar) = ellipse
        x_radius_scaled = min(1.0, x_radius_scalar) * self._radius
        y_radius_scaled = min(1.0, y_radius_scalar) * self._radius
        self._curr_style_str += (f"Ellipse: ({base_point}, {x_radius_scaled}, {y_radius_scaled}), "
                                 f"{border_thickness}{border_color.as_hex()}#{fill_color.as_hex()};")

    def base_rect(self, base_circle: PainterCircleT, top_left_deg: float, bottom_right_deg: float,
                  fill_color: PainterColor = PainterColor(a=0), border_thickness: int = 0,
                  border_color: PainterColor | None = None) -> None:
        """
        Draw a rectangle based on circular references.

        :param base_circle: tuple[PainterCoordT, radius scalar (0 to 1)]
        :param top_left_deg: float, the top left deg for the point of the rectangle
        :param bottom_right_deg: float, the top right deg for the point of the rectangle
        :param fill_color: PainterColor
        :param border_thickness: int
        :param border_color: PainterColor | None
        """
        if border_color is None:
            border_color = fill_color
        (base_point, radius_scalar) = base_circle
        base_x, base_y = base_point.get_point()
        scaled_x = base_x - self._diameter
        scaled_y = base_y - self._diameter
        rel_tl_x, rel_tl_y = self.coord().polar_to_cartesian(top_left_deg, min(1.0, radius_scalar))
        rel_br_x, rel_br_y = self.coord().polar_to_cartesian(bottom_right_deg, min(1.0, radius_scalar))
        self._curr_style_str += (f"Rect: (({rel_tl_x + scaled_x}, {rel_tl_y + scaled_y}), "
                                 f"({rel_br_x + scaled_x}, {rel_br_y + scaled_y})), "
                                 f"{border_thickness}{border_color.as_hex()}#{fill_color.as_hex()};")

    def rect(self, top_left_point: PainterCoordT, bottom_right_point: PainterCoordT,
                  fill_color: PainterColor = PainterColor(a=0), border_thickness: int = 0,
             border_color: PainterColor | None = None) -> None:
        """
        Draw a rectangle.

        :param top_left_point: PainterCoordT, the top left point of the rectangle
        :param bottom_right_point: PainterCoordT, the top left point of the rectangle
        :param fill_color: PainterColor
        :param border_thickness: int
        :param border_color: PainterColor | None
        """
        if border_color is None:
            border_color = fill_color
        self._curr_style_str += (f"Rect: ({top_left_point}, {bottom_right_point}), "
                                 f"{border_thickness}{border_color.as_hex()}#{fill_color.as_hex()};")

    def polygon(self, points: list[PainterCoordT], fill_color: PainterColor = PainterColor(a=0),
                border_thickness: int = 0, border_color: PainterColor | None = None) -> None:
        """
        Draw a polygon.

        :param points: list[PainterCoordT]
        :param fill_color: PainterColor
        :param border_thickness: int
        :param border_color: PainterColor | None
        """
        if border_color is None:
            border_color = fill_color
        self._curr_style_str += (f"Polygon: ({', '.join(str(x) for x in points)}), "
                                 f"{border_thickness}{border_color.as_hex()}#{fill_color.as_hex()};")

    def text(self, start_point: PainterCoordT, text: str, bold: bool = False, italic: bool = False,
             underline: bool = False, strikethrough: bool = False, fill_color: PainterColor = PainterColor(a=0)) -> None:
        """
        Draw text from a specific start point.

        :param start_point: PainterCoordT
        :param text: The text to draw
        :param bold: bool
        :param italic: bool
        :param underline: bool
        :param strikethrough: bool
        :param fill_color: PainterColor
        """
        empty_flag: int = 0
        for i, flag in enumerate((bold, italic, underline, strikethrough)):
            empty_flag |= (1 if flag else 0) << i

        self._curr_style_str += f"Text: {start_point} ,('{text}', {empty_flag}{fill_color.as_hex()})"

    def clean_out_style_str(self) -> str:
        """Returns the current style string and then resets it"""
        result: str = self._curr_style_str
        self._curr_style_str = ""
        return result


class PainterStr:
    """Deserializes a PainterString into something that can be drawn"""
    def __init__(self, painter_str: str) -> None:
        self._painter_str: str = painter_str
        self.painter_cache: list[tuple[QPen, QColor | None, str, tuple[_ty.Any, ...]]] = []
        self._draw(painter_str)

    def _draw(self, command_str: str) -> None:
        commands: list[str] = command_str.strip().split(";")
        for cmd in commands:
            cmd_start: str = cmd.split(":", maxsplit=1)[0]
            match cmd_start:
                case "Line":
                    self._draw_line(cmd)
                case "Arc":
                    self._draw_arc(cmd)
                case "Ellipse":
                    self._draw_ellipse(cmd)
                case "Rect":
                    self._draw_rect(cmd)
                case "Polygon":
                    self._draw_polygon(cmd)
                case "Text":
                    self._draw_text(cmd)
                case "":  # End of string
                    break
                case _:
                    ...  # Error Case. Skip?
                    break
        return None

    def _draw_line(self, cmd_str: str) -> None:
        """Parse and draw line cmd string"""
        match: re.Match[str] | None = re.search(r"Line: \(\(([^,]+), ([^,]+)\), \(([^,]+), ([^,]+)\)\), (\d+)(#[0-9A-Fa-f]+)", cmd_str)
        if match is None:  # Error case
            ...
            return None
        x1, y1, x2, y2, thickness, fill_color = match.groups()
        pen: QPen = QPen(QColor.fromString(fill_color), int(thickness))
        self.painter_cache.append((pen, None, "line", (float(x1), float(y1), float(x2), float(y2))))
        return None

    def _draw_arc(self, cmd_str: str) -> None:
        """Parse and draw arc cmd string"""
        match: re.Match[str] | None = re.search(r"Arc: \(\(([^,]+), ([^,]+)\), ([^,]+), ([^,]+)\), \(([^,]+), ([^,]+)\), (\d+)(#[0-9A-Fa-f]+)#(#[0-9A-Fa-f]+)", cmd_str)
        if match is None:  # Error case
            ...
            return None
        x, y, x_radius, y_radius, start_deg, span_deg, border_thickness, border_color, fill_color = match.groups()
        pen: QPen = QPen(QColor.fromString(border_color), int(border_thickness))
        brush: QColor = QColor.fromString(fill_color)
        self.painter_cache.append((pen, brush, "arc", (float(x), float(y), float(x_radius), float(y_radius), float(start_deg), float(span_deg))))
        return None

    def _draw_ellipse(self, cmd_str: str) -> None:
        """Parse and draw ellipse cmd string"""
        match: re.Match[str] | None = re.search(r"Ellipse: \(\(([^,]+), ([^,]+)\), ([^,]+), ([^,]+)\), (\d+)(#[0-9A-Fa-f]+)#(#[0-9A-Fa-f]+)", cmd_str)
        if match is None:  # Error case
            ...
            return None
        x, y, x_radius, y_radius, border_thickness, border_color, fill_color = match.groups()
        pen: QPen = QPen(QColor.fromString(border_color), int(border_thickness))
        brush: QColor = QColor.fromString(fill_color)
        self.painter_cache.append((pen, brush, "ellipse", (float(x), float(y), float(x_radius), float(y_radius))))
        return None

    def _draw_rect(self, cmd_str: str) -> None:
        """Parse and draw rect cmd string"""
        match: re.Match[str] | None = re.search(r"Rect: \(\(([^,]+), ([^,]+)\), \(([^,]+), ([^,]+)\)\), (\d+)(#[0-9A-Fa-f]+)#(#[0-9A-Fa-f]+)", cmd_str)
        if match is None:  # Error case
            ...
            return None
        x1, y1, x2, y2, border_thickness, border_color, fill_color = match.groups()
        pen: QPen = QPen(QColor.fromString(border_color), int(border_thickness))
        brush: QColor = QColor.fromString(fill_color)
        self.painter_cache.append((pen, brush, "rect", (float(x1), float(y1), float(x2), float(y2))))
        return None

    def _draw_polygon(self, cmd_str: str) -> None:
        """Parse and draw polygon cmd string"""
        match: re.Match[str] | None = re.search(r"Polygon: \((.+)\), (\d+)(#[0-9A-Fa-f]+)#(#[0-9A-Fa-f]+)", cmd_str)
        if match is None:  # Error case
            ...
            return None
        points_str, border_thickness, border_color, fill_color = match.groups()

        points: list[QPointF] = []
        try:
            raw_points: list[str] = points_str.removeprefix("(").removesuffix(")").split("), (")
            for p in raw_points:
                values: list[str] = p.split(", ")
                if len(values) != 2:
                    raise ValueError
                x, y = float(values[0]), float(values[1])
                points.append(QPointF(x, y))
        except ValueError:  # Error case
            ...
            return None
        # polygon: QPainterPath = QPainterPath()
        # if points:
        #     polygon.moveTo(QPointF(points[0][0], points[0][1]))
        #     for x, y in points[1:]:
        #         polygon.lineTo(QPointF(x, y))
        #     polygon.closeSubpath()

        pen: QPen = QPen(QColor.fromString(border_color), int(border_thickness))
        brush: QColor = QColor.fromString(fill_color)
        self.painter_cache.append((pen, brush, "polygon", (points,)))
        return None

    def _draw_text(self, cmd_str: str) -> None:
        """Parse and draw text cmd string"""
        match: re.Match[str] | None = re.search(r"Text: \(([^,]+), ([^,]+)\), \('([^']+)', (\d+)(#[0-9A-Fa-f]+)\)", cmd_str)
        if match is None:  # Error case
            ...
            return None
        x, y, text, style_flags, color = match.groups()
        pen: QPen = QPen(QColor.fromString(color))
        self.painter_cache.append((pen, None, "text", (float(x), float(y), text, int(style_flags))))
        return None


class StrToPainter:
    """Converts a string to Painter commands"""
    def __init__(self, painter: QPainter, center: QPointF, diameter: float, diameter_scale: float = 360.0) -> None:
        self._painter: QPainter = painter
        self._center: QPointF = center
        self._diameter: float = diameter
        self._radius: float = diameter / 2

        self._start_point: QPointF = center - QPointF(self._radius, self._radius)

        self._diameter_scale: float = diameter_scale
        self._magic_scale: float = self._diameter / self._diameter_scale

        # Set clipping path for circular drawing
        clip_path: QPainterPath = QPainterPath()
        clip_path.addEllipse(QRectF(center.x() - self._radius, center.y() - self._radius, diameter, diameter))
        self._painter.setClipPath(clip_path)

    def draw_painter_str(self, painter_str: PainterStr) -> None:
        """Draws a PainterStr using the QPainter"""
        commands: list[tuple[QPen, QColor | None, str, tuple[_ty.Any, ...]]] = painter_str.painter_cache
        for cmd in commands:
            match cmd[2]:
                case "line":
                    self._draw_line(cmd)
                case "arc":
                    self._draw_arc(cmd)
                case "ellipse":
                    self._draw_ellipse(cmd)
                case "rect":
                    self._draw_rect(cmd)
                case "polygon":
                    self._draw_polygon(cmd)
                case "text":
                    self._draw_text(cmd)
                case _:
                    ...  # Error Case. Skip?
                    break
        return None

    def _scale(self, value: float) -> float:
        """Scale measurement based on diameter scale."""
        return value * self._magic_scale

    def _is_of_type(self, value: _ty.Any, expected_type: _ty.Any) -> bool:
        """Recursively checks if a value matches the given type annotation."""
        origin = _ty.get_origin(expected_type)
        args = _ty.get_args(expected_type)
        if origin is None:  # Base case: check direct instance
            return isinstance(value, expected_type)
        if origin is tuple:
            if not isinstance(value, tuple) or len(value) != len(args):
                return False
            return all(self._is_of_type(v, t) for v, t in zip(value, args))
        if origin is _ty.Literal:
            return value in args  # Ensure it's one of the allowed literal values
        # Fallback
        return isinstance(value, expected_type)

    def _draw_line(self, cmd: tuple[QPen, QColor | None, str, tuple[_ty.Any, ...]]) -> None:
        """Draw line cmd"""
        if not self._is_of_type(cmd, tuple[QPen, None, _ty.Literal["line"], tuple[float, float, float, float]]):  # Error case
            ...
            return None
        pen, _, _, (x1, y1, x2, y2) = cmd
        self._painter.setPen(pen)
        self._painter.drawLine(
            QPointF(self._scale(x1), self._scale(y1)) + self._start_point,
            QPointF(self._scale(x2), self._scale(y2)) + self._start_point
        )
        return None

    def _draw_arc(self, cmd: tuple[QPen, QColor | None, str, tuple[_ty.Any, ...]]) -> None:
        """Draw arc cmd"""
        if not self._is_of_type(cmd, tuple[QPen, QColor, _ty.Literal["arc"], tuple[float, float, float, float, float, float]]):  # Error case
            ...
            return None
        pen, brush, _, (x, y, x_radius, y_radius, start_deg, span_deg) = cmd
        rect: QRectF = QRectF(
            self._scale(x - x_radius) + self._start_point.x(),
            self._scale(y - y_radius) + self._start_point.y(),
            self._scale(x_radius * 2),
            self._scale(y_radius * 2)
        )
        self._painter.setPen(pen)
        self._painter.setBrush(brush)
        self._painter.drawArc(rect, int(start_deg * 16), int(span_deg * 16))
        return None

    def _draw_ellipse(self, cmd: tuple[QPen, QColor | None, str, tuple[_ty.Any, ...]]) -> None:
        """Draw ellipse cmd"""
        if not self._is_of_type(cmd, tuple[QPen, QColor, _ty.Literal["ellipse"], tuple[float, float, float, float]]):  # Error case
            ...
            return None
        pen, brush, _, (x, y, x_radius, y_radius) = cmd
        rect: QRectF = QRectF(
            self._scale(x - x_radius) + self._start_point.x(),
            self._scale(y - y_radius) + self._start_point.y(),
            self._scale(x_radius * 2),
            self._scale(y_radius * 2)
        )
        self._painter.setPen(pen)
        self._painter.setBrush(brush)
        self._painter.drawEllipse(rect)
        return None

    def _draw_rect(self, cmd: tuple[QPen, QColor | None, str, tuple[_ty.Any, ...]]) -> None:
        """Draw rect cmd"""
        if not self._is_of_type(cmd, tuple[QPen, QColor, _ty.Literal["rect"], tuple[float, float, float, float]]):  # Error case
            ...
            return None
        pen, brush, _, (x1, y1, x2, y2) = cmd
        rect: QRectF = QRectF(
            self._scale(x1) + self._start_point.x(),
            self._scale(y1) + self._start_point.y(),
            self._scale(x2 - x1),
            self._scale(y2 - y1)
        )
        self._painter.setPen(pen)
        self._painter.setBrush(brush)
        self._painter.drawRect(rect)
        return None

    def _draw_polygon(self, cmd: tuple[QPen, QColor | None, str, tuple[_ty.Any, ...]]) -> None:
        """Draw polygon cmd"""
        if not self._is_of_type(cmd, tuple[QPen, QColor, _ty.Literal["polygon"], tuple[list[QPointF]]]):  # Error case
            ...
            return None
        pen, brush, _, (points,) = cmd

        # Scale the points
        scaled_points: list[QPointF] = []
        for point in points:
            scaled_points.append(
                QPointF(
                    self._scale(point.x()) + self._start_point.x(),
                    self._scale(point.y()) + self._start_point.y()
                )
            )

        self._painter.setPen(pen)
        self._painter.setBrush(brush)
        self._painter.drawPolygon(scaled_points)
        return None

    def _draw_text(self, cmd: tuple[QPen, QColor | None, str, tuple[_ty.Any, ...]]) -> None:
        """Draw text cmd"""
        if not self._is_of_type(cmd, tuple[QPen, None, _ty.Literal["text"], tuple[float, float, str, int]]):  # Error case
            ...
            return None
        pen, _, _, (x, y, text, style_flags) = cmd
        point: QPointF = QPointF(
            self._scale(x) + self._start_point.x(),
            self._scale(y) + self._start_point.y()
        )
        self._painter.drawText(point, text)
        return None


if __name__ == "__main__":
    obj = PainterToStr()
    obj.line((obj.coord().load_from_polar(102, 0.3), obj.coord().load_from_polar(230, 1.0)),
             color=PainterColor(245, 22, 1, 0))
    obj.arc((obj.coord().load_from_cartesian(180, 180), 0.9, 0.9), (0, 360), PainterColor(0, 255, 0), 2, PainterColor(0, 255, 0))
    obj.ellipse((obj.coord().load_from_cartesian(180, 180), 0.9, 0.9), PainterColor(255, 0, 0))
    print(obj.clean_out_style_str())
    obj.base_rect((obj.coord().load_from_cartesian(180, 180), 1.0), 80, 270)
    obj.rect(obj.coord().load_from_polar(80, 1.0), obj.coord().load_from_polar(270, 1.0))
    print(obj.clean_out_style_str())
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
    smaller_radius: float = 0.85
    painter.ellipse((center, 1.0, 1.0), PainterColor(255, 255, 255), 6, PainterColor(0, 0, 0))
    painter.ellipse((center, smaller_radius, smaller_radius), PainterColor(a=0), 2, PainterColor(0, 0, 0))
    print(f"Endzustand (Smaller Circle) design: {painter.clean_out_style_str()}")
