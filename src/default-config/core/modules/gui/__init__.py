"""Here we can expose what we want to be used outside"""
from PySide6.QtWidgets import QWidget

from ._main import MainWindow


def assign_object_names_iterative(parent: QWidget, prefix: str = "", exclude_primitives: bool = True,
                                  name_map: dict | None = None) -> None:
    """Assign object names iteratively to children using a hierarchy."""
    stack = [(parent, prefix)]  # Stack to manage widgets and their prefixes

    # List of primitive classes to exclude if `exclude_primitives` is True
    primitives: tuple = ()

    while stack:
        current_parent, current_prefix = stack.pop()

        parent_var_names = {
            obj: name
            for name, obj in vars(current_parent).items()
            if isinstance(obj, current_parent.__class__) or obj in current_parent.children()
        }

        for child in current_parent.children():
            # Construct the object name using colons for hierarchy
            var_name = parent_var_names.get(child, child.__class__.__name__)
            object_name = f"{current_prefix}-{var_name}" if current_prefix else var_name

            # Assign the object name
            child.setObjectName(object_name)
            print(object_name)

            # Check if we should process this child further
            if not exclude_primitives or not isinstance(child, primitives):
                stack.append((child, object_name))
