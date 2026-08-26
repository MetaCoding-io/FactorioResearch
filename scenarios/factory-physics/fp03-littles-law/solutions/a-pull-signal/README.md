# fp03 solution A — pull signal (WIP control at admission)

**The intervention:** a red circuit wire from the source-side inserter to a
belt tile four tiles downstream; the belt reads its contents (hold mode);
the inserter is enabled only while that tile holds `rough workpiece < 1`.

**Why it works:** in the baseline, the source inserter admits work as fast
as it can swing, but the first machine consumes only one workpiece per 4 s —
so the entire input belt fills with queued work (~40+ units of WIP doing
nothing but waiting). The wire turns admission into a *pull*: a new
workpiece enters only when the previous one has moved on, so admissions pace
themselves to actual bottleneck consumption and the queue never forms.

**Predicted vs baseline** (baseline reference: run `01M0XP8VJ78KXRC8DB6BATBW39`,
avg WIP 51.70, throughput 15.00/min, CT 206.78 s):

- throughput: **unchanged** (~15/min — the bottleneck machine didn't change)
- average WIP: **single digits** (only work in transit + in machines)
- cycle time: **tens of seconds** (Little's Law: CT = WIP / TH)

Same output, a fraction of the inventory, a fraction of the flow time —
the core Factory Physics claim, produced by one wire.

**Run it:**

```sh
fisl run scenarios/factory-physics/fp03-littles-law --headless \
    --solution a-pull-signal
fisl compare runs/<baseline-run> runs/<solution-run>
```

The solution id and script hash are recorded in the run's provenance, so a
solution run is always distinguishable from a learner run.
