from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from itertools import product
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.patches import Rectangle
from matplotlib.widgets import Button


REFERENCE_PATH = Path(__file__).with_name("scale-modes-reference.md")
STANDARD_TUNING_8_STRING = ["E", "B", "G", "D", "A", "E", "B", "F#"]
KEY_ORDER = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
NOTE_TO_PITCH = {
    "C": 0,
    "B#": 0,
    "C#": 1,
    "Db": 1,
    "Cx": 2,
    "D": 2,
    "Ebb": 2,
    "D#": 3,
    "Eb": 3,
    "Fbb": 3,
    "Dx": 4,
    "E": 4,
    "Fb": 4,
    "E#": 5,
    "F": 5,
    "Gbb": 5,
    "F#": 6,
    "Gb": 6,
    "Ex": 6,
    "Fx": 7,
    "G": 7,
    "Abb": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "Bbb": 9,
    "A#": 10,
    "Bb": 10,
    "Cbb": 10,
    "Ax": 11,
    "B": 11,
    "Cb": 11,
}
PITCH_TO_ENHARMONIC_LABEL = {
    0: "C",
    1: "C#/Db",
    2: "D",
    3: "D#/Eb",
    4: "E",
    5: "F",
    6: "F#/Gb",
    7: "G",
    8: "G#/Ab",
    9: "A",
    10: "A#/Bb",
    11: "B",
}
LETTER_TO_PITCH = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
LETTER_ORDER = ["C", "D", "E", "F", "G", "A", "B"]
DISPLAY_MODES = ["Notes", "Intervals", "Chords"]
ROMAN_NUMERALS = ["I", "II", "III", "IV", "V", "VI", "VII"]
INSTRUMENTS = ["guitar", "piano"]
WHITE_PITCHES = {0, 2, 4, 5, 7, 9, 11}


@dataclass(frozen=True)
class ScaleDefinition:
    family: str
    mode: str
    key: str
    notes: tuple[str, ...]


@dataclass(frozen=True)
class ChordDefinition:
    degree_index: int
    roman_numeral: str
    quality: str
    notes: tuple[str, ...]
    interval_labels: tuple[str, ...]


@dataclass(frozen=True)
class ChordPosition:
    strings: tuple[int, ...]
    frets: tuple[int, ...]


@dataclass(frozen=True)
class PianoKey:
    midi: int
    pitch: int
    octave: int
    is_white: bool
    x: float
    label: str


def parse_scale_reference(path: Path) -> tuple[list[str], dict[tuple[str, str, str], ScaleDefinition]]:
    families: list[str] = []
    scale_map: dict[tuple[str, str, str], ScaleDefinition] = {}

    current_family: str | None = None
    current_mode: str | None = None
    in_table = False

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            in_table = False
            continue

        if line.startswith("## "):
            current_family = line[3:].strip()
            families.append(current_family)
            current_mode = None
            in_table = False
            continue

        if line.startswith("### "):
            current_mode = line[4:].strip()
            in_table = False
            continue

        if line.startswith("| Key | Notes |"):
            in_table = True
            continue

        if line.startswith("| --- | --- |"):
            continue

        if in_table and line.startswith("|") and current_family and current_mode:
            match = re.match(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|$", line)
            if not match:
                continue
            key, note_block = match.groups()
            notes = tuple(note.strip() for note in note_block.split("-"))
            scale_map[(current_family, current_mode, key)] = ScaleDefinition(
                family=current_family,
                mode=current_mode,
                key=key,
                notes=notes,
            )

    return families, scale_map


def note_to_pitch(note: str) -> int:
    try:
        return NOTE_TO_PITCH[note]
    except KeyError as exc:
        raise ValueError(f"Unsupported note spelling: {note}") from exc


def pitch_to_display_label(pitch: int) -> str:
    try:
        return PITCH_TO_ENHARMONIC_LABEL[pitch]
    except KeyError as exc:
        raise ValueError(f"Unsupported pitch class: {pitch}") from exc


def split_note(note: str) -> tuple[str, str]:
    match = re.match(r"^([A-G])(.*)$", note)
    if not match:
        raise ValueError(f"Unsupported note spelling: {note}")
    return match.group(1), match.group(2)


def accidental_offset(accidental: str) -> int:
    if "x" in accidental:
        return accidental.count("x") * 2 - accidental.count("b")
    return accidental.count("#") - accidental.count("b")


def interval_label(root: str, note: str) -> str:
    root_letter, root_accidental = split_note(root)
    note_letter, note_accidental = split_note(note)
    root_index = LETTER_ORDER.index(root_letter)
    note_index = LETTER_ORDER.index(note_letter)
    degree = ((note_index - root_index) % 7) + 1

    root_pitch = LETTER_TO_PITCH[root_letter] + accidental_offset(root_accidental)
    note_pitch = LETTER_TO_PITCH[note_letter] + accidental_offset(note_accidental)
    actual = (note_pitch - root_pitch) % 12
    expected = {1: 0, 2: 2, 3: 4, 4: 5, 5: 7, 6: 9, 7: 11}[degree]
    delta = actual - expected
    if delta > 6:
        delta -= 12
    if delta < -6:
        delta += 12

    accidental_prefix = {0: "", -1: "b", -2: "bb", 1: "#", 2: "x"}.get(delta, "")
    if accidental_prefix == "":
        if delta not in {0}:
            accidental_prefix = f"{'b' * abs(delta)}" if delta < 0 else f"{'#' * delta}"
    return f"{accidental_prefix}{degree}"


def chord_quality(chord_notes: tuple[str, str, str]) -> str:
    root_pitch = note_to_pitch(chord_notes[0])
    third = (note_to_pitch(chord_notes[1]) - root_pitch) % 12
    fifth = (note_to_pitch(chord_notes[2]) - root_pitch) % 12
    quality_map = {
        (4, 7): "major",
        (3, 7): "minor",
        (3, 6): "diminished",
        (4, 8): "augmented",
    }
    return quality_map.get((third, fifth), "other")


def roman_for_quality(degree_index: int, quality: str) -> str:
    base = ROMAN_NUMERALS[degree_index]
    if quality == "major":
        return base
    if quality == "minor":
        return base.lower()
    if quality == "diminished":
        return f"{base.lower()}°"
    if quality == "augmented":
        return f"{base}+"
    return base


def build_diatonic_triads(scale: ScaleDefinition) -> list[ChordDefinition]:
    chords: list[ChordDefinition] = []
    for degree_index in range(len(scale.notes)):
        chord_notes = (
            scale.notes[degree_index],
            scale.notes[(degree_index + 2) % len(scale.notes)],
            scale.notes[(degree_index + 4) % len(scale.notes)],
        )
        quality = chord_quality(chord_notes)
        chords.append(
            ChordDefinition(
                degree_index=degree_index,
                roman_numeral=roman_for_quality(degree_index, quality),
                quality=quality,
                notes=chord_notes,
                interval_labels=tuple(interval_label(chord_notes[0], note) for note in chord_notes),
            )
        )
    return chords


def generate_chord_positions(chord: ChordDefinition, max_fret: int) -> list[ChordPosition]:
    chord_pitches = {note_to_pitch(note) for note in chord.notes}
    candidates: list[tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int, int]]] = []

    for start_string in range(len(STANDARD_TUNING_8_STRING) - 2):
        strings = (start_string, start_string + 1, start_string + 2)
        for window_start in range(0, max_fret + 1):
            window_end = min(max_fret, window_start + 4)
            choices: list[list[int]] = []

            for string_index in strings:
                open_pitch = note_to_pitch(STANDARD_TUNING_8_STRING[string_index])
                frets = []
                for fret in range(0, window_end + 1):
                    if fret == 0 and window_start > 0:
                        continue
                    if fret > 0 and fret < window_start:
                        continue
                    if (open_pitch + fret) % 12 in chord_pitches:
                        frets.append(fret)
                if not frets:
                    choices = []
                    break
                choices.append(frets[:4])

            if not choices:
                continue

            for frets in product(*choices):
                used = [fret for fret in frets if fret > 0]
                if used and max(used) - min(used) > 3:
                    continue
                pitches = tuple(
                    (note_to_pitch(STANDARD_TUNING_8_STRING[string_index]) + fret) % 12
                    for string_index, fret in zip(strings, frets)
                )
                if set(pitches) != chord_pitches:
                    continue
                lowest_fret = min(used) if used else 0
                span = (max(used) - lowest_fret) if used else 0
                candidates.append((strings, frets, (lowest_fret, span, sum(frets), start_string)))

    candidates.sort(key=lambda item: item[2])
    unique: list[ChordPosition] = []
    seen: set[tuple[tuple[int, ...], tuple[int, ...]]] = set()
    for strings, frets, _score in candidates:
        key = (strings, frets)
        if key in seen:
            continue
        seen.add(key)
        unique.append(ChordPosition(strings=strings, frets=frets))
        if len(unique) == 4:
            break
    return unique


def build_piano_keys(start_midi: int, octaves: int) -> list[PianoKey]:
    white_positions: dict[int, float] = {}
    keys: list[PianoKey] = []
    white_index = 0

    for midi in range(start_midi, start_midi + octaves * 12 + 1):
        pitch = midi % 12
        octave = (midi // 12) - 1
        if pitch in WHITE_PITCHES:
            white_positions[midi] = float(white_index)
            keys.append(
                PianoKey(
                    midi=midi,
                    pitch=pitch,
                    octave=octave,
                    is_white=True,
                    x=float(white_index),
                    label=f"{pitch_to_display_label(pitch)}{octave}",
                )
            )
            white_index += 1

    for midi in range(start_midi, start_midi + octaves * 12 + 1):
        pitch = midi % 12
        if pitch in WHITE_PITCHES:
            continue
        octave = (midi // 12) - 1
        left_x = white_positions[midi - 1]
        keys.append(
            PianoKey(
                midi=midi,
                pitch=pitch,
                octave=octave,
                is_white=False,
                x=left_x + 0.68,
                label=f"{pitch_to_display_label(pitch)}{octave}",
            )
        )

    keys.sort(key=lambda key: (key.is_white, key.midi))
    return keys


class FretboardScaleViewer:
    def __init__(
        self,
        family_order: list[str],
        scales: dict[tuple[str, str, str], ScaleDefinition],
        frets: int,
        start_family: str,
        start_mode: str,
        start_key: str,
        start_display: str,
        start_degree: int,
    ) -> None:
        self.family_order = family_order
        self.scales = scales
        self.frets = frets
        self.family_to_modes = self._build_family_mode_index()

        self.family_index = self.family_order.index(start_family)
        self.mode_index = self.family_to_modes[start_family].index(start_mode)
        self.key_index = KEY_ORDER.index(start_key)
        self.display_mode_index = DISPLAY_MODES.index(start_display)
        self.chord_degree_index = start_degree % 7

        self.fig, self.ax = plt.subplots(figsize=(16, 7))
        self.fig.subplots_adjust(bottom=0.28, left=0.06, right=0.72, top=0.88)
        self.chord_axes = [
            self.fig.add_axes([0.76, 0.60 - i * 0.15, 0.2, 0.12]) for i in range(4)
        ]
        self._build_buttons()
        self.fig.canvas.mpl_connect("key_press_event", self._on_key_press)
        self.redraw()

    def _build_family_mode_index(self) -> dict[str, list[str]]:
        index: dict[str, list[str]] = {family: [] for family in self.family_order}
        for family, mode, key in self.scales:
            if key != "C":
                continue
            index[family].append(mode)
        return index

    def current_family(self) -> str:
        return self.family_order[self.family_index]

    def current_mode(self) -> str:
        return self.family_to_modes[self.current_family()][self.mode_index]

    def current_key(self) -> str:
        return KEY_ORDER[self.key_index]

    def current_scale(self) -> ScaleDefinition:
        return self.scales[(self.current_family(), self.current_mode(), self.current_key())]

    def current_display_mode(self) -> str:
        return DISPLAY_MODES[self.display_mode_index]

    def _build_buttons(self) -> None:
        button_specs = [
            ("Prev Family", [0.06, 0.10, 0.11, 0.06], lambda event: self.shift_family(-1)),
            ("Next Family", [0.18, 0.10, 0.11, 0.06], lambda event: self.shift_family(1)),
            ("Prev Mode", [0.31, 0.10, 0.10, 0.06], lambda event: self.shift_mode(-1)),
            ("Next Mode", [0.42, 0.10, 0.10, 0.06], lambda event: self.shift_mode(1)),
            ("Prev Key", [0.54, 0.10, 0.09, 0.06], lambda event: self.shift_key(-1)),
            ("Next Key", [0.64, 0.10, 0.09, 0.06], lambda event: self.shift_key(1)),
            ("Prev View", [0.06, 0.02, 0.11, 0.06], lambda event: self.shift_display_mode(-1)),
            ("Next View", [0.18, 0.02, 0.11, 0.06], lambda event: self.shift_display_mode(1)),
            ("Prev Chord", [0.31, 0.02, 0.11, 0.06], lambda event: self.shift_chord_degree(-1)),
            ("Next Chord", [0.43, 0.02, 0.11, 0.06], lambda event: self.shift_chord_degree(1)),
        ]
        self.buttons = []
        for label, rect, handler in button_specs:
            button_ax = self.fig.add_axes(rect)
            button = Button(button_ax, label)
            button.on_clicked(handler)
            self.buttons.append(button)

    def shift_family(self, delta: int) -> None:
        self.family_index = (self.family_index + delta) % len(self.family_order)
        mode_count = len(self.family_to_modes[self.current_family()])
        self.mode_index %= mode_count
        self.redraw()

    def shift_mode(self, delta: int) -> None:
        modes = self.family_to_modes[self.current_family()]
        self.mode_index = (self.mode_index + delta) % len(modes)
        self.redraw()

    def shift_key(self, delta: int) -> None:
        self.key_index = (self.key_index + delta) % len(KEY_ORDER)
        self.redraw()

    def shift_display_mode(self, delta: int) -> None:
        self.display_mode_index = (self.display_mode_index + delta) % len(DISPLAY_MODES)
        self.redraw()

    def shift_chord_degree(self, delta: int) -> None:
        self.chord_degree_index = (self.chord_degree_index + delta) % 7
        self.redraw()

    def _on_key_press(self, event) -> None:
        keymap = {
            "left": lambda: self.shift_key(-1),
            "right": lambda: self.shift_key(1),
            "up": lambda: self.shift_mode(1),
            "down": lambda: self.shift_mode(-1),
            "[": lambda: self.shift_family(-1),
            "]": lambda: self.shift_family(1),
            ",": lambda: self.shift_chord_degree(-1),
            ".": lambda: self.shift_chord_degree(1),
            "n": lambda: self.set_display_mode("Notes"),
            "i": lambda: self.set_display_mode("Intervals"),
            "c": lambda: self.set_display_mode("Chords"),
        }
        handler = keymap.get(event.key)
        if handler:
            handler()

    def set_display_mode(self, mode: str) -> None:
        self.display_mode_index = DISPLAY_MODES.index(mode)
        self.redraw()

    def redraw(self) -> None:
        scale = self.current_scale()
        scale_pitch_classes = {note_to_pitch(note) for note in scale.notes}
        root_pitch = note_to_pitch(scale.notes[0])
        interval_lookup = {note_to_pitch(note): interval_label(scale.notes[0], note) for note in scale.notes}
        diatonic_chords = build_diatonic_triads(scale)
        active_chord = diatonic_chords[self.chord_degree_index]
        active_chord_pitches = {note_to_pitch(note) for note in active_chord.notes}
        active_root_pitch = note_to_pitch(active_chord.notes[0]) if self.current_display_mode() == "Chords" else root_pitch

        self.ax.clear()
        self.ax.set_xlim(-0.75, self.frets + 0.75)
        self.ax.set_ylim(-0.75, len(STANDARD_TUNING_8_STRING) - 0.25)
        self.ax.invert_yaxis()
        self.ax.axis("off")
        self.ax.set_facecolor("#f5ede0")

        for fret in range(self.frets + 1):
            x = fret
            linewidth = 4 if fret == 0 else 1.6
            color = "#4f3422" if fret == 0 else "#8b735f"
            self.ax.plot([x, x], [0, len(STANDARD_TUNING_8_STRING) - 1], color=color, linewidth=linewidth, zorder=1)
            if 0 < fret <= self.frets:
                self.ax.text(fret - 0.5, -0.45, str(fret), ha="center", va="center", fontsize=10, color="#4f3422")

        for string_index, open_note in enumerate(STANDARD_TUNING_8_STRING):
            y = string_index
            open_pitch = note_to_pitch(open_note)
            active_pitches = active_chord_pitches if self.current_display_mode() == "Chords" else scale_pitch_classes
            open_in_scale = open_pitch in active_pitches
            open_is_root = open_pitch == active_root_pitch
            self.ax.plot([0, self.frets], [y, y], color="#9a9a9a", linewidth=1.2 + (string_index + 1) * 0.25, zorder=1)
            self.ax.text(-0.45, y, open_note, ha="center", va="center", fontsize=11, fontweight="bold", color="#1f2933")
            open_marker_face = "#d94841" if open_is_root else "#2a9d8f" if open_in_scale else "#f5ede0"
            open_marker_edge = "#641220" if open_is_root else "#155e63" if open_in_scale else "#4f3422"
            open_string_marker = Circle(
                (-0.18, y),
                0.18,
                facecolor=open_marker_face,
                edgecolor=open_marker_edge,
                linewidth=1.4,
                zorder=2,
            )
            self.ax.add_patch(open_string_marker)
            if open_in_scale:
                if self.current_display_mode() == "Intervals":
                    open_label = interval_lookup[open_pitch]
                elif self.current_display_mode() == "Chords":
                    open_label = interval_label(
                        active_chord.notes[0],
                        self._preferred_label_for_pitch(open_pitch, active_chord.notes),
                    )
                else:
                    open_label = pitch_to_display_label(open_pitch)
                self.ax.text(-0.18, y, open_label, ha="center", va="center", fontsize=8, color="white", zorder=4)

        for string_index, open_note in enumerate(STANDARD_TUNING_8_STRING):
            open_pitch = note_to_pitch(open_note)
            for fret in range(1, self.frets + 1):
                pitch = (open_pitch + fret) % 12
                highlight_pitches = active_chord_pitches if self.current_display_mode() == "Chords" else scale_pitch_classes
                if pitch not in highlight_pitches:
                    continue

                x = fret - 0.5
                y = string_index
                is_root = pitch == active_root_pitch
                facecolor = "#d94841" if is_root else "#2a9d8f"
                edgecolor = "#641220" if is_root else "#155e63"
                if self.current_display_mode() == "Intervals":
                    note_name = interval_lookup[pitch]
                elif self.current_display_mode() == "Chords":
                    note_name = interval_label(active_chord.notes[0], self._preferred_label_for_pitch(pitch, active_chord.notes))
                else:
                    note_name = pitch_to_display_label(pitch)
                radius = 0.23

                marker = Circle((x, y), radius, facecolor=facecolor, edgecolor=edgecolor, linewidth=1.5, zorder=3)
                self.ax.add_patch(marker)
                self.ax.text(x, y, note_name, ha="center", va="center", fontsize=8, color="black", zorder=4)

        formula_text = "  ".join(interval_label(scale.notes[0], note) for note in scale.notes)
        self.ax.text(
            self.frets / 2,
            len(STANDARD_TUNING_8_STRING) - 0.02,
            f"View: {self.current_display_mode()} | Formula: {formula_text} | Arrows change key/mode, [ ] family, n/i/c view, ,/. chord degree",
            ha="center",
            va="bottom",
            fontsize=10,
            color="#4f3422",
        )
        self.ax.set_title(
            f"8-String Guitar Fretboard ({'-'.join(STANDARD_TUNING_8_STRING)})\n"
            f"{scale.key} {scale.mode} [{scale.family}]",
            fontsize=16,
            fontweight="bold",
            color="#1f2933",
            pad=20,
        )
        self._draw_chord_panel(diatonic_chords)
        self.fig.canvas.draw_idle()

    def _draw_chord_panel(self, diatonic_chords: list[ChordDefinition]) -> None:
        active_chord = diatonic_chords[self.chord_degree_index]
        positions = generate_chord_positions(active_chord, self.frets)

        chord_summary = "  ".join(
            f"{chord.roman_numeral} {chord.notes[0]} {chord.quality}"
            for chord in diatonic_chords
        )
        self.fig.texts.clear()
        self.fig.text(
            0.76,
            0.91,
            "Diatonic Chords",
            fontsize=12,
            fontweight="bold",
            color="#1f2933",
        )
        self.fig.text(
            0.76,
            0.875,
            chord_summary,
            fontsize=9,
            color="#4f3422",
        )
        self.fig.text(
            0.76,
            0.84,
            f"Selected: {active_chord.roman_numeral}  {'-'.join(active_chord.notes)}  ({active_chord.quality})",
            fontsize=10,
            color="#1f2933",
        )

        for index, chord_ax in enumerate(self.chord_axes):
            chord_ax.clear()
            chord_ax.set_facecolor("#fbf7ef")
            chord_ax.axis("off")
            if index >= len(positions):
                chord_ax.text(0.5, 0.5, "No more shapes", ha="center", va="center", fontsize=9, color="#8b735f")
                continue
            self._draw_chord_diagram(chord_ax, active_chord, positions[index], index + 1)

    def _draw_chord_diagram(
        self,
        chord_ax,
        chord: ChordDefinition,
        position: ChordPosition,
        diagram_number: int,
    ) -> None:
        strings = position.strings
        frets = position.frets
        used_frets = [fret for fret in frets if fret > 0]
        base_fret = min(used_frets) if used_frets and min(used_frets) > 1 else 1
        last_fret = max(max(frets), base_fret + 3)

        chord_ax.set_xlim(-0.3, len(strings) - 0.7)
        chord_ax.set_ylim(-0.6, 4.4)
        chord_ax.invert_yaxis()

        for string_offset in range(len(strings)):
            chord_ax.plot([string_offset, string_offset], [0, 4], color="#8b735f", linewidth=1.4)
        for fret_offset in range(5):
            linewidth = 2.5 if fret_offset == 0 and base_fret == 1 else 1.2
            chord_ax.plot([0, len(strings) - 1], [fret_offset, fret_offset], color="#8b735f", linewidth=linewidth)

        chord_ax.text(
            0,
            -0.35,
            f"Pos {diagram_number}: strings {strings[0] + 1}-{strings[-1] + 1}",
            ha="left",
            va="center",
            fontsize=8,
            color="#1f2933",
        )
        chord_ax.text(
            len(strings) - 1,
            -0.35,
            f"fret {base_fret}",
            ha="right",
            va="center",
            fontsize=8,
            color="#4f3422",
        )

        for string_offset, (string_index, fret) in enumerate(zip(strings, frets)):
            pitch = (note_to_pitch(STANDARD_TUNING_8_STRING[string_index]) + fret) % 12
            note_name = self._preferred_label_for_pitch(pitch, chord.notes)
            label = interval_label(chord.notes[0], note_name)
            if fret == 0:
                chord_ax.text(string_offset, -0.1, "O", ha="center", va="center", fontsize=9, color="#155e63")
                y = 0.5
            else:
                y = fret - base_fret + 0.5
            is_root = pitch == note_to_pitch(chord.notes[0])
            marker = Circle(
                (string_offset, y),
                0.18,
                facecolor="#d94841" if is_root else "#2a9d8f",
                edgecolor="#641220" if is_root else "#155e63",
                linewidth=1.2,
            )
            chord_ax.add_patch(marker)
            chord_ax.text(string_offset, y, label, ha="center", va="center", fontsize=7, color="black")

    @staticmethod
    def _preferred_label_for_pitch(pitch: int, notes: tuple[str, ...]) -> str:
        for note in notes:
            if note_to_pitch(note) == pitch:
                return note
        raise ValueError(f"Pitch {pitch} not found in scale notes")


class PianoScaleViewer:
    def __init__(
        self,
        family_order: list[str],
        scales: dict[tuple[str, str, str], ScaleDefinition],
        octaves: int,
        start_note: str,
        start_family: str,
        start_mode: str,
        start_key: str,
        start_display: str,
    ) -> None:
        self.family_order = family_order
        self.scales = scales
        self.octaves = octaves
        self.family_to_modes = self._build_family_mode_index()

        self.family_index = self.family_order.index(start_family)
        self.mode_index = self.family_to_modes[start_family].index(start_mode)
        self.key_index = KEY_ORDER.index(start_key)
        self.display_mode_index = DISPLAY_MODES.index(start_display)
        self.start_midi = self._start_note_to_midi(start_note)
        self.keys = build_piano_keys(self.start_midi, self.octaves)

        self.fig, self.ax = plt.subplots(figsize=(16, 5))
        self.fig.subplots_adjust(bottom=0.24, left=0.04, right=0.96, top=0.84)
        self._build_buttons()
        self.fig.canvas.mpl_connect("key_press_event", self._on_key_press)
        self.redraw()

    def _build_family_mode_index(self) -> dict[str, list[str]]:
        index: dict[str, list[str]] = {family: [] for family in self.family_order}
        for family, mode, key in self.scales:
            if key == "C":
                index[family].append(mode)
        return index

    def _start_note_to_midi(self, note: str) -> int:
        match = re.match(r"^([A-G](?:#|b|x){0,2})(-?\d+)$", note)
        if not match:
            raise ValueError("Start note must look like C2, F#3, or Bb1")
        name, octave_text = match.groups()
        octave = int(octave_text)
        return (octave + 1) * 12 + note_to_pitch(name)

    def current_family(self) -> str:
        return self.family_order[self.family_index]

    def current_mode(self) -> str:
        return self.family_to_modes[self.current_family()][self.mode_index]

    def current_key(self) -> str:
        return KEY_ORDER[self.key_index]

    def current_scale(self) -> ScaleDefinition:
        return self.scales[(self.current_family(), self.current_mode(), self.current_key())]

    def current_display_mode(self) -> str:
        return DISPLAY_MODES[self.display_mode_index]

    def _build_buttons(self) -> None:
        specs = [
            ("Prev Family", [0.05, 0.09, 0.12, 0.07], lambda event: self.shift_family(-1)),
            ("Next Family", [0.18, 0.09, 0.12, 0.07], lambda event: self.shift_family(1)),
            ("Prev Mode", [0.33, 0.09, 0.11, 0.07], lambda event: self.shift_mode(-1)),
            ("Next Mode", [0.45, 0.09, 0.11, 0.07], lambda event: self.shift_mode(1)),
            ("Prev Key", [0.60, 0.09, 0.10, 0.07], lambda event: self.shift_key(-1)),
            ("Next Key", [0.71, 0.09, 0.10, 0.07], lambda event: self.shift_key(1)),
            ("Toggle View", [0.83, 0.09, 0.11, 0.07], lambda event: self.shift_display_mode(1)),
        ]
        self.buttons = []
        for label, rect, handler in specs:
            button_ax = self.fig.add_axes(rect)
            button = Button(button_ax, label)
            button.on_clicked(handler)
            self.buttons.append(button)

    def shift_family(self, delta: int) -> None:
        self.family_index = (self.family_index + delta) % len(self.family_order)
        self.mode_index %= len(self.family_to_modes[self.current_family()])
        self.redraw()

    def shift_mode(self, delta: int) -> None:
        modes = self.family_to_modes[self.current_family()]
        self.mode_index = (self.mode_index + delta) % len(modes)
        self.redraw()

    def shift_key(self, delta: int) -> None:
        self.key_index = (self.key_index + delta) % len(KEY_ORDER)
        self.redraw()

    def shift_display_mode(self, delta: int) -> None:
        self.display_mode_index = (self.display_mode_index + delta) % len(DISPLAY_MODES[:2])
        self.redraw()

    def _on_key_press(self, event) -> None:
        keymap = {
            "left": lambda: self.shift_key(-1),
            "right": lambda: self.shift_key(1),
            "up": lambda: self.shift_mode(1),
            "down": lambda: self.shift_mode(-1),
            "[": lambda: self.shift_family(-1),
            "]": lambda: self.shift_family(1),
            "n": lambda: self.set_display_mode("Notes"),
            "i": lambda: self.set_display_mode("Intervals"),
        }
        handler = keymap.get(event.key)
        if handler:
            handler()

    def set_display_mode(self, mode: str) -> None:
        self.display_mode_index = DISPLAY_MODES.index(mode)
        self.redraw()

    def redraw(self) -> None:
        scale = self.current_scale()
        scale_pitches = {note_to_pitch(note) for note in scale.notes}
        root_pitch = note_to_pitch(scale.notes[0])
        interval_lookup = {note_to_pitch(note): interval_label(scale.notes[0], note) for note in scale.notes}

        white_keys = [key for key in self.keys if key.is_white]
        self.ax.clear()
        self.ax.set_xlim(-0.2, len(white_keys) + 0.2)
        self.ax.set_ylim(0, 1.55)
        self.ax.axis("off")
        self.ax.set_facecolor("#efe7d4")

        for key in white_keys:
            is_active = key.pitch in scale_pitches
            is_root = key.pitch == root_pitch
            face = "#d94841" if is_root else "#f7fbff" if not is_active else "#b8e3dc"
            rect = Rectangle((key.x, 0), 1.0, 1.35, facecolor=face, edgecolor="#5b4636", linewidth=1.5, zorder=1)
            self.ax.add_patch(rect)
            label = interval_lookup[key.pitch] if self.current_display_mode() == "Intervals" and is_active else pitch_to_display_label(key.pitch)
            text_color = "#ffffff" if is_root else "#1f2933"
            self.ax.text(key.x + 0.5, 0.23, label if is_active else key.label[:-1], ha="center", va="center", fontsize=8, color=text_color, zorder=3)
            self.ax.text(key.x + 0.5, 0.08, key.label, ha="center", va="center", fontsize=7, color="#4f3422", zorder=3)

        for key in [key for key in self.keys if not key.is_white]:
            is_active = key.pitch in scale_pitches
            is_root = key.pitch == root_pitch
            face = "#d94841" if is_root else "#1f2933" if not is_active else "#2a9d8f"
            rect = Rectangle((key.x, 0.54), 0.64, 0.74, facecolor=face, edgecolor="#0f1720", linewidth=1.2, zorder=4)
            self.ax.add_patch(rect)
            if is_active:
                label = interval_lookup[key.pitch] if self.current_display_mode() == "Intervals" else pitch_to_display_label(key.pitch)
                self.ax.text(key.x + 0.32, 0.87, label, ha="center", va="center", fontsize=7, color="black", zorder=5)

        formula = "  ".join(interval_label(scale.notes[0], note) for note in scale.notes)
        self.ax.set_title(
            f"Piano Scale Viewer\n{scale.key} {scale.mode} [{scale.family}]",
            fontsize=16,
            fontweight="bold",
            color="#1f2933",
            pad=16,
        )
        self.ax.text(
            len(white_keys) / 2,
            1.45,
            f"View: {self.current_display_mode()} | Formula: {formula} | Arrows change key/mode, [ ] family, n/i view",
            ha="center",
            va="center",
            fontsize=10,
            color="#4f3422",
        )
        self.fig.canvas.draw_idle()


def validate_selection(
    family_order: list[str],
    scales: dict[tuple[str, str, str], ScaleDefinition],
    family: str,
    mode: str,
    key: str,
) -> tuple[str, str, str]:
    if family not in family_order:
        family = family_order[0]

    available_modes = sorted({scale.mode for scale in scales.values() if scale.family == family})
    if mode not in available_modes:
        mode = available_modes[0]

    if key not in KEY_ORDER:
        key = "F#"
    if key == "F#":
        key = "Gb"

    if (family, mode, key) not in scales:
        key = "C"

    return family, mode, key


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Interactive guitar or piano scale viewer for the scales in scale-modes-reference.md."
    )
    parser.add_argument(
        "--instrument",
        choices=INSTRUMENTS,
        help="Choose which viewer to launch. If omitted, the program asks at startup.",
    )
    parser.add_argument("--family", default="Major Scale", help="Scale family heading from the markdown reference.")
    parser.add_argument("--mode", default="Ionian", help="Mode name within the selected family.")
    parser.add_argument(
        "--key",
        default="Gb",
        help="Starting key. Uses the markdown spellings, so F# standard defaults to Gb for the scale selector.",
    )
    parser.add_argument("--frets", type=int, default=24, help="Number of frets to draw.")
    parser.add_argument(
        "--save",
        type=Path,
        help="Optional output image path. If set, the current diagram is saved instead of opening an interactive window.",
    )
    parser.add_argument(
        "--display",
        choices=[mode.lower() for mode in DISPLAY_MODES],
        default="notes",
        help="Initial display mode: notes, intervals, or chords.",
    )
    parser.add_argument(
        "--degree",
        type=int,
        default=1,
        help="Initial diatonic chord degree to inspect in chord view, from 1 to 7.",
    )
    parser.add_argument("--octaves", type=int, default=3, help="Number of piano octaves to draw.")
    parser.add_argument("--start-note", default="C2", help="Piano keyboard start note, like C2 or F1.")
    return parser


def prompt_for_instrument() -> str:
    while True:
        choice = input("Choose instrument ([g]uitar / [p]iano): ").strip().lower()
        if choice in {"g", "guitar"}:
            return "guitar"
        if choice in {"p", "piano"}:
            return "piano"
        print("Please enter 'guitar' or 'piano'.")


def main() -> None:
    args = build_arg_parser().parse_args()
    if args.save:
        plt.switch_backend("Agg")

    instrument = args.instrument or prompt_for_instrument()
    family_order, scales = parse_scale_reference(REFERENCE_PATH)
    family, mode, key = validate_selection(family_order, scales, args.family, args.mode, args.key)

    if instrument == "piano":
        viewer = PianoScaleViewer(
            family_order=family_order,
            scales=scales,
            octaves=max(1, args.octaves),
            start_note=args.start_note,
            start_family=family,
            start_mode=mode,
            start_key=key,
            start_display="Intervals" if args.display.title() == "Intervals" else "Notes",
        )
    else:
        viewer = FretboardScaleViewer(
            family_order=family_order,
            scales=scales,
            frets=args.frets,
            start_family=family,
            start_mode=mode,
            start_key=key,
            start_display=args.display.title(),
            start_degree=max(0, min(6, args.degree - 1)),
        )

    if args.save:
        viewer.fig.savefig(args.save, dpi=180, bbox_inches="tight")
        return

    plt.show()


if __name__ == "__main__":
    main()
