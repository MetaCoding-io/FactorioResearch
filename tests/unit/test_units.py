import pytest

from fisl.scenario.units import Rate, UnitError, parse_duration_ticks, parse_rate


def test_duration_forms():
    assert parse_duration_ticks("120t") == 120
    assert parse_duration_ticks("30s") == 1800
    assert parse_duration_ticks("5m") == 18000
    assert parse_duration_ticks(42) == 42


def test_duration_rejects_fractional_ticks():
    with pytest.raises(UnitError):
        parse_duration_ticks("0.5t")
    # 0.25s = 15 ticks is exact and allowed
    assert parse_duration_ticks("0.25s") == 15


def test_duration_rejects_nonpositive_and_garbage():
    with pytest.raises(UnitError):
        parse_duration_ticks(0)
    with pytest.raises(UnitError):
        parse_duration_ticks("five minutes")


def test_rate_exact_rational():
    assert parse_rate("60/min") == Rate(1, 60)
    assert parse_rate("75/min") == Rate(1, 48)
    assert parse_rate("1/s") == Rate(1, 60)
    assert parse_rate("180/min") == Rate(1, 20)


def test_rate_fractional_magnitude_stays_exact():
    assert parse_rate("0.5/s") == Rate(1, 120)


def test_rate_per_minute_roundtrip():
    assert parse_rate("75/min").per_minute == 75
