"""TBA"""

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


class CardinalDirection:
    North = "n"
    East = "e"
    South = "s"
    West = "w"


@auto_repr_with_privates
class UiState(IUiState):  # TODO: mypy does not like that IUiState is of type Any
    def __init__(self, colour: str, position: _ty.Tuple[float, float], display_text: str, node_type: str):
        super().__init__(colour, position, display_text, node_type)
        self._colour: str = colour
        self._position: _ty.Tuple[float, float] = position
        self._display_text: str = display_text
        self._type: str = node_type
        self._is_active: bool = False

    def set_colour(self, colour: str) -> None:
        self._colour = colour

    def set_position(self, position: _ty.Tuple[float, float]) -> None:
        self._position = position

    def set_display_text(self, display_text: str) -> None:
        self._display_text = display_text

    def get_colour(self) -> str:
        return self._colour

    def get_position(self) -> _ty.Tuple[float, float]:
        return self._position

    def get_display_text(self) -> str:
        return self._display_text

    def get_type(self) -> str:  # TODO: add docu to IUiState
        return self._type

    def is_active(self) -> bool:
        return self._is_active

    def _activate(self) -> None:
        self._is_active = True

    def _deactivate(self) -> None:
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
        self._from_state = from_state

    def set_from_state_connecting_point(self, connecting_point: _ty.Literal['n', 's', 'e', 'w']) -> None:
        self._from_state_connecting_point = connecting_point

    def set_to_state(self, to_state: UiState) -> None:
        self._to_state = to_state

    def set_to_state_connecting_point(self, connecting_point: _ty.Literal['n', 's', 'e', 'w']) -> None:
        self._to_state_connecting_point = connecting_point

    def get_from_state(self) -> UiState:
        return self._from_state

    def get_from_state_connecting_point(self) -> _ty.Literal['n', 's', 'e', 'w']:
        return self._from_state_connecting_point

    def get_to_state(self) -> UiState:
        return self._to_state

    def get_to_state_connecting_point(self) -> _ty.Literal['n', 's', 'e', 'w']:
        return self._to_state_connecting_point

    def is_active(self) -> bool:
        return self._is_active

    def _activate(self) -> None:
        self._is_active = True

    def _deactivate(self) -> None:
        self._is_active = False

    def set_condition(self, condition: _ty.List[str]) -> None:
        self._condition = condition

    def get_condition(self) -> _ty.List[str]:
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
        return self._start_state

    def get_states(self) -> OrderedSet[UiState]:
        return self._states

    def get_transitions(self) -> OrderedSet[UiTransition]:
        return self._transitions

    def add_state(self, state: UiState) -> None:
        self._states.add(state)

    def add_transition(self, transition: UiTransition) -> None:
        self._transitions.add(transition)

    def get_name(self) -> str:
        return self._type

    def set_start_state(self, state: UiState) -> None:
        self._start_state = state

        if state not in self._states:
            self.add_state(state)

    def handle_bridge_updates(self) -> None:
        bridge: UiBridge = UiBridge()
        if not bridge.has_ui_items():
            return

        # Handle bridge
        bridge_item: _ty.Dict[str, _ty.Any] = bridge.get_ui_task()
        pass  # Todo: implement as needed

    def get_state_by_id(self, state_id: int) -> UiState:
        return self._states.get_by_index(state_id)

    def get_state_index(self, state: UiState) -> int:
        return self._states.get_index(state)

    def get_transition_by_id(self, transition_id: int) -> UiTransition:
        return self._transitions.get_by_index(transition_id)

    def get_transition_index(self, transition: UiTransition) -> int:
        return self._transitions.get_index(transition)

    def _serialise_structure_for_simulation(self) -> _ty.List[_ty.Dict[str, _ty.Any]]:  # TODO testing
        """Serialises the automaton into a format the backend can understand"""
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

                transitions_list.append(transition_data)

            data["transitions"] = transitions_list
            serialised_structure.append(data)

        return serialised_structure

    def simulate(self, input: _ty.List[_ty.Any]) -> None:
        """Simulates the automaton with a given input."""
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
        """
        Handles updates from the simulation bridge.
        
        Returns:
            _result.Result: A result object indicating the success or failure of the operation.
                            (If success contains the return value of the simulation step)
            None: If the simulation bridge does not have any items.
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

        state_data: _ty.Dict[str, _ty.Any] = simulation_task["state"]
        # transition_data: _ty.Dict[str, _ty.Any] = simulation_task["transition"]
        automaton_data: _ty.Dict[str, _ty.Any] = simulation_task["automaton"]

        # State data
        state_index: int = state_data["id"]

        state: UiState = self.get_state_by_id(state_index)
        if state is None:
            return _result.Failure(f"State with index {state_index} not found.")
        state._activate()

        # Transition data
        # transition_index: int = transition_data["id"]
        #
        # transition: UiTransition = self.get_transition_by_id(transition_index)
        # if transition is None:
        #     return _result.Failure(f"Transition with index {transition_index} not found.")
        # transition._activate()

        # Automaton data
        self._input = automaton_data["input"]
        self._pointer_index = automaton_data["pointer_index"]

        return _result.Success(automaton_data["output"])

    def get_author(self) -> str:
        return self._author

    def get_token_lists(self) -> _ty.List[_ty.List[str]]:
        return self._token_lists

    def get_is_changeable_token_list(self) -> _ty.List[bool]:
        return self._changeable_token_lists

    def get_transition_pattern(self) -> _ty.List[int]:
        return self._transition_pattern

    def set_token_lists(self, token_lists: _ty.List[_ty.List[str]]) -> None:
        self._token_lists = token_lists

    def set_is_changeable_token_list(self, changeable_token_lists: _ty.List[bool]) -> None:
        self._changeable_token_lists = changeable_token_lists

    def set_transition_pattern(self, transition_pattern: _ty.List[int]) -> None:
        self._transition_pattern = transition_pattern

    def get_state_types_with_design(self) -> _ty.Dict[str, _ty.Any]:
        return self._state_types_with_design

    def set_state_types_with_design(self, state_types_with_design: _ty.Dict[str, _ty.Any]) -> None:
        self._state_types_with_design = state_types_with_design

    def __eq__(self, other: _ty.Self):
        return (self._type == other.get_name()
                and self._states == other.get_states()
                and self._transitions == other.get_transitions()
                and self._start_state == other.get_start_state()
                and self._state_types_with_design == other.get_state_types_with_design())
