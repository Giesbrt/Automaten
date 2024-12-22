"""TBA"""
import threading

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
from PySide6.QtWidgets import QApplication, QMainWindow, QCheckBox, QMessageBox
from PySide6.QtCore import QUrl
from PySide6.QtGui import QIcon, QDesktopServices
from packaging.version import Version, InvalidVersion
import stdlib_list
import requests

# Aplustools imports (2.0.0.0a1 stable, not feature complete release.)
from aplustools.io.env import get_system, SystemTheme, BaseSystemType
from aplustools.package.timid import TimidTimer
from aplustools.io import ActLogger
from aplustools.io.qtquick import QQuickMessageBox

# Core imports (dynamically resolved)
from core.modules.storage import MultiUserDBStorage, JSONAppStorage
from core.modules.gui import DBMainWindow

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

hiddenimports = list(stdlib_list.stdlib_list())
multiprocessing.freeze_support()


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


class DudPyApp:  # The main logic and gui are separated
    """TBA"""
    version, version_add = 100, ""
    gui: DBMainWindowInterface | None = None

    def __init__(self) -> None:
        # Setting up the base directory in AppData\Local? For now it's in ./localconfig
        self.base_app_dir: str = config.base_app_dir
        self.data_folder: str = os.path.join(self.base_app_dir, "data")  # Like logs, icons, ...
        self.core_folder: str = os.path.join(self.base_app_dir, "core")  # For core functionality like gui
        self.extensions_folder: str = os.path.join(self.base_app_dir, "extensions")  # Extensions
        self.config_folder: str = os.path.join(self.base_app_dir, "config")  # Configurations
        self.gui.icons_dir = os.path.join(self.data_folder, "icons")

        # Setup logger
        self._order_logs(f"{self.data_folder}/logs")
        self.logger: ActLogger = ActLogger(log_to_file=True, filename=f"{self.data_folder}/logs/latest.log")
        self.logger.logger.setLevel(logging.DEBUG if config.INDEV else logging.INFO)
        self.logger.monitor_pipe(sys.stdout, level=logging.DEBUG)
        self.logger.monitor_pipe(sys.stderr, level=logging.ERROR)
        self.logger.debug(config.exported_logs)  # Flush config prints

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
            "geometry": "(100, 100, 1050, 640)",
            "provider_type": "direct",
            "chapter_rate": "0.5",
            "no_update_info": "False",
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
            "window_title_template": "DudPy {version}{version_add} {title} ",
            "simulation_loader_max_restart_counter": "5"
        })
        self.abs_window_icon_path: str = self.app_settings.retrieve("window_icon_abs_path")

        # Setup window
        if self.abs_window_icon_path.startswith("#"):
            self.abs_window_icon_path = self.abs_window_icon_path.replace("#", self.base_app_dir, 1)
        self.gui.setWindowIcon(QIcon(self.abs_window_icon_path))
        self.system: BaseSystemType = get_system()
        self.os_theme: SystemTheme = self.get_os_theme()
        # TODO: self.update_theme()
        x, y, height, width = self.user_settings.retrieve("configs", "geometry", "tuple")
        self.gui.setWindowTitle(self.app_settings.retrieve("window_title_template").format(version=self.version, version_add=self.version_add, title=".."))
        self.gui.setGeometry(x, y + 31, height, width)  # Somehow saves it as 31 pixels less,
        self.gui.setup_gui()  # I guess windows does some weird shit with the title bar

        # Setup values, signals, ...
        self.gui.set_scroll_speed(self.user_settings.retrieve("configs", "scrolling_sensitivity", "float"))

        # Show gui
        self.gui.show()
        self.gui.raise_()

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
        do_popup: bool = True

        try:
            response = requests.get("https://raw.githubusercontent.com/Giesbrt/Automaten/main/meta/update_check.json",
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
            print("MSGBox exec start time: ", timer.tock())
            print("Total:", timer.end())
            if do_popup:
                msg_box = QQuickMessageBox(self.gui, icon, title, text, description, checkbox,
                                           standard_buttons=standard_buttons,
                                           default_button=default_button)
                retval = msg_box.exec()  # Keep ref to msg_box so checkbox doesn't get deleted prematurely
                retval_func(retval)
                if checkbox is not None and checkbox.isChecked():
                    self.user_settings.store(*checkbox_setting, value=False, value_type="bool")

    def timer_tick(self):
        # print("Tick")
        # if not self.threading:
        #     self.update_content()
        ...

    def exit(self) -> None:
        if hasattr(self, "timer"):
            self.timer.stop_fires(0, not_exists_okay=True)

    def __del__(self) -> None:
        self.exit()


if __name__ == "__main__":
    CODES: dict[int, _a.Callable] = {
        1000: lambda: os.execv(sys.executable, [sys.executable] + sys.argv)  # RESTART_CODE (only works compiled)
    }
    qapp: QApplication | None = None
    qgui: DBMainWindowInterface | None = None
    dp_app: DudPyApp | None = None
    current_exit_code: int = -1

    try:
        qapp = QApplication(sys.argv)
        qgui = DBMainWindow()
        DudPyApp.gui = qgui
        side_thread = threading.Thread()
        dp_app = DudPyApp()  # Shows gui
        side_thread.start()
        current_exit_code = qapp.exec()
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        title = "Info"
        text = ("There was an error while running the app E.F.S' Simulator.\n"
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
        raise e
    finally:
        if dp_app is not None:
            dp_app.exit()
        if qgui is not None:
            qgui.close()
        if qapp is not None:
            qapp.instance().quit()
        CODES.get(current_exit_code, lambda: sys.exit(current_exit_code))()
