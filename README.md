# Factorio Research

Research and development repository for the **Factorio Industrial Systems Laboratory (FISL)**: a controllable experimental layer on top of Factorio for teaching and researching Factory Physics, operations management, control, and eventually organizational cybernetics.

## Core idea

> **Use Factorio to model the system. Use FISL to model the experiment.**

Factorio already provides a rich physical simulation of production: machines, belts, buffers, recipes, power, trains, logistics, circuits, and construction. FISL adds the experimental apparatus needed to make that world reproducible, measurable, parameterized, and extensible for serious teaching.

The immediate target is **deterministic Factory Physics**. Future work may add controlled variability, economics, feedback/control experiments, and structured multiplayer organizational-cybernetics exercises.

## Using FISL

- [`docs/ROADMAP.md`](docs/ROADMAP.md) — **living plan/status**: what's done (with evidence), the current phase, and issue links.
- [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) — **living operator's guide**: setup, `fisl validate/build-baseline/run/report`, connecting the graphical client, run artifacts, troubleshooting. Kept current with every workflow change.

## Start here for implementation

An independent pre-implementation review produced a focused revision pass. **For the immediate POC, start with the post-review handoff rather than treating the full v1 PRD as one implementation milestone.**

1. [`docs/POST_REVIEW_REVISIONS.md`](docs/POST_REVIEW_REVISIONS.md) — what changed after independent design review and which older statements are superseded.
2. [`docs/RUNTIME_VALIDATION.md`](docs/RUNTIME_VALIDATION.md) — empirical Factorio 2.0.77 assumptions that the first spike must prove/falsify.
3. [GitHub Issue #2](https://github.com/MetaCoding-io/FactorioResearch/issues/2) — immediate runtime-validation spike + Lab 3 / Little's Law vertical-slice definition of done.
4. [`docs/FISL_V1_SCHEMA.md`](docs/FISL_V1_SCHEMA.md) — implementation-grade `AuthorScenario` → stable `ResolvedScenario` + per-run `RunConfiguration` contract.
5. [`docs/adr/README.md`](docs/adr/README.md) — accepted ADR index, including ADR 0017 conserved-ledger WIP and ADR 0018 local-server pause/disconnect behavior.

Then use the broader documents as the destination/full-v1 specification:

- [`docs/FISL_V1_PRD.md`](docs/FISL_V1_PRD.md) — full v1 product/runtime requirements, including features deliberately deferred from the first vertical slice.
- [`docs/FACTORY_PHYSICS_LABS_V1.md`](docs/FACTORY_PHYSICS_LABS_V1.md) — Labs 0–6 contract validation and integration-fixture goals; Lab 3 is the first human-facing implementation target.

## Background documents

- [`docs/DESIGN_REVIEW.md`](docs/DESIGN_REVIEW.md) — independent pre-implementation critique that triggered the revision pass.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — FISL architecture, scope, design principles, v1 boundary, and future extension model.
- [`docs/SCENARIO_MEASUREMENT_CONTRACT.md`](docs/SCENARIO_MEASUREMENT_CONTRACT.md) — accepted scientific API summary linking the detailed ADRs.
- [`docs/RESEARCH_NOTES.md`](docs/RESEARCH_NOTES.md) — research and intellectual provenance behind the project.

## Repository layout

- `factorio/` — in-game FISL Lua runtime (`fisl-core`) and Factory Physics content mod (`fisl-factory-physics`).
- `python/` — scenario compiler, controller, metrics, and report tooling (`fisl` package).
- `scenarios/` — reproducible teaching/experimental scenario packages.
- `tests/unit/` — deterministic unit tests (no Factorio required).
- `tests/integration/` — runtime-validation spike against a real Factorio headless server (see its README).
- `docs/` — architecture, contracts, pedagogy, PRD, and ADRs.

The durable artifact is the laboratory platform and scenario contract rather than any one hard-coded course factory.

## Development quick start

```sh
pip install -e .[dev]
pytest tests/unit                 # no Factorio needed
fisl validate scenarios/factory-physics/fp03-littles-law

# runtime-validation spike (Issue #2 Stage A) — needs a real binary:
FACTORIO_BIN=/path/to/factorio/bin/x64/factorio pytest tests/integration -v
```
