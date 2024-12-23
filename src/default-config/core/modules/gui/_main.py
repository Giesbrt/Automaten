"""TBA"""
from PySide6.QtWidgets import QWidget, QMainWindow, QMessageBox

from aplustools.io.qtquick import QQuickMessageBox

from ..abstract import MainWindowInterface

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts


class MainWindow(MainWindowInterface, QMainWindow):
    icons_dir: str
    linked: bool = False

    def __new__(cls, *args, **kwargs):
        return QMainWindow.__new__(cls,)

    def __init__(self) -> None:
        self.user_panel: dict
        self.settings_panel: dict
        super().__init__(parent=None)

    def setup_gui(self) -> None:
        # self.user_panel = UserPanel(parent=self)
        # # self.window_layout.addWidget(self.user_panel)
        # self.user_panel.setGeometry(0, 0, self.width(), self.height())

        # Animation for Side Menu
        # # self.user_panel_animation = QPropertyAnimation(self.user_panel, b"geometry")
        # self.user_panel_animation = QVariantAnimation()  # self.user_panel
        # self.user_panel_animation.setDuration(500)
        # self.user_panel_animation.valueChanged.connect(self.animate_geometry)
        # self.user_panel_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        #
        # self.settings_panel = SettingsPanel(parent=self)
        # # self.window_layout.addWidget(self.settings_panel)
        # self.settings_panel.setGeometry(self.width(), 0, self.width(), self.height())
        #
        # # Animation for Side Menu
        # # self.settings_panel_animation = QPropertyAnimation(self.settings_panel, b"geometry")
        # # self.settings_panel_animation.setDuration(500)
        # # self.animation_group = QParallelAnimationGroup()
        # # self.timer = TimidTimer()
        # # self.timer.interval(3, count=2, callback=self.switch_panel)
        # self.animation_timer = QTimer()
        # self.animation_timer.setInterval(3000)
        # self.animation_timer.timeout.connect(self.switch_panel)
        # self.animation_timer.start()
        # self.current_x = 0
        # self.target_x = -self.width()
        ...

    def switch_panel_simple(self):
        print("Switching ...")
        width = self.width()
        height = self.height()

        user_panel_hidden_value = QRect(-width, 0, width, height)
        shown_panel_end_value = QRect(0, 0, width, height)
        settings_panel_hidden_value = QRect(width, 0, width, height)

        if self.settings_panel.x() == 0:
            print("To user")
            self.user_panel.setGeometry(shown_panel_end_value)
            self.settings_panel.setGeometry(settings_panel_hidden_value)
        else:
            print("To sett")
            self.user_panel.setGeometry(user_panel_hidden_value)
            self.settings_panel.setGeometry(shown_panel_end_value)

    def switch_panel2(self):
        print("Switching")
        print((((((((('a',),),),),),),),))
        self.current_x = self.user_panel.x()
        self.target_x = -self.width() if self.current_x == 0 else 0
        print(self.current_x, self.target_x)
        self.timer.fire_ms(10, self.manual_animation_step, daemon=True)
        # self.animation_timer.timeout.connect(self.manual_animation_step)
        # self.animation_timer.start()

    def manual_animation_step(self):
        print("STEP")
        step = 20  # Adjust for smoothness
        if self.current_x > self.target_x:
            self.current_x -= step
            print("Setting", QRect(self.current_x, 0, self.width(), self.height()))
            self.user_panel.setGeometry(QRect(self.current_x, 0, self.width(), self.height()))
        else:
            self.timer.stop_fire()

    def animate_geometry(self, value):
        print("Animating geometry:", value)  # Debug the intermediate values
        self.user_panel.setGeometry(value)

    def switch_panel(self):
        print("Switching ...")
        width = self.width()
        height = self.height()

        user_panel_hidden_value = QRect(-width, 0, width, height)
        shown_panel_end_value = QRect(0, 0, width, height)
        settings_panel_hidden_value = QRect(width, 0, width, height)

        self.some_animation = QVariantAnimation()
        self.some_animation.setDuration(1000)
        self.some_animation.valueChanged.connect(lambda x: print(x))
        self.some_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.some_animation.setStartValue(QRect(0, 0, 1050, 640))
        self.some_animation.setEndValue(QRect(-1050, 0, 1050, 640))
        self.some_animation.start()

        if self.settings_panel.x() == 0:
            print("To user")
            self.user_panel_animation.setStartValue(user_panel_hidden_value)
            self.user_panel_animation.setEndValue(shown_panel_end_value)
            # self.settings_panel_animation.setStartValue(shown_panel_end_value)
            # self.settings_panel_animation.setEndValue(settings_panel_hidden_value)
        else:
            print("To sett")
            self.user_panel_animation.setStartValue(shown_panel_end_value)
            self.user_panel_animation.setEndValue(user_panel_hidden_value)
            # self.settings_panel_animation.setStartValue(settings_panel_hidden_value)
            # self.settings_panel_animation.setEndValue(shown_panel_end_value)
        print("Animation state before start:", self.user_panel_animation.state())
        print("Starting at ", self.user_panel_animation.startValue())
        print("Ending at ", self.user_panel_animation.endValue())
        self.user_panel_animation.start()
        print("Animation state after start:", self.user_panel_animation.state())
        # self.settings_panel_animation.start()

    def popup(self, title: str, text: str, description: str, icon: QMessageBox.Icon = QMessageBox.Icon.Information,
              buttons: list[QMessageBox.StandardButton] | QMessageBox.StandardButton = QMessageBox.StandardButton.Ok,
              default_button: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok) -> QMessageBox.StandardButton:
        msg_box = QQuickMessageBox(self, icon, title, text, description,
                                   standard_buttons=buttons,
                                   default_button=default_button)
        return msg_box.exec()

    def set_scroll_speed(self, value: float) -> None:
        return

    def start(self) -> None:
        self.show()
        self.raise_()

    def close(self) -> None:
        QMainWindow.close(self)
