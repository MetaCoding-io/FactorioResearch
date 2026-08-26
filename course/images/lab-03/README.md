# Lab 3 screenshots — capture list

The chapter references these files (as `.jpg` — see the conversion step):

| Filename | What to capture | When |
|---|---|---|
| `fisl-panel-ready.jpg` | The FISL panel showing READY + Start Experiment, learner standing at spawn near the toolbox | before pressing Start |
| `run1-jammed-belt.jpg` | The input belt packed solid with rough workpieces, Alt overlay on, source chest visible at left | run 1, a few minutes in |
| `run2-pull-gate.jpg` | The red wire from the source inserter to the gate belt tile near machine 1, with the mostly-empty belt between | run 2 (or after applying the intervention pre-start) |

**Preferred: automated capture.** `fisl snap
scenarios/factory-physics/fp03-littles-law` drives all three shots — you
only connect the client when prompted; framing/zoom/overlays are scripted.
PNGs land on your client under `script-output/fisl-snap/` as
`fisl-panel-ready.png`, `run1-jammed-belt.png`, and `run2-pull-gate.png`.
Game screenshots are always PNG (~5 MB at 1080p), so convert before
committing to keep the site light:

```sh
python3 -c "
from PIL import Image
for n in ['fisl-panel-ready','run1-jammed-belt','run2-pull-gate']:
    Image.open(f'{n}.png').convert('RGB').save(f'{n}.jpg', quality=88, optimize=True)
"
```

**Manual fallback:** run windowed (`--window-size 1680x950`), hold **Alt**
for the info overlay, zoom so the subject fills the frame; plain OS
screenshots, cropped, under ~1 MB each.

The comparison figure is **not** a screenshot: generate
`course/data/lab-03-comparison.svg` with
`fisl solutions scenarios/factory-physics/fp03-littles-law --run
--json course/data/lab-03-comparison.json
--svg course/data/lab-03-comparison.svg`.
