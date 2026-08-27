"""Post-run drill checks (operator-training scenarios).

A scenario may carry a read-only world inspection at

    <scenario-dir>/drills/check.lua

If present, the controller executes it over RCON after the run COMPLETES
(server still up, world in its final state) and stores the result as
`runs/<run_id>/drills.json`. The script must print exactly one JSON
document via `rcon.print(helpers.table_to_json{...})` shaped as:

    {"drills": [{"id": "...", "passed": true, "detail": "..."}, ...]}

Design boundaries, deliberate:

- Drills are *grading of practice*, not measurement: they never touch the
  metrics pipeline, the summary, validity, or any hash. The physics
  instruments stay pure measurement.
- The check is read-only by convention and runs after the final phase, so
  it cannot influence the experiment it follows.
- A failing or crashing check degrades to a recorded warning — it never
  fails the run (the run's own data is unaffected and already collected).
- Headless runs skip drills: they grade a human's hands, and a headless
  world has none.
"""

from __future__ import annotations

import json
from pathlib import Path

from fisl.controller.solutions import to_single_line


class DrillError(Exception):
    pass


DRILLS_CHECK = Path("drills") / "check.lua"


def load_drill_check(scenario_dir: Path) -> str | None:
    """Return the single-line check command, or None if the scenario has none."""
    path = Path(scenario_dir) / DRILLS_CHECK
    if not path.exists():
        return None
    return to_single_line(
        str(DRILLS_CHECK), path.read_text(encoding="utf-8"),
        required_token="rcon.print", error=DrillError,
    )


def parse_drill_response(response: str) -> dict:
    """Validate the check script's JSON output into {"drills": [...]}."""
    try:
        payload = json.loads(response)
    except json.JSONDecodeError as exc:
        raise DrillError(f"drill check printed non-JSON output: {response!r}") from exc
    drills = payload.get("drills") if isinstance(payload, dict) else None
    if not isinstance(drills, list) or not drills:
        raise DrillError(f"drill check JSON must contain a non-empty 'drills' list: {payload!r}")
    for entry in drills:
        if not isinstance(entry, dict) or "id" not in entry or "passed" not in entry:
            raise DrillError(f"malformed drill entry: {entry!r}")
        entry["passed"] = bool(entry["passed"])
        entry.setdefault("detail", "")
    return {"drills": drills}


def run_drill_check(scenario_dir: Path, rcon, run_dir: Path) -> dict:
    """Execute the check, write drills.json, return a small summary dict."""
    command = load_drill_check(scenario_dir)
    if command is None:
        return {}
    response = rcon.command("/silent-command " + command).strip()
    result = parse_drill_response(response)
    (Path(run_dir) / "drills.json").write_text(json.dumps(result, indent=2))
    passed = sum(1 for d in result["drills"] if d["passed"])
    return {"passed": passed, "total": len(result["drills"])}
