"""Data models and helpers for interactive simulation dashboards."""

from __future__ import annotations

import math
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Sequence


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Panel:
    """One Plotly figure on the dashboard.

    ``traces`` and ``layout`` are passed directly to ``Plotly.newPlot``;
    every value must be JSON-serialisable.

    ``driven_by`` lists control IDs that update this panel via the
    ``update_fn`` JavaScript snippet (string with the function body --
    ``payload``, ``controls``, ``Plotly``, ``panelId`` are in scope).
    Use it when the panel must re-compute from raw data (e.g. heatmap
    slice at a slider value).
    """

    panel_id: str
    title: str
    traces: list[dict[str, Any]]
    layout: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    driven_by: list[str] = field(default_factory=list)
    update_fn: str = ""  # JS body run on control change
    # Tabular preview row count (for the data-inspector tab); 0 == hide.
    preview_rows: int = 10


@dataclass
class Control:
    """One interactive control (slider / dropdown / toggle)."""

    control_id: str
    label: str
    kind: Literal["slider", "dropdown", "toggle", "number"] = "slider"
    # slider: min/max/step/default; dropdown: options/default;
    # toggle: default (bool); number: min/max/step/default.
    min: float | None = None
    max: float | None = None
    step: float | None = None
    default: Any = 0.0
    options: list[Any] = field(default_factory=list)  # dropdown values
    option_labels: list[str] = field(default_factory=list)  # optional labels
    description: str = ""


@dataclass
class Invariant:
    """A single numerical invariant to validate.

    ``kind`` selects the comparator:
      - ``"equal"``     : ``|actual - expected| <= tol``
      - ``"le"``        : ``actual <= expected + tol``
      - ``"ge"``        : ``actual >= expected - tol``
      - ``"in_range"``  : ``expected[0] - tol <= actual <= expected[1] + tol``
      - ``"monotone_increasing"`` / ``"monotone_decreasing"``:
          ``actual`` is the sequence; ``expected`` is ignored;
          checks the sequence is (weakly) monotone within ``tol``.
      - ``"finite"``    : ``actual`` is a finite float (or all-finite array)
      - ``"nonneg"``    : ``actual >= -tol`` (scalar or array)
      - ``"array_close"``: ``max |actual_i - expected_i| <= tol`` (elementwise)
    """

    name: str
    actual: float | Sequence[float]
    expected: float | tuple[float, float] | Sequence[float] | None = None
    tol: float = 1e-9
    kind: Literal[
        "equal",
        "le",
        "ge",
        "in_range",
        "monotone_increasing",
        "monotone_decreasing",
        "finite",
        "nonneg",
        "array_close",
    ] = "equal"
    description: str = ""

    @staticmethod
    def _scalar(value: float | Sequence[float] | None) -> float:
        if value is None or isinstance(value, Sequence):
            raise TypeError("expected a scalar value")
        return float(value)

    @staticmethod
    def _sequence(value: float | Sequence[float] | None) -> Sequence[float]:
        if value is None or not isinstance(value, Sequence):
            raise TypeError("expected a sequence value")
        return value

    def evaluate(self) -> tuple[bool, str]:
        """Return ``(passed, witness)``. ``witness`` is a human string."""
        try:
            if self.kind == "equal":
                a = self._scalar(self.actual)
                e = self._scalar(self.expected)
                diff = abs(a - e)
                return diff <= self.tol, (f"|{a:.6g} - {e:.6g}| = {diff:.3e} (tol={self.tol:.1e})")
            if self.kind == "le":
                a = self._scalar(self.actual)
                e = self._scalar(self.expected)
                return a <= e + self.tol, f"{a:.6g} <= {e:.6g} + {self.tol:.1e}"
            if self.kind == "ge":
                a = self._scalar(self.actual)
                e = self._scalar(self.expected)
                return a >= e - self.tol, f"{a:.6g} >= {e:.6g} - {self.tol:.1e}"
            if self.kind == "in_range":
                a = self._scalar(self.actual)
                lo, hi = self._sequence(self.expected)
                lo, hi = float(lo), float(hi)
                ok = (lo - self.tol) <= a <= (hi + self.tol)
                return ok, f"{lo:.6g} <= {a:.6g} <= {hi:.6g} (tol={self.tol:.1e})"
            if self.kind in ("monotone_increasing", "monotone_decreasing"):
                seq = list(self._sequence(self.actual))
                worst = 0.0
                inc = self.kind == "monotone_increasing"
                for x, y in zip(seq, seq[1:]):
                    delta = (y - x) if inc else (x - y)
                    if delta < -self.tol:
                        worst = min(worst, delta)
                ok = worst >= -self.tol
                arrow = "<=" if inc else ">="
                return ok, (
                    f"worst out-of-order step = {worst:.3e} (tol={self.tol:.1e}, "
                    f"sequence length {len(seq)}, expect a_i {arrow} a_{{i+1}})"
                )
            if self.kind == "finite":
                if hasattr(self.actual, "__iter__"):
                    bad = [i for i, v in enumerate(self.actual) if not math.isfinite(float(v))]
                    ok = not bad
                    return (
                        ok,
                        (
                            f"all finite ({len(list(self.actual))} values)"
                            if ok
                            else f"non-finite at indices {bad[:8]}{'...' if len(bad) > 8 else ''}"
                        ),
                    )
                a = self._scalar(self.actual)
                ok = math.isfinite(a)
                return ok, f"value = {a!r}"
            if self.kind == "nonneg":
                if hasattr(self.actual, "__iter__"):
                    vals = [float(v) for v in self.actual]
                    worst = min(vals) if vals else 0.0
                    ok = worst >= -self.tol
                    return ok, f"min = {worst:.6g} (tol={self.tol:.1e})"
                a = self._scalar(self.actual)
                return a >= -self.tol, f"value = {a:.6g} (tol={self.tol:.1e})"
            if self.kind == "array_close":
                actual_values = list(self._sequence(self.actual))
                expected_values = list(self._sequence(self.expected))
                if len(actual_values) != len(expected_values):
                    return False, f"length mismatch: actual={len(actual_values)}, expected={len(expected_values)}"
                worst = 0.0
                bad_idx = -1
                for i, (av, ev) in enumerate(zip(actual_values, expected_values)):
                    d = abs(float(av) - float(ev))
                    if d > worst:
                        worst, bad_idx = d, i
                return worst <= self.tol, (
                    f"max |Δ| = {worst:.3e} at index {bad_idx} (tol={self.tol:.1e}, length {len(actual_values)})"
                )
        except Exception as exc:  # pragma: no cover - defensive
            return False, f"evaluation error: {exc!r}"
        return False, f"unknown kind {self.kind!r}"


# ---------------------------------------------------------------------------
# Provenance helpers
# ---------------------------------------------------------------------------


def _git_rev(repo_root: Path | None = None) -> str:
    cwd = str(repo_root) if repo_root else None
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=cwd,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        return out.decode().strip()
    except Exception:
        return "unknown"


def _git_dirty(repo_root: Path | None = None) -> bool:
    cwd = str(repo_root) if repo_root else None
    try:
        out = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=cwd,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        return bool(out.strip())
    except Exception:
        return False


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# JSON helpers (numpy arrays → lists)
# ---------------------------------------------------------------------------


def _to_jsonable(obj: Any) -> Any:
    """Recursively convert numpy arrays / Path / dataclasses to JSON-safe."""
    if obj is None or isinstance(obj, (bool, int, float, str)):
        if isinstance(obj, float) and not math.isfinite(obj):
            return None
        return obj
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {str(k): _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_to_jsonable(v) for v in obj]
    # numpy without import-cost
    cls = obj.__class__
    if cls.__module__.startswith("numpy"):
        if hasattr(obj, "tolist"):
            return _to_jsonable(obj.tolist())
        if hasattr(obj, "item"):
            return _to_jsonable(obj.item())
    if hasattr(obj, "__dataclass_fields__"):
        return _to_jsonable(asdict(obj))
    return repr(obj)


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


__all__ = ["Panel", "Control", "Invariant"]
