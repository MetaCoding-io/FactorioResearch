"""Factorio Industrial Systems Laboratory (FISL).

Python side of FISL: scenario compilation, run orchestration, and post-run
reporting. The scientific contract lives in docs/adr/; this package implements
the POC scope of GitHub Issue #2 (runtime-validation spike + Lab 3 vertical
slice).
"""

SPEC = "fisl/v1"
COMPILER_VERSION = "0.1.0"
PROTOCOL_VERSION = 1

__all__ = ["SPEC", "COMPILER_VERSION", "PROTOCOL_VERSION"]
