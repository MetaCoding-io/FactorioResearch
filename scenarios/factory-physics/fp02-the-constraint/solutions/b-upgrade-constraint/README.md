# fp02 solution B — upgrade the constraint

**The intervention:** the middle machine — the constraint, 2.0 s per
craft — is replaced with a mid-tier model (1.33 s per craft). Structurally
identical to solution A: same action, different target.

**What happens:** throughput rises until the *next* constraint binds — the
upstream machine at 1.6 s per craft caps the line at **37.5/min** (+25%).
The state signature migrates with the constraint: upstream blocked time
disappears, and both the upgraded machine and the downstream one now show
starved time as the upstream machine becomes the pacemaker.

Expected vs baseline (TH ~30/min):

- throughput: **+25%** (~37.5/min — the upstream machine's rate, not the
  upgraded machine's 45/min: the constraint *moved*, it didn't vanish)
- pre-constraint queue drains; WIP and cycle time **down**
- blocked-above/starved-below now points at the upstream machine

Two questions worth asking after both runs: why didn't throughput reach
the new machine's own rate? And what would you upgrade *next* — and when
would you stop?

```sh
fisl solutions scenarios/factory-physics/fp02-the-constraint --run \
    --json course/data/lab-02-comparison.json
```
