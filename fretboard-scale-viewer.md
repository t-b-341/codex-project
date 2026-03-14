# Fretboard Scale Viewer

Run the viewer with:

```powershell
python .\fretboard_scale_viewer.py
```

Useful options:

```powershell
python .\fretboard_scale_viewer.py --family "Melodic Minor" --mode "Altered" --key B
python .\fretboard_scale_viewer.py --frets 18
python .\fretboard_scale_viewer.py --save .\gb-ionian.png
```

Controls inside the Matplotlib window:

- `Prev/Next Family` cycles the scale families.
- `Prev/Next Mode` cycles the modes inside the current family.
- `Prev/Next Key` cycles the 12 keys in the markdown reference.
- Arrow keys change key and mode.
- `[` and `]` switch scale families.

The viewer uses 8-string F# standard tuning: `F# B E A D G B E`.
