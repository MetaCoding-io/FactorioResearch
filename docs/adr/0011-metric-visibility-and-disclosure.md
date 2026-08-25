# ADR 0011: Metric Visibility and Disclosure Semantics

- **Status:** Accepted
- **Issue:** #1 — Define FISL v1 scenario and measurement contract
- **Scope:** FISL v1

## Context

FISL collects scientific observations and derives metrics for several different purposes:

- learner feedback during an experiment;
- post-run debrief;
- instructor diagnosis;
- objective evaluation;
- debugging and validation;
- future role-specific information experiments.

Those purposes must not be conflated. If a metric is required for a scientifically valid result, hiding it from the learner cannot mean that FISL stops collecting it. Conversely, collecting a diagnostic does not mean the learner should automatically see it live.

This matters pedagogically. A bottleneck exercise may be much stronger if the learner sees system throughput but does not receive a live label saying exactly which machine is starved or blocked. A push/pull lab may expose customer service and current WIP while reserving detailed machine-state distributions for the debrief.

It also matters architecturally because Layer III organizational-cybernetics experiments will eventually need role-specific information structures. V1 should establish a disclosure model that can be extended to named roles rather than replaced.

## Decision

### 1. Collection, evaluation, and visibility are independent concerns

FISL separates:

1. **observation/collection** — what scientific facts are recorded;
2. **metric/objective evaluation** — what is calculated from those facts;
3. **visibility/disclosure** — what information is revealed to which audience and when.

A visibility rule MUST NOT change the underlying measurement definition.

The same authoritative metric result is either disclosed or withheld; FISL does not compute a second learner-specific version of a metric merely for display.

### 2. V1 defines four conceptual audiences

The baseline disclosure audiences are:

```text
learner_live
learner_post_run
instructor
debug
```

Their intent is:

- `learner_live` — information available during the active experiment;
- `learner_post_run` — information revealed to the learner after the run/debrief boundary;
- `instructor` — richer result/diagnostic information intended for scenario authors/instructors;
- `debug` — implementation-level diagnostics, primitive details, coverage failures, adapter internals, and validation information.

These are disclosure audiences, not separate copies of the dataset.

### 3. Visibility is allowlist-based

Information is not learner-visible merely because it exists.

A scenario/profile explicitly declares which metrics/objectives/diagnostics are exposed to learner audiences. If an item has no learner visibility rule, the conservative default is that it is not shown to the learner UI.

Instructor/debug tools may have broader defaults under the execution environment, but their access is not implied by learner disclosure.

### 4. V1 visibility applies primarily to named metric/objective outputs, not arbitrary raw telemetry browsing

The learner-facing in-game UI should expose named metric and objective views declared by the scenario.

Primitive telemetry remains an internal/run-dataset artifact unless a scenario deliberately exposes a pedagogical diagnostic derived from it.

This prevents the learner UI from becoming a raw scientific-debug console and protects exercises in which detailed diagnosis is intentionally withheld.

### 5. A metric can have different live and post-run disclosure

A metric may be:

```text
hidden live -> revealed post-run
```

or:

```text
visible live -> also visible post-run
```

For example:

```yaml
visibility:
  learner_live:
    metrics:
      - live_throughput
      - customer_service
  learner_post_run:
    metrics:
      - average_wip
      - p95_wip
      - machine_state_summary
      - loaded_cycle_time
```

The exact final syntax is deferred to the schema document, but the semantics are fixed.

### 6. Current/live values and final aggregate results are distinct disclosures

A scenario that exposes a live metric must identify a metric whose temporal semantics are valid at the current checkpoint, such as:

- current point state (`WIP(T)`);
- a fully resolved trailing window;
- cumulative count to date;
- a provisional objective status explicitly marked provisional.

FISL MUST NOT display the future final value of a whole-phase metric before the phase is complete.

If a live view uses a rolling or partial metric, that metric is a separately named metric definition with its own window semantics under ADR 0010.

### 7. Objective target/value/status disclosures are independently controllable

Objectives can leak information even when their underlying metric is hidden. Therefore visibility may distinguish conceptually among:

```text
objective target/rule
current/provisional status
final status
underlying metric value
```

A scenario may, for example, tell the learner:

> Maintain customer service at or above 95%.

while withholding detailed customer backlog or machine-state diagnostics.

Another scenario may hide the pass/fail status until the end.

The final schema may provide profiles for common combinations, but the scientific contract does not assume all objective information is always visible.

### 8. Hidden metric values may still drive objectives

An objective may reference a metric that is not learner-visible.

The objective engine always uses the authoritative metric result. Visibility only controls disclosure.

If the objective status itself is shown live, that disclosure is explicit and may reveal information indirectly; scenario authors are responsible for that pedagogical choice.

### 9. Debug diagnostics are never scientific replacements for named metrics

Debug UI may expose raw Factorio status, holder counts, classifier reasons, observation gaps, port internals, sequence numbers, and other implementation facts.

Those diagnostics do not become learner metrics merely because they are convenient to display during development.

Production scenario definitions SHOULD reference stable named metrics/objectives rather than debug fields.

### 10. Visibility does not alter run-dataset completeness

The run dataset should retain the primitive/derived data required by the observation plan and provenance contract regardless of learner disclosure.

For example, a learner may see only throughput live while the run still records:

- WIP holder observations;
- machine-state classifications;
- demand cohorts;
- coverage diagnostics;
- objective dependencies.

This is essential for post-run audit and reproducibility.

### 11. V1 visibility is a pedagogical disclosure mechanism, not an adversarial security boundary

In a normal local single-player FISL installation, a technically capable learner may be able to inspect local files, mods, or process data.

V1 therefore makes a narrower guarantee:

> FISL's supported learner UI and scenario presentation will disclose only information permitted by the visibility policy.

It does not claim cryptographic secrecy from a user who controls the machine.

Future multiplayer/organizational experiments that depend on genuine differential information access may require stronger server-authoritative enforcement and deployment controls.

### 12. Future role-specific visibility extends the audience model

Layer III may introduce named roles such as:

```text
operations
logistics
planning
management
```

Those roles should be able to inherit or compose the same disclosure concepts used by v1:

- metric availability;
- current vs post-run timing;
- objective rule/status disclosure;
- local/aggregate diagnostic views.

The v1 audience names are therefore not hard-coded into metric semantics; they are initial principals in a broader disclosure model.

### 13. Visibility configuration is scenario semantics and belongs in the resolved scenario/provenance

Changing what the learner can see can change learner behavior and therefore experimental conditions.

Consequently the resolved visibility policy is part of the experiment definition and MUST contribute to the resolved experiment hash/provenance.

A run with hidden WIP and a run with live WIP are not treated as the same experimental condition merely because the physical factory and demand schedule are identical.

### 14. Visibility changes during a phase are not required for v1

V1 SHOULD keep disclosure policies stable within a run unless a scenario uses explicit phase-level visibility changes supported by the final schema.

Arbitrary event-driven reveal/hide rules are deferred.

If phase-specific disclosure is supported initially, transitions occur on the same clean tick boundaries as phase changes and become part of the resolved scenario.

### 15. Learner UI refresh cadence is presentation only

A metric's visibility does not change its scientific sampling or aggregation cadence.

For example, machine state may be classified every simulation tick while the learner UI refreshes an allowed rolling summary once per second.

The UI must consume authoritative metric state rather than re-querying Factorio with its own measurement logic.

## Illustrative schema shape

```yaml
visibility:
  learner_live:
    metrics:
      - current_wip
      - live_throughput
      - customer_service_live
    objectives:
      - service_requirement

  learner_post_run:
    metrics:
      - average_wip
      - measured_throughput
      - loaded_cycle_time
      - machine_state_summary
    objectives:
      - service_requirement
      - minimize_wip

  instructor:
    metrics: all_declared
    diagnostics:
      - protocol_violations
      - coverage
      - balance_errors

  debug:
    diagnostics: all
```

The final schema may use explicit lists/profiles rather than the exact tokens above.

## Consequences

### Positive

- Pedagogical information withholding cannot corrupt scientific data collection.
- A single authoritative metric definition feeds UI, objectives, reports, and telemetry.
- Scenario authors can avoid giving away the diagnosis during exploratory labs.
- Objective disclosure can be controlled independently from metric disclosure.
- Visibility becomes a first-class experimental variable and is included in provenance.
- The model extends naturally toward future role-specific information structures.

### Negative / trade-offs

- Scenario authors must think deliberately about what information is revealed.
- A local learner with filesystem/process access can potentially bypass pedagogical hiding; v1 does not promise adversarial secrecy.
- Hidden objectives/status can make exercises feel opaque unless course materials explain the task well.
- Live and final views may require separately named rolling/final metrics rather than reusing one ambiguous metric.

## Acceptance criteria

The metric-visibility portion of Issue #1 is complete when:

1. collection, evaluation, and disclosure are separate concerns;
2. v1 recognizes learner-live, learner-post-run, instructor, and debug audiences;
3. learner disclosure is explicit/allowlist-based;
4. visibility does not change metric semantics or run-dataset collection;
5. live metrics must have valid current/rolling semantics rather than exposing unfinished final aggregates;
6. objective target/status/value disclosure can be controlled independently;
7. hidden metrics may still drive authoritative objectives;
8. the supported learner UI respects disclosure, while v1 does not claim adversarial local secrecy;
9. visibility is part of the resolved experimental condition/provenance;
10. future named roles extend rather than replace this disclosure model.
