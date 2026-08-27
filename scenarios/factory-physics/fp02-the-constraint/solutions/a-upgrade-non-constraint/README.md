# fp02 solution A — upgrade a non-constraint (the futile upgrade)

**The intervention:** the downstream fast machine (1.33 s per craft) is
replaced with the fastest available model (0.8 s per craft). A genuine,
expensive-feeling capacity upgrade.

**What happens:** nothing, at the system level. The middle machine still
processes one workpiece per 2.0 s, so completion throughput stays at its
rate. The upgraded machine finishes each workpiece faster and then waits
longer — its starved fraction *rises*. Every other number is unchanged.

Measured (run `01M0Z644ZYFBWHBFR8TCC5YVHN` vs baseline
`01M0Z61XH0VQ2JNKQRDP0426P4`, TH 30.00/min / avg WIP 57.54):

- throughput: **30.00/min, +0.0%**
- pooled starved fraction: **+80.8%** (11.3% -> 20.5%) — faster appetite,
  same diet; pooled productive *fell* to 73.4%
- WIP: **−0.5%** (unchanged); every customer-visible number flat

This is the Theory-of-Constraints lesson in its purest measurable form:
an improvement anywhere but the constraint is invisible to the customer.
Compare with solution B — the *same class of action* at a different
machine — before drawing conclusions about "upgrades" in general.

```sh
fisl solutions scenarios/factory-physics/fp02-the-constraint --run \
    --json course/data/lab-02-comparison.json
```
