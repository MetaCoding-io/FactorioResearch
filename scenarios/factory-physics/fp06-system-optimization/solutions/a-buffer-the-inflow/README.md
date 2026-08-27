# fp06 solution A — buffer the inflow (the seductive partial fix)

**The intervention:** Lab 4's inline chest splice, upstream of the
constraint. It targets the loudest symptom: the supplier's deliveries
overflowing the finite warehouse and being lost.

**What it fixes:** supply loss. With M1 unblocked, the line's intake
(37.5/min) keeps up with the 36/min schedule, the warehouse stops
overflowing, and the `supply_requirement` **passes**.

**What it doesn't:** the customer. The constraint still produces 30/min
against 33/min of demand, so the `service_requirement` still **fails** —
and everything rescued from the supplier's scrap heap now accumulates in
the chest, so WIP grows for the entire run. `fisl compare` marks this run
**INFEASIBLE**: its (large!) WIP value is displayed but does not compete.

The capstone lesson in one run: fixing the symptom you can see, at the
place you can see it, moved material from one loss column to an inventory
column and left the customer exactly as unserved as before.

```sh
fisl solutions scenarios/factory-physics/fp06-system-optimization --run \
    --json course/data/lab-06-comparison.json
```
