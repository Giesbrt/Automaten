"""TBA"""
# Std Lib imports
import multiprocessing

# Third party imports
import stdlib_list
from dancer import package

hiddenimports = list(stdlib_list.stdlib_list())
multiprocessing.freeze_support()


run_results: str = package("mainpkg")
print(f"[DEBUG] {run_results}")
