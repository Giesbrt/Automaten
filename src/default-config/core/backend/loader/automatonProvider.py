from core.backend.abstract.automaton.iautomaton import IAutomaton as _IAutomaton
from core.backend.abstract.automaton.isettings import IAutomatonSettings as _ISettings
from core.libs.utils.singleton import singleton

import threading

# Standard typing imports for aps
import typing as _ty
import types as _ts


@singleton
class AutomatonProvider:
    def __init__(self):
        super().__init__()
        self._loaded_automatons: _ty.Dict[str, _ty.Dict[_ts.ModuleType, _ts.ModuleType]] = {}
        self._lock: threading.Lock = threading.Lock()

    @property
    def loaded_automatons(self) -> _ty.Dict[str, _ty.Dict[_ts.ModuleType, _ts.ModuleType]]:
        with self._lock:
            return self._loaded_automatons

    def get_automaton(self, automaton_name: str) -> _ty.Dict[_ts.ModuleType, _ts.ModuleType] | None:
        with self._lock:
            if automaton_name.lower() not in self._loaded_automatons:
                return None
            return self._loaded_automatons[automaton_name.lower()]

    def clear(self) -> None:
        with self._lock:
            self._loaded_automatons.clear()

    def register_automatons(self, automatons: _ty.List[_ty.Dict[str, _ts.ModuleType | str]], append: bool=True):
        with self._lock:

            if not append:
                self.clear()

            for automaton in automatons:
                automaton_name: str = automaton["automaton_name"].lower()
                automaton_class: _IAutomaton = automaton["automaton"]
                setting_class: _ISettings = automaton["settings"]

                self._loaded_automatons[automaton_name] = {_IAutomaton: automaton_class, _ISettings: setting_class}





