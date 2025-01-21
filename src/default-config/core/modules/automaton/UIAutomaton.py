"""TBA"""
from PySide6.QtGui import Qt

from returns import result as _result

# Bridge Import
from core.modules.automaton.UiBridge import UiBridge

# abstract imports
from core.modules.abstract import IUiState
from core.modules.abstract import IUiTransition
from core.modules.abstract import IUiAutomaton

from aplustools.io.env import auto_repr_with_privates
from aplustools.io import ActLogger
from core.utils.OrderedSet import OrderedSet

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts


# Docs generated with Github Copilot


class CardinalDirection:
    """Enum for cardinal directions"""
    North = "n"
    East = "e"
    South = "s"
    West = "w"


@auto_repr_with_privates
class UiState(IUiState):  # TODO: mypy does not like that IUiState is of type Any
    """A class representing a state in the automaton."""

    def __init__(self, colour: Qt.GlobalColor, position: _ty.Tuple[float, float], display_text: str,
                 node_type: str) -> None:
        super().__init__(colour, position, display_text, node_type)
        self._colour: Qt.GlobalColor = colour
        self._position: _ty.Tuple[float, float] = position
        self._display_text: str = display_text
        self._type: str = node_type
        self._is_active: bool = False

    def set_colour(self, colour: Qt.GlobalColor) -> None:
        """Sets the colour of the state.

        :param colour: The colour of the state.
        :return: None
        """
        self._colour = colour

    def set_position(self, position: _ty.Tuple[float, float]) -> None:
        """Sets the position of the state.
        
        :param position: The position of the state.
        :return: None
        """
        self._position = position

    def set_display_text(self, display_text: str) -> None:
        """Sets the display text of the state.
        
        :param display_text: The display text of the state.
        :return: None
        """
        self._display_text = display_text

    def get_colour(self) -> Qt.GlobalColor:
        """Gets the colour of the state.
        
        :return: The colour of the state.
        """
        return self._colour

    def get_position(self) -> _ty.Tuple[float, float]:
        """Gets the position of the state.
        
        :return: The position of the state."""
        return self._position

    def get_display_text(self) -> str:
        """Gets the display text of the state.
        
        :return: The display text of the state."""
        return self._display_text

    def get_type(self) -> str:  # TODO: add docu to IUiState
        """Gets the node type of the state.
        
        :return: The type of the state."""
        return self._type

    def is_active(self) -> bool:
        """Checks if the state is active.
        
        :return: True if the state is active, False otherwise."""
        return self._is_active

    def _activate(self) -> None:
        """Activates the state."""
        self._is_active = True

    def _deactivate(self) -> None:
        """Deactivates the state."""
        self._is_active = False

    def __eq__(self, other: _ty.Self):
        return (self._colour == other.get_colour()
                and self._position == other.get_position()
                and self._display_text == other.get_display_text()
                and self._type == other.get_type()
                and self._is_active == other.is_active())

    def __hash__(self):
        return hash(repr(self))


@auto_repr_with_privates
class UiTransition(IUiTransition):
    def __init__(self, from_state: UiState, from_state_connecting_point: _ty.Literal['n', 's', 'e', 'w'],
                 to_state: UiState, to_state_connecting_point: _ty.Literal['n', 's', 'e', 'w']
                 , condition: _ty.List[str]):
        super().__init__(from_state, from_state_connecting_point, to_state, to_state_connecting_point, condition)
        self._from_state: UiState = from_state
        self._from_state_connecting_point: _ty.Literal['n', 's', 'e', 'w'] = from_state_connecting_point
        self._to_state: UiState = to_state
        self._to_state_connecting_point: _ty.Literal['n', 's', 'e', 'w'] = to_state_connecting_point

        self._is_active: bool = False

    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)

    def set_from_state(self, from_state: UiState) -> None:
        """Sets the state from which the transition originates.
        
        :param from_state: The state from which the transition originates.
        :return: None
        """
        self._from_state = from_state

    def set_from_state_connecting_point(self, connecting_point: _ty.Literal['n', 's', 'e', 'w']) -> None:
        """Sets the connecting point of the from state.
        
        :param connecting_point: The connecting point of the from state.
        :return: None
        """
        self._from_state_connecting_point = connecting_point

    def set_to_state(self, to_state: UiState) -> None:
        """Sets the state to which the transition leads.
        
        :param to_state: The state to which the transition leads.
        :return: None
        """
        self._to_state = to_state

    def set_to_state_connecting_point(self, connecting_point: _ty.Literal['n', 's', 'e', 'w']) -> None:
        """Sets the connecting point of the to state.
        
        :param connecting_point: The connecting point of the to state.
        :return: None
        """
        self._to_state_connecting_point = connecting_point

    def get_from_state(self) -> UiState:
        """Gets the state from which the transition originates.
        
        :return: The state from which the transition originates.
        """
        return self._from_state

    def get_from_state_connecting_point(self) -> _ty.Literal['n', 's', 'e', 'w']:
        """Gets the connecting point of the from state.

        n = North, s = South, e = East, w = West
        
        :return: The connecting point of the from state."""
        return self._from_state_connecting_point

    def get_to_state(self) -> UiState:
        """Gets the state to which the transition leads.
        
        :return: The state to which the transition leads."""
        return self._to_state

    def get_to_state_connecting_point(self) -> _ty.Literal['n', 's', 'e', 'w']:
        """Gets the connecting point of the to state.

        n = North, s = South, e = East, w = West
        
        :return: The connecting point of the to state."""
        return self._to_state_connecting_point

    def is_active(self) -> bool:
        """Checks if the transition is active.
        
        :return: True if the transition is active, False otherwise."""
        return self._is_active

    def _activate(self) -> None:
        """Activates the transition."""
        self._is_active = True

    def _deactivate(self) -> None:
        """Deactivates the transition."""
        self._is_active = False

    def set_condition(self, condition: _ty.List[str]) -> None:
        """Sets the condition of the transition.
        
        :param condition: The condition of the transition.
        :return: None
        """
        self._condition = condition

    def get_condition(self) -> _ty.List[str]:
        """Gets the condition of the transition.
        
        :return: The condition of the transition.
        """
        return self._condition

    def __eq__(self, other: _ty.Self):
        return (self._from_state == other.get_from_state()
                and self._from_state_connecting_point == other.get_from_state_connecting_point()
                and self._to_state == other.get_to_state()
                and self._to_state_connecting_point == other.get_to_state_connecting_point()
                and self._is_active == other.is_active())

    def __hash__(self):
        return hash(repr(self))


@auto_repr_with_privates
class UiAutomaton(IUiAutomaton):

    def __init__(self, automaton_type: str, author: str, state_types_with_design: _ty.Dict[str, _ty.Any]):
        # state_types_with_design = {"end": {"design": "Linex",  future}, "default": {"design": "Line y", future}}
        super().__init__(automaton_type, author, state_types_with_design)

        self._type: str = automaton_type

        self._states: OrderedSet[UiState] = OrderedSet()
        self._transitions: OrderedSet[UiTransition] = OrderedSet()

        self._start_state: UiState | None = None
        self._input: _ty.List[_ty.Any] = []
        self._pointer_index: int = 0

    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)

    def get_start_state(self) -> UiState | None:
        """Gets the start state of the automaton.
        
        :return: The start state of the automaton.
        """
        return self._start_state

    def get_states(self) -> OrderedSet[UiState]:
        """Gets the states of the automaton.
        
        :return: The states of the automaton.
        """
        return self._states

    def get_transitions(self) -> OrderedSet[UiTransition]:
        """Gets the transitions of the automaton.
        
        :return: The transitions of the automaton.
        """
        return self._transitions

    def add_state(self, state: UiState) -> None:
        """Adds a state to the automaton.
        
        :param state: The state to be added.
        :return: None
        """
        self._states.add(state)

    def add_transition(self, transition: UiTransition) -> None:
        """Adds a transition to the automaton.
        
        :param transition: The transition to be added.
        :return: None
        """
        self._transitions.add(transition)

    def get_name(self) -> str:
        """Gets the name of the automaton.
        
        :return: The name of the automaton.
    """
        return self._type

    def set_start_state(self, state: UiState) -> None:
        """Sets the start state of the automaton.
        
        :param state: The start state of the automaton.
        :return: None
        """
        self._start_state = state

        if state not in self._states:
            self.add_state(state)

    def handle_bridge_updates(self) -> None:
        """Handles updates from the UI bridge.
        
        :return: None
        """
        bridge: UiBridge = UiBridge()
        if not bridge.has_ui_items():
            return

        # Handle bridge
        bridge_item: _ty.Dict[str, _ty.Any] = bridge.get_ui_task()
        pass  # Todo: implement as needed

    def get_state_by_id(self, state_id: int) -> UiState:
        """Gets a state by its id.
        
        :param state_id: The id of the state.
        :return: The state with the given id.
        """
        return self._states.get_by_index(state_id)

    def get_state_index(self, state: UiState) -> int:
        """Gets the index of a state.
        
        :param state: The state.
        :return: The index of the state.
        """
        return self._states.get_index(state)

    def get_transition_by_id(self, transition_id: int) -> UiTransition:
        """Gets a transition by its id.
        
        :param transition_id: The id of the transition.
        :return: The transition with the given id.
        """
        return self._transitions.get_by_index(transition_id)

    def get_transition_index(self, transition: UiTransition) -> int:
        """Gets the index of a transition.
        
        :param transition: The transition.
        :return: The index of the transition.
        """
        return self._transitions.get_index(transition)

    def _serialise_structure_for_simulation(self) -> _ty.List[_ty.Dict[str, _ty.Any]]:
        """Serialises the automaton into a format the backend can understand
        
        :return: The serialised structure of the automaton.
        """
        serialised_structure: _ty.List[_ty.Dict[str, _ty.Any]] = []

        for state in self._states:
            data: _ty.Dict[str, _ty.Any] = {}
            data["name"] = state.get_display_text()
            data["type"] = state.get_type()

            # Transitions
            transitions_list: _ty.List[_ty.Dict[str, _ty.Any]] = []
            for transition in self._transitions:
                if transition.get_from_state() != state:
                    continue

                transition_data: _ty.Dict[str, _ty.Any] = {}
                transition_to_state: UiState = transition.get_to_state()

                transition_data["to"] = self.get_state_index(transition_to_state)
                transition_data["condition"] = "|".join(transition.get_condition())
                transition_data["id"] = self.get_transition_index(transition)

                transitions_list.append(transition_data)

            data["transitions"] = transitions_list
            serialised_structure.append(data)

        return serialised_structure

    def simulate(self, input: _ty.List[_ty.Any]) -> None:
        """Simulates the automaton with a given input.
        
        :param input: The input to the automaton.
        :return: None"""
        structure: _ty.Dict[str, _ty.Any] = {}
        structure["action"] = "SIMULATION"
        structure["id"] = f"{self.get_author().lower()}:{self.get_name().lower()}"
        structure["input"] = input
        structure["content"] = self._serialise_structure_for_simulation()

        if not structure["content"]:
            ActLogger().error("No structure found for simulation")
            return

        # send to bridge
        bridge: UiBridge = UiBridge()
        bridge.add_backend_item(structure)

    def handle_simulation_updates(self) -> _result.Result or None:
        """Handles updates from the simulation.
        
        :return: The result of the simulation.
        """
        bridge: UiBridge = UiBridge()
        if not bridge.has_simulation_items():
            return None

        # Remove all other activations
        for state in self.get_states():
            state._deactivate()

        for transition in self.get_transitions():
            transition._deactivate()

        # Handle bridge
        simulation_task: _ty.Dict[str, _ty.Any] = bridge.get_simulation_task()

        if simulation_task["type"].upper() != "SIMULATION_UPDATE":
            if simulation_task["type"].upper() != "SIMULATION_RESULT":
                return

            success = simulation_task["success"]
            if success:
                return _result.Success(simulation_task["message"])
            return _result.Failure(simulation_task["message"])

        automaton_data: _ty.Dict[str, _ty.Any] = simulation_task["automaton"]

        # State data
        if "state" in simulation_task:
            state_data: _ty.Dict[str, _ty.Any] = simulation_task["state"]
            state_index: int = state_data["id"]

            state: UiState = self.get_state_by_id(state_index)
            if state is None:
                return _result.Failure(f"State with index {state_index} not found.")
            state._activate()

        # Transition data
        if "transition" in simulation_task:
            transition_data: _ty.Dict[str, _ty.Any] = simulation_task["transition"]
            transition_index: int = transition_data["id"]

            transition: UiTransition = self.get_transition_by_id(transition_index)
            if transition is None:
                return _result.Failure(f"Transition with index {transition_index} not found.")
            transition._activate()

        # Automaton data
        self._input = automaton_data["input"]
        self._pointer_index = automaton_data["pointer_index"]

        return _result.Success(automaton_data["output"])

    def get_author(self) -> str:
        """Gets the author of the automaton.
        
        :return: The author of the automaton.
        """
        return self._author

    def get_token_lists(self) -> _ty.List[_ty.List[str]]:
        """Gets the token lists of the automaton.
        
        :return: The token lists of the automaton.
        """
        return self._token_lists

    def get_is_changeable_token_list(self) -> _ty.List[bool]:
        """Gets the changeable token lists of the automaton.
        
        :return: The changeable token lists of the automaton.
        """
        return self._changeable_token_lists

    def get_transition_pattern(self) -> _ty.List[int]:
        """Gets the transition pattern of the automaton.
        
        :return: The transition pattern of the automaton.
        """
        return self._transition_pattern

    def set_token_lists(self, token_lists: _ty.List[_ty.List[str]]) -> None:
        """Sets the token lists of the automaton.
        
        :param token_lists: The token lists of the automaton.
        :return: None
        """
        self._token_lists = token_lists

    def set_is_changeable_token_list(self, changeable_token_lists: _ty.List[bool]) -> None:
        """Sets the changeable token lists of the automaton.
        
        :param changeable_token_lists: The changeable token lists of the automaton.
        :return: None
        """
        self._changeable_token_lists = changeable_token_lists

    def set_transition_pattern(self, transition_pattern: _ty.List[int]) -> None:
        """Sets the transition pattern of the automaton.
        
        :param transition_pattern: The transition pattern of the automaton.
        :return: None
        """
        self._transition_pattern = transition_pattern

    def get_state_types_with_design(self) -> _ty.Dict[str, _ty.Any]:
        """Gets the state types with design of the automaton.
        
        :return: The state types with design of the automaton.
        """
        return self._state_types_with_design

    def set_state_types_with_design(self, state_types_with_design: _ty.Dict[str, _ty.Any]) -> None:
        """Sets the state types with design of the automaton.
        
        :param state_types_with_design: The state types with design of the automaton.
        :return: None
        """
        self._state_types_with_design = state_types_with_design

    def __eq__(self, other: _ty.Self):
        return (self._type == other.get_name()
                and self._states == other.get_states()
                and self._transitions == other.get_transitions()
                and self._start_state == other.get_start_state()
                and self._state_types_with_design == other.get_state_types_with_design())
