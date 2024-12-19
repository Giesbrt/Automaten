"""TBA"""
from core.modules.storage import JSONAppStorage, MultiUserDBStorage


# Whatever


class _Backend:
    def run_infinite(self) -> None:
        """
        Used to actually start the backend. The gui will launch this in a seperate thread.
        Note that JSONAppStorage is NOT thread-safe at the moment.
        """
        ...


def start(simple_storage: JSONAppStorage, extended_storage: MultiUserDBStorage) -> _Backend:
    inst = _Backend()  # You can save as file attr, or do other config stuff.
    return inst
