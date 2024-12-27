"""Here we can expose what we want to be used outside"""
import os
import re

from PySide6.QtWidgets import QWidget

from aplustools.io.fileio import os_open

from ._main import MainWindow

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts


def assign_object_names_iterative(parent: QWidget, prefix: str = "", exclude_primitives: bool = True) -> None:
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


class Theme:
    loaded_themes: list[_ty.Self] = []

    def __init__(self, author: str, theme_name: str, theme_str: str, base: str | None, placeholders: list[str],
                 compatible_styling: str | None, load_styles_for: str,
                 inherit_extend_from: tuple[str | None, str | None]) -> None:
        self._author: str = author
        self._theme_name: str = theme_name
        self._theme_str: str = theme_str
        self._base: str | None = base
        self._placeholders: list[str] = placeholders
        self._compatible_styling: str | None = compatible_styling
        self._load_styles_for: str = load_styles_for
        self._inherit_extend_from: tuple[str, str] = inherit_extend_from

    @classmethod
    def load_from_file(cls, filepath: str) -> _ty.Self:
        with os_open(filepath, "r") as f:
            content = f.read()
        filename = os.path.basename(filepath)
        return cls.load_from_content(filename, content.decode("utf-8"))

    @classmethod
    def load_from_content(cls, filename: str, content: str) -> _ty.Self:
        if "_" in filename and filename.endswith(".th"):
            author, theme_name_ext = filename.split("_", 1)
            theme_name = theme_name_ext[:-3]  # Remove ".th"
        else:
            raise ValueError(f"Invalid .th file name: {filename}")

        cleaned_content = re.sub(r"//.*?$|/\*.*?\*/", "", content, flags=re.DOTALL | re.MULTILINE).strip() + "\n"
        if cleaned_content == "":
            raise ValueError("The .th file is empty.")

        mode: _ty.Literal["extending", "inheriting"] | None = None
        from_theme: str | None = None
        if cleaned_content.startswith("inheriting") or cleaned_content.startswith("extending"):
            mode_line_s, cleaned_content = cleaned_content.split(";", maxsplit=1)
            mode, from_theme = mode_line_s.split(" ", 1)

        config_line, other_content = cleaned_content.lstrip().split("\n", maxsplit=1)
        style_metadata = config_line.split("/")
        # print("Config Line:  ", repr(config_line), style_metadata)
        if len(style_metadata) < 3:
            raise ValueError(f"The config line of the .th file is invalid: '{config_line}'")
        base_app_style = style_metadata[0] if len(style_metadata[0].strip()) > 0 else None
        compatible_styling = style_metadata[1] if len(style_metadata[1].strip()) > 0 else None
        style_precautions = style_metadata[2] if len(style_metadata[2].strip()) > 0 else None
        print(f"Mode+Style ({author}::{theme_name}): '{mode} {from_theme}'; '{base_app_style, compatible_styling, style_precautions}'")

        lines = other_content.split("\n")

        qss: str = ""
        raw_placeholders: list[str] = []
        for i, line in enumerate(lines):
            if line.startswith("ph:"):
                raw_placeholders.extend(line.removeprefix("ph:").split(";"))
                raw_placeholders.extend(''.join(lines[i+1:]).split(";"))
            else:
                qss += line

        placeholders: list[str] = []
        for raw_placeholder in raw_placeholders:
            placeholder = raw_placeholder.strip()
            if placeholder != "":
                placeholders.append(placeholder)
        # TODO: add other attributes more clearly
        load_styles_for = from_theme if style_precautions == "nocolor" and from_theme is not None else theme_name
        inherit_extend = (mode, from_theme)
        return cls(author, theme_name, qss.strip(), base_app_style, placeholders, compatible_styling, load_styles_for,
                   inherit_extend)

    def __eq__(self, other: str) -> bool:
        return f"{self._author}/{self._theme_name}" == other

    def __repr__(self) -> str:
        return (f"Theme(author={self._author}, theme_name={self._theme_name}, theme_str={self._theme_str[:10]}, "
                f"base={self._base}, placeholder={self._placeholders}, compatible_styling={self._compatible_styling}, "
                f"load_styles_for={self._load_styles_for}, inherit_extend_from={self._inherit_extend_from})")


class Style:
    loaded_styles: list[_ty.Self] = []

    def __init__(self, style_name: str, for_paths: list[str], parameters: list[str]) -> None:
        self._style_name: str = style_name
        self._for_paths: list[str] = for_paths
        self._parameters: list[str] = parameters

    @classmethod
    def load_from_file(cls, filepath: str) -> _ty.Self:
        with os_open(filepath, "r") as f:
            content = f.read()
        filename = os.path.basename(filepath)
        return cls.load_from_content(filename, content.decode("utf-8"))

    @staticmethod
    def _parse_paths(input_str: str) -> list[str]:
        # Step 1: Extract the part after "for" and before the ";"
        match = re.match(r'for\s+(.+);', input_str.strip())
        if not match:
            raise ValueError("Input must start with 'for' and end with ';'")

        content = match.group(1).strip()

        # Step 2: Recursive function to expand curly braces
        def expand(segment):
            if "{" not in segment:
                return [segment]

            # Find the first set of braces
            start = segment.index("{")
            end = segment.index("}", start)

            # Before the braces, the braces content, and after the braces
            prefix = segment[:start]
            brace_content = segment[start + 1:end]
            suffix = segment[end + 1:]

            # Expand the content inside the braces
            options = brace_content.split(",")

            # Recursively expand the rest of the string
            expanded_suffixes = expand(suffix)

            # Combine each option with the expanded suffixes
            result = []
            for option in options:
                for expanded_suffix in expanded_suffixes:
                    result.append(f"{prefix}{option.strip()}{expanded_suffix}")
            return result

        # Step 3: Call the recursive function on the cleaned-up string
        return expand(content)

    @classmethod
    def load_from_content(cls, filename: str, content: str) -> _ty.Self:
        if filename.endswith(".st"):
            style_name = filename[:-3].replace("_", " ").title()
        else:
            raise ValueError(f"Invalid .st file name: {filename}")

        translation_table = str.maketrans("", "", "\n\t")
        cleaned_content = re.sub(r"//.*?$|/\*.*?\*/", "", content, flags=re.DOTALL | re.MULTILINE)
        trans_content = cleaned_content.translate(translation_table)
        if trans_content == "":
            raise ValueError("The .st file is empty.")

        for_line, other_content = trans_content.split(";", maxsplit=1)
        for_paths = cls._parse_paths(for_line + ";")

        parameters: list[str] = [x.strip() for x in other_content.split(";")]

        return cls(style_name, for_paths, parameters)

    def __repr__(self) -> str:
        return f"Style(style_name={self._style_name}, for_paths={self._for_paths}, parameters={self._parameters})"
