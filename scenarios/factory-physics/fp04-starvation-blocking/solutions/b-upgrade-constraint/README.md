# fp04 solution B — upgrade the constraint (throughput moves)

**The intervention:** the middle machine — the constraint, one workpiece
per 2.0 s — is replaced with an assembling-machine-3 (same inspect recipe,
0.8 s per craft).

**What happens:** throughput rises until the *next* constraint binds:
machine 1 at 1.6 s per craft caps the line at 37.5/min (up from 30/min,
+25%). The state signature moves with the constraint — machine 1's blocked
time vanishes (nothing downstream holds it back now), while the upgraded
machine 2 and machine 3 now show *starved* time because machine 1 can't
feed them at their new appetite. Blocked-above/starved-below points at
machine 1 now: the diagnosis method still works, the answer changed.

Expected vs baseline:

- throughput: **+25%** (~37.5/min, machine 1's rate)
- machine 1: blocked **→ ~0**, productive → ~100% (it *is* the constraint)
- machines 2 and 3: newly/more **starved** (paced by machine 1)
- the M1→M2 belt queue drains; the source-side queue remains (admission is
  still uncontrolled — that queue is Lab 3's lesson, not this one)

Contrast with solution A: the buffer made a machine look better and moved
no throughput; the upgrade moved throughput because it attacked the
constraint itself. Improvement anywhere but the constraint is an illusion
measured in local statistics.

**Dynamic membership note:** this solution runs before start and swaps a
measured machine. The destroyed assembling-machine-1 leaves the entity set
with empty eligibility; the replacement joins at boundary 0 (raise_built).
The pooled machine-time denominators stay honest through the swap —
exactly what ADR 0016 exists for.

```sh
fisl solutions scenarios/factory-physics/fp04-starvation-blocking --run \
    --json course/data/lab-04-comparison.json
```
