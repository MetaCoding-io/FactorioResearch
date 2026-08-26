"""Authoritative post-run metric recomputation from telemetry
(POST_REVIEW_REVISIONS.md revision 8: Python is the post-run authority; the
Lua streaming summary is cross-verified, never trusted blind).

All arithmetic is exact: integer work-unit quantities, integer tick windows,
Fractions for ratios. Decimal formatting is presentation (ADR 0010 §25).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any

TICKS_PER_MINUTE = 3600


@dataclass
class TelemetryData:
    records: list[dict] = field(default_factory=list)
    completed: bool = False
    aborted: bool = False
    abort_reason: str | None = None
    final_experiment_tick: int | None = None
    lua_summary: dict | None = None

    @classmethod
    def load(cls, path: Path) -> "TelemetryData":
        data = cls()
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                data.records.append(record)
                if record["type"] == "experiment_completed":
                    data.completed = True
                    data.final_experiment_tick = record.get("experiment_tick")
                    data.lua_summary = record.get("summary")
                elif record["type"] == "experiment_aborted":
                    data.aborted = True
                    data.abort_reason = record.get("reason")
                    data.lua_summary = record.get("summary")
        return data

    def of_type(self, record_type: str) -> list[dict]:
        return [r for r in self.records if r["type"] == record_type]


def ledger_trajectory(data: TelemetryData, flow_id: str) -> list[tuple[int, int]]:
    """Return [(boundary_tick, wip_after_boundary)] change points, starting at
    (0, initial_wip). WIP(T) is the value of the last change point <= T."""
    initial = 0
    for record in data.of_type("initial_census"):
        if record["flow"] == flow_id:
            initial = record["wip"]
    changes: dict[int, int] = {}
    for record in data.of_type("ledger_transaction"):
        if record["flow"] == flow_id:
            delta = record.get("admitted", 0) - record.get("completed", 0)
            tick = record["interval_end_tick"]
            changes[tick] = changes.get(tick, 0) + delta
    trajectory = [(0, initial)]
    wip = initial
    for tick in sorted(changes):
        wip += changes[tick]
        if tick == trajectory[-1][0]:
            trajectory[-1] = (tick, wip)
        else:
            trajectory.append((tick, wip))
    return trajectory


def wip_area(trajectory: list[tuple[int, int]], start_tick: int, end_tick: int) -> int:
    """Exact sum of WIP(T) for T in [start_tick, end_tick) — ADR 0010 §5."""
    area = 0
    for index, (tick, wip) in enumerate(trajectory):
        next_tick = trajectory[index + 1][0] if index + 1 < len(trajectory) else end_tick
        lo = max(tick, start_tick)
        hi = min(next_tick, end_tick)
        if hi > lo:
            area += wip * (hi - lo)
    return area


def wip_min_max(trajectory: list[tuple[int, int]], start_tick: int, end_tick: int) -> tuple[int | None, int | None]:
    lo_value = None
    hi_value = None
    for index, (tick, wip) in enumerate(trajectory):
        next_tick = trajectory[index + 1][0] if index + 1 < len(trajectory) else end_tick
        if max(tick, start_tick) < min(next_tick, end_tick):
            lo_value = wip if lo_value is None else min(lo_value, wip)
            hi_value = wip if hi_value is None else max(hi_value, wip)
    return lo_value, hi_value


def completed_work(data: TelemetryData, resolved: dict, flow_id: str, start_tick: int, end_tick: int) -> int:
    return _boundary_work(data, resolved, flow_id, start_tick, end_tick,
                          record_type="sink_delivery", port_role="completion_ports")


def admitted_work(data: TelemetryData, resolved: dict, flow_id: str, start_tick: int, end_tick: int) -> int:
    """Entry-boundary flow (ADR 0006): work-units withdrawn through the
    flow's entry ports — the admission rate numerator."""
    return _boundary_work(data, resolved, flow_id, start_tick, end_tick,
                          record_type="source_withdrawal", port_role="entry_ports")


def _boundary_work(data: TelemetryData, resolved: dict, flow_id: str, start_tick: int,
                   end_tick: int, *, record_type: str, port_role: str) -> int:
    flow = resolved["flows"][flow_id]
    boundary_ports = set(flow[port_role])
    total = 0
    for record in data.of_type(record_type):
        if record["port"] in boundary_ports and start_tick <= record["interval_start_tick"] < end_tick:
            item = resolved["ports"][record["port"]]["material"]["item"]
            coefficient = flow["basis"]["materials"].get(item, 0)
            total += record["quantity"] * coefficient
    return total


def machine_state_membership(data: TelemetryData, metric_id: str) -> dict | None:
    """The static-at-READY roster record for one production_state metric."""
    membership = None
    for record in data.of_type("machine_state_membership"):
        if record["metric"] == metric_id:
            membership = record
    return membership


def machine_state_spans(data: TelemetryData, metric_id: str) -> list[dict]:
    return [r for r in data.of_type("machine_state_span") if r["metric"] == metric_id]


def machine_eligibility(data: TelemetryData, metric_id: str) -> tuple[dict, dict]:
    """Machine identities and eligibility intervals (ADR 0016 §5) for one
    production_state metric: the READY roster (eligible from tick 0) plus
    boundary membership changes. Returns (machines, intervals) keyed by
    unit_number string; an interval is (start, end) with end=None meaning
    "member through the end of observation" — callers clip to their own
    horizon. A removal boundary is a legitimate denominator end (§6); a
    still-member machine's interval never shrinks for missing data."""
    machines: dict[str, dict] = {}
    intervals: dict[str, list] = {}
    membership = machine_state_membership(data, metric_id)
    if membership:
        for machine in membership["machines"]:
            unit = str(machine["unit_number"])
            machines[unit] = machine
            intervals[unit] = [0, None]
    for record in data.of_type("machine_state_membership_change"):
        if record["metric"] != metric_id:
            continue
        unit = str(record["unit_number"])
        if record["change"] == "added":
            machines.setdefault(
                unit,
                {
                    "unit_number": record["unit_number"],
                    "prototype": record.get("prototype"),
                    "position": record.get("position"),
                },
            )
            intervals[unit] = [record["boundary_tick"], None]
        elif record["change"] == "removed" and unit in intervals:
            intervals[unit][1] = record["boundary_tick"]
    return machines, {unit: (lo, hi) for unit, (lo, hi) in intervals.items()}


def eligible_ticks(interval: tuple[int, int | None], lo: int, hi: int) -> int:
    """Machine-ticks of one eligibility interval inside [lo, hi)."""
    start, end = interval
    end = hi if end is None else min(end, hi)
    return max(0, end - max(start, lo))


def state_ticks_in_window(spans: list[dict], start_tick: int, end_tick: int) -> dict[str, dict[str, int]]:
    """Clip classified spans to [start_tick, end_tick) and pool machine-ticks
    by headline, per machine. `coverage_missing` stays a separate bucket —
    it is missing measurement, never a state (ADR 0007 §24)."""
    per_machine: dict[str, dict[str, int]] = {}
    for span in spans:
        lo = max(span["from_tick"], start_tick)
        hi = min(span["to_tick"], end_tick)
        if hi > lo:
            ticks_by_state = per_machine.setdefault(str(span["unit_number"]), {})
            ticks_by_state[span["headline"]] = ticks_by_state.get(span["headline"], 0) + (hi - lo)
    return per_machine


def _pool_states(per_machine: dict[str, dict[str, int]]) -> tuple[dict[str, int], int, int]:
    """Returns (pooled headline->machine_ticks, classified ticks, covered
    ticks incl. coverage_missing spans)."""
    pooled: dict[str, int] = {}
    classified = 0
    covered = 0
    for ticks_by_state in per_machine.values():
        for headline, ticks in ticks_by_state.items():
            pooled[headline] = pooled.get(headline, 0) + ticks
            covered += ticks
            if headline != "coverage_missing":
                classified += ticks
    return pooled, classified, covered


def census_validity(data: TelemetryData, start_tick: int, end_tick: int) -> dict:
    """Strict WIP validity over a window under ADR 0017 §9: any conservative
    discrepancy interval overlapping the window flags it."""
    overlapping = []
    for record in data.of_type("wip_census_discrepancy"):
        lo, hi = record["suspect_from_tick"], record["suspect_to_tick"]
        if lo < end_tick and hi > start_tick:
            overlapping.append({"from_tick": lo, "to_tick": hi, "discrepancy": record["discrepancy"]})
    checks = [r for r in data.of_type("wip_census") if start_tick <= r["experiment_tick"] < end_tick]
    return {
        "census_checks_in_window": len(checks),
        "discrepancy_intervals": overlapping,
        "valid": not overlapping,
    }


def compute_summary(resolved: dict, run_config: dict, telemetry_path: Path) -> dict:
    data = TelemetryData.load(telemetry_path)
    metrics_out: dict[str, Any] = {}

    trajectories: dict[str, list[tuple[int, int]]] = {}

    def trajectory_for(flow_id: str) -> list[tuple[int, int]]:
        if flow_id not in trajectories:
            trajectories[flow_id] = ledger_trajectory(data, flow_id)
        return trajectories[flow_id]

    def window_complete(end_tick: int) -> bool:
        return data.completed and (data.final_experiment_tick or 0) >= end_tick

    resolved_metrics = resolved["metrics"]
    for metric_id, metric in resolved_metrics.items():
        if metric["type"] == "wip":
            flow_id = metric["flow"]
            trajectory = trajectory_for(flow_id)
            metrics_out[metric_id] = {
                "type": "wip",
                "method": "conservation_ledger",
                "flow": flow_id,
                "final_wip": trajectory[-1][1],
                "change_points": len(trajectory),
            }
        elif metric["type"] == "aggregate":
            source = resolved_metrics[metric["source"]]
            flow_id = source["flow"]
            window = metric["window"]
            start_tick, end_tick = window["start_tick"], window["end_tick"]
            trajectory = trajectory_for(flow_id)
            area = wip_area(trajectory, start_tick, end_tick)
            ticks = end_tick - start_tick
            validity = census_validity(data, start_tick, end_tick)
            entry: dict[str, Any] = {
                "type": "aggregate",
                "aggregation": metric["aggregation"],
                "source": metric["source"],
                "window": window,
                "coverage_complete": window_complete(end_tick),
                "census_validity": validity,
            }
            if metric["aggregation"] == "time_integral":
                entry.update({"value": area, "unit": "work-unit-ticks", "exact": {"numerator": area, "denominator": 1}})
            elif metric["aggregation"] == "time_mean":
                mean = Fraction(area, ticks)
                entry.update(
                    {
                        "value": float(mean),
                        "unit": "work units",
                        "exact": {"numerator": area, "denominator": ticks},
                        "area_work_unit_ticks": area,
                        "window_ticks": ticks,
                    }
                )
            else:
                lo, hi = wip_min_max(trajectory, start_tick, end_tick)
                entry.update({"value": lo if metric["aggregation"] == "min" else hi, "unit": "work units"})
            metrics_out[metric_id] = entry
        elif metric["type"] == "throughput":
            flow_id = metric["flow"]
            window = metric["window"]
            start_tick, end_tick = window["start_tick"], window["end_tick"]
            boundary = metric.get("boundary", "completion")
            if boundary == "entry":
                completed = admitted_work(data, resolved, flow_id, start_tick, end_tick)
                method = "entry_source_withdrawal"
            else:
                completed = completed_work(data, resolved, flow_id, start_tick, end_tick)
                method = "completion_sink_delivery"
            ticks = end_tick - start_tick
            per_minute = Fraction(completed * TICKS_PER_MINUTE, ticks)
            metrics_out[metric_id] = {
                "type": "throughput",
                "flow": flow_id,
                "window": window,
                "boundary": boundary,
                "method": method,
                "completed_quantity": completed,
                "window_ticks": ticks,
                "value_per_minute": float(per_minute),
                "exact_per_minute": {"numerator": per_minute.numerator, "denominator": per_minute.denominator},
                "coverage_complete": window_complete(end_tick),
            }
        elif metric["type"] == "cycle_time":
            pass  # second pass below; depends on other metric results
        elif metric["type"] == "current_value":
            metrics_out[metric_id] = {"type": "current_value", "source": metric["source"], "note": "live display metric"}
        elif metric["type"] == "production_state":
            membership = machine_state_membership(data, metric_id)
            spans = machine_state_spans(data, metric_id)
            machines, intervals = machine_eligibility(data, metric_id)
            final_tick = data.final_experiment_tick or max((s["to_tick"] for s in spans), default=0)
            per_machine = state_ticks_in_window(spans, 0, final_tick) if final_tick else {}
            pooled, classified, covered = _pool_states(per_machine)
            eligible = {
                unit: eligible_ticks(interval, 0, final_tick)
                for unit, interval in intervals.items()
            }
            metrics_out[metric_id] = {
                "type": "production_state",
                "adapter": membership["adapter"] if membership else None,
                "classifier_version": membership["classifier_version"] if membership else None,
                "membership_resolution": metric["membership_resolution"],
                "entity_set": metric["entities"],
                "machine_count": len(machines),
                "machines": [machines[unit] for unit in sorted(machines)],
                "eligibility": {
                    unit: {"from_tick": lo, "to_tick": hi if hi is not None else final_tick}
                    for unit, (lo, hi) in sorted(intervals.items())
                },
                "eligible_machine_ticks": sum(eligible.values()),
                "per_machine_eligible_ticks": eligible,
                "run_ticks": final_tick,
                "pooled_state_ticks": pooled,
                "per_machine_state_ticks": per_machine,
                "classified_machine_ticks": classified,
                "covered_machine_ticks": covered,
                "span_count": len(spans),
            }
        elif metric["type"] == "state_fraction":
            spans = machine_state_spans(data, metric["source"])
            _machines, intervals = machine_eligibility(data, metric["source"])
            window = metric["window"]
            start_tick, end_tick = window["start_tick"], window["end_tick"]
            ticks = end_tick - start_tick
            per_machine = state_ticks_in_window(spans, start_tick, end_tick)
            pooled, classified, _covered = _pool_states(per_machine)
            # Pooled ELIGIBLE machine-time over the full window (ADR 0010
            # §11-§12 + ADR 0016 §5-§6): a machine contributes exactly its
            # eligibility ∩ window — a removal legitimately ends its
            # denominator share, no retroactive history for late joiners —
            # but the denominator NEVER shrinks for classification gaps;
            # those stay visible as coverage next to the fraction.
            per_machine_denominator = {
                unit: eligible_ticks(interval, start_tick, end_tick)
                for unit, interval in intervals.items()
            }
            denominator_ticks = sum(per_machine_denominator.values())
            machine_count = sum(1 for value in per_machine_denominator.values() if value > 0)
            state_ticks = pooled.get(metric["state"], 0)
            entry = {
                "type": "state_fraction",
                "source": metric["source"],
                "state": metric["state"],
                "entity_aggregation": metric["entity_aggregation"],
                "denominator": metric["denominator"],
                "window": window,
                "machine_count": machine_count,
                "window_ticks": ticks,
                "denominator_machine_ticks": denominator_ticks,
                "per_machine_denominator_ticks": dict(sorted(per_machine_denominator.items())),
                "state_machine_ticks": state_ticks,
                "classified_machine_ticks": classified,
                "coverage_complete": window_complete(end_tick) and classified == denominator_ticks,
            }
            if denominator_ticks > 0:
                fraction = Fraction(state_ticks, denominator_ticks)
                coverage = Fraction(classified, denominator_ticks)
                entry.update(
                    {
                        "value": float(fraction),
                        "exact": {"numerator": state_ticks, "denominator": denominator_ticks},
                        "coverage_fraction": float(coverage),
                    }
                )
            else:
                entry.update({"value": None, "status": "no_data", "reason": "no machines in entity set"})
            metrics_out[metric_id] = entry

    for metric_id, metric in resolved_metrics.items():
        if metric["type"] != "cycle_time":
            continue
        wip_result = metrics_out.get(metric["wip_metric"])
        throughput_result = metrics_out.get(metric["throughput_metric"])
        entry: dict[str, Any] = {
            "type": "cycle_time",
            "flow": metric["flow"],
            "method": "little_law_derived",
            "measurement_class": "derived",
            "wip_metric": metric["wip_metric"],
            "throughput_metric": metric["throughput_metric"],
        }
        if (
            wip_result
            and throughput_result
            and throughput_result["completed_quantity"] > 0
            and wip_result.get("area_work_unit_ticks") is not None
        ):
            # CT = average_WIP / TH = area / completed (ticks), exactly.
            cycle_ticks = Fraction(wip_result["area_work_unit_ticks"], throughput_result["completed_quantity"])
            entry.update(
                {
                    "value_seconds": float(cycle_ticks / 60),
                    "exact_ticks": {"numerator": cycle_ticks.numerator, "denominator": cycle_ticks.denominator},
                    "coverage_complete": wip_result["coverage_complete"] and throughput_result["coverage_complete"],
                    "census_validity": wip_result["census_validity"],
                }
            )
        else:
            entry.update({"value_seconds": None, "status": "no_data", "reason": "no completed work in window or missing inputs"})
        metrics_out[metric_id] = entry

    validity = {
        "completed": data.completed,
        "aborted": data.aborted,
        "abort_reason": data.abort_reason,
        "protocol_events": _collect_protocol_events(data),
        "manual_carriage_residual": sum(r["quantity"] for r in data.of_type("manual_carriage_residual")),
    }

    verification = _verify_against_lua(data, metrics_out)

    return {
        "run_id": run_config["run_id"],
        "resolved_scenario_hash": run_config["resolved_scenario_hash"],
        "scenario": resolved["scenario"],
        "metrics": metrics_out,
        "validity": validity,
        "lua_cross_verification": verification,
    }


def _collect_protocol_events(data: TelemetryData) -> dict[str, int]:
    counters: dict[str, int] = {}
    for kind in ("source_reverse_flow", "port_contamination", "wip_census_discrepancy",
                 "port_binding_lost", "manual_carriage_residual"):
        count = len(data.of_type(kind))
        if count:
            counters[kind] = count
    return counters


def _verify_against_lua(data: TelemetryData, metrics_out: dict) -> dict:
    """Compare Python-recomputed exact quantities with the Lua streaming
    summary (ADR 0010 §24 / revision 8). Disagreement is a defect flag."""
    if not data.lua_summary:
        return {"available": False}
    mismatches = []
    lua_metrics = data.lua_summary.get("metrics", {})
    for metric_id, ours in metrics_out.items():
        lua_metric = lua_metrics.get(metric_id)
        if not lua_metric:
            continue
        if ours["type"] == "aggregate" and "area_work_unit_ticks" in ours:
            if lua_metric.get("area") != ours["area_work_unit_ticks"]:
                mismatches.append(
                    f"{metric_id}: lua area {lua_metric.get('area')} != python {ours['area_work_unit_ticks']}"
                )
        if ours["type"] == "throughput":
            if lua_metric.get("completed_quantity") != ours["completed_quantity"]:
                mismatches.append(
                    f"{metric_id}: lua completed {lua_metric.get('completed_quantity')} != "
                    f"python {ours['completed_quantity']}"
                )
    lua_machine_state = data.lua_summary.get("machine_state") or {}
    for metric_id, ours in metrics_out.items():
        if ours["type"] != "production_state":
            continue
        lua_entry = lua_machine_state.get(metric_id)
        if not lua_entry:
            continue
        lua_pooled = {k: v for k, v in (lua_entry.get("pooled_state_ticks") or {}).items()}
        python_pooled = {k: v for k, v in ours["pooled_state_ticks"].items() if k != "coverage_missing"}
        lua_pooled["coverage_missing"] = lua_entry.get("coverage_missing_ticks", 0)
        python_pooled["coverage_missing"] = ours["pooled_state_ticks"].get("coverage_missing", 0)
        if lua_pooled != python_pooled:
            mismatches.append(
                f"{metric_id}: lua pooled state ticks {lua_pooled} != python {python_pooled}"
            )
        lua_eligible = lua_entry.get("eligible_machine_ticks")
        if lua_eligible is not None and lua_eligible != ours.get("eligible_machine_ticks"):
            mismatches.append(
                f"{metric_id}: lua eligible machine-ticks {lua_eligible} != "
                f"python {ours.get('eligible_machine_ticks')}"
            )
    return {"available": True, "agrees": not mismatches, "mismatches": mismatches}
