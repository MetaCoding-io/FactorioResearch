# fp04 solution A — buffer before the constraint (decoupling, not throughput)

**The intervention:** three belt tiles just upstream of the middle machine
are replaced with `inserter → wooden chest → inserter`, inline on the belt
row. The chest is a buffer: it absorbs the surplus that machine 1 produces
faster than machine 2 can consume (0.625/s vs 0.5/s).

**What it buys — and what it doesn't.** Before the buffer, machine 1 spends
a steady share of its time **blocked**: its output backs up the short belt
into its output slot. With the chest absorbing the surplus, machine 1 runs
nearly 100% productive. But the system constraint is unchanged — machine 2
still processes one workpiece per 2 s — so **throughput does not move**.
The surplus has to live somewhere, and now it lives in the chest: WIP grows
for the entire run (a wooden chest holds 1,600 workpieces; the rate
mismatch fills it at ~0.125/s, so it never fills within the experiment).

Measured (run `01M0YJ0RNJCQZ7ZRSXVC75J1VR` vs baseline
`01M0YHYH9TAVJP0SK6F60XX8W9`, TH 30.00/min / avg WIP 57.54 / CT 115.08 s):

- throughput: **30.00/min, +0.0%** — machine 2's rate, untouched
- average WIP: **91.16 (+58.4%)** and still growing at run end (final WIP
  122 vs the baseline's steady 58 — the linear-growth signature of a
  buffer absorbing a permanent rate mismatch)
- cycle time: **182.31 s (+58.4%)**
- machine 1 blocked fraction: **→ ~0**; its productive fraction **rises**;
  machine 3's starved fraction unchanged (still paced by machine 2)

That is the lesson stated by the lab: a buffer buys *decoupling* — machine 1
stops feeling machine 2's pace — and the price is inventory, paid in flow
time at Little's Law rates. Local productive time went up; the system got
strictly slower per workpiece. In a deterministic world this buffer buys
nothing else. (Hold that thought for the variability course, where buffers
earn their keep.)

Authoritative numbers come from running it:

```sh
fisl solutions scenarios/factory-physics/fp04-starvation-blocking --run \
    --json course/data/lab-04-comparison.json
```
