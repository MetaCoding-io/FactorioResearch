"""Exact authoring-unit conversion (ADR 0001 §3, schema §4).

1 simulation second = 60 ticks; 1 simulation minute = 3600 ticks.
Durations that do not resolve to a whole number of ticks are rejected —
silent rounding is forbidden by ADR 0001.

Rates such as "75/min" compile to an exact rational (quantity, period_ticks)
pair; FISL never accumulates floating-point items-per-tick (ADR 0003 §12).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction
from math import gcd

TICKS_PER_SECOND = 60
TICKS_PER_MINUTE = 3600

_DURATION_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(t|ticks?|s|sec|seconds?|m|min|minutes?)\s*$")
_RATE_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*/\s*(t|tick|s|sec|second|m|min|minute)\s*$")

_UNIT_TICKS = {
    "t": 1, "tick": 1, "ticks": 1,
    "s": TICKS_PER_SECOND, "sec": TICKS_PER_SECOND, "second": TICKS_PER_SECOND, "seconds": TICKS_PER_SECOND,
    "m": TICKS_PER_MINUTE, "min": TICKS_PER_MINUTE, "minute": TICKS_PER_MINUTE, "minutes": TICKS_PER_MINUTE,
}


class UnitError(ValueError):
    """An authoring quantity could not be converted exactly."""


def parse_duration_ticks(value: str | int) -> int:
    """Convert an authoring duration to an exact positive tick count."""
    if isinstance(value, int):
        ticks = value
    else:
        match = _DURATION_RE.match(value)
        if not match:
            raise UnitError(f"unrecognized duration {value!r} (expected forms like '120t', '30s', '5m')")
        magnitude, unit = match.groups()
        exact = Fraction(magnitude) * _UNIT_TICKS[unit]
        if exact.denominator != 1:
            raise UnitError(
                f"duration {value!r} is not a whole number of ticks ({exact} ticks); "
                "ADR 0001 forbids silent rounding"
            )
        ticks = int(exact)
    if ticks <= 0:
        raise UnitError(f"duration must be positive, got {ticks} ticks")
    return ticks


@dataclass(frozen=True)
class Rate:
    """Exact rational release rate: `quantity` items per `period_ticks` ticks."""

    quantity: int
    period_ticks: int

    def __post_init__(self) -> None:
        if self.quantity <= 0 or self.period_ticks <= 0:
            raise UnitError(f"rate must be positive, got {self.quantity}/{self.period_ticks}t")

    @property
    def per_minute(self) -> Fraction:
        return Fraction(self.quantity * TICKS_PER_MINUTE, self.period_ticks)

    def reduced(self) -> "Rate":
        g = gcd(self.quantity, self.period_ticks)
        return Rate(self.quantity // g, self.period_ticks // g)


def parse_rate(value: str) -> Rate:
    """Convert an authoring rate such as '75/min' to an exact reduced Rate."""
    match = _RATE_RE.match(value)
    if not match:
        raise UnitError(f"unrecognized rate {value!r} (expected forms like '60/min', '1/s')")
    magnitude, unit = match.groups()
    quantity = Fraction(magnitude)
    period = _UNIT_TICKS[unit]
    # quantity/period per tick == quantity per (period) ticks; scale away any
    # fractional authoring magnitude exactly (e.g. "0.5/s" -> 1 per 120t).
    rate = Fraction(quantity, period)  # items per tick
    return Rate(rate.numerator, rate.denominator).reduced()
