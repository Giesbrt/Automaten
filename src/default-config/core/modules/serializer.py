"""TBA"""
from collections import deque
from io import BytesIO
import json

# aplustools
from aplustools.data.bintools import (get_variable_bytes_like, encode_float, encode_integer, read_variable_bytes_like,
                                      decode_integer, decode_float)
from aplustools.io.fileio import os_open
from aplustools.io.env import auto_repr

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts


class DCGNode:
    """
    Represents a node in a directed cyclic graph (DCG).

    A DCG node is defined by its spatial position, connections to other nodes, and optional metadata. It may also have
    a specific role as a root node in the graph hierarchy.

    Attributes:
        position (tuple[float, float]):
            The 2D coordinates of the node in the graph.

        connections (set[tuple[tuple[int | str, ...], DCGNode]]):
            A set of connections (edges) originating from this node. Each connection is a tuple comprising:
            - A transition (tuple[int | str, ...]): Metadata or labels describing the transition.
            - A reference to another DCGNode instance representing the destination of the connection.
            Defaults to an empty set if not provided.

        extra_info (bytes):
            Optional additional metadata or information about the node, stored as a bytes object.
            Defaults to an empty bytes object.

        root (bool):
            Specifies if this node acts as the root of the graph. Defaults to False.
    """
    representative_lists: tuple[list[str] | None, ...]
    node_list: list[_ty.Self] = []

    def __init__(self, position: tuple[float, float], connections: set[tuple[tuple[int | str, ...], int]] | None = None, *_,
                 root: bool = False, extra_info: bytes = b"") -> None:
        self.position: tuple[float, float] = position
        self.connections: set[tuple[tuple[int | str, ...], int]] = connections or set()  # Max conns = len(sum)
        self.extra_info: bytes = extra_info  # idk would mean we limit ourselves
        self.root: bool = root
        if root:
            self.node_list.append(self)

    def tie_to(self, transition: tuple[int | str, ...], node: _ty.Self) -> None:
        """
        Establishes a connection (edge) between this node and another node with a specified transition.

        Args:
            transition (tuple[int | str, ...]):
                Metadata or labels defining the nature of the transition.

            node (DCGNode):
                The target node to which this connection leads.

        Raises:
            RuntimeError: If the length of the transition tuple does not match the length of the representative lists,
            or if the transition violates the rules defined by the representative lists.
        """
        if len(transition) != len(self.representative_lists):
            raise RuntimeError("Transition isn't of same length as the representative lists")
        for item, lst in zip(transition, self.representative_lists):
            if isinstance(item, int) and lst is not None:
                ...
            elif isinstance(item, str) and lst is None:
                ...
            else:
                raise RuntimeError(f"Transition '{transition}' is invalid for the reprlsts {self.representative_lists}")
        self.connections.add((transition, len(self.node_list)))
        self.node_list.append(node)

    def __hash__(self) -> int:
        return hash(repr(self))
auto_repr(DCGNode, use_repr=True)


def activate_dcg_node_root(node: DCGNode, representative_lists: tuple[list[str] | None, ...]) -> None:
    """
    Activates a DCGNode as the root of the graph and assigns representative lists to it.

    Args:
        node (DCGNode):
            The node to be activated as the root. It must already be marked as a root node.

        representative_lists (tuple[list[str] | None, ...]):
            A tuple of lists representing the structure of transitions in the graph. Lists may be None to represent
            unrestricted transitions.

    Raises:
        RuntimeError: If the node is not a root node, or if any representative list is an empty list.
    """
    for lst in representative_lists:
        if lst is not None and len(lst) == 0:
            raise RuntimeError("You can't have empty lists in the representative lists")
    if not node.root:
        raise RuntimeError("DCGNode needs to be the root node to be activated")
    DCGNode.representative_lists = representative_lists


def reset_dcg_node_root(node: DCGNode) -> None:
    if not node.root:
        raise RuntimeError("DCGNode needs to be the root node to be activated")
    DCGNode.representative_lists = []
    DCGNode.node_list = []


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


def decode_str_or_int_iterable(bytes_like: bytes, repr_lsts: _a.Iterable[list[str] | None, ...]) -> list[str | int]:
    """
    Decodes a byte sequence into a list of strings or integers.

    The decoding process respects the structure defined by the representative lists.

    Args:
        bytes_like (bytes):
            The byte sequence to be decoded.

        repr_lsts (Iterable[list[str] | None, ...]):
            The structure of representative lists used to guide decoding.

    Returns:
        list[str | int]:
            A list of decoded strings and integers.
    """
    output: list[str | int] = []
    io = BytesIO(bytes_like)
    for lst in repr_lsts:
        if lst is None:
            output.append(read_variable_bytes_like(io).decode("utf-8"))
        else:
            output.append(decode_integer(read_variable_bytes_like(io)))
    return output


def serialize_dcg_to_file(output_file: str, content: DCGNode) -> None:
    """
    Serializes a DCGNode structure into a binary file format.

    The format includes metadata about the graph structure, representative lists, node positions, connections, and extra information.

    Args:
        output_file (str):
            The path to the binary output file.

        content (DCGNode):
            The root node of the DCG to serialize.
    """
    with os_open(output_file, "wb") as f:
        f.write(b"BCUL")  # Header
        f.write(get_variable_bytes_like(encode_integer(len(content.representative_lists))))
        for lst in content.representative_lists:
            if isinstance(lst, list):
                f.write(get_variable_bytes_like(encode_integer(len(lst))))
                f.write(get_variable_bytes_like(encode_str_or_int_iterable(lst)))
            else:
                f.write(get_variable_bytes_like(encode_integer(0)))
        for item in content.node_list:
            f.write(encode_float(item.position[0], "double"))
            f.write(encode_float(item.position[1], "double"))

            f.write(get_variable_bytes_like(encode_integer(len(item.connections))))

            for (transition, node_idx) in item.connections:
                f.write(get_variable_bytes_like(encode_str_or_int_iterable(transition)))
                f.write(get_variable_bytes_like(encode_integer(node_idx)))
            f.write(get_variable_bytes_like(item.extra_info))
            f.write(b"\xFF" if item.root else b"\x00")


def dump_dcg_to_file(output_file: str, node: DCGNode) -> None:
    """
    Serializes a DCGNode structure into a human-readable JSON file.

    The JSON format represents nodes as a list, where node indices are used to reference connections.

    Args:
        output_file (str):
            The path to the output JSON file.

        node (DCGNode):
            The root node of the DCG to serialize.
    """
    with os_open(output_file, "w") as f:
        nodes_list = []  # List of nodes to be serialized

        for current_node in node.node_list:
            current_data = {
                "position": current_node.position,
                "connections": [],
                "extra_info": current_node.extra_info.decode('utf-8', errors='ignore'),
                "root": current_node.root,
            }

            for transition, connected_node_idx in current_node.connections:
                # Append the connection using the index of the connected node
                current_data["connections"].append({
                    "transition": transition,
                    "node_idx": connected_node_idx,  # Reference by index
                })
            nodes_list.append(current_data)
        f.write(json.dumps(nodes_list, indent=4).encode())


def deserialize_dcg_from_file(input_file: str) -> DCGNode:
    """
    Deserializes a binary file into a DCGNode structure.

    The file must be in the specific format generated by `serialize_dcg_to_file`.

    Args:
        input_file (str):
            The path to the binary input file.

    Returns:
        DCGNode:
            The root node of the reconstructed graph.

    Raises:
        RuntimeError: If the file has an invalid header or contains corrupted data.
    """
    with os_open(input_file, "rb") as f:
        header = f.read(4)
        if header != b"BCUL":
            raise RuntimeError(f"Input file has wrong header, is '{header}' instead of b'BCUL'")
        repr_lst_length = decode_integer(read_variable_bytes_like(f))
        repr_lsts: list[list[str] | None] = []
        for _ in range(repr_lst_length):
            lst_length = decode_integer(read_variable_bytes_like(f))
            if lst_length != 0:
                repr_lsts.append(decode_str_or_int_iterable(read_variable_bytes_like(f), (None,) * lst_length))
            else:
                repr_lsts.append(None)

        current = f.tell()
        end_position = f.seek(0, f.SEEK_END)
        f.seek(current, f.SEEK_SET)
        root_node = None
        while f.tell() < end_position:
            x = decode_float(f.read(8), "double")
            y = decode_float(f.read(8), "double")

            num_of_connections = decode_integer(read_variable_bytes_like(f))
            connections: set = set()
            for _ in range(num_of_connections):
                transition = tuple(decode_str_or_int_iterable(read_variable_bytes_like(f), repr_lsts))
                tied_node_idx = decode_integer(read_variable_bytes_like(f))
                connections.add((transition, tied_node_idx))
            extra_info = read_variable_bytes_like(f)
            root = f.read(1) == b"\xFF"
            node = DCGNode((x, y), connections, extra_info=extra_info, root=root)
            DCGNode.node_list.append(node)
            if root and root_node is None:
                root_node = node
            elif root:
                raise RuntimeError("Found second root node")
        return root_node


def load_dcg_from_json(input_file: str) -> DCGNode:
    """
    Deserializes a JSON file into a DCGNode structure.

    The JSON file must follow the format generated by `dump_dcg_to_file`.

    Args:
        input_file (str):
            The path to the JSON file.

    Returns:
        DCGNode:
            The root node of the reconstructed graph.
    """
    with open(input_file, "r") as f:
        nodes_list = json.load(f)

    counted_nodes: list[DCGNode] = []
    root_node = None

    for idx, node_data in enumerate(nodes_list):
        connections = set()
        for connection in node_data["connections"]:
            transition = tuple(connection["transition"])
            connections.add((transition, connection["node_idx"]))

        counted_nodes.append(
            DCGNode(
                tuple(node_data["position"]),
                connections,
                extra_info=node_data["extra_info"].encode("utf-8"),
                root=node_data["root"]
            )
        )
        if node_data["root"] and root_node is None:
            root_node = counted_nodes[-1]
        elif node_data["root"]:
            raise RuntimeError("Found second root node")
    return root_node


if __name__ == "__main__":
    root = DCGNode((102.0, 22.0), root=True)
    activate_dcg_node_root(root, (["a", "b", "c", "d", "e"],))
    other_node = DCGNode((1002.1, 2289.22), {((3,), 0)}, extra_info=b"is_end")
    root.tie_to((2,), other_node)
    serialize_dcg_to_file("./test.bin", root)
    dump_dcg_to_file("./test.json", root)

    # There can only be one root network at a time. Could be changed but is unneeded
    print(root)
    reset_dcg_node_root(root)
    
    bin_root = deserialize_dcg_from_file("./test.bin")
    print(bin_root)
    reset_dcg_node_root(bin_root)
    
    json_root = load_dcg_from_json("./test.json")
    print(json_root)
    reset_dcg_node_root(json_root)
