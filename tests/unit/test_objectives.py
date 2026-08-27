"""Objective evaluation goldens (ADR 0012): pass/fail/undetermined per
requirement, conjunction overall, preferences as reported values, and the
censored-metric → UNDETERMINED rule (§7 — missing measurement is never a
fabricated outcome)."""

import pytest

from fisl.metrics.objectives import evaluate_objectives

RESOLVED = {
    "objectives": {
        "service_requirement": {
            "type": "requirement", "metric": "customer_service",
            "unit": "fraction", "minimum": 0.95,
        },
        "throughput_band": {
            "type": "requirement", "metric": "measured_throughput",
            "unit": "per_minute", "minimum": 10.0, "maximum": 20.0,
        },
        "minimize_wip": {
            "type": "preference", "metric": "average_wip",
            "unit": "work_units", "direction": "minimize",
        },
    }
}


def metrics(service=1.0, service_complete=True, throughput=15.0, wip=51.7):
    return {
        "customer_service": {
            "type": "on_time_item_rate", "value": service,
            "coverage_complete": service_complete,
        },
        "measured_throughput": {
            "type": "throughput", "value_per_minute": throughput,
            "coverage_complete": True,
        },
        "average_wip": {
            "type": "aggregate", "aggregation": "time_mean", "value": wip,
            "coverage_complete": True,
        },
    }


def test_all_pass_and_preference_reported():
    result = evaluate_objectives(RESOLVED, metrics())
    assert result["overall_requirement_status"] == "PASS"
    assert result["objectives"]["service_requirement"]["status"] == "PASS"
    assert result["objectives"]["throughput_band"]["status"] == "PASS"
    preference = result["objectives"]["minimize_wip"]
    assert preference["status"] == "REPORTED"
    assert preference["direction"] == "minimize"
    assert preference["value"] == pytest.approx(51.7)


def test_requirement_failure_dominates_conjunction():
    result = evaluate_objectives(RESOLVED, metrics(service=0.225))
    assert result["objectives"]["service_requirement"]["status"] == "FAIL"
    assert result["overall_requirement_status"] == "FAIL"
    # The metric value stays visible in the result (ADR 0012 §13).
    assert result["objectives"]["service_requirement"]["value"] == pytest.approx(0.225)


def test_range_requirement_upper_bound():
    result = evaluate_objectives(RESOLVED, metrics(throughput=37.5))
    assert result["objectives"]["throughput_band"]["status"] == "FAIL"


def test_incomplete_metric_is_undetermined_never_failed():
    result = evaluate_objectives(RESOLVED, metrics(service_complete=False))
    entry = result["objectives"]["service_requirement"]
    assert entry["status"] == "UNDETERMINED"
    assert "incomplete" in entry["reason"]
    # No failure anywhere, one unresolved => overall UNDETERMINED (§6).
    assert result["overall_requirement_status"] == "UNDETERMINED"


def test_missing_value_is_undetermined():
    m = metrics()
    m["customer_service"]["value"] = None
    result = evaluate_objectives(RESOLVED, m)
    assert result["objectives"]["service_requirement"]["status"] == "UNDETERMINED"


def test_fail_beats_undetermined_in_conjunction():
    result = evaluate_objectives(
        RESOLVED, metrics(service_complete=False, throughput=50.0)
    )
    assert result["overall_requirement_status"] == "FAIL"


def test_no_objectives_returns_none():
    assert evaluate_objectives({}, metrics()) is None
