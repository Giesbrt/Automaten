"""TBA"""

import returns.result as _result

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts

from aplustools.io import ActLogger
import json


class _StateDisplayManager:
    """
    Note: This class is basically pointless, however it is useful to keep because of single responsibility reasons

    """

    def __init__(self, display_name: str,
                 position: _ty.Tuple[float, float],
                 colour_in_hex: str) -> None:
        self.display_name: str = display_name
        self.position: _ty.Tuple[float, float] = position
        self.colour: str = colour_in_hex

        self.connecting_points: _ty.Dict[str, _ty.Tuple[float, float]] = {}
        self._calculate_connecting_points()

    def _calculate_connecting_points(self) -> None:
        n: _ty.Tuple[float, float] = (self.position[0] + self.outer_radius, self.position[1])
        self.connecting_points['n'] = n

        e: _ty.Tuple[float, float] = (self.position[0], self.position[1] + self.outer_radius)
        self.connecting_points['e'] = e

        s: _ty.Tuple[float, float] = (self.position[0] - self.outer_radius, self.position[1])
        self.connecting_points['s'] = s

        w: _ty.Tuple[float, float] = (self.position[0], self.position[1] - self.outer_radius)
        self.connecting_points['w'] = w

    def get_display_name(self) -> str:
        return self.display_name

    def set_display_name(self, new_display_name: str) -> None:
        self.display_name = new_display_name

    def get_position(self) -> _ty.Tuple[float, float]:
        return self.position

    def set_position(self, new_position: _ty.Tuple[float, float]) -> None:
        self.position = new_position

    def get_colour(self) -> str:
        return self.colour

    def set_colour(self, new_colour: str):
        self.colour = new_colour


class _TransitionDisplayManager:
    def __init__(self, display_name: str, colour_in_hex: str) -> None:
        self.display_name: str = display_name
        self.colour: str = colour_in_hex

    def get_display_name(self) -> str:
        return self.display_name

    def set_display_name(self, new_display_name: str) -> None:
        self.display_name = new_display_name

    def get_colour(self) -> str:
        return self.colour

    def set_colour(self, new_colour: str):
        self.colour = new_colour
