# Scale Instrument Viewers

This project contains a single Python visualizer that can launch either an 8-string guitar view or a piano view.

Both viewers read scale and mode definitions from `scale-modes-reference.md`, render them with Matplotlib, and let you click through keys, modes, and scale families.

## What It Does

- Draws an 8-string fretboard in `F# B E A D G B E` tuning.
- Draws a piano keyboard across a configurable note range.
- Highlights scale tones across the neck.
- Highlights scale tones across the keyboard.
- Shows root notes in red and other active tones in teal.
- Supports three display modes:
  - `Notes`: note names on the fretboard
  - `Intervals`: interval formulas relative to the selected scale root
  - `Chords`: diatonic chord tones for the selected scale degree
- Supports two piano display modes:
  - `Notes`: note names on the keyboard
  - `Intervals`: interval formulas relative to the selected scale root
- Includes a chord panel for `I`, `II`, `III`, and the other diatonic triads, with generated compact chord-shape positions.
- Highlights open strings that belong to the active scale or chord.

## Files

- `fretboard_scale_viewer.py`: the main interactive viewer for both guitar and piano
- `scale-modes-reference.md`: the scale and mode source data
- `fretboard-scale-viewer.md`: short usage notes

## Requirements

- Python 3.10+
- `matplotlib`

Install Matplotlib if needed:

```powershell
pip install matplotlib
```

## How To Run

Start the interactive viewer:

```powershell
python .\fretboard_scale_viewer.py
```

When it starts, it asks:

```powershell
Choose instrument ([g]uitar / [p]iano):
```

You can also skip the prompt:

```powershell
python .\fretboard_scale_viewer.py --instrument guitar
python .\fretboard_scale_viewer.py --instrument piano
```

Open directly in interval mode:

```powershell
python .\fretboard_scale_viewer.py --display intervals
```

Open in chord mode on a specific diatonic degree:

```powershell
python .\fretboard_scale_viewer.py --display chords --degree 5
```

Save the current diagram to an image instead of opening a window:

```powershell
python .\fretboard_scale_viewer.py --save .\fretboard.png
```

Save the piano view:

```powershell
python .\fretboard_scale_viewer.py --instrument piano --display intervals --octaves 4 --save .\piano.png
```

## Command-Line Options

- `--family`: starting scale family, such as `Major Scale`
- `--mode`: starting mode, such as `Ionian`
- `--key`: starting key, using the spellings from `scale-modes-reference.md`
- `--frets`: number of frets to draw
- `--display`: `notes`, `intervals`, or `chords`
- `--degree`: starting diatonic chord degree from `1` to `7`
- `--save`: output image path for non-interactive export

- `--family`: starting scale family
- `--mode`: starting mode
- `--key`: starting key
- `--instrument`: `guitar` or `piano`
- `--octaves`: number of octaves to draw
- `--start-note`: first keyboard note, like `C2`
- `--display`: `notes` or `intervals`
- `--save`: output image path for non-interactive export

## Controls

Buttons:

- `Prev/Next Family`
- `Prev/Next Mode`
- `Prev/Next Key`
- `Prev/Next View`
- `Prev/Next Chord`

Keyboard:

- Left / Right arrows: change key
- Up / Down arrows: change mode
- `[` and `]`: change scale family
- `n`: notes view
- `i`: intervals view
- `c`: chords view
- `,` and `.`: move through diatonic chord degrees

Piano keyboard controls:

- Left / Right arrows: change key
- Up / Down arrows: change mode
- `[` and `]`: change scale family
- `n`: notes view
- `i`: intervals view

## How It Works

The viewer parses the markdown reference file into a structured scale dictionary. From there it:

1. Converts note spellings into pitch classes.
2. Map each scale tone across the target instrument layout.
3. Draw the instrument and note markers with Matplotlib.
4. Build interval labels from the selected scale root.
5. Derive diatonic triads for the guitar chord viewer.
6. Generate compact chord positions for the guitar chord panel.

## Current Limitations

- The chord diagrams currently focus on compact 3-string triad voicings, not every possible full chord voicing across all 8 strings.
- The project depends on a working Matplotlib GUI backend for the interactive window.
- Some keys in the reference use flat spellings like `Gb` rather than `F#`, because the viewer follows the markdown source data.
- The piano viewer currently focuses on scale visualization and intervals, not chord voicing generation.

## Future Ideas

- Add 7th chords and extended chord views
- Add filters for string sets or fret ranges
- Add alternative tunings
- Export SVG or PDF diagrams
- Add a web-based version with richer interaction
