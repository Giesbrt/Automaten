"""TBA"""
from core.modules.storage import JSONAppStorage, MultiUserDBStorage

# Whatever

simple_storage: JSONAppStorage or None = None
extended_storage: MultiUserDBStorage or None = None


class _Backend:
    def run_infinite(self) -> None:
        """
        Used to actually start the backend. The gui will launch this in a seperate thread.
        """
        ...


def start(simple_stor: JSONAppStorage, extended_stor: MultiUserDBStorage) -> _Backend:
    global simple_storage
    global extended_storage

    inst = _Backend()  # You can save as file attr, or do other config stuff.
    simple_storage = simple_stor
    extended_storage = extended_stor
    return inst
