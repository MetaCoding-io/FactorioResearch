"""AuthorScenario -> ResolvedScenario compilation (schema §1, §18–§20).

The resolved document contains only explicit runtime semantics: integer tick
boundaries, exact rational schedules, resolved cross-references, and the
compiled observation plan. It excludes `run_id`, the actual execution seed,
and explanatory `learning` metadata (ADR 0013 revision; schema §17).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from fisl import COMPILER_VERSION, PROTOCOL_VERSION, SPEC
from fisl.scenario.author_models import (
    AggregateMetric,
    AuthorScenario,
    CurrentValueMetric,
    CycleTimeMetric,
    DemandWaitPercentileMetric,
    OnTimeItemRateMetric,
    ProductionStateMetric,
    ScheduledSupply,
    StateFractionMetric,
    ThroughputMetric,
    WipMetric,
)
from fisl.scenario.canonical import canonical_json_bytes, document_hash
from fisl.scenario.units import UnitError, parse_duration_ticks, parse_rate


class CompilationError(Exception):
    """Scenario failed validation/compilation. Message lists every problem."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("scenario compilation failed:\n" + "\n".join(f"  - {p}" for p in problems))


def validate_author_dict(raw: dict) -> AuthorScenario:
    try:
        return AuthorScenario.model_validate(raw)
    except ValidationError as exc:
        problems = []
        for error in exc.errors():
            location = ".".join(str(part) for part in error["loc"])
            problems.append(f"{location}: {error['msg']}")
        raise CompilationError(problems) from exc


def load_author_yaml(path: str | Path) -> AuthorScenario:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise CompilationError([f"{path}: top level must be a mapping"])
    return validate_author_dict(raw)


def compile_author_scenario(author: AuthorScenario) -> dict[str, Any]:
    """Compile a validated AuthorScenario into the ResolvedScenario document."""
    problems: list[str] = []

    resolved_phases = _resolve_phases(author, problems)
    phase_by_id = {phase["id"]: phase for phase in resolved_phases}

    _check_references(author, problems)
    resolved_ports = _resolve_ports(author, phase_by_id, problems)
    resolved_flows = _resolve_flows(author, problems)
    resolved_metrics = _resolve_metrics(author, phase_by_id, problems)
    _check_visibility(author, problems)

    if problems:
        raise CompilationError(problems)

    resolved: dict[str, Any] = {
        "spec": SPEC,
        "compiler_version": COMPILER_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "scenario": {
            "id": author.scenario.id,
            "version": author.scenario.version,
            "title": author.scenario.title,
        },
        "factorio": {
            "version": author.factorio.version.model_dump(exclude_none=True),
            "baseline_save": author.factorio.baseline_save,
            "required_mods": dict(sorted(author.factorio.required_mods.items())),
        },
        "experiment": {
            "time": {
                "game_speed": author.experiment.time.game_speed.model_dump(),
                "pause_policy": author.experiment.time.pause_policy,
            },
            "phases": resolved_phases,
            "total_duration_ticks": resolved_phases[-1]["end_tick"] if resolved_phases else 0,
            "default_seed": author.experiment.seed,
        },
        "zones": {
            zone_id: {
                "surface": zone.surface,
                "area": {
                    "left_top": list(zone.area.left_top),
                    "right_bottom": list(zone.area.right_bottom),
                },
            }
            for zone_id, zone in sorted(author.zones.items())
        },
        "systems": {
            system_id: {
                "primary_zone": system.primary_zone,
                "boundary_integrity": system.boundary_integrity,
            }
            for system_id, system in sorted(author.systems.items())
        },
        "entity_sets": {
            set_id: entity_set.model_dump()
            for set_id, entity_set in sorted(author.entity_sets.items())
        },
        "ports": resolved_ports,
        "flows": resolved_flows,
        "metrics": resolved_metrics,
        "visibility": author.visibility.model_dump(),
        "observation_plan": _build_observation_plan(author, resolved_metrics),
    }
    return resolved


def resolved_hash(resolved: dict[str, Any]) -> str:
    return document_hash(resolved)


def resolved_bytes(resolved: dict[str, Any]) -> bytes:
    return canonical_json_bytes(resolved)


# --- internal helpers -------------------------------------------------------


def _resolve_phases(author: AuthorScenario, problems: list[str]) -> list[dict[str, Any]]:
    phases = []
    cursor = 0
    for phase in author.experiment.phases:
        try:
            duration = parse_duration_ticks(phase.duration)
        except UnitError as exc:
            problems.append(f"experiment.phases[{phase.id}]: {exc}")
            continue
        phases.append(
            {
                "id": phase.id,
                "duration_ticks": duration,
                "start_tick": cursor,
                "end_tick": cursor + duration,
            }
        )
        cursor += duration
    return phases


def _check_references(author: AuthorScenario, problems: list[str]) -> None:
    for system_id, system in author.systems.items():
        if system.primary_zone not in author.zones:
            problems.append(f"systems.{system_id}: unknown primary_zone {system.primary_zone!r}")
    for set_id, entity_set in author.entity_sets.items():
        if entity_set.zone not in author.zones:
            problems.append(f"entity_sets.{set_id}: unknown zone {entity_set.zone!r}")
    for port_id, port in author.ports.items():
        if port.system not in author.systems:
            problems.append(f"ports.{port_id}: unknown system {port.system!r}")


def _resolve_ports(
    author: AuthorScenario, phase_by_id: dict[str, Any], problems: list[str]
) -> dict[str, Any]:
    resolved = {}
    for port_id, port in sorted(author.ports.items()):
        entry: dict[str, Any] = {
            "system": port.system,
            "direction": port.direction,
            "binding": {
                "surface": port.binding.surface,
                "position": list(port.binding.position),
                "prototype": port.binding.prototype,
            },
            "material": {"item": port.material.item, "quality": port.material.quality},
        }
        if port.supply is not None:
            supply: dict[str, Any] = {"mode": port.supply.mode}
            active = port.supply.active_phases
            if active is not None:
                unknown = [p for p in active if p not in phase_by_id]
                if unknown:
                    problems.append(f"ports.{port_id}.supply.active_phases: unknown phases {unknown}")
                supply["active_phases"] = active
            else:
                supply["active_phases"] = [p["id"] for p in phase_by_id.values()]
            if isinstance(port.supply, ScheduledSupply):
                try:
                    rate = parse_rate(port.supply.schedule.rate)
                    supply["schedule"] = {
                        "type": "constant",
                        "quantity": rate.quantity,
                        "period_ticks": rate.period_ticks,
                    }
                except UnitError as exc:
                    problems.append(f"ports.{port_id}.supply.schedule.rate: {exc}")
                supply["initial_quantity"] = port.supply.initial_quantity
                capacity = port.supply.external_buffer.capacity
                supply["external_buffer"] = (
                    {"kind": "unbounded"} if capacity == "unbounded" else {"kind": "finite", "quantity": capacity}
                )
            else:
                supply["target"] = port.supply.target
            entry["supply"] = supply
        if port.demand is not None:
            demand: dict[str, Any] = {
                "id": port.demand.id,
                "shortage_policy": port.demand.shortage_policy,
                "allocation": port.demand.allocation,
            }
            try:
                rate = parse_rate(port.demand.schedule.rate)
                demand["schedule"] = {
                    "type": "constant",
                    "quantity": rate.quantity,
                    "period_ticks": rate.period_ticks,
                }
            except UnitError as exc:
                problems.append(f"ports.{port_id}.demand.schedule.rate: {exc}")
            active = port.demand.active_phases
            if active is not None:
                unknown = [p for p in active if p not in phase_by_id]
                if unknown:
                    problems.append(f"ports.{port_id}.demand.active_phases: unknown phases {unknown}")
                demand["active_phases"] = active
            else:
                demand["active_phases"] = [p["id"] for p in phase_by_id.values()]
            entry["demand"] = demand
        resolved[port_id] = entry
    demand_ids: dict[str, str] = {}
    for port_id, entry in resolved.items():
        demand = entry.get("demand")
        if demand:
            if demand["id"] in demand_ids:
                problems.append(
                    f"ports.{port_id}.demand: id {demand['id']!r} already used by "
                    f"port {demand_ids[demand['id']]!r} — demand processes are distinct (ADR 0008 §18)"
                )
            demand_ids[demand["id"]] = port_id
    return resolved


def _resolve_flows(author: AuthorScenario, problems: list[str]) -> dict[str, Any]:
    resolved = {}
    for flow_id, flow in sorted(author.flows.items()):
        if flow.system not in author.systems:
            problems.append(f"flows.{flow_id}: unknown system {flow.system!r}")
        for role, port_ids, want_direction in (
            ("entry_ports", flow.entry_ports, "source"),
            ("completion_ports", flow.completion_ports, "sink"),
            ("loss_ports", flow.loss_ports, "sink"),
        ):
            for port_id in port_ids:
                port = author.ports.get(port_id)
                if port is None:
                    problems.append(f"flows.{flow_id}.{role}: unknown port {port_id!r}")
                    continue
                if port.direction != want_direction:
                    problems.append(
                        f"flows.{flow_id}.{role}: port {port_id!r} has direction "
                        f"{port.direction!r}, expected {want_direction!r}"
                    )
                if port.system != flow.system:
                    problems.append(
                        f"flows.{flow_id}.{role}: port {port_id!r} belongs to system "
                        f"{port.system!r}, flow declares {flow.system!r}"
                    )
                if port.material.item not in flow.basis.materials:
                    problems.append(
                        f"flows.{flow_id}.{role}: port {port_id!r} material "
                        f"{port.material.item!r} has no work-unit mapping in the flow basis"
                    )
        resolved[flow_id] = {
            "system": flow.system,
            "unit": flow.unit,
            "basis": {
                "type": flow.basis.type,
                "materials": dict(sorted(flow.basis.materials.items())),
            },
            "entry_ports": flow.entry_ports,
            "completion_ports": flow.completion_ports,
            "loss_ports": flow.loss_ports,
        }
    return resolved


def _resolve_metrics(
    author: AuthorScenario, phase_by_id: dict[str, Any], problems: list[str]
) -> dict[str, Any]:
    resolved: dict[str, Any] = {}
    demand_ports = {
        port.demand.id: port_id
        for port_id, port in author.ports.items()
        if port.demand is not None
    }

    def window_for(metric_id: str, window) -> dict[str, int] | None:
        phase = phase_by_id.get(window.phase)
        if phase is None:
            problems.append(f"metrics.{metric_id}.window: unknown phase {window.phase!r}")
            return None
        return {"phase": window.phase, "start_tick": phase["start_tick"], "end_tick": phase["end_tick"]}

    def demand_service_base(metric_id: str, metric) -> dict[str, Any] | None:
        """Shared resolution for demand-cohort service metrics: demand ref,
        cohort window, observation horizon."""
        if metric.demand not in demand_ports:
            problems.append(f"metrics.{metric_id}: unknown demand process {metric.demand!r}")
            return None
        window = window_for(metric_id, metric.cohort_window)
        if window is None:
            return None
        horizon_phase = phase_by_id.get(metric.observation_horizon.through_phase)
        if horizon_phase is None:
            problems.append(
                f"metrics.{metric_id}.observation_horizon: unknown phase "
                f"{metric.observation_horizon.through_phase!r}"
            )
            return None
        return {
            "demand": metric.demand,
            "port": demand_ports[metric.demand],
            "cohort_window": window,
            "observation_horizon": {
                "through_phase": metric.observation_horizon.through_phase,
                "end_tick": horizon_phase["end_tick"],
            },
        }

    for metric_id, metric in sorted(author.metrics.items()):
        if isinstance(metric, WipMetric):
            if metric.flow not in author.flows:
                problems.append(f"metrics.{metric_id}: unknown flow {metric.flow!r}")
                continue
            census = metric.validation.physical_census
            try:
                cadence = parse_duration_ticks(census.every)
            except UnitError as exc:
                problems.append(f"metrics.{metric_id}.validation.physical_census.every: {exc}")
                continue
            resolved[metric_id] = {
                "type": "wip",
                "flow": metric.flow,
                "method": "conservation_ledger",
                "validation": {
                    "physical_census": {
                        "required": census.required,
                        "every_ticks": cadence,
                        "discrepancy_tolerance": census.discrepancy_tolerance,
                        "include_player_inventory": census.include_player_inventory,
                    }
                },
            }
        elif isinstance(metric, CurrentValueMetric):
            resolved[metric_id] = {"type": "current_value", "source": metric.source}
        elif isinstance(metric, AggregateMetric):
            window = window_for(metric_id, metric.window)
            if window is None:
                continue
            resolved[metric_id] = {
                "type": "aggregate",
                "source": metric.source,
                "aggregation": metric.aggregation,
                "window": window,
            }
        elif isinstance(metric, ThroughputMetric):
            if metric.flow not in author.flows:
                problems.append(f"metrics.{metric_id}: unknown flow {metric.flow!r}")
                continue
            window = window_for(metric_id, metric.window)
            if window is None:
                continue
            resolved[metric_id] = {
                "type": "throughput",
                "flow": metric.flow,
                "window": window,
                # Key present only for the non-default boundary so scenarios
                # predating it keep their resolved hash (comparability).
                **({"boundary": "entry"} if metric.boundary == "entry" else {}),
                **({"display_unit": metric.display_unit} if metric.display_unit else {}),
            }
        elif isinstance(metric, CycleTimeMetric):
            resolved[metric_id] = {
                "type": "cycle_time",
                "flow": metric.flow,
                "method": "little_law_derived",
                "wip_metric": metric.wip_metric,
                "throughput_metric": metric.throughput_metric,
                "interpretation": metric.interpretation,
            }
        elif isinstance(metric, ProductionStateMetric):
            if metric.entities not in author.entity_sets:
                problems.append(f"metrics.{metric_id}: unknown entity_set {metric.entities!r}")
                continue
            resolved[metric_id] = {
                "type": "production_state",
                "entities": metric.entities,
                "adapter": metric.adapter,
                "activity": {
                    "method": metric.activity.method,
                    "cadence": metric.activity.cadence,
                },
                "classification": {"profile": metric.classification.profile},
                # ADR 0016 dynamic membership: the READY scan seeds the
                # roster; additions/removals take effect at canonical
                # checkpoint boundaries. Semantically load-bearing, so it is
                # part of the resolved document (and the hash).
                "membership_resolution": "dynamic_boundary",
            }
        elif isinstance(metric, StateFractionMetric):
            window = window_for(metric_id, metric.window)
            if window is None:
                continue
            resolved[metric_id] = {
                "type": "state_fraction",
                "source": metric.source,
                "state": metric.state,
                "entity_aggregation": metric.entity_aggregation,
                "denominator": metric.denominator,
                "window": window,
            }
        elif isinstance(metric, OnTimeItemRateMetric):
            base = demand_service_base(metric_id, metric)
            if base is None:
                continue
            try:
                max_wait = parse_duration_ticks(metric.max_wait)
            except UnitError as exc:
                problems.append(f"metrics.{metric_id}.max_wait: {exc}")
                continue
            if max_wait < 1:
                problems.append(
                    f"metrics.{metric_id}.max_wait: must be >= 1 tick — port-backed demand "
                    "cannot be fulfilled before the next settlement boundary (ADR 0008 §7)"
                )
                continue
            # The direct deadline property (ADR 0008 §9-§10 / schema §13.8):
            # the latest selected cohort is created at cohort_end - 1; its
            # deadline must be observable, or the reported rate would be
            # censored by construction.
            latest_deadline = (base["cohort_window"]["end_tick"] - 1) + max_wait
            horizon_end = base["observation_horizon"]["end_tick"]
            if horizon_end < latest_deadline:
                problems.append(
                    f"metrics.{metric_id}: observation horizon ends at tick {horizon_end} but the "
                    f"latest selected cohort's deadline is tick {latest_deadline}; extend the "
                    "horizon phase (e.g. a service_tail) so every reported deadline is observed"
                )
                continue
            resolved[metric_id] = {
                "type": "on_time_item_rate",
                **base,
                "max_wait_ticks": max_wait,
            }
        elif isinstance(metric, DemandWaitPercentileMetric):
            base = demand_service_base(metric_id, metric)
            if base is None:
                continue
            resolved[metric_id] = {
                "type": "demand_wait_percentile",
                **base,
                "p": metric.p,
                "weighting": metric.weighting,
                "quantile_method": metric.quantile_method,
            }
        else:  # pragma: no cover - exhaustiveness guard
            problems.append(f"metrics.{metric_id}: unsupported metric type")

    # Second pass: source references and Little's-Law compatibility (ADR 0009
    # §7, ADR 0010 §26, FR-SCHEMA-005).
    for metric_id, metric in sorted(author.metrics.items()):
        if isinstance(metric, (CurrentValueMetric, AggregateMetric)):
            source = author.metrics.get(metric.source)
            if source is None:
                problems.append(f"metrics.{metric_id}: unknown source metric {metric.source!r}")
            elif not isinstance(source, WipMetric):
                problems.append(
                    f"metrics.{metric_id}: source {metric.source!r} must be a point-state "
                    "metric (wip) in the POC"
                )
        if isinstance(metric, StateFractionMetric):
            source = author.metrics.get(metric.source)
            if source is None:
                problems.append(f"metrics.{metric_id}: unknown source metric {metric.source!r}")
            elif not isinstance(source, ProductionStateMetric):
                problems.append(
                    f"metrics.{metric_id}: source {metric.source!r} must be a "
                    "production_state metric"
                )
        if isinstance(metric, CycleTimeMetric):
            wip = author.metrics.get(metric.wip_metric)
            throughput = author.metrics.get(metric.throughput_metric)
            if not isinstance(wip, AggregateMetric) or wip.aggregation != "time_mean":
                problems.append(
                    f"metrics.{metric_id}: wip_metric {metric.wip_metric!r} must be an "
                    "aggregate time_mean of a ledger wip metric"
                )
            if not isinstance(throughput, ThroughputMetric):
                problems.append(
                    f"metrics.{metric_id}: throughput_metric {metric.throughput_metric!r} "
                    "must be a throughput metric"
                )
            elif throughput.boundary != "completion":
                problems.append(
                    f"metrics.{metric_id}: Little's-Law throughput must be measured at the "
                    "completion boundary; entry-boundary admission rate is not system throughput"
                )
            if isinstance(wip, AggregateMetric) and isinstance(throughput, ThroughputMetric):
                wip_source = author.metrics.get(wip.source)
                if isinstance(wip_source, WipMetric) and wip_source.flow != metric.flow:
                    problems.append(
                        f"metrics.{metric_id}: WIP flow {wip_source.flow!r} does not match "
                        f"cycle-time flow {metric.flow!r}"
                    )
                if throughput.flow != metric.flow:
                    problems.append(
                        f"metrics.{metric_id}: throughput flow {throughput.flow!r} does not "
                        f"match cycle-time flow {metric.flow!r}"
                    )
                if wip.window.phase != throughput.window.phase:
                    problems.append(
                        f"metrics.{metric_id}: Little's-Law inputs use different windows "
                        f"({wip.window.phase!r} vs {throughput.window.phase!r}); ADR 0010 §26 "
                        "forbids combining unlike windows"
                    )
    return resolved


def _check_visibility(author: AuthorScenario, problems: list[str]) -> None:
    for audience_name in ("learner_live", "learner_post_run", "instructor"):
        audience = getattr(author.visibility, audience_name)
        for metric_id in audience.metrics:
            if metric_id not in author.metrics:
                problems.append(f"visibility.{audience_name}: unknown metric {metric_id!r}")
        if audience.objectives:
            problems.append(
                f"visibility.{audience_name}: objectives are deferred by Issue #2 and "
                "cannot be referenced yet"
            )


def _build_observation_plan(author: AuthorScenario, resolved_metrics: dict[str, Any]) -> dict[str, Any]:
    """Dependency closure of primitive instrumentation (schema §19), POC subset."""
    plan: dict[str, Any] = {
        "ports": sorted(author.ports.keys()),
        "ledgers": [],
        "census": [],
    }
    for port_id, port in sorted(author.ports.items()):
        if port.demand is not None:
            # Key added only when present so scenarios without demand keep
            # their existing resolved hash (comparability).
            plan.setdefault("demand", []).append(
                {"demand": port.demand.id, "port": port_id, "allocation": port.demand.allocation}
            )
    for metric_id, metric in resolved_metrics.items():
        if metric["type"] == "production_state":
            # Key added only when present so scenarios without machine-state
            # metrics keep their existing resolved hash (comparability).
            plan.setdefault("machine_state", []).append(
                {
                    "metric": metric_id,
                    "entity_set": metric["entities"],
                    "adapter": metric["adapter"],
                    "activity_method": metric["activity"]["method"],
                    "cadence": metric["activity"]["cadence"],
                    "classification_profile": metric["classification"]["profile"],
                    "membership_resolution": metric["membership_resolution"],
                }
            )
        if metric["type"] == "wip":
            plan["ledgers"].append({"metric": metric_id, "flow": metric["flow"]})
            census = metric["validation"]["physical_census"]
            if census["required"]:
                plan["census"].append(
                    {
                        "metric": metric_id,
                        "flow": metric["flow"],
                        "every_ticks": census["every_ticks"],
                        "discrepancy_tolerance": census["discrepancy_tolerance"],
                        "include_player_inventory": census["include_player_inventory"],
                    }
                )
    return plan
