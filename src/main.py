"""TBA"""
import config

config.check()
config.setup()

# Standard imports
from returns import result as _result
from pathlib import Path as PLPath
from traceback import format_exc
from functools import partial
import multiprocessing
from string import Template
from argparse import ArgumentParser
import threading
import logging
import sys
import os
import re

# Third party imports
from packaging.version import Version, InvalidVersion
import stdlib_list
import requests

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QIcon, QDesktopServices

from aplustools.io.env import get_system, SystemTheme, BaseSystemType, diagnose_shutdown_blockers
from aplustools.io import ActLogger
from aplustools.io.fileio import os_open
from aplustools.io.concurrency import LazyDynamicThreadPoolExecutor, ThreadSafeList
from aplustools.io.qtquick import QQuickMessageBox, QtTimidTimer

# Core imports (dynamically resolved)
from core.modules.signal_bus import SignalBus, SingletonObserver
from core.modules.automaton.UIAutomaton import UiAutomaton
from core.modules.automaton.automatonProvider import AutomatonProvider
from core.modules.serializer import serialize, deserialize
from core.modules.storage import MultiUserDBStorage, JSONAppStorage
from core.modules.gui import MainWindow, assign_object_names_iterative, Theme, Style
from core.modules.abstract import IMainWindow, IBackend
from core.modules.automaton_loader import start
from utils.errorCache import ErrorCache, ErrorSeverity
from core.extensions_loader import Extensions_Loader

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

hiddenimports = list(stdlib_list.stdlib_list())
multiprocessing.freeze_support()


class App:
    """The main logic and gui are separated"""

    def __init__(self, window: IMainWindow, qapp: QApplication, input_path: str, logging_level: int | None = None
                 ) -> None:
        try:
            self.window: IMainWindow = window
            self.qapp: QApplication = qapp

            self.base_app_dir: str = config.base_app_dir
            self.data_folder: str = os.path.join(self.base_app_dir, "data")  # Like logs, icons, ...
            self.core_folder: str = os.path.join(self.base_app_dir, "core")  # For core functionality like gui
            self.extensions_folder: str = os.path.join(self.base_app_dir, "extensions")  # Extensions
            self.config_folder: str = os.path.join(self.base_app_dir, "config")  # Configurations
            self.styling_folder: str = os.path.join(self.data_folder, "styling")  # App styling

            # Thread pool
            self.pool = LazyDynamicThreadPoolExecutor(0, 2, 1.0, 1)
            self.for_loop_list: list[tuple[_ty.Callable[[_ty.Any], _ty.Any], tuple[_ty.Any]]] = ThreadSafeList()
            self.pool.submit(lambda :
                             self.for_loop_list.append(
                                 (
                                     self.set_extensions,
                                     (Extensions_Loader(self.base_app_dir).load_content(),)
                                 )
                             ))
            self.extensions: dict[str, list[_ty.Type[_ty.Any]]] | None = None  # None means not yet loaded

            self.window.setup_gui()
            self.control_menu = self.window.user_panel.control_menu

            # Setup logger
            self._order_logs(f"{self.data_folder}/logs")
            self.logger: ActLogger = ActLogger(log_to_file=True, filename=f"{self.data_folder}/logs/latest.log")
            self.logger.setLevel(logging_level or (logging.DEBUG if config.INDEV else logging.INFO))
            self.logger.monitor_pipe(sys.stdout, level=logging.DEBUG)
            self.logger.monitor_pipe(sys.stderr, level=logging.ERROR)
            for exported_line in config.exported_logs.split("\n"):
                self.logger.debug(exported_line)  # Flush config prints

            # Load settings
            self.user_settings: MultiUserDBStorage = MultiUserDBStorage(f"{self.config_folder}/user_settings.db",
                                                                        ("auto", "design", "advanced", "shortcuts"))
            # self.app_settings: JSONAppStorage = JSONAppStorage(f"{config.old_cwd}/locations.json")
            # print(self.app_settings._storage._filepath)
            self.configure_settings()

            self.backend: IBackend = start(None, self.user_settings)
            self.backend_stop_event: threading.Event = threading.Event()
            self.backend_thread: threading.Thread = threading.Thread(target=self.backend.run_infinite,
                                                                     args=(self.backend_stop_event,))
            self.backend_thread.start()

            self.signal_bus = SignalBus()
            self.singleton_observer = SingletonObserver()

            # Automaton backend init
            if input_path != "":
                self.ui_automaton: UiAutomaton | None = self.load_file(input_path)
                if self.ui_automaton is None:
                    input_path = ""
                else:
                    self.singleton_observer.set('is_loaded', True)
                    self.singleton_observer.set('automaton_type', self.ui_automaton.get_automaton_type())
                    self.signal_bus.emit_automaton_changed(
                        is_loaded=True,
                        token_list=self.ui_automaton.get_token_lists()
                    )
            if input_path == "":
                states_with_design = {
                    'default': '',
                    'end': '',
                    'fehler': ''
                }
                self.singleton_observer.set('is_loaded', False)
                self.signal_bus.emit_automaton_changed(is_loaded=False)
                self.ui_automaton: UiAutomaton = UiAutomaton(None, 'TheCodeJak', states_with_design)

            self.load_themes(os.path.join(self.styling_folder, "themes"))
            self.load_styles(os.path.join(self.styling_folder, "styles"))
            self.window.app = self.qapp

            # Setup errorCache
            self.error_cache: ErrorCache = ErrorCache()
            self.error_cache.init(self.window.button_popup, config.INDEV)

            # Setup window
            self.system: BaseSystemType = get_system()
            self.os_theme: SystemTheme = self.get_os_theme()
            self.apply_theme()

            self.update_icon()
            self.update_title()
            self.update_font()
            x, y, height, width = self.user_settings.retrieve("auto", "geometry", "tuple")
            if not self.user_settings.retrieve("advanced", "save_window_dimensions", "bool"):
                height = 640
                width = 1050
            if self.user_settings.retrieve("advanced", "save_window_position", "bool"):
                self.window.set_window_geometry(x, y + 31, height, width)  # Somehow saves it as 31 pixels less,
            else:  # I guess windows does some weird shit with the title bar
                self.window.set_window_dimensions(height, width)
            assign_object_names_iterative(self.window.internal_obj())  # Set object names for theming

            # Setup values, signals, ...
            # TODO: self.window.set_scroll_speed(self.user_settings.retrieve("configs", "scrolling_sensitivity", "float"))

            self.connect_signals()
            # Show gui
            self.pool.submit(lambda : self.check_for_update())
            self.window.start()

            self.timer: QtTimidTimer = QtTimidTimer()
            self.timer.timeout.connect(self.timer_tick)
            self.timer.start(500, 0)
            self.timer_number: int = 1
            # self.timer.start(1500, 1)  # 1.5 second timer
        except Exception as e:
            self.exit()
            raise Exception("Exception occurred during initialization of the App class") from e

    def connect_signals(self):
        grid_view = self.window.user_panel.grid_view
        automaton: UiAutomaton = self.ui_automaton

        self.control_menu.play_button.clicked.connect(self.start_simulation)
        self.control_menu.stop_button.clicked.connect(self.stop_simulation)
        self.control_menu.next_button.clicked.connect(self.next_step)

        self.window.save_file_signal.connect(partial(self.save_to_file, automaton=self.ui_automaton))
        self.window.open_file_signal.connect(self.load_file)

        grid_view.set_is_changeable_token_list.connect(automaton.set_is_changeable_token_list)

        grid_view.add_state.connect(automaton.add_state)
        grid_view.add_transition.connect(automaton.add_transition)
        grid_view.delete_state.connect(automaton.delete_state)
        grid_view.delete_transition.connect(automaton.delete_transition)

        """grid_view.get_start_state.connect(automaton.get_start_state)
        grid_view.get_state_types_with_design.connect(automaton.get_state_types_with_design)
        grid_view.set_state_types_with_design.connect(automaton.set_state_types_with_design)
        grid_view.get_author.connect(automaton.get_author)
        grid_view.get_token_lists.connect(automaton.get_token_lists)
        grid_view.get_is_changeable_token_list.connect(automaton.get_is_changeable_token_list)
        grid_view.get_transition_pattern.connect(automaton.get_transition_pattern)
        grid_view.set_token_lists.connect(automaton.set_token_lists)
        grid_view.set_transition_pattern.connect(automaton.set_transition_pattern)

        grid_view.get_transitions.connect(automaton.get_transitions)
        grid_view.get_automaton_type.connect(automaton.get_automaton_type)
        grid_view.set_start_state.connect(automaton.set_start_state)
        grid_view.get_state_by_id.connect(automaton.get_state_by_id)
        grid_view.get_state_index.connect(automaton.get_state_index)
        grid_view.get_transition_index.connect(automaton.get_transition_index)
        grid_view.get_transition_by_id.connect(automaton.get_transition_by_id)
        grid_view.simulate.connect(automaton.simulate)
        grid_view.handle_simulation_updates.connect(automaton.handle_simulation_updates)
        grid_view.handle_bridge_updates.connect(automaton.handle_bridge_updates)
        grid_view.has_simulation_data.connect(automaton.has_simulation_data)
        grid_view.has_bridge_updates.connect(automaton.has_bridge_updates)
        grid_view.is_simulation_data_available.connect(automaton.is_simulation_data_available)"""

    def start_simulation(self) -> None:
        overlay = self.window.user_panel.control_menu

        if not self.ui_automaton:
            ErrorCache().waring('No Automaton loaded!', '', True, True)
            return
        else:
            current_input = ['a']

            print(self.ui_automaton)
            try:
                result = self.ui_automaton.simulate(current_input)
            except Exception as e:
                ErrorCache().waring(e, '', True, True)
            if isinstance(result, _result.Success):
                overlay.play_button.setEnabled(False)
                overlay.next_button.setEnabled(False)
                overlay.stop_button.setEnabled(True)

                while self.ui_automaton.is_simulation_data_available():
                    sim_result = self.ui_automaton.handle_simulation_updates()
                    if sim_result:
                        if isinstance(sim_result, _result.Failure):
                            print(f"Simulationsfehler: {sim_result.value_or('Unbekannter Fehler')}")
                            self.stop_simulation()
                            break
            else:
                print(f"Fehler beim Starten der Simulation: {result.value_or('Unbekannter Fehler')}")

    def stop_simulation(self):
        if self.ui_automaton:
            self.control_menu.play_button.setEnabled(True)
            self.control_menu.next_button.setEnabled(True)
            self.control_menu.stop_button.setEnabled(False)

    def next_step(self):
        if self.ui_automaton:
            # Hole die aktuelle Eingabe
            current_input = []

            # Führe einen Simulationsschritt aus
            result = self.ui_automaton.simulate(current_input)
            if isinstance(result, _result.Success):
                # Verarbeite das Update des aktuellen Schritts
                sim_result = self.ui_automaton.handle_simulation_updates()
                if sim_result and isinstance(sim_result, _result.Failure):
                    print(f"Fehler im Simulationsschritt: {sim_result.value_or('Unbekannter Fehler')}")
                    self.stop_simulation()

    def set_extensions(self, extensions: dict[str, list[_ty.Type[_ty.Any]]]) -> None:
        self.extensions = extensions
        AutomatonProvider(None).load_from_dict(extensions)

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
            start_date = re.search(date_pattern, first_line).group(1)  # type: ignore
            end_date = re.search(date_pattern, last_line).group(1)  # type: ignore
        except AttributeError:
            print("Removing malformed latest.log")
            os.remove(to_log_file)
            return

        date_name = f"{start_date}_{end_date}"
        date_logs = list(logs_dir.rglob(f"{date_name}*.log"))

        if not date_logs:
            new_log_file_name = logs_dir / f"{date_name}.log"
        else:
            try:
                max_num = max(
                    (int(re.search(r"#(\d+)$", p.stem).group(1)) for p in date_logs if  # type: ignore
                     re.search(r"#(\d+)$", p.stem)),
                    default=0
                )
            except AttributeError:
                return
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
        """TBA"""
        update_result = self.get_update_result()
        self.for_loop_list.append((self.show_update_result, (update_result,)))

    @staticmethod
    def load_file(filepath: str) -> UiAutomaton | None:
        """Loads a UIAutomaton from a serialized file.
        Returns an UIAutomaton upon successful load or None if an error occurred."""
        end = filepath.rsplit(".", maxsplit=1)[1]
        try:
            with os_open(filepath, "rb") as f:
                content: bytes = f.read()
        except OSError as e:  # File locking problems
            ErrorCache().warning(
                f"The loading of the file '{os.path.basename(filepath)}' has failed.\nThe file could not be locked.",
                format_exc(), True, True)
            return None
        filetype: _ty.Literal["json", "yaml", "binary"] | None = {"json": "json", "yml": "yaml", "yaml": "yaml", "au": "binary"}.get(end, None)  # type: ignore
        if filetype is None:  # Error case
            ErrorCache().warning(
                f"The loading of the file '{os.path.basename(filepath)}' has failed.\nIncompatible file extension.", "",
                True, True)
            return None
        try:
            automaton: UiAutomaton = deserialize(content, filetype)
        except Exception as e:
            ErrorCache().warning(
                f"The loading of the file '{os.path.basename(filepath)}' has failed.\nThe file may be corrupted.",
                format_exc(), True, True)
            return None
        return automaton

    @staticmethod
    def save_to_file(filepath: str, automaton: UiAutomaton) -> str | None:
        """Saves a UIAutomaton to a file.
        Returns the filepath upon successful save or None if an error occurred."""
        end = filepath.rsplit(".", maxsplit=1)[1]
        filetype: _ty.Literal["json", "yaml", "binary"] | None = {"json": "json", "yml": "yaml", "yaml": "yaml", "au": "binary"}.get(end, None)  # type: ignore
        if filetype is None:  # Error case
            ErrorCache().warning(
                f"The saving to the file '{os.path.basename(filepath)}' has failed.\nIncompatible file extension.", "",
                True, True)
            return None
        try:
            print(automaton, filetype)
            content: bytes = serialize(automaton, "", filetype)
            with os_open(filepath, "wb") as f:
                f.write(content)
        except OSError as e:  # File locking problems
            ErrorCache().warning(
                f"The saving to the file '{os.path.basename(filepath)}' has failed.\nThe file could not be locked.",
                format_exc(), True, True)
        except Exception as e:  # serialization error
            ErrorCache().warning(
                f"The saving to the file '{os.path.basename(filepath)}' has failed.\nThere was an internal serialization error.",
                format_exc(), True, True)
        else:
            return filepath
        return None

    def get_update_result(self) -> tuple[bool, tuple[str, str, str, str], tuple[str | None, tuple[str, str]], tuple[list[str], str], _a.Callable[[str], _ty.Any]]:
        """
        Checks for an update and returns the result.
        """
        icon: str = "Information"
        title: str = "Title"
        text: str = "Text"
        description: str = "Description"
        checkbox: str | None = None
        checkbox_setting: tuple[str, str] = ("", "")
        standard_buttons: list[str] = ["Ok"]
        default_button: str = "Ok"
        retval_func: _a.Callable[[str], _ty.Any] = lambda button: None
        do_popup: bool = True

        try:  # Get update content
            response: requests.Response = requests.get(
                "https://raw.githubusercontent.com/Giesbrt/Automaten/main/meta/update_check.json",
                timeout=self.user_settings.retrieve("advanced", "update_check_request_timeout", "float"))
        except requests.exceptions.Timeout:
            title, text, description = "Update Info", ("The request timed out.\n"
                                                       "Please check your internet connection, "
                                                       "and try again."), format_exc()
            standard_buttons, default_button = ["Ok"], "Ok"
            checkbox, checkbox_setting = "Do not show again", ("auto", "show_update_timeout")
            show_update_timeout: bool = self.user_settings.retrieve("auto", "show_update_timeout", "bool")
            if not show_update_timeout:
                do_popup = False
            return (do_popup,
                    (icon, title, text, description),
                    (checkbox, checkbox_setting),
                    (standard_buttons, default_button), retval_func)
        except requests.exceptions.RequestException:
            title, text, description = "Update Info", ("There was an error with the request.\n"
                                                       "Please check your internet connection and antivirus, "
                                                       "and try again."), format_exc()
            standard_buttons, default_button = ["Ok"], "Ok"
            return (do_popup,
                    (icon, title, text, description),
                    (checkbox, checkbox_setting),
                    (standard_buttons, default_button), retval_func)

        try:  # Parse update content
            update_json: dict = response.json()
            current_version = Version(f"{config.VERSION}{config.VERSION_ADD}")
            found_version: Version | None = None
            found_release: dict | None = None
            found_push: bool = False

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
                if found_release and found_version != current_version:
                    raise NotImplementedError
        except (requests.exceptions.JSONDecodeError, InvalidVersion, NotImplementedError):
            icon = "Information"  # Reset everything to default, we don't know when the error happened
            title, text, description = "Update Info", "There was an error when decoding the update info.", format_exc()
            checkbox, checkbox_setting = None, ("", "")
            standard_buttons, default_button = ["Ok"], "Ok"
            retval_func = lambda button: None
            return (do_popup,
                    (icon, title, text, description),
                    (checkbox, checkbox_setting),
                    (standard_buttons, default_button), retval_func)

        show_update_info: bool = self.user_settings.retrieve("auto", "show_update_info", "bool")
        show_no_update_info: bool = self.user_settings.retrieve("auto", "show_no_update_info", "bool")

        if found_version != current_version and show_update_info and found_push:
            title = "There is an update available"
            text = (f"There is a newer version ({found_version}) "
                    f"available.\nDo you want to open the link to the update?")
            description = str(found_release.get("description"))  # type: ignore
            checkbox, checkbox_setting = "Do not show again", ("auto", "show_update_info")
            standard_buttons, default_button = ["Yes", "No"], "Yes"

            def retval_func(button: str) -> None:
                """TBA"""
                if button == "Yes":
                    url = str(found_release.get("updateUrl", "None"))  # type: ignore
                    if url.title() == "None":
                        link = update_json["metadata"].get("sorryUrl", "https://example.com")
                    else:
                        link = url
                    QDesktopServices.openUrl(QUrl(link))
        elif show_no_update_info and found_version == current_version:
            title = "Update Info"
            text = (f"No new updates available.\nChecklist last updated "
                    f"{update_json['metadata']['lastUpdated'].replace('-', '.')}.")
            description = f" --- v{found_version} --- \n{found_release.get('description')}"  # type: ignore
            checkbox, checkbox_setting = "Do not show again", ("auto", "show_no_update_info")
        elif show_no_update_info and found_push:
            title = "Info"
            text = (f"New version available, but not recommended {found_version}.\n"
                    f"Checklist last updated {update_json['metadata']['lastUpdated'].replace('-', '.')}.")
            description = str(found_release.get("description"))  # type: ignore
            checkbox, checkbox_setting = "Do not show again", ("auto", "show_no_update_info")
        else:
            title, text, description = "Update Info", "There was a logic-error when checking for updates.", ""
            do_popup = False
        return (do_popup,
                (icon, title, text, description),
                (checkbox, checkbox_setting),
                (standard_buttons, default_button), retval_func)

    def show_update_result(self, update_result: tuple[bool, tuple[str, str, str, str], tuple[str | None, tuple[str, str]], tuple[list[str], str], _a.Callable[[str], _ty.Any]]) -> None:
        """
        Shows update result using a message box
        """
        (do_popup,
         (icon, title, text, description),
         (checkbox, checkbox_setting),
         (standard_buttons, default_button), retval_func) = update_result
        if do_popup:
            retval, checkbox_checked = self.window.button_popup(title, text, description, icon, standard_buttons,
                                                                default_button, checkbox)
            retval_func(retval)
            if checkbox is not None and checkbox_checked:
                self.user_settings.store(*checkbox_setting, value=False, value_type="bool")

    def update_icon(self) -> None:
        """Updates the window icon with data from the settings"""
        window_icon_set_path: str = self.user_settings.retrieve("design", "window_icon_set", "string")
        if window_icon_set_path.startswith(":"):
            window_icon_set_path = window_icon_set_path.replace(":", self.base_app_dir, 1)
        self.window.set_window_icon(os.path.join(window_icon_set_path, "logo-nobg.png"))

    def update_title(self) -> None:
        """Updates the window title with data from the settings"""
        raw_title: Template = Template(
            self.user_settings.retrieve("design", "window_title_template", "string"))
        formatted_title: str = raw_title.safe_substitute(version=config.VERSION, version_add=config.VERSION_ADD)
        self.window.set_window_title(formatted_title)

    def update_font(self) -> None:
        """Updates the window font with data from the settings. This is an expensive operation."""
        self.window.set_font(self.user_settings.retrieve("design", "font", "string"))

    def configure_settings(self) -> None:
        self.user_settings.set_default_settings("auto", {
            "geometry": "(100, 100, 1050, 640)",
            "show_no_update_info": "False",
            "show_update_info": "True",
            "show_update_timeout": "True",
            # "last_scroll_positions": "(0, 0, 0, 0)",
            # "scrolling_sensitivity": "4.0",
            "ask_to_reopen_last_opened_file": "True",
            "recent_files": "()"
        })
        self.user_settings.set_default_settings("design", {
            "light_theming": "adalfarus::thin/thin_light",  # thin_light_dark, colored_summer_sky
            "dark_theming": "adalfarus::thin/colored_evening_sky",
            # "dark_theming": "adalfarus::thick/thick_light",
            # "dark_theming": "adalfarus::chisled/base",
            # "dark_theming": "adalfarus::modern/base",
            # "dark_theming": "adalfarus::default/base",
            "window_icon_set": ":/data/assets/app_icons/shelline",
            "font": "Segoe UI",
            "window_title_template": f"{config.PROGRAM_NAME} $version$version_add $title" + (" [INDEV]" if config.INDEV else ""),
            "high_contrast_mode": "NO",  # Just make a high contrast theme
            "automaton_scaling": "NO",  # Why? We could manipulate the scroll max and mins
            "automatic_scaling": "True",  # Would enable / disable next two options
            "larger_icons": "FORNOWNO",  # Would require theme loader mods
            "font_size": "automatic",  # idk, also mods to theme loader
            "enable_animations": "True",
            "auto_open_tutorial_tab": "True",
            "default_state_background_color": "#FFFFFFFF",
            "transition_func_seperator": "/"
        })
        self.user_settings.set_default_settings("security", {
            "warn_of_unsigned_plugins": "True",
            "run_plugin_in_seperate_process": "False",
            "user_safe_file_access": "True"
        })
        self.user_settings.set_default_settings("advanced", {
            "hide_titlebar": "False",
            # "hide_scrollbar": "True",
            "stay_on_top": "False",
            "settings_backup_file_path": "",
            "settings_backup_file_mode": "overwrite",
            "settings_backup_auto_export": "False",
            "save_window_dimensions": "True",
            "save_window_position": "False",
            "update_check_request_timeout": "2.0",
            "max_timer_tick_handled_events": "5",
            "logging_mode": "DEBUG" if config.INDEV else "INFO",
        })
        self.user_settings.set_default_settings("shortcuts", {
            "file_open": "Ctrl+O",  # "" means disabled
            "file_save": "Ctrl+S",
            "file_close": "Ctrl+Q",
            "simulation_start": "Ctrl+G",
            "simulation_step": "Ctrl+T",
            "simulation_halt": "Ctrl+H",
            "simulation_end": "Ctrl+Y",
            "states_cut": "Ctrl+X",
            "states_copy": "Ctrl+C",
            "states_paste": "Ctrl+V",
        })
        self.user_settings.set_default_settings("general", {
            "app_language": "enUS",
            "open_last_file_on_startup": "True",
            "launch_at_system_startup": "False"
        })

    def load_themes(self, theme_folder: str, clear: bool = False) -> None:
        """Loads all theme files from styling/themes"""
        if clear:
            Theme.clear_loaded_themes()
        for file in os.listdir(theme_folder):
            if file.endswith(".th"):
                path = os.path.join(theme_folder, file)
                Theme.load_from_file(path)

        if Theme.get_loaded_theme("adalfarus::base") is None:
            raise RuntimeError(f"Base theme is not present")

    def load_styles(self, style_folder: str, clear: bool = False) -> None:
        """Loads all styles from styling/styles"""
        if clear:
            Style.clear_loaded_styles()
        for file in os.listdir(style_folder):
            if file.endswith(".st"):
                path = os.path.join(style_folder, file)
                Style.load_from_file(path)

        if (Style.get_loaded_style("Default Dark", "*") is None
                or Style.get_loaded_style("Default Light", "*") is None):
            raise RuntimeError(f"Default light and/or dark style are/is not present")

    def apply_theme(self) -> None:
        theming_str: str = self.user_settings.retrieve("design",
                                                       {SystemTheme.LIGHT: "light_theming",
                                                        SystemTheme.DARK: "dark_theming"}[self.os_theme],
                                                       "string")
        theme_str, style_str = theming_str.split("/", maxsplit=1)
        theme = Theme.get_loaded_theme(theme_str)

        if theme is None:  # TODO: Popup
            self.logger.warning(f"Specified theme '{theme}' is not available")
            return
        style = theme.get_compatible_style(style_str.replace("_", " ").title())
        theme_str, palette = theme.apply_style(style, self.qapp.palette(),
                                               transparency_mode="none")  # TODO: Get from settings
        self.qapp.setPalette(palette)
        self.window.set_global_theme(theme_str, getattr(self.window.AppStyle, theme.get_base_styling()))

    def check_theme_change(self):
        if self.timer_number & 1 == 1:
            current_os_theme = self.get_os_theme()
            if current_os_theme != self.os_theme:
                self.os_theme = current_os_theme
                self.apply_theme()

    def timer_tick(self, index: int) -> None:
        if index == 0:  # Default 500ms timer
            self.update_icon()
            self.update_title()
            # self.update_font()
            self.check_theme_change()
            self.timer_number += 1
            if self.timer_number > 999:
                self.timer_number = 1

            # display cached Errors
            self.error_cache.invoke_popup()

            num_handled: int = 0
            while len(self.for_loop_list) > 0 and num_handled < 5:
                entry = self.for_loop_list.pop()
                func, args = entry
                func(*args)
                num_handled += 1
            # print(self.extensions)
        else:
            print("Tock")
        # if not self.threading:
        #     self.update_content()
        ...

    def exit(self) -> None:
        if hasattr(self, "timer"):
            self.timer.stop_all()
        if hasattr(self, "pool"):
            self.pool.shutdown()
        if hasattr(self, "backend_thread") and self.backend_thread.is_alive():  # TODO: Is it alive after error?
            self.backend_stop_event.set()
            self.backend_thread.join()

    def __del__(self) -> None:
        self.exit()


if __name__ == "__main__":
    print(f"Starting {config.PROGRAM_NAME} {str(config.VERSION) + config.VERSION_ADD} with py{'.'.join([str(x) for x in sys.version_info])} ...")
    CODES: dict[int, _a.Callable[[], None]] = {
        1000: lambda: os.execv(sys.executable, [sys.executable] + sys.argv)  # RESTART_CODE (only works compiled)
    }
    qapp: QApplication | None = None
    qgui: IMainWindow | None = None
    dp_app: App | None = None
    current_exit_code: int = -1

    parser = ArgumentParser(description=f"{config.PROGRAM_NAME}")
    parser.add_argument("input", nargs="?", default="", help="Path to the input file.")
    parser.add_argument("--logging-mode", choices=["DEBUG", "INFO", "WARN", "ERROR"], default=None,
                        help="Logging mode (default: None)")
    args = parser.parse_args()

    logging_mode: str = args.logging_mode
    logging_level: int | None = None
    if logging_mode is not None:
        logging_level = getattr(logging, logging_mode.upper(), None)
        if logging_level is None:
            logging.error(f"Invalid logging mode: {logging_mode}")

    input_path: str = ""
    if args.input != "":
        input_path = os.path.abspath(args.input)

        if not os.path.exists(input_path):
            logging.error(f"The input file ({input_path}) needs to exist")
            input_path = ""
        else:
            config.exported_logs += f"Reading {input_path}\n"

    try:
        qapp = QApplication(sys.argv)
        qgui = MainWindow()
        dp_app = App(qgui, qapp, input_path, logging_level)  # Shows gui
        current_exit_code = qapp.exec()
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        error_title = "Info"
        error_text = (f"There was an error while running the app {config.PROGRAM_NAME}.\n"
                      "This error is unrecoverable.\nPlease submit the details to our GitHub issues page.")
        error_description = format_exc()

        icon: QIcon = QIcon(QMessageBox.standardIcon(QMessageBox.Icon.Warning))
        custom_icon: bool = False
        if hasattr(dp_app, "abs_window_icon_path"):
            icon_path = dp_app.abs_window_icon_path
            icon = QIcon(icon_path)
            custom_icon = True

        msg_box = QQuickMessageBox(None, QMessageBox.Icon.Warning if custom_icon else None, error_title, error_text, error_description,
                                   standard_buttons=QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Retry,
                                   default_button=QMessageBox.StandardButton.Ok)
        msg_box.setWindowIcon(icon)
        pressed_button = msg_box.exec()
        if pressed_button == QMessageBox.StandardButton.Retry:
            current_exit_code = 1000

        logger: logging.Logger = logging.getLogger("ActLogger")
        if not logger.hasHandlers():
            print(error_description.strip())  # We print, in case the logger is not initialized yet
        else:
            for line in error_description.strip().split("\n"):
                logger.error(line)
    finally:
        if dp_app is not None:
            dp_app.exit()
        if qgui is not None:
            qgui.close()
        if qapp is not None:
            qapp.instance().quit()
        diagnose_shutdown_blockers()
        CODES.get(current_exit_code, lambda: sys.exit(current_exit_code))()
