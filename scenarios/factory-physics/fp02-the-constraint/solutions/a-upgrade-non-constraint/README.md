# fp02 solution A — upgrade a non-constraint (the futile upgrade)

**The intervention:** the downstream fast machine (1.33 s per craft) is
replaced with the fastest available model (0.8 s per craft). A genuine,
expensive-feeling capacity upgrade.

**What happens:** nothing, at the system level. The middle machine still
processes one workpiece per 2.0 s, so completion throughput stays at its
rate. The upgraded machine finishes each workpiece faster and then waits
longer — its starved fraction *rises*. Every other number is unchanged.

Expected vs baseline (TH ~30/min):

- throughput: **unchanged**
- upgraded machine: starved fraction **up** (faster appetite, same diet)
- WIP, cycle time: **unchanged**

This is the Theory-of-Constraints lesson in its purest measurable form:
an improvement anywhere but the constraint is invisible to the customer.
Compare with solution B — the *same class of action* at a different
machine — before drawing conclusions about "upgrades" in general.

```sh
fisl solutions scenarios/factory-physics/fp02-the-constraint --run \
    --json course/data/lab-02-comparison.json
```
