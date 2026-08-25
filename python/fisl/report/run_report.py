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
        else:
            continue
        table.add_row(metric_id, value, method, exact, validity_text)

    console.print(table)


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
