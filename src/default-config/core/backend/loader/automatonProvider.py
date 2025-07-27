from core.backend.abstract.automaton.iautomaton import IAutomaton as _IAutomaton, IAutomaton
from core.backend.data.automatonSettings import AutomatonSettings as _Settings, AutomatonSettings
from core.libs.utils.singleton import singleton

import threading

# Standard typing imports for aps
import typing as _ty
import types as _ts


@singleton
class AutomatonProvider:
    def __init__(self):
        super().__init__()
        self._loaded_automatons: _ty.Dict[
            str, _ty.Dict[_ty.Type[_IAutomaton | _Settings], _IAutomaton | _Settings]] = {}
        self._lock: threading.Lock = threading.Lock()

    @property
    def loaded_automatons(self) -> list[str]:  # _ty.Dict[str, _ty.Dict[_ty.Type[IAutomaton | AutomatonSettings], IAutomaton | AutomatonSettings]]
        with self._lock:
            return list(self._loaded_automatons.keys())

    def get_automaton(self, automaton_name: str) -> _ty.Dict[_ty.Type[IAutomaton | AutomatonSettings], IAutomaton | AutomatonSettings] | None:
        with self._lock:
            if automaton_name.lower() not in self._loaded_automatons:
                return None
            return self._loaded_automatons[automaton_name.lower()]

    def clear(self) -> None:
        with self._lock:
            self._loaded_automatons.clear()

    def register_automatons(self, automatons: _ty.List[_ty.Dict[str, _IAutomaton | _Settings | str]],
                            append: bool = True):
        with self._lock:

            if not append:
                self.clear()

            for automaton in automatons:
                automaton_name: str = automaton["automaton_name"].lower()
                automaton_class: _IAutomaton = automaton["automaton"]
                setting_class: _Settings = automaton["settings"]

                self._loaded_automatons[automaton_name] = {_IAutomaton: automaton_class, _Settings: setting_class}

    def __len__(self) -> int:
        return len(self._loaded_automatons.values())
