## What are th and st files and how do they work?

### th files:

The file name of th files is of importance. It encodes the name of the creator as the first word and the name of the theme as the rest.

For example:

``adalfarus_cool_theme.th``

is the theme Cool Theme by adalfarus. This is done so we have less name conflicts when dealing with .st files later.

The first line in the file is composed of "{base_app_style}/{compatible_styling}"

Firstly we can look at what a base_app_style is. A base app style is one of the styles Qt6 provides by default. They include:

- Default (No styling)
- windows11 (Windows 11 if you're on Windows 11)
- Windows (Windows 95 look)
- windowsvista (Windows 95 look)
- Fusion (Modern take with bright accent colors)

Secondly we can come to the compatible_styling attribute. There are 4 possible options:
- light (Only supports light theming)
- dark (Only supports dark theming)
- \* (Support both light and dark theming)
- os (Support both light and dark theming and is build so that it works with only QPalette and base colors, meaning it can be set by OS-specific theming)

Next up we have the Actual QSS with placeholders for **all** colors.

All GUI elements within our app have their object names set to their location within the class hierarchy so a QPushButton in the var settings_button within the user panel would be named ``user_panel-settings_button`` and could be accessed by using ``QPushButton#user_panel-settings_button { ... }``

Placeholders can be inserted using the $ symbol, here an example: ``background: $black;``.

Lastly we have "ph:", which stands for placeholder

Here you specify what placeholders you've used and if they're changeable. For example:

````commandline
dark_color~=#111111;
background_color~=#291292;
black==#000000;
white==#ffffff;
see_trough==rgba(0, 0, 0, 0);
````

If you define a placeholder using ~= it means it can be changed. If you define it with == it will always be the same. Though it is important to know that some placeholers are globally defined:
- all Qt.Globalcolors
- all QPalette colors like QPalette.WindowText (in rgb) and their transparent version like QPalette.WindowTextT which are rgba with an open bracket so you can add you own alpha value.

If we put that together we get something like this:

````commandline
adalfarus_modern_theme.th

Fusion/os

/* Start of QSS (not needed) */

QWidget {
    background-color: {background_color};
    color: {text_color};
}

QPushButton {
    background-color: {button_color};
    color: {button_text_color};
    border: 1px solid {button_border_color};
    border-radius: 4px;
    padding: 5px;
}

QPushButton:hover {
    background-color: {button_hover_color};
}

QLineEdit {
    background-color: {input_background_color};
    color: {input_text_color};
    border: 1px solid {input_border_color};
    border-radius: 3px;
    padding: 2px;
}

/* End of QSS (not needed) */

ph:
background_color~=#ffffff;
text_color~=#000000;
button_color~=#007bff;
button_text_color~=#ffffff;
button_border_color~=#0056b3;
button_hover_color~=#0056b3;
input_background_color~=#f8f9fa;
input_text_color~=#495057;
input_border_color~=#ced4da;
````

### st files:

At the start of each st file is the for command. It specifies for which themes this style can be applied. A * can be used to include everything from a (sub-)category.

The base is the authors name, then the theme name and lastly what type of theme it is (light, dark, *).

Here is an example:

````jsunicoderegexp
for adalfarus::{
    thick::*, thin::*
}; // Remember the ;
````

Moving on we now just define the placeholders. QPalette is an "object" with multiple color attributes so it's defined a bit differently, here's an example:

````python
QPalette[
    background: rgba(10, 22, 211, 0.1);
    foreground: #d3d3d3;
]
// Qt global colors
white: #ffffff;
black: #000000;
... // Other Qt.Globalcolors you wish to overwrite
````

Transparency can be archived through 3 different ways. Either the style author implements it themselves and adds a T variant of all colors they want to be affected. Like this:

````
background_secondaryT: rgba(255, 222, 111, 129);
... // Other transparent colors
````

Or the program dynamically adds transparency to all colors like this:

````
Example 1:
background_secondary: rgb(255, 222, 111);
-->
background_secondaryT: rgba(255, 222, 111, 200); // 200 or anything else depending on what transparency we want. This doesn't affect colors that already have an alpha value.'

Example 2:
border: #222222;
-->
borderT: #22222200; // 0 or any other transparency
````

Lastly, we can add transparency to the already generated stylesheets.

To make that happen we just append a * style to the end of the style sheet like this:

````python
from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QColor

def deepen_color(self, color, darken_factor=100, saturation_factor=1.3):
    # Increase saturation and darken the color
    # Convert to HSL for control over lightness and saturation
    color = color.toHsl()

    deepened_color = color.darker(darken_factor)  # 100 is original, higher values are darker

    # Optionally adjust saturation using HSV
    deepened_color = deepened_color.toHsv()
    deepened_color.setHsv(deepened_color.hue(),
                          min(255, int(deepened_color.saturation() * saturation_factor)),
                          deepened_color.value())

    return deepened_color

menu_button = QPushButton()  # Should have the theme already applied.

styles_sheet = "\nQPushButton:hover,\nQComboBox:hover"
bg_color = menu_button.palette().color(menu_button.backgroundRole())
bg_color.setAlpha(30)
deep_bg_color = deepen_color(bg_color)
stylesheet = f"""
* {{
    background-color: {bg_color.name(QColor.NameFormat.HexArgb)};
}}
""" + styles_sheet + f"""
 {{
    background-color: {deep_bg_color.name(QColor.NameFormat.HexArgb)};
}}"""
centralWidget().setStyleSheet(stylesheet)

# If we want to remove this, we just use this:
centralWidget().setStyleSheet("")
````
