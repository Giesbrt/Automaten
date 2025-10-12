"""TBA"""
# Std Lib imports
import multiprocessing

import sys
import os

# This is done because on NixOS installing dancer, ... with numpy, ... is not possible (pip vs flake)
# because of that we install numpy, ... using flake and then install dancer, ... using pip into extra-libs,
# so we need to load it here.
extra_libs = "./default-config/config/extra-libs"
os.makedirs(extra_libs, exist_ok=True)
sys.path.append(extra_libs)  # We append it to make sure the flakes are prioritized

# Third party imports
import stdlib_list
from dancer import package

hiddenimports = list(stdlib_list.stdlib_list())
multiprocessing.freeze_support()


run_results: str = package("mainpkg")
print(f"[DEBUG] {run_results}")
