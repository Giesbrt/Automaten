from automaton.base.settings import Settings as BaseSettings
from abstractions import IUiAutomaton
# from utils.IOManager import IOManager
from dancer.io import IOManager
# from aplustools.io import ActLogger
from dancer.io import ActLogger

# Standard typing imports for aps
import typing as _ty


class UiSettingsProvider:
    _loaded_settings: _ty.Dict[str, BaseSettings] = {}

    def __init__(self):
        super().__init__()

    def get_loaded_settings(self) -> _ty.Dict[str, BaseSettings]:
        return self._loaded_settings

    def get_loaded_setting_keys(self) -> _ty.List[str]:
        return list(self._loaded_settings.keys())

    def get_loaded_setting_names(self) -> _ty.List[_ty.Tuple[str, str]]:
        """

        :return: Loaded automaton setting names (idx 0 of tuple: name, idx 1: automaton key)
        """
        loaded_names: _ty.List[_ty.Tuple[str, str]] = []
        for setting_key in self.get_loaded_setting_keys():
            settings: BaseSettings = self.get_settings(setting_key)

            full_automaton_name: str = settings.full_automaton_name.capitalize()

            if " " in full_automaton_name:
                split_automaton_names: _ty.List[str] = full_automaton_name.split(" ")
                full_automaton_name = ""
                for name in split_automaton_names:
                    full_automaton_name += name.capitalize() + " "

            loaded_names.append(
                (f"{full_automaton_name.strip()} ({settings.module_name.upper()})", setting_key))
        return loaded_names

    def get_settings(self, automaton_type: str) -> BaseSettings | None:
        automaton_type: str = automaton_type.lower()
        if automaton_type not in self._loaded_settings:
            IOManager().warn(f"Could not load settings for automaton of type {automaton_type}!",
                              f"Settings for {automaton_type}-automaton could not be cached due to it being not loaded!",
                             True)
            return None

        return self._loaded_settings[automaton_type]

    def add_settings(self, settings: BaseSettings, override: bool = False) -> None:
        if not all(iter(settings)):
            IOManager().error("Could not load settings due to fields being unfilled!",
                               f"Affected Settings: {settings}", True)
            return
        name: str = settings.module_name.lower()
        if name in self._loaded_settings and not override:
            return

        self._loaded_settings[name] = settings
        ActLogger().debug(f"Loaded settings of {name}-automaton")

    def load_from_incoherent_mess(self, mess: dict[str, list[_ty.Type[_ty.Any]]] | None) -> None:
        def filter_settings(settings) -> bool:
            return issubclass(settings, BaseSettings)

        for k in mess:
            data: list[_ty.Type[_ty.Any]] = mess[k]
            filtered_list: list[_ty.Type] = list(filter(filter_settings, data))

            if not filtered_list:
                return

            raw_settings: _ty.Type = filtered_list[0]
            if not issubclass(raw_settings, BaseSettings):
                return

            settings: BaseSettings = raw_settings()

            self.add_settings(settings)

    def remove_settings(self, settings: BaseSettings) -> None:
        name: str = settings.module_name.lower()
        if name not in self._loaded_settings:
            return

        del self._loaded_settings[name]

    def apply_to_automaton(self, ui_automaton: IUiAutomaton, automaton_name: str | None,
                           settings: BaseSettings | None = None):
        if automaton_name is None and settings is None:
            raise AttributeError("'automaton_name' and 'settings' can not be both None")

        if settings is None:
            assert automaton_name is not None and ui_automaton is not None
            settings = self.get_settings(automaton_name)

        # ui_automaton.set_automaton_type(settings.module_name)
        ui_automaton.set_token_lists(settings.token_lists)
        ui_automaton.set_transition_pattern(settings.transition_description_layout)
        ui_automaton.set_is_changeable_token_list(settings.customisable_token_list)
        ui_automaton.set_state_types_with_design(settings.state_types_with_design)
        ui_automaton.set_author(settings.author)
        ui_automaton.set_input_widget(settings.input_widget)


if __name__ == '__main__':
    from extensions.dfa import DFASettings
    from extensions.tm import TmSettings
    from extensions.mealy import MealySettings
    from automaton.UIAutomaton import UiAutomaton

    auto = UiAutomaton(None, None, None)

    prov = UiSettingsProvider()
    prov.add_settings(DFASettings())
    prov.add_settings(TmSettings())
    prov.add_settings(MealySettings())

    print(prov.get_loaded_setting_names())
    print()

    print(auto)
    print()

    prov.apply_to_automaton(auto, automaton_name="dfa")
    print(auto)
