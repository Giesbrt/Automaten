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
- all QPalette colors like QPalette.WindowText

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
  