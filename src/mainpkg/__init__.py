"""TBA"""
from importlib.resources import files as _files, as_file as _as_file
from argparse import ArgumentParser as _ArgumentParser
import sys
import os

# This is done because on NixOS installing dancer, ... with numpy, ... is not possible (pip vs flake)
# because of that we install numpy, ... using flake and then install dancer, ... using pip into extra-libs,
# so we need to load it here.
extra_libs = "./default-config/config/extra-libs"
os.makedirs(extra_libs, exist_ok=True)
sys.path.append(extra_libs)  # We append it to make sure the flakes are prioritized

from dancer import config

_pkg_root = _files("mainpkg")

_paths = [
    _pkg_root,
    _pkg_root / "core",
    _pkg_root / "core" / "modules",
    # _pkg_root / "core" / "libs",
]

_absolute_paths = []
for p in _paths:
    with _as_file(p) as actual_path:
        _absolute_paths.append(str(actual_path.resolve()))
_absolute_paths.append(os.path.abspath("./libs"))

app_info = config.AppConfig(
    True, False, True,
    "N.E.F.S.' Simulator",
    "nefs_simulator",
    1400, "b4",
    {"Windows": [config.OSEntry("11", ("24H2",), ("any",))],
     "Linux": [config.OSEntry("6.12.37", (r".*NixOS.*",), ("any",))],
     "Darwin": [config.OSEntry("24.6.0", (r"Darwin Kernel Version 24\.6\.0.*",), ("arm64",))]},
    {"Windows": [config.OSEntry("10", ("any",), ("any",)), config.OSEntry("11", ("any",), ("any",))],
     "Linux": [config.OSEntry(r"6\.\d+\.\d+(-[a-zA-Z0-9])?", ("any",), ("any",))],
     "Darwin": [config.OSEntry(r"24\.\d+\.\d+(-[a-zA-Z0-9])?", ("any",), ("any",))]},
    {},
    [(3, 10), (3, 11), (3, 12), (3, 13)],  #! Add 3.14 if possible
    {
        "config": {
            "libs": {},
            "extra-libs": {},
        },
        "data": {
            "assets": {
                "app_icons": {}
            },
            "styling": {
                "styles": {},
                "themes": {}
            },
            "logs": {}
        }
    },
    _absolute_paths
)
__version__ = f"{app_info.VERSION}{app_info.VERSION_ADD}"

parser = _ArgumentParser(description=f"{app_info.PROGRAM_NAME}")
parser.add_argument("input", nargs="?", default="", help="Path to the input file.")
