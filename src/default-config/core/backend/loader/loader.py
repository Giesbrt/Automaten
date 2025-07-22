import importlib
import inspect
import json
import os

from pathlib import Path as _Path
from pprint import pprint
from time import time, perf_counter

# from dotenv import load_dotenv

from core.backend.abstract.automaton.iautomaton import IAutomaton as _IAutomaton
from core.backend.data.automatonSettings import AutomatonSettings as _Settings

from dancer.io import ActLogger

# Standard typing imports for aps
import typing as _ty
import types as _ts


class Loader:

    def __init__(self, base_path: _Path):
        self._base_path: _Path = base_path
        self._implementation_path: _Path = base_path / "extensions"  # TODO set path
        self._cache_path: _Path = self._base_path / "cache"  # TODO set path
        self._cache_file_name: str = "cache.json"

        self._previous_cache_data: _ty.Dict[str, _ty.Dict[str, _ty.Any]] = self._load_previous_caches()

        self._required_abstract_class_implementations: _ty.Dict[_ts.ModuleType, _ts.ModuleType | None] = {
            _IAutomaton: None}

    def _load_previous_caches(self) -> _ty.Dict[str, _ty.Dict[str, _ty.Any]]:
        full_cache_path: str = os.path.join(self._cache_path, self._cache_file_name)

        if not os.path.isfile(full_cache_path):
            return {}

        with open(full_cache_path, "r") as file:
            return dict(json.load(file))

    def _to_cache(self, file_name: str, working: bool, description: str | None = None) -> None:
        full_cache_path: str = os.path.join(self._cache_path, self._cache_file_name)

        self._previous_cache_data[file_name] = {"working": working, "description": description,
                                                "timestamp": time()}
        ActLogger().info(f"[{file_name}:{'success' if working else 'failed'}] {description}")

        json_parsed = json.dumps(self._previous_cache_data, indent=4)

        # Create The Parent directory
        dir_path = os.path.dirname(full_cache_path)
        os.makedirs(dir_path, exist_ok=True)

        with open(full_cache_path, "w") as file:
            file.write(json_parsed)

    def load(self) -> tuple[_ty.List[_ty.Dict[str, _ts.ModuleType | str]]]:
        implementation_files = [file for file in os.listdir(self._implementation_path) if
                                os.path.isfile(os.path.join(self._implementation_path, file)) and
                                os.path.splitext(file)[1].lower() == ".py"]

        loaded_modules: _ty.List[_ty.Dict[str, _ts.ModuleType | str] | None] = []
        for file_name in implementation_files:
            full_file_path: str = os.path.join(self._implementation_path, file_name)
            impl_last_changed: float = os.path.getmtime(full_file_path)

            skip_checks: bool = False
            if (file_name in self._previous_cache_data and
                    # Implementation has not changed
                    impl_last_changed < self._previous_cache_data[file_name]["timestamp"] and
                    self._previous_cache_data[file_name]["working"]):
                skip_checks = True

            module_data: _ty.Dict[str, _ts.ModuleType | str] | None = self._load_file(full_file_path, file_name,
                                                                                      skip_checks)

            if module_data is not None:
                loaded_modules.append(module_data)

        return (loaded_modules,)

    def _check_for_classes(self, classes_in_module: _ty.List[_ty.Tuple[str, _ts.ModuleType]]) -> _ty.Dict[
                                                                                                     _ts.ModuleType, \
                                                                                                             _ts.ModuleType | None] | \
                                                                                                 _ty.List[str]:
        required_abstract_class_implementations: _ty.Dict[
            _ts.ModuleType, _ts.ModuleType | None] = self._required_abstract_class_implementations.copy()
        # All Classes Implemented?
        for (name, cls) in classes_in_module:
            for abstract_class in required_abstract_class_implementations:
                if issubclass(cls, abstract_class) and \
                        abstract_class in required_abstract_class_implementations and \
                        not required_abstract_class_implementations[abstract_class]:
                    required_abstract_class_implementations[abstract_class] = cls

        if not (all(required_abstract_class_implementations.values()) or
                len(required_abstract_class_implementations) == 0):
            return [parent.__name__ for parent in required_abstract_class_implementations if
                    not required_abstract_class_implementations[parent]]

        return required_abstract_class_implementations

    @staticmethod
    def _check_for_abstract_methods(module_methods: _ty.List[_ty.Tuple[str, _ts.FunctionType]],
                                    parent_class: _ts.ModuleType) -> _ty.List[str]:

        missing_methods: _ty.List[str] = []
        for abstract_method in parent_class.__abstractmethods__:
            if abstract_method in list(map(lambda x: x[0], module_methods)):
                continue
            missing_methods.append(abstract_method)

        return missing_methods

    @staticmethod
    def _check_for_method_body(module_methods: _ty.List[_ty.Tuple[str, _ts.FunctionType | str]]) -> _ty.List[str]:
        unimplemented_methods: _ty.List[str] = []
        BLACKLISTED_FUNCTION_BODYS: _ty.List[str] = ["pass", "raise NotImplementedError"]

        for (name, function) in module_methods:
            # function source code without the signature
            source = inspect.getsource(function).split("\n")
            source_without_signature = '\n'.join(source[1:]).strip()

            if not source_without_signature or source_without_signature in BLACKLISTED_FUNCTION_BODYS:
                unimplemented_methods.append(name)

        return unimplemented_methods

    def _load_file(self, file_path: str, file_name: str, skip_checks: bool = False) -> _ty.Dict[
                                                                                           str, _ts.ModuleType | str] | None:
        relative_path: str = os.path.relpath(file_path, self._base_path)
        split_rel_path: str = os.path.splitext(relative_path)[0]
        module_path: str = split_rel_path.replace(os.path.sep, ".")

        module: _ts.ModuleType = importlib.import_module(module_path)

        all_module_classes: _ty.List[_ty.Tuple[str, _ts.ModuleType]] = inspect.getmembers(module, inspect.isclass)
        module_classes: _ty.List[_ty.Tuple[str, _ts.ModuleType]] = [(name, cls) for name, cls in all_module_classes if
                                                                    cls.__module__ == module.__name__]

        # Check If All Classes Are Present
        required_abstract_class_implementations: _ty.Dict[_ts.ModuleType, _ts.ModuleType | None] = \
            self._check_for_classes(module_classes)

        if type(required_abstract_class_implementations) is list and not skip_checks:
            self._to_cache(file_name, False, "[N/A] Not all Classes Implemented")
            #  print("[N/A] Not all Classes Implemented")
            return None

        # Automaton Name
        automaton_settings_instance: _Settings | None = None
        try:
            main_class: _IAutomaton = required_abstract_class_implementations[_IAutomaton]()
            automaton_settings_instance = main_class.get_automaton_settings()
            automaton_name: str = automaton_settings_instance.module_name
        except TypeError:
            #  ("[N/A] Error occurred whilst fetching automaton name")
            self._to_cache(file_name, False, "[N/A] Error occurred whilst fetching automaton name")
            return None
        finally:
            if not automaton_settings_instance:
                self._to_cache(file_name, False, "[N/A] Error occurred whilst fetching automaton name")
                return None

        # Abstract Method Checks
        for parent_class in required_abstract_class_implementations:

            class_in_module: _ts.ModuleType = required_abstract_class_implementations[parent_class]

            all_module_methods: _ty.List[_ty.Tuple[str, _ts.FunctionType]] = inspect.getmembers(class_in_module,
                                                                                                inspect.isfunction)

            module_methods: _ty.List[_ty.Tuple[str, _ts.FunctionType]] = [(function_name, function) for
                                                                          function_name, function in all_module_methods
                                                                          if
                                                                          function.__module__ == class_in_module.__module__]

            all_native_module_methods: _ty.List[_ty.Tuple[str, _ts.FunctionType]] = [(function_name, function) for
                                                                                     function_name, function in
                                                                                     module_methods if
                                                                                     not str(
                                                                                         function.__name__).startswith(
                                                                                         "__")]

            if not skip_checks:
                # Check If All Abstract Methods are Present
                missing_abstract_methods: _ty.List[str] = self._check_for_abstract_methods(all_native_module_methods,
                                                                                           parent_class)
                if missing_abstract_methods:
                    #  print(f"[{automaton_name}] Not all Methods Present", missing_abstract_methods)
                    self._to_cache(file_name, False,
                                   f"[{automaton_name}] Not all Methods Present {missing_abstract_methods}")
                    return None

                # Check If Methods Have A Body
                unimplemented_methods: _ty.List[str] = self._check_for_method_body(all_native_module_methods)
                if unimplemented_methods:
                    #  print(f"[{automaton_name}] Not all Methods Implemented", unimplemented_methods)
                    self._to_cache(file_name, False,
                                   f"[{automaton_name}] Not all Methods Implemented {unimplemented_methods}")
                    return None

        self._to_cache(file_name, True, "All Checks passed" if not skip_checks else f"Skipped Checks due to an "
                                                                                    f"unchanged file")
        return {"automaton_name": automaton_name,
                "automaton": required_abstract_class_implementations[_IAutomaton],
                "settings": automaton_settings_instance}


if __name__ == '__main__':
    load_dotenv(r"../../.env")

    start = perf_counter()
    loaded = Loader(_Path(os.getenv("BASE_PATH"))).load()
    end = perf_counter()

    pprint(loaded)
    print(f"Loaded in {(end - start) * 1000}ms")
