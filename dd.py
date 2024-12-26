from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt


def print_palette_colors(palette):
    print(f"\nCurrent Mode Colors:\n" + "-" * 30)

    for name in QPalette.ColorRole.__dict__:
        if name.startswith("_"):
            continue
        try:
            color = palette.color(getattr(QPalette.ColorRole, name))
            # print(f"{name:<20}: {color.name()} ({color.red()}, {color.green()}, {color.blue()}, {color.alpha()})")
            print(f"{name}: rgba{(color.red(), color.green(), color.blue(), color.alpha())};")
        except:
            pass


def list_global_colors():
    print("\nQt Global Colors:\n" + "-" * 30)

    for name in Qt.GlobalColor:
        color = QColor(name)
        print(f"{name:<12}: {color.name()} ({color.red()}, {color.green()}, {color.blue()})")


def main():
    app = QApplication([])
    print_palette_colors(app.palette())

    # List Global Colors
    # list_global_colors()


if __name__ == "__main__":
    main()
