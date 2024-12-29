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


PainterPointT = tuple[tuple[float, float], float]
PainterLineT = tuple[tuple[float, float], tuple[float, float]]
PainterCircleT = tuple[tuple[float, float], float]
PainterArcT = tuple[float, float]
AngleT = float


class PainterColor:
    ColorSpace = QColor.Spec

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


class PainterToStr:
    def __init__(self, diameter_scale: int = 360) -> None:
        self._diameter: int = diameter_scale
        self._radius: float = diameter_scale / 2
        self._curr_style_str: str = ""

    def _polar_to_cartesian(self, angle_deg: float, radius_scalar: float) -> tuple[float, float]:
        """
        Convert polar coordinates to Cartesian.

        :param angle_deg: Angle in degrees
        :param radius_scalar: Relative radius (0 to 1)
        :return: tuple[float, float]
        """
        radius_scaled: float = self._radius * radius_scalar
        angle_rad: float = math.radians(angle_deg)
        x: float = 0 + radius_scaled * math.cos(angle_rad)
        y: float = 0 - radius_scaled * math.sin(angle_rad)
        return x, y

    def line(self, line: PainterLineT, thickness: int = 1, color: PainterColor | None = None) -> None:
        """
        Draw a line from one angle to another within a radius range.

        :param line: tuple[tuple[Starting angle in degrees, Ending angle in degrees], tuple[start_radius_scalar, end_radius_scalar]]
        :param thickness: int
        :param color: PainterColor
        """
        if color is None:
            color = PainterColor(0, 0, 0)

        ((start_deg, end_deg), (start_radius_scalar, end_radius_scalar)) = line
        start_point = self._polar_to_cartesian(start_deg, start_radius_scalar)
        end_point = self._polar_to_cartesian(end_deg, end_radius_scalar)
        self._curr_style_str += f"Line: ({start_point}, {end_point}), {thickness}{color.as_hex()}"

    def arc(self, base_circle: PainterCircleT, arc: PainterArcT, thickness: int = 1, color: PainterColor | None = None) -> None:
        """
        Draw an arc within the circle canvas.

        :param base_circle: tuple[tuple[origin_x, origin_y], radius scalar (0 to 2)]
        :param arc: tuple[Starting angle in degrees, Span angle in degrees]
        :param thickness: int
        :param color: PainterColor
        """
        if color is None:
            color = PainterColor(0, 0, 0)

        ((base_x, base_y), radius_scalar) = base_circle

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
    obj.line(((102, 230), (0.3, 1)), color=PainterColor(245, 22, 1, 0))
    print(obj.clean_out_style_str())
