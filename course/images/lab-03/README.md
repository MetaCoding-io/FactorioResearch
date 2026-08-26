# Lab 3 screenshots — capture list

Drop PNGs here with these exact filenames, then uncomment the matching
`![...]` figure blocks in `course/labs/lab-03-littles-law.qmd`.

| Filename | What to capture | When |
|---|---|---|
| `fisl-panel-ready.png` | The FISL panel showing READY + Start Experiment, learner standing at spawn near the toolbox | before pressing Start |
| `run1-jammed-belt.png` | The input belt packed solid with rough workpieces, Alt overlay on, source chest visible at left | run 1, a few minutes in |
| `run2-pull-gate.png` | The red wire from the source inserter to the gate belt tile near machine 1, with the mostly-empty belt between | run 2 (or after applying the intervention pre-start) |

**Preferred: automated capture.** `fisl snap
scenarios/factory-physics/fp03-littles-law` drives all three shots — you
only connect the client when prompted; framing/zoom/overlays are scripted.
PNGs land on your client under `script-output/fisl-snap/` with the correct
filenames; copy them here.

**Manual fallback:** run windowed (`--window-size 1680x950`), hold **Alt**
for the info overlay, zoom so the subject fills the frame; plain OS
screenshots, cropped, under ~1 MB each.

The comparison figure is **not** a screenshot: generate
`course/data/lab-03-comparison.svg` with
`fisl solutions scenarios/factory-physics/fp03-littles-law --run
--json course/data/lab-03-comparison.json
--svg course/data/lab-03-comparison.svg`.
