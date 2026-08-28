# fp07 solution w-14 — CONWIP cap at W < 14

One gate, four cap levels (w-04/w-08/w-14/w-24): the sweep that traces
the line's characteristic curves. This point sits at the predicted critical WIP (W0 = rb x T0 = 0.25/s x ~56 s).

**First-order prediction:** the knee: TH reaching ~15/min for the first time, CT still near its floor. The measured point lands at or below
the best-case bound — belt discreteness and inserter timing are real
mechanisms, and the honest x-coordinate is the *measured* average WIP,
not the nominal cap.

**Measured** (reference dataset): avg WIP 14.04, TH 15.00/min, CT 56.17 s — already on the flat branch (measured T0 = 43.02 s puts W0 at 10.8, not the estimated 14).

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
