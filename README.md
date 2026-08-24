# Factorio Research

Research and development repository for the **Factorio Industrial Systems Laboratory (FISL)**: a controllable experimental layer on top of Factorio for teaching and researching factory physics, operations management, control, and eventually organizational cybernetics.

## Core idea

> **Use Factorio to model the system. Use FISL to model the experiment.**

Factorio already provides a rich physical simulation of production: machines, belts, buffers, recipes, power, trains, logistics, circuits, and construction. FISL adds the experimental apparatus needed to make that world reproducible, measurable, parameterized, and extensible for serious teaching.

The immediate target is **Factory Physics**. Future work may add controlled variability, economics, feedback/control experiments, and structured multiplayer organizational-cybernetics exercises.

## Documents

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — FISL architecture, scope, design principles, v1 boundary, and future extension model.
- [`docs/SCENARIO_MEASUREMENT_CONTRACT.md`](docs/SCENARIO_MEASUREMENT_CONTRACT.md) — working home for the next design task: the scenario and measurement contract.
- [`docs/adr/README.md`](docs/adr/README.md) — architectural decision records as implementation choices become concrete.

## Repository direction

The intended implementation shape is:

- `factorio/` — the in-game FISL Lua mod/runtime.
- `python/` — external experiment/scenario tooling.
- `scenarios/` — reproducible teaching/experimental scenario packages.
- `docs/` — architecture, contracts, pedagogy, and ADRs.

These directories should grow only as their contracts become clear; FISL is deliberately **not** starting as a large framework implementation.
