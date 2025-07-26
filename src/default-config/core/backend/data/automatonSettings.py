from dataclasses import dataclass, field
from PySide6.QtWidgets import QFrame
from core.backend.default.defaultInputOutputWidget import DefaultInputOutputWidget

# Standard typing imports for aps
import abc as _abc
import typing as _ty


class AutomatonSettings:  # TODO: What about the file names? Like tm.py
    def __init__(
            self,
            module_name: str,
            full_automaton_name: str,
            author: str,
            token_lists: _ty.List[_ty.Tuple[_ty.List[str], bool]],
            transition_description_layout: _ty.List[int],
            default_widget: type[QFrame] = DefaultInputOutputWidget,
            state_types: _ty.List[str] | None = None,
            default_state_type_index: int = 0
    ):
        if state_types is None:
            state_types = ["default", "end"]

        self._module_name: str = module_name
        self._full_automaton_name: str = full_automaton_name
        self._author: str = author
        self._token_lists: _ty.List[_ty.Tuple[_ty.List[str], bool]] = token_lists
        self._transition_description_layout: _ty.List[int] = transition_description_layout
        self._default_widget: type[QFrame] = default_widget
        self._state_types: _ty.List[str] = state_types
        self._default_state_type_index: int = default_state_type_index

    @property
    def module_name(self) -> str:
        return self._module_name

    @module_name.setter
    def module_name(self, value: str) -> None:
        self._module_name = value

    @property
    def default_state_type_index(self) -> int:
        return self._default_state_type_index

    @default_state_type_index.setter
    def default_state_type_index(self, value: int) -> None:
        self._default_state_type_index = value

    @property
    def full_automaton_name(self) -> str:
        return self._full_automaton_name

    @full_automaton_name.setter
    def full_automaton_name(self, value: str) -> None:
        self._full_automaton_name = value

    @property
    def author(self) -> str:
        return self._author

    @author.setter
    def author(self, value: str) -> None:
        self._author = value

    @property
    def token_lists(self) -> _ty.List[_ty.Tuple[_ty.List[str], bool]]:
        return self._token_lists

    @token_lists.setter
    def token_lists(self, value: _ty.List[_ty.Tuple[_ty.List[str], bool]]) -> None:
        self._token_lists = value

    @property
    def transition_description_layout(self) -> _ty.List[int]:
        return self._transition_description_layout

    @transition_description_layout.setter
    def transition_description_layout(self, value: _ty.List[int]) -> None:
        self._transition_description_layout = value

    @property
    def default_widget(self) -> type[QFrame]:
        return self._default_widget

    @default_widget.setter
    def default_widget(self, value: type[QFrame]) -> None:
        self._default_widget = value

    @property
    def state_types(self) -> _ty.List[str]:
        return self._state_types

    @state_types.setter
    def state_types(self, value: _ty.List[str]) -> None:
        self._state_types = value
