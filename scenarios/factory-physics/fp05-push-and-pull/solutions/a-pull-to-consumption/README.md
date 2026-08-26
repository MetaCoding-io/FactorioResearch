# fp05 solution A — pull to consumption (serve the customer, drop the WIP)

**The intervention:** Lab 3's proven pull gate, unchanged: red wire from
the source inserter (relayed — wire reach) to the last belt tile before
machine 1, gate reads contents (hold), admission enabled while
`rough workpiece < 2`.

**Why it's interesting under demand:** the gate paces admission to the
*bottleneck's consumption* (15/min), which still exceeds customer demand
(12/min). So the customer notices nothing — on-time rate and waits match
the push baseline — while the factory carries a fraction of the
inventory. WIP control and service are not opposites while capacity covers
demand; push's extra inventory was buying literally nothing here.

Expected vs the push baseline:

- on-time item rate: **unchanged** (capacity > demand either way)
- p95 customer wait: **unchanged / similar**
- average WIP and cycle time: **way down** (Lab 3's result, now with a
  customer watching)
- admission rate: down from "as fast as the inserter swings" to ~15/min

Contrast with solution B before concluding pull is free: B pulls
*too hard* and the customer pays for it.

```sh
fisl solutions scenarios/factory-physics/fp05-push-and-pull --run \
    --json course/data/lab-05-comparison.json
```
