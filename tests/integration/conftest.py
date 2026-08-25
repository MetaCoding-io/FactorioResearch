"""Integration/spike harness plumbing.

These tests require a real Factorio 2.0.x headless binary:

    FACTORIO_BIN=/path/to/factorio/bin/x64/factorio pytest tests/integration -v

Without FACTORIO_BIN the whole directory is skipped. Passing tests append
runtime-validation evidence records (RUNTIME_VALIDATION.md "Validation
evidence") to tests/integration/evidence/rv-evidence.jsonl for review and
commit.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = Path(__file__).resolve().parent / "evidence"


def factorio_bin() -> Path | None:
    value = os.environ.get("FACTORIO_BIN")
    if value and Path(value).exists():
        return Path(value)
    return None


def pytest_collection_modifyitems(config, items):
    if factorio_bin() is None:
        here = Path(__file__).resolve().parent
        skip = pytest.mark.skip(reason="FACTORIO_BIN not set; runtime spike requires a real Factorio binary")
        for item in items:
            if here in Path(str(item.fspath)).resolve().parents:
                item.add_marker(skip)


@pytest.fixture(scope="session")
def factorio() -> Path:
    binary = factorio_bin()
    assert binary is not None
    return binary


@pytest.fixture(scope="session")
def factorio_version(factorio: Path) -> str:
    output = subprocess.run(
        [str(factorio), "--version"], capture_output=True, text=True, timeout=60
    ).stdout
    return output.splitlines()[0].split()[1] if output else "unknown"


@pytest.fixture(scope="session")
def git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=REPO, timeout=10
        ).stdout.strip()
    except OSError:
        return "unknown"


class EvidenceLog:
    def __init__(self, factorio_version: str, git_sha: str):
        self.factorio_version = factorio_version
        self.git_sha = git_sha
        EVIDENCE_DIR.mkdir(exist_ok=True)
        self.path = EVIDENCE_DIR / "rv-evidence.jsonl"

    def record(self, rv_id: str, *, fixture: str, expected: str, observed: str,
               passed: bool, detail: dict | None = None) -> None:
        entry = {
            "rv_id": rv_id,
            "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "factorio_version": self.factorio_version,
            "fisl_commit": self.git_sha,
            "fixture": fixture,
            "expected": expected,
            "observed": observed,
            "pass": passed,
        }
        if detail:
            entry["detail"] = detail
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")


@pytest.fixture(scope="session")
def evidence(factorio_version: str, git_sha: str) -> EvidenceLog:
    return EvidenceLog(factorio_version, git_sha)
