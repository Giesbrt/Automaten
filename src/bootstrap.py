import sys
import os

# This is done because on NixOS installing dancer, ... with numpy, ... is not possible (pip vs flake)
# because of that we install numpy, ... using flake and then install dancer, ... using pip into extra-libs,
# so we need to load it here.
extra_libs = "./default-config/core/extra-libs"
os.makedirs(extra_libs, exist_ok=True)
sys.path.append(extra_libs)  # We append it to make sure the flakes are prioritized

from dancer import config, start

app_info = config.AppConfig(
    True, False, True,
    "N.E.F.S.' Simulator",
    "nefs_simulator",
    1400, "b4",
    {"Windows": {"11": ("22H2",)},
     "Linux": {"6.12.37": ("#1-NixOS SMP PREEMPT_DYNAMIC Thu Jul 10 14:05:15 UTC 2025",)}},
    {"Windows": {"10": ("any",), "11": ("any",)},
     "Linux": {r"6\.\d+\.\d+(-[a-zA-Z0-9])?": ("any",)}},
    {},
    [(3, 10), (3, 11), (3, 12), (3, 13)],
    {
        "config": {},
        "core": {
            "libs": {},
            "modules": {}
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
    ["./", "./core", "./core/modules", "./core/libs"]
)
config.do(app_info)
