"""Here we can expose what we want to be used outside"""
from string import Template, ascii_letters, digits
import os
import re

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

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


class Style:
    loaded_styles: list[_ty.Self] = []

    def __init__(self, style_name: str, for_paths: list[str], parameters: list[str],
                 palette_parameter: list[str]) -> None:
        self._style_name: str = style_name
        self._for_paths: list[str] = for_paths
        self._parameters: list[str] = parameters
        self._palette_parameter: list[str] = palette_parameter
        self.loaded_styles.append(self)

    def get_style_name(self) -> str:
        return self._style_name

    def get_parameters(self) -> list[str]:
        return self._parameters

    def get_palette_parameters(self) -> list[str]:
        return self._palette_parameter

    def get_for_paths(self) -> list[str]:
        return self._for_paths.copy()

    @classmethod
    def load_from_file(cls, filepath: str) -> _ty.Self:
        with os_open(filepath, "r") as f:
            content = f.read()
        filename = os.path.basename(filepath)
        return cls.load_from_content(filename, content.decode("utf-8"))

    @staticmethod
    def _parse_paths(input_str: str) -> list[str]:
        # Step 1: Extract the part after "for" and before the ";"
        match = re.match(r'for\s?(.+);', input_str.strip())
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
        """TBA"""
        if filename.endswith(".st"):
            style_name: str = filename[:-3].replace("_", " ").title()
        else:
            raise ValueError(f"Invalid .st file name: {filename}")

        translation_table = str.maketrans("", "", "\n\t ")
        cleaned_content: str = re.sub(r"//.*?$|/\*.*?\*/", "", content, flags=re.DOTALL | re.MULTILINE)

        if not cleaned_content.startswith("for "):
            raise RuntimeError("Style does not include for directive")

        trans_content: str = cleaned_content.translate(translation_table)
        if trans_content == "":
            raise ValueError("The .st file is empty.")

        for_line: str
        other_content: str
        for_line, other_content = trans_content.split(";", maxsplit=1)
        for_paths = cls._parse_paths(for_line + ";")

        parameters: list[str] = []
        palette_parameter: list[str] = []
        palette_part = False
        for part in other_content.split(";"):
            if not part:
                continue
            if palette_part:
                if part == "]":
                    palette_part = False
                    continue
                palette_parameter.append(part)
            elif part.startswith("QPalette["):
                palette_part = True
            else:
                parameters.append(part)

        if palette_part:
            raise RuntimeError("Unterminated QPalette declaration")

        return cls(style_name, for_paths, parameters, palette_parameter)

    def __repr__(self) -> str:
        return (f"Style(style_name={self._style_name}, for_paths={self._for_paths}, parameters={self._parameters}, "
                f"palette_parameter={self._palette_parameter})")


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
        self.loaded_themes.append(self)

    def get_theme_uid(self) -> str:
        return self._author + "::" + self._theme_name

    def get_base(self) -> str:
        return self._base

    @staticmethod
    def _find_special_sequence(s: str) -> tuple[str, str, str]:
        """
        Finds the first non-alphanumeric or non-underscore character in a string,
        collects it and all contiguous characters of the same type immediately following it,
        and returns the resulting substring.

        :param s: The input string to search.
        :return: The substring of contiguous special characters or an empty string if none found.
        """
        allowed_chars = ascii_letters + digits + '_'
        front = ""
        back = ""
        for i, char in enumerate(s):
            if char not in allowed_chars:
                special_sequence = char

                for j in range(i + 1, len(s)):
                    if s[j] not in allowed_chars:
                        special_sequence += s[j]
                    else:
                        back = s[j:]
                        break
                return front, special_sequence, back
            else:
                front += char
        return s, "", ""  # Return empty string if no special characters found

    @staticmethod
    def _to_camel_case(s: str) -> str:
        """
        Converts PascalCase or TitleCase to camelCase.

        :param s: The input string to convert.
        :return: The camel case version of the string.
        """
        if not s:
            return s
        return s[0].lower() + s[1:]

    def supports_styles(self) -> bool:
        return self._compatible_styling in ("*", "os")

    def is_compatible(self, style: Style) -> bool:
        load_st_author, load_st_theme = self._load_styles_for.split("::")
        for path in style.get_for_paths():  # TODO: Check for wildcards
            author, theme_name, styling, maybe_default, *_ = path.split("::", maxsplit=3) + [""]
            if author == load_st_author and theme_name == load_st_theme:
                return True
        return False

    def get_compatible_styles(self) -> list[Style]:
        if not self.supports_styles():
            raise RuntimeError(f"The theme '{self._theme_name}' doesn't support styles")
        compatible_styles = []
        load_st_author, load_st_theme = self._load_styles_for.split("::")
        for style in Style.loaded_styles:
            for path in style.get_for_paths():
                author, theme_name, styling, maybe_default, *_ = path.split("::", maxsplit=3) + [""]
                if author == load_st_author and theme_name == load_st_theme:
                    compatible_styles.append(style)
        return compatible_styles

    def get_compatible_style(self, name: str) -> Style | None:
        if not self.supports_styles():
            raise RuntimeError(f"The theme '{self._theme_name}' doesn't support styles")
        load_st_author, load_st_theme = self._load_styles_for.split("::")
        for style in Style.loaded_styles:
            if style.get_style_name() != name:
                continue
            for path in style.get_for_paths():
                author, theme_name, styling, maybe_default, *_ = path.split("::", maxsplit=3) + [""]
                if author == load_st_author and theme_name == load_st_theme:
                    return style

    def is_theme(self, theme_str: str) -> bool:
        return f"{self._author}::{self._theme_name}" == theme_str

    def assemble_qss_row(self) -> str:
        mode, from_theme = self._inherit_extend_from
        if mode == "inheriting":
            theme = None
            for theme in self.loaded_themes:
                if theme.is_theme(from_theme):
                    break
            if theme is None:
                raise RuntimeError(f"Unknown theme '{from_theme}'")
            return theme.assemble_qss_row() + self._theme_str
        elif mode == "extending":
            theme = None
            for theme in self.loaded_themes:
                if theme.is_theme(from_theme):
                    break
            if theme is None:
                raise RuntimeError(f"Unknown theme '{from_theme}'")
            return self._theme_str + theme.assemble_qss_row()
        elif mode is None:
            return self._theme_str
        else:
            raise RuntimeError(f"Unsupported mode '{mode}'")

    def apply_style(self, style: Style, palette: QPalette,
                    transparency_mode: _ty.Literal["none", "author", "direct", "indirect"] = "none"
                    ) -> tuple[str, QPalette]:
        # TODO: Make transparency mode, make everything better
        if transparency_mode != "none":
            raise NotImplementedError("Transparency modes are not supported yet")
        if not self.is_compatible(style):  # Remove ?
            raise RuntimeError()
        raw_qss = Template(self.assemble_qss_row())

        formatted_placeholder: dict[str, str] = {}
        if style is not None:
            for style_placeholder in style.get_parameters():  # Move style placeholders and QPalette conversion up
                front, back = [c.strip() for c in style_placeholder.split(":")]
                formatted_placeholder[front] = back
            for qpalette_placeholder in style.get_palette_parameters():
                key, val = qpalette_placeholder.split(":")
                getattr(palette, f"set{key}")(val)

        for placeholder in self._placeholders:
            front, assignment_type, end = self._find_special_sequence(placeholder)
            if assignment_type == "~=":
                if end.startswith("QPalette."):
                    color = getattr(palette, self._to_camel_case(end.removeprefix("QPalette.")))().color()
                elif end.startswith("#") and end[1:].isalnum():
                    color = end
                elif (end.startswith("rba(") or end.startswith("rgba(")) and end.endswith(")"):
                    color = end
                else:
                    color = QColor(getattr(Qt.GlobalColor, self._to_camel_case(end)))
                if not isinstance(color, str):
                    color = f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()})"
                if front not in formatted_placeholder:
                    formatted_placeholder[front] = color
            elif assignment_type == "==":
                if end.startswith("QPalette."):
                    color = getattr(palette, self._to_camel_case(end.removeprefix("QPalette.")))().color()
                elif end.startswith("#") and end[1:].isalnum():
                    color = end
                elif (end.startswith("rba(") or end.startswith("rgba(")) and end.endswith(")"):
                    color = end
                else:
                    color = QColor(getattr(Qt.GlobalColor, self._to_camel_case(end)))
                if not isinstance(color, str):
                    color = f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()})"
                formatted_placeholder[front] = color
            else:
                raise RuntimeError("Malformed placeholder")

        formatted_qss = raw_qss.safe_substitute(**formatted_placeholder)
        return formatted_qss, palette

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
        # TODO: Use string translation here
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
                break
            else:
                qss += line

        placeholders: list[str] = []
        for raw_placeholder in raw_placeholders:
            placeholder = raw_placeholder.strip()
            if placeholder != "":
                placeholders.append(placeholder)
        # TODO: add other attributes more clearly
        load_styles_for = from_theme if style_precautions == "reuse_st" and from_theme is not None else theme_name
        inherit_extend = (mode, from_theme)
        return cls(author, theme_name, qss.strip(), base_app_style, placeholders, compatible_styling, load_styles_for,
                   inherit_extend)

    def __eq__(self, other: str) -> bool:
        return f"{self._author}/{self._theme_name}" == other

    def __repr__(self) -> str:
        return (f"Theme(author={self._author}, theme_name={self._theme_name}, theme_str={self._theme_str[:10]}, "
                f"base={self._base}, placeholder={self._placeholders}, compatible_styling={self._compatible_styling}, "
                f"load_styles_for={self._load_styles_for}, inherit_extend_from={self._inherit_extend_from})")
