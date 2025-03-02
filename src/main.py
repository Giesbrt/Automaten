"""TBA"""
import config
config.check()
config.setup()

# Std Lib imports
from argparse import ArgumentParser
from traceback import format_exc
from functools import partial
from string import Template
import multiprocessing
import threading
import logging
import sys
import os

# Third party imports
from packaging.version import Version, InvalidVersion
from returns import result as _result
import stdlib_list
import requests
# PySide6
from PySide6.QtWidgets import QApplication, QMessageBox, QSizePolicy
from PySide6.QtGui import QIcon, QDesktopServices, Qt
from PySide6.QtCore import QUrl
# aplustools
from aplustools.io.env import get_system, SystemTheme, BaseSystemType, diagnose_shutdown_blockers
from aplustools.io.fileio import os_open
from aplustools.io.concurrency import LazyDynamicThreadPoolExecutor, ThreadSafeList
from aplustools.io.qtquick import QQuickMessageBox, QtTimidTimer

# Internal imports
from automaton.UIAutomaton import UiAutomaton
from automaton.automatonProvider import AutomatonProvider
from serializer import serialize, deserialize
from storage import MultiUserDBStorage
from gui import MainWindow, assign_object_names_iterative, Theme, Style
from abstractions import IMainWindow, IBackend, IAppSettings
from automaton import start_backend
from utils.IOManager import IOManager
from utils.staticSignal import SignalCache
from automaton.UiSettingsProvider import UiSettingsProvider
from customPythonHandler import CustomPythonHandler
from extensions_loader import Extensions_Loader
from automaton.base.QAutomatonInputWidget import QAutomatonInputOutput

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts


hiddenimports = list(stdlib_list.stdlib_list())
multiprocessing.freeze_support()


class AppSettings(IAppSettings):
    """TBA"""
    _settings: MultiUserDBStorage

    def __init__(self) -> None:
        ...

    def init(self, settings_folder_path: str) -> None:
        """Initializes the AppSettings"""
        self._settings: MultiUserDBStorage = MultiUserDBStorage(f"{settings_folder_path}/user_settings.db",
                                                                    ("auto", "design", "advanced", "shortcuts"))
        # self.app_settings: JSONAppStorage = JSONAppStorage(f"{config.old_cwd}/locations.json")
        # print(self.app_settings._storage._filepath)
        self._configure_settings()

    def _configure_settings(self) -> None:
        self._settings.set_default_settings("auto", {
            "geometry": "(100, 100, 1050, 640)",
            "show_no_update_info": "False",
            "show_update_info": "True",
            "show_update_timeout": "True",
            # "last_scroll_positions": "(0, 0, 0, 0)",
            # "scrolling_sensitivity": "4.0",
            "ask_to_reopen_last_opened_file": "True",
            "recent_files": "()"
        })
        self._settings.set_default_settings("design", {
            "light_theming": "adalfarus::thin/thin_light_green",  # thin_light_dark, colored_summer_sky
            "dark_theming": "adalfarus::thin/colored_evening_sky",
            # "dark_theming": "adalfarus::thick/thick_light",
            # "dark_theming": "adalfarus::chisled/base",
            # "dark_theming": "adalfarus::modern/base",
            # "dark_theming": "adalfarus::default/base",
            "window_icon_set": ":/data/assets/app_icons/shelline",
            "font": "Segoe UI",
            "window_title_template": f"{config.PROGRAM_NAME} $version$version_add $title" + (
                " [INDEV]" if config.INDEV else ""),
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
        self._settings.set_default_settings("security", {
            "warn_of_unsigned_plugins": "True",
            "run_plugin_in_seperate_process": "False",
            "user_safe_file_access": "True"
        })
        self._settings.set_default_settings("advanced", {
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
        self._settings.set_default_settings("shortcuts", {
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
        self._settings.set_default_settings("general", {
            "app_language": "enUS",
            "open_last_file_on_startup": "True",
            "launch_at_system_startup": "False"
        })

    def get_window_geometry(self) -> tuple[int, int, int, int]:
        return self._settings.retrieve("auto", "geometry", "tuple")  # type: ignore

    def set_window_geometry(self, window_geometry: tuple[int, int, int, int]) -> None:
        self._settings.store("auto", "geometry", window_geometry, "tuple")

    def get_save_window_dimensions(self) -> bool:
        return self._settings.retrieve("advanced", "save_window_dimensions", "bool")  # type: ignore

    def set_save_window_dimensions(self, flag: bool) -> None:
        self._settings.store("advanced", "save_window_dimensions", flag, "bool")

    def get_save_window_position(self) -> bool:
        return self._settings.retrieve("advanced", "save_window_position", "bool")  # type: ignore

    def set_save_window_position(self, flag: bool) -> None:
        self._settings.store("advanced", "save_window_position", flag, "bool")


class App:
    """The main logic and gui are separated"""
    def __init__(self, window: IMainWindow, qapp: QApplication, input_path: str, logging_level: int | None = None
                 ) -> None:
        try:
            self.window: IMainWindow = window
            self.qapp: QApplication = qapp
            self.window.app = self.qapp

            self.base_app_dir: str = config.base_app_dir
            self.data_folder: str = os.path.join(self.base_app_dir, "data")  # Like logs, icons, ...
            self.core_folder: str = os.path.join(self.base_app_dir, "core")  # For core functionality like gui
            self.extensions_folder: str = os.path.join(self.base_app_dir, "extensions")  # Extensions
            self.config_folder: str = os.path.join(self.base_app_dir, "config")  # Configurations
            self.styling_folder: str = os.path.join(self.data_folder, "styling")  # App styling

            print(1)

            # Thread pool
            self.pool = LazyDynamicThreadPoolExecutor(0, 2, 1.0, 1)
            self.for_loop_list: list[tuple[_ty.Callable[[_ty.Any], _ty.Any], tuple[_ty.Any]]] = ThreadSafeList()
            self.pool.submit(lambda:
                             self.for_loop_list.append(
                                 (
                                     self.set_extensions,
                                     (Extensions_Loader(self.base_app_dir).load_content(),)
                                 )
                             ))
            self.pool.submit(self.check_for_update)
            self.extensions: dict[str, list[_ty.Type[_ty.Any]]] | None = None  # None means not yet loaded
            print(2)


            # Automaton backend init
            # self.singleton_observer = SingletonObserver()
            self.ui_automaton: UiAutomaton = UiAutomaton(None, 'TheCodeJak', {}) # Placeholder
            # self.singleton_observer.set('is_loaded', False)
            if input_path != "":
                success: bool = self.load_file(input_path)
                if not success:
                    print('Could not load file')
                    # ErrorCache().error("Could not load file", "", True, True)
                    """self.singleton_observer.set('automaton_type', self.ui_automaton.get_automaton_type())
                    self.singleton_observer.set('token_lists', self.ui_automaton.get_token_lists())
                    self.singleton_observer.set('is_loaded', True)"""

            print(3)

            self.window.setup_gui(self.ui_automaton)
            # self.window.user_panel.setShowScrollbars(False)
            # self.window.user_panel.setAutoShowInfoMenu(False)
            self.grid_view = self.window.user_panel.grid_view
            self.control_menu = self.window.user_panel.control_menu

            print(4)

            # Setup IOManager
            self.io_manager: IOManager = IOManager()
            self.io_manager.init(self.window.button_popup, f"{self.data_folder}/logs", config.INDEV)
            self.io_manager.set_logging_level(logging_level or (logging.DEBUG if config.INDEV else logging.INFO))
            for exported_line in config.exported_logs.split("\n"):
                self.io_manager.debug(exported_line)  # Flush config prints

            print(5)

            # Settings
            self.settings: AppSettings = AppSettings()
            self.settings.init(self.config_folder)

            self.backend: IBackend = start_backend(self.settings)
            self.backend_stop_event: threading.Event = threading.Event()
            self.backend_thread: threading.Thread = threading.Thread(target=self.backend.run_infinite,
                                                                     args=(self.backend_stop_event,))
            self.backend_thread.start()

            print(6)

            # Setup window
            self.system: BaseSystemType = get_system()
            self.os_theme: SystemTheme = self.get_os_theme()
            self.load_themes(os.path.join(self.styling_folder, "themes"))
            self.load_styles(os.path.join(self.styling_folder, "styles"))
            # self.window.set_recently_opened_files(list(self.user_settings.retrieve("auto", "recent_files", "tuple")))

            print(7)

            x, y, height, width = self.settings.get_window_geometry()
            if not self.settings.get_save_window_dimensions():
                height = 640
                width = 1050
            if self.settings.get_save_window_position():
                self.window.set_window_geometry(x, y + 31, height, width)  # Somehow saves it as 31 pixels less,
            else:  # I guess windows does some weird shit with the title bar
                self.window.set_window_dimensions(height, width)

            print(8)

            # assign_object_names_iterative(self.window.internal_obj())  # Set object names for theming
            self.apply_theme()
            print(1.1)
            self.connect_signals()
            print(1.2)
            # self.timer_tick(0)  # Updates everything
            print(1.3)
            self.window.start()  # Shows gui

            print(9)

            self.timer: QtTimidTimer = QtTimidTimer()
            self.timer.timeout.connect(self.timer_tick)
            # self.timer.start(500, 0)
            self.timer_number: int = 1
        except Exception as e:
            self.exit()
            raise Exception("Exception occurred during initialization of the App class") from e

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

    def check_for_update(self) -> None:
        """TBA"""
        update_result = self.get_update_result()
        self.for_loop_list.append((self.show_update_result, (update_result,)))

    def get_os_theme(self) -> SystemTheme:
        """Gets the os theme based on a number of parameters, like environment variables."""
        base = self.system.get_system_theme()
        if not base:
            raw_fallback = str(os.environ.get("BACKUP_THEME")).lower()  # Can return None
            fallback = {"light": SystemTheme.LIGHT, "dark": SystemTheme.DARK}.get(raw_fallback)
            if fallback is None:
                return SystemTheme.LIGHT
            return fallback
        return base

    def connect_signals(self) -> None:
        automaton: UiAutomaton = self.ui_automaton

        self.control_menu.play_button.clicked.connect(lambda: self.start_simulation(['a', 'b']))
        self.control_menu.stop_button.clicked.connect(self.stop_simulation)
        self.control_menu.next_button.clicked.connect(lambda: self.start_simulation_step_for_step(['a', 'b']))

        self.window.save_file_signal.connect(partial(self.save_to_file, automaton=self.ui_automaton))
        self.window.open_file_signal.connect(self.open_file)

        self.grid_view.set_transition_pattern.connect(automaton.set_transition_pattern)
        self.grid_view.set_is_changeable_token_list.connect(automaton.set_is_changeable_token_list)

        self.grid_view.add_state.connect(automaton.add_state)
        self.grid_view.add_transition.connect(automaton.add_transition)
        self.grid_view.delete_state.connect(automaton.delete_state)
        self.grid_view.delete_transition.connect(automaton.delete_transition)
        # self.window.settings_changed.connect(self.set_settings)

    def set_settings(self, settings_to_be_changed: dict[str, dict[str, str]]):
        self.window.set_font(self.user_settings.retrieve("design", "font", "string"))
        self.window.set_enable_animations(self.user_settings.retrieve("design", "enable_animations", "bool"))
        self.window.set_auto_open_tutorial_tab(
            self.user_settings.retrieve("design", "auto_open_tutorial_tab", "string"))
        self.window.set_transition_func_separator(
            self.user_settings.retrieve("design", "transition_func_separator", "string"))
        self.window.set_default_state_background_color(
            self.user_settings.retrieve("design", "default_state_background_color", "str"))

        self.window.set_file_open_shortcut(self.user_settigs.retrieve("shortcuts", "file_open", "string"))
        self.window.set_file_save_shortcut(self.user_settigs.retrieve("shortcuts", "file_save", "string"))
        self.window.set_file_close_shortcut(self.user_settigs.retrieve("shortcuts", "file_close", "string"))
        self.window.set_simulation_start_shortcut(self.user_settigs.retrieve("shortcuts", "simulation_start", "string"))
        self.window.set_simulation_step_shortcut(self.user_settigs.retrieve("shortcuts", "simulation_step", "string"))
        self.window.set_simulation_halt_shortcut(self.user_settigs.retrieve("shortcuts", "simulation_halt", "string"))
        self.window.set_simulation_end_shortcut(self.user_settigs.retrieve("shortcuts", "simulation_end", "string"))
        self.window.set_states_cut_shortcut(self.user_settigs.retrieve("shortcuts", "states_cut", "string"))
        self.window.set_states_copy_shortcut(self.user_settigs.retrieve("shortcuts", "states_copy", "string"))
        self.window.set_states_paste_shortcut(self.user_settigs.retrieve("shortcuts", "states_paste", "string"))

    def update_simulation_controls(self, running: bool) -> None:
        if self.simulation_mode == 'auto':
            self.control_menu.play_button.setEnabled(not running)
            self.control_menu.next_button.setEnabled(False)
            self.control_menu.stop_button.setEnabled(running)
        elif self.simulation_mode == 'step':
            self.control_menu.play_button.setEnabled(True)
            self.control_menu.next_button.setEnabled(True)
            self.control_menu.stop_button.setEnabled(running)
        else:
            self.control_menu.play_button.setEnabled(True)
            self.control_menu.next_button.setEnabled(True)
            self.control_menu.stop_button.setEnabled(False)

    def start_simulation(self, automaton_input: _ty.List[str]) -> None:
        self.simulation_mode = 'auto'
        if not self.ui_automaton:
            IOManager().warning('No Automaton loaded!', '', True, True)
            return
        else:
            try:
                result = self.ui_automaton.simulate(automaton_input, self.handle_simulation)
                if isinstance(result, _result.Success):
                    self.update_simulation_controls(running=True)
                elif isinstance(result, _result.Failure):
                    IOManager().info('Fehler beim Simulieren aufgetreten!', '', True, True)
            except Exception as e:
                IOManager().error('External simulation error!', f'{e}', True, True)

    def stop_simulation(self) -> None:
        self.grid_view.reset_all_highlights()
        if self.ui_automaton:
            self.ui_automaton.stop_simulation()
            self.simulation_mode = None
            self.update_simulation_controls(running=False)
            IOManager().info('Finished Simulation!', '', True, False)

    def handle_simulation(self) -> None:
        self.simulation_timer = QtTimidTimer()
        self.simulation_timer.timeout.connect(self.start_simulation_visualisation)
        self.simulation_timer.start(500, 0)

    def start_simulation_visualisation(self):
        if self.ui_automaton.has_simulation_data():
            simulation_result: _ty.Dict = self.ui_automaton.handle_simulation_updates()._inner_value
            active_state: 'UiState' = self.ui_automaton.get_active_state()
            active_transition: 'UiTransition' = self.ui_automaton.get_active_transition()
            state_item = self.grid_view.get_active_state(active_state)
            self.grid_view.highlight_state_item(state_item)

            if active_transition:
                transition_item = self.grid_view.get_active_transition(active_transition)
                self.grid_view.highlight_transition_item(transition_item)
        else:
            self.simulation_timer.stop(0)
            self.stop_simulation()

    def start_simulation_step_for_step(self, automaton_input: _ty.List[str]) -> None:
        self.simulation_mode = 'step'
        if self.ui_automaton and not self.ui_automaton.has_simulation_data():
            result = self.ui_automaton.simulate(automaton_input, self.step_simulation)
            if isinstance(result, _result.Success):
                self.update_simulation_controls(running=True)
        else:
            self.step_simulation()

    def step_simulation(self) -> None:
        if self.ui_automaton.has_simulation_data():
            if self.simulation_mode == 'auto':
                self.update_simulation_controls(running=True)
            else:
                self.control_menu.play_button.setEnabled(True)
                self.control_menu.next_button.setEnabled(True)
                self.control_menu.stop_button.setEnabled(True)
            simulation_result: _ty.Dict = self.ui_automaton.handle_simulation_updates()._inner_value
            active_state: 'UiState' = self.ui_automaton.get_active_state()
            active_transition: 'UiTransition' = self.ui_automaton.get_active_transition()
            state_item = self.grid_view.get_active_state(active_state)

            self.grid_view.highlight_state_item(state_item)
            if active_transition:
                transition_item = self.grid_view.get_active_transition(active_transition)
                self.grid_view.highlight_transition_item(transition_item)
        else:
            self.stop_simulation()

    def set_extensions(self, extensions: dict[str, list[_ty.Type[_ty.Any]]]) -> None:
        self.extensions = extensions
        if not self.extensions:
            self.io_manager.error('No extensions loaded!', '', True, True, error_severity=ErrorSeverity.FATAL)

        AutomatonProvider(None).load_from_dict(extensions)
        UiSettingsProvider().load_from_incoherent_mess(self.extensions)

        # apply settings
        settings_loader: UiSettingsProvider = UiSettingsProvider()
        automaton_type: str = self.ui_automaton.get_automaton_type()  # TODO: This may not be loaded yet ...
        automaton_settings = settings_loader.get_settings(automaton_type)
        if automaton_settings is not None:
            settings_loader.apply_to_automaton(self.ui_automaton, None, automaton_settings)
            # widget: QAutomatonInputOutput = self.ui_automaton.get_input_widget()
            # self.window.user_panel.position_input_widget(widget)

            self.io_manager.debug(f"Applied settings to {automaton_type}-automaton", "")
        else:
            self.io_manager.error(f"Could not load and apply settings of {automaton_type}", "", True)

    def open_file(self, filepath: str) -> None:
        """Opens a file and notifies the GUI to update"""
        success: bool = self.load_file(filepath)
        if not success:
            return

        self.singleton_observer.set('automaton_type', self.ui_automaton.get_automaton_type())
        self.singleton_observer.set('token_lists', self.ui_automaton.get_token_lists())
        self.singleton_observer.set('is_loaded', True)

    def load_file(self, filepath: str) -> bool:
        """Loads a UIAutomaton from a serialized file.
        Returns an UIAutomaton upon successful load or None if an error occurred."""
        end = filepath.rsplit(".", maxsplit=1)[1]
        try:
            with os_open(filepath, "rb") as f:
                content: bytes = f.read()
        except OSError as e:  # File locking problems
            self.io_manager.warning(
                f"The loading of the file '{os.path.basename(filepath)}' has failed.\nThe file could not be locked.",
                format_exc(), True, True)
            return False
        filetype: _ty.Literal["json", "yaml", "binary"] | None = {"json": "json", "yml": "yaml", "yaml": "yaml",
                                                                  "au": "binary"}.get(end, None)  # type: ignore
        if filetype is None:  # Error case
            self.io_manager.warning(
                f"The loading of the file '{os.path.basename(filepath)}' has failed.\nIncompatible file extension.", "",
                True, True)
            return False
        try:
            self.ui_automaton.unload()
            custom_python: str = deserialize(self.ui_automaton, content, filetype)

            # apply settings
            if self.extensions:
                settings_loader: UiSettingsProvider = UiSettingsProvider()
                automaton_type: str = self.ui_automaton.get_automaton_type()
                automaton_settings = settings_loader.get_settings(automaton_type)
                if automaton_settings is not None:
                    settings_loader.apply_to_automaton(self.ui_automaton, None, automaton_settings)

                    widget: QAutomatonInputOutput = self.ui_automaton.get_input_widget()()
                    self.window.user_panel.position_input_widget(widget)

                    self.io_manager.debug(f"Applied settings to {automaton_type}-automaton", "")
                else:
                    self.io_manager.error(f"Could not load and apply settings of {automaton_type}", "", True)

            # Custom python
            extension_folder: str = self.extensions_folder
            path: str = f"{extension_folder}{os.path.sep}{self.ui_automaton.get_automaton_type()}.py"
            result: _result.Result = CustomPythonHandler().load(custom_python, path)
            # ErrorCache().debug(f"Custom python loading {"success" if isinstance(result, _result.Success) else "failure"}: {result._inner_value}", "", True, True)
        except Exception as e:
            self.io_manager.warning(
                f"The loading of the file '{os.path.basename(filepath)}' has failed.\nThe file may be corrupted.",
                format_exc(), True, True)
            return False
        return True

    def save_to_file(self, filepath: str, automaton: UiAutomaton) -> str | None:
        """Saves a UIAutomaton to a file.
        Returns the filepath upon successful save or None if an error occurred."""
        # print(automaton)
        end = filepath.rsplit(".", maxsplit=1)[1]
        filetype: _ty.Literal["json", "yaml", "binary"] | None = {"json": "json", "yml": "yaml", "yaml": "yaml",
                                                                  "au": "binary"}.get(end, None)  # type: ignore
        if filetype is None:  # Error case
            IOManager().warning(
                f"The saving to the file '{os.path.basename(filepath)}' has failed.\nIncompatible file extension.", "",
                True, True)
            return None
        try:
            # Custom python:
            extension_folder: str = self.extensions_folder
            path: str = f"{extension_folder}{os.path.sep}{automaton.get_automaton_type()}.py"
            custom_python = CustomPythonHandler().to_custom_python(path)

            content: bytes = serialize(automaton, custom_python, filetype)
            with os_open(filepath, "wb") as f:
                f.write(content)
        except OSError as e:  # File locking problems
            IOManager().warning(
                f"The saving to the file '{os.path.basename(filepath)}' has failed.\nThe file could not be locked.",
                format_exc(), True, True)
        except Exception as e:  # serialization error
            IOManager().warning(
                f"The saving to the file '{os.path.basename(filepath)}' has failed.\nThere was an internal serialization error.",
                format_exc(), True, True)
        else:
            return filepath
        return None

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
        theming_str = 'adalfarus::thin/colored_evening_sky'
        """theming_str: str = self.user_settings.retrieve("design",
                                                       {SystemTheme.LIGHT: "light_theming",
                                                        SystemTheme.DARK: "dark_theming"}[self.os_theme],
                                                       "string")"""
        theme_str, style_str = theming_str.split("/", maxsplit=1)
        theme: Theme | None = Theme.get_loaded_theme(theme_str)

        if theme is None:  # TODO: Popup
            IOManager().warning(f"Specified theme '{theme}' is not available", "", show_dialog=True)
            return
        style: Style | None = theme.get_compatible_style(style_str.replace("_", " ").title())
        if style is None:
            IOManager().warning(f"Couldn't find specified style {style_str} for theme {theme_str}", "",
                                show_dialog=True)
            return
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
            self.io_manager.invoke_popup()
            SignalCache().invoke()

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
        """Cleans up resources"""
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
    print(
        f"Starting {config.PROGRAM_NAME} {str(config.VERSION) + config.VERSION_ADD} with py{'.'.join([str(x) for x in sys.version_info])} ...")
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

        msg_box = QQuickMessageBox(None, QMessageBox.Icon.Warning if custom_icon else None, error_title, error_text,
                                   error_description,
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
        results: str = diagnose_shutdown_blockers(return_result=True)
        # print(results)
        CODES.get(current_exit_code, lambda: sys.exit(current_exit_code))()
