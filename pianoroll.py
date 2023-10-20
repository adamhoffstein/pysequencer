import asyncio
import dataclasses
from enum import Enum

from rich.segment import Segment
from rich.style import Style
from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.geometry import Offset, Region, Size
from textual.message import Message
from textual.reactive import var
from textual.strip import Strip
from textual.widget import Widget
from textual.widgets import Footer, Log


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


OCTAVES = 2

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


class PianoRoll(Widget):
    class Selected(Message):
        def __init__(
            self, clicked_cell: Offset, current_state: dict[Offset, 1]
        ) -> None:
            self.clicked_cell = clicked_cell
            self.current_state = current_state
            super().__init__()

        @property
        def coords(self) -> str:
            return f"{self.clicked_cell.x}, {self.clicked_cell.y}: {self.current_state}"

    class Played(Message):
        def __init__(self, current_cell: Offset) -> None:
            self.current_cell = current_cell
            super().__init__()

        @property
        def coords(self) -> str:
            return f"{self.current_cell.x}, {self.current_cell.y}"

    COMPONENT_CLASSES = {
        "piano-roll--white-key",
        "piano-roll--white-cell",
        "piano-roll--black-key",
        "piano-roll--black-cell",
        "piano-roll--mouseover-cell",
        "piano-roll--selected-cell",
        "piano-roll--play-inactive",
        "piano-roll--play-active",
    }

    DEFAULT_CSS = """
    PianoRoll .piano-roll--mouseover-cell {
        background: #f0eeb1;
    }
    PianoRoll .piano-roll--selected-cell {
        background: #8b99e2;
    }
    PianoRoll .piano-roll--white-cell {
        background: #a3a3a3;
    }
    PianoRoll .piano-roll--black-cell {
        background: #919090;
    }
    PianoRoll .piano-roll--black-key {
        background: #272829;
    }
    PianoRoll .piano-roll--white-key {
        background: #FFFFFF;
    }
    PianoRoll .piano-roll--play-inactive {
        background: pink;
    }
    PianoRoll .piano-roll--play-active {
        background: red;
    }
    """

    cursor_cell = var(Offset(0, 0))
    last_clicked = var(Offset(0, 0))
    drawn_keys_state = var({})
    play_cursor = var(Offset(1, CURSOR_ROW))

    def __init__(self) -> None:
        super().__init__()
        self.board_size = len(PIANO_KEYS)
        self.virtual_size = Size(8, 1)

    def on_mouse_move(self, event: events.MouseMove) -> None:
        mouse_position = event.offset + self.scroll_offset
        self.cursor_cell = Offset(
            mouse_position.x // 8, mouse_position.y // ROW_LENGTH
        )

    def _on_click(self, event: events.Click) -> None:
        self.last_clicked = self.cursor_cell
        if self.last_clicked.x > 0 and self.last_clicked.y - 1 < len(
            PIANO_KEYS
        ):
            if self.drawn_keys_state.get(self.last_clicked):
                self.drawn_keys_state.pop(self.last_clicked)
            else:
                self.drawn_keys_state.update(
                    {self.last_clicked: PIANO_KEYS[self.last_clicked.y - 1]}
                )
        self.post_message(
            self.Selected(self.last_clicked, self.drawn_keys_state)
        )

    def refresh_cell(
        self, previous_square: Offset, cursor_square: Offset
    ) -> None:
        """Called when the cursor square changes."""

        def get_square_region(square_offset: Offset) -> Region:
            """Get region relative to widget from square coordinate."""
            x, y = square_offset
            region = Region(x * 8, y * ROW_LENGTH, 8, ROW_LENGTH)
            # Move the region in to the widgets frame of reference
            region = region.translate(-self.scroll_offset)
            return region

        # Refresh the previous cursor square
        self.refresh(get_square_region(previous_square))

        # Refresh the new cursor square
        self.refresh(get_square_region(cursor_square))

    def watch_cursor_cell(
        self, previous_cell: Offset, cursor_cell: Offset
    ) -> None:
        """Called when the cursor cell changes."""

        self.refresh_cell(previous_cell, cursor_cell)

    def watch_last_clicked(
        self, previous_cell: Offset, clicked_cell: Offset
    ) -> None:
        """Called when the cursor cell changes."""

        self.refresh_cell(previous_cell, clicked_cell)

    def play(self) -> None:
        self.post_message(self.Played(self.play_cursor))
        if self.play_cursor.x < 16:
            previous_cell = Offset(self.play_cursor.x - 1, CURSOR_ROW)
            self.play_cursor = Offset(self.play_cursor.x + 1, CURSOR_ROW)
        else:
            previous_cell = Offset(16, CURSOR_ROW)
            self.play_cursor = Offset(1, CURSOR_ROW)
        self.refresh_cell(previous_cell, self.play_cursor)

    def clear(self) -> None:
        self.drawn_keys_state = {}
        self.refresh()

    def render_line(self, y: int) -> Strip:
        """Render a line of the widget. y is relative to the top of the widget."""

        row_index = y // ROW_LENGTH

        if row_index > len(PIANO_KEYS) + 1:
            return Strip.blank(self.size.width)

        white_key = self.get_component_rich_style("piano-roll--white-key")
        white_cell = self.get_component_rich_style("piano-roll--white-cell")
        black_key = self.get_component_rich_style("piano-roll--black-key")
        black_cell = self.get_component_rich_style("piano-roll--black-cell")
        cursor = self.get_component_rich_style("piano-roll--mouseover-cell")
        selected = self.get_component_rich_style("piano-roll--selected-cell")
        play_inactive = self.get_component_rich_style(
            "piano-roll--play-inactive"
        )
        play_active = self.get_component_rich_style("piano-roll--play-active")

        def get_style(column: int, row: int) -> Style:
            if row == len(PIANO_KEYS) + 1:
                if Offset(column, row) == self.play_cursor:
                    return play_active
                return play_inactive

            if self.cursor_cell == Offset(column, row):
                return cursor

            if self.drawn_keys_state.get(Offset(column, row)):
                return selected

            current_key: PianoKey = PIANO_KEYS[row_index - 1]

            if column == 0:
                return black_key if current_key.sharp else white_key
            else:
                return black_cell if current_key.sharp else white_cell

        segments = [
            Segment(" " * 8, get_style(column, row_index))
            for column in range(NOTE_COUNT + 1)
        ]

        strip = Strip(segments)
        return strip


class PianoRollApp(App):
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("space", "play", "Play / Stop"),
        ("c", "clear", "Clear"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.is_playing = False

    def compose(self) -> ComposeResult:
        with Container(id="main_container"):
            yield PianoRoll()
            yield Footer()
        with Container(id="debug_container"):
            yield Log()

    def toggle_play(self) -> None:
        self.is_playing = not self.is_playing

    async def action_play(self) -> None:
        self.toggle_play()
        if self.is_playing:
            asyncio.create_task(self.play_sequence())

    def action_clear(self) -> None:
        self.query_one(PianoRoll).clear()

    async def play_sequence(self) -> None:
        while self.is_playing:
            self.query_one(PianoRoll).play()
            await asyncio.sleep(TICK)

    def on_piano_roll_selected(self, message: PianoRoll.Selected) -> None:
        self.query_one(Log).write_line(message.coords)

    def on_piano_roll_played(self, message: PianoRoll.Played) -> None:
        self.query_one(Log).write_line(message.coords)


if __name__ == "__main__":
    app = PianoRollApp()
    app.run()
