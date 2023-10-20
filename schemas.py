import dataclasses
from enum import Enum


class Note(Enum):
    A = 1
    B = 2
    C = 3
    D = 4
    E = 5
    F = 6
    G = 7


@dataclasses.dataclass
class PianoKey:
    note: Note
    octave: int
    sharp: bool
