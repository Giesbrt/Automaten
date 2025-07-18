from threading import RLock
from ast import literal_eval

from PySide6.QtCore import Signal

from dancer.data import SQLite3Storage, JSONStorage
from dancer.system import SystemTheme
from dancer.qt import QtAppSettings
from dancer import config, Translation

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

__all__ = ["AppSettings", "AppTranslation"]


class MultiUserDBStorage:
    """
    A class for managing multi-user storage in a SQLite3 database. It provides methods
    for storing, retrieving, and managing settings across multiple tables.

    Attributes:
        _storage (SQLite3Storage): The internal SQLite storage handler.
        _tables (tuple[str, ...]): The names of tables in the database.
        _table (str): The primary table name for default operations.
        _default_settings (dict[str, dict[str, str]]): Default settings for each table.
    """
    def __init__(self, db_path: str, tables: tuple[str, ...] = ("storage",)) -> None:
        self._storage: SQLite3Storage = SQLite3Storage(db_path, tables, drop_unused_tables=True)
        self._tables: tuple[str, ...] = tables
        self._table: str = tables[0]
        self._default_settings: dict[str, dict[str, str]] = {}

    def _check_if_defaulted(self, table: str, key: str) -> bool:
        """
        Check if a key has a default value set in the specified table.

        Args:
            table (str): The table name.
            key (str): The key to check.

        Returns:
            bool: True if a default value exists, False otherwise.
        """
        return key in self._default_settings[table]

    def store(self, table: str, key: str, value: _ty.Any) -> None:
        """
        Store a single item in the database with explicit type specification and conversion.

        Args:
            table (str): The name of the table to store the value in.
            key (str): The key under which the value will be stored.
            value (Any): The value to store.

        Raises:
            ValueError: If the key does not have a default setting.
        """
        if not self._check_if_defaulted(table, key):
            raise ValueError(f"{table}.{key} does not have a default!")
        self._storage.switch_table(table)  # Is not expensive
        self._storage.store({key: repr(value)})

    def retrieve(self, table: str, key: str) -> _ty.Any:
        """
        Retrieve a single item from the database with explicit type specification and conversion.

        Args:
            table (str): The name of the table to retrieve the value from.
            key (str): The key under which the value is stored.

        Returns:
            Any: The retrieved value converted to the specified type.

        Raises:
            ValueError: If the key does not have a default setting or if the stored value
                cannot be converted to the specified type.
        """
        if not self._check_if_defaulted(table, key):
            raise ValueError(f"{table}.{key} does not have a default!")
        self._storage.switch_table(table)
        value = self._storage.retrieve([key])[0]
        if value is None:
            raise RuntimeError(f"The key {table}.{key} does not exist in the database!")
        return literal_eval(value)

    def set_default_settings(self, table: str, default_settings: dict[str, _ty.Any]) -> None:
        """
        Set default settings for a table if they do not already exist.

        Args:
            table (str): The name of the table to set default settings for.
            default_settings (dict[str, str]): A dictionary of default settings for the table.

        Stores any settings in the table that do not already exist.
        """
        self._storage.switch_table(table)
        existing_keys: list[str | None] = self._storage.retrieve(list(default_settings.keys()))
        to_store = {k: repr(v) for i, (k, v) in enumerate(default_settings.items())
                    if existing_keys[i] is None}
        if to_store:
            self._storage.store(to_store)
        self._default_settings[table] = default_settings

    def acquire(self, timeout: float = -1) -> None:
        """
        Sets the lock for multiple operations.

        :param timeout: Timeout before returning if lock cannot get acquired.
        """
        self._storage.acquire(timeout)

    def release(self) -> None:
        """
        Releases the lock acquired with acquire(timeout=...)
        :return:
        """
        self._storage.release()


class JSONAppStorage:
    """
    A class for managing JSON-based storage for a single-user application. It provides methods
    for storing, retrieving, and managing default settings in a JSON file.

    Attributes:
        _storage (SimpleJSONStorage): The internal JSON storage handler.
        _default_settings (dict[str, str]): Default settings for the storage.
    """
    def __init__(self, path: str, default_settings: dict[str, str] | None = None) -> None:
        self._storage: JSONStorage = JSONStorage(path, beautify=True)
        self._default_settings: dict[str, str] = {}
        self._lock: RLock = RLock()
        if default_settings is not None:
            self.set_default_settings(default_settings)

    def _check_if_defaulted(self, key: str) -> bool:
        """
        Check if a key has a default value set.

        Args:
            key (str): The key to check.

        Returns:
            bool: True if a default value exists, False otherwise.
        """
        return key in self._default_settings

    def retrieve(self, key: str, convert_to: _ty.Type | None = None) -> _ty.Any:
        """
        Retrieve a single item from the JSON storage with optional type conversion.

        Args:
            key (str): The key under which the value is stored.
            convert_to (Type, optional): The type to convert the retrieved value to.
                Defaults to None.

        Returns:
            Any: The retrieved value, optionally converted to the specified type.

        Raises:
            ValueError: If the key does not have a default setting.
        """
        with self._lock:
            if not self._check_if_defaulted(key):
                raise ValueError(f"{key} does not have a default!")
            setting = self._storage.retrieve([key])[0]
            if convert_to:
                return convert_to(setting)
            return setting

    def set_default_settings(self, default_settings: dict[str, str]) -> None:
        """
        Set default settings if they do not already exist in the storage.

        Args:
            default_settings (dict[str, str]): A dictionary of default settings for the storage.

        Stores any settings in the storage that do not already exist.
        """
        with self._lock:
            self._default_settings = default_settings
            existing_keys: list[str | None] = self._storage.retrieve(list(default_settings.keys()))
            to_store = {k: v for i, (k, v) in enumerate(default_settings.items())
                        if existing_keys[i] is None}
            if to_store:
                self._storage.store(to_store)

    def acquire(self, timeout: float = -1) -> None:
        """
        Sets the lock for multiple operations.

        :param timeout: Timeout before returning if lock cannot get acquired.
        """
        self._lock.acquire(timeout=timeout)

    def release(self) -> None:
        """
        Releases the lock acquired with acquire(timeout=...)
        :return:
        """
        self._lock.release()


class AppSettings(QtAppSettings):
    """TBA"""
    _settings: MultiUserDBStorage
    # _automaton_type: str | None = None

    # general
    auto_open_tutorial_tab_changed = Signal(bool)
    auto_hide_input_widget_changed = Signal(bool)
    auto_check_for_updates_changed = Signal(bool)
    # automatic
    geometry_changed = Signal(tuple)  # tuple[int, int, int, int]
    show_no_update_info_changed = Signal(bool)
    show_update_info_changed = Signal(bool)
    show_update_timeout_changed = Signal(bool)
    show_update_error_changed = Signal(bool)
    ask_to_reopen_last_file_changed = Signal(bool)
    recent_files_changed = Signal(tuple)  # tuple[str, ...]
    # shortcuts
    file_new_shortcut_changed = Signal(str)
    file_open_shortcut_changed = Signal(str)
    file_save_shortcut_changed = Signal(str)
    file_save_as_shortcut_changed = Signal(str)
    file_close_shortcut_changed = Signal(str)
    simulation_start_shortcut_changed = Signal(str)
    simulation_step_shortcut_changed = Signal(str)
    simulation_halt_shortcut_changed = Signal(str)
    simulation_end_shortcut_changed = Signal(str)
    states_cut_shortcut_changed = Signal(str)
    states_copy_shortcut_changed = Signal(str)
    states_paste_shortcut_changed = Signal(str)
    states_delete_shortcut_changed = Signal(str)
    zoom_in_shortcut_changed = Signal(str)
    zoom_out_shortcut_changed = Signal(str)
    zoom_reset_shortcut_changed = Signal(str)
    # design
    window_icon_sets_path_changed = Signal(str)
    window_icon_set_changed = Signal(str)
    window_title_template_changed = Signal(str)
    enable_animations_changed = Signal(str)
    default_state_background_color_changed = Signal(str)
    hide_scrollbars_changed = Signal(str)
    # performance
    option_changed = Signal(bool)
    # security
    warn_of_new_plugins_changed = Signal(bool)
    run_plugin_in_separate_process_changed = Signal(bool)
    use_safe_file_access_changed = Signal(bool)
    # advanced
    hide_titlebar_changed = Signal(bool)
    stay_on_top_changed = Signal(bool)
    update_check_request_timeout_changed = Signal(float)
    max_timer_tick_handled_events_changed = Signal(int)

    # custom
    automaton_type_changed = Signal(str)

    def _initialize(self, *args, **kwargs) -> None:
        """Initializes the AppSettings"""
        settings_folder_path: str | None = kwargs.get("settings_folder_path")
        if settings_folder_path is None:
            raise ValueError("You need to pass settings folder path as a keyword argument when initializing the Settings")
        self._settings: MultiUserDBStorage = MultiUserDBStorage(f"{settings_folder_path}/user_settings.db",
                                                                    ("general", "automatic", "design", "security", "performance", "advanced", "shortcuts"))

    def _set_default_settings(self) -> None:
        self._settings.set_default_settings("general", {
            "app_language": "enUS",
            "auto_open_tutorial_tab": True,
            "auto_hide_input_widget": False,
            "auto_check_for_updates": True
        })
        self._settings.set_default_settings("automatic", {
            "window_geometry": (100, 100, 1050, 640),
            "show_no_update_info": False,
            "show_update_info": True,
            "show_update_timeout": True,
            "show_update_error": True,
            "ask_to_reopen_last_file": True,
            "recent_files": ()
        })
        self._settings.set_default_settings("shortcuts", {
            "file_new": "",  # "" means disabled
            "file_open": "Ctrl+O",
            "file_save": "Ctrl+S",
            "file_save_as": "",
            "file_close": "Ctrl+Q",
            "simulation_start": "Ctrl+G",
            "simulation_step": "Ctrl+T",
            "simulation_halt": "Ctrl+H",
            "simulation_end": "Ctrl+Y",
            "states_cut": "Ctrl+X",
            "states_copy": "Ctrl+C",
            "states_paste": "Ctrl+V",
            "states_delete": "Del",
            "zoom_in": "Ctrl++",
            "zoom_out": "Ctrl+-",
            "zoom_reset": "Ctrl+0",
        })
        self._settings.set_default_settings("design", {
            "light_theming": "adalfarus::thin/thin_light_green",  # thin_light_dark, colored_summer_sky
            # "dark_theming": "adalfarus::high_contrast/base",
            # "dark_theming": "adalfarus::thin/high_contrast",
            "dark_theming": "adalfarus::thin/colored_evening_sky",
            # "dark_theming": "adalfarus::thick/thick_light",
            # "dark_theming": "adalfarus::chisled/base",
            # "dark_theming": "adalfarus::modern/base",
            # "dark_theming": "adalfarus::default/base",
            "window_icon_sets_path": ":/data/assets/app_icons",
            "window_icon_set": "shelline",
            "font": "Segoe UI",
            "window_title_template": f"$program_name $version$version_add [$automaton_type]" + (
                " [INDEV]" if config.INDEV else ""),
            "enable_animations": True,
            "default_state_background_color": "#FFFFFFFF",
            "hide_scrollbars": True
        })
        self._settings.set_default_settings("performance", {
            "option": True
        })
        self._settings.set_default_settings("security", {
            "warn_of_new_plugins": True,
            "run_plugin_in_separate_process": False,
            "use_safe_file_access": True
        })
        self._settings.set_default_settings("advanced", {
            "hide_titlebar": False,
            "stay_on_top": False,
            "save_window_dimensions": True,
            "save_window_position": False,
            "update_check_request_timeout": 2.0,
            "max_timer_tick_handled_events": 5,
            "logging_mode": "DEBUG" if config.INDEV else "INFO",
        })

    def _retrieve(self, category: str, name: str) -> _ty.Any:
        return self._settings.retrieve(category, name)
    def _store(self, category: str, name: str, value: _ty.Any) -> None:
        self._settings.store(category, name, value)

    # general
    def get_auto_open_tutorial_tab(self) -> bool:
        return self._retrieve("general", "auto_open_tutorial_tab")
    def set_auto_open_tutorial_tab(self, flag: bool) -> None:
        self._store("general", "auto_open_tutorial_tab", flag)
        self.auto_open_tutorial_tab_changed.emit(flag)
    def get_auto_hide_input_widget(self) -> bool:
        return self._retrieve("general", "auto_hide_input_widget")
    def set_auto_hide_input_widget(self, flag: bool) -> None:
        self._store("general", "auto_hide_input_widget", flag)
        self.auto_hide_input_widget_changed.emit(flag)
    def get_auto_check_for_updates(self) -> bool:
        return self._retrieve("general", "auto_check_for_updates")
    def set_auto_check_for_updates(self, flag: bool) -> None:
        self._store("general", "auto_check_for_updates", flag)
        self.auto_check_for_updates_changed.emit(flag)
    # automatic
    def get_show_no_update_info(self) -> bool:
        return self._retrieve("automatic", "show_no_update_info")
    def set_show_no_update_info(self, flag: bool) -> None:
        self._store("automatic", "show_no_update_info", flag)
        self.show_no_update_info_changed.emit(flag)
    def get_show_update_info(self) -> bool:
        return self._retrieve("automatic", "show_update_info")
    def set_show_update_info(self, flag: bool) -> None:
        self._store("automatic", "show_update_info", flag)
        self.show_update_info_changed.emit(flag)
    def get_show_update_timeout(self) -> bool:
        return self._retrieve("automatic", "show_update_timeout")
    def set_show_update_timeout(self, flag: bool) -> None:
        self._store("automatic", "show_update_timeout", flag)
        self.show_update_timeout_changed.emit(flag)
    def get_show_update_error(self) -> bool:
        return self._retrieve("automatic", "show_update_error")
    def set_show_update_error(self, flag: bool) -> None:
        self._store("automatic", "show_update_error", flag)
        self.show_update_error_changed.emit(flag)
    def get_ask_to_reopen_last_file(self) -> bool:
        return self._retrieve("automatic", "ask_to_reopen_last_file")
    def set_ask_to_reopen_last_file(self, flag: bool) -> None:
        self._store("automatic", "ask_to_reopen_last_file", flag)
        self.ask_to_reopen_last_file_changed.emit(flag)
    def get_recent_files(self) -> tuple[str, ...]:
        return self._retrieve("automatic", "recent_files")
    def set_recent_files(self, recent_files: tuple[str, ...]) -> None:
        self._store("automatic", "recent_files", recent_files)
        self.recent_files_changed.emit(recent_files)
    # shortcuts
    def get_file_new_shortcut(self) -> str:
        return self._retrieve("shortcuts", "file_new")
    def set_file_new_shortcut(self, shortcut_str: str) -> None:
        self._store("shortcuts", "file_new", shortcut_str)
        self.file_new_shortcut_changed.emit(shortcut_str)
    def get_file_open_shortcut(self) -> str:
        return self._retrieve("shortcuts", "file_open")
    def set_file_open_shortcut(self, shortcut_str: str) -> None:
        self._store("shortcuts", "file_open", shortcut_str)
        self.file_open_shortcut_changed.emit(shortcut_str)
    def get_file_save_shortcut(self) -> str:
        return self._retrieve("shortcuts", "file_save")
    def set_file_save_shortcut(self, shortcut_str: str) -> None:
        self._store("shortcuts", "file_save", shortcut_str)
        self.file_save_shortcut_changed.emit(shortcut_str)
    def get_file_save_as_shortcut(self) -> str:
        return self._retrieve("shortcuts", "file_save_as")
    def set_file_save_as_shortcut(self, shortcut_str: str) -> None:
        self._store("shortcuts", "file_save_as", shortcut_str)
        self.file_save_as_shortcut_changed.emit(shortcut_str)
    def get_file_close_shortcut(self) -> str:
        return self._retrieve("shortcuts", "file_close")
    def set_file_close_shortcut(self, shortcut_str: str) -> None:
        self._store("shortcuts", "file_close", shortcut_str)
        self.file_close_shortcut_changed.emit(shortcut_str)
    def get_simulation_start_shortcut(self) -> str:
        return self._retrieve("shortcuts", "simulation_start")
    def set_simulation_start_shortcut(self, shortcut_str: str) -> None:
        self._store("shortcuts", "simulation_start", shortcut_str)
        self.simulation_start_shortcut_changed.emit(shortcut_str)
    def get_simulation_step_shortcut(self) -> str:
        return self._retrieve("shortcuts", "simulation_step")
    def set_simulation_step_shortcut(self, shortcut_str: str) -> None:
        self._store("shortcuts", "simulation_step", shortcut_str)
        self.simulation_step_shortcut_changed.emit(shortcut_str)
    def get_simulation_halt_shortcut(self) -> str:
        return self._retrieve("shortcuts", "simulation_halt")
    def set_simulation_halt_shortcut(self, shortcut_str: str) -> None:
        self._store("shortcuts", "simulation_halt", shortcut_str)
        self.simulation_halt_shortcut_changed.emit(shortcut_str)
    def get_simulation_end_shortcut(self) -> str:
        return self._retrieve("shortcuts", "simulation_end")
    def set_simulation_end_shortcut(self, shortcut_str: str) -> None:
        self._store("shortcuts", "simulation_end", shortcut_str)
        self.simulation_end_shortcut_changed.emit(shortcut_str)
    def get_states_cut_shortcut(self) -> str:
        return self._retrieve("shortcuts", "states_cut")
    def set_states_cut_shortcut(self, shortcut_str: str) -> None:
        self._store("shortcuts", "states_cut", shortcut_str)
        self.states_cut_shortcut_changed.emit(shortcut_str)
    def get_states_copy_shortcut(self) -> str:
        return self._retrieve("shortcuts", "states_copy")
    def set_states_copy_shortcut(self, shortcut_str: str) -> None:
        self._store("shortcuts", "states_copy", shortcut_str)
        self.states_copy_shortcut_changed.emit(shortcut_str)
    def get_states_paste_shortcut(self) -> str:
        return self._retrieve("shortcuts", "states_paste")
    def set_states_paste_shortcut(self, shortcut_str: str) -> None:
        self._store("shortcuts", "states_paste", shortcut_str)
        self.states_paste_shortcut_changed.emit(shortcut_str)
    def get_states_delete_shortcut(self) -> str:
        return self._retrieve("shortcuts", "states_delete")
    def set_states_delete_shortcut(self, shortcut_str: str) -> None:
        self._store("shortcuts", "states_delete", shortcut_str)
        self.states_delete_shortcut_changed.emit(shortcut_str)
    def get_zoom_in_shortcut(self) -> str:
        return self._retrieve("shortcuts", "zoom_in")
    def set_zoom_in_shortcut(self, shortcut_str: str) -> None:
        self._store("shortcuts", "zoom_in", shortcut_str)
        self.zoom_in_shortcut_changed.emit(shortcut_str)
    def get_zoom_out_shortcut(self) -> str:
        return self._retrieve("shortcuts", "zoom_out")
    def set_zoom_out_shortcut(self, shortcut_str: str) -> None:
        self._store("shortcuts", "zoom_out", shortcut_str)
        self.zoom_out_shortcut_changed.emit(shortcut_str)
    def get_zoom_reset_shortcut(self) -> str:
        return self._retrieve("shortcuts", "zoom_reset")
    def set_zoom_reset_shortcut(self, shortcut_str: str) -> None:
        self._store("shortcuts", "zoom_reset", shortcut_str)
        self.zoom_reset_shortcut_changed.emit(shortcut_str)
    # design
    def get_window_icon_sets_path(self) -> str:
        return self._retrieve("design", "window_icon_sets_path")
    def set_window_icon_sets_path(self, icon_sets_path: str) -> None:
        self._store("design", "window_icon_sets_path", icon_sets_path)
        self.window_icon_sets_path_changed.emit(icon_sets_path)
    def get_window_icon_set(self) -> str:
        return self._retrieve("design", "window_icon_set")
    def set_window_icon_set(self, icon_set: str) -> None:
        self._store("design", "window_icon_set", icon_set)
        self.window_icon_set_changed.emit(icon_set)
    def get_window_title_template(self) -> str:
        return self._retrieve("design", "window_title_template")
    def set_window_title_template(self, title_template: str) -> None:
        self._store("design", "window_title_template", title_template)
        self.window_title_template_changed.emit(title_template)
    def get_enable_animations(self) -> bool:
        return self._retrieve("design", "enable_animations")
    def set_enable_animations(self, flag: bool) -> None:
        self._store("design", "enable_animations", flag)
        self.enable_animations_changed.emit(flag)
    def get_default_state_background_color(self) -> str:
        return self._retrieve("design", "default_state_background_color")
    def set_default_state_background_color(self, default_state_background_color: str) -> None:
        self._store("design", "default_state_background_color", default_state_background_color)
        self.default_state_background_color_changed.emit(default_state_background_color)
    def get_hide_scrollbars(self) -> bool:
        return self._retrieve("design", "hide_scrollbars")
    def set_hide_scrollbars(self, flag: bool) -> None:
        self._store("design", "hide_scrollbars", flag)
        self.hide_scrollbars_changed.emit(flag)
    # performance
    def get_option(self) -> bool:
        return self._retrieve("performance", "option")
    def set_option(self, flag: bool) -> None:
        self._store("performance", "option", flag)
        self.option_changed.emit(flag)
    # security
    def get_warn_of_new_plugins(self) -> bool:
        return self._retrieve("security", "warn_of_new_plugins")
    def set_warn_of_new_plugins(self, flag: bool) -> None:
        self._store("security", "warn_of_new_plugins", flag)
        self.warn_of_new_plugins_changed.emit(flag)
    def get_run_plugin_in_separate_process(self) -> bool:
        return self._retrieve("security", "run_plugin_in_separate_process")
    def set_run_plugin_in_separate_process(self, flag: bool) -> None:
        self._store("security", "run_plugin_in_separate_process", flag)
        self.run_plugin_in_separate_process_changed.emit(flag)
    def get_use_safe_file_access(self) -> bool:
        return self._retrieve("security", "use_safe_file_access")
    def set_use_safe_file_access(self, flag: bool) -> None:
        self._store("security", "use_safe_file_access", flag)
        self.use_safe_file_access_changed.emit(flag)
    # advanced
    def get_hide_titlebar(self) -> bool:
        return self._retrieve("advanced", "hide_titlebar")
    def set_hide_titlebar(self, flag: bool) -> None:
        self._store("advanced", "hide_titlebar", flag)
        self.hide_titlebar_changed.emit(flag)
    def get_stay_on_top(self) -> bool:
        return self._retrieve("advanced", "stay_on_top")
    def set_stay_on_top(self, flag: bool) -> None:
        self._store("advanced", "stay_on_top", flag)
        self.stay_on_top_changed.emit(flag)
    def get_update_check_request_timeout(self) -> float:
        return self._retrieve("advanced", "update_check_request_timeout")
    def set_update_check_request_timeout(self, request_timeout: float) -> None:
        self._store("advanced", "update_check_request_timeout", request_timeout)
        self.update_check_request_timeout_changed.emit(request_timeout)
    def get_max_timer_tick_handled_events(self) -> int:
        return self._retrieve("advanced", "max_timer_tick_handled_events")
    def set_max_timer_tick_handled_events(self, max_handled_events: int) -> None:
        self._store("advanced", "max_timer_tick_handled_events", max_handled_events)
        self.max_timer_tick_handled_events_changed.emit(max_handled_events)

    # def get_automaton_type(self) -> str:
    #     return self._automaton_type
    #
    # def set_automaton_type(self, automaton_type: str) -> None:
    #     self._automaton_type = automaton_type
    #     self.automaton_type_changed.emit(automaton_type)


class AppTranslation(Translation):
    ...
