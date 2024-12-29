"""TBA"""
import config

# Standard imports
from pathlib import Path as PLPath
from traceback import format_exc
import multiprocessing
from string import Template
import threading
import logging
import sys
import os
import re

# Third party imports
from PySide6.QtWidgets import QApplication, QCheckBox, QMessageBox
from PySide6.QtCore import QUrl
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtGui import (QCloseEvent, QResizeEvent, QMoveEvent, QFocusEvent, QKeyEvent, QMouseEvent,
                           QEnterEvent, QPaintEvent, QDragEnterEvent, QDragMoveEvent, QDropEvent,
                           QDragLeaveEvent, QShowEvent, QHideEvent, QContextMenuEvent,
                           QWheelEvent, QTabletEvent)
from PySide6.QtCore import QEvent, QTimerEvent

from packaging.version import Version, InvalidVersion
import stdlib_list
import requests

# Aplustools imports (2.0.0.0a1 stable, not feature complete release.)
from aplustools.io.env import get_system, SystemTheme, BaseSystemType
from aplustools.io import ActLogger
from aplustools.package.timid import TimidTimer
from aplustools.io.qtquick import QQuickMessageBox, QtTimidTimer

# Core imports (dynamically resolved)
from core.modules.storage import MultiUserDBStorage, JSONAppStorage
from core.modules.gui import MainWindow, assign_object_names_iterative, Theme, Style
from core.modules.abstract import MainWindowInterface, BackendInterface
from core.modules.automaton_loader import start

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

hiddenimports = list(stdlib_list.stdlib_list())
multiprocessing.freeze_support()


class App:  # The main logic and gui are separated
    """TBA"""
    window: MainWindowInterface | None = None
    qapp: QApplication | None = None
    linked: bool = False

    def __init__(self) -> None:
        # Setting up the base directory in AppData\Local? For now it's in ./localconfig
        self.base_app_dir: str = config.base_app_dir
        self.data_folder: str = os.path.join(self.base_app_dir, "data")  # Like logs, icons, ...
        self.core_folder: str = os.path.join(self.base_app_dir, "core")  # For core functionality like gui
        self.extensions_folder: str = os.path.join(self.base_app_dir, "extensions")  # Extensions
        self.config_folder: str = os.path.join(self.base_app_dir, "config")  # Configurations
        self.styling_folder: str = os.path.join(self.base_app_dir, "styling")  # App styling

        # TODO: remove dependency on self.window.icons_dir
        self.window.icons_dir = os.path.join(self.data_folder, "icons")
        self.window.app = self.qapp

        # Setup logger
        self._order_logs(f"{self.data_folder}/logs")
        self.logger: ActLogger = ActLogger(log_to_file=True, filename=f"{self.data_folder}/logs/latest.log")
        self.logger.logger.setLevel(logging.DEBUG if config.INDEV else logging.INFO)
        self.logger.monitor_pipe(sys.stdout, level=logging.DEBUG)
        self.logger.monitor_pipe(sys.stderr, level=logging.ERROR)
        for exported_line in config.exported_logs.split("\n"):
            self.logger.debug(exported_line)  # Flush config prints

        # Load settings
        self.user_settings: MultiUserDBStorage = MultiUserDBStorage(f"{self.config_folder}/user_settings.db",
                                                                    ("auto_configs", "user_configs_design",
                                                                     "user_configs_advanced"))
        self.app_settings: JSONAppStorage = JSONAppStorage(f"{self.config_folder}/app_settings.json")
        self.configure_settings()
        self.abs_window_icon_path: str = self.app_settings.retrieve("window_icon_abs_path")

        self.backend: BackendInterface = start(self.app_settings, self.user_settings)
        self.backend_stop_event: threading.Event = threading.Event()
        self.backend_thread: threading.Thread = threading.Thread(target=self.backend.run_infinite,
                                                                 args=(self.backend_stop_event,))
        self.backend_thread.start()

        self.load_themes(os.path.join(self.styling_folder, "themes"))
        self.load_styles(os.path.join(self.styling_folder, "styles"))

        # Setup window
        if self.abs_window_icon_path.startswith("#"):
            self.abs_window_icon_path = self.abs_window_icon_path.replace("#", self.base_app_dir, 1)
        self.window.set_window_icon(self.abs_window_icon_path)
        self.system: BaseSystemType = get_system()
        self.os_theme: SystemTheme = self.get_os_theme()

        self.update_title()
        x, y, height, width = self.user_settings.retrieve("auto_configs", "geometry", "tuple")
        if not self.user_settings.retrieve("user_configs_advanced", "save_window_dimensions", "bool"):
            height = 640
            width = 1050
        if self.user_settings.retrieve("user_configs_advanced", "save_window_position", "bool"):
            self.window.set_window_geometry(x, y + 31, height, width)  # Somehow saves it as 31 pixels less,
        else:
            self.window.set_window_dimensions(height, width)
        self.window.setup_gui()  # I guess windows does some weird shit with the title bar
        assign_object_names_iterative(self.window)  # Set object names for theming
        #self.window.set_global_theme("""
        #    QPushButton#user_panel-settings_button {
        #        background-color: lightblue;
        #    }
        #""", self.window.AppStyle.Default)  # getattr(self.window.AppStyle, "Fusion")
        self.link_gui()

        # Setup values, signals, ...
        # TODO: self.window.set_scroll_speed(self.user_settings.retrieve("configs", "scrolling_sensitivity", "float"))

        # Show gui
        self.window.start()

        self.timer: QtTimidTimer = QtTimidTimer()
        self.timer.timeout.connect(self.timer_tick)
        self.timer.start(500, 0)
        # self.timer.start(1500, 1)  # 1.5 second timer
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
            raw_fallback = str(os.environ.get("APP_THEME")).lower()  # Can return None
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
        do_popup: bool = True

        try:
            response = requests.get("https://raw.githubusercontent.com/Giesbrt/Automaten/main/meta/update_check.json",
                                    timeout=self.app_settings.retrieve("update_check_request_timeout", float))
            print("Response time: ", timer.tock())
            update_json = response.json()
            print("JSON Parse time: ", timer.tock())

            # Find a version bigger than the current version and prioritize versions with push
            # Version(".".join(list(str(self.version))) + self.version_add)
            current_version = Version(f"{config.VERSION}{config.VERSION_ADD}")
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
            show_update_info: bool = self.user_settings.retrieve("auto_configs", "show_update_info", "bool")
            show_no_update_info: bool = self.user_settings.retrieve("auto_configs", "show_no_update_info", "bool")

            if found_version != current_version and show_update_info and found_push:
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
            elif show_no_update_info and found_version == current_version:
                title = "Update Info"
                text = (f"No new updates available.\nChecklist last updated "
                        f"{update_json['metadata']['lastUpdated'].replace('-', '.')}.")
                description = f" --- v{found_version} --- \n{found_release.get('description')}"
                checkbox, checkbox_setting = QCheckBox("Do not show again"), ("configs", "no_update_info")
            elif show_no_update_info and found_push:
                title = "Info"
                text = (f"New version available, but not recommended {found_version}.\n"
                        f"Checklist last updated {update_json['metadata']['lastUpdated'].replace('-', '.')}.")
                description = found_release.get("description")
                checkbox, checkbox_setting = QCheckBox("Do not show again"), ("configs", "no_update_info")
            else:
                title, text, description = "Update Info", "There was a logic-error when checking for updates.", ""
                do_popup = False
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
            print("Popup time: ", timer.tock())
            print("Total:", timer.end())
            if do_popup:
                msg_box = QQuickMessageBox(self.window, icon, title, text, description, checkbox,
                                           standard_buttons=standard_buttons,
                                           default_button=default_button)
                retval = msg_box.exec()  # Keep ref to msg_box so checkbox doesn't get deleted prematurely
                retval_func(retval)
                if checkbox is not None and checkbox.isChecked():
                    self.user_settings.store(*checkbox_setting, value=False, value_type="bool")

    def configure_settings(self) -> None:
        self.user_settings.set_default_settings("auto_configs", {
            "geometry": "(100, 100, 1050, 640)",
            "show_no_update_info": "False",
            "show_update_info": "True",
            "last_scroll_positions": "(0, 0, 0, 0)",
            "scrolling_sensitivity": "4.0",
            "ask_to_reopen_last_opened_file": "True",
            "recent_files": "()"
        })
        self.user_settings.set_default_settings("user_configs_design", {
            "light_theme": "adalfarus::thin::light_icons",
            "dark_theme": "adalfarus::thin::dark_icons",
            "font": "Segoe UI",
            "window_title_template": f"{config.PROGRAM_NAME} $version$version_add $title" + " [INDEV]" if config.INDEV else ""
        })
        self.user_settings.set_default_settings("user_configs_advanced", {
            "hide_titlebar": "False",
            "hide_scrollbar": "True",
            "stay_on_top": "False",
            "settings_backup_file_path": "",
            "settings_backup_file_mode": "overwrite",
            "settings_backup_auto_export": "False",
            "save_window_dimensions": "True",
            "save_window_position": "False"
        })
        self.app_settings.set_default_settings({
            "update_check_request_timeout": "2.0",
            "titlebox_rotation_reset_delay_seconds": "5",
            "titlebox_rotation_rate": "1",
            "window_icon_abs_path": "#/data/assets/logo-nobg.png",
            "simulation_loader_max_restart_counter": "5"
        })

    def closeEvent(self, event: QCloseEvent) -> None:
        ...

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.window.reload_panels()

    def moveEvent(self, event: QMoveEvent) -> None:
        ...

    def focusInEvent(self, event: QFocusEvent) -> None:
        ...

    def focusOutEvent(self, event: QFocusEvent) -> None:
        ...

    def keyPressEvent(self, event: QKeyEvent) -> None:
        ...

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        ...

    def mousePressEvent(self, event: QMouseEvent) -> None:
        ...

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        ...

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        ...

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        ...

    def enterEvent(self, event: QEnterEvent) -> None:
        ...

    def leaveEvent(self, event: QEvent) -> None:
        ...

    def paintEvent(self, event: QPaintEvent) -> None:
        ...

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        ...

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        ...

    def dropEvent(self, event: QDropEvent) -> None:
        ...

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        ...

    def showEvent(self, event: QShowEvent) -> None:
        ...

    def hideEvent(self, event: QHideEvent) -> None:
        ...

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        ...

    def wheelEvent(self, event: QWheelEvent) -> None:
        ...

    def tabletEvent(self, event: QTabletEvent) -> None:
        ...

    def timerEvent(self, event: QTimerEvent) -> None:
        ...

    def _create_link_event(self, event_handler, eventFunc) -> _a.Callable:
        return lambda e: (event_handler(e), getattr(self, eventFunc)(e))

    def link_gui(self):
        """Links the gui events to this class."""
        if not self.linked:
            self.linked = True
            for eventFunc in ("closeEvent", "resizeEvent", "moveEvent", "focusInEvent", "focusOutEvent",
                              "keyPressEvent", "keyReleaseEvent", "mousePressEvent", "mouseReleaseEvent",
                              "mouseDoubleClickEvent", "mouseMoveEvent", "enterEvent", "leaveEvent", "paintEvent",
                              "dragEnterEvent", "dragMoveEvent", "dropEvent", "dragLeaveEvent", "showEvent",
                              "hideEvent", "contextMenuEvent", "wheelEvent", "tabletEvent", "timerEvent"):
                event_handler = getattr(self.window, eventFunc)
                setattr(self.window, eventFunc, self._create_link_event(event_handler, eventFunc))

    def load_themes(self, theme_folder: str) -> None:
        paths: list[str] = [os.path.join(theme_folder, "adalfarus_base.th")]

        for file in os.listdir(theme_folder):
            if file.endswith(".th"):
                path = os.path.join(theme_folder, file)
                if path not in paths:
                    paths.append(path)

        for path in paths:
            Theme.load_from_file(path)
        print(Theme._loaded_themes)

    def load_styles(self, style_folder: str) -> None:
        for file in os.listdir(style_folder):
            if file.endswith(".st"):
                path = os.path.join(style_folder, file)
                Style.load_from_file(path)
        print(Style.loaded_styles)

        for theme in Theme._loaded_themes:
            if theme.get_theme_uid() == "adalfarus::thin":
                style = theme.get_compatible_style("Thin Light Dark")  # "Colored Evening Sky"
                theme_str, palette = theme.apply_style(style, self.qapp.palette(), )
                self.qapp.setPalette(palette)
                break
        print("TS", theme_str)
        self.window.set_global_theme(theme_str, getattr(self.window.AppStyle, theme.get_base()))

    def update_title(self) -> None:
        raw_title = Template(self.user_settings.retrieve("user_configs_design", "window_title_template", "string"))
        formatted_title = raw_title.safe_substitute(version=config.VERSION, version_add=config.VERSION_ADD)
        self.window.set_window_title(formatted_title)

    def timer_tick(self, index: int) -> None:
        if index == 0:  # Default 500ms timer
            self.update_title()
        else:
            print("Tock")
        # if not self.threading:
        #     self.update_content()
        ...

    def exit(self) -> None:
        if hasattr(self, "timer"):
            self.timer.stop_all()
        if hasattr(self, "backend_thread") and self.backend_thread.is_alive():
            self.backend_stop_event.set()
            self.backend_thread.join()

    def __del__(self) -> None:
        self.exit()


if __name__ == "__main__":
    CODES: dict[int, _a.Callable] = {
        1000: lambda: os.execv(sys.executable, [sys.executable] + sys.argv)  # RESTART_CODE (only works compiled)
    }
    qapp: QApplication | None = None
    qgui: MainWindowInterface | None = None
    dp_app: App | None = None
    current_exit_code: int = -1

    try:
        qapp = QApplication(sys.argv)
        qgui = MainWindow()
        App.window = qgui
        App.qapp = qapp
        dp_app = App()  # Shows gui
        current_exit_code = qapp.exec()
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        title = "Info"
        text = (f"There was an error while running the app {config.PROGRAM_NAME}.\n"
                "This error is unrecoverable.\nPlease submit the details to our GitHub issues page.")
        description = format_exc()
        msg_box = QQuickMessageBox(None, QMessageBox.Icon.Warning, title, text, description,
                                   standard_buttons=QMessageBox.StandardButton.Ok,
                                   default_button=QMessageBox.StandardButton.Ok)
        icon_path = os.path.abspath("./data/assets/logo-nobg.png")
        if hasattr(dp_app, "abs_window_icon_path"):
            icon_path = dp_app.abs_window_icon_path
        msg_box.setWindowIcon(QIcon(icon_path))
        msg_box.exec()
        logger: logging.Logger = logging.getLogger("ActLogger")
        if not logger.hasHandlers():
            print(description.strip())  # We print, in case the logger is not initialized yet
        else:
            for line in description.strip().split("\n"):
                logger.error(line)
    finally:
        if dp_app is not None:
            dp_app.exit()
        if qgui is not None:
            qgui.close()
        if qapp is not None:
            qapp.instance().quit()
        CODES.get(current_exit_code, lambda: sys.exit(current_exit_code))()
