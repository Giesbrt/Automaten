"""Abstract api interfaces for everything"""
import math
import threading

from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts


class MainWindowInterface:
    """TBA"""
    icons_folder: str = ""
    popups: list[_ty.Any] = []  # Basically anything that isn't the main window, but a window
    app: QApplication | None = None

    class AppStyle:
        """QApp Styles"""
        Windows11 = 'windows11'
        WindowsVista = 'windowsvista'
        Windows = 'Windows'
        Fusion = 'Fusion'
        Default = None

    def __new__(cls, *args, **kwargs):
        raise Exception("This class can't be initialized; it is just an Interface.")

    def setup_gui(self) -> None:
        """
        Configure the main graphical user interface (GUI) elements of the MV application.

        This method sets up various widgets, layouts, and configurations required for the
        main window interface. It is called after initialization and prepares the interface
        for user interaction.

        Note:
            This method is intended to be overridden by subclasses with application-specific
            GUI components.
        """
        raise NotImplementedError

    def set_window_icon(self, absolute_path_to_icon: str) -> None:
        raise NotImplementedError

    def set_window_title(self, title: str) -> None:
        raise NotImplementedError

    def set_window_geometry(self, x: int, y: int, height: int, width: int) -> None:
        raise NotImplementedError

    def set_window_dimensions(self, height: int, width: int) -> None:
        raise NotImplementedError

    def reload_panels(self) -> None:
        raise NotImplementedError

    def create_popup(self, of_what: QWidget, window_flags: Qt.WindowType) -> int:  # Return the popup-index
        raise NotImplementedError

    def destroy_popup(self, index) -> None:  # Remove popup by index
        raise NotImplementedError

    def set_theme_to_singular(self, theme_str: str, widget_or_window: QWidget) -> None:
        """Applies a theme string to a singular object"""
        raise NotImplementedError

    def set_global_theme(self, theme_str: str, base: str | None = None) -> None:
        raise NotImplementedError

    def start(self) -> None:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError


class BackendInterface:
    """The backend entry point"""
    def run_infinite(self, backend_stop_event: threading.Event) -> None:
        """
        Used to actually start the backend. The gui will launch this in a separate thread.
        """
        ...


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


PainterPointT = tuple[tuple[float, float], float]
PainterCoordT = _PainterCoord
PainterLineT = tuple[PainterCoordT, PainterCoordT]
PainterCircleT = tuple[PainterCoordT, float]
PainterArcT = tuple[float, float]
AngleT = float


class PainterToStr:
    def __init__(self, diameter_scale: float = 360.0) -> None:
        self._diameter: float = diameter_scale
        self._radius: float = diameter_scale / 2
        self._curr_style_str: str = ""

    def coord(self) -> _PainterCoord:
        """Get a coordinate type linked to this PainterToStr instance"""
        return _PainterCoord(self._diameter)

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
