"""Canonical JSON serialization and hashing (ADR 0013 §3–§4, revision 4).

The canonical form must be deterministic across platforms and library
versions: UTF-8, sorted keys, minimal separators, no NaN/Infinity, integers
only where the contract is exact. `resolved_scenario_hash` is the SHA-256 of
the canonical bytes of the ResolvedScenario document, which deliberately
excludes `run_id` and the actual execution seed (POST_REVIEW_REVISIONS.md
revision 4).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json_bytes(document: Any) -> bytes:
    return json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def document_hash(document: Any) -> str:
    return "sha256:" + sha256_hex(canonical_json_bytes(document))


def file_sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()
