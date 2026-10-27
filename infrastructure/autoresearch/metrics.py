"""Metric-unit inference and grading helpers for autoresearch benchmarks."""

from __future__ import annotations

import math
import re
from collections.abc import Sequence
from statistics import median

_METRIC_LINE_RE = re.compile(
    r"^METRIC\s+(?P<name>[A-Za-z_][A-Za-z0-9_.:-]*)=(?P<value>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)$"
)

_UNIT_SUFFIXES: tuple[tuple[str, str], ...] = (
    ("_milliseconds", "ms"),
    (".milliseconds", "ms"),
    ("_millis", "ms"),
    (".millis", "ms"),
    ("_ms", "ms"),
    (".ms", "ms"),
    ("_seconds", "s"),
    (".seconds", "s"),
    ("_secs", "s"),
    (".secs", "s"),
    ("_sec", "s"),
    (".sec", "s"),
    ("_s", "s"),
    (".s", "s"),
    ("_percent", "%"),
    (".percent", "%"),
    ("_pct", "%"),
    (".pct", "%"),
    ("_usd", "USD"),
    (".usd", "USD"),
    ("_bytes", "bytes"),
    (".bytes", "bytes"),
)


def parse_metric_lines(output: str) -> dict[str, float]:
    """Return trusted numeric metrics from exact ``METRIC name=value`` lines.

    Non-metric log lines are ignored. Lines that begin with ``METRIC`` but do
    not match the contract raise ``ValueError`` so invalid benchmark output
    cannot silently become evidence. Duplicate metric names are rejected because
    the template should not have to guess which run-derived number is canonical.
    """
    metrics: dict[str, float] = {}
    for line_number, raw_line in enumerate(output.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        if not line.startswith("METRIC"):
            continue
        match = _METRIC_LINE_RE.fullmatch(line)
        if match is None:
            raise ValueError(f"invalid METRIC line at {line_number}: {raw_line!r}")
        name = match.group("name")
        if name in metrics:
            raise ValueError(f"duplicate METRIC name at {line_number}: {name}")
        value = float(match.group("value"))
        if not math.isfinite(value):
            raise ValueError(f"non-finite METRIC value at {line_number}: {name}")
        metrics[name] = value
    return metrics


def metric_unit_from_name(name: str) -> str:
    """Process metric unit from name."""
    normalized = name.strip().lower()
    for suffix, unit in _UNIT_SUFFIXES:
        if normalized.endswith(suffix):
            return unit
    return ""


def mad_confidence(values: Sequence[float | str], baseline: float, best: float) -> float | None:
    """Return absolute improvement divided by the run-value MAD noise floor.

    ``None`` means there is not enough finite variation to estimate confidence.
    This keeps confidence/noise disclosure explicit instead of treating a
    zero-noise sample as proof.
    """
    finite_values = []
    for value in values:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(numeric):
            finite_values.append(numeric)
    if len(finite_values) < 2 or not math.isfinite(baseline) or not math.isfinite(best):
        return None
    center = median(finite_values)
    noise_floor = median(abs(value - center) for value in finite_values)
    if noise_floor <= 0:
        return None
    return abs(float(best) - float(baseline)) / noise_floor
