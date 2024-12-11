"""TBA"""

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts


class PositionManager:
    def __init__(self, display_name: str = "",
                 position: _ty.Tuple[float, float] = (0, 0),
                 colour: _ty.Tuple[int, int, int] = (0, 0, 0),
                 accent_colour: _ty.Tuple[int, int, int] = (255, 0, 0)):
        super().__init__()
        self._display_name: str = display_name
        self._position: _ty.Tuple[float, float] = position
        self._colour: _ty.Tuple[int, int, int] = colour  # rgb- Color
        self._accent_colour: _ty.Tuple[int, int, int] = accent_colour

    def get_display_name(self) -> str:
        return self._display_name

    def set_display_name(self, new_display_name: str) -> None:
        self._display_name = new_display_name

    def get_position(self) -> _ty.Tuple[float, float]:
        return self._position

    def set_position(self, new_position: _ty.Tuple[float, float]) -> None:
        self._position = new_position

    def get_colour(self) -> _ty.Tuple[int, int, int]:
        return self._colour

    def set_colour(self, new_colour: _ty.Tuple[int, int, int]) -> None:
        self._colour = new_colour

    def get_accent_colour(self) -> _ty.Tuple[int, int, int]:
        return self._accent_colour

    def set_accent_colour(self, new_accent_colour: _ty.Tuple[int, int, int]) -> None:
        self._accent_colour = new_accent_colour


