"""TBA"""
import config

# Standard imports
from pathlib import Path as PLPath
from traceback import format_exc
import multiprocessing
import logging
import sys
import os
import re

# Third party imports
from PySide6.QtWidgets import (QApplication, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QWidget, QMainWindow,
                               QCheckBox, QMessageBox, QGraphicsItem, QGraphicsEllipseItem, QGraphicsWidget,
                               QStyleOptionGraphicsItem)
from PySide6.QtCore import Qt, QPointF, QRect, QRectF, QUrl, QTimer
from PySide6.QtGui import QPainter, QWheelEvent, QIcon, QDesktopServices, QMouseEvent, QCursor
from packaging.version import Version, InvalidVersion
import stdlib_list
import requests

# Aplustools imports (2.0.0.0a1 stable, not feature complete release.)
from aplustools.io.env import get_system, SystemTheme, BaseSystemType
from aplustools.package.timid import TimidTimer
from aplustools.io import ActLogger
from aplustools.io.qtquick import QQuickMessageBox, QNoSpacingBoxLayout, QBoxDirection

# Core imports (dynamically resolved)
from core.modules.storage import MultiUserDBStorage, JSONAppStorage

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

hiddenimports = list(stdlib_list.stdlib_list())
multiprocessing.freeze_support()


class MyItem(QGraphicsWidget):
    def __init__(self, node_item):
        super().__init__(parent=None)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.setFlag(QGraphicsWidget.ItemIsMovable, True)
        self.setFlag(QGraphicsWidget.ItemIsSelectable, True)

        self.offset : QPointF = None

    def boundingRect(self) -> QRectF:
        return QRect(0,0,30,30)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = ...) -> None:
        r = QRect(0, 0, 30, 30)
        painter.drawRect(r)


    def mouseMoveEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
        self.moveBy(event.pos().x() - self.offset.x(), event.pos().y() - self.offset.y())


class GridView(QGraphicsView):
    """TBA"""
    def __init__(self, parent: QWidget | None = None, grid_size: int = 100, start_x: int = 50, start_y: int = 50,
                 fixed_objects: list[tuple[float, float, QGraphicsItem]] | None = None) -> None:
        super().__init__(parent=parent)
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

        self._grid_size: int = grid_size
        self._offset: QPointF = QPointF(start_x * grid_size, start_y * grid_size)

        self.scene().setSceneRect(-1000, -1000, 2000, 2000)
        self._objects: list[QGraphicsRectItem] = []

        # Center object (input)
        center_rect = QGraphicsRectItem(0, 0, self._grid_size, self._grid_size)
        center_rect.setBrush(Qt.GlobalColor.red)
        center_rect.setPen(Qt.PenStyle.NoPen)
        self._objects.append(center_rect)

        if fixed_objects is not None:
            for (x, y, item) in fixed_objects:
                item.setPos(x * self._grid_size, y * self._grid_size)
                self._objects.append(item)
        for obj in self._objects:  # Can be combined
            self.scene().addItem(obj)

        self.zoom_level: float = 1  # Zoom parameters
        self.zoom_step: float = 0.1
        self.min_zoom: float = 0.2
        self.max_zoom: float = 5.0

        # Panning attributes
        self._is_panning: bool = False
        self._pan_start: QPointF = QPointF(0, 0)

    def drawBackground(self, painter: QPainter, rect: QRect | QRectF) -> None:  # Overwrite
        """Draw an infinite grid."""
        left = int(rect.left()) - (int(rect.left()) % self._grid_size)
        top = int(rect.top()) - (int(rect.top()) % self._grid_size)

        line_t = float | int
        lines: list[tuple[line_t, line_t, line_t, line_t]] = []
        for x in range(left, int(rect.right()), self._grid_size):
            lines.append((x, rect.top(), x, rect.bottom()))
        for y in range(top, int(rect.bottom()), self._grid_size):
            lines.append((rect.left(), y, rect.right(), y))

        painter.setPen(Qt.GlobalColor.lightGray)
        for line in lines:
            painter.drawLine(*line)

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Zoom in and out with the mouse wheel."""
        if event.angleDelta().y() > 0:
            zoom_factor = 1 + self.zoom_step
        else:
            zoom_factor = 1 - self.zoom_step

        new_zoom: float = self.zoom_level * zoom_factor
        if self.min_zoom <= new_zoom <= self.max_zoom:
            self.scale(zoom_factor, zoom_factor)
            self.zoom_level = new_zoom

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Start panning on right or middle mouse button click."""
        if event.button() in (Qt.MouseButton.RightButton, Qt.MouseButton.MiddleButton):
            self._is_panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._is_panning:
            delta = event.position() - self._pan_start

            # Only process significant deltas
            if abs(delta.x()) > 2 or abs(delta.y()) > 2:
                self.horizontalScrollBar().setValue(
                    self.horizontalScrollBar().value() - int(delta.x())
                )
                self.verticalScrollBar().setValue(
                    self.verticalScrollBar().value() - int(delta.y())
                )
                self._pan_start = event.position()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Stop panning on mouse button release."""
        if event.button() in (Qt.MouseButton.RightButton, Qt.MouseButton.MiddleButton):
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)


class DBMainWindowInterface(QMainWindow):
    """TBA"""
    icons_folder: str = ""

    def __init__(self) -> None:
        super().__init__(parent=None)

    def setup_gui(self) -> None:
        """
        Configure the main graphical user interface (GUI) elements of the MV application.

        This method sets up various widgets, layouts, and configurations required for the
        main window interface. It is called after initialization and prepares the interface
        for user interaction.

        Note:
            This method is intended to be overridden by subclasses with application-specific
            GUI components.
        """
        raise NotImplementedError

    def set_scroll_speed(self, value: float) -> None:
        raise NotImplementedError


class DBMainWindow(DBMainWindowInterface):
    def setup_gui(self) -> None:
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.window_layout = QNoSpacingBoxLayout(QBoxDirection.TopToBottom, parent=central_widget)

        # Define positions of fixed objects with their respective QGraphicsItems
        fixed_positions = [
            (10, 10, QGraphicsRectItem(0, 0, 100, 100)),  # A rectangle at (10, 10)
            (100, 100, QGraphicsEllipseItem(0, 0, 150, 150)),  # A circle at (100, 100)
            (20, 50, QGraphicsRectItem(0, 0, 75, 75)),  # A smaller rectangle at (20, 50)
            (50, 20, QGraphicsEllipseItem(0, 0, 50, 100)),  # An ellipse at (50, 20)
        ]

        # Customize appearance of the objects if necessary
        for _, _, item in fixed_positions:
            item.setBrush(Qt.GlobalColor.blue)  # Set the fill color to blue
            item.setPen(Qt.PenStyle.NoPen)  # Remove the border
        self.grid_view = GridView(grid_size=100, start_x=50, start_y=50, fixed_objects=fixed_positions)
        self.window_layout.addWidget(self.grid_view)

    def set_scroll_speed(self, value: float) -> None:
        return


class DudPyApp:  # The main logic and gui are separated
    """TBA"""
    version, version_add = 100, "a0"
    qapp: QApplication | None = None
    qgui: DBMainWindowInterface | None = None

    def __init__(self) -> None:
        # Setting up the base directory in AppData\Local? For now it's in ./localconfig
        self.base_app_dir: str = config.base_app_dir
        self.data_folder: str = os.path.join(self.base_app_dir, "data")  # Like logs, icons, ...
        self.core_folder: str = os.path.join(self.base_app_dir, "core")  # For core functionality like gui
        self.extensions_folder: str = os.path.join(self.base_app_dir, "extensions")  # Extensions
        self.config_folder: str = os.path.join(self.base_app_dir, "config")  # Configurations

        # Setup logger
        self._order_logs(f"{self.data_folder}/logs")
        self.logger: ActLogger = ActLogger(log_to_file=True, filename=f"{self.data_folder}/logs/latest.log")
        self.logger.logger.setLevel(logging.DEBUG if config.INDEV else logging.INFO)
        self.logger.monitor_pipe(sys.stdout, level=logging.DEBUG)
        self.logger.monitor_pipe(sys.stderr, level=logging.ERROR)
        print(config.exported_logs, end="", flush=True)  # Flush config prints

        # Load settings
        self.user_settings: MultiUserDBStorage = MultiUserDBStorage(f"{self.config_folder}/user_settings.db",
                                                                    ("configs", "advanced_configs"))
        self.user_settings.set_default_settings("configs", {
            "provider": "ManhwaClan",
            "title": "Thanks for using ManhwaViewer!",
            "chapter": "1",
            "downscaling": "True",
            "upscaling": "False",
            "manual_content_width": "1200",
            "borderless": "True",
            "hide_titlebar": "False",
            "hover_effect_all": "True",
            "acrylic_menus": "True",
            "acrylic_background": "False",
            "hide_scrollbar": "True",
            "stay_on_top": "False",
            "geometry": "(100, 100, 640, 480)",
            "provider_type": "direct",
            "chapter_rate": "0.5",
            "no_update_info": "True",
            "update_info": "True",
            "last_scroll_positions": "(0, 0)",
            "scrolling_sensitivity": "4.0",
            "save_last_titles": "True"  # Also save chapters
        })
        self.user_settings.set_default_settings("advanced_configs", {
            "recent_titles": "()",
            "light_theme": "light_light",
            "dark_theme": "dark",
            "font": "Segoe UI",
            "settings_backup_file_path": "",
            "settings_backup_file_mode": "overwrite",
            "settings_backup_auto_export": "False",
            "range_web_workers": "(2, 10, 5)",
            "web_workers_check_interval": "5.0"
        })
        self.app_settings: JSONAppStorage = JSONAppStorage(f"{self.config_folder}/app_settings.json", {
            "update_check_request_timeout": "2.0",
            "titlebox_rotation_reset_delay_seconds": "5",
            "titlebox_rotation_rate": "1",
            "window_icon_abs_path": "#/data/assets/logo-nobg.png",
            "window_title_template": "DudPy {version}{version_add} {title} "
        })
        self.abs_window_icon_path: str = self.app_settings.retrieve("window_icon_abs_path")

        # Setup window
        if self.abs_window_icon_path.startswith("#"):
            self.abs_window_icon_path = self.abs_window_icon_path.replace("#", self.base_app_dir, 1)
        self.qgui.setWindowIcon(QIcon(self.abs_window_icon_path))
        self.system: BaseSystemType = get_system()
        self.os_theme: SystemTheme = self.get_os_theme()
        # TODO: self.update_theme()
        x, y, height, width = self.user_settings.retrieve("configs", "geometry", "tuple")
        self.qgui.setGeometry(x, y + 31, height, width)  # Somehow saves it as 31 pixels less,
        self.qgui.setup_gui()  # I guess windows does some weird shit with the title bar

        # Setup values, signals, ...
        self.qgui.set_scroll_speed(self.user_settings.retrieve("configs", "scrolling_sensitivity", "float"))

        # Show gui
        self.qgui.show()
        self.qgui.raise_()

        self.timer: TimidTimer = TimidTimer(start_now=False)
        self.timer.fire_ms(500, self.timer_tick, daemon=True)
        self.check_for_update()

    @staticmethod
    def _order_logs(directory: str) -> None:
        logs_dir = PLPath(directory)
        to_log_file = logs_dir / "latest.log"

        if not to_log_file.exists():
            return

        with open(to_log_file, "rb") as f:
            # (solution from https://stackoverflow.com/questions/46258499/how-to-read-the-last-line-of-a-file-in-python)
            first_line = f.readline().decode()
            try:  # catch OSError in case of a one line file
                f.seek(-2, os.SEEK_END)
                while f.read(1) != b"\n":
                    f.seek(-2, os.SEEK_CUR)
            except OSError:
                f.seek(0)
            last_line = f.readline().decode()

        try:
            date_pattern = r"^[\[(](\d{4}-\d{2}-\d{2})"
            start_date = re.search(date_pattern, first_line).group(1)
            end_date = re.search(date_pattern, last_line).group(1)
        except AttributeError:
            print("Removing malformed latest.log")
            os.remove(to_log_file)
            return

        date_name = f"{start_date}_{end_date}"
        date_logs = list(logs_dir.rglob(f"{date_name}*.log"))

        if not date_logs:
            new_log_file_name = logs_dir / f"{date_name}.log"
        else:
            max_num = max(
                (int(re.search(r"#(\d+)$", p.stem).group(1)) for p in date_logs if
                 re.search(r"#(\d+)$", p.stem)),
                default=0
            )
            max_num += 1
            base_log_file = logs_dir / f"{date_name}.log"
            if base_log_file.exists():
                os.rename(base_log_file, logs_dir / f"{date_name}#{max_num}.log")
                max_num += 1
            new_log_file_name = logs_dir / f"{date_name}#{max_num}.log"

        os.rename(to_log_file, new_log_file_name)
        print(f"Renamed latest.log to {new_log_file_name}")

    def get_os_theme(self) -> SystemTheme:
        """Gets the os theme based on a number of parameters, like environment variables."""
        base = self.system.get_system_theme()
        if not base:
            raw_fallback = str(os.environ.get("MV_THEME")).lower()  # Can return None
            fallback = {"light": SystemTheme.LIGHT, "dark": SystemTheme.DARK}.get(raw_fallback)
            if fallback is None:
                return SystemTheme.LIGHT
            return fallback
        return base

    def check_for_update(self) -> None:
        """Checks for an update and creates a message box accordingly."""
        print("Checking time taken to check for update ...")
        timer = TimidTimer()
        icon = QMessageBox.Icon.Information
        title, text, description = "Title", "Text", "Description"
        checkbox, checkbox_setting = None, ("", "")
        standard_buttons, default_button = QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Ok
        retval_func = lambda button: None

        try:
            response = requests.get("https://raw.githubusercontent.com/adalfarus/update_check/main/mv/update.json",
                                    timeout=self.app_settings.retrieve("update_check_request_timeout", float))
            print("Response time: ", timer.tock())
            update_json = response.json()
            print("JSON Parse time: ", timer.tock())

            # Find a version bigger than the current version and prioritize versions with push
            # Version(".".join(list(str(self.version))) + self.version_add)
            current_version = Version(f"{self.version}{self.version_add}")
            found_version: Version | None = None
            found_release: dict | None = None
            found_push: bool = False
            print("VLoop Start time: ", timer.tock())
            for release in update_json["versions"]:
                release_version = Version(release["versionNumber"])
                if release_version == current_version:
                    found_version = release_version
                    found_release = release
                    found_push = False  # Doesn't need to be set again
                if release_version > current_version:
                    push = release["push"].title() == "True"
                    if found_version is None or (release_version > found_version and push):
                        found_version = release_version
                        found_release = release
                        found_push = push
            print("VLoop End time: ", timer.tock())

            if found_version != current_version and self.user_settings.retrieve("configs", "update_info", "bool") and found_push:
                title = "There is an update available"
                text = (f"There is a newer version ({found_version}) "
                        f"available.\nDo you want to open the link to the update?")
                description = found_release.get("description")
                checkbox, checkbox_setting = QCheckBox("Do not show again"), ("configs", "update_info")

                def retval_func(button) -> None:
                    """TBA"""
                    if button == QMessageBox.StandardButton.Yes:
                        url = found_release.get("updateUrl", "None")
                        if url.title() == "None":
                            link = update_json["metadata"].get("sorryUrl", "https://example.com")
                        else:
                            link = url
                        QDesktopServices.openUrl(QUrl(link))
            elif self.user_settings.retrieve("configs", "no_update_info", "bool") and found_version == current_version:
                title = "Update Info"
                text = (f"No new updates available.\nChecklist last updated "
                        f"{update_json['metadata']['lastUpdated'].replace('-', '.')}.")
                description = f" --- v{found_version} --- \n{found_release.get('description')}"
                checkbox, checkbox_setting = QCheckBox("Do not show again"), ("configs", "no_update_info")
            elif self.user_settings.retrieve("configs", "no_update_info", "bool") and found_push:
                title = "Info"
                text = (f"New version available, but not recommended {found_version}.\n"
                        f"Checklist last updated {update_json['metadata']['lastUpdated'].replace('-', '.')}.")
                description = found_release.get("description")
                checkbox, checkbox_setting = QCheckBox("Do not show again"), ("configs", "no_update_info")
            else:
                title, text, description = "Update Info", "There was a logic-error when checking for updates.", ""
        except (requests.exceptions.JSONDecodeError, InvalidVersion):
            icon = QMessageBox.Icon.Information  # Reset everything to default, we don't know when the error happened
            title, text, description = "Update Info", "There was an error when checking for updates.", format_exc()
            checkbox, checkbox_setting = None, ("", "")
            standard_buttons, default_button = QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Ok
            retval_func = lambda button: None
        except (requests.exceptions.RequestException, requests.exceptions.Timeout):
            title, text, description = "Update Info", "The request timed out.\nPlease check your internet connection and try again.", format_exc()
            standard_buttons, default_button = QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Ok
        finally:
            print("MSGBox exec start time: ", timer.tock())
            print("Total:", timer.end())
            msg_box = QQuickMessageBox(self.qgui, icon, title, text, description, checkbox,
                                       standard_buttons=standard_buttons,
                                       default_button=default_button)
            retval = msg_box.exec()  # Keep ref to msg_box so checkbox doesn't get deleted prematurely
            retval_func(retval)
            if checkbox is not None and checkbox.isChecked():
                self.user_settings.store(*checkbox_setting, value=False, value_type="bool")

    def timer_tick(self):
        # print("Tick")
        return
        if not self.threading:
            self.update_content()
        if random.randint(0, 20) == 0:
            os_theme = (self.system.get_windows_theme() or os.environ.get("MV_THEME")).lower()
            if os_theme != self.os_theme:
                self.update_theme(os_theme)

    def exit(self) -> None:
        if hasattr(self, "timer"):
            self.timer.stop_fires(0, not_exists_okay=True)

    def __del__(self) -> None:
        self.exit()


if __name__ == "__main__":
    RESTART_CODE = 1000
    current_exit_code = -1
    try:
        qapp = QApplication(sys.argv)
        qgui = DBMainWindow()
        DudPyApp.qapp = qapp
        DudPyApp.qgui = qgui
        dp_app = DudPyApp()  # Shows gui
        current_exit_code = qapp.exec()

        if current_exit_code == RESTART_CODE:
            os.execv(sys.executable, [sys.executable] + sys.argv)
        else:
            exit(current_exit_code)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        title = "Info"
        text = ("There was an error while running the app DudPy.\n"
                "This error is unrecoverable.\nPlease submit the details to our GitHub issues page.")
        description = format_exc()
        msg_box = QQuickMessageBox(None, QMessageBox.Icon.Warning, title, text, description,
                                   standard_buttons=QMessageBox.StandardButton.Ok,
                                   default_button=QMessageBox.StandardButton.Ok)
        icon_path = os.path.abspath("./data/assets/logo-nobg.png")
        if "mv_app" in locals():
            if hasattr(dp_app, "abs_window_icon_path"):
                icon_path = dp_app.abs_window_icon_path
        msg_box.setWindowIcon(QIcon(icon_path))
        msg_box.exec()
        raise e
    finally:
        if "mv_app" in locals():
            dp_app.exit()
        if "qgui" in locals():
            qgui.close()
        if "qapp" in locals():
            qapp.instance().quit()
        exit(current_exit_code)
