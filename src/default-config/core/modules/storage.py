from aplustools.data.storage import SQLite3Storage as _SQLite3Storage  # User safe
from aplustools.data.storage import SimpleJSONStorage as _SimpleJSONStorage

from threading import RLock as _RLock

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
    def _convert_from_storage(value: str, value_type: _ty.Literal["bool", "float", "tuple", "string"]) -> _ty.Any:
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
        elif value_type == "tuple":
            try:
                return eval(value, {"__builtins__": {}})
            except (SyntaxError, NameError):
                raise ValueError("Stored tuple is malformed")
        elif value_type == "str":
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

    def store(self, table: str, key: str, value: _ty.Any, value_type: _ty.Literal["bool", "float", "tuple", "string"]
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
        value_type_literal = {"bool": bool, "float": float, "tuple": tuple, "string": str}[value_type]
        self._storage.store({key: str(value_type_literal(value))})

    def retrieve(self, table: str, key: str, value_type: _ty.Literal["bool", "float", "tuple", "string"]) -> _ty.Any:
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
