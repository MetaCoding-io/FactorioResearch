# fp07 solution w-04 — CONWIP cap at W < 4

One gate, four cap levels (w-04/w-08/w-14/w-24): the sweep that traces
the line's characteristic curves. This point sits far below the knee.

**First-order prediction:** TH ~ w/T0 ~ 4.3/min at CT ~ T0 ~ 56 s: an inventory-starved line, every machine mostly starved, but every workpiece flying through. The measured point lands at or below
the best-case bound — belt discreteness and inserter timing are real
mechanisms, and the honest x-coordinate is the *measured* average WIP,
not the nominal cap.

**Measured** (reference dataset): avg WIP 4.02, TH 5.60/min, CT 43.02 s (= the direct T0 measurement; the walk-estimate said ~56 s and was wrong), pooled productive 24.6%.

**The mechanism** (all three steps checked and loud): two tap belts read
admissions and completions as pulses, two arithmetic combinators sign
them into `signal-W`, a self-looped decider accumulates the running
difference — the conservation ledger, rebuilt in circuits — and a relay
chain carries the sink's pulses home along the line's own belts. The
report's census will agree with your wire.

```sh
fisl solutions scenarios/factory-physics/fp07-characteristic-curves --run \
    --json course/data/lab-07-comparison.json
```
