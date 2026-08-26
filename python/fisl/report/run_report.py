"""Human-readable run report (FR-CTRL-007): every number carries its method,
window, exact numerator/denominator, and validity state."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table


def render_report(summary: dict, console: Console) -> None:
    scenario = summary.get("scenario", {})
    console.print(
        f"[bold]FISL run report[/bold]  {summary.get('run_id')}  "
        f"({scenario.get('id')} v{scenario.get('version')})"
    )
    console.print(f"Resolved scenario: {summary.get('resolved_scenario_hash')}")
    console.print(f"Lifecycle: {summary.get('lifecycle')}")

    validity = summary.get("validity", {})
    if validity.get("aborted"):
        console.print(f"[red]Aborted:[/red] {validity.get('abort_reason')}")
    if validity.get("protocol_events"):
        console.print(f"[yellow]Protocol events:[/yellow] {validity['protocol_events']}")
    if validity.get("manual_carriage_residual"):
        console.print(
            f"[yellow]manual_carriage_residual:[/yellow] "
            f"{validity['manual_carriage_residual']} work units held by players at end of run"
        )

    verification = summary.get("lua_cross_verification", {})
    if verification.get("available"):
        if verification.get("agrees"):
            console.print("[green]Lua/Python cross-verification: agree[/green]")
        else:
            console.print(f"[red]Lua/Python cross-verification MISMATCH:[/red] {verification['mismatches']}")

    table = Table(show_header=True)
    table.add_column("Metric")
    table.add_column("Value")
    table.add_column("Method / window")
    table.add_column("Exact")
    table.add_column("Validity")

    for metric_id, metric in summary.get("metrics", {}).items():
        metric_type = metric.get("type")
        if metric_type == "aggregate" and metric.get("aggregation") == "time_mean":
            value = f"{metric['value']:.2f} {metric.get('unit', '')}"
            exact = f"{metric['exact']['numerator']}/{metric['exact']['denominator']}"
            window = metric["window"]
            method = f"time_mean over {window['phase']} [{window['start_tick']},{window['end_tick']})"
            validity_text = _validity_text(metric)
        elif metric_type == "throughput":
            value = f"{metric['value_per_minute']:.2f}/min"
            exact = f"{metric['completed_quantity']} units / {metric['window_ticks']} ticks"
            window = metric["window"]
            method = f"{metric['method']} over {window['phase']}"
            validity_text = "complete" if metric.get("coverage_complete") else "[red]incomplete[/red]"
        elif metric_type == "cycle_time":
            if metric.get("value_seconds") is not None:
                value = f"{metric['value_seconds']:.2f} s"
                exact = f"{metric['exact_ticks']['numerator']}/{metric['exact_ticks']['denominator']} ticks"
                validity_text = _validity_text(metric)
            else:
                value = "no data"
                exact = "-"
                validity_text = metric.get("reason", "")
            method = f"{metric['method']} (derived)"
        elif metric_type == "wip":
            value = f"final {metric['final_wip']}"
            exact = "-"
            method = metric["method"]
            validity_text = ""
        elif metric_type == "state_fraction":
            if metric.get("value") is not None:
                value = f"{metric['value'] * 100:.1f}% {metric['state']}"
                exact = f"{metric['exact']['numerator']}/{metric['exact']['denominator']} machine-ticks"
                coverage = metric.get("coverage_fraction")
                validity_text = _validity_text(metric)
                if coverage is not None and coverage < 1:
                    validity_text += f", [yellow]classified coverage {coverage * 100:.1f}%[/yellow]"
            else:
                value = "no data"
                exact = "-"
                validity_text = metric.get("reason", "")
            window = metric["window"]
            method = (
                f"pooled machine-time / full window, {metric['machine_count']} machines "
                f"over {window['phase']}"
            )
        else:
            continue
        table.add_row(metric_id, value, method, exact, validity_text)

    console.print(table)

    for metric_id, metric in summary.get("metrics", {}).items():
        if metric.get("type") == "production_state":
            _render_production_state(metric_id, metric, console)


def _render_production_state(metric_id: str, metric: dict, console: Console) -> None:
    console.print(
        f"\n[bold]{metric_id}[/bold] — classified machine states "
        f"(adapter {metric.get('adapter')}, classifier {metric.get('classifier_version')}, "
        f"membership {metric.get('membership_resolution')})"
    )
    machines = {str(m["unit_number"]): m for m in metric.get("machines", [])}
    eligibility = metric.get("eligibility", {})
    eligible = metric.get("per_machine_eligible_ticks", {})
    run_ticks = metric.get("run_ticks") or 0
    table = Table(show_header=True)
    table.add_column("Machine")
    table.add_column("eligible")
    for headline in ("productive", "starved", "blocked", "unavailable", "disabled",
                     "idle_other", "unclassified", "coverage_missing"):
        table.add_column(headline)
    for unit_number in sorted(machines):
        info = machines.get(unit_number, {})
        ticks_by_state = metric.get("per_machine_state_ticks", {}).get(unit_number, {})
        position = info.get("position") or {}
        label = f"{info.get('prototype', 'machine')} @ ({position.get('x')}, {position.get('y')})"
        interval = eligibility.get(unit_number, {})
        machine_eligible = eligible.get(unit_number, 0)
        if run_ticks and machine_eligible == run_ticks:
            eligible_text = "full run"
        else:
            eligible_text = f"[{interval.get('from_tick')},{interval.get('to_tick')})"
        row = [label, eligible_text]
        for headline in ("productive", "starved", "blocked", "unavailable", "disabled",
                         "idle_other", "unclassified", "coverage_missing"):
            ticks = ticks_by_state.get(headline, 0)
            if ticks and machine_eligible:
                row.append(f"{ticks / machine_eligible * 100:.1f}%")
            else:
                row.append("-" if not ticks else str(ticks))
        table.add_row(*row)
    console.print(table)
    console.print(
        "Cell = share of that machine's ELIGIBLE machine-ticks (ADR 0016: "
        "machines added/removed mid-run count only while members); exact "
        "counts are in summary.json."
    )


def _validity_text(metric: dict) -> str:
    parts = []
    parts.append("complete" if metric.get("coverage_complete") else "[red]incomplete[/red]")
    census = metric.get("census_validity")
    if census is not None:
        if census.get("valid"):
            parts.append(f"census ok ({census['census_checks_in_window']} checks)")
        else:
            parts.append(f"[red]census discrepancy x{len(census['discrepancy_intervals'])}[/red]")
    return ", ".join(parts)
