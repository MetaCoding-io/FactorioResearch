# Factorio Research

Research and development repository for the **Factorio Industrial Systems Laboratory (FISL)**: a controllable experimental layer on top of Factorio for teaching and researching Factory Physics, operations management, control, and eventually organizational cybernetics.

## Core idea

> **Use Factorio to model the system. Use FISL to model the experiment.**

Factorio already provides a rich physical simulation of production: machines, belts, buffers, recipes, power, trains, logistics, circuits, and construction. FISL adds the experimental apparatus needed to make that world reproducible, measurable, parameterized, and extensible for serious teaching.

The immediate target is **deterministic Factory Physics**. Future work may add controlled variability, economics, feedback/control experiments, and structured multiplayer organizational-cybernetics exercises.

## Start here for implementation

The v1 scientific contract is now sufficiently specified to begin implementation.

- [`docs/FISL_V1_PRD.md`](docs/FISL_V1_PRD.md) — **Codex-ready implementation/product requirements document.**
- [`docs/FISL_V1_SCHEMA.md`](docs/FISL_V1_SCHEMA.md) — implementation-grade authoring/resolved scenario schema.
- [`docs/FACTORY_PHYSICS_LABS_V1.md`](docs/FACTORY_PHYSICS_LABS_V1.md) — Labs 0–6 contract validation and required integration fixtures.
- [`docs/adr/README.md`](docs/adr/README.md) — accepted ADR index and scientific/architectural decisions.

## Background documents

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — FISL architecture, scope, design principles, v1 boundary, and future extension model.
- [`docs/SCENARIO_MEASUREMENT_CONTRACT.md`](docs/SCENARIO_MEASUREMENT_CONTRACT.md) — accepted scientific API summary linking the detailed ADRs.
- [`docs/RESEARCH_NOTES.md`](docs/RESEARCH_NOTES.md) — research and intellectual provenance behind the project.

## Repository direction

The intended implementation shape is:

- `factorio/` — in-game FISL Lua runtime and Factory Physics content mod.
- `python/` — scenario/compiler/controller/report tooling.
- `scenarios/` — reproducible teaching/experimental scenario packages.
- `tests/` — deterministic unit and Factorio headless integration fixtures.
- `docs/` — architecture, contracts, pedagogy, PRD, and ADRs.

The durable artifact is the laboratory platform and scenario contract rather than any one hard-coded course factory.
