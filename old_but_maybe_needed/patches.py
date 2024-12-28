import re
@staticmethod
def _parse_color(color_str: str, color_space: ColorSpace) -> QColor:
    """
    Parse the input color into a QColor object.

    :param color_str: Input color in any supported format
    :param color_space: QColor.Spec value for color space
    :return: QColor object
    """
    if not isinstance(color_str, str):
        raise ValueError(f"Color has to be a string")
    cleaned_color = color_str.strip().lower()

    # Hexadecimal color: #rgb, #rgba, #rrggbb, #rrggbbaa
    if match := re.match(r"^#([a-f0-9]{3,8})$", cleaned_color):
        return QColor(cleaned_color, color_space)
    # RGB: rgb(r, g, b)
    elif match := re.match(r"^rgb\((\d+),\s*(\d+),\s*(\d+)\)$", cleaned_color):
        r, g, b = map(int, match.groups())
        return QColor(r, g, b, 255, color_space)
    # RGBA: rgba(r, g, b, a)
    elif match := re.match(r"^rgba\((\d+),\s*(\d+),\s*(\d+),\s*([01]?(?:\.\d+)?)\)$", cleaned_color):
        r, g, b = map(int, match.groups()[:3])
        a = int(float(match.group(4)) * 255)
        return QColor(r, g, b, a, color_space)
        QColor.fr
    else:
        raise ValueError(f"Unsupported color format: '{cleaned_color}'")