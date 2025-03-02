from threading import RLock as _RLock

from abstractions import IAppSettings

from PySide6.QtCore import Signal, QObject

from aplustools.data.storage import SQLite3Storage as _SQLite3Storage  # User safe
from aplustools.data.storage import SimpleJSONStorage as _SimpleJSONStorage
from aplustools.io.env import SystemTheme

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts


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
        self._storage: _SQLite3Storage = _SQLite3Storage(db_path, tables, drop_unused_tables=True)
        self._tables: tuple[str, ...] = tables
        self._table: str = tables[0]
        self._default_settings: dict[str, dict[str, str]] = {}

    @staticmethod
    def _convert_from_storage(value: str, value_type: _ty.Literal["bool", "float", "tuple", "string", "integer"]) -> _ty.Any:
        """
        Convert a stored string back to its original type based on the specified type.

        Args:
            value (str): The stored value as a string.
            value_type (Literal["bool", "float", "tuple", "string"]): The type to convert the value to.

        Returns:
            Any: The converted value in its original type.

        Raises:
            ValueError: If the value cannot be converted or if an unsupported type is specified.
        """
        if value_type == "bool":
            return value == "True"
        elif value_type == "float":
            return float(value)
        elif value_type == "integer":
            return int(value)
        elif value_type == "tuple":
            try:
                return eval(value, {"__builtins__": {}})
            except (SyntaxError, NameError):
                raise ValueError("Stored tuple is malformed")
        elif value_type == "string":
            return value
        else:
            raise ValueError("Unsupported data type for retrieval")

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

    def store(self, table: str, key: str, value: _ty.Any, value_type: _ty.Literal["bool", "float", "tuple", "string", "integer"]
              ) -> None:
        """
        Store a single item in the database with explicit type specification and conversion.

        Args:
            table (str): The name of the table to store the value in.
            key (str): The key under which the value will be stored.
            value (Any): The value to store.
            value_type (Literal["bool", "float", "tuple", "string"]): The type of the value.

        Raises:
            ValueError: If the key does not have a default setting.
        """
        if not self._check_if_defaulted(table, key):
            raise ValueError(f"{table}.{key} does not have a default!")
        self._storage.switch_table(table)  # Is not expensive
        value_type_literal = {"bool": bool, "float": float, "tuple": tuple, "string": str, "integer": int}[value_type]
        self._storage.store({key: str(value_type_literal(value))})

    def retrieve(self, table: str, key: str, value_type: _ty.Literal["bool", "float", "tuple", "string", "integer"]) -> _ty.Any:
        """
        Retrieve a single item from the database with explicit type specification and conversion.

        Args:
            table (str): The name of the table to retrieve the value from.
            key (str): The key under which the value is stored.
            value_type (Literal["bool", "float", "tuple", "string"]): The type of the value.

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
        return self._convert_from_storage(value, value_type)

    def set_default_settings(self, table: str, default_settings: dict[str, str]) -> None:
        """
        Set default settings for a table if they do not already exist.

        Args:
            table (str): The name of the table to set default settings for.
            default_settings (dict[str, str]): A dictionary of default settings for the table.

        Stores any settings in the table that do not already exist.
        """
        self._storage.switch_table(table)
        existing_keys: list[str | None] = self._storage.retrieve(list(default_settings.keys()))
        to_store = {k: v for i, (k, v) in enumerate(default_settings.items())
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
        self._storage: _SimpleJSONStorage = _SimpleJSONStorage(path, beautify=True)
        self._default_settings: dict[str, str] = {}
        self._lock: _RLock = _RLock()
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


class AppSettings(QObject):
    """TBA"""
    _instance: _ty.Self | None = None
    _settings: MultiUserDBStorage
    _initialized: bool = False
    setup: bool = False

    # general
    app_language_changed = Signal(str)
    auto_open_tutorial_tab_changed = Signal(bool)
    auto_check_for_updates_changed = Signal(bool)
    # auto
    geometry_changed = Signal(tuple[int, int, int, int])
    show_no_update_info_changed = Signal(bool)
    show_update_info_changed = Signal(bool)
    show_update_timeout_changed = Signal(bool)
    ask_to_reopen_last_file_changed = Signal(bool)
    recent_files_changed = Signal(tuple[str, ...])
    # shortcuts
    file_open_shortcut_changed = Signal(str)
    file_save_shortcut_changed = Signal(str)
    file_close_shortcut_changed = Signal(str)
    simulation_start_shortcut_changed = Signal(str)
    simulation_step_shortcut_changed = Signal(str)
    simulation_halt_shortcut_changed = Signal(str)
    simulation_end_shortcut_changed = Signal(str)
    states_cut_shortcut_changed = Signal(str)
    states_copy_shortcut_changed = Signal(str)
    states_paste_shortcut_changed = Signal(str)
    # design
    light_theming_changed = Signal(str)
    dark_theming_changed = Signal(str)
    window_icon_sets_path_changed = Signal(str)
    window_icon_set_changed = Signal(str)
    font_changed = Signal(str)
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
    save_window_dimensions_changed = Signal(bool)
    save_window_position_changed = Signal(bool)
    update_check_request_timeout_changed = Signal(float)
    max_timer_tick_handled_events_changed = Signal(int)
    logging_mode_changed = Signal(str)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppSettings, cls).__new__(cls)
            # cls._instance._initialized = False  # Track initialization state
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:  # Prevent reinitialization
            return
        super().__init__()
        self._initialized = True

    def init(self, config, settings_folder_path: str) -> None:
        """Initializes the AppSettings"""
        if self.setup:  # Prevent reinitialization
            return
        self._settings: MultiUserDBStorage = MultiUserDBStorage(f"{settings_folder_path}/user_settings.db",
                                                                    ("general", "auto", "design", "security", "performance", "advanced", "shortcuts"))
        # self.app_settings: JSONAppStorage = JSONAppStorage(f"{config.old_cwd}/locations.json")
        # print(self.app_settings._storage._filepath)
        self._configure_settings(config)
        self.setup = True

    def _configure_settings(self, config) -> None:
        self._settings.set_default_settings("general", {
            "app_language": "enUS",
            "auto_open_tutorial_tab": "True",
            "auto_check_for_updates": "True"
        })
        self._settings.set_default_settings("auto", {
            "geometry": "(100, 100, 1050, 640)",
            "show_no_update_info": "False",
            "show_update_info": "True",
            "show_update_timeout": "True",
            "ask_to_reopen_last_file": "True",
            "recent_files": "()"
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
            "window_title_template": f"{config.PROGRAM_NAME} $version$version_add $title" + (
                " [INDEV]" if config.INDEV else ""),
            "enable_animations": "True",
            "default_state_background_color": "#FFFFFFFF",
            "hide_scrollbars": "True"
        })
        self._settings.set_default_settings("performance", {
            "option": "True"
        })
        self._settings.set_default_settings("security", {
            "warn_of_new_plugins": "True",
            "run_plugin_in_separate_process": "False",
            "use_safe_file_access": "True"
        })
        self._settings.set_default_settings("advanced", {
            "hide_titlebar": "False",
            "stay_on_top": "False",
            "save_window_dimensions": "True",
            "save_window_position": "False",
            "update_check_request_timeout": "2.0",
            "max_timer_tick_handled_events": "5",
            "logging_mode": "DEBUG" if config.INDEV else "INFO",
        })

    # general
    def get_app_language(self) -> str:
        return self._settings.retrieve("general", "app_language", "string")
    def set_app_language(self, app_language: str) -> None:
        self.app_language_changed.emit(app_language)
        self._settings.store("general", "app_language", app_language, "string")
    def get_auto_open_tutorial_tab(self) -> bool:
        return self._settings.retrieve("general", "auto_open_tutorial_tab", "bool")
    def set_auto_open_tutorial_tab(self, flag: bool) -> None:
        self.auto_open_tutorial_tab_changed.emit(flag)
        self._settings.store("general", "auto_open_tutorial_tab", flag, "bool")
    def get_auto_check_for_updates(self) -> bool:
        return self._settings.retrieve("general", "auto_check_for_updates", "bool")
    def set_auto_check_for_updates(self, flag: bool) -> None:
        self.auto_check_for_updates_changed.emit(flag)
        self._settings.store("general", "auto_check_for_updates", flag, "bool")
    # auto
    def get_window_geometry(self) -> tuple[int, int, int, int]:
        return self._settings.retrieve("auto", "geometry", "tuple")  # type: ignore
    def set_window_geometry(self, window_geometry: tuple[int, int, int, int]) -> None:
        self.geometry_changed.emit(window_geometry)
        self._settings.store("auto", "geometry", window_geometry, "tuple")
    def get_show_no_update_info(self) -> bool:
        return self._settings.retrieve("auto", "show_no_update_info", "bool")  # type: ignore
    def set_show_no_update_info(self, flag: bool) -> None:
        self.show_no_update_info_changed.emit(flag)
        self._settings.store("auto", "show_no_update_info", flag, "bool")
    def get_show_update_info(self) -> bool:
        return self._settings.retrieve("auto", "show_update_info", "bool")  # type: ignore
    def set_show_update_info(self, flag: bool) -> None:
        self.show_update_info_changed.emit(flag)
        self._settings.store("auto", "show_update_info", flag, "bool")
    def get_show_update_timeout(self) -> bool:
        return self._settings.retrieve("auto", "show_update_timeout", "bool")  # type: ignore
    def set_show_update_timeout(self, flag: bool) -> None:
        self.show_update_timeout_changed.emit(flag)
        self._settings.store("auto", "show_update_timeout", flag, "bool")
    def get_ask_to_reopen_last_file(self) -> bool:
        return self._settings.retrieve("auto", "ask_to_reopen_last_file", "bool")  # type: ignore
    def set_ask_to_reopen_last_file(self, flag: bool) -> None:
        self.ask_to_reopen_last_file_changed.emit(flag)
        self._settings.store("auto", "ask_to_reopen_last_file", flag, "bool")
    def get_recent_files(self) -> tuple[str, ...]:
        return self._settings.retrieve("auto", "recent_files", "tuple")  # type: ignore
    def set_recent_files(self, recent_files: tuple[str, ...]) -> None:
        self.recent_files_changed.emit(recent_files)
        self._settings.store("auto", "recent_files", recent_files, "tuple")
    # shortcuts
    def get_file_open_shortcut(self) -> str:
        return self._settings.retrieve("shortcuts", "file_open", "string")
    def set_file_open_shortcut(self, shortcut_str: str) -> None:
        self.file_open_shortcut_changed.emit(shortcut_str)
        self._settings.store("shortcuts", "file_open", shortcut_str, "string")
    def get_file_save_shortcut(self) -> str:
        return self._settings.retrieve("shortcuts", "file_save", "string")
    def set_file_save_shortcut(self, shortcut_str: str) -> None:
        self.file_save_shortcut_changed.emit(shortcut_str)
        self._settings.store("shortcuts", "file_save", shortcut_str, "string")
    def get_file_close_shortcut(self) -> str:
        return self._settings.retrieve("shortcuts", "file_close", "string")
    def set_file_close_shortcut(self, shortcut_str: str) -> None:
        self.file_close_shortcut_changed.emit(shortcut_str)
        self._settings.store("shortcuts", "file_close", shortcut_str, "string")
    def get_simulation_start_shortcut(self) -> str:
        return self._settings.retrieve("shortcuts", "simulation_start", "string")
    def set_simulation_start_shortcut(self, shortcut_str: str) -> None:
        self.simulation_start_shortcut_changed.emit(shortcut_str)
        self._settings.store("shortcuts", "simulation_start", shortcut_str, "string")
    def get_simulation_step_shortcut(self) -> str:
        return self._settings.retrieve("shortcuts", "simulation_step", "string")
    def set_simulation_step_shortcut(self, shortcut_str: str) -> None:
        self.simulation_step_shortcut_changed.emit(shortcut_str)
        self._settings.store("shortcuts", "simulation_step", shortcut_str, "string")
    def get_simulation_halt_shortcut(self) -> str:
        return self._settings.retrieve("shortcuts", "simulation_halt", "string")
    def set_simulation_halt_shortcut(self, shortcut_str: str) -> None:
        self.simulation_halt_shortcut_changed.emit(shortcut_str)
        self._settings.store("shortcuts", "simulation_halt", shortcut_str, "string")
    def get_simulation_end_shortcut(self) -> str:
        return self._settings.retrieve("shortcuts", "simulation_end", "string")
    def set_simulation_end_shortcut(self, shortcut_str: str) -> None:
        self.simulation_end_shortcut_changed.emit(shortcut_str)
        self._settings.store("shortcuts", "simulation_end", shortcut_str, "string")
    def get_states_cut_shortcut(self) -> str:
        return self._settings.retrieve("shortcuts", "states_cut", "string")
    def set_states_cut_shortcut(self, shortcut_str: str) -> None:
        self.states_cut_shortcut_changed.emit(shortcut_str)
        self._settings.store("shortcuts", "states_cut", shortcut_str, "string")
    def get_states_copy_shortcut(self) -> str:
        return self._settings.retrieve("shortcuts", "states_copy", "string")
    def set_states_copy_shortcut(self, shortcut_str: str) -> None:
        self.states_copy_shortcut_changed.emit(shortcut_str)
        self._settings.store("shortcuts", "states_copy", shortcut_str, "string")
    def get_states_paste_shortcut(self) -> str:
        return self._settings.retrieve("shortcuts", "states_paste", "string")
    def set_states_paste_shortcut(self, shortcut_str: str) -> None:
        self.states_paste_shortcut_changed.emit(shortcut_str)
        self._settings.store("shortcuts", "states_paste", shortcut_str, "string")
    # design
    def get_theming(self, mode: SystemTheme) -> str:
        theming_type: str = {SystemTheme.LIGHT: "light_theming",
                             SystemTheme.DARK: "dark_theming"}[mode]
        return self._settings.retrieve("design", theming_type, "string")
    def set_theming(self, mode: SystemTheme, theming: str) -> None:
        theming_type: str = {SystemTheme.LIGHT: "light_theming",
                             SystemTheme.DARK: "dark_theming"}[mode]
        getattr(self, f"{theming_type}_changed").emit(theming)
        self._settings.store("design", theming_type, theming, "string")
    def get_window_icon_sets_path(self) -> str:
        return self._settings.retrieve("design", "window_icon_sets_path", "string")
    def set_window_icon_sets_path(self, icon_sets_path: str) -> None:
        self.window_icon_sets_path_changed.emit(icon_sets_path)
        self._settings.store("design", "window_icon_sets_path", icon_sets_path, "string")
    def get_window_icon_set(self) -> str:
        return self._settings.retrieve("design", "window_icon_set", "string")
    def set_window_icon_set(self, icon_set: str) -> None:
        self.window_icon_set_changed.emit(icon_set)
        self._settings.store("design", "window_icon_set", icon_set, "string")
    def get_font(self) -> str:
        return self._settings.retrieve("design", "font", "string")
    def set_font(self, font: str) -> None:
        self.font_changed.emit(font)
        self._settings.store("design", "font", font, "string")
    def get_window_title_template(self) -> str:
        return self._settings.retrieve("design", "window_title_template", "string")
    def set_window_title_template(self, title_template: str) -> None:
        self.window_title_template_changed.emit(title_template)
        self._settings.store("design", "window_title_template", title_template, "string")
    def get_enable_animations(self) -> bool:
        return self._settings.retrieve("design", "enable_animations", "bool")  # type: ignore
    def set_enable_animations(self, flag: bool) -> None:
        self.enable_animations_changed.emit(flag)
        self._settings.store("design", "enable_animations", flag, "bool")
    def get_default_state_background_color(self) -> str:
        return self._settings.retrieve("design", "default_state_background_color", "string")
    def set_default_state_background_color(self, default_state_background_color: str) -> None:
        self.default_state_background_color_changed.emit(default_state_background_color)
        self._settings.store("design", "default_state_background_color", default_state_background_color, "string")
    def get_hide_scrollbars(self) -> bool:
        return self._settings.retrieve("design", "hide_scrollbars", "bool")  # type: ignore
    def set_hide_scrollbars(self, flag: bool) -> None:
        self.hide_scrollbars_changed.emit(flag)
        self._settings.store("design", "hide_scrollbars", flag, "bool")
    # performance
    def get_option(self) -> bool:
        return self._settings.retrieve("performance", "option", "bool")  # type: ignore
    def set_option(self, flag: bool) -> None:
        self.option_changed.emit(flag)
        self._settings.store("performance", "option", flag, "bool")
    # security
    def get_warn_of_new_plugins(self) -> bool:
        return self._settings.retrieve("security", "warn_of_new_plugins", "bool")  # type: ignore
    def set_warn_of_new_plugins(self, flag: bool) -> None:
        self.warn_of_new_plugins_changed.emit(flag)
        self._settings.store("security", "warn_of_new_plugins", flag, "bool")
    def get_run_plugin_in_separate_process(self) -> bool:
        return self._settings.retrieve("security", "run_plugin_in_separate_process", "bool")  # type: ignore
    def set_run_plugin_in_separate_process(self, flag: bool) -> None:
        self.run_plugin_in_separate_process_changed.emit(flag)
        self._settings.store("security", "run_plugin_in_separate_process", flag, "bool")
    def get_use_safe_file_access(self) -> bool:
        return self._settings.retrieve("security", "use_safe_file_access", "bool")  # type: ignore
    def set_use_safe_file_access(self, flag: bool) -> None:
        self.use_safe_file_access_changed.emit(flag)
        self._settings.store("security", "use_safe_file_access", flag, "bool")
    # advanced
    def get_hide_titlebar(self) -> bool:
        return self._settings.retrieve("advanced", "hide_titlebar", "bool")  # type: ignore
    def set_hide_titlebar(self, flag: bool) -> None:
        self.hide_titlebar_changed.emit(flag)
        self._settings.store("advanced", "hide_titlebar", flag, "bool")
    def get_stay_on_top(self) -> bool:
        return self._settings.retrieve("advanced", "stay_on_top", "bool")  # type: ignore
    def set_stay_on_top(self, flag: bool) -> None:
        self.stay_on_top_changed.emit(flag)
        self._settings.store("advanced", "stay_on_top", flag, "bool")
    def get_save_window_dimensions(self) -> bool:
        return self._settings.retrieve("advanced", "save_window_dimensions", "bool")  # type: ignore
    def set_save_window_dimensions(self, flag: bool) -> None:
        self.save_window_dimensions_changed.emit(flag)
        self._settings.store("advanced", "save_window_dimensions", flag, "bool")
    def get_save_window_position(self) -> bool:
        return self._settings.retrieve("advanced", "save_window_position", "bool")  # type: ignore
    def set_save_window_position(self, flag: bool) -> None:
        self.save_window_position_changed.emit(flag)
        self._settings.store("advanced", "save_window_position", flag, "bool")
    def get_update_check_request_timeout(self) -> float:
        return self._settings.retrieve("advanced", "update_check_request_timeout", "float")
    def set_update_check_request_timeout(self, request_timeout: float) -> None:
        self.update_check_request_timeout_changed.emit(request_timeout)
        self._settings.store("advanced", "update_check_request_timeout", request_timeout, "float")
    def get_max_timer_tick_handled_events(self) -> int:
        return self._settings.retrieve("advanced", "max_timer_tick_handled_events", "float")
    def set_max_timer_tick_handled_events(self, max_handled_events: int) -> None:
        self.max_timer_tick_handled_events_changed.emit(max_handled_events)
        self._settings.store("advanced", "max_timer_tick_handled_events", max_handled_events, "integer")
    def get_logging_mode(self) -> str:
        return self._settings.retrieve("advanced", "logging_mode", "string")
    def set_logging_mode(self, logging_mode: str) -> None:
        self.logging_mode_changed.emit(logging_mode)
        self._settings.store("advanced", "logging_mode", logging_mode, "string")
