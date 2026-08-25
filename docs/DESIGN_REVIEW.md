# FISL v1 Design Review — Pre-Implementation Critique

**Status:** Review / input to a revision pass
**Reviewed:** `ARCHITECTURE.md`, ADRs 0001–0016, `SCENARIO_MEASUREMENT_CONTRACT.md`, `FISL_V1_SCHEMA.md`, `FISL_V1_PRD.md`, `FACTORY_PHYSICS_LABS_V1.md`, `RESEARCH_NOTES.md`
**Date:** 2026-08-25
**Purpose:** Independent critical review of the accepted design before major implementation begins.

---

## Overall verdict

The measurement semantics are unusually strong: the ADRs get many genuinely hard
things right, and most of the scientific contract should be kept as-is (see
§8). The significant problems are mostly not in what the documents say — they
are in what the documents **assume**, what they **omit**, and the process
posture they take. Three structural risks should be resolved before major
building, plus several concrete spec bugs and internal contradictions.

Findings are ordered by severity.

---

## 1. The contract is "Accepted" with zero contact with the real Factorio runtime — and forbids reopening itself

All 16 ADRs are marked Accepted and the PRD instructs the implementer:

> "Do not reopen accepted scientific semantics merely because an
> implementation shortcut would be easier."

But nothing in the contract has ever executed against Factorio 2.0.77. Several
ADRs are load-bearing on **unverified API behavior**:

- **ADR 0007** — craft-progress-delta activity detection depends on exact
  `crafting_progress` reset behavior at craft completion, `products_finished`
  monotonicity, float precision of tiny per-tick progress increments under
  brownout, and machines that can complete more than one craft per tick at
  high effective speeds.
- **ADR 0005 §11** — the "in-process occupancy" WIP adapter depends on exactly
  when ingredients are consumed relative to `is_crafting`, and on how
  partially-buffered machine input inventories behave. The ADR itself calls
  the verifying test "mandatory," which is an admission that the semantic is a
  hypothesis.
- **ADR 0005 §13** — transport-line deduplication via line-equality semantics
  across belts, undergrounds, and splitters is notoriously fiddly and
  version-sensitive.
- **ADR 0015** — RCON `/silent-command` payload limits, chunked transfer
  behavior, and `script-output` write throughput at per-tick emission rates.

The "don't reopen" instruction is exactly wrong for this situation: it will
push an implementation agent to contort around infeasible semantics rather
than surface them.

**Recommendation:**

1. Re-label the ADRs "Accepted (design-stage; unvalidated against runtime)."
2. Extract the empirical API assumptions into an explicit checklist, each
   tagged with the ADR that depends on it.
3. Run a short Lua spike whose only goal is to confirm or kill those
   assumptions. The WIP-continuity fixture (one workpiece through
   source → inserter → belt → assembler → sink staying WIP = 1) is the ideal
   spike because it touches nearly all of them.
4. Only then freeze the contract and stamp each ADR with what the spike
   confirmed.

---

## 2. Tick-resolution WIP observation has no valid fallback under the contract's own rules

This is the largest internal design hole. The chain:

- **ADR 0010 §5/§7**: authoritative time-weighted WIP requires **complete
  one-tick coverage** "or an exactly equivalent event/change accumulator," and
  explicitly forbids integrating sparse point samples without a justified
  reconstruction rule.
- **ADR 0005 §13**: belt WIP requires reading deduplicated transport-line
  contents.
- Belts fire **no events** when items move. There is no event-driven
  equivalent for belt contents. The "exactly equivalent event accumulator"
  escape hatch is unavailable for the one holder class that changes nearly
  every tick.

The contract therefore effectively mandates scanning every transport line,
machine process inventory, inserter hand, and active craft **every tick at
60 UPS**, in Lua — alongside per-machine per-tick status and progress sampling
(ADR 0007 §22) and per-tick entity-set membership reconciliation (ADR 0016).
The PRD defers performance ("no fixed UPS budget is asserted before
profiling"), but if profiling fails, the contract as written provides **no
legal degradation path**: sparse sampling is banned for canonical WIP, and
canonical labs require canonical WIP.

**Recommendation:** either budget and profile this now (it may be fine for
small teaching factories — nobody has measured), or amend ADR 0010 to bless a
sanctioned coarser cadence with declared hold semantics — e.g. "WIP sampled
every N ticks; each sample holds for its N-tick interval" is a perfectly
defensible *declared* method. The amendment costs little now and removes a
cliff later.

---

## 3. Routine learner actions will invalidate runs — ADR 0005 contradicts Lab 6

**ADR 0005 §16** makes tracked work entering a player inventory a protocol
violation / WIP-coverage flag. But in Factorio, **mining a belt or machine that
contains items places those items into the player's inventory**. Mid-run
redesign is not an edge case — it is the explicit point of Lab 4 (resize
buffers) and Lab 6 ("Dynamic redesign requirement": learners add/remove
machines during the run). Every learner who picks up a belt segment carrying
workpieces — which happens constantly during redesign — flags the run.

Combine that with the strict-coverage default (ADR 0010 §21) and objective
semantics (ADR 0012 §7: incomplete metric → `undetermined`), and the
predictable classroom outcome is that **most student runs end with flagged WIP
coverage and undetermined objectives**. Scientifically principled;
pedagogically fatal.

**Recommendation:** design an answer rather than a flag. Candidates:

- count player-held tracked items as a WIP holder ("work in limbo") with a
  diagnostic condition instead of a violation;
- make the carriage restriction apply only when tracked items *leave* the
  system via the player;
- scope the violation to phases where redesign is prohibited (but note Lab 6
  expects redesign during measurement).

As written, ADR 0005 and `FACTORY_PHYSICS_LABS_V1.md` contradict each other.

---

## 4. The POC is not a POC

The PRD's "POC definition of done" (§33) has 17 items spanning essentially the
entire product: compiler, CLI, server orchestration, RCON protocol, core mod,
GUI, ports, WIP, machine state, service cohorts, cycle time, objectives,
visibility, provenance, retry, and headless tests. That is the full v1 with
the word "POC" attached.

Honestly assessed, Labs 0–4 need: clock/phases, ports, conserved WIP,
throughput, machine state, and aggregation. They do **not** need service
cohorts, censoring semantics, demand-wait percentiles, external supply buffers
with three capacity policies, visibility enforcement, or `fisl compare`.
Roughly 40% of the specified surface (ADR 0008, ADR 0011, much of ADR 0012,
and the external-buffer machinery of ADR 0003) exists only for Labs 5–6 and
beyond — the architecture document preaches YAGNI in §24.2 and the ADR set
then violates it.

**Recommendation:** cut a true vertical slice and sequence around teaching:

1. Headless fixture proving clock + port settlement + WIP continuity +
   throughput (this doubles as the §1 validation spike).
2. Lab 3 (Little's Law) with a human learner.
3. Teach it once.
4. Only then implement the service/visibility/objective layers for Labs 5–6.

---

## 5. Concrete spec bugs and inconsistencies

### 5.1 ADR status mismatch

ADR 0004 and ADR 0005 say `Status: Proposed` in their headers while
`adr/README.md` and all downstream documents list them as Accepted. These are
the two most load-bearing ADRs; fix the headers.

### 5.2 Resolved-hash / run-config conflation

`FISL_V1_SCHEMA.md` §20 requires the resolved JSON delivered to Lua to contain
`run_id` and the actual seed. ADR 0013 §3/§9 defines the *resolved experiment
hash* as a stable identity that repeated runs can share (and ADR 0014 §3
depends on retries sharing a reproducibility fingerprint). If the hash covers
the §20 document, it changes on every run and fingerprints never match. The
documents never say which subset is hashed.

**Fix:** explicitly split the **resolved scenario** (run-independent, hashed)
from the **run configuration** (run_id + seed + a reference to the resolved
scenario), and state that the resolved experiment hash covers only the former.

### 5.3 Pause policy is near-meaningless in the chosen topology

ADR 0001 defines `pause_policy: allowed/prohibited` for the learner, but
ADR 0015 makes the canonical runtime a multiplayer server — where a client
pressing Esc does **not** pause the game, and a dedicated server typically
auto-pauses when the last player disconnects. So the learner cannot exercise
"allowed," and a client disconnect can silently freeze the experiment clock
mid-run (technically correct under ADR 0001, operationally surprising). The
interaction between these two accepted ADRs is unexamined; document intended
server pause settings and what a disconnect means for a measured run.

### 5.4 `service_tail` = `max_wait` is razor-thin

In the canonical example both are 30 s, so a cohort created on the final
measured tick has its deadline land exactly at experiment end. It validates,
but one off-by-one in the half-open arithmetic silently censors the last
cohorts. Recommend the compiler require the observation tail to exceed
`max_wait` by at least one settlement interval.

### 5.5 Dual metric implementation burden

ADR 0010 §24 requires Lua streaming accumulators and Python post-run
computation to be capable of producing identical results. That doubles the
metric engine and creates a permanent equivalence-testing burden. Minimize
Lua-computed final metrics to only what the live UI and in-game objectives
strictly need; make Python the sole authority for everything post-run.

---

## 6. Material omissions

### 6.1 Classroom operations and deployment

Nothing addresses how N students obtain a pinned Factorio version, the mods,
the Python controller, port/firewall permissions on institutional machines, or
Factorio licenses. For a teaching product this is a top-three risk; it appears
only as "README/user docs" in the v1 definition of done.

### 6.2 Iteration-loop time

Reset = full server restart + baseline reload, and the canonical run is
25+ minutes at fixed speed 1.0. A 90-minute class gets roughly three attempts.
The deterministic labs do not need real-time human reaction; consider a fixed
2× speed as the human default and shorter measured phases. The contract
already permits this (ADR 0001 §4) — the defaults just point the wrong way.

### 6.3 A simpler alternative to the chunked RCON config upload

The controller already assembles the per-run mod directory, so it can emit a
tiny companion mod (e.g. `fisl-scenario-config`) containing the resolved
configuration as a Lua table that `fisl-core` simply `require`s at startup.
That deletes the entire begin/append/commit/hash-verify protocol, keeps RCON
for lifecycle only (start/abort/status/save), and makes the configuration a
natural part of save state. Cost: the mod manifest varies per run (minor
provenance noise). Worth a revision or explicit rejection in ADR 0015.

### 6.4 Telemetry volume unsized

Per-tick classified state for N machines over 90,000 ticks is millions of
JSONL records per run. Lossless compression is permitted but nobody has sized
the output or the per-tick `script-output` write cost.

### 6.5 Documentation redundancy will drift

The same rules are restated across five layers (ADRs → contract summary →
schema → PRD → labs doc). Drift is already visible (§5.1). The source-of-truth
hierarchy in PRD §36 helps, but consider slimming the restatements or marking
them explicitly non-normative.

---

## 7. Process critique

The ADRs were proposed and "accepted" in a single design conversation with no
independent reviewer and no empirical validation; acceptance criteria written
as "we agree that…" reflect one author agreeing with itself. That is fine for
a design draft — it is not fine as settled law that an implementation agent is
instructed never to reopen. The fix is cheap: downgrade the status wording
(§1) and route all implementation-discovered conflicts through superseding
ADRs, which the documents already anticipate.

---

## 8. What is genuinely good — keep it

Several decisions are better than what most teams produce, and none of the
findings above argue for redesigning them:

- the zone / system / entity-set / port / flow separation;
- refusing bare `utilization` and bare `service_level`;
- missing-data-is-never-zero, strict coverage, and censored-cohort semantics;
- the **conserved workpiece family** — the best call in the whole set; it
  dissolves the Little's Law item-identity problem instead of faking it;
- Lua-authoritative simulation time with the controller demoted to
  orchestration;
- reset-as-baseline-reload instead of an undo engine;
- "persistent state is boring data";
- half-open intervals used uniformly across time, zones, and windows;
- honest measurement epistemics (`net_inventory_delta` labeled weaker than
  controlled transactions; `little_law_derived` never masquerading as direct
  measurement);
- explicit v1 non-goals and the scenario-before-theory pedagogy.

---

## 9. Recommended sequence

1. **Paper fixes:** ADR 0004/0005 statuses; split resolved-scenario hash from
   run configuration; document pause/topology interaction; require
   `tail > max_wait`.
2. **Contract amendments before they are load-bearing:** player-inventory WIP
   handling (§3) and a sanctioned coarser WIP sampling cadence (§2).
3. **API-validation spike:** WIP continuity, craft-progress semantics, belt
   dedup, RCON limits, `script-output` throughput. Stamp each ADR with what it
   confirmed or broke.
4. **Re-scope the POC** to the headless vertical slice + Lab 3, and defer
   ADR 0008/0011/0012 implementation until a human has been taught with the
   slice.
