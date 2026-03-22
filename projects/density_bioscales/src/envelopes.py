"""Interval-valued outputs for uncertainty / scenario boxes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Interval:
    """Closed interval [low, high] with low <= high."""

    low: float
    high: float

    def __post_init__(self) -> None:
        if self.low > self.high:
            raise ValueError("interval low must be <= high")

    def width(self) -> float:
        return self.high - self.low


def interval_from_samples(values: list[float]) -> Interval:
    """Min/max envelope over a finite set."""
    if not values:
        raise ValueError("values must be non-empty")
    return Interval(low=min(values), high=max(values))


def scale_interval(iv: Interval, factor: float) -> Interval:
    """Multiply both bounds by factor (e.g. unit conversion)."""
    return Interval(low=iv.low * factor, high=iv.high * factor)
