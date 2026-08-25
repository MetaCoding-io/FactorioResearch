# ADR 0010: Aggregation and Observation-Window Semantics

- **Status:** Accepted
- **Issue:** #1 — Define FISL v1 scenario and measurement contract
- **Scope:** FISL v1

The complete accepted decision is preserved in this ADR. Its normative implementation requirements are also summarized in `../SCENARIO_MEASUREMENT_CONTRACT.md`, `../FISL_V1_SCHEMA.md`, and `../FISL_V1_PRD.md`.

## Accepted decision summary

FISL v1 aggregation follows these rules:

1. Ordinary aggregate metrics resolve to explicit contiguous half-open simulation-time windows `[A,B)`.
2. Cohort-selection windows and observation horizons remain distinct.
3. A prepared state sample `X(T)` represents the FISL state for `[T,T+1)`.
4. Time-weighted state integration uses left-boundary occupancy: `sum X(T)` over interval starts in the window.
5. Closing state `X(B)` is diagnostic and contributes no occupancy to `[A,B)`.
6. Integrated exposures such as WIP/backlog unit-ticks are first-class exact results.
7. Sparse point samples are not silently treated as continuous state without an explicit reconstruction method.
8. Interval facts aggregate by attributed interval, not settlement checkpoint.
9. Machine-state durations use classified intervals from ADR 0007.
10. FISL exposes no bare `utilization` percentage without an explicit denominator.
11. Missing coverage does not silently shrink denominators or become zero.
12. Cross-machine aggregation explicitly names pooled machine-time or another method.
13. State percentiles are weighted by simulation-time exposure.
14. Demand/cohort percentiles are quantity-weighted when defined per unit.
15. V1 uses deterministic weighted nearest-rank empirical quantiles without scientific interpolation.
16. Empty populations yield undefined/no-data rather than fabricated zero/perfect performance.
17. Strict coverage is the default for canonical scientific metrics.
18. Trailing window at `T` is `[T-L,T)` and contains only settled history.
19. Authoritative aggregation semantics are implementation-independent between Lua streaming and Python post-run calculation.
20. Exact integer/rational numerators/denominators are retained where practical; display rounding is non-authoritative.
21. Derived metrics verify window compatibility before combining inputs.
22. Results preserve window, weighting, denominator, quantile/method, dependencies, and coverage provenance.

## Core formulas

For canonical tick-resolution state:

```text
area_X = sum_{T=A}^{B-1} X(T) * 1 tick
mean_X = area_X / (B - A)
```

For WIP:

```text
wip_work_unit_ticks = sum WIP(T)
average_WIP = wip_work_unit_ticks / window_ticks
```

For weighted nearest-rank quantile, sort `(x_i, w_i)` by value and choose the smallest `x_i` whose cumulative weight reaches at least `p * sum(w_i)`.

For machine-state fractions, denominators are explicit (`full_window`, `classified_time`, or a named eligible state set). Missing classification remains visible as coverage rather than being silently removed.

## Consequences

These rules provide the authoritative average-WIP numerator required by Little's Law, make machine-time percentages auditable, and ensure Lua/Python/reporting libraries cannot silently disagree because of sampling or percentile defaults.
