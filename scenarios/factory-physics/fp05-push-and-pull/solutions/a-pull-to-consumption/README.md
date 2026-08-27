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

Measured (run `01M0Z6B1JESS0T4Q0N9WPHDPYG` vs push baseline
`01M0Z68MAR07HYK6ADFF8MTTVV`):

- on-time item rate: **100.0%, unchanged**; p95 wait **3.02 s, identical**
  to push — the customer cannot tell the difference
- average WIP: **19.16 (−62.9%)**; cycle time **76.64 s (−62.9%)** —
  bit-identical to fp03's pulled run (same gate, same world)
- admission rate: **14.30/min** (the gate's staging allowance trims it
  slightly below the bottleneck's 15/min; throughput still 15.00/min while
  the warmup queue drains)

Contrast with solution B before concluding pull is free: B pulls
*too hard* and the customer pays for it.

```sh
fisl solutions scenarios/factory-physics/fp05-push-and-pull --run \
    --json course/data/lab-05-comparison.json
```
