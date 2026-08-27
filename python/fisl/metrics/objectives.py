"""Objective evaluation (ADR 0012): requirements pass/fail/undetermined,
preferences report direction + value, overall status is conjunction over
requirements only. Evaluation uses final authoritative metric results (§9);
incomplete/censored/no-data metrics yield UNDETERMINED, never a fabricated
outcome (§7); there is no weighted score of any kind (§5)."""

from __future__ import annotations

from typing import Any

# metric type -> (value key, canonical unit) matching the compiler's
# _OBJECTIVE_UNITS table.
_VALUE_KEYS = {
    "on_time_item_rate": ("value", "fraction"),
    "state_fraction": ("value", "fraction"),
    "supply_loss": ("value", "fraction"),
    "throughput": ("value_per_minute", "per_minute"),
    "aggregate": ("value", "work_units"),
    "cycle_time": ("value_seconds", "seconds"),
    "demand_wait_percentile": ("value_seconds", "seconds"),
}


def comparable_value(metric_result: dict) -> tuple[float | None, bool]:
    """(value in the metric's canonical unit, measurement complete)."""
    spec = _VALUE_KEYS.get(metric_result.get("type"))
    if spec is None:
        return None, False
    value = metric_result.get(spec[0])
    complete = bool(metric_result.get("coverage_complete")) and value is not None
    return (float(value) if value is not None else None), complete


def evaluate_objectives(resolved: dict, metrics_out: dict) -> dict[str, Any] | None:
    """Evaluate the resolved objectives against final metric results.

    Returns None when the scenario declares no objectives. Each objective
    result carries full provenance (§10): the rule, the metric value/unit,
    the status, and why an UNDETERMINED is undetermined. Protocol validity
    is deliberately NOT consulted here — it stays a separate axis (§8).
    """
    objectives = resolved.get("objectives")
    if not objectives:
        return None

    results: dict[str, Any] = {}
    requirement_statuses: list[str] = []
    for objective_id, objective in objectives.items():
        metric_result = metrics_out.get(objective["metric"], {})
        value, complete = comparable_value(metric_result)
        entry: dict[str, Any] = {
            "type": objective["type"],
            "metric": objective["metric"],
            "unit": objective["unit"],
            "value": value,
            "measurement_complete": complete,
        }
        if objective["type"] == "requirement":
            entry["rule"] = {
                key: objective[key] for key in ("minimum", "maximum") if key in objective
            }
            if value is None or not complete:
                entry["status"] = "UNDETERMINED"
                entry["reason"] = (
                    "metric has no value" if value is None
                    else "metric measurement incomplete under strict coverage"
                )
            else:
                passed = True
                if "minimum" in objective and value < objective["minimum"]:
                    passed = False
                if "maximum" in objective and value > objective["maximum"]:
                    passed = False
                entry["status"] = "PASS" if passed else "FAIL"
            requirement_statuses.append(entry["status"])
        else:
            entry["direction"] = objective["direction"]
            # A preference does not pass or fail in isolation (§4); its
            # value exists for cross-run comparison among feasible runs (§13).
            entry["status"] = "REPORTED" if (value is not None and complete) else "UNDETERMINED"
        results[objective_id] = entry

    if not requirement_statuses:
        overall = "no_requirements"
    elif "FAIL" in requirement_statuses:
        overall = "FAIL"
    elif "UNDETERMINED" in requirement_statuses:
        overall = "UNDETERMINED"
    else:
        overall = "PASS"
    return {
        "objectives": results,
        # Conjunction over requirements only (§6): any definite failure
        # fails; otherwise any unresolved leaves the overall undetermined.
        "overall_requirement_status": overall,
    }
