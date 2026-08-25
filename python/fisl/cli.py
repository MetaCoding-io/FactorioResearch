"""FISL command-line interface.

POC commands (Issue #2): `validate`, `run`, `report`, `retry`.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from fisl.scenario.canonical import file_sha256
from fisl.scenario.compiler import (
    CompilationError,
    compile_author_scenario,
    load_author_yaml,
    resolved_bytes,
    resolved_hash,
)

app = typer.Typer(no_args_is_help=True, add_completion=False)
console = Console()


def _scenario_yaml_path(scenario: Path) -> Path:
    return scenario / "scenario.yaml" if scenario.is_dir() else scenario


@app.command()
def validate(
    scenario: Path = typer.Argument(..., help="Scenario directory or scenario.yaml path"),
    emit_resolved: Path | None = typer.Option(None, help="Write resolved JSON to this path"),
) -> None:
    """Validate/compile a scenario without launching Factorio (FR-CTRL-002)."""
    yaml_path = _scenario_yaml_path(scenario)
    try:
        author = load_author_yaml(yaml_path)
        resolved = compile_author_scenario(author)
    except CompilationError as exc:
        console.print("[red]Scenario invalid[/red]")
        for problem in exc.problems:
            console.print(f"  [red]-[/red] {problem}")
        raise typer.Exit(code=1)

    digest = resolved_hash(resolved)
    console.print(f"[green]Scenario valid[/green]  {resolved['scenario']['id']} v{resolved['scenario']['version']}")

    table = Table(show_header=False, box=None)
    table.add_row("Factorio", f">= {resolved['factorio']['version']['minimum']}")
    baseline = yaml_path.parent / resolved["factorio"]["baseline_save"]
    if baseline.exists():
        table.add_row("Baseline", f"{baseline.name}  {file_sha256(str(baseline))[:23]}…")
    else:
        table.add_row("Baseline", f"[yellow]{baseline} (missing — required before run)[/yellow]")
    for phase in resolved["experiment"]["phases"]:
        table.add_row(
            f"Phase {phase['id']}",
            f"[{phase['start_tick']}, {phase['end_tick']}) = {phase['duration_ticks']} ticks",
        )
    table.add_row("Metrics", str(len(resolved["metrics"])))
    table.add_row("Resolved hash", digest)
    console.print(table)

    if emit_resolved is not None:
        emit_resolved.write_bytes(resolved_bytes(resolved))
        console.print(f"Resolved scenario written to {emit_resolved}")


@app.command()
def run(
    scenario: Path = typer.Argument(..., help="Scenario directory"),
    headless: bool = typer.Option(False, help="Run without a graphical client"),
    factorio: Path | None = typer.Option(None, envvar="FACTORIO_BIN", help="Factorio binary"),
    runs_dir: Path = typer.Option(Path("runs"), help="Run workspace root"),
    run_ticks: int | None = typer.Option(
        None, help="Headless only: execute this many ticks then finish (defaults to full experiment)"
    ),
) -> None:
    """Compile, launch a local Factorio server, execute a run, collect artifacts."""
    from fisl.controller.run import RunError, execute_run

    try:
        result = execute_run(
            scenario_dir=_scenario_yaml_path(scenario).parent,
            headless=headless,
            factorio_bin=factorio,
            runs_dir=runs_dir,
            run_ticks=run_ticks,
            console=console,
        )
    except RunError as exc:
        console.print(f"[red]Run failed:[/red] {exc}")
        raise typer.Exit(code=1)
    console.print(f"[green]Run complete[/green]  {result.run_id}")
    console.print(f"Artifacts: {result.run_dir}")


@app.command("build-baseline")
def build_baseline_command(
    scenario: Path = typer.Argument(..., help="Scenario directory (e.g. scenarios/factory-physics/fp03-littles-law)"),
    factorio: Path | None = typer.Option(None, envvar="FACTORIO_BIN", help="Factorio binary"),
    verify: bool = typer.Option(True, help="Run the scenario headlessly against the new baseline as acceptance"),
    workspace: Path = typer.Option(Path("runs/_baseline_build"), help="Scratch workspace"),
) -> None:
    """Construct the scenario's baseline.zip against a real Factorio server
    (Issue #2 Stage B) and optionally verify it with a full headless run."""
    from fisl.controller.baseline_builder import BuildError, build_baseline, verify_baseline

    if factorio is None or not Path(factorio).exists():
        console.print("[red]No Factorio binary: pass --factorio or set FACTORIO_BIN[/red]")
        raise typer.Exit(code=1)
    scenario_dir = _scenario_yaml_path(scenario).parent
    try:
        target = build_baseline(
            factorio_bin=Path(factorio), scenario_dir=scenario_dir,
            workspace=workspace, console=console,
        )
        if verify:
            console.print("Verifying baseline with a full headless run…")
            summary = verify_baseline(
                factorio_bin=Path(factorio), scenario_dir=scenario_dir,
                runs_dir=workspace / "verify-runs", console=console,
            )
            throughput = summary["metrics"]["measured_throughput"]
            console.print(
                f"[green]Baseline verified[/green]: {throughput['completed_quantity']} workpieces "
                f"completed in measured window; census valid; Lua/Python agree."
            )
    except BuildError as exc:
        console.print(f"[red]Baseline build failed:[/red] {exc}")
        raise typer.Exit(code=1)
    console.print(f"Done: {target}")


@app.command()
def report(run_dir: Path = typer.Argument(..., help="runs/<run_id> directory")) -> None:
    """Display final metrics with method/window/coverage metadata (FR-CTRL-007)."""
    from fisl.report.run_report import render_report

    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        console.print(f"[red]No summary.json in {run_dir}[/red]")
        raise typer.Exit(code=1)
    render_report(json.loads(summary_path.read_text()), console)


if __name__ == "__main__":
    app()
