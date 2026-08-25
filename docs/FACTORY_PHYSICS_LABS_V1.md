# Factory Physics Labs 0–6 — V1 Contract Validation

**Status:** V1 scenario/acceptance specification  
**Purpose:** Prove that the accepted FISL contract can express the first course without lab-specific runtime hacks.

The exact Factorio layouts, instructional prose, and tuned numeric parameters will evolve during implementation. The scientific structure below is the acceptance target for the platform.

A core implementation rule follows from this document:

> **No Lab 0–6 behavior should require special-case code keyed on a lab ID.**

Every lab should be implemented using the generic `fisl/v1` scenario, port, flow, metric, objective, visibility, and observation mechanisms.

---

## 1. Course progression

| Lab | Primary concept | New FISL capability exercised |
|---|---|---|
| 0 | Measuring the Factory | zones, ports, observations, explicit metric definitions |
| 1 | Flow & Capacity | throughput, input/output rates, production resource sets |
| 2 | The Constraint | machine-state diagnostics, local vs system rate |
| 3 | WIP & Little's Law | conserved work unit, WIP integration, derived cycle time |
| 4 | Starvation & Blocking | state classification, buffers, pooled machine-time |
| 5 | Push & Pull | demand cohorts, service constraint, WIP/service trade-off |
| 6 | System Optimization | objectives, upstream congestion/loss, dynamic redesign, comparative debrief |

---

# Lab 0 — Measuring the Factory

## Learning purpose

The learner should experience that a production metric is meaningless until the system boundary, unit, and time window are declared.

Questions:

- What counts as inside the factory?
- What is a stock versus a flow?
- Where exactly do inputs enter and outputs leave?
- Why is a current inventory value different from a throughput rate?

## Baseline world

A small deterministic workpiece line using normal Factorio handling and a simple FISL conserved workpiece family.

```text
FISL source -> transport -> simple process -> transport -> FISL sink
```

The layout should be deliberately easy to understand; the challenge is measurement, not optimization.

## Scenario contract

Required:

```text
1 primary rectangular system zone
1 source port
1 completion sink
1 conserved workpiece flow
explicit warmup + measured phases
```

Metrics:

```text
current WIP
input count/rate
output count/throughput
average WIP
```

Optional physical inventory vector should demonstrate that physical inventory and scalar WIP are different concepts.

## Visibility

Learner may see current WIP and a live trailing output rate.

Post-run should expose exact metric definitions/window/provenance.

## Objective

No optimization objective is required. The lab can be completion/debrief-oriented.

## E2E platform acceptance

The implementation test must be able to:

1. launch a known baseline;
2. bind source/sink;
3. run a fixed-duration experiment;
4. record exact source withdrawals and sink deliveries;
5. calculate point/average WIP;
6. show that closing state is distinct from time occupancy;
7. emit a reproducible run dataset.

No lab-specific runtime code is permitted.

---

# Lab 1 — Flow & Capacity

## Learning purpose

The learner encounters rates, serial process capacity, and the difference between installed local capacity and achieved system output.

## Baseline world

A serial line with at least two production stages with deliberately different nominal capacities.

Supply should normally use `replenish` so upstream material availability does not accidentally become the lesson.

A pure completion sink is sufficient; customer demand is not required yet.

## Metrics

```text
system throughput
admission/input rate
selected machine productive fraction
optional stage/local output diagnostics
```

The authoritative system throughput remains completion-sink delivery, not craft count.

## Objective

A preference may ask learners to maximize measured throughput.

No single numeric score is required.

## E2E platform acceptance

A deterministic fixture must establish that:

- system throughput is bounded by the known limiting stage;
- adding upstream inventory does not magically exceed the bottleneck;
- input rate may differ from completion throughput while WIP changes;
- output is measured at the completion boundary rather than from Factorio production statistics.

---

# Lab 2 — The Constraint

## Learning purpose

The learner experiences the Theory-of-Constraints/local-optimization problem before formal vocabulary is introduced.

A deliberately unbalanced line should make upgrades to non-constraints produce little/no system-throughput improvement, while improving the true constraint does.

## Baseline world

At least three serial production stages:

```text
A (fast) -> B (slow) -> C (fast)
```

with sufficient material supply and a clean completion sink.

## Metrics

```text
system throughput
WIP / queue inventory by relevant region where useful
per-machine productive/starved/blocked classification
pooled machine-state summaries
```

## Visibility

Recommended:

```text
learner live: system throughput, current WIP
learner post-run: detailed machine-state distribution
```

The detailed diagnostic should initially be withheld so the lab does not simply point at the bottleneck.

## Objective

Preference:

```text
maximize measured throughput
```

Potential secondary preference/diagnostic:

```text
avoid unnecessary WIP growth
```

but no hidden weighted score.

## E2E platform acceptance

Known baseline variants should verify:

1. improving stage A alone does not materially change completion throughput when B remains limiting;
2. improving stage B increases system throughput until another constraint becomes active;
3. state classification explains the resulting starvation/blocking pattern;
4. learner disclosure can hide that diagnosis live while still collecting it.

---

# Lab 3 — WIP and Little's Law

## Learning purpose

Teach:

```text
WIP = TH × CT
```

and make the learner distinguish processing time from total elapsed residence time.

This is the canonical justification for purpose-built conserved workpiece families.

## Baseline world

Use deterministic one-for-one stage transformations:

```text
rough-workpiece
  -> machined-workpiece
  -> inspected-workpiece
  -> finished-workpiece
```

Each physical identity represents exactly one conserved `workpiece` flow unit.

The line should support controlled changes to buffers/release rate while remaining easy to bring into stable flow.

## Experiment phases

Recommended:

```text
warmup
measured
```

The measured phase should be long enough for a stable-flow interpretation and record opening/closing WIP diagnostics.

An optional separate probe scenario/phase may send one isolated workpiece through the line to contrast unloaded direct residence time with loaded Little's-Law-derived cycle time.

## Metrics

```text
point WIP
WIP workpiece-ticks
average WIP
completion throughput
Little's-Law-derived cycle time
opening/closing WIP
flow balance error
optional direct single-work-unit probe time
```

## Objective

No optimization is necessary; the primary task is explanation/comparison.

## E2E platform acceptance

The platform must prove:

1. one admitted workpiece remains WIP=1 through every supported holder state until sink delivery;
2. active craft and inserter/belt states do not create disappearance/double-counting;
3. average WIP uses exact tick-weighted integration;
4. cycle time uses `average_wip / throughput` with matching flow/window;
5. the result is labeled `little_law_derived`, not direct item tracking;
6. an isolated probe can produce a separately labeled direct result.

---

# Lab 4 — Starvation and Blocking

## Learning purpose

Make queueing, buffers, decoupling, starvation, and downstream backpressure visible.

The learner should see that buffers can reduce local coupling while increasing WIP, and that local productive time is not itself the system objective.

## Baseline world

A multi-stage line with intentionally small/intermediate buffers that can be resized or redesigned using normal Factorio chests/belts.

## Metrics

Per machine/entity set:

```text
productive machine-ticks
starved machine-ticks
blocked machine-ticks
unavailable/disabled/idle-other ticks
```

Aggregate:

```text
pooled productive fraction
pooled starved fraction
pooled blocked fraction
average/peak WIP
throughput
```

No bare `utilization` metric.

## Visibility

Learner live may see throughput/current WIP.

Detailed state distribution can be post-run or instructor-visible depending on exercise variant.

## Objective

Comparison-oriented rather than one-dimensional optimization.

A scenario may require maintaining a minimum throughput while asking learners to compare buffer/WIP consequences.

## E2E platform acceptance

Dedicated fixtures must force and validate:

```text
normal progress -> productive
missing process input -> starved
full output/downstream capacity -> blocked
no power -> unavailable
circuit disable -> disabled
```

The main lab must demonstrate that changing buffers alters starvation/blocking/WIP without redefining the classifier.

---

# Lab 5 — Push and Pull

## Learning purpose

Make demand signaling and WIP control concrete.

The learner must maintain customer service while comparing push-style overproduction with pull/WIP-limited control.

The critical lesson is:

> Low WIP is not success if the customer is not served.

## Baseline world

A production line capable of meeting deterministic customer demand when configured competently.

Use native Factorio circuit/control mechanics where possible for learner-built pull/Kanban logic.

FISL supplies the external demand process and measurement apparatus rather than replacing the control system.

## Experiment phases

Recommended:

```text
warmup
measured
service_tail
```

Demand is active during the measured cohort window and disabled during `service_tail`, allowing final deadlines to resolve.

## Port/demand model

```text
source: replenish or sufficiently unconstrained scheduled input
completion sink + FIFO backlog demand
explicit max customer wait
```

## Metrics

```text
on-time item rate
current/peak/average customer backlog
customer backlog work-unit-ticks
average/peak/p95 WIP
throughput
machine-state distribution
Little's-Law-derived cycle time where appropriate
```

## Objectives

Canonical:

```text
Requirement: on-time item rate >= 95% within declared max wait
Preference:  minimize average WIP
```

This is the reference demonstration of requirements + preferences.

## Visibility

Recommended live:

```text
current WIP
trailing throughput
service requirement target/status if pedagogically desired
```

Detailed machine-state and wait distributions post-run.

## E2E platform acceptance

The platform must support two run variants from the same baseline:

- a push-oriented configuration that can achieve service but accumulates more WIP;
- a pull/WIP-controlled configuration capable of meeting the same service requirement with lower WIP after scenario tuning.

The acceptance criterion for the software is the ability to measure/evaluate the comparison correctly; exact tuned numeric values are scenario-content calibration work.

---

# Lab 6 — System Optimization

## Learning purpose

Capstone the deterministic course by forcing the learner to optimize the **system** rather than any one local metric.

The lab should combine:

- production capacity;
- WIP;
- customer service;
- starvation/blocking;
- possibly constrained inbound supply/warehouse capacity;
- dynamic factory redesign.

## Baseline world

A more complex but still deterministic factory with multiple opportunities for local optimization traps.

At least one scenario variant SHOULD use scheduled source supply with finite or zero external storage so upstream congestion/loss becomes visible.

## Metrics

Potential v1 set:

```text
customer on-time item rate
throughput
average/peak WIP
upstream external pending average/peak/item-ticks
supply lost quantity/fraction
machine-state pooled distributions
cycle time
```

## Objectives

Example:

```text
Requirements:
  service >= 95%
  supply loss <= scenario threshold

Preferences:
  minimize average WIP
  optionally maximize throughput when not redundant with fixed demand/service
```

Multiple preferences remain a vector; no hidden scalar score.

## Dynamic redesign requirement

Learners may add/remove production machines.

`line_machines` and similar entity sets MUST update dynamically, with new resources contributing machine-time only for their eligibility intervals under ADR 0016.

## E2E platform acceptance

The capstone regression scenario must prove that:

1. newly built matching machines join the analytical set;
2. removed machines stop contributing future denominator time;
3. system metrics remain tied to fixed ports/flow boundaries during redesign;
4. finite/zero external supply storage produces measurable upstream backlog/loss according to policy;
5. requirements/preferences evaluate without a weighted score;
6. comparison reports preserve whether runs used compatible experimental conditions.

---

# Cross-lab contract coverage

| Contract capability | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---:|---:|---:|---:|---:|---:|---:|
| phases/tick clock | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| zones/system boundary | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| source/sink ports | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| conserved flow | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| WIP | ✓ | optional | optional | ✓ | ✓ | ✓ | ✓ |
| throughput | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| machine state | optional | ✓ | ✓ | optional | ✓ | ✓ | ✓ |
| service cohorts | — | — | — | — | — | ✓ | ✓ |
| cycle time | — | — | — | ✓ | optional | ✓ | ✓ |
| aggregation/windows | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| visibility | ✓ | optional | ✓ | ✓ | ✓ | ✓ | ✓ |
| objectives | — | ✓ | ✓ | — | optional | ✓ | ✓ |
| upstream external buffer | — | — | — | — | — | optional | ✓ |
| dynamic entity sets | — | optional | optional | optional | ✓ | ✓ | ✓ |
| reset/provenance | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

No capability in Labs 0–6 requires stochastic disturbance, economics, organizational roles, or a general-purpose web dashboard.

---

# Platform-level acceptance suite derived from the labs

Codex implementation should create deterministic integration fixtures independent of final course artwork/layout.

At minimum:

1. **Clock fixture** — phase/window boundaries and clean tick start/end.
2. **Port fixture** — known source withdrawal/sink delivery/demand settlement.
3. **Supply overflow fixture** — unbounded, finite, and zero external storage.
4. **WIP continuity fixture** — one workpiece through source → inserter → belt → machine → sink remains WIP=1 until completion.
5. **Belt deduplication fixture** — no transport-line double count.
6. **Machine-state fixtures** — productive/starved/blocked/unavailable/disabled/idle and brownout/degraded condition.
7. **Aggregation fixture** — known tick series produces exact time mean/integral/nearest-rank percentile.
8. **Service cohort fixture** — opening backlog and end-of-window demand cannot corrupt the on-time denominator; deadlines/censoring work.
9. **Cycle-time fixture** — Little's-Law-derived vs isolated direct probe are distinct methods.
10. **Visibility fixture** — hidden post-run diagnostics are still collected but not learner-live visible.
11. **Objective fixture** — requirements/preferences, incomplete→undetermined, no hidden scalar score.
12. **Dynamic entity-set fixture** — build/remove changes eligibility intervals correctly.
13. **Reset fixture** — retry reloads baseline and produces a new run ID with the same reproducibility fingerprint where inputs match.
14. **Headless/controller fixture** — resolved config transfers through RCON and authoritative JSONL telemetry survives independently of live control responses.

---

# Validation conclusion

The accepted FISL v1 contract is sufficient to express Factory Physics Labs 0–6 without adding lab-specific runtime concepts.

The remaining work is implementation and content calibration:

- build the generic FISL core runtime/controller/schema;
- create/tune baseline saves and workpiece recipes;
- implement course text/debriefs;
- calibrate numeric targets after deterministic integration fixtures are passing.

This is the threshold at which the design can move from contract definition to implementation.
