"""Abstract api interfaces for everything"""
import math
import threading

from PySide6.QtWidgets import QWidget, QApplication, QMainWindow
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

# Standard typing imports for aps
import abc as _abc
import collections.abc as _a
import typing as _ty
import types as _ts


class MainWindowInterface:
    """TBA"""
    icons_folder: str = ""
    popups: list[_ty.Any] = []  # Basically anything that isn't the main window, but a window
    app: QApplication | None = None

    class AppStyle:
        """QApp Styles"""
        Windows11 = 'windows11'
        WindowsVista = 'windowsvista'
        Windows = 'Windows'
        Fusion = 'Fusion'
        Default = None

    def __new__(cls, *args, **kwargs):
        raise Exception("This class can't be initialized; it is just an Interface.")

    def setup_gui(self) -> None:
        """
        Configure the main graphical user interface (GUI) elements of the MV application.

        This method sets up various widgets, layouts, and configurations required for the
        main window interface. It is called after initialization and prepares the interface
        for user interaction.

        Note:
            This method is intended to be overridden by subclasses with application-specific
            GUI components.
        """
        raise NotImplementedError

    def set_window_icon(self, absolute_path_to_icon: str) -> None:
        raise NotImplementedError

    def set_window_title(self, title: str) -> None:
        raise NotImplementedError

    def set_window_geometry(self, x: int, y: int, height: int, width: int) -> None:
        raise NotImplementedError

    def set_window_dimensions(self, height: int, width: int) -> None:
        raise NotImplementedError

    def reload_panels(self) -> None:
        raise NotImplementedError

    def create_popup(self, of_what: QWidget, window_flags: Qt.WindowType) -> int:  # Return the popup-index
        raise NotImplementedError

    def destroy_popup(self, index) -> None:  # Remove popup by index
        raise NotImplementedError

    def button_popup(self, title: str, text: str, description: str,
                     icon: _ty.Literal["Information", "Critical", "Question", "Warning", "NoIcon"],
                     buttons: list[str], default_button: str, checkbox: str | None = None) -> tuple[str | None, bool]:
        raise NotImplementedError

    def set_theme_to_singular(self, theme_str: str, widget_or_window: QWidget) -> None:
        """Applies a theme string to a singular object"""
        raise NotImplementedError

    def set_global_theme(self, theme_str: str, base: str | None = None) -> None:
        raise NotImplementedError

    def internal_obj(self) -> QMainWindow:
        raise NotImplementedError

    def start(self) -> None:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError


class BackendInterface:
    """The backend entry point"""

    def __new__(cls, *args, **kwargs):
        raise Exception("This class can't be initialized; it is just an Interface.")

    def run_infinite(self, backend_stop_event: threading.Event) -> None:
        """
        Used to actually start the backend. The gui will launch this in a separate thread.
        """
        ...


class BackendInstructionManager:
    @staticmethod
    def load_file(file_path: str) -> _ty.Dict[str, _ty.Any]:
        pass

    @staticmethod
    def save_file(file_path: str) -> ...:
        pass


class GuiInstructionManager:
    @staticmethod
    def load_automaton():  ## Todo implement
        pass


# Todo add ui automaton interface
#
# def __new__(cls, *args, **kwargs):
#        raise Exception("This class can't be initialized; it is just an Interface.")
#
#


class IUiState(_abc.ABC):

    def __init__(self, colour: str, position: _ty.Tuple[float, float], display_text: str, node_type: str):
        self._colour: str = colour
        self._position: _ty.Tuple[float, float] = position
        self._display_text: str = display_text
        self._type: str = node_type
        self._is_active: bool = False

    @_abc.abstractmethod
    def set_colour(self, colour: str) -> None:
        """Sets the colour of the state."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def set_position(self, position: _ty.Tuple[float, float]) -> None:
        """Sets the position of the state."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def set_display_text(self, display_text: str) -> None:
        """Sets the display text of the state."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def get_colour(self) -> str:
        """Gets the colour of the state."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def get_position(self) -> _ty.Tuple[float, float]:
        """Gets the position of the state."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def get_display_text(self) -> str:
        """Gets the display text of the state."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def get_type(self) -> str:  # TODO: add docu to IUiState
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def is_active(self) -> bool:
        """Checks if the state is active."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def _activate(self) -> None:
        """Activates the state."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def _deactivate(self) -> None:
        """Deactivates the state."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    def __new__(cls, *args, **kwargs):
        raise Exception("This class can't be initialized; it is just an Interface.")


class IUiTransition(_abc.ABC):

    def __init__(self, from_state: IUiState, from_state_connecting_point: _ty.Literal['n', 's', 'e', 'w'],
                 to_state: IUiState, to_state_connecting_point: _ty.Literal['n', 's', 'e', 'w'], condition: _ty.List[str]):
        self._from_state: IUiState = from_state
        self._from_state_connecting_point: _ty.Literal['n', 's', 'e', 'w'] = from_state_connecting_point
        self._to_state: IUiState = to_state
        self._to_state_connecting_point: _ty.Literal['n', 's', 'e', 'w'] = to_state_connecting_point
        self._condition: _ty.List[str] = condition

        self._is_active: bool = False

    @_abc.abstractmethod
    def set_condition(self, condition: _ty.List[str]) -> None:
        self._condition = condition

    @_abc.abstractmethod
    def get_condition(self) -> _ty.List[str]:
        return self._condition

    @_abc.abstractmethod
    def set_from_state(self, from_state: 'IUiState') -> None:
        """Sets the source state of the transition."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def set_from_state_connecting_point(self, connecting_point: _ty.Literal['n', 's', 'e', 'w']) -> None:
        """Sets the connecting point on the source state."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def set_to_state(self, to_state: 'IUiState') -> None:
        """Sets the destination state of the transition."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def set_to_state_connecting_point(self, connecting_point: _ty.Literal['n', 's', 'e', 'w']) -> None:
        """Sets the connecting point on the destination state."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def get_from_state(self) -> 'IUiState':
        """Gets the source state of the transition."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def get_from_state_connecting_point(self) -> _ty.Literal['n', 's', 'e', 'w']:
        """Gets the connecting point on the source state."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def get_to_state(self) -> 'IUiState':
        """Gets the destination state of the transition."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def get_to_state_connecting_point(self) -> _ty.Literal['n', 's', 'e', 'w']:
        """Gets the connecting point on the destination state."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def is_active(self) -> bool:
        """Checks if the transition is active."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def _activate(self) -> None:
        """Activates the transition."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def _deactivate(self) -> None:
        """Deactivates the transition."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    def __new__(cls, *args, **kwargs):
        raise Exception("This class can't be initialized; it is just an Interface.")


class IUiAutomaton(_abc.ABC):

    def __init__(self, automaton_type: str, author: str, state_types_with_design: _ty.Dict[str, _ty.Any], uuid: str = None):
        # state_types_with_design = {"end": {"design": "Linex",  future}, "default": {"design": "Line y", future}}
        self._type: str = automaton_type
        self._uuid: str = uuid

        self._states: _ty.Set[IUiState] = set()
        self._transitions: _ty.Set[IUiTransition] = set()

        self._start_state: IUiState | None = None
        self._input: _ty.List[_ty.Any] = []
        self._pointer_index: int = 0

        self._author: str = author
        self._token_lists: _ty.List[_ty.List[str]] = []
        self._changeable_token_lists: _ty.List[bool] = []
        self._transition_pattern: _ty.List[int] = []

        self._state_types_with_design: _ty.Dict[str, _ty.Any] = state_types_with_design
    
    @_abc.abstractmethod
    def get_uuid(self) -> str:
        raise NotImplementedError("This method must be implemented by subclasses.")
    
    @_abc.abstractmethod
    def set_uuid(self, uuid: str) -> None:
        raise NotImplementedError("This method must be implemented by subclasses.")
    
    @_abc.abstractmethod
    def get_state_types_with_design(self) -> _ty.Dict[str, _ty.Any]:
        raise NotImplementedError("This method must be implemented by subclasses.")
    
    @_abc.abstractmethod
    def set_state_types_with_design(self, state_types_with_design: _ty.Dict[str, _ty.Any]) -> None:
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def get_author(self) -> str:
        """Returns the author of the automaton."""
        raise NotImplementedError("This method must be implemented by subclasses.")
    
    @_abc.abstractmethod
    def get_token_lists(self) -> _ty.List[_ty.List[str]]:
        """Returns the token lists of the automaton."""
        raise NotImplementedError("This method must be implemented by subclasses.")
    
    @_abc.abstractmethod
    def get_changeable_token_lists(self) -> _ty.List[bool]:
        """Returns the changeable token lists of the automaton."""
        raise NotImplementedError("This method must be implemented by subclasses.")
    
    @_abc.abstractmethod
    def get_transition_pattern(self) -> _ty.List[int]:
        """Returns the transition pattern of the automaton."""
        raise NotImplementedError("This method must be implemented by subclasses.")
    
    @_abc.abstractmethod
    def set_token_lists(self, token_lists: _ty.List[_ty.List[str]]) -> None:
        """Sets the token lists of the automaton."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def set_changeable_token_lists(self, changeable_token_lists: _ty.List[bool]) -> None:
        """Sets the changeable token lists of the automaton."""
        raise NotImplementedError("This method must be implemented by subclasses.")
    
    @_abc.abstractmethod
    def set_transition_pattern(self, transition_pattern: _ty.List[int]) -> None:
        """Sets the transition pattern of the automaton."""
        raise NotImplementedError("This method must be implemented by subclasses.")


    @_abc.abstractmethod
    def get_states(self) -> _ty.Set['IUiState']:
        """Returns all states in the automaton."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def get_transitions(self) -> _ty.Set['IUiTransition']:
        """Returns all transitions in the automaton."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def add_state(self, state: 'IUiState') -> None:
        """Adds a state to the automaton."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def add_transition(self, transition: 'IUiTransition') -> None:
        """Adds a transition to the automaton."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def delete_state(self, state: 'IUiState') -> None:
        """Deletes a state from the automaton."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def delete_transition(self, transition: 'IUiTransition') -> None:
        """Deletes a transition from the automaton."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def get_type(self) -> str:
        """Returns the type of the automaton."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def set_start_state(self, state: 'IUiState') -> None:
        """Sets the starting state of the automaton."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def get_state_by_id(self, state_id: int) -> 'IUiState':
        """Fetches a state by its ID."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def get_transition_by_id(self, transition_id: int) -> 'IUiTransition':
        """Fetches a transition by its ID."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def simulate(self, input: _ty.List[_ty.Any]) -> None:
        """Simulates the automaton with a given input."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def handle_simulation_updates(self) -> '_result.Result | None':
        """
        Handles updates from the simulation bridge and returns the result.

        Returns:
            _result.Result: The success or failure of the simulation step.
            None: If no updates are available.
        """
        raise NotImplementedError("This method must be implemented by subclasses.")

    @_abc.abstractmethod
    def handle_bridge_updates(self) -> None:
        """Handles updates from the UI bridge."""
        raise NotImplementedError("This method must be implemented by subclasses.")

    def __new__(cls, *args, **kwargs):
        raise Exception("This class can't be initialized; it is just an Interface.")
