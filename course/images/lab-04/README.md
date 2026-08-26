# Lab 4 screenshots — capture list

The chapter has no figure blocks yet; add them once these exist (as
`.jpg` — see the conversion step below).

| Filename | What to capture | When |
|---|---|---|
| `lab4-line-overview.jpg` | The whole compact line: three visibly different machines, ports at both ends | READY, before Start |
| `lab4-blocked-starved.jpg` | M1's output belt packed solid while M3's input belt runs empty, Alt overlay on | baseline run, ~6 min in |
| `lab4-buffer-chest.jpg` | Solution A's inline inserter → chest → inserter splice, chest filling | solution A run, ~6 min in |

**Preferred: automated capture.** `fisl snap
scenarios/factory-physics/fp04-starvation-blocking` drives all three shots —
you only connect the client when prompted. PNGs land on your client under
`script-output/fisl-snap/` as `lab4-line-overview.png`,
`lab4-blocked-starved.png`, and `lab4-buffer-chest.png`. Game screenshots
are always PNG (~5 MB at 1080p), so convert before committing:

```sh
python3 -c "
from PIL import Image
for n in ['lab4-line-overview','lab4-blocked-starved','lab4-buffer-chest']:
    Image.open(f'{n}.png').convert('RGB').save(f'{n}.jpg', quality=88, optimize=True)
"
```

The comparison figure is **not** a screenshot: generate
`course/data/lab-04-comparison.svg` with
`fisl solutions scenarios/factory-physics/fp04-starvation-blocking --run
--json course/data/lab-04-comparison.json
--svg course/data/lab-04-comparison.svg`.
