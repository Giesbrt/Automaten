from automaton.base.QAutomatonInputWidget import QAutomatonInputOutput, QAutomatonTokenIO

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts


class Settings(_abc.ABC):
    def __init__(self, module_name: str,
                 full_automaton_name: str,
                 author: str,
                 token_lists: _ty.List[_ty.List[_ty.Any]],
                 customisable_token_list: _ty.List[bool],
                 transition_description_layout: _ty.List[int],
                 state_types_with_design: _ty.Dict[str, str],
                 input_widget: _ty.Type[QAutomatonInputOutput] = QAutomatonTokenIO):
        """ Constructor of the automaton settings file.
        This file serves as a settings-provider to make basic automaton settings (like the transition content)
        :param module_name: The short name of the automaton module (e.g. for a Deterministic Finite Automaton -> dfa)
        :param full_automaton_name: The full name of the automaton (e.g. Deterministic Finite Automaton)
        :param author: The creator of this module
        :param token_lists: The different alphabets the automaton depends on (e.g. a turing machine has following token_lists: The input alphabet like [a, b, c] and the movement alphabet, like [L, R, H]) - If you want, that a specific list has no presets, then just add an empty list
        :param customisable_token_list: This defines which of the previous declared lists can be modified by the user (format: [True, False] if the first list should be changeable, but the second list not)
        :param transition_description_layout: This parameter defines which format the transition description has (format [0, 1] if the transition should have two parameters, and if the first transition attribute should be an element of the first token_list and the second attribute an element out of the second list)
        :param state_types_with_design: The different possible state types (like end or default) are the keys and the value is the design
        :param input_widget: the _ty.Type[QAutomatonInputOutput] which should handle the input of the automaton
        """
        self._module_name: str = module_name
        self._full_automaton_name: str = full_automaton_name
        self._author: str = author
        self._token_lists: _ty.List[_ty.List[_ty.Any]] = token_lists
        self._customisable_token_list: _ty.List[bool] = customisable_token_list
        self._transition_description_layout: _ty.List[int] = transition_description_layout
        self._state_types_with_design: _ty.Dict[str, str] = state_types_with_design
        self._input_widget: _ty.Type[QAutomatonInputOutput] = input_widget

    @property
    def module_name(self) -> str:
        return self._module_name

    @property
    def full_automaton_name(self) -> str:
        return self._full_automaton_name

    @property
    def author(self) -> str:
        return self._author

    @property
    def token_lists(self) -> _ty.List[_ty.List[_ty.Any]]:
        return self._token_lists

    @property
    def customisable_token_list(self) -> _ty.List[bool]:
        return self._customisable_token_list

    @property
    def transition_description_layout(self) -> _ty.List[int]:
        return self._transition_description_layout

    @property
    def state_types_with_design(self) -> _ty.Dict[str, str]:
        return self._state_types_with_design

    @property
    def input_widget(self) -> _ty.Type[QAutomatonInputOutput]:
        return self._input_widget

    def __iter__(self):
        content: _ty.List[_ty.Any] = [self._module_name,
                                      self._full_automaton_name,
                                      self._author,
                                      self._token_lists,
                                      self._customisable_token_list,
                                      self._transition_description_layout,
                                      self._state_types_with_design,
                                      self._input_widget]
        return iter(content)
