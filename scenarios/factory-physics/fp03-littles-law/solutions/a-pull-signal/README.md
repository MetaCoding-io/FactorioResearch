# fp03 solution A — pull signal (WIP control at admission)

**The intervention:** a red circuit wire from the source-side inserter to
the **last belt tile before machine 1's input pickup**; the belt reads its
contents (hold mode); the inserter is enabled only while that tile holds
`rough workpiece < 2`.

**Why it works:** in the baseline, the source inserter admits work as fast
as it can swing while the bottleneck consumes one workpiece per 4 s, so the
whole input belt fills with queued work. The wire turns admission into a
*pull*: a new workpiece may enter only while fewer than two are staged at
the machine — admissions pace themselves to actual consumption, and the
queue never forms. The `< 2` staging allowance covers the ~4.8 s belt
transit from the source so the bottleneck never starves.

**Gate placement is the lesson.** Version 1 of this solution monitored a
tile near the *source* and cut WIP by only ~19% (avg WIP 41.66, CT 166.65 s,
run `01M0Y063ACYSD8JWRF78EJAWTF`): the gate stopped the queue growing
upstream of the monitored tile, but every tile *between the gate and the
machine* still packed solid. A pull signal must watch the point where the
queue actually forms — immediately upstream of the constraint.

**The floor is transport, not zero.** This line is ~90 tiles long; at belt
speed that is ~48 s of pure transit, so even a perfect pull system carries
`TH × transit ≈ 0.25/s × 48 s ≈ 12–14` workpieces of *in-transit* WIP.
Conveyors are inventory. Expected result vs baseline (avg WIP 51.70,
TH 15.00/min, CT 206.78 s):

- throughput: **unchanged** (~15/min)
- average WIP: **~16–19** (transit floor + staging + machine internals)
- cycle time: **~65–75 s** (Little's Law: CT = WIP / TH)

Authoritative numbers come from running it, not from this prose:

```sh
fisl solutions scenarios/factory-physics/fp03-littles-law --run \
    --json course/data/lab-03-comparison.json
```

The solution id and script hash are recorded in the run's provenance, so a
solution run is always distinguishable from a learner run.
