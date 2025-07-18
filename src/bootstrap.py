from dancer import config, start

app_info = config.AppInfo(
    True, False,
    "N.E.F.S.' Simulator",
    "nefs_simulator",
    1400, "b4",
    {"Windows": {"10": ("any",), "11": ("any",)}},
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
    ["./core/common", "./core/modules", "./core/libs", "./core/plugins", "./"]
)
config.do(app_info)
