# 8-String Scale Fretboard Viewer

This project is a standalone Python fretboard visualizer for 8-string guitar in F# standard.

It reads scale and mode definitions from `scale-modes-reference.md`, renders them on a guitar fretboard with Matplotlib, and lets you click through keys, modes, and scale families.

## What It Does

- Draws an 8-string fretboard in `F# B E A D G B E` tuning.
- Highlights scale tones across the neck.
- Shows root notes in red and other active tones in teal.
- Supports three display modes:
  - `Notes`: note names on the fretboard
  - `Intervals`: interval formulas relative to the selected scale root
  - `Chords`: diatonic chord tones for the selected scale degree
- Includes a chord panel for `I`, `II`, `III`, and the other diatonic triads, with generated compact chord-shape positions.
- Highlights open strings that belong to the active scale or chord.

## Files

- `fretboard_scale_viewer.py`: the main interactive viewer
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

## Command-Line Options

- `--family`: starting scale family, such as `Major Scale`
- `--mode`: starting mode, such as `Ionian`
- `--key`: starting key, using the spellings from `scale-modes-reference.md`
- `--frets`: number of frets to draw
- `--display`: `notes`, `intervals`, or `chords`
- `--degree`: starting diatonic chord degree from `1` to `7`
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

## How It Works

The script parses the markdown reference file into a structured scale dictionary. From there it:

1. Converts note spellings into pitch classes.
2. Maps each scale tone across the fretboard for the chosen tuning.
3. Draws the fretboard and note markers with Matplotlib.
4. Builds interval labels from the selected scale root.
5. Derives diatonic triads for the selected scale.
6. Generates compact chord positions for the chord viewer panel.

## Current Limitations

- The chord diagrams currently focus on compact 3-string triad voicings, not every possible full chord voicing across all 8 strings.
- The project depends on a working Matplotlib GUI backend for the interactive window.
- Some keys in the reference use flat spellings like `Gb` rather than `F#`, because the viewer follows the markdown source data.

## Future Ideas

- Add 7th chords and extended chord views
- Add filters for string sets or fret ranges
- Add alternative tunings
- Export SVG or PDF diagrams
- Add a web-based version with richer interaction
