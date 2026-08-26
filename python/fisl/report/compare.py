"""Side-by-side run comparison (FR-CTRL-008, ADR 0012 §11-§13, ADR 0014 §17).

Runs are compared as vectors of authoritative metric results — never
collapsed into a scalar score. Compatibility is checked from provenance:
identical `resolved_scenario_hash` means the same experiment semantics;
identical reproducibility fingerprints mean the same controlled condition.
Incompatible runs are still displayed, loudly flagged, because preserving
and showing data beats refusing (§ validity model).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.table import Table


class CompareError(Exception):
    pass


@dataclass
class RunRecord:
    run_dir: Path
    run_id: str
    summary: dict
    manifest: dict

    @classmethod
    def load(cls, run_dir: Path) -> "RunRecord":
        summary_path = run_dir / "summary.json"
        manifest_path = run_dir / "manifest.json"
        if not summary_path.exists():
            raise CompareError(f"{run_dir}: no summary.json (run incomplete or not collected)")
        summary = json.loads(summary_path.read_text())
        manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
        return cls(run_dir=run_dir, run_id=summary.get("run_id", run_dir.name),
                   summary=summary, manifest=manifest)


def compatibility(runs: list[RunRecord]) -> dict:
    """Semantic comparability per ADR 0012 §11 / ADR 0014 §17."""
    hashes = {run.summary.get("resolved_scenario_hash") for run in runs}
    fingerprints = {run.manifest.get("reproducibility_fingerprint") for run in runs}
    return {
        "same_experiment_semantics": len(hashes) == 1 and None not in hashes,
        "resolved_hashes": sorted(str(h) for h in hashes),
        "same_controlled_condition": len(fingerprints) == 1 and None not in fingerprints,
    }


def _metric_value(metric: dict) -> tuple[float | None, str]:
    """Comparable numeric value + display string for a metric result."""
    metric_type = metric.get("type")
    if metric_type == "aggregate" and metric.get("aggregation") == "time_mean":
        value = metric.get("value")
        return value, (f"{value:.2f} {metric.get('unit', '')}" if value is not None else "—")
    if metric_type == "aggregate":
        value = metric.get("value")
        return (float(value) if value is not None else None), str(value)
    if metric_type == "throughput":
        value = metric.get("value_per_minute")
        return value, (f"{value:.2f}/min" if value is not None else "—")
    if metric_type == "cycle_time":
        value = metric.get("value_seconds")
        return value, (f"{value:.2f} s" if value is not None else "no data")
    if metric_type == "wip":
        value = metric.get("final_wip")
        return (float(value) if value is not None else None), f"final {value}"
    return None, "—"


def _metric_validity(metric: dict) -> str:
    flags = []
    if metric.get("coverage_complete") is False:
        flags.append("incomplete")
    census = metric.get("census_validity")
    if census is not None and not census.get("valid", True):
        flags.append("census!")
    return " ".join(flags)


def comparison_rows(runs: list[RunRecord]) -> list[dict]:
    """One row per metric shared by all runs, with values and (for exactly
    two runs) absolute/percent deltas on numeric metrics."""
    shared = [
        metric_id
        for metric_id in runs[0].summary.get("metrics", {})
        if all(metric_id in run.summary.get("metrics", {}) for run in runs)
    ]
    rows = []
    for metric_id in shared:
        metrics = [run.summary["metrics"][metric_id] for run in runs]
        if metrics[0].get("type") == "current_value":
            continue  # live display metric; nothing to compare post-run
        values, displays, validities = [], [], []
        for metric in metrics:
            value, display = _metric_value(metric)
            values.append(value)
            displays.append(display)
            validities.append(_metric_validity(metric))
        row: dict = {
            "metric": metric_id,
            "values": values,
            "displays": displays,
            "validities": validities,
        }
        # Deltas relative to run A (the first run) for every later run — this
        # is what makes N-way solution comparisons readable.
        row["deltas_vs_first"] = [
            (value - values[0]) if (value is not None and values[0] is not None) else None
            for value in values
        ]
        row["delta_pcts_vs_first"] = [
            (delta / values[0] * 100.0)
            if (delta is not None and values[0] not in (None, 0))
            else None
            for delta in row["deltas_vs_first"]
        ]
        if len(runs) == 2 and values[0] is not None and values[1] is not None:
            row["delta"] = values[1] - values[0]
            row["delta_pct"] = row["delta_pcts_vs_first"][1]
        rows.append(row)
    return rows


def comparison_to_json(run_dirs: list[Path]) -> dict:
    """Machine-readable comparison (for course chapters, analysis, CI)."""
    runs = [RunRecord.load(run_dir) for run_dir in run_dirs]
    return {
        "scenario": runs[0].summary.get("scenario", {}),
        "compatibility": compatibility(runs),
        "runs": [
            {
                "run_id": run.run_id,
                "lifecycle": run.summary.get("lifecycle"),
                "scripted_intervention": run.manifest.get("scripted_intervention"),
                "validity": run.summary.get("validity", {}),
            }
            for run in runs
        ],
        "metrics": comparison_rows(runs),
    }


def export_comparison_svg(run_dirs: list[Path], svg_path: Path, width: int = 110) -> None:
    """Render the comparison into a crisp SVG (for the course book) — the
    figure regenerates from run data instead of being a hand-taken
    terminal screenshot."""
    recording = Console(record=True, width=width)
    render_comparison(run_dirs, recording)
    recording.save_svg(str(svg_path), title="fisl compare")


def render_comparison(run_dirs: list[Path], console: Console) -> None:
    runs = [RunRecord.load(run_dir) for run_dir in run_dirs]
    if len(runs) < 2:
        raise CompareError("need at least two run directories to compare")

    compat = compatibility(runs)
    scenario = runs[0].summary.get("scenario", {})
    console.print(f"[bold]FISL run comparison[/bold]  ({scenario.get('id')})")
    for index, run in enumerate(runs):
        lifecycle = run.summary.get("lifecycle", "?")
        intervention = run.manifest.get("scripted_intervention")
        suffix = f"  (scripted solution: {intervention['id']})" if intervention else ""
        console.print(f"  run {chr(65 + index)}: {run.run_id}  [{lifecycle}]{suffix}")

    if compat["same_experiment_semantics"]:
        console.print("[green]Same experiment semantics[/green] (identical resolved scenario hash)")
    else:
        console.print(
            "[red]WARNING: different experiment semantics[/red] — these runs did not execute "
            f"the same resolved scenario ({compat['resolved_hashes']}); values are shown but are "
            "not a controlled comparison (ADR 0012 §11)"
        )
    if compat["same_controlled_condition"]:
        console.print("[green]Same controlled condition[/green] (identical reproducibility fingerprint)")
    else:
        console.print(
            "[yellow]Different controlled conditions[/yellow] (seed/software/baseline/profile differ "
            "or fingerprint missing) — differences may not be caused by the learner's design alone"
        )

    for run, letter in zip(runs, "ABCDEFGH"):
        validity = run.summary.get("validity", {})
        problems = []
        if validity.get("aborted"):
            problems.append(f"aborted: {validity.get('abort_reason')}")
        if validity.get("protocol_events"):
            problems.append(f"protocol events {validity['protocol_events']}")
        if validity.get("manual_carriage_residual"):
            problems.append(f"manual carriage residual {validity['manual_carriage_residual']}")
        if problems:
            console.print(f"[yellow]run {letter} validity:[/yellow] {'; '.join(problems)}")

    table = Table(show_header=True)
    table.add_column("Metric")
    for index in range(len(runs)):
        table.add_column(f"Run {chr(65 + index)}")

    for row in comparison_rows(runs):
        cells = [row["metric"]]
        for index, (display, validity) in enumerate(zip(row["displays"], row["validities"])):
            cell = display
            delta_pct = row["delta_pcts_vs_first"][index]
            if index > 0 and delta_pct is not None:
                cell += f"  [dim]({delta_pct:+.1f}% vs A)[/dim]"
            if validity:
                cell += f"  [red]{validity}[/red]"
            cells.append(cell)
        table.add_row(*cells)
    console.print(table)
    console.print(
        "[dim]Metrics are compared as a vector; FISL does not compute a combined score "
        "(ADR 0012 §5/§12).[/dim]"
    )
