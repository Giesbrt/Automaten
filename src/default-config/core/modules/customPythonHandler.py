from returns import result as _result
from os import path
from aplustools.io.fileio import os_open
# from utils.IOManager import IOManager
from dancer.io import IOManager
from traceback import format_exc

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts


class CustomPythonHandler:

    def __init__(self) -> None:
        super().__init__()
        # use os open (aplustools)

    def load(self, custom_python: str, extensions_path: str) -> _result.Result:
        """ Loads an extension

        :param custom_python: The file content as a string
        :param extensions_path: The path, where the extension should be saved to
        :return: _result.Result
        """
        if not custom_python or not extensions_path:
            return _result.Failure("Attributes can not be None or empty!")

        if path.exists(extensions_path):
            # file exists -> SKIP
            return _result.Failure("The file already exists!")

        try:
            with os_open(extensions_path, "wb") as f:
                f.write(custom_python.encode())
        except Exception as e:
            IOManager().fatal_error("An error occurred whilst trying to load a custom python extension",
                              format_exc(), True)
            return _result.Failure(f"An error occurred whilst trying to load a custom python extension {str(e)}!")
        return _result.Success("File successfully created!")

    def to_custom_python(self, module_path: str) -> str:
        """ Transforms a module (in module_path) into a string

        :param module_path: the path, the module lies in
        :return: the file content as a string
        """
        if not module_path:
            return ""

        try:
            with os_open(module_path, "rb") as f:
                file_content: bytes = f.read()

        except Exception as e:
            IOManager().error("An error occurred whilst trying to load a custom python extension",
                              format_exc(), True)
            return ""

        if not file_content:
            return ""

        return file_content.decode()
