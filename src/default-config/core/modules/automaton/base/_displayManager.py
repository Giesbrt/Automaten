"""TBA"""

import returns.result as _result

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts

from aplustools.io import ActLogger
import json


# Docs generated with Chat-GPT

class DisplayManager:
    """
    Represents the visual properties for automaton elements such as states and transitions.

    This class allows setting and retrieving visual attributes like position, primary color,
    accent color, and display name. These attributes enable consistent rendering in graphical
    representations of automata.

    Attributes:
        _display_name (str):
            The display name associated with the object.

        _position (_ty.Tuple[float, float]):
            The 2D position coordinates of the object.

        _colour (_ty.Tuple[int, int, int]):
            The primary color in RGB format.

        _accent_colour (_ty.Tuple[int, int, int]):
            The accent color in RGB format, used for highlighting.
    """

    def __init__(self, display_name: str = "",
                 position: _ty.Tuple[float, float] = (0, 0),
                 colour: _ty.Tuple[int, int, int] = (0, 0, 0),
                 accent_colour: _ty.Tuple[int, int, int] = (255, 0, 0)) -> None:
        """
        Initializes a new `PositionManager` object with default or provided values.

        Args:
            display_name (str):
                The name displayed for the object. Default is an empty string.

            position (_ty.Tuple[float, float]):
                The initial 2D position as (x, y). Default is (0, 0).

            colour (_ty.Tuple[int, int, int]):
                The primary color in RGB format. Default is black (0, 0, 0).

            accent_colour (_ty.Tuple[int, int, int]):
                The accent color in RGB format, typically used for highlighting.
                Default is red (255, 0, 0).
        """
        self._display_name: str = display_name
        self._position: _ty.Tuple[float, float] = position
        self._colour: _ty.Tuple[int, int, int] = colour
        self._accent_colour: _ty.Tuple[int, int, int] = accent_colour

    def get_display_name(self) -> str:
        """
        Retrieves the display name of the object.

        Returns:
            str: The display name of the object.
        """
        return self._display_name

    def set_display_name(self, new_display_name: str) -> None:
        """
        Updates the display name of the object.

        Args:
            new_display_name (str):
                The new display name to set for the object.
        """
        self._display_name = new_display_name

    def get_position(self) -> _ty.Tuple[float, float]:
        """
        Retrieves the current position of the object.

        Returns:
            _ty.Tuple[float, float]: The position as (x, y).
        """
        return self._position

    def set_position(self, new_position: _ty.Tuple[float, float]) -> None:
        """
        Updates the position of the object.

        Args:
            new_position (_ty.Tuple[float, float]):
                The new position to set as (x, y).
        """
        self._position = new_position

    def get_colour(self) -> _ty.Tuple[int, int, int]:
        """
        Retrieves the primary color of the object.

        Returns:
            _ty.Tuple[int, int, int]: The primary color in RGB format.
        """
        return self._colour

    def set_colour(self, new_colour: _ty.Tuple[int, int, int]) -> None:
        """
        Updates the primary color of the object.

        Args:
            new_colour (_ty.Tuple[int, int, int]):
                The new primary color in RGB format.
        """
        self._colour = new_colour

    def get_accent_colour(self) -> _ty.Tuple[int, int, int]:
        """
        Retrieves the accent color of the object.

        Returns:
            _ty.Tuple[int, int, int]: The accent color in RGB format.
        """
        return self._accent_colour

    def set_accent_colour(self, new_accent_colour: _ty.Tuple[int, int, int]) -> None:
        """
        Updates the accent color of the object.

        Args:
            new_accent_colour (_ty.Tuple[int, int, int]):
                The new accent color in RGB format.
        """
        self._accent_colour = new_accent_colour
