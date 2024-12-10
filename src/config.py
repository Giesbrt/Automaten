"""TBA"""
import sys as _sys
import os as _os
import shutil as _shutil


INDEV = 1


def is_compiled() -> bool:
    """  # From aps.io.env
    Detects if the code is running in a compiled environment and identifies the compiler used.

    This function checks for the presence of attributes and environment variables specific
    to common Python compilers, including PyInstaller, cx_Freeze, and py2exe.
    :return: bool
    """
    return getattr(_sys, "frozen", False) and (hasattr(_sys, "_MEIPASS") or _sys.executable.endswith(".exe"))


def _configure() -> dict[str, str]:
    if is_compiled():
        _os.chdir(_os.path.join(_os.getcwd(), "_internal"))
    accumulated_logs = "Starting cloning of defaults ...\n"
    old_cwd = _os.getcwd()
    install_dir = _os.path.join(old_cwd, "default-config")
    base_app_dir = _os.path.join(_os.environ.get("LOCALAPPDATA", "."), "dudpy")

    if INDEV and _os.path.exists(base_app_dir):  # Remove everything to simulate a fresh install
        _shutil.rmtree(base_app_dir)
        _os.mkdir(base_app_dir)

    dirs_to_create = []
    dir_structure = (
            ("config", ()),
            ("core", ("libs", "modules")),
            ("data", (("assets", ("icons", "logo_cache")),
                      "logs")),
            ("extensions", ()),
            ("themes", ())
    )  # Use a stack to iteratively traverse the directory structure
    stack: list[tuple[str, tuple[str, ...] | tuple]] = [(base_app_dir, item) for item in dir_structure]
    while stack:
        base_path, (dir_name, subdirs) = stack.pop()
        current_path = _os.path.join(base_path, dir_name)

        if not subdirs:  # No subdirectories; it's a leaf
            dirs_to_create.append(current_path)
        else:
            for subdir in subdirs:  # Add each subdirectory to the stack for further processing
                if isinstance(subdir, tuple):
                    stack.append((current_path, subdir))  # Nested structure
                else:  # Direct leaf under the current directory
                    dirs_to_create.append(_os.path.join(current_path, subdir))
    for dir_to_create in dirs_to_create:
        _os.makedirs(dir_to_create, exist_ok=True)
    _sys.path.insert(0, _os.path.join(base_app_dir, "core", "libs"))
    _sys.path.insert(0, base_app_dir)  # To bug-fix some problem, I think with std libs

    for dirpath, dirnames, filenames in _os.walk(install_dir):
        for filename in filenames:
            file_path = _os.path.join(dirpath, filename)
            stripped_filename = _os.path.relpath(file_path, install_dir)
            alternate_file_location = _os.path.join(base_app_dir, stripped_filename)
            if not _os.path.exists(alternate_file_location) or INDEV:  # Replace all for indev
                accumulated_logs += f"{file_path} -> {alternate_file_location}\n"  # To flush config prints in main
                _os.makedirs(_os.path.dirname(alternate_file_location), exist_ok=True)
                _shutil.copyfile(file_path, alternate_file_location)
            else:
                accumulated_logs += f"{alternate_file_location} Already exists\n"  # To flush config prints in main

    _os.chdir(base_app_dir)
    return {
        "accumulated_logs": accumulated_logs, "old_cwd": old_cwd, "install_dir": install_dir,
        "base_app_dir": base_app_dir,
    }


exported_vars = _configure()
exported_logs, base_app_dir, old_cwd = (exported_vars["accumulated_logs"], exported_vars["base_app_dir"],
                                        exported_vars["old_cwd"])
del _sys, _os, _shutil
