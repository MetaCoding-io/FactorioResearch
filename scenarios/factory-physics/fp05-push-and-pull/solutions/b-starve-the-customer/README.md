# fp05 solution B — the over-tight pull (deliberately wrong)

**The intervention:** a combinator clock throttles admission to ~10
workpieces/min — below the 12/min customer demand. One constant
combinator, one self-looped decider (a 6-second clock), and an enable
window on the source inserter shorter than one inserter swing: exactly one
admission per cycle, deterministic.

**What it demonstrates** (measured, run `01M0Z6DF3N10M8DMR7ZDZNMS5E`):
the smallest WIP number of any run in this course — average WIP **7.33**,
admission exactly **10.00/min** — and a customer catastrophe: on-time
**22.5%**, p95 wait **censored**. The 22.5% is derivable: backlog grows at
2/min while service runs at 10/min, so waits pass 30 s once backlog
exceeds 5 — about 2.5 minutes into the 10-minute window.

- backlog grows ~2/min for the whole measured phase and never recovers;
- the on-time item rate collapses: every deadline missed is *fixed* — the
  cohort accounting never lets later deliveries rewrite history
  (ADR 0008 §11);
- the p95 wait comes back **censored**, not as a number: demand that was
  never served within the observation horizon has no measurable wait, and
  FISL reports that honestly instead of guessing (§10).

This run exists to be compared against A: both are "pull", both have low
WIP, and only one of them is a factory. **Low WIP is not success if the
customer is not served.** WIP targets, throughput targets, and service
targets are three different dials; this lab's objective form — a service
*requirement* plus a WIP *preference* — exists precisely so this run reads
as the failure it is.

Mechanics note: this is the first scripted use of Factorio 2.0's
combinator control behaviors (constant-combinator logistic sections,
decider conditions/outputs). The script fails loudly on any rejected
parameter or unconnected wire — no silent fallbacks (fp03 v2's lesson).

```sh
fisl solutions scenarios/factory-physics/fp05-push-and-pull --run \
    --json course/data/lab-05-comparison.json
```
