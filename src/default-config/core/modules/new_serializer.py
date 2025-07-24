"""Serialize an AutomatonData class to a file"""
# Build-in
import contextlib
import threading
import hashlib
import json
import re
import os

# Internal
from core.backend.loader.automatonProvider import AutomatonProvider
from core.backend.data.simulation import Simulation
from core.backend.default.defaultTape import DefaultTape
from core.backend.packets.simulationPackets import SimulationStartPacket, SimulationDataPacket
from core.backend.data.transition import Transition
from core.backend.packets.packetManager import PacketManager

from core.backend.abstract.automaton.iautomaton import IAutomaton
from core.backend.data.automatonSettings import AutomatonSettings

# Third-party
from PySide6.QtGui import QColor
from dancer.data import beautify_json
from dancer.system import os_open
import yaml

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

from zope.interface.adapter import VerifyingBase


def _strip_python_code(source: str) -> str:
    # Remove docstrings (triple-quoted strings that appear as docstrings)
    source = re.sub(r'(?s)"""(.*?)"""', '', source)  # triple double quotes
    source = re.sub(r"(?s)'''(.*?)'''", '', source)  # triple single quotes

    # Remove single-line comments
    source = re.sub(r'#.*', '', source)

    # Optionally: remove excessive blank lines
    source = re.sub(r'\n\s*\n', '\n', source)

    return source.strip()


class SerializationModule(_ty.Protocol):
    def hook(self, data: dict) -> dict: ...


class GUIDataModule(SerializationModule):
    def __init__(self, state_extra_info: dict[str, dict[str, _ty.Any]],
                 transition_extra_info: dict[tuple[str, str], _ty.Any],
                 styling_extra_data: dict[str, _ty.Any]) -> None:
        self._state_extra_info: dict[str, dict[str, _ty.Any]] = state_extra_info
        self._transition_extra_info: dict[tuple[str, str], _ty.Any] = transition_extra_info
        self._styling_extra_data: dict[str, _ty.Any] = styling_extra_data

    def hook(self, data: dict) -> dict:
        states: list[dict] = data["data"]["content"]
        transitions: list[dict] = data["data"]["content_transitions"]
        for state in states:
            state_extra_info: dict[str, _ty.Any] = state["extra_info"]
            state_extra_info.update(self._state_extra_info[state["name"]])
        for transition in transitions:
            from_state: str = states[transition["from_idx"]]["name"]
            to_state: str = states[transition["to_idx"]]["name"]
            transition_extra_info: dict[str, _ty.Any] = transition["extra_info"]
            transition_extra_info.update(self._transition_extra_info.get((from_state, to_state), {"points": []}))
        data["extra_data"]["styling"] = self._styling_extra_data
        return data


class CustomPythonModule(SerializationModule):
    def __init__(self, extension_path: str) -> None:
        self._content: str
        with os_open(extension_path, "r") as f:
            self._content = f.read().decode("UTF-8")

    def hook(self, data: dict) -> dict:
        data["extra_data"]["custom_python"] = {
            "full_hash_sha256": hashlib.sha256(self._content.encode("UTF-8")).digest(),
            "stripped": _strip_python_code(self._content)
        }
        return data


class InvalidParameterError(Exception):
    """Raised when a parameter does not exist or is unrecognized."""
    pass


def step_simulation(simulation: Simulation, step_size: int = 1,
                    MAX_SIMULATION_REPLAY_STEPS: int = 100) -> bool | None:
    timer = FlexTimer()
    if simulation.finished.get_value() and simulation.paused.get_value():
        print("finished")
        return False

    if simulation.step_index >= len(simulation.simulation_steps):
        if simulation.finished.get_value():
            return False

        print(f"bigger {simulation.step_index}, {len(simulation.simulation_steps)}")
        return None

    if simulation.step_index >= MAX_SIMULATION_REPLAY_STEPS:
        simulation.finished.set_value(True)
        simulation.paused.set_value(True)
        print("max")
        return False

    i = simulation.step_index

    step = simulation.simulation_steps[i]
    output: DefaultTape = step["complete_output"]
    state_id = step["active_states"]
    print("Inner", timer.end())

    print(f"{i + 1} {len(simulation.simulation_steps)} {[output.get_tape()[k] for k in output.get_tape().keys()]} "
          f"State: {state_id[0] + 1}")
    print(f"{" " * len(str(i + 1))} {len(simulation.simulation_steps)} {' ' * 5 * output.get_pointer()}^")
    simulation.step_index = simulation.step_index + step_size

    return True


class AutomatonData:
    def __init__(self, extensions: list[dict[str, _ts.ModuleType | str]], /,
                 base_extensions_dir: str) -> None:
        self._extensions: AutomatonProvider = AutomatonProvider()
        self._extensions.register_automatons(extensions)
        self._loaded: bool = False
        self._automaton_type: str = "Unknown"
        self._automaton: IAutomaton | None = None  # TODO: Remove
        self._settings: AutomatonSettings | None = None
        self._start_state: str = ""  # "" is an invalid state name
        self._states: list[str] = []
        self._state_types: list[str] = []
        self._transitions: list[tuple[str, str, tuple[str, ...]]] = []
        self._token_lsts: list[tuple[list[str], bool]] = []

        self._simulation_result_lst: list = []

        if not os.path.isdir(base_extensions_dir):
            raise ValueError(f"The path '{base_extensions_dir}' for base_extension_dir is not a directory.")
        self._base_extension_dir: str = base_extensions_dir

    @staticmethod
    def _get_index(lst: list[_ty.Any], element: _ty.Any) -> int:
        try:
            return lst.index(element)
        except ValueError:
            return -1

    def get_loaded_automaton_types(self) -> tuple[str, ...]:
        return self._extensions.loaded_automatons

    def get_loaded_automatons_state_types(self) -> tuple[str, ...]:
        return tuple(self._settings.state_types)

    def create(self, automaton_type: str) -> None:
        """Creates a new automaton of automaton_type"""
        if self._loaded:
            raise RuntimeError(
                f"Cannot create new automaton while automaton of type '{self._automaton_type}' is loaded."
            )
        if automaton_type not in self._extensions.loaded_automatons:
            raise InvalidParameterError(f"Automaton type '{automaton_type}' is not loaded")
        print(f"Creating automaton of type {automaton_type} ...")
        self._automaton_type = automaton_type
        auto_dict = self._extensions.get_automaton(automaton_type)
        self._automaton = auto_dict[IAutomaton]  # TODO: Remove
        self._settings = auto_dict[AutomatonSettings]
        self._start_state = ""
        self._states.clear()
        self._state_types.clear()
        self._transitions.clear()
        self._token_lsts.clear()
        self._token_lsts.extend(self._settings.token_lists)
        self._simulation_result_lst.clear()
        self._loaded = True

    # TODO: Implement together with how to load module / extra data
    def load(self, filepath: str) -> None:
        """Loads a new automaton from filepath"""
        if self._loaded:
            raise RuntimeError(
                f"Cannot load new automaton while automaton of type '{self._automaton_type}' is loaded."
            )
        elif not os.path.isfile(filepath):
            raise InvalidParameterError("You need to provide an existing file path to load.")
        elif not filepath.endswith((".au", ".json", ".yml", ".yaml")):
            raise InvalidParameterError("You need to select a valid automaton file.")
        print(f"Loading automaton from filepath {filepath} ...")
        raise NotImplementedError("This option is currently not available")
        auto_type: str = "tm"
        self.create(auto_type)
        self._states.extend(["a"])

    def save(self, filepath: str, extra_modules: list[SerializationModule]) -> None:
        """Saves the loaded automaton to filepath"""
        if not self._loaded:
            raise RuntimeError(
                f"Cannot save automaton when there is none loaded."
            )
        elif not filepath.endswith((".au", ".json", ".yml", ".yaml")):
            raise InvalidParameterError("You need to select a valid automaton file.")
        print(f"Saving automaton to filepath {filepath} ...")
        os.makedirs(os.path.basename(filepath), exist_ok=True)
        modules: list[SerializationModule] = [
            CustomPythonModule(os.path.join(self._base_extension_dir, f"{self._settings.module_name}.py"))
        ]
        modules.extend(extra_modules)
        file_ext: str = os.path.splitext(filepath)[-1][1:]  # Last element is .{ext} then we remove the dot
        format_: _ty.Literal["binary", "yaml", "json"] = {"au": "binary", "yml": "yaml"}.get(file_ext, file_ext)

        serialized_automaton: bytes = serialize(self, modules, format_=format_)
        with os_open(filepath, "w") as f:
            f.write(serialized_automaton)

    def close(self) -> None:
        """Closes currently loaded / created automaton"""
        if not self._loaded:
            raise RuntimeError("Can't close when there is no automaton loaded.")
        self._loaded = False

    @contextlib.contextmanager
    def _ensure_loaded(self) -> tuple[IAutomaton, AutomatonSettings]:
        if not self._loaded:
            raise RuntimeError("You can't perform operations when there is no automaton loaded.")
        elif self._automaton is None or self._settings is None:
            raise RuntimeError("Unknown error occurred, internal _automaton or _settings is None while loaded.")
        yield self._automaton, self._settings

    def add_state(self, state_name: str | None = None) -> None:
        """Adds a state with the name state_name. If no name is provided, it uses an ascending name."""
        with self._ensure_loaded() as (automaton, settings):
            if state_name is None:
                state_name = f"q{len(self._states)}"
                print(f"Using ascending name '{state_name}'")
            elif state_name in self._states:
                raise InvalidParameterError(f"A state with the name '{state_name}' already exists.")
            elif state_name == "":
                raise InvalidParameterError(f"A state can't have no name.")
            self._states.append(state_name)
            self._state_types.append(settings.state_types[0])  # TODO: Assuming idx 0 is the default

    def change_state_name(self, old_state_name: str, new_state_name: str) -> None:
        with self._ensure_loaded() as (automaton, settings):
            if old_state_name not in self._states:
                raise InvalidParameterError(f"State '{old_state_name}' does not exist.")
            elif new_state_name == "":
                raise InvalidParameterError(f"A state can't have no name.")
            if old_state_name == self._start_state:
                self._start_state = new_state_name
            idx_pairs_to_change: list[tuple[int, int]] = []
            for i, (tq1, tq2, _) in enumerate(self._transitions):
                if tq1 == old_state_name:
                    idx_pairs_to_change.append((i, 0))
                if tq2 == old_state_name:  # State can transition to itself
                    idx_pairs_to_change.append((i, 1))
            for (outer_i, inner_i) in idx_pairs_to_change:
                (q0, q1, params) = self._transitions[outer_i]
                if inner_i == 0:
                    new = (new_state_name, q1, params)
                elif inner_i == 1:
                    new = (q0, new_state_name, params)
                self._transitions[outer_i] = new

    def set_start_state(self, state_name: str) -> None:
        """Sets the state with the name state_name to be the start state"""
        with self._ensure_loaded() as (automaton, settings):
            idx: int = self._states.index(state_name)
            if idx == -1:
                raise InvalidParameterError(f"A state with the name '{state_name}' does not exist.")
            self._start_state = state_name

    def change_state_type(self, state_name: str, new_state_type: str) -> None:
        """Changes the state type of the state with the name state_name"""
        with self._ensure_loaded() as (automaton, settings):
            idx: int = self._states.index(state_name)
            if idx == -1:
                raise InvalidParameterError(f"A state with the name '{state_name}' does not exist.")
            elif new_state_type not in settings.state_types:
                raise InvalidParameterError(
                    f"State type '{new_state_type}' is not a valid state type for automaton of type {self._automaton_type}"
                )
            self._state_types[idx] = new_state_type

    def connect_states(self, q1: str, q2: str, params: tuple[str, ...]) -> None:
        """Connects states q1 and q2 together with the parameters params"""
        with self._ensure_loaded() as (automaton, settings):
            idx1: int = self._get_index(self._states, q1)
            idx2: int = self._get_index(self._states, q2)
            if idx1 == -1 or idx2 == -1:
                raise InvalidParameterError("One or both of the provided states does/do not exist")
            elif len(params) != len(settings.transition_description_layout):
                raise InvalidParameterError(
                    f"You did not provide the correct param length, they need to be "
                    f"{len(settings.transition_description_layout)} long"
                )
            for token, trans_idx in zip(params, settings.transition_description_layout):
                token_lst: list[str] = self._token_lsts[trans_idx][0]
                if token not in token_lst:  # TODO: Raise error
                    print(f"The input token '{token}' is not in the token list {token_lst}")
            self._transitions.append((q1, q2, params))

    def unconnect_states(self, q1: str, q2: str) -> None:
        """Unconnects states q1 and q2"""
        with self._ensure_loaded() as (automaton, settings):
            idx1: int = self._get_index(self._states, q1)
            idx2: int = self._get_index(self._states, q2)
            if idx1 == -1 or idx2 == -1:
                raise InvalidParameterError("One or both of the provided states does/do not exist")
            i: int = -1
            for i, (tq1, tq2, _) in enumerate(self._transitions):
                if tq1 == q1 and tq2 == q2:
                    break
            if i == -1:
                raise InvalidParameterError(f"There is no transition between {q1} and {q2}")
            self._transitions.pop(i)

    def remove_state(self, state_name: str) -> None:
        """Removes the state with the name state_name"""
        with self._ensure_loaded() as (automaton, settings):
            try:
                self._states.remove(state_name)
                if state_name == self._start_state:
                    self._start_state = ""
            except ValueError:
                raise InvalidParameterError(f"State '{state_name}' does not exist.")
            idxs_to_delete: list[int] = []
            for i, (tq1, tq2, _) in enumerate(self._transitions):
                if tq1 == state_name or tq2 == state_name:
                    idxs_to_delete.append(i)
            for idx in idxs_to_delete[::-1]:  # From the back so the idx do not shift around
                self._transitions.pop(idx)

    def add_token(self, token_lst_idx: int, token_name: str) -> None:
        """Adds token token_name to token list at token_lst_idx"""
        with self._ensure_loaded() as (automaton, settings):
            if token_lst_idx >= len(self._token_lsts):
                raise InvalidParameterError(f"The token lst idx '{token_lst_idx}' is invalid.")
            token_lst: tuple[list[str], bool] = self._token_lsts[token_lst_idx]
            if not token_lst[1]:
                raise InvalidParameterError(f"The token lst at idx {token_lst_idx} is not editable.")
            token_lst[0].append(token_name)

    def remove_token(self, token_lst_idx: int, token_name: str) -> None:
        """Removes token token_name to token list at token_lst_idx"""
        with self._ensure_loaded() as (automaton, settings):
            if token_lst_idx >= len(self._token_lsts):
                raise InvalidParameterError(f"The token lst idx '{token_lst_idx}' is invalid.")
            token_lst: tuple[list[str], bool] = self._token_lsts[token_lst_idx]
            if not token_lst[1]:
                raise InvalidParameterError(f"The token lst at idx {token_lst_idx} is not editable.")
            try:
                token_lst[0].remove(token_name)
            except ValueError:
                raise InvalidParameterError(f"Token '{token_name}' does not exist in the token list at idx {token_lst_idx}.")

    def _packet_notifier(self, simulation, step_size: int,
                         max_simulation_replay_steps: int,
                         stopevent: threading.Event):
        for i, step in list(enumerate(simulation.simulation_steps))[::step_size]:
            self._simulation_result_lst.append(step)
            if i + step_size >= max_simulation_replay_steps:
                simulation.finished.set_value(True)
                simulation.paused.set_value(True)
                break
        stopevent.set()

    def start_automaton(self, input_tokens: list[str], /, step_size: int = 1,
                        max_simulation_replay_steps: int = 100) -> threading.Event:
        """Starts the automaton async and returns a stop event when for when it has finished."""
        with self._ensure_loaded() as (automaton, settings):
            token_lst: list[str] = self._token_lsts[0][0]  # TODO: What to do about custom options with the Tape?
            for token in input_tokens:
                if token not in token_lst:  # TODO: Raise error
                    print(f"The input token '{token}' is not in the token list {token_lst}")
            stopevent = threading.Event()
            start_state_idx: int = self._get_index(self._states, self._start_state)
            if start_state_idx == -1:
                raise InvalidParameterError("You need to set a start state before starting the automaton")
            sim_packet = SimulationStartPacket(
                [(i, v) for i, v in enumerate(self._state_types)],
                start_state_idx,
                [
                    Transition(i, self._states.index(q1), self._states.index(q2), list(params)) for
                    i, (q1, q2, params) in enumerate(self._transitions)
                ],
                DefaultTape(input_tokens),  # TODO: What to do about custom options with the Tape?
                self._automaton_type,
                lambda simulation: self._packet_notifier(simulation, step_size, max_simulation_replay_steps, stopevent)
            )
            self._simulation_result_lst.clear()  # TODO: Maybe move to _packet_notifier?
            PacketManager().send_backend_packet(sim_packet)
            print(f"packet send {PacketManager().has_backend_packets()}")
            print("REPLAY START")
            return stopevent


def _verify_dcg_dict(target: dict[str, _ty.Any], tuple_as_lists: bool = False) -> bool:
    """Verifies the given dictionary matches the specified rules."""
    rules = {  # Validation rules
        "version": float,  # The file version
        "info": {
            "uuid": str,  # The uuid of the plugin
            "name": str,
            "author": str,
            "state_types": [str],  # list[str]
            "token_lsts": [[str]],  # list[list[str]]
            "token_lst_info": [
                {  # RUNNING WIDGET !!! Maybe custom widget for running state instead of custom widget for output?
                    "name": str,
                    "is_input": bool,
                    "is_changeable": bool,
                    "transition_section_idx": int
                }
            ]
        },
        "data": {
            "automaton_name": str,  # get this name from username of pc
            "automaton_author": str,
            "start_idx": 0,
            "content": [  # "content_root_idx": 0,  --> Always make 0, work through stack, if at bottom get next element that was not yet (de-)serialized?
                {
                    "name": str,
                    "type": str,
                    "extra_info": {  # dict[str, _ty.Any]
                        "position": (float, float),
                        "size": float,
                        "background_color": str
                    }
                    # "extra_info": {str: object}
                }
            ],
            "content_transitions": [
                {  # From content idx to content idx | x, y points for the different sections | different token lst idxs
                    "from_idx": int,
                    "to_idx": int,
                    "transition": [int],
                    "extra_info": {  # dict[str, _ty.Any]
                        "points": [(int, int)]
                    }
                    # "extra_info": {str: object}
                }
            ]
        },
        "extra_data": {
            "styling": {  # Maybe ask if it should load custom (state) styling? Values are always [light, dark], we could also just completely exclude this styling now
                "activation_graphics_effect": str,
                # These all have different stylings depending on the os theme (light/dark)
                "states": {},  # dict[str, tuple[str, str]]
                "arrow_color": (str, str),
                "text_color": (str, str),
                "text_underglow_color": (str, str)
            },
            "custom_python": {
                "full_hash_sha256": str,
                "stripped": str
            }
        }
        # "extra_data": {str: {str: object}}
    }

    def _validate(value: _ty.Any, rule: _ty.Any) -> bool:
        """Recursively validates a value against a rule."""
        if isinstance(rule, type):  # Base type
            return isinstance(value, rule)
        elif isinstance(rule, list):  # List of specific structure
            if not isinstance(value, list):
                return False
            element_rule = rule[0]
            return all(_validate(item, element_rule) for item in value)
        elif isinstance(rule, tuple):  # Tuple of specific structure
            if (not isinstance(value, tuple) or len(value) != len(rule)) and not tuple_as_lists:
                return False
            return all(_validate(value[i], rule[i]) for i in range(len(rule)))
        elif isinstance(rule, dict):  # Dictionary with specific structure
            if not isinstance(value, dict):
                return False
            for key_rule, val_rule in rule.items():
                if isinstance(key_rule, type):  # Dynamic keys (e.g., str)
                    if not all(isinstance(k, key_rule) and _validate(v, val_rule) for k, v in value.items()):
                        return False
                elif key_rule not in value or not _validate(value[key_rule], val_rule):
                    return False
            return True
        else:
            return False

    for key, key_rule in rules.items():
        if key not in target or not _validate(target[key], key_rule):
            print(f"Validation failed for key '{key}': {target.get(key)}")
            return False
    return True


def _serialize_to_json(serialisation_target: dict) -> bytes:
    return beautify_json(serialisation_target).encode("utf-8")
def _serialize_to_yaml(serialisation_target: dict) -> bytes:
    dump: _ty.Any = yaml.safe_dump(serialisation_target, default_flow_style=False)  # Will return a str if no stream is passed
    if not isinstance(dump, str):
        raise RuntimeError("Yaml Dump did not result in str")
    return dump.encode("utf-8")
def _serialize_to_binary(serialisation_target: dict) -> bytes: ...

def serialize(
        automaton: AutomatonData, modules: list[SerializationModule], /,
        format_: _ty.Literal["json", "yaml", "binary"] = "json"
    ) -> bytes:
    """TBA"""

def _deserialize_from_json(bytes_like: bytes) -> dict:
    obj: _ty.Any = json.loads(bytes_like.decode("utf-8"))
    if not isinstance(obj, dict):
        raise RuntimeError("Loaded json object is not in the right format")
    return obj
def _deserialize_from_yaml(bytes_like: bytes) -> dict:
    obj: _ty.Any = yaml.safe_load(StringIO(bytes_like.decode("utf-8")))
    if not isinstance(obj, dict):
        raise RuntimeError("Loaded yaml object is not in the right format")
    return obj
def _deserialize_from_binary(bytes_like: bytes) -> dict: ...

def deserialize(automaton: AutomatonData, bytes_like: bytes,
                format_: _ty.Literal["json", "yaml", "binary"] = "json") -> str:
    """TBA"""
