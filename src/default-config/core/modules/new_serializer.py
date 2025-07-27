"""Serialize an AutomatonData class to a file"""
# Build-in
from dataclasses import dataclass as _dataclass, field as _field
from io import StringIO
import contextlib
import threading
import hashlib
import base64
import json
import zlib
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
import msgpack
import yaml

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts


class SerializationModule(_ty.Protocol):
    def hook(self, data: dict) -> dict: ...
    def unhook(self, data: dict, auto: "AutomatonData") -> None: ...


# TODO: Update
class QtGUIDataModule(SerializationModule):
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

    def unhook(self, data: dict, auto: "AutomatonData") -> None:
        return None  # TODO: Implement


class CustomPythonModule(SerializationModule):
    def __init__(self, base_extension_path: str, extension_filename: str | None) -> None:
        self._base_extension_path: str = base_extension_path
        self._extension_filename: str | None = extension_filename
        self._content: str | None = None

    @staticmethod
    def _strip_python_code(source: str) -> str:
        # Remove docstrings (triple-quoted strings that appear as docstrings)
        source = re.sub(r'(?s)"""(.*?)"""', '', source)  # triple double quotes
        source = re.sub(r"(?s)'''(.*?)'''", '', source)  # triple single quotes

        # Remove single-line comments
        source = re.sub(r'#.*', '', source)

        # Optionally: remove excessive blank lines
        source = re.sub(r'\n\s*\n', '\n', source)

        return source.strip()

    @staticmethod
    def _compress_python_code(source: str) -> str:
        """Compress and base64-encode the code using zlib."""
        compressed = zlib.compress(source.encode('utf-8'), level=9)
        return base64.b64encode(compressed).decode('utf-8')

    def hook(self, data: dict) -> dict:
        if self._extension_filename is None:
            raise RuntimeError("You did not provide an extension filename and then tried to hook")
        with os_open(os.path.join(self._base_extension_path, self._extension_filename), "r") as f:
            self._content = f.read().decode("UTF-8")
        stripped: str = self._strip_python_code(self._content)
        compressed: str = self._compress_python_code(stripped)
        data["extra_data"]["custom_python"] = {
            "full_hash_sha256": hashlib.sha256(self._content.encode("UTF-8")).digest(),
            "minimal_compressed": compressed
        }
        return data

    def unhook(self, data: dict, auto: "AutomatonData") -> None:
        custom_python_dict: dict | None = data["extra_data"].get("custom_python")
        if custom_python_dict is None:
            return None
        filename: str = f"{data['info']['name']}.py"
        filepath: str = os.path.join(self._base_extension_path, filename)
        if not os.path.exists(filepath):
            with os_open(filepath, "w") as f:
                f.write(custom_python_dict["minimal_compressed"])  # TODO: uncompress etc.
        return None  # TODO: Do something with the hash? Maybe verify if it's the same when it's there.


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


# TODO: Maybe work more closely with backend?
class AutomatonSession:
    def __init__(self, validator: "AutomatonInterface") -> None:
        self._validator: "AutomatonInterface" = validator
        self._simulation_result_lst: list = []

        self._data: "AutomatonData | None" = None
        self._settings: AutomatonSettings | None = None

    def _packet_notifier(self, simulation: Simulation, step_size: int,
                         max_simulation_replay_steps: int,
                         stopevent: threading.Event):
        for i, step in list(enumerate(simulation.simulation_steps))[::step_size]:
            self._simulation_result_lst.append(step)
            if i + step_size >= max_simulation_replay_steps:
                simulation.finished.set_value(True)
                simulation.paused.set_value(True)
                break
        stopevent.set()

    def start(self, input_tokens: list[str], notifier: _a.Callable[[dict[str, _ty.Any]], int], /, step_size: int = 1,
                        max_simulation_replay_steps: int = 100) -> threading.Event:
        """Starts the automaton async and returns a stop event when for when it has finished."""
        if self._settings is None:
            raise RuntimeError("You need to enter the context manager to use this method")
        self._simulation_result_lst.clear()
        token_lst: list[str] = self._data.token_lsts[0]  # TODO: What to do about custom options with the Tape?
        for token in input_tokens:
            if token not in token_lst:
                raise InvalidParameterError(f"The input token '{token}' is not in the token list {token_lst}")
        stopevent = threading.Event()
        try:
            start_state_idx: int = self._data.get_state_idx(self._data.start_state)
        except InvalidParameterError as e:
            raise InvalidParameterError("You need to set a start state before starting the automaton") from e
        sim_packet = SimulationStartPacket(
            [(i, v) for i, v in enumerate(self._data.state_types)],
            start_state_idx,
            [
                Transition(i, self._data.get_state_idx(q0), self._data.get_state_idx(q1), list(params)) for
                i, (q0, q1, params) in enumerate(self._data.transitions)
            ],
            DefaultTape(input_tokens),  # TODO: What to do about custom options with the Tape?
            self._data.automaton_type,
            lambda simulation: self._packet_notifier(simulation, step_size, max_simulation_replay_steps, stopevent)
        )
        PacketManager().send_backend_packet(sim_packet)
        print(f"packet send {PacketManager().has_backend_packets()}")
        print("REPLAY START")
        return stopevent

    def __enter__(self) -> None:
        data: AutomatonData
        settings: AutomatonSettings
        with self._validator._ensure_loaded() as (data, settings):
            self._data = data
            self._settings = settings
            yield

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self._settings = None
        return False


@_dataclass
class AutomatonData:
    automaton_uuid: str = "00000000-0000-0000-0000-000000000000"
    automaton_type: str = "Unknown"
    states: list[str] = _field(default_factory=list)
    state_types: list[str] = _field(default_factory=list)
    state_runtime_data: list[dict[str, _ty.Any]] = _field(default_factory=list)
    start_state: str = ""  # "" is an invalid state name
    transitions: list[tuple[str, str, tuple[str, ...]]] = _field(default_factory=list)
    transition_runtime_data: list[dict[str, _ty.Any]] = _field(default_factory=list)
    token_lsts: list[list[str]] = _field(default_factory=list)
    # runtime_data: dict[str, _ty.Any] = _field(default_factory=dict)  # TODO: Can also be transported using the module instance

    @staticmethod
    def _get_index(lst: list[_ty.Any], element: _ty.Any) -> int:
        try:
            return lst.index(element)
        except ValueError:
            return -1

    def get_state_idx(self, state_name: str) -> int:
        idx: int = self._get_index(self.states, state_name)
        if idx == -1:
            raise InvalidParameterError(f"State of name '{state_name}' does not exist")
        return idx

    def get_state_type(self, state_name: str) -> str | None:
        idx: int = self._get_index(self.states, state_name)
        if idx == -1:
            return None
        return self.state_types[idx]

    def get_state_runtime_data(self, state_name) -> dict[str, _ty.Any] | None:
        idx: int = self._get_index(self.states, state_name)
        if idx == -1:
            return None
        return self.state_runtime_data[idx]

    def get_transition_idx(self, from_: str, to: str) -> int:
        self.get_state_idx(from_)  # To raise errors if they do not exist
        self.get_state_idx(to)
        for idx, (q0, q1, _) in enumerate(self.transitions):
            if q0 == from_ and q1 == to:
                return idx
        raise InvalidParameterError(f"There is no transition between {from_} and {to}")


class AutomatonInterface:
    def __init__(self, extensions: list[dict[str, _ts.ModuleType | str]], /,
                 base_extensions_dir: str) -> None:
        self._extensions: AutomatonProvider = AutomatonProvider()
        self._extensions.register_automatons(extensions)
        self._loaded: bool = False
        self._settings: AutomatonSettings | None = None
        self._data: AutomatonData = AutomatonData()

        if not os.path.isdir(base_extensions_dir):
            raise ValueError(f"The path '{base_extensions_dir}' for base_extension_dir is not a directory.")
        self._base_extension_dir: str = base_extensions_dir

    def get_loaded_automaton_types(self) -> list[str]:
        return self._extensions.loaded_automatons

    def get_loaded_automatons_state_types(self) -> list[str]:
        return self._settings.state_types

    def create(self, automaton_type: str) -> None:
        """Creates a new automaton of automaton_type"""
        if self._loaded:
            raise RuntimeError(
                f"Cannot create new automaton while automaton of type '{self._data.automaton_type}' is loaded."
            )
        if automaton_type not in self._extensions.loaded_automatons:
            raise InvalidParameterError(f"Automaton type '{automaton_type}' is not loaded")
        print(f"Creating automaton of type {automaton_type} ...")
        self._data.automaton_type = automaton_type
        auto_dict = self._extensions.get_automaton(automaton_type)
        self._settings = auto_dict[AutomatonSettings]
        # self._data.automaton_uuid = self._settings.get_uuid()  # TODO: Add
        self._data.start_state = ""
        self._data.states.clear()
        self._data.state_types.clear()
        self._data.state_runtime_data.clear()
        self._data.transitions.clear()
        self._data.transition_runtime_data.clear()
        self._data.token_lsts.clear()
        self._data.token_lsts.extend([lst[0] for lst in self._settings.token_lists])
        self._loaded = True

    def load(self, filepath: str, extra_modules: list[SerializationModule] | None = None) -> "tuple[AutomatonSettings, AutomatonInfo]":
        """Loads a new automaton from filepath"""
        if extra_modules is None:
            extra_modules = []
        if self._loaded:
            raise RuntimeError(
                f"Cannot load new automaton while automaton of type '{self._data.automaton_type}' is loaded."
            )
        elif not os.path.isfile(filepath):
            raise InvalidParameterError("You need to provide an existing file path to load.")
        elif not filepath.endswith((".au", ".json", ".yml", ".yaml")):
            raise InvalidParameterError("You need to select a valid automaton file.")
        print(f"Loading automaton from filepath {filepath} ...")

        content: bytes
        with os_open(filepath, "r") as f:
            content = f.read()

        modules: list[SerializationModule] = [
            CustomPythonModule(self._base_extension_dir, None)
        ]
        modules.extend(extra_modules)

        data: AutomatonData
        settings: AutomatonSettings  # If we did not load the automaton what we know about it will be loaded here
        info: AutomatonInfo
        data, settings, info = deserialize(content, modules)

        # TODO: Maybe try to create and if not use the provided settings?
        self.create(data.automaton_type)  # This way all of this is authenticated
        for state_name, type_, runtime_data in zip(data.states, data.state_types, data.state_runtime_data):
            self.add_state(state_name)
            self.change_state_type(state_name, type_)
            self._data.state_runtime_data[self._data.get_state_idx(state_name)].update(runtime_data)
        if data.start_state != "":
            self.set_start_state(data.start_state)
        for i, token_lst in enumerate(data.token_lsts):  # Load tokens first so the transitions work
            default = self._settings.token_lists[i][0]
            extra_tokens = [item for item in token_lst if item not in default]
            for token in extra_tokens:
                self.add_token(i, token)
        for (q0, q1, params), runtime_data in zip(data.transitions, data.transition_runtime_data):
            self.connect_states(q0, q1, params)
            self._data.transition_runtime_data[self._data.get_transition_idx(q0, q1)].update(runtime_data)
        return settings, info

    def save(self, filepath: str, automaton_name: str = "New automaton",
             extra_modules: list[SerializationModule] | None = None) -> None:
        """Saves the loaded automaton to filepath"""
        if extra_modules is None:
            extra_modules = []
        if not self._loaded:
            raise RuntimeError(
                f"Cannot save automaton when there is none loaded."
            )
        elif not filepath.endswith((".au", ".json", ".yml", ".yaml")):
            raise InvalidParameterError("You need to select a valid automaton file.")
        data: AutomatonData
        settings: AutomatonSettings
        with self._ensure_loaded() as (data, settings):
            print(f"Saving automaton to filepath {filepath} ...")
            os.makedirs(os.path.basename(filepath), exist_ok=True)

            modules: list[SerializationModule] = [
                CustomPythonModule(self._base_extension_dir, f"{settings.module_name.lower()}.py")
            ]
            modules.extend(extra_modules)

            file_ext: str = os.path.splitext(filepath)[-1][1:]  # Last element is .{ext} then we remove the dot
            format_: str = {"au": "binary", "yml": "yaml"}.get(file_ext, file_ext)
            if format_ not in ["binary", "yaml", "json"]:
                raise InvalidParameterError("You need to select a valid automaton file.")
            format_: _ty.Literal["binary", "yaml", "json"] = _ty.cast(_ty.Literal["binary", "yaml", "json"], format_)

            user_name: str
            try:
                user_name = os.getlogin()
            except OSError:
                user_name = "Unknown"

            automaton_info: AutomatonInfo = AutomatonInfo(automaton_name, user_name)

            serialized_automaton: bytes = serialize(data, settings, automaton_info, modules, format_=format_)
            with os_open(filepath, "w") as f:
                f.write(serialized_automaton)

    def close(self) -> None:
        """Closes currently loaded / created automaton"""
        if not self._loaded:
            raise RuntimeError("Can't close when there is no automaton loaded.")
        self._loaded = False

    @contextlib.contextmanager
    def _ensure_loaded(self) -> tuple[AutomatonData, AutomatonSettings]:
        if not self._loaded:
            raise RuntimeError("You can't perform operations when there is no automaton loaded.")
        elif self._settings is None:
            raise RuntimeError("Unknown error occurred, internal _settings is None while loaded.")
        yield self._data, self._settings

    def add_state(self, state_name: str | None = None) -> None:
        """Adds a state with the name state_name. If no name is provided, it uses an ascending name."""
        data: AutomatonData
        settings: AutomatonSettings
        with self._ensure_loaded() as (data, settings):
            if state_name is None:
                state_name = f"q{len(data.states)}"
                print(f"Using ascending name '{state_name}'")
            elif state_name in data.states:
                raise InvalidParameterError(f"A state with the name '{state_name}' already exists.")
            elif state_name == "":
                raise InvalidParameterError(f"A state can't have no name.")
            data.states.append(state_name)
            data.state_types.append(settings.state_types[settings.default_state_type_index])
            data.state_runtime_data.append({})

    def change_state_name(self, old_state_name: str, new_state_name: str) -> None:
        data: AutomatonData
        settings: AutomatonSettings
        with self._ensure_loaded() as (data, settings):
            if old_state_name not in data.states:
                raise InvalidParameterError(f"State '{old_state_name}' does not exist.")
            elif new_state_name == "":
                raise InvalidParameterError(f"A state can't have no name.")
            if old_state_name == data.start_state:
                data.start_state = new_state_name
            idx_pairs_to_change: list[tuple[int, int]] = []
            for i, (tq1, tq2, _) in enumerate(data.transitions):
                if tq1 == old_state_name:
                    idx_pairs_to_change.append((i, 0))
                if tq2 == old_state_name:  # State can transition to itself
                    idx_pairs_to_change.append((i, 1))
            for (outer_i, inner_i) in idx_pairs_to_change:
                (q0, q1, params) = data.transitions[outer_i]
                if inner_i == 0:
                    new = (new_state_name, q1, params)
                elif inner_i == 1:
                    new = (q0, new_state_name, params)
                data.transitions[outer_i] = new

    def set_start_state(self, state_name: str) -> None:
        """Sets the state with the name state_name to be the start state"""
        data: AutomatonData
        settings: AutomatonSettings
        with self._ensure_loaded() as (data, settings):
            idx: int = data.states.index(state_name)
            if idx == -1:
                raise InvalidParameterError(f"A state with the name '{state_name}' does not exist.")
            data.start_state = state_name

    def change_state_type(self, state_name: str, new_state_type: str) -> None:
        """Changes the state type of the state with the name state_name"""
        data: AutomatonData
        settings: AutomatonSettings
        with self._ensure_loaded() as (data, settings):
            idx: int = data.states.index(state_name)
            if idx == -1:
                raise InvalidParameterError(f"A state with the name '{state_name}' does not exist.")
            elif new_state_type not in settings.state_types:
                raise InvalidParameterError(
                    f"State type '{new_state_type}' is not a valid state type for automaton of type {data.automaton_type}"
                )
            data.state_types[idx] = new_state_type

    def connect_states(self, q0: str, q1: str, params: tuple[str, ...]) -> None:
        """Connects states q0 and q1 together with the parameters params"""
        data: AutomatonData
        settings: AutomatonSettings
        with self._ensure_loaded() as (data, settings):
            data.get_state_idx(q0)  # Checks for the existence of q0 and q1
            data.get_state_idx(q1)
            if len(params) != len(settings.transition_description_layout):
                raise InvalidParameterError(
                    f"You did not provide the correct param length, they need to be "
                    f"{len(settings.transition_description_layout)} long"
                )
            for token, trans_idx in zip(params, settings.transition_description_layout):
                token_lst: list[str] = data.token_lsts[trans_idx]
                if token not in token_lst:
                    raise InvalidParameterError(f"The input token '{token}' is not in the token list {token_lst}")
            data.transitions.append((q0, q1, params))
            data.transition_runtime_data.append({})

    def unconnect_states(self, q0: str, q1: str) -> None:
        """Unconnects states q0 and q1"""
        data: AutomatonData
        settings: AutomatonSettings
        with self._ensure_loaded() as (data, settings):
            # Checks for the existence of q0 and q1 and the transition between them
            idx: int = data.get_transition_idx(q0, q1)
            data.transitions.pop(idx)
            data.transition_runtime_data.pop(idx)

    def remove_state(self, state_name: str) -> None:
        """Removes the state with the name state_name"""
        data: AutomatonData
        settings: AutomatonSettings
        with self._ensure_loaded() as (data, settings):
            state_idx: int = data.get_state_idx(state_name)  # Raises an InvalidParameter error if state does not exist

            data.states.pop(state_idx)
            data.state_types.pop(state_idx)
            data.state_runtime_data.pop(state_idx)

            if state_name == data.start_state:
                data.start_state = ""

            idxs_to_delete: list[int] = []
            for i, (tq1, tq2, _) in enumerate(data.transitions):
                if tq1 == state_name or tq2 == state_name:
                    idxs_to_delete.append(i)
            for idx in idxs_to_delete[::-1]:  # From the back so the idx do not shift around
                data.transitions.pop(idx)

    # TODO: Add token lst names?
    def add_token(self, token_lst_idx: int, token_name: str) -> None:
        """Adds token token_name to token list at token_lst_idx"""
        data: AutomatonData
        settings: AutomatonSettings
        with self._ensure_loaded() as (data, settings):
            if token_lst_idx >= len(data.token_lsts):
                raise InvalidParameterError(f"The token lst idx '{token_lst_idx}' is invalid.")
            token_lst: tuple[list[str], bool] = self._settings.token_lists[token_lst_idx]
            if not token_lst[1]:
                raise InvalidParameterError(f"The token lst at idx {token_lst_idx} is not editable.")
            data.token_lsts[token_lst_idx].append(token_name)

    # TODO: Add token lst names?
    def remove_token(self, token_lst_idx: int, token_name: str) -> None:
        """Removes token token_name to token list at token_lst_idx"""
        data: AutomatonData
        settings: AutomatonSettings
        with self._ensure_loaded() as (data, settings):
            if token_lst_idx >= len(data.token_lsts):
                raise InvalidParameterError(f"The token lst idx '{token_lst_idx}' is invalid.")
            token_lst: tuple[list[str], bool] = self._settings.token_lists[token_lst_idx]
            if not token_lst[1]:
                raise InvalidParameterError(f"The token lst at idx {token_lst_idx} is not editable.")
            try:
                data.token_lsts[token_lst_idx].remove(token_name)
            except ValueError:
                raise InvalidParameterError(f"Token '{token_name}' does not exist in the token list at idx {token_lst_idx}.")

    def session(self) -> AutomatonSession:
        return AutomatonSession(self)


dcg_0_5_rules = {  # Validation rules
    "name": str,
    "author": str,
    "token_lsts": [[str]],  # list[list[str]]
    "is_custom_token_lst": [bool],  # list[bool]
    "abs_transition_idxs": [int],  # list[int]
    "types": {
        str: str
    },
    "content_root_idx": int,
    "content": [
        {
            "name": str,
            "type": str,
            "position": (float, float),  # tuple[float, float]
            "background_color": str,
        }
    ],
    "content_transitions": [
        ((int, int), (str, str), [int])
    ],  # list[tuple[tuple[int, int], tuple[int, int], list[int]]]
    "custom_python": str,
}
dcg_1_0_rules = {  # Validation rules
    "version": float,  # The file version
    "info": {
        "uuid": str,  # The uuid of the plugin
        "name": str,
        "author": str,
        "state_types": [str],  # list[str]
        "default_token_lsts": [[str]],  # list[list[str]]
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
        "token_lsts": [[str]],  # list[list[str]]
        "start_idx": int,
        "content": [  # "content_root_idx": 0,  --> Always make 0, work through stack, if at bottom get next element that was not yet (de-)serialized?
            {
                "name": str,
                "type": str,
                # "extra_info": {  # dict[str, _ty.Any]
                #     "position": (float, float),
                #     "size": float,
                #     "background_color": str
                # }
                "extra_info": {str: object}
            }
        ],
        "content_transitions": [
            {  # From content idx to content idx | x, y points for the different sections | different token lst idxs
                "from_idx": int,
                "to_idx": int,
                "transition": [int],
                # "extra_info": {  # dict[str, _ty.Any]
                #     "points": [(int, int)]
                # }
                "extra_info": {str: object}
            }
        ]
    },
    # "extra_data": {
    #     "styling": {  # Maybe ask if it should load custom (state) styling? Values are always [light, dark], we could also just completely exclude this styling now
    #         "activation_graphics_effect": str,
    #         # These all have different stylings depending on the os theme (light/dark)
    #         "states": {},  # dict[str, tuple[str, str]]
    #         "arrow_color": (str, str),
    #         "text_color": (str, str),
    #         "text_underglow_color": (str, str)
    #     },
    #     "custom_python": {
    #         "full_hash_sha256": str,
    #         "minimal_compressed": str
    #     }
    # }
    "extra_data": {str: {str: object}}
}


def _verify_dcg_dict(target: dict[str, _ty.Any], rules: dict[str, _ty.Any], tuple_as_lists: bool = False) -> bool:
    """Verifies the given dictionary matches the specified rules."""
    class Validator:
        def __init__(self, default: bool, raise_if_fail: bool = False) -> None:
            self._rif: bool = raise_if_fail
            self._flag: bool = default

        def set(self, value: bool) -> None:
            if not value and self._rif:
                raise RuntimeError("Failed check")
            self._flag = value

        def get(self) -> bool:
            return self._flag

        def __bool__(self) -> bool:
            return self._flag

    def _validate(value: _ty.Any, rule: _ty.Any) -> bool:
        """Recursively validates a value against a rule."""
        valid: Validator = Validator(True, raise_if_fail=False)  # Default true
        if isinstance(rule, type):  # Base type
            print("Checking base type", rule, repr(value))
            valid.set(isinstance(value, rule))
            if not valid:
                print("Failed to validate, is not of base type")
        elif isinstance(rule, list):  # List of specific structure
            print("Checking list", rule, repr(value))
            if not isinstance(value, list):
                print("Failed to validate, is not of type list")
                valid.set(False)
            else:
                element_rule = rule[0]
                valid.set(all(_validate(item, element_rule) for item in value))
                if not valid:
                    print("Failed to validate, not all elements are of the right type")
        elif isinstance(rule, tuple):  # Tuple of specific structure
            print("Checking tuple", rule, repr(value))
            if (not isinstance(value, tuple) or len(value) != len(rule)) and not tuple_as_lists:
                print("Failed to validate, value is not tuple or is of different length and TAL is not activated")
                valid.set(False)
            else:
                valid.set(all(_validate(value[i], rule[i]) for i in range(len(rule))))
                if not valid:
                    print("Failed to validate all values are of correct type")
        elif isinstance(rule, dict):  # Dictionary with specific structure
            print("Checking dict", rule, repr(value))
            if not isinstance(value, dict):
                print("Failed to validate, is not of type dict")
                valid.set(False)
            else:
                for key_rule, val_rule in rule.items():
                    if isinstance(key_rule, type):  # Dynamic keys (e.g., str)
                        if not all(isinstance(k, key_rule) and _validate(v, val_rule) for k, v in value.items()):
                            print("Failed to validate dynamic key rule", key_rule, value)
                            valid.set(False)
                    elif key_rule not in value or not _validate(value[key_rule], val_rule):
                        print("Failed to validate set key rule", key_rule, val_rule, value[key_rule])
                        valid.set(False)
                # return True
        else:
            print("Unknown rule", rule)
            valid.set(False)
        if not valid:
            print("Check failed")
        return bool(valid)

    for key, key_rule in rules.items():
        print(f"Key {key}")
        if key not in target or not _validate(target[key], key_rule):
            print(f"Validation failed for key '{key}'-> {target.get(key)}")
            return False
    return True


def _serialize_to_json(serialisation_target: dict) -> bytes:
    return beautify_json(serialisation_target).encode("utf-8")
def _serialize_to_yaml(serialisation_target: dict) -> bytes:
    dump: _ty.Any = yaml.safe_dump(serialisation_target, default_flow_style=False)  # Will return a str if no stream is passed
    if not isinstance(dump, str):
        raise RuntimeError("Yaml Dump did not result in str")
    return dump.encode("utf-8")
def _serialize_to_binary(serialisation_target: dict) -> bytes:
    return msgpack.packb(serialisation_target)


@_dataclass
class AutomatonInfo:
    name: str
    author: str


def serialize(
        data: AutomatonData, settings: AutomatonSettings, automaton_info: AutomatonInfo, modules: list[SerializationModule], /,
        format_: _ty.Literal["json", "yaml", "binary"] = "json"
    ) -> bytes:
    """TBA"""
    dcg_dict: dict[str, _ty.Any] = {
        "version": 1.0,
        "info": {
            "uuid": data.automaton_uuid,
            "name": data.automaton_type,
            "author": settings.author,
            "state_types": settings.state_types,
            "default_token_lsts": [token_lst[0] for token_lst in settings.token_lists],
            "token_lst_info": [  # TODO: Get rid of this conversion?
                {
                    "name": "Unknown",
                    "is_input": True,
                    "is_changeable": settings.token_lists[idx][1],
                    "transition_section_idx": idx
                } for idx in settings.transition_description_layout
            ]
        },
        "data": {
            "automaton_name": automaton_info.name,
            "automaton_author": automaton_info.author,
            "token_lsts": data.token_lsts,
            "start_idx": data._get_index(data.states, data.start_state),
            "content": [],  # Will be filled later
            "content_transitions": []  # Will be filled later
        },
        "extra_data": {}  # Will be filled by modules
    }

    nodes_lst: list[dict[str, str | tuple[float, float]]] = dcg_dict["data"]["content"]
    transitions_lst: list = dcg_dict["data"]["content_transitions"]
    transition_tokens: list[list[str]] = [
        dcg_dict["data"]["token_lsts"][info["transition_section_idx"]]
        for info in dcg_dict["info"]["token_lst_info"]
    ]
    for state_name in data.states:
        nodes_lst.append({
            "name": state_name,
            "type": data.state_types[data.get_state_idx(state_name)],
            "extra_info": {}  # Will be filled by modules
        })
    for (q0, q1, params) in data.transitions:
        idx1: int = data.get_state_idx(q0)  # This works as we added them in the same order
        idx2: int = data.get_state_idx(q1)  # This works as we added them in the same order
        transitions_lst.append(
            {
                "from_idx": idx1,
                "to_idx": idx2,
                "transition": [transition_tokens[i].index(x[0]) for i, x in enumerate(params)],
                "extra_info": {}  # Will be filled by modules
            }
        )

    for module in modules:
        dcg_dict = module.hook(dcg_dict)

    if not _verify_dcg_dict(dcg_dict, dcg_1_0_rules):
        raise RuntimeError("DCG Dict could not be verified")

    return {
        "json": _serialize_to_json,
        "yaml": _serialize_to_yaml,
        "binary": _serialize_to_binary
    }[format_](dcg_dict)

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
def _deserialize_from_binary(bytes_like: bytes) -> dict:
    def _decode_bytes(obj: dict) -> dict | list | str | bytes:
        """
        Recursively convert all bytes (b'...') to strings in a data structure.
        """
        if isinstance(obj, dict):
            return {_decode_bytes(k): _decode_bytes(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_decode_bytes(item) for item in obj]
        elif isinstance(obj, bytes):
            try:
                return obj.decode('utf-8')
            except UnicodeDecodeError:
                return obj  # Leave as bytes if not UTF-8
        else:
            return obj
    unpacked_obj: _ty.Any = msgpack.unpackb(bytes_like)
    if not isinstance(unpacked_obj, dict):
        raise RuntimeError("Loaded au/messagepack object is not in the right format")
    return _decode_bytes(unpacked_obj)

def deserialize(bytes_like: bytes, modules: list[SerializationModule], /,
                format_: _ty.Literal["json", "yaml", "binary"] = "json") -> tuple[AutomatonData, AutomatonSettings, AutomatonInfo]:
    """TBA"""
    def _accepting_binary_deserialize(b_like: bytes) -> dict[str, _ty.Any]:
        try:
            result = _deserialize_from_binary(b_like)
        except Exception as e:
            print(f"Got exception {e} while trying to deserialize binary, trying older deserializer ...")
            # TODO: Older ...
            result = {}
        return result

    dcg_dict: dict[str, _ty.Any] = {"json": _deserialize_from_json,
                                    "yaml": _deserialize_from_yaml,
                                    "binary": _accepting_binary_deserialize}[format_](bytes_like)

    data: AutomatonData = AutomatonData()
    settings: AutomatonSettings
    info: AutomatonInfo

    version: float = dcg_dict.get("version", 0.5)  # Version 0.5 did not have a proper version identifier

    if version == 0.5:
        if not _verify_dcg_dict(dcg_dict, dcg_0_5_rules, tuple_as_lists=True):
            raise RuntimeError("DCG Dict could not be verified")
        name: str = dcg_dict["name"]  # type: ignore
        author: str = dcg_dict["author"]  # type: ignore
        token_lsts: list[list[str]] = dcg_dict["token_lsts"]  # type: ignore
        is_custom_token_lst: list[bool] = dcg_dict["is_custom_token_lst"]  # type: ignore
        abs_transition_idxs: list[int] = dcg_dict["abs_transition_idxs"]  # type: ignore
        types: dict[str, str] = dcg_dict["types"]  # type: ignore
        content_root_idx: int = dcg_dict["content_root_idx"]  # type: ignore
        content: list[dict] = dcg_dict["content"]  # type: ignore  # [str, str | tuple[float, float]]
        content_transitions: list = dcg_dict["content_transitions"]  # type: ignore  # [tuple[tuple[int, int], tuple[str, str], list[int]]]
        custom_python: str = dcg_dict["custom_python"]  # type: ignore

        data.automaton_type = name

        proper_token_lsts: list[tuple[list[str], bool]] = []  # TODO: Get rid of this conversion?
        for token_lst, is_custom in zip(token_lsts, is_custom_token_lst):
            proper_token_lsts.append((token_lst, is_custom))

        settings = AutomatonSettings(
            "Unknown",
            data.automaton_type,
            author,
            proper_token_lsts,
            abs_transition_idxs,
            state_types=list(types.keys()),
            default_state_type_index=-1
        )

        info = AutomatonInfo("Unknown", "Unknown")

        data.token_lsts = token_lsts
        for state_dict in content:
            data.states.append(state_dict["name"])
            type_: str = state_dict["type"]
            if type_ == "start":
                data.state_types.append(list(types.keys())[0])  # The default type
                data.start_state = state_dict["name"]
            else:
                data.state_types.append(state_dict["type"])
            state_dict["extra_data"] = {  # To maintain compatibility with the newer modules
                "position": state_dict["position"],
                "size": 1.0,
                "background_color": state_dict["background_color"]
            }
            data.state_runtime_data.append({})

        transition_tokens: list[list[str]] = [
            data.token_lsts[i]
            for i in settings.transition_description_layout
        ]
        new_content_transitions: list[dict] = []
        for ((from_idx, to_idx), (_, _), trans_token_idxs) in content_transitions:
            from_name: str = data.states[from_idx]
            to_name: str = data.states[to_idx]
            params: list[str] = [transition_tokens[i][j] for i, j in zip(settings.transition_description_layout, trans_token_idxs)]

            new_content_transitions.append({  # To maintain compatibility with the newer modules
                "from_idx": from_idx,
                "to_idx": to_idx,
                "transition": trans_token_idxs,
                "extra_info": {"points": []}
            })

            data.transitions.append((from_name, to_name, tuple(params)))
            data.transition_runtime_data.append({})
        content_transitions.clear()
        content_transitions.extend(new_content_transitions)

        dcg_dict["extra_data"] = {  # To maintain compatibility with the newer modules
            "custom_python": {
                "full_hash_sha256": hashlib.sha256(custom_python.encode("UTF-8")).hexdigest(),
                "minimal_compressed": CustomPythonModule._compress_python_code(custom_python)
            },
            "styling": {
                "activation_graphics_effect": "#FFFF00",
                "states": {k: (v, v) for k, v in types.items()},
                "arrow_color": ("#000000", "#000000"),
                "text_color": ("#FFFFFF", "#FFFFFF"),
                "text_underglow_color": ("#000000", "#000000")
            }
        }
    elif version == 1.0:
        if not _verify_dcg_dict(dcg_dict, dcg_1_0_rules, tuple_as_lists=True):
            raise RuntimeError("DCG Dict could not be verified")
        info_dict: dict[str, _ty.Any] = dcg_dict["info"]
        data.automaton_uuid = info_dict["uuid"]
        data.automaton_type = info_dict["name"]
        author: str = info_dict["author"]
        state_types: list[str] = info_dict["state_types"]
        default_token_lsts: list[list[str]] = info_dict["default_token_lsts"]
        token_lst_info: dict = info_dict["token_lst_info"]

        proper_token_lsts: list[tuple[list[str], bool]] = [None for _ in range(len(default_token_lsts))]  # TODO: Get rid of this conversion?
        proper_transition_idxs: list[int] = []
        for token_lst_info_dict in token_lst_info:
            transition_section_idx: int = token_lst_info_dict["transition_section_idx"]
            proper_token_lsts[transition_section_idx] = (default_token_lsts[transition_section_idx], token_lst_info_dict["is_changeable"])
            proper_transition_idxs.append(transition_section_idx)

        settings = AutomatonSettings(
            "Unknown",
            data.automaton_type,
            author,
            proper_token_lsts,
            proper_transition_idxs,
            state_types=state_types,
            default_state_type_index=-1
        )

        data_dict: dict[str, _ty.Any] = dcg_dict["data"]
        automaton_name: str = data_dict["automaton_name"]
        automaton_author: str = data_dict["automaton_author"]
        info = AutomatonInfo(automaton_name, automaton_author)
        data.token_lsts = data_dict["token_lsts"]

        for state_dict in data_dict["content"]:
            data.states.append(state_dict["name"])
            data.state_types.append(state_dict["type"])
            data.state_runtime_data.append({})
        start_idx: int = data_dict["start_idx"]
        if start_idx != -1:  # Start state is set as invalid by default, so we do not need to set it here
            data.start_state = data.states[start_idx]

        # transition_tokens: list[list[str]] = [
        #     data.token_lsts[i]
        #     for i in settings.transition_description_layout
        # ]
        for transition_dict in data_dict["content_transitions"]:
            from_name: str = data.states[transition_dict["from_idx"]]
            to_name: str = data.states[transition_dict["to_idx"]]
            params: list[str] = [data.token_lsts[i][j]
                                 for i, j
                                 in zip(settings.transition_description_layout, transition_dict["transition"])]

            data.transitions.append((from_name, to_name, tuple(params)))
            data.transition_runtime_data.append({})
    else:
        raise RuntimeError(f"This deserializer does not support automaton files of version {version}, please upgrade.")

    for module in modules:
        module.unhook(dcg_dict, data)

    return data, settings, info
