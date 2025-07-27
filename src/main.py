"""TBA"""
import bootstrap  # Bootstraps the app

# Debugging
# print("Debugging stuff ...")
# import os
# import subprocess, sys
#
# # 1. Run `pip list --format=freeze` and capture the text
# raw = subprocess.check_output(
#     [sys.executable, "-m", "pip", "list", "--format=freeze"],
#     text=True                      # decode to str instead of bytes
# )
#
# # 2. Extract just the distribution names (part before the first '=')
# packages = [line.split("=", 1)[0].lower() for line in raw.splitlines()]
# # import site
#
# import re
# to_delete: list[str] = []
#
# for pkgs_site in site.getsitepackages():
#     for file in os.listdir(pkgs_site):
#         match = re.fullmatch(r"([^-]+)-(?:\w+\.)+dist-info", file)
#         if match is not None:
#             to_delete.append(match.group(1))
#         elif file.endswith(".dist-info"):
#             print(fr"{file} did not match ([^-]+)-(?:\d\.)+dist-info")
#
# print(to_delete)
#
# print(set(to_delete) - set(packages))
# print(set(packages) - set(to_delete))

# exit(1)

# Std Lib imports
from pathlib import Path as PLPath
from argparse import ArgumentParser, Namespace
from traceback import format_exc
from functools import partial
from string import Template
import multiprocessing
import threading
import logging
import os

# Third party imports
from packaging.version import Version, InvalidVersion
# from returns import result as _result
import stdlib_list
# import requests
# PySide6
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
# dancer
from dancer import Translator  # , Translation
from dancer.qt import DefaultAppGUIQt  # , QtTimidTimer
from dancer.system import os_open, SystemTheme, diagnose_shutdown_blockers
from dancer.timing import FlexTimer

# Internal imports
# from automaton.UIAutomaton import UiAutomaton
# from automaton.automatonProvider import AutomatonProvider
from globals import AppSettings, AppTranslation
# from gui import MainWindow  # TODO: Re-enable
from abstractions import IMainWindow, IBackend
# from automaton import start_backend
# from utils.IOManager import IOManager
from dancer.io import IOManager
# from utils.staticSignal import SignalCache
# from automaton.UiSettingsProvider import UiSettingsProvider
# from automaton.base.QAutomatonInputWidget import QAutomatonInputOutput
# from extensions_loader import Extensions_Loader
from core.backend.loader.loader import Loader
from core.backend.backend import start_backend, BackendType
from core.libs.utils.staticSignal import SignalCache

from core.modules.new_serializer import AutomatonInterface, InvalidParameterError

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

hiddenimports = list(stdlib_list.stdlib_list())
multiprocessing.freeze_support()


class App(DefaultAppGUIQt):
    """The main logic and gui are separated"""
    def __init__(self, parsed_args: Namespace, logging_level: int) -> None:
        self.base_app_dir: str = bootstrap.config.base_app_dir
        self.data_folder: str = os.path.join(self.base_app_dir, "data")  # Like logs, icons, ...
        self.core_folder: str = os.path.join(self.base_app_dir, "core")  # For core functionality like gui
        self.extensions_folder: str = os.path.join(self.base_app_dir, "extensions")  # Extensions
        self.config_folder: str = os.path.join(self.base_app_dir, "config")  # Configurations
        self.styling_folder: str = os.path.join(self.data_folder, "styling")  # App styling

        print("Starting init ...")
        super().__init__(os.path.join(self.styling_folder, "themes"),
                         os.path.join(self.styling_folder, "styles"),
                         os.path.join(self.data_folder, "logs"),
                         parsed_args, logging_level, setup_thread_pool=True)
        print("Starting setup ...")
        try:
            # self.window: IMainWindow = MainWindow()
            self.settings: AppSettings = AppSettings()
            self.settings.init(settings_folder_path=self.config_folder)
            self.translator = Translator(os.path.join(self.data_folder, "localisations"))
            self.translator.set_translation_cls(AppTranslation)

            # Automaton backend init
            self.offload_work("load_extensions", self.set_extensions, lambda: Loader(PLPath(self.base_app_dir)).load())

            if self.settings.get_auto_check_for_updates():
                self.offload_work("check_for_update", self.show_update_result, self.get_update_result)

            # self.extensions: AutomatonProvider = AutomatonProvider()
            self.wait_for_manual_completion("load_extensions", check_interval=0.1)

            # self.ui_automaton: UiAutomaton = UiAutomaton(None, 'TheCodeJak', {})  # Placeholder
            # self.window.set_ui_automaton(self.ui_automaton)
            #
            # # Setup window
            # self.window.manual_update_check.connect(lambda: self.pool.submit(self.check_for_update))

            input_path: str = os.path.abspath(parsed_args.input)
            if (
                    os.path.exists(input_path)
                    and os.path.isfile(input_path)
                    and input_path.endswith((".au", ".json", ".yml", "yaml"))
            ):
                self.io_manager.info(f"Reading {input_path}")
                success: bool = self.load_file(input_path)
                self.window.user_panel.grid_view.load_automaton_from_file()
                self.window.file_path = input_path
                if not success:
                    self.ui_automaton.unload()
                    print('Could not load file')
            else:
                self.io_manager.error(f"The input file ({input_path}) needs to exist")

            # self.window.user_panel.setShowScrollbars(False)
            # self.window.user_panel.setAutoShowInfoMenu(False)
            # self.grid_view = self.window.user_panel.grid_view
            # self.control_menu = self.window.user_panel.control_menu

            self.backend: BackendType = start_backend(self.settings)
            self.backend_stop_event: threading.Event = threading.Event()
            self.backend_thread: threading.Thread = threading.Thread(target=self.backend.run_infinite,
                                                                     args=(self.backend_stop_event,))
            self.backend_thread.start()
            # self.window.set_recently_opened_files(list(self.user_settings.retrieve("auto", "recent_files", "tuple")))

            # self.connect_signals()

            # self.update_icon()
            # self.update_title()
            # self.settings.window_icon_sets_path_changed.connect(lambda _: self.update_icon())
            # self.settings.window_icon_set_changed.connect(lambda _: self.update_icon())
            # self.settings.window_title_template_changed.connect(lambda _: self.update_title())
            # self.settings.automaton_type_changed.connect(lambda _: self.update_title())
            # self.settings.font_changed.connect(lambda _: self.update_font())
            print("Finished setup ...")
        except Exception as e:
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
                timeout=float(self.settings.get_update_check_request_timeout()))
        except requests.exceptions.Timeout:
            title, text, description = "Update Info", ("The request timed out.\n"
                                                       "Please check your internet connection, "
                                                       "and try again."), format_exc()
            standard_buttons, default_button = ["Ok"], "Ok"
            checkbox, checkbox_setting = "Do not show again", ("auto", "show_update_timeout")
            show_update_timeout: bool = self.settings.get_show_update_timeout()
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
        except Exception as e:
            return (self.settings.get_show_update_error(),
                    ("Warning", "Update check failed", "Due to an internal error,\nthe operation could not be completed.", format_exc()),
                    ("Do not show again", ("auto", "show_update_error")),
                    (["Ok"], "Ok"), lambda button: None)

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
                # if found_release and found_version != current_version:
                #     raise NotImplementedError
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

        show_update_info: bool = self.settings.get_show_update_info()
        show_no_update_info: bool = self.settings.get_show_no_update_info()

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
        elif show_no_update_info and found_version <= current_version:
            title = "Update Info"
            text = (f"No new updates available.\nChecklist last updated "
                    f"{update_json['metadata']['lastUpdated'].replace('-', '.')}.")
            description = f" --- v{found_version} --- \n{found_release.get('description')}"  # type: ignore
            checkbox, checkbox_setting = "Do not show again", ("auto", "show_no_update_info")
        elif show_no_update_info and not found_push:
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

    def show_update_result(self, do_popup: bool, box_settings: tuple[str, str, str, str],
                           checkbox_settings: tuple[str | None, tuple[str, str]], buttons: tuple[list[str], str],
                           retval_func: _a.Callable[[str], _ty.Any]) -> None:
        """
        Shows update result using a message box
        """
        (icon, title, text, description) = box_settings
        (checkbox, checkbox_setting) = checkbox_settings
        (standard_buttons, default_button) = buttons
        if do_popup:
            retval, checkbox_checked = self.window.button_popup(title, text, description, icon, standard_buttons,
                                                                default_button, checkbox)
            retval_func(retval)
            if checkbox is not None and checkbox_checked:
                getattr(self.settings, f"set_{checkbox_setting[1]}")(False)

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
        self.control_menu.play_button.clicked.connect(lambda: self.start_simulation())
        self.control_menu.stop_button.clicked.connect(self.stop_simulation)
        self.control_menu.next_button.clicked.connect(lambda: self.start_simulation_step_for_step(None))

        # self.control_menu.token_update_signal.connect(self.grid_view.update_token_lists)

        self.window.save_file_signal.connect(partial(self.save_to_file, automaton=self.ui_automaton))
        self.window.open_file_signal.connect(self.open_file)

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

    def build_simulation_output(self, simulation_output: _ty.Dict) -> _ty.List[str]:
        """Builds the simulation output from the simulation result"""
        output = simulation_output["input"]
        if not simulation_output["output"]:
            return output
        else:
            if max(0, simulation_output["pointer_index"] -1) < len(output):
                output[max(0, simulation_output["pointer_index"] -1)] = simulation_output["output"]
            else:
                output.append(simulation_output["output"])
        return output

    def start_simulation(self, automaton_input: _ty.List[str] = None) -> None:
        # print(f"Input: {self.window.user_panel.input_widget.getFormattedInput()}")
        print(automaton_input, "inp", bool(automaton_input))
        if automaton_input is None:
            automaton_input = self.window.user_panel.input_widget.getFormattedInput()
            self.io_manager.debug("Input: " + str(automaton_input))

        if not automaton_input or not all(automaton_input):
            self.io_manager.error('No input provided!', '', True, True)
            return

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
        self.window.user_panel.input_widget.reset()
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
            simulation_result_raw: _ty.Dict = self.ui_automaton.handle_simulation_updates()
            simulation_result: _ty.Dict = simulation_result_raw._inner_value

            # display the simulation output in the input widget
            print(simulation_result, "SIM")

            if not isinstance(simulation_result, dict):
                self.io_manager.info(f"Simulation Message: {simulation_result}", "", True, True)
                return
            if isinstance(simulation_result_raw, _result.Success) and simulation_result is not None:
                output = self.build_simulation_output(simulation_result)
                self.window.user_panel.input_widget.simulationStep(output,
                                                                   simulation_result["pointer_index"])
            else:
                self.window.user_panel.input_widget.reset()
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

    def start_simulation_step_for_step(self, automaton_input: _ty.List[str] | None) -> None:
        if automaton_input is None:
            automaton_input = self.window.user_panel.input_widget.getFormattedInput()
            self.io_manager.debug("Input: " + str(automaton_input))

        if not automaton_input or not all(automaton_input):
            self.io_manager.error('No input provided!', '', True, True)
            return

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
            simulation_result_raw: _ty.Dict = self.ui_automaton.handle_simulation_updates()
            simulation_result: _ty.Dict = simulation_result_raw._inner_value

            # display the simulation output in the input widget

            if not isinstance(simulation_result, dict):
                self.io_manager.info(f"Simulation Message: {simulation_result}", "", True, True)
                return

            if isinstance(simulation_result_raw, _result.Success) and simulation_result is not None:
                output = self.build_simulation_output(simulation_result)
                self.window.user_panel.input_widget.simulationStep(output, simulation_result["pointer_index"])
            else:
                self.window.user_panel.input_widget.reset()

            active_state: 'UiState' = self.ui_automaton.get_active_state()
            active_transition: 'UiTransition' = self.ui_automaton.get_active_transition()
            state_item = self.grid_view.get_active_state(active_state)

            self.grid_view.highlight_state_item(state_item)
            if active_transition:
                transition_item = self.grid_view.get_active_transition(active_transition)
                self.grid_view.highlight_transition_item(transition_item)
        else:
            self.stop_simulation()

    def set_extensions(self, extensions: list[dict[str, _ts.ModuleType | str]]) -> None:
        # self.extensions.clear()
        # self.extensions.register_automatons(extensions, append=True)

        # if len(self.extensions) == 0:
        #     self.io_manager.fatal_error('No extensions loaded!', '', True, True)
        self.automaton: AutomatonInterface = AutomatonInterface(extensions, self.extensions_folder)

    def open_file(self, filepath: str) -> None:
        """Opens a file and notifies the GUI to update"""
        success: bool = self.load_file(filepath)
        if not success:
            return
        else:
            self.window.file_path = filepath
            self.grid_view.load_automaton_from_file()

    def load_file(self, filepath: str) -> bool:
        """Loads a UIAutomaton from a serialized file.
        Returns an UIAutomaton upon successful load or None if an error occurred."""
        recent_files = [filepath]
        for file in self.settings.get_recent_files():
            if PLPath(file) != PLPath(filepath):
                recent_files.append(file)
        self.settings.set_recent_files(tuple(recent_files))
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

            self.settings.set_automaton_type(self.ui_automaton.get_automaton_type())

            # Custom python
            extension_folder: str = self.extensions_folder
            path: str = f"{extension_folder}{os.path.sep}{self.ui_automaton.get_automaton_type()}.py"
            result: _result.Result = CustomPythonHandler().load(custom_python, path)
            if isinstance(result, _result.Success) and False:
                self.io_manager.info("Custom python loaded successfully, you may want to restart the Application", "", True, False)
                return True

            if self.window.user_panel.input_widget:
                self.window.user_panel.input_widget.reset()
                self.window.user_panel.deposition_input_widget()

            widget: QAutomatonInputOutput = self.ui_automaton.get_input_widget()
            self.window.user_panel.position_input_widget(widget)
            self.window.user_panel.refresh_tokens_input_widget(self.ui_automaton.get_token_lists()[0])
            self.window.user_panel.control_menu.update_token_lists(self.ui_automaton.get_token_lists())

            # ErrorCache().debug(f"Custom python loading {"success" if isinstance(result, _result.Success) else "failure"}: {result._inner_value}", "", True, True)
        except Exception as e:
            self.io_manager.warning(
                f"The loading of the file '{os.path.basename(filepath)}' has failed.\nThe file may be corrupted.",
                format_exc(), True, True)
            self.ui_automaton.unload()
            self.window.user_panel.grid_view.empty_scene()
            self.window.show_automaton_selection()
            return False
        return True

    def save_to_file(self, filepath: str, automaton: _ty.Any) -> str | None:
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
        window_icon_sets_path: str = self.settings.get_window_icon_sets_path()
        window_icon_set: str = self.settings.get_window_icon_set()
        if window_icon_sets_path.startswith(":"):
            window_icon_sets_path = window_icon_sets_path.replace(":", self.base_app_dir, 1)
        self.window.set_window_icon(os.path.join(window_icon_sets_path, window_icon_set, "logo-nobg.png"))

    def update_title(self) -> None:
        """Updates the window title with data from the settings"""
        raw_title: Template = Template(self.settings.get_window_title_template())
        formatted_title: str = raw_title.safe_substitute(program_name=bootstrap.config.PROGRAM_NAME,
                                                         version=bootstrap.config.VERSION,
                                                         version_add=bootstrap.config.VERSION_ADD,
                                                         automaton_type=str(self.ui_automaton.get_automaton_type()).upper()
                                                         )
        self.window.set_window_title(formatted_title)

    def update_font(self) -> None:
        """Updates the window font with data from the settings. This is an expensive operation."""
        self.window.set_font(self.settings.get_font())

    # def check_theme_change(self):
    #     if self.timer_number & 1 == 1:
    #         current_os_theme = self.get_os_theme()
    #         if current_os_theme != self.os_theme or self.settings.get_theming(current_os_theme) != self.current_theming:
    #             self.os_theme = current_os_theme
    #             self.apply_theme()

    def exec(self) -> int:  # Overwrite GUI exec, so we can focus on the backend
        # Start simulation
        import sys, logging, platform
        from ast import literal_eval

        self.io_manager.info("Disabling logger and entering into tty mode ...")
        self.io_manager.set_logging_level(logging.CRITICAL)
        sys.stdout = self.io_manager._logger.restore_pipe(sys.stdout)  # type: ignore
        sys.stderr = self.io_manager._logger.restore_pipe(sys.stderr)  # type: ignore

        try:
            while True:
                print("\nPlease choose an action:")
                print("create {type} - Create new automaton of type {type}\n"
                      "load {filepath} - Load file from {filepath}\n"
                      "list - List automaton types\n"
                      "quit - Exit the application")

                inp = input("> ")

                if inp.startswith("create"):
                    try:
                        automaton_type: str = inp.split(" ", maxsplit=1)[1]
                        self.automaton.create(automaton_type)
                    except IndexError:
                        input("You did not provide enough arguments")
                        continue
                    except (InvalidParameterError, NotImplementedError) as e:
                        input(e.args[0])
                        continue
                elif inp.startswith("load"):
                    # try:
                        file_path: str = inp.split(" ", maxsplit=1)[1]
                        self.automaton.load(file_path)
                    # except IndexError:
                    #     input("You did not provide enough arguments")
                    #     continue
                    # except (InvalidParameterError, NotImplementedError) as e:
                    #     input(e.args[0])
                    #     continue
                elif inp.startswith("list"):
                    if inp != "list":
                        input(f"The list option does not have any parameters")
                    for automaton in self.automaton.get_loaded_automaton_types():
                        input(automaton)
                    continue
                elif inp.startswith("quit"):
                    if inp != "quit":
                        input(f"The quit option does not have any parameters")
                    raise KeyboardInterrupt()
                else:
                    input(f"{inp} is not a valid command")
                    continue

                while True:
                    print("\nPlease choose an edit action:")
                    print("add {name, default ascending} - Create new state with name {name}\n"
                          "startstate {name} - Set the state with name {name} as the start state\n"
                          "change {name} {type} - Change the type of state with name {name} to type {type}\n"
                          "list - List all state types\n"
                          "conn {q1} {q2} {params} - Connect state {q1} to state {q2} with params {params}\n"
                          "unconn {q1} {q2} - Remove connection between state {q1} to state {q2}\n"
                          "remv {name} - Remove the state with the name {name}\n\n"
                          "start {input} - Start the automaton with input {input}\n"
                          "startstep {input} - Start automaton in step mode, giving you back control after every simulation step\n\n"
                          "close - Close the automaton without saving\n"
                          "save {filepath} - Save the automaton to {filepath}")

                    inner_inp = input("> ")

                    if inner_inp.startswith("add"):
                        try:
                            state_name: str | None = None
                            args = inner_inp.split(" ", maxsplit=1)[1:]
                            if args:
                                state_name = args[0]
                            self.automaton.add_state(state_name)
                        except (InvalidParameterError, NotImplementedError) as e:
                            input(e.args[0])
                            continue
                    elif inner_inp.startswith("startstate"):
                        try:
                            state_name: str = inner_inp.split(" ", maxsplit=2)[1]
                            self.automaton.set_start_state(state_name)
                        except IndexError:
                            input("You did not provide enough arguments")
                            continue
                        except (InvalidParameterError, NotImplementedError) as e:
                            input(e.args[0])
                            continue
                    elif inner_inp.startswith("change"):
                        state_name: str
                        state_type: str
                        try:
                            state_name, state_type = inner_inp.split(" ", maxsplit=2)[1:]
                            self.automaton.change_state_type(state_name, state_type)
                        except ValueError:
                            input("You did not provide enough arguments")
                            continue
                        except (InvalidParameterError, NotImplementedError) as e:
                            input(e.args[0])
                            continue
                    elif inner_inp.startswith("list"):
                        if inner_inp != "list":
                            input(f"The list option does not have any parameters")
                        for state_type in self.automaton.get_loaded_automatons_state_types():
                            input(state_type)
                        continue
                    elif inner_inp.startswith("conn"):
                        q1: str
                        q2: str
                        raw_params: str
                        params: tuple[str, ...]
                        try:
                            args = inner_inp.split(" ", maxsplit=3)[1:]
                            if len(args) == 3:
                                q1, q2, raw_params = args
                            else:
                                input("You did not provide enough arguments")
                                continue
                            params = literal_eval(raw_params)
                            while True:
                                for param, token_lst_idx in zip(params, self.automaton._settings.transition_description_layout):
                                    token_lst: list[str] = self.automaton._data.token_lsts[token_lst_idx]
                                    if param not in token_lst:
                                        bool_inp = input(f"The token '{param}' is not in {token_lst}, do you want to add it? [Y/n]")
                                        if bool_inp.lower() != "n":
                                            self.automaton.add_token(token_lst_idx, param)
                                break
                            self.automaton.connect_states(q1, q2, params)
                        except ValueError:
                            input("You did not pass valid strings as tokens in the tuple")
                            continue
                        except SyntaxError:
                            input("You did not pass a valid tuple as the last argument")
                            continue
                        except (InvalidParameterError, NotImplementedError) as e:
                            input(e.args[0])
                            continue
                    elif inner_inp.startswith("unconn"):
                        q1: str
                        q2: str
                        try:
                            q1, q2 = inner_inp.split(" ", maxsplit=2)[1:]
                            self.automaton.unconnect_states(q1, q2)
                        except ValueError:
                            input("You did not provide enough arguments")
                            continue
                        except (InvalidParameterError, NotImplementedError) as e:
                            input(e.args[0])
                            continue
                    elif inner_inp.startswith("remv"):
                        try:
                            state_name: str = inner_inp.split(" ", maxsplit=1)[1]
                            self.automaton.remove_state(state_name)
                        except IndexError:
                            input("You did not provide enough arguments")
                            continue
                        except (InvalidParameterError, NotImplementedError) as e:
                            input(e.args[0])
                            continue
                    elif inner_inp.startswith("start"):
                        try:
                            automaton_input: str = inner_inp.split(" ", maxsplit=1)[1]
                            # TODO: We do not currently care about token longer than 1
                            input_tokens: list[str] = list(automaton_input)
                            input("Not implemented yet")
                            continue
                            with self.automaton.session() as s:
                                s.start()
                            stopevent = self.automaton.start_automaton(input_tokens)
                            while not stopevent.is_set():
                                print("Tick")  # TODO: What about about results? About length?
                                self.timer_tick(0)
                            input("Finished simulation")
                        except IndexError:
                            input("You did not provide enough arguments")
                            continue
                        except (InvalidParameterError, NotImplementedError) as e:
                            input(e.args[0])
                            continue
                    elif inner_inp.startswith("startstep"):
                        try:
                            automaton_input: str = inner_inp.split(" ", maxsplit=1)[1]
                        except IndexError:
                            input("You did not provide enough arguments")
                            continue
                        input("This option is currently not available")
                        continue
                    elif inner_inp.startswith("close"):
                        if inner_inp != "close":
                            input(f"The close option does not have any parameters")
                        self.automaton.close()
                        break
                    elif inner_inp.startswith("save"):
                        try:
                            file_path: str = inner_inp.split(" ", maxsplit=1)[1]
                            self.automaton.save(file_path)
                        except IndexError:
                            input("You did not provide enough arguments")
                            continue
                        except (InvalidParameterError, NotImplementedError) as e:
                            input(e.args[0])
                            continue
                    else:
                        input(f"{inner_inp} is not a valid command")
                        continue

                if platform.system() == "Windows":
                    os.system("cls")
                else:
                    os.system("clear")
        # except Exception as e:  # We have a dedicated crash() for this
        #     print(e)
        #     return -1
        except KeyboardInterrupt:
            print("Exiting ...")
        return 0

    def crash(self, error_title: str, error_text: str, error_description: str) -> bool:
        print(error_description)
        return super().crash(error_title, error_text, error_description)

    def timer_tick(self, index: int) -> None:
        # super().timer_tick(index)
        if index == 0:  # Default 500ms timer
            # self.check_theme_change()
            # self.timer_number += 1
            # if self.timer_number > 999:
            #     self.timer_number = 1

            # display cached Errors
            # self.io_manager.invoke_popup()
            if SignalCache().has_elements() is None:
                return
            SignalCache().invoke()

            # num_handled: int = 0
            # while len(self.for_loop_list) > 0 and num_handled < self.settings.get_max_timer_tick_handled_events():
            #     entry = self.for_loop_list.pop()
            #     func, args = entry
            #     func(*args)
            #     num_handled += 1

    def close(self) -> None:
        """Cleans up resources"""
        super().close()
        if hasattr(self, "backend_thread") and self.backend_thread.is_alive():  # TODO: Is it alive after error?
            self.backend_stop_event.set()
            self.backend_thread.join()


if __name__ == "__main__":
    parser = ArgumentParser(description=f"{bootstrap.config.PROGRAM_NAME}")
    parser.add_argument("input", nargs="?", default="", help="Path to the input file.")

    bootstrap.start(App, parser)

    results: str = diagnose_shutdown_blockers(return_result=True)
