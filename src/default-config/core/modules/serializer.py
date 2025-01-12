"""TBA"""

from core.modules.abstract import IUiState, IUiTransition, IUiAutomaton  # Many thanks :)
from core.modules.automaton.UIAutomaton import UiAutomaton, UiState, UiTransition  # Don't know how to do without this

from queue import Queue
from io import BytesIO, StringIO
import json
import yaml

from aplustools.data.bintools import (get_variable_bytes_like, encode_float, encode_integer, read_variable_bytes_like,
                                      decode_integer, decode_float)

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts


DCGDictT = dict[str, str  # name, author, custom_python
                     | list[list[str]]  # token_lsts
                     | list[bool]  # is_custom_lst
                     | list[int]  # abs_transition_idxs
                     | dict[str, str]  # types
                     | int
                     | list[dict[
                                 str, str
                                      | tuple[float, float]
                                ]
                     ]  # content
                    | list[tuple[tuple[int, int], tuple[str, str], list[int]]]  # content_transitions
]


def _verify_dcg_dict(target: dict[str, _ty.Any], tuple_as_lists: bool = False) -> bool:
    """Verifies the given dictionary matches the specified rules."""
    # TODO: Verify max and min byte length for coordinates, ...
    rules = {  # Validation rules
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
    def validate(value: _ty.Any, rule: _ty.Any) -> bool:
        """Recursively validates a value against a rule."""
        if isinstance(rule, type):  # Base type
            return isinstance(value, rule)
        elif isinstance(rule, list):  # List of specific structure
            if not isinstance(value, list):
                return False
            element_rule = rule[0]
            return all(validate(item, element_rule) for item in value)
        elif isinstance(rule, tuple):  # Tuple of specific structure
            if (not isinstance(value, tuple) or len(value) != len(rule)) and not tuple_as_lists:
                return False
            return all(validate(value[i], rule[i]) for i in range(len(rule)))
        elif isinstance(rule, dict):  # Dictionary with specific structure
            if not isinstance(value, dict):
                return False
            for key_rule, val_rule in rule.items():
                if isinstance(key_rule, type):  # Dynamic keys (e.g., str)
                    if not all(isinstance(k, key_rule) and validate(v, val_rule) for k, v in value.items()):
                        return False
                elif key_rule not in value or not validate(value[key_rule], val_rule):
                    return False
            return True
        else:
            return False

    for key, key_rule in rules.items():
        if key not in target or not validate(target[key], key_rule):
            print(f"Validation failed for key '{key}': {target.get(key)}")
            return False
    return True


def encode_str_or_int_iterable(str_iter: _a.Iterable[str | int]) -> bytes:
    """
    Encodes an iterable of strings and integers into a byte sequence.

    This function uses a variable-length encoding format for compact representation.

    Args:
        str_iter (Iterable[str | int]):
            An iterable containing strings and/or integers to be encoded.

    Returns:
        bytes:
            The encoded byte sequence.
    """
    output = b""
    for item in str_iter:
        if isinstance(item, str):
            output += get_variable_bytes_like(item.encode("utf-8"))
        else:
            output += get_variable_bytes_like(encode_integer(item))
    return output


def _serialize_to_json(serialisation_target: DCGDictT) -> bytes:
    return json.dumps(serialisation_target, indent=4).encode("utf-8")
def _serialize_to_yaml(serialisation_target: DCGDictT) -> bytes:
    dump: _ty.Any = yaml.safe_dump(serialisation_target, default_flow_style=False)  # Will return a str if no stream is passed
    if not isinstance(dump, str):
        raise RuntimeError("Yaml Dump did not result in str")
    return dump.encode("utf-8")
def _serialize_to_binary(serialisation_target: DCGDictT) -> bytes:
    name: bytes = serialisation_target["name"].encode("utf-8")  # type: ignore
    author: bytes = serialisation_target["author"].encode("utf-8")  # type: ignore
    token_lsts: list[list[str]] = serialisation_target["token_lsts"]  # type: ignore
    is_custom_token_lst: list[bool] = serialisation_target["is_custom_token_lst"]  # type: ignore
    abs_transition_idxs: list[int] = serialisation_target["abs_transition_idxs"]  # type: ignore
    types: dict[str, str] = serialisation_target["types"]  # type: ignore
    content_root_idx: int = serialisation_target["content_root_idx"]  # type: ignore
    content: list[dict[str, str | tuple[float, float]]] = serialisation_target["content"]  # type: ignore
    content_transitions: list[tuple[tuple[int, int], tuple[str, str], list[int]]] = serialisation_target["content_transitions"]  # type: ignore
    custom_python: bytes = serialisation_target["custom_python"].encode("utf-8")  # type: ignore

    buffer = BytesIO(b"")

    buffer.write(b"BCUL")  # Header
    buffer.write(get_variable_bytes_like(name))
    buffer.write(get_variable_bytes_like(author))

    buffer.write(get_variable_bytes_like(encode_integer(len(token_lsts))))
    for lst, custom in zip(token_lsts, is_custom_token_lst):
        buffer.write(get_variable_bytes_like(encode_integer(len(lst))))
        buffer.write(get_variable_bytes_like(encode_str_or_int_iterable(lst)))
        buffer.write(b"\xff" if custom else b"\x00")

    buffer.write(get_variable_bytes_like(encode_integer(len(abs_transition_idxs))))
    buffer.write(get_variable_bytes_like(encode_str_or_int_iterable(abs_transition_idxs)))

    buffer.write(get_variable_bytes_like(encode_integer(len(types.items()))))
    for type_name, type_design in types.items():
        buffer.write(get_variable_bytes_like(type_name.encode("utf-8")))
        buffer.write(get_variable_bytes_like(type_design.encode("utf-8")))

    buffer.write(get_variable_bytes_like(encode_integer(content_root_idx)))

    buffer.write(get_variable_bytes_like(encode_integer(len(content))))
    for content_node in content:
        content_node_name: bytes = content_node["name"].encode("utf-8")  # type: ignore
        content_node_type: bytes = content_node["type"].encode("utf-8")  # type: ignore
        content_node_position: tuple[float, float] = content_node["position"]  # type: ignore
        content_node_background_color: bytes = content_node["background_color"].encode("utf-8")  # type: ignore

        buffer.write(get_variable_bytes_like(content_node_name))
        buffer.write(get_variable_bytes_like(content_node_type))
        buffer.write(encode_float(content_node_position[0], "double"))
        buffer.write(encode_float(content_node_position[1], "double"))

        buffer.write(get_variable_bytes_like(content_node_background_color))

    buffer.write(get_variable_bytes_like(encode_integer(len(content_transitions))))
    for ((from_idx, to_idx), (from_side, to_side), transition_pattern) in content_transitions:
        buffer.write(get_variable_bytes_like(encode_integer(from_idx)))
        buffer.write(get_variable_bytes_like(encode_integer(to_idx)))
        buffer.write(ord(from_side).to_bytes(1, "big"))
        buffer.write(ord(to_side).to_bytes(1, "big"))
        buffer.write(get_variable_bytes_like(encode_str_or_int_iterable(transition_pattern)))

    buffer.write(get_variable_bytes_like(custom_python))
    return buffer.getvalue()


def serialize(
        automaton: IUiAutomaton, custom_python: str = "",
        format_: _ty.Literal["json", "yaml", "binary"] = "json"
    ) -> bytes:
    """TBA"""
    dcg_dict: DCGDictT = {
        "name": automaton.get_name(),
        "author": automaton.get_author(),
        "token_lsts": automaton.get_token_lists(),
        "is_custom_token_lst": automaton.get_is_changeable_token_list(),
        "abs_transition_idxs": automaton.get_transition_pattern(),
        "types": automaton.get_state_types_with_design(),
	    "content_root_idx": -1,
        "content": [],
        "content_transitions": [],
        "custom_python": custom_python
    }
    content_root: IUiState = next(iter(automaton.get_states()))  # automaton.get_start_state()
    counted_nodes: dict[IUiState, int] = {content_root: 0}
    stack: Queue[IUiState] = Queue(maxsize=100)  # Stack for traversal
    stack.put(content_root)
    nodes_lst: list[dict[str, str | list[tuple[int, list[int]]]]] = dcg_dict["content"]  # type: ignore # List is the same object
    nodes_lst.append({
        "name": content_root.get_display_text(),
        "type": content_root.get_type(),
        "position": content_root.get_position(),
        "background_color": content_root.get_colour()
    })
    transition_tokens: list[list[str]] = [
        dcg_dict["token_lsts"][i]  # type: ignore
        for i in dcg_dict["abs_transition_idxs"]  # type: ignore
    ]

    while not stack.empty():
        current_node = stack.get()
        current_idx = counted_nodes[current_node]

        if current_node == automaton.get_start_state():
            dcg_dict["content_root_idx"] = current_idx
        # TODO: Fix when there is a better way to find transitions
        _found_transitions: list[IUiTransition] = [x for x in automaton.get_transitions()
                                                   if x.get_from_state() == current_node]
        for transition in _found_transitions:
            connected_node: IUiState = transition.get_to_state()
            if connected_node not in counted_nodes:  # Assign a new index to the connected node
                new_idx: int = len(nodes_lst)
                counted_nodes[connected_node] = new_idx
                # Add the connected node to the nodes list
                nodes_lst.append({
                    "name": connected_node.get_display_text(),
                    "type": connected_node.get_type(),
                    "position": connected_node.get_position(),
                    "background_color": connected_node.get_colour()
                })
                stack.put(connected_node)  # Push the connected node onto the stack
            # Append the connection using the index of the connected node
            dcg_dict["content_transitions"].append(  # type: ignore
                (  # type: ignore
                    (current_idx, counted_nodes[connected_node]),
                    (transition.get_from_state_connecting_point(), transition.get_to_state_connecting_point()),
                    [transition_tokens[i].index(x[0])
                     for i, x in enumerate(transition.get_condition())]
                )
            )
    if not _verify_dcg_dict(dcg_dict):
        raise RuntimeError("DCG Dict could not be verified")
    return {
        "json": _serialize_to_json,
        "yaml": _serialize_to_yaml,
        "binary": _serialize_to_binary
    }[format_](dcg_dict)


def decode_str_iterable(bytes_like: bytes, length: int) -> list[str]:
    """
    Decodes a byte sequence into a list of strings or integers.

    The decoding process respects the structure defined by the representative lists.

    Args:
        bytes_like (bytes):
            The byte sequence to be decoded.

    Returns:
        list[str]:
            A list of decoded strings and integers.
    """
    output: list[str] = []
    io = BytesIO(bytes_like)
    for _ in range(length):
        output.append(read_variable_bytes_like(io).decode("utf-8"))
    return output
def decode_int_iterable(bytes_like: bytes, length: int) -> list[int]:
    """
    Decodes a byte sequence into a list of strings or integers.

    The decoding process respects the structure defined by the representative lists.

    Args:
        bytes_like (bytes):
            The byte sequence to be decoded.

    Returns:
        list[int]:
            A list of decoded strings and integers.
    """
    output: list[int] = []
    io = BytesIO(bytes_like)
    for _ in range(length):
        output.append(decode_integer(read_variable_bytes_like(io)))
    return output



def _deserialize_from_json(bytes_like: bytes) -> DCGDictT:
    obj: _ty.Any = json.loads(bytes_like.decode("utf-8"))
    if not isinstance(obj, dict):
        raise RuntimeError("Loaded json object is not in the right format")
    return obj
def _deserialize_from_yaml(bytes_like: bytes) -> DCGDictT:
    obj: _ty.Any = yaml.safe_load(StringIO(bytes_like.decode("utf-8")))
    if not isinstance(obj, dict):
        raise RuntimeError("Loaded yaml object is not in the right format")
    return obj
def _deserialize_from_binary(bytes_like: bytes) -> DCGDictT:
    reader = BytesIO(bytes_like)
    header = reader.read(4)
    if header != b"BCUL":
        raise RuntimeError(f"Input file has wrong header, is '{header}' instead of b'BCUL'")

    name: str = read_variable_bytes_like(reader).decode("utf-8")
    author: str = read_variable_bytes_like(reader).decode("utf-8")
    token_lst_len: int = decode_integer(read_variable_bytes_like(reader))
    token_lsts: list[list[str]] = []
    is_custom_token_lst: list[bool] = []

    for i in range(token_lst_len):
        lst_len: int = decode_integer(read_variable_bytes_like(reader))
        lst: list[str] = decode_str_iterable(read_variable_bytes_like(reader), lst_len)
        token_lsts.append(lst)
        is_custom_token_lst.append(reader.read(1) == b"\xff")

    abs_transition_len: int = decode_integer(read_variable_bytes_like(reader))
    abs_transition_idxs: list[int] = decode_int_iterable(read_variable_bytes_like(reader), abs_transition_len)

    items_len: int = decode_integer(read_variable_bytes_like(reader))
    types: dict[str, str] = {}
    for j in range(items_len):
        type_name: str = read_variable_bytes_like(reader).decode("utf-8")
        type_design: str = read_variable_bytes_like(reader).decode("utf-8")
        types[type_name] = type_design

    content_root_idx: int = decode_integer(read_variable_bytes_like(reader))

    content_len: int = decode_integer(read_variable_bytes_like(reader))
    content: list[dict[str, str | tuple[float, float]]] = []
    for n in range(content_len):
        node_name: str = read_variable_bytes_like(reader).decode("utf-8")
        node_type: str = read_variable_bytes_like(reader).decode("utf-8")
        node_position: tuple[float, float] = (
            decode_float(reader.read(8), "double"),
            decode_float(reader.read(8), "double")
        )
        node_background_color: str = read_variable_bytes_like(reader).decode("utf-8")
        content.append({
                "name": node_name,
                "type": node_type,
                "position": node_position,
                "background_color": node_background_color
        })

    transitions_len: int = decode_integer(read_variable_bytes_like(reader))
    transitions: list[tuple[tuple[int, int], tuple[str, str], list[int]]] = []
    for l in range(transitions_len):
        from_idx: int = decode_integer(read_variable_bytes_like(reader))
        to_idx: int = decode_integer(read_variable_bytes_like(reader))
        from_side: str = chr(int.from_bytes(reader.read(1)))
        to_side: str = chr(int.from_bytes(reader.read(1)))
        transition_pattern: list[int] = decode_int_iterable(read_variable_bytes_like(reader), len(abs_transition_idxs))
        transitions.append(((from_idx, to_idx), (from_side, to_side), transition_pattern))

    custom_python: str = read_variable_bytes_like(reader).decode("utf-8")
    return {
        "name": name,
        "author": author,
        "token_lsts": token_lsts,
        "is_custom_token_lst": is_custom_token_lst,
        "abs_transition_idxs": abs_transition_idxs,
        "types": types,
        "content_root_idx": content_root_idx,
        "content": content,
        "content_transitions": transitions,
        "custom_python": custom_python
    }


def deserialize(bytes_like: bytes,
                format_: _ty.Literal["json", "yaml", "binary"] = "json") -> UiAutomaton:
    """TBA"""
    dcg_dict: DCGDictT = {"json": _deserialize_from_json,
                          "yaml": _deserialize_from_yaml,
                          "binary": _deserialize_from_binary}[format_](bytes_like)
    if not _verify_dcg_dict(dcg_dict, tuple_as_lists=True):
        raise RuntimeError("DCG Dict could not be verified")

    name: str = dcg_dict["name"]  # type: ignore
    author: str = dcg_dict["author"]  # type: ignore
    token_lsts: list[list[str]] = dcg_dict["token_lsts"]  # type: ignore
    is_custom_token_lst: list[bool] = dcg_dict["is_custom_token_lst"]  # type: ignore
    abs_transition_idxs: list[int] = dcg_dict["abs_transition_idxs"]  # type: ignore
    types: dict[str, str] = dcg_dict["types"]  # type: ignore
    content_root_idx: int = dcg_dict["content_root_idx"]  # type: ignore
    content: list[dict[str, str | tuple[float, float]]] = dcg_dict["content"]  # type: ignore
    content_transitions: list[tuple[tuple[int, int], tuple[str, str], list[int]]] = dcg_dict["content_transitions"]  # type: ignore
    custom_python: str = dcg_dict["custom_python"]  # type: ignore
    transition_tokens: list[list[str]] = [
        dcg_dict["token_lsts"][i]  # type: ignore
        for i in dcg_dict["abs_transition_idxs"]  # type: ignore
    ]

    automaton: UiAutomaton = UiAutomaton(name, author, types)
    automaton.set_token_lists(token_lsts)
    automaton.set_is_changeable_token_list(is_custom_token_lst)
    automaton.set_transition_pattern(abs_transition_idxs)

    node_lookup_dict: dict[int, UiState] = {}

    for i, node in enumerate(content):
        node_name: str = node["name"]  # type: ignore
        node_type: str = node["type"]  # type: ignore
        node_position: tuple[float, float] = tuple(node["position"])  # type: ignore
        node_background_color: str = node["background_color"]  # type: ignore

        node_obj: UiState = UiState(node_background_color, node_position, node_name,
                                     node_type)
        node_lookup_dict[i] = node_obj
        automaton.add_state(node_obj)
        if i == content_root_idx:
            automaton.set_start_state(node_obj)

    for transition in content_transitions:
        ((from_idx, to_idx), (from_side, to_side), transition_pattern) = transition
        transition_obj: IUiTransition = UiTransition(
            node_lookup_dict[from_idx],
            from_side,
            node_lookup_dict[to_idx],
            to_side,
            [transition_tokens[i][j]
             for i, j in zip(abs_transition_idxs, transition_pattern)]
        )
        automaton.add_transition(transition_obj)
    return automaton


auto = UiAutomaton("DFA", "Griesbert", {"default": "..."})
auto.set_token_lists([["X", "y"], ["y"]])
auto.set_is_changeable_token_list([False, False])
auto.set_transition_pattern([0, 1])
dis_state = UiState("", (1.0, 2.0), "DIS", "default")
dio_state = UiState("", (2.0, 1.0), "DIO", "default")
auto.set_start_state(dis_state)
auto.add_state(dis_state)
auto.add_state(dio_state)
auto.add_transition(UiTransition(dis_state, "n", dio_state, "s", ["X", "y"]))
auto.add_transition(UiTransition(dio_state, "s", dis_state, "n", ["y", "y"]))

seri = serialize(auto, "", format_="binary")
print(seri)
auto2 = deserialize(seri, "binary")
print("Name: ", auto.get_name() == auto2.get_name())
print("States: ", auto.get_states() == auto2.get_states())
print("Transitions: ", auto.get_transitions() == auto2.get_transitions())
print("Start States: ", auto.get_start_state() == auto2.get_start_state())
print("Types: ", auto.get_state_types_with_design() == auto2.get_state_types_with_design())
print("Overall: ", auto == auto2)
exit()
