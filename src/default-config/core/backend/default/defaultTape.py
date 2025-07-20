from core.backend.abstract.automaton.itape import ITape as _ITape

# Standard typing imports for aps
import typing as _ty


class DefaultTape(_ITape):
    def __init__(self, original_input: _ty.List[str], can_exceed_length: bool = False, blank_char: str = 'B'):
        super().__init__()
        self._original_input: _ty.List[str] = original_input
        self._simulation_tape: _ty.Dict[int, str] = {int(i): str(v) for i, v in enumerate(self._original_input)}

        self._pointer_index: int = 0
        self._can_exceed_length: bool = can_exceed_length

        self._blank_char: str = blank_char

    def left(self) -> None:
        self._move_pointer(-1)

    def right(self) -> None:
        self._move_pointer(1)

    def hold(self):
        pass

    def _move_pointer(self, pointer_move: int) -> None:
        lower_bound: int = min(self._simulation_tape.keys())
        upper_bound: int = max(self._simulation_tape.keys())

        if lower_bound <= self._pointer_index + pointer_move <= upper_bound:
            self._pointer_index += pointer_move
            return

        # tape is exceeded on the left
        if not self._can_exceed_length:
            raise ValueError("Simulation Tape exceeding is not allowed")

        self._pointer_index += pointer_move

        self._simulation_tape[self._pointer_index] = self._blank_char

    def read(self) -> str:
        return self._simulation_tape[self._pointer_index]

    def write(self, char: str) -> None:
        self._simulation_tape[self._pointer_index] = char

    def is_at_end(self) -> bool:
        return self._pointer_index >= max(self._simulation_tape.keys())

    def is_at_start(self) -> bool:
        return self._pointer_index <= min(self._simulation_tape.keys())

    def get_tape(self) -> _ty.Dict[int, str]:
        return self._simulation_tape

    def get_pointer(self) -> int:
        return self._pointer_index

    def get_original_input(self) -> _ty.List[str]:
        return self._original_input

    def get_blank_char(self) -> str:
        return self._blank_char

    def get_can_exceed_length(self) -> bool:
        return self._can_exceed_length

    def set_can_exceed_length(self, can_exceed_length: bool) -> None:
        self._can_exceed_length = can_exceed_length

    def set_blank_char(self, blank_char: str) -> None:
        self._blank_char = blank_char

    def set_original_input(self, original_input: _ty.List[str]) -> None:
        self._original_input: _ty.List[str] = original_input
        self._simulation_tape: _ty.Dict[int, str] = {int(i): str(v) for i, v in enumerate(self._original_input)}

    def __repr__(self):
        return str({k: self._simulation_tape[k] for k in sorted(self._simulation_tape)})

    @classmethod
    def from_all_args(cls, original_input, simulation_tape, pointer_index, can_exceed_length, blank_char) -> 'DefaultTape':
        obj = cls(original_input, can_exceed_length, blank_char)
        obj._simulation_tape = simulation_tape
        obj._pointer_index = pointer_index
        return obj

    def move_to_beginning(self) -> None:
        self._pointer_index = 0

    def copy(self) -> 'DefaultTape':
        return DefaultTape.from_all_args(
            original_input=self._original_input[:],  # Liste kopieren
            simulation_tape=self._simulation_tape.copy(),  # Dict kopieren
            pointer_index=self._pointer_index,
            can_exceed_length=self._can_exceed_length,
            blank_char=self._blank_char
        )

