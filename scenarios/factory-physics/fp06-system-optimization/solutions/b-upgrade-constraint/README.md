# fp06 solution B — relieve the constraint (the system fix)

**The intervention:** replace the middle machine (2.0 s per craft, 30/min
— the constraint) with a mid-tier model (1.33 s, 45/min). The line's pace
moves to M1 at 37.5/min.

**Why one move fixes both requirements:** the supplier overflows because
the line can't *swallow* 36/min, and the customer starves because the line
can't *produce* 33/min — both symptoms of the same 30/min constraint.
Raise the constraint past both external rates and:

- intake ≥ 36/min → the warehouse stops overflowing → `supply_requirement`
  **passes**;
- output ≥ 33/min → deadlines are met → `service_requirement` **passes**;
- WIP settles at a moderate level (the preference value that now actually
  competes, this being the feasible run).

Contrast with solution A, which spent effort at the most visible symptom
and moved nothing the customer or the objective conjunction could see.
Note what was *not* needed: no buffer, no pull gate, no combinators — in a
deterministic world with one constraint, capacity at the constraint was
the whole answer. (Ask what changes when supply is 40/min: M1 caps at
37.5, and no machine swap fixes intake — then the buffer/loss trade
becomes real. That variant is the debrief's homework.)

The machine swap exercises dynamic entity-set membership (ADR 0016): the
report's per-machine table shows the old machine with empty eligibility
and the replacement eligible from boundary 0.

```sh
fisl solutions scenarios/factory-physics/fp06-system-optimization --run \
    --json course/data/lab-06-comparison.json
```
