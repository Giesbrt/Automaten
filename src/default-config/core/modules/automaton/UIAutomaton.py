"""TBA"""

from returns import result as _result

# Bridge Import
from core.modules.automaton.UiBridge import UiBridge

# abstract imports
from core.modules.abstract import IUiState
from core.modules.abstract import IUiTransition
from core.modules.abstract import IUiAutomaton

# Standard typing imports for aps
import collections.abc as _a
import abc as _abc
import typing as _ty
import types as _ts


class UiState(IUiState):
    def __init__(self, colour: str, position: _ty.Tuple[float, float], display_text: str, automaton_type: str):
        super().__init__(colour, position, display_text, automaton_type)
        self._colour: str = colour
        self._position: _ty.Tuple[float, float] = position
        self._display_text: str = display_text
        self._type: str = automaton_type
        self._is_active: bool = False

    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)

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

    def is_active(self) -> bool:
        return self._is_active

    def _activate(self) -> None:
        self._is_active = True

    def _deactivate(self) -> None:
        self._is_active = False


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


class UiAutomaton(IUiAutomaton):

    def __init__(self, automaton_type: str, author: str):
        super().__init__(automaton_type, author)

        self._type: str = automaton_type

        self._states: _ty.Set[UiState] = set()
        self._transitions: _ty.Set[UiTransition] = set()

        self._start_state: UiState | None = None
        self._input: _ty.List[_ty.Any] = []
        self._pointer_index: int = 0

    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)

    def delete_state(self, state: UiState) -> None:
        # Convert state into index of _states and send to bridge
        if state not in self.get_states():
            return

        if state == self._start_state:
            self._start_state = None

        # Get index of state in _states
        state_index: int = 0
        for i, s in enumerate(self._states):
            if s != state:
                continue

            state_index = i
            break

        # Note: state_index can not be None here, as state is in _states

        # Pack state_index into json/dict format
        task_list: _ty.List[_ty.Dict[str, _ty.Any]] = []

        delete_statement: _ty.Dict[str, _ty.Any] = {}
        delete_statement["type"] = "DELETE_STATE"
        delete_statement["state_index"] = state_index
        task_list.append(delete_statement)

        # remove all transitions that are connected to this state
        for i, t in enumerate(self._transitions):
            if t.get_from_state() == state or t.get_to_state() == state:
                delete_statement: _ty.Dict[str, _ty.Any] = {}
                delete_statement["type"] = "DELETE_TRANSITION"
                delete_statement["transition_index"] = i
                task_list.append(delete_statement)

        # Send delete_statement to bridge
        bridge: UiBridge = UiBridge()

        for task in task_list:
            bridge.add_backend_item(task)

    def delete_transition(self, transition: UiTransition) -> None:
        # Convert into index and send to bridge
        if transition not in self.get_transitions():
            return

        # Get index of transition in _transitions
        transition_index: int = None
        for i, t in enumerate(self._transitions):
            if t != transition:
                continue

            transition_index = i
            break

        # Note: transition_index can not be None here, as transition is in _transitions

        # Pack transition_index into json/dict format
        delete_statement: _ty.Dict[str, _ty.Any] = {}
        delete_statement["type"] = "DELETE_TRANSITION"
        delete_statement["transition_index"] = transition_index

        # Send delete_statement to bridge
        bridge: UiBridge = UiBridge()

        bridge.add_backend_item(delete_statement)

    def get_states(self) -> _ty.Set[UiState]:
        return self._states

    def get_transitions(self) -> _ty.Set[UiTransition]:
        return self._transitions

    def add_state(self, state: UiState) -> None:
        self._states.add(state)

    def add_transition(self, transition: UiTransition) -> None:
        self._transitions.add(transition)

    def get_type(self) -> str:
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
        for i, state in enumerate(self._states):
            if i != state_id:
                continue

            return state

    def get_transition_by_id(self, transition_id: int) -> UiTransition:
        for i, transition in enumerate(self._transitions):
            if i != transition_id:
                continue

            return transition

    def simulate(self, input: _ty.List[_ty.Any]) -> None:
        # bridge hey ich will simulieren mit input "input"
        pass  # Todo

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
        transition_data: _ty.Dict[str, _ty.Any] = simulation_task["transition"]
        automaton_data: _ty.Dict[str, _ty.Any] = simulation_task["automaton"]

        # State data
        state_index: int = state_data["id"]

        state: UiState = self.get_state_by_id(state_index)
        if state is None:
            return _result.Failure(f"State with index {state_index} not found.")
        state._activate()

        # Transition data
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
        return self._author

    def get_token_lists(self) -> _ty.List[_ty.List[str]]:
        return self._token_lists

    def get_changeable_token_lists(self) -> _ty.List[bool]:
        return self._changeable_token_lists

    def get_transition_pattern(self) -> _ty.List[int]:
        return self._transition_pattern

    def set_token_lists(self, token_lists: _ty.List[_ty.List[str]]) -> None:
        self._token_lists = token_lists

    def set_changeable_token_lists(self, changeable_token_lists: _ty.List[bool]) -> None:
        self._changeable_token_lists = changeable_token_lists

    def set_transition_pattern(self, transition_pattern: _ty.List[int]) -> None:
        self._transition_pattern = transition_pattern


