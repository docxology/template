"""Tests for interval envelopes."""

from __future__ import annotations

import pytest

import envelopes


def test_interval_width() -> None:
    iv = envelopes.Interval(1.0, 4.0)
    assert iv.width() == pytest.approx(3.0)


def test_interval_rejects_inverted() -> None:
    with pytest.raises(ValueError):
        envelopes.Interval(5.0, 2.0)


def test_interval_from_samples() -> None:
    iv = envelopes.interval_from_samples([3.0, 1.0, 2.0])
    assert iv.low == 1.0
    assert iv.high == 3.0


def test_interval_from_samples_empty() -> None:
    with pytest.raises(ValueError):
        envelopes.interval_from_samples([])


def test_scale_interval() -> None:
    iv = envelopes.scale_interval(envelopes.Interval(2.0, 5.0), 10.0)
    assert iv.low == 20.0
    assert iv.high == 50.0
