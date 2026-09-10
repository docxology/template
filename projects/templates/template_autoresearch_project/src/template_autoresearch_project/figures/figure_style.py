"""Configurable visual style for the AutoResearch figures.

This module is the single source of truth for every visual decision the figure
writers make: resolution (``dpi``), the semantic colour palette, the heatmap
colormaps, font scaling, grid visibility, and background transparency. It is
loaded from the project-local ``figures.yaml`` (falling back to
:data:`DEFAULT_FIGURE_STYLE` when absent) and applied through the
:func:`apply_style` context manager, which both records the active config for the
figure writers and scopes a matplotlib ``rc_context`` so nothing leaks across the
generation batch.

Design contract (see ``MEMORY/WORK/autoresearch-viz/ISA.md``):

* **Default == current behaviour.** :data:`DEFAULT_FIGURE_STYLE` reproduces the
  values previously hardcoded across the figure modules, so introducing
  configurability does not silently restyle existing output. At ``font_scale ==
  1.0`` the emitted ``font.size`` equals matplotlib's own default (10.0), keeping
  default renders byte-identical.
* **No leaked global state.** :func:`apply_style` saves the previous active style
  and restores it in a ``finally`` block (exception- and nesting-safe), and wraps
  ``matplotlib.pyplot.rc_context`` so rcParams revert on exit. Absence of leakage
  is proven externally by a permuted-order A/B regeneration probe.
* **PNG-scoped.** Output filenames are bound to ``.png`` in the figure registry,
  so an ``output_format`` knob is deliberately *not* exposed — that keeps the
  determinism guarantee and the figure-quality gate intact.
"""

from __future__ import annotations

import contextlib
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

FIGURE_STYLE_SCHEMA = "template-autoresearch-figure-style-v1"

# Colourblind-safe (Okabe-Ito aligned) palette mapped to semantic roles. These
# values reproduce the colours previously hardcoded across the figure modules so
# the default render is unchanged; they are unified here so a single override
# restyles every figure at once.
_DEFAULT_PALETTE: dict[str, str] = {
    # candidate status (consumed by figures_core._status_color)
    "baseline": "#52525b",
    "accepted": "#0072b2",
    "rejected": "#56b4e9",
    "evaluated": "#56b4e9",
    "deferred": "#64748b",  # historical _status_color value for deferred markers (kept byte-identical)
    # semantic accents
    "positive": "#0f766e",
    "warning": "#a16207",
    "negative": "#7c2d12",
    "accent": "#2563eb",
    "accent2": "#7c3aed",
    "accent_light": "#60a5fa",
    "positive_light": "#34d399",
    "series_warn": "#e69f00",
    "highlight": "#f59e0b",
    "text_dark": "#111827",
    "reference": "#52525b",
    # structural / chrome
    "grid": "#d4d4d8",
    "annotation": "#475569",
    "connector": "#cbd5e1",
    "muted": "#64748b",
    "rule": "#94a3b8",
    "box_face": "#f8fafc",
    "box_edge": "#334155",
    "arrow": "#475569",
    "ink": "#0f172a",
    # security control-matrix / status badges
    "row_alt": "#eef6f8",
    "row_edge": "#e2e8f0",
    "ok_face": "#ecfdf5",
    "ok_fill": "#d1fae5",
    "ok_ink": "#064e3b",
    "warn_fill": "#fef3c7",
    "warn_ink": "#713f12",
}

# Knobs that accept a simple scalar from the YAML ``figures:`` block.
_SCALAR_FIELDS: dict[str, type] = {
    "dpi": int,
    "transparent": bool,
    "font_scale": float,
    "grid": bool,
    "heatmap_colormap": str,
    "metrics_colormap": str,
}


@dataclass(frozen=True)
class FigureStyleConfig:
    """Immutable visual style applied to every generated figure."""

    dpi: int = 160
    transparent: bool = False
    font_scale: float = 1.0
    grid: bool = True
    heatmap_colormap: str = "Blues"
    metrics_colormap: str = "YlGnBu"
    palette: Mapping[str, str] = field(default_factory=lambda: dict(_DEFAULT_PALETTE))

    def color(self, role: str, fallback: str = "#000000") -> str:
        """Resolve a palette ``role`` to a hex colour, with a fallback."""
        return str(self.palette.get(role, fallback))

    def rc_params(self) -> dict[str, Any]:
        """Return matplotlib rcParams for this style.

        Only ``font.size`` is scaled (matplotlib's relative size keywords such as
        ``large``/``medium`` then scale proportionally). At ``font_scale == 1.0``
        this equals the matplotlib default of ``10.0`` so default renders are
        byte-identical. ``dpi`` is intentionally *not* set here — it is applied
        once, explicitly, in :func:`figures_core.save_figure`, to avoid a
        double-apply between ``figure.dpi`` and ``savefig.dpi``.
        """
        return {"font.size": 10.0 * float(self.font_scale)}

    def to_dict(self) -> dict[str, object]:
        """Serialize to a JSON-safe mapping for registry/report provenance."""
        return {
            "schema": FIGURE_STYLE_SCHEMA,
            "dpi": int(self.dpi),
            "transparent": bool(self.transparent),
            "font_scale": float(self.font_scale),
            "grid": bool(self.grid),
            "heatmap_colormap": str(self.heatmap_colormap),
            "metrics_colormap": str(self.metrics_colormap),
            "palette": dict(self.palette),
        }


DEFAULT_FIGURE_STYLE = FigureStyleConfig()


def figure_style_from_mapping(raw: Mapping[str, Any]) -> FigureStyleConfig:
    """Build a :class:`FigureStyleConfig` from a mapping, merging over defaults.

    Partial overrides are supported: any field absent from ``raw`` keeps its
    default, and a partial ``palette`` mapping is merged over the default palette
    (so overriding one role leaves the rest intact).
    """
    if not isinstance(raw, Mapping):
        raise ValueError("figures style config must be a mapping")

    # Reject typo'd / unknown top-level keys so a misspelled knob fails loudly
    # rather than being silently ignored.
    allowed_keys = set(_SCALAR_FIELDS) | {"palette"}
    unknown_keys = sorted(str(key) for key in raw if str(key) not in allowed_keys)
    if unknown_keys:
        raise ValueError(
            f"unknown figure style key(s): {', '.join(unknown_keys)}; allowed: {', '.join(sorted(allowed_keys))}"
        )

    values: dict[str, Any] = {}
    for key, caster in _SCALAR_FIELDS.items():
        if key not in raw or raw[key] is None:
            continue
        value = raw[key]
        if caster is bool:
            if not isinstance(value, bool):
                raise ValueError(f"figures.{key} must be a boolean")
            values[key] = value
        elif caster is int:
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"figures.{key} must be an integer")
            if value <= 0:
                raise ValueError(f"figures.{key} must be a positive integer")
            values[key] = value
        elif caster is float:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"figures.{key} must be a number")
            if value <= 0:
                raise ValueError(f"figures.{key} must be a positive number")
            values[key] = float(value)
        else:  # str
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"figures.{key} must be a non-empty string")
            values[key] = value

    palette = dict(_DEFAULT_PALETTE)
    raw_palette = raw.get("palette")
    if raw_palette is not None:
        if not isinstance(raw_palette, Mapping):
            raise ValueError("figures.palette must be a mapping of role -> hex colour")
        for role, hex_value in raw_palette.items():
            role_name = str(role)
            # Reject unknown role names so a misspelled role fails loudly instead
            # of being stored inertly and polluting the provenance artifact.
            if role_name not in _DEFAULT_PALETTE:
                raise ValueError(f"unknown palette role: {role_name}; allowed: {', '.join(sorted(_DEFAULT_PALETTE))}")
            if not isinstance(hex_value, str) or not _is_hex_color(hex_value):
                raise ValueError(f"figures.palette.{role_name} must be a hex colour like '#1a2b3c'")
            palette[role_name] = hex_value
    values["palette"] = palette

    return FigureStyleConfig(**values)


FIGURE_STYLE_FILENAME = "figures.yaml"


def load_figure_style(project_root: Path) -> FigureStyleConfig:
    """Load the figure style from the project-local ``figures.yaml``.

    The file is a flat mapping of style fields (see :func:`figure_style_from_mapping`).
    Returns :data:`DEFAULT_FIGURE_STYLE` when the file is absent or empty, so the
    exemplar renders identically out of the box. A dedicated file is used (rather
    than ``autoresearch.yaml``) because the AutoResearch config loader rejects
    unrecognised keys.
    """
    config_path = project_root / FIGURE_STYLE_FILENAME
    if not config_path.is_file():
        return DEFAULT_FIGURE_STYLE
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if payload is None:
        return DEFAULT_FIGURE_STYLE
    if not isinstance(payload, Mapping):
        raise ValueError(f"{FIGURE_STYLE_FILENAME} root must be a mapping of style fields")
    return figure_style_from_mapping(payload)


# --- active-style management ------------------------------------------------

_ACTIVE_STYLE: FigureStyleConfig = DEFAULT_FIGURE_STYLE


def get_active_style() -> FigureStyleConfig:
    """Return the currently active figure style.

    Defaults to :data:`DEFAULT_FIGURE_STYLE` so figure writers called outside any
    :func:`apply_style` block (e.g. the existing direct-call tests) keep producing
    the historical output.
    """
    return _ACTIVE_STYLE


@contextlib.contextmanager
def apply_style(style: FigureStyleConfig) -> Iterator[FigureStyleConfig]:
    """Activate ``style`` for the duration of the block.

    Saves and restores the previous active style in a ``finally`` block (so a
    writer raising mid-block still restores it, and nested use is safe) and scopes
    a matplotlib ``rc_context`` so rcParams revert on exit. This is the only place
    module-level style state is mutated.

    NOT thread-safe: it mutates a process-global active style and the global
    matplotlib rcParams. Figure generation in this project is single-threaded by
    design (sequential ``with apply_style(...)`` blocks in ``writers.py``), which
    is what keeps determinism and the no-leak guarantee intact; do not call it
    from concurrent threads without a per-thread guard. Treat ``FigureStyleConfig``
    as read-only — the dataclass is frozen but its ``palette`` mapping is only
    shallow-frozen, so mutating ``style.palette`` in place would bypass restore.
    """
    from matplotlib import pyplot as plt

    global _ACTIVE_STYLE
    previous = _ACTIVE_STYLE
    _ACTIVE_STYLE = style
    try:
        with plt.rc_context(style.rc_params()):
            yield style
    finally:
        _ACTIVE_STYLE = previous


def _is_hex_color(value: str) -> bool:
    text = value.strip()
    if not text.startswith("#") or len(text) not in (4, 7):
        return False
    return all(ch in "0123456789abcdefABCDEF" for ch in text[1:])
