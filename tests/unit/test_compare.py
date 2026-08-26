"""Unit tests for fisl compare (FR-CTRL-008): compatibility, deltas, and
validity flagging against synthetic run directories."""

import json
from pathlib import Path

import pytest
from rich.console import Console

from fisl.report.compare import CompareError, RunRecord, comparison_rows, compatibility, render_comparison


def make_run(tmp_path: Path, name: str, *, avg_wip: float, throughput: float, ct: float,
             resolved_hash: str = "sha256:same", fingerprint: str = "sha256:fp",
             aborted: bool = False) -> Path:
    run_dir = tmp_path / name
    run_dir.mkdir()
    summary = {
        "run_id": name,
        "resolved_scenario_hash": resolved_hash,
        "scenario": {"id": "fp-03-littles-law", "version": "0.1.0"},
        "lifecycle": "ABORTED" if aborted else "COMPLETED",
        "metrics": {
            "average_wip": {
                "type": "aggregate", "aggregation": "time_mean", "value": avg_wip,
                "unit": "work units", "coverage_complete": not aborted,
                "census_validity": {"valid": True, "census_checks_in_window": 600,
                                    "discrepancy_intervals": []},
            },
            "measured_throughput": {
                "type": "throughput", "value_per_minute": throughput,
                "completed_quantity": int(throughput * 10), "window_ticks": 36000,
                "coverage_complete": not aborted,
            },
            "loaded_cycle_time": {
                "type": "cycle_time", "method": "little_law_derived",
                "value_seconds": ct, "coverage_complete": not aborted,
                "census_validity": {"valid": True, "census_checks_in_window": 600,
                                    "discrepancy_intervals": []},
            },
            "current_wip": {"type": "current_value", "source": "line_wip"},
        },
        "validity": {"completed": not aborted, "aborted": aborted,
                     "abort_reason": "learner_disconnected" if aborted else None,
                     "protocol_events": {}, "manual_carriage_residual": 0},
    }
    (run_dir / "summary.json").write_text(json.dumps(summary))
    (run_dir / "manifest.json").write_text(json.dumps({
        "run_id": name, "reproducibility_fingerprint": fingerprint,
    }))
    return run_dir


def test_compatible_pair_with_deltas(tmp_path):
    run_a = RunRecord.load(make_run(tmp_path, "A", avg_wip=51.70, throughput=15.0, ct=206.78))
    run_b = RunRecord.load(make_run(tmp_path, "B", avg_wip=8.2, throughput=15.0, ct=32.8))
    compat = compatibility([run_a, run_b])
    assert compat["same_experiment_semantics"] is True
    assert compat["same_controlled_condition"] is True

    rows = {row["metric"]: row for row in comparison_rows([run_a, run_b])}
    assert "current_wip" not in rows  # live display metric excluded
    assert rows["average_wip"]["delta"] == pytest.approx(8.2 - 51.70)
    assert rows["average_wip"]["delta_pct"] == pytest.approx((8.2 - 51.70) / 51.70 * 100)
    assert rows["measured_throughput"]["delta"] == pytest.approx(0.0)


def test_different_semantics_flagged_not_refused(tmp_path):
    run_a = RunRecord.load(make_run(tmp_path, "A", avg_wip=50, throughput=15, ct=200))
    run_b = RunRecord.load(
        make_run(tmp_path, "B", avg_wip=50, throughput=15, ct=200, resolved_hash="sha256:other")
    )
    compat = compatibility([run_a, run_b])
    assert compat["same_experiment_semantics"] is False
    # rendering still works (loud warning, no exception)
    console = Console(record=True, width=120)
    render_comparison([run_a.run_dir, run_b.run_dir], console)
    output = console.export_text()
    assert "different experiment semantics" in output
    assert "combined score" in output  # no-scalar-score note always shown


def test_aborted_run_validity_surfaces(tmp_path):
    run_a = make_run(tmp_path, "A", avg_wip=50, throughput=15, ct=200)
    run_b = make_run(tmp_path, "B", avg_wip=10, throughput=3, ct=100, aborted=True)
    console = Console(record=True, width=120)
    render_comparison([run_a, run_b], console)
    output = console.export_text()
    assert "aborted: learner_disconnected" in output
    assert "incomplete" in output


def test_single_run_rejected(tmp_path):
    run_a = make_run(tmp_path, "A", avg_wip=50, throughput=15, ct=200)
    with pytest.raises(CompareError):
        render_comparison([run_a], Console(record=True))


def test_missing_summary_rejected(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(CompareError):
        RunRecord.load(empty)
