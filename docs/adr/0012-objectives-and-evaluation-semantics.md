# ADR 0012: Objectives and Evaluation Semantics

- **Status:** Accepted
- **Issue:** #1 — Define FISL v1 scenario and measurement contract
- **Scope:** FISL v1

## Context

FISL now has explicit metric semantics. The remaining evaluation question is how a scenario states what constitutes acceptable or preferable performance without collapsing the entire experiment into one arbitrary score.

Factory Physics labs naturally combine constraints and trade-offs. A push/pull exercise might require:

```text
customer service >= 95%
```

while asking the learner to reduce:

```text
average WIP
```

A bottleneck lab might ask learners to maximize throughput but still expose WIP and machine-state consequences. A later variability lab may ask learners to trade inventory, capacity, and response time.

The objective model must therefore separate metric facts from evaluation rules, support incomplete/no-data results honestly, and avoid hidden weighting.

## Decision

### 1. Metrics and objectives are separate objects

A metric answers:

> What happened, according to a declared measurement method?

An objective answers:

> How should a declared metric result be evaluated for this scenario?

Objectives reference existing metric IDs. They MUST NOT redefine measurement windows, units, denominators, or methods independently from the metric they evaluate.

### 2. V1 supports two objective families: requirements and preferences

A scenario objective set may contain:

1. **requirements** — threshold/range rules that can pass or fail;
2. **preferences** — minimize/maximize directions used for comparison/debrief rather than producing a standalone pass/fail result.

This supports the canonical pattern:

```text
subject to service >= 95%
minimize average WIP
```

without inventing one weighted score.

### 3. Requirement objectives use explicit comparison operators and units

V1 requirements support at least:

```text
minimum   metric >= threshold
maximum   metric <= threshold
range     lower <= metric <= upper
```

Equality MAY be supported for exact integer/count fixtures but SHOULD NOT be the default style for floating/ratio teaching objectives.

Thresholds must be dimensionally compatible with the referenced metric.

Author-facing percentages/durations may compile to exact resolved numeric/tick representations where applicable.

### 4. Preference objectives declare direction only

A preference objective is conceptually:

```text
minimize <metric>
```

or:

```text
maximize <metric>
```

A preference does not pass or fail in a single isolated run unless an additional threshold requirement exists.

It produces a comparable value for debrief/cross-run analysis.

### 5. V1 does not define an implicit weighted scalar score

FISL MUST NOT automatically convert objectives such as:

```text
service
WIP
throughput
cycle time
```

into one score by assigning hidden weights or normalization constants.

If a future scenario needs a scalar utility/cost function, it must declare the formula and units explicitly as a metric/objective model.

V1 favors transparent requirements + preferences.

### 6. Overall requirement status is conjunction by default

If a scenario has multiple requirement objectives, overall requirement status is:

```text
pass       if every required objective passes
fail       if at least one required objective definitively fails
undetermined if none fail but at least one is unresolved/incomplete/no-data
```

A scenario may report individual objective statuses regardless of the overall status.

### 7. Incomplete or no-data metrics produce `undetermined`, not automatic failure or success

If an objective's source metric is:

- incomplete under strict coverage;
- censored/unresolved;
- undefined/no-data;
- dimensionally invalid;

then the objective result is `undetermined` unless the scenario explicitly defines a different policy for a non-scientific exercise.

Canonical scientific objectives MUST NOT treat missing measurement as zero, perfect performance, or failure merely for convenience.

### 8. Protocol validity and objective outcome remain separate

A learner can numerically satisfy every objective while violating an experiment protocol, and a protocol-valid run can fail an objective.

Results therefore preserve separately:

```text
measurement completeness
objective outcome
run/protocol validity
```

The UI/debrief may state, for example:

```text
Objective result: PASS
Run comparison validity: FLAGGED (tracked work manually carried)
```

rather than collapsing both into one boolean.

### 9. Objective evaluation uses final authoritative metric results

Final objective status is computed only from the final resolved metric result for its declared window/population.

A live/provisional objective display may exist, but it must be labeled provisional and use a metric whose current semantics are valid, such as a trailing or cumulative metric.

FISL MUST NOT extrapolate an unfinished whole-phase aggregate and label it final.

### 10. Objectives inherit metric provenance

An objective result retains at least:

```text
objective_id
objective_type
metric_id
comparison/operator/direction
threshold(s) if applicable
metric result/value/unit
status/value
metric coverage/validity reference
```

A reviewer must be able to trace a pass/fail back through the metric to its primitive observations.

### 11. Cross-run preference comparison requires semantic compatibility

Two runs may be compared on a preference objective only when their referenced metric definitions are compatible for the intended comparison.

At minimum this normally means matching:

- scenario/experiment definition or an explicitly compatible variant;
- metric ID/semantic definition;
- flow/system boundary;
- unit;
- observation window semantics;
- coverage policy.

FISL MUST NOT rank two values merely because both are labeled `average_wip` if their measurement contracts differ.

### 12. Multiple preferences remain a vector in v1

If a scenario declares multiple preferences, FISL v1 reports the vector rather than inventing a total ordering.

For example:

```text
average WIP: 120 (minimize)
throughput:  61/min (maximize)
energy:      ... future
```

The debrief may identify simple dominance where one run is no worse on every declared preference and better on at least one, but general Pareto-front tooling is not required for v1.

### 13. Requirements can define the feasible set for preference comparison

Canonical instructional comparison SHOULD treat requirement-passing runs as feasible.

For example:

```text
Requirement: on-time item rate >= 95%
Preference: minimize average WIP
```

A run with extremely low WIP because it fails to serve customers is not considered a successful optimization of the exercise.

The raw metric values remain visible for analysis; the evaluation layer simply distinguishes feasible from infeasible runs.

### 14. Objectives are scenario semantics and affect experiment identity

Changing a requirement threshold or optimization target changes the instructional/experimental condition even if physical runtime behavior is otherwise identical.

Therefore resolved objectives are part of the resolved scenario and experiment provenance/hash.

### 15. Objective visibility follows ADR 0011

Scenario authors may independently disclose:

- the objective rule/target;
- provisional status;
- final status;
- underlying metric value.

Evaluation itself always uses the authoritative metric regardless of disclosure.

### 16. V1 objective vocabulary remains deliberately small

Required v1 support:

```text
minimum requirement
maximum requirement
range requirement
minimize preference
maximize preference
```

Deferred:

- weighted scoring;
- arbitrary expression languages;
- multi-stage reward functions;
- stochastic risk objectives;
- confidence-bound objectives;
- automated Pareto optimization;
- economic utility functions beyond explicitly declared future metrics.

This keeps objective evaluation auditable and sufficient for Factory Physics Labs 0–6.

## Illustrative schema shape

```yaml
objectives:
  service_requirement:
    type: requirement
    metric: customer_service
    minimum: 0.95

  minimize_wip:
    type: preference
    metric: average_wip
    direction: minimize
```

A range example:

```yaml
  target_throughput_band:
    type: requirement
    metric: measured_throughput
    range:
      minimum: 55/min
      maximum: 65/min
```

The final schema will normalize quantities/units before evaluation.

## Consequences

### Positive

- Scientific metrics remain factual and reusable independently of grading/evaluation.
- Canonical Factory Physics trade-offs can be expressed as constraints plus preferences.
- Missing data cannot accidentally become a pass/fail value.
- FISL avoids opaque game-like scoring and hidden weights.
- Cross-run comparison is tied to compatible measurement semantics.
- Future explicit economic cost/utility functions can be added without redesigning metrics.

### Negative / trade-offs

- V1 does not provide one leaderboard score for multi-objective experiments.
- Multiple preferences may require human/debrief interpretation.
- Scenario authors must define requirement thresholds explicitly.
- Provisional live objective displays need separately valid live metrics when final metrics are unfinished.

## Acceptance criteria

The objectives portion of Issue #1 is complete when:

1. objectives reference metrics rather than redefining measurements;
2. v1 separates pass/fail requirements from minimize/maximize preferences;
3. requirement comparisons are unit-compatible and explicit;
4. multiple requirements combine by conjunction unless a future explicit composition says otherwise;
5. incomplete/no-data metrics yield undetermined objective status;
6. protocol validity remains separate from objective outcome;
7. final objectives use final authoritative metric results;
8. no implicit weighted scalar score exists in v1;
9. multiple preferences remain an explicit vector and comparisons require semantic compatibility;
10. requirements can define feasibility for preference comparisons;
11. objectives contribute to resolved experiment identity/provenance;
12. objective disclosure follows the independent visibility policy.
