from schemas import PianoKey, Note

OCTAVES = 3

KEY_SEQUENCE = []

for octave in range(OCTAVES, 0, -1):
    KEY_SEQUENCE.extend(
        [
            (Note.C, octave, False),
            (Note.C, octave, True),
            (Note.D, octave, False),
            (Note.D, octave, True),
            (Note.E, octave, False),
            (Note.F, octave, False),
            (Note.F, octave, True),
            (Note.G, octave, False),
            (Note.G, octave, True),
            (Note.A, octave, False),
            (Note.A, octave, True),
            (Note.B, octave, False),
        ]
    )

PIANO_KEYS = [PianoKey(*key) for key in KEY_SEQUENCE]

ROW_LENGTH = 1

NOTE_COUNT = 16

CURSOR_ROW = 12 * OCTAVES + 1

TICK = 0.1
