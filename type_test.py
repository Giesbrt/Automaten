from typing import Any, Literal, get_origin, get_args, Tuple
from PyQt5.QtGui import QPen, QColor

def is_of_type(value: Any, expected_type: Any) -> bool:
    """Recursively checks if a value matches the given type annotation."""
    origin = get_origin(expected_type)
    args = get_args(expected_type)

    if origin is None:  # Base case: check direct instance
        return isinstance(value, expected_type)

    if origin is tuple:
        if not isinstance(value, tuple) or len(value) != len(args):
            return False
        return all(is_of_type(v, t) for v, t in zip(value, args))

    if origin is Literal:
        return value in args  # Ensure it's one of the allowed literal values

    return isinstance(value, expected_type)  # Fallback

# Define the general type
GeneralType = Tuple[QPen, QColor | None, str, Tuple[Any, ...]]

# Define the specific type
SpecificType = Tuple[QPen, None, Literal["line"], Tuple[float, float, float, float]]

# Example values
value1 = (QPen(), None, "line", (1.0, 2.0, 3.0, 4.0))
value2 = (QPen(), None, "circle", (1.0, 2.0, 3.0, 4.0))  # Wrong type (third element)

# Check against the specific type
print(is_of_type(value1, SpecificType))  # True
print(is_of_type(value2, SpecificType))  # False
