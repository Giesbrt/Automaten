"""TBA"""
from collections import deque
from io import BytesIO
import json

# aplustools
from aplustools.data.bintools import (get_variable_bytes_like, encode_float, encode_integer, read_variable_bytes_like,
                                      decode_integer, decode_float)
from aplustools.io.fileio import os_open

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

    def __init__(self, position: tuple[float, float], connections: set[tuple[tuple[int | str, ...], _ty.Self]] | None = None, *_,
                 root: bool = False, extra_info: bytes = b"") -> None:
        self.position: tuple[float, float] = position
        self.connections: set[tuple[tuple[int | str, ...], _ty.Self]] = connections or set()  # Max conns = len(sum)
        self.extra_info: bytes = extra_info  # idk would mean we limit ourselves
        self.root: bool = root

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
        self.connections.add((transition, node))

    def __hash__(self) -> int:
        return hash(repr(self))

    def __repr__(self) -> str:
        return f"Node(position={self.position}, connections={self.connections}, root={self.root})"


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
        stack: deque[DCGNode] = deque()
        stack.append(content)
        counter: int = 1
        counted_nodes: dict[DCGNode, int] = {content: 0}

        while stack:
            item: DCGNode = stack.popleft()
            f.write(encode_float(item.position[0], "double"))
            f.write(encode_float(item.position[1], "double"))

            f.write(get_variable_bytes_like(encode_integer(len(item.connections))))
            for (transition, node) in item.connections:
                if node not in counted_nodes:
                    stack.append(node)
                    counted_nodes[node] = counter
                    f.write(get_variable_bytes_like(encode_str_or_int_iterable(transition)))
                    f.write(get_variable_bytes_like(encode_integer(counter)))
                    counter += 1
                else:
                    f.write(get_variable_bytes_like(encode_str_or_int_iterable(transition)))
                    f.write(get_variable_bytes_like(encode_integer(counted_nodes[node])))

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
        stack: deque[DCGNode] = deque()  # Stack for traversal
        stack.append(node)

        counted_nodes: dict[DCGNode, int] = {}  # Mapping of nodes to their indices
        counted_nodes[node] = 0

        # Add the root node to the list
        nodes_list.append({
            "position": node.position,
            "connections": [],
            "extra_info": node.extra_info.decode('utf-8', errors='ignore'),  # Decode bytes for JSON compatibility
            "root": node.root,
        })

        while stack:
            current_node = stack.pop()
            current_idx = counted_nodes[current_node]  # Get the index of the current node
            current_data = nodes_list[current_idx]

            for transition, connected_node in current_node.connections:
                if connected_node not in counted_nodes:
                    # Assign a new index to the connected node
                    new_idx = len(nodes_list)
                    counted_nodes[connected_node] = new_idx

                    # Add the connected node to the nodes list
                    nodes_list.append({
                        "position": connected_node.position,
                        "connections": [],
                        "extra_info": connected_node.extra_info.decode('utf-8', errors='ignore'),
                        "root": connected_node.root,
                    })

                    # Push the connected node onto the stack
                    stack.append(connected_node)

                # Append the connection using the index of the connected node
                current_data["connections"].append({
                    "transition": transition,
                    "node_idx": counted_nodes[connected_node],  # Reference by index
                })
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
        counter: int = 0
        counted_nodes: dict[int, DCGNode] = {}

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
            if root:
                root_node = node
            counted_nodes[counter] = node
            counter += 1
        for (_, node) in counted_nodes.items():
            new_connections: set[tuple[tuple[str | int, ...], DCGNode]] = set()
            for (trans, node_idx) in node.connections:
                new_connections.add((trans, counted_nodes[node_idx]))
            node.connections = new_connections
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

    # Create placeholder nodes to fill connections later
    counted_nodes: dict[int, DCGNode] = {
        idx: DCGNode(
            tuple(node_data["position"]),
            set(),
            extra_info=node_data["extra_info"].encode("utf-8"),
            root=node_data["root"]
        )
        for idx, node_data in enumerate(nodes_list)
    }

    # Populate connections
    for idx, node_data in enumerate(nodes_list):
        current_node = counted_nodes[idx]
        new_connections: set[tuple[tuple[str, ...], DCGNode]] = set()

        for connection in node_data["connections"]:
            transition = tuple(connection["transition"])
            connected_node = counted_nodes[connection["node_idx"]]
            new_connections.add((transition, connected_node))

        current_node.connections = new_connections

    # Find and return the root node
    root_node = next(node for node in counted_nodes.values() if node.root)
    return root_node


if __name__ == "__main__":
    root = DCGNode((102.0, 22.0), root=True)
    activate_dcg_node_root(root, (["a", "b", "c", "d", "e"],))
    other_node = DCGNode((1002.1, 2289.22), {((3,), root)}, extra_info=b"is_end")
    root.tie_to((2,), other_node)
    serialize_dcg_to_file("./test.bin", root)
    dump_dcg_to_file("./test.json", root)
    print(root)
    print(deserialize_dcg_from_file("./test.bin"))
    print(load_dcg_from_json("./test.json"))
