"""Per-attempt RunConfiguration and reproducibility fingerprint (ADR 0013 rev.).

The stable ResolvedScenario is hashed without run identity. Each attempt then
gets a RunConfiguration carrying `run_id`, the actual execution seed, the
resolved-scenario hash reference, baseline identity, and the behavior-affecting
run profile (ADR 0018). The reproducibility fingerprint includes the seed and
profile but deliberately excludes `run_id`.
"""

from __future__ import annotations

import os
import time
from typing import Any

from fisl import PROTOCOL_VERSION, SPEC
from fisl.scenario.canonical import document_hash

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def new_run_id(timestamp_ms: int | None = None) -> str:
    """Generate a ULID: 48-bit millisecond timestamp + 80 random bits."""
    if timestamp_ms is None:
        timestamp_ms = int(time.time() * 1000)
    value = (timestamp_ms & ((1 << 48) - 1)) << 80 | int.from_bytes(os.urandom(10), "big")
    chars = []
    for _ in range(26):
        chars.append(_CROCKFORD[value & 0x1F])
        value >>= 5
    return "".join(reversed(chars))


def default_run_profile(mode: str = "interactive") -> dict[str, Any]:
    """Deterministic POC run profile per ADR 0018."""
    if mode not in ("interactive", "headless"):
        raise ValueError(f"unknown run mode {mode!r}")
    return {
        "mode": mode,
        "server_auto_pause": False,
        "disconnect_policy": "abort" if mode == "interactive" else "none",
        "required_learner_connection": mode == "interactive",
    }


def build_run_configuration(
    *,
    resolved_scenario_hash: str,
    seed: int,
    baseline_path: str,
    baseline_sha256: str,
    run_profile: dict[str, Any],
    run_id: str | None = None,
) -> dict[str, Any]:
    return {
        "spec": SPEC,
        "protocol_version": PROTOCOL_VERSION,
        "run_id": run_id or new_run_id(),
        "experiment_seed": seed,
        "resolved_scenario_hash": resolved_scenario_hash,
        "baseline": {"save": baseline_path, "sha256": baseline_sha256},
        "run_profile": run_profile,
    }


def reproducibility_fingerprint(
    *,
    resolved_scenario_hash: str,
    seed: int,
    baseline_sha256: str,
    factorio_version: str,
    fisl_versions: dict[str, str],
    mod_manifest: dict[str, str],
    run_profile: dict[str, Any],
) -> str:
    """Identify the controlled experimental input condition (ADR 0013 §9).

    Includes the actual seed and behavior-affecting run profile; excludes
    `run_id` so retries under identical conditions share the fingerprint
    (ADR 0014 §3).
    """
    return document_hash(
        {
            "resolved_scenario_hash": resolved_scenario_hash,
            "experiment_seed": seed,
            "baseline_sha256": baseline_sha256,
            "factorio_version": factorio_version,
            "fisl_versions": dict(sorted(fisl_versions.items())),
            "mod_manifest": dict(sorted(mod_manifest.items())),
            "run_profile": run_profile,
        }
    )
