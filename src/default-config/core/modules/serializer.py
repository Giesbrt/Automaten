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


DCGDictT = dict[str, str  # name, author, uuid, custom_python
                     | list[list[str]]  # token_lsts
                     | list[bool]  # is_custom_lst
                     | list[int]  # abs_transition_idxs
                     | dict[str, dict[str, str]]  # types
                     | int
                     | list[dict[
                                 str, str
                                      | tuple[float, float]
                                      | list[tuple[int, list[int]]]
                                ]
                     ]  # content
]


def _verify_dcg_dict(target: dict[str, _ty.Any]) -> bool:
    """Verifies the given dictionary matches the specified rules."""
    rules = {  # Validation rules
        "name": str,
        "author": str,
        "uuid": str,
        "token_lsts": [[str]],  # list[list[str]]
        "is_custom_token_lst": [bool],  # list[bool]
        "abs_transition_idxs": [int],  # list[int]
        "types": {
            str: {
                "design": str
            }
        },
        "content_root_idx": int,
        "content": [
            {
                "name": str,
                "type": str,
                "position": (float, float),  # tuple[float, float]
                "transitions": [(int, [int])],  # list[tuple[int, list[int]]]
                "background_color": str,
            }
        ],
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
            if not isinstance(value, tuple) or len(value) != len(rule):
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
    uuid: bytes = serialisation_target["uuid"].encode("utf-8")  # type: ignore
    token_lsts: list[list[str]] = serialisation_target["token_lsts"]  # type: ignore
    is_custom_token_lst: list[bool] = serialisation_target["is_custom_token_lst"]  # type: ignore
    abs_transition_idxs: list[int] = serialisation_target["abs_transition_idxs"]  # type: ignore
    types: dict[str, dict[str, str]] = serialisation_target["types"]  # type: ignore
    content_root_idx: int = serialisation_target["content_root_idx"]  # type: ignore
    content: list[dict[str, str | list[tuple[int, list[int]]]]] = serialisation_target["content"]  # type: ignore
    custom_python: bytes = serialisation_target["custom_python"].encode("utf-8")  # type: ignore

    buffer = BytesIO(b"")

    buffer.write(b"BCUL")  # Header
    buffer.write(get_variable_bytes_like(name))
    buffer.write(get_variable_bytes_like(author))
    buffer.write(get_variable_bytes_like(uuid))

    buffer.write(get_variable_bytes_like(encode_integer(len(token_lsts))))
    for lst, custom in zip(token_lsts, is_custom_token_lst):
        buffer.write(get_variable_bytes_like(encode_integer(len(lst))))
        buffer.write(get_variable_bytes_like(encode_str_or_int_iterable(lst)))
        buffer.write(b"\xff" if custom else b"\x00")

    buffer.write(get_variable_bytes_like(encode_integer(len(abs_transition_idxs))))
    buffer.write(get_variable_bytes_like(encode_str_or_int_iterable(abs_transition_idxs)))

    for type_name, type_design in types.items():
        buffer.write(get_variable_bytes_like(type_name.encode("utf-8")))
        buffer.write(get_variable_bytes_like(type_design["design"].encode("utf-8")))

    buffer.write(get_variable_bytes_like(encode_integer(content_root_idx)))

    for content_node in content:
        content_node_name: bytes = content_node["name"].encode("utf-8")  # type: ignore
        content_node_type: bytes = content_node["type"].encode("utf-8")  # type: ignore
        content_node_position: tuple[float, float] = content_node["position"]  # type: ignore
        content_node_transitions: list[tuple[int, list[int]]] = content_node["transitions"]  # type: ignore
        content_node_background_color: bytes = content_node["background_color"].encode("utf-8")  # type: ignore

        buffer.write(get_variable_bytes_like(content_node_name))
        buffer.write(get_variable_bytes_like(content_node_type))
        buffer.write(encode_float(content_node_position[0], "double"))
        buffer.write(encode_float(content_node_position[1], "double"))

        buffer.write(get_variable_bytes_like(encode_integer(len(content_node_transitions))))
        for transition_idx, abs_idxs in content_node_transitions:
            buffer.write(get_variable_bytes_like(encode_integer(transition_idx)))
            buffer.write(get_variable_bytes_like(encode_str_or_int_iterable(abs_idxs)))

        buffer.write(get_variable_bytes_like(content_node_background_color))

    buffer.write(get_variable_bytes_like(custom_python))
    return buffer.getvalue()


def serialize(
        automaton_name: str, uuid: str, types: dict[str, dict[str, str]],
        automaton: IUiAutomaton, custom_python: str = "",
        format_: _ty.Literal["json", "yaml", "binary"] = "json"
    ) -> bytes:
    """TBA"""
    # TODO: Remove all arguments that can be gotten from automaton
    dcg_dict: DCGDictT = {
        "name": automaton_name,
        "author": automaton.get_author(),
        "uuid": uuid,
        "token_lsts": automaton.get_token_lists(),
        "is_custom_token_lst": automaton.get_changeable_token_lists(),  # TODO: Please use a better name
        "abs_transition_idxs": automaton.get_transition_pattern(),
        "types": types,
	    "content_root_idx": 0,
        "content": [],
        "custom_python": custom_python
    }
    # TODO: Fix when we can get the actual content root
    content_root: IUiState = next(iter(automaton.get_states()))
    counted_nodes: dict[IUiState, int] = {content_root: 0}
    stack: Queue[IUiState] = Queue(maxsize=100)  # Stack for traversal
    stack.put(content_root)
    nodes_lst: list[dict[str, str | list[tuple[int, list[int]]]]] = dcg_dict["content"]  # type: ignore # List is the same object
    nodes_lst.append({
        "name": content_root.get_display_text(),
        "type": content_root.get_type(),
        "position": content_root.get_position(),
        "transitions": [],
        "background_color": content_root.get_colour()
    })
    transition_tokens: list[list[str]] = [
        dcg_dict["token_lsts"][i]  # type: ignore
        for i in dcg_dict["abs_transition_idxs"]]  # type: ignore

    while not stack.empty():
        current_node = stack.get()
        current_idx = counted_nodes[current_node]
        current_data = nodes_lst[current_idx]
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
                    "transitions": [],
                    "background_color": connected_node.get_colour()
                })
                stack.put(connected_node)  # Push the connected node onto the stack
            # Append the connection using the index of the connected node
            current_data["transitions"].append(  # type: ignore
                (counted_nodes[connected_node], [transition_tokens[i].index(x[0])
                                                 for i, x in enumerate(transition.get_condition())])
            )
    if not _verify_dcg_dict(dcg_dict):
        raise RuntimeError("DCG Dict could not be verified")
    return {
        "json": _serialize_to_json,
        "yaml": _serialize_to_yaml,
        "binary": _serialize_to_binary
    }[format_](dcg_dict)


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
    raise NotImplementedError("The bytes method is not implemented yet")
    return {}


def deserialize_from(bytes_like: bytes) -> IUiAutomaton:
    """TBA"""
    raise NotImplementedError("The bytes method is not implemented yet")
    if not _verify_dcg_dict(dcg_dict):
        raise RuntimeError("DCG Dict could not be verified")
