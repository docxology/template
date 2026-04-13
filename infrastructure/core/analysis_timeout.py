"""Per-script subprocess timeout for Stage 02 (``scripts/02_run_analysis.py``).

Default is **2 hours** per discovered analysis script — enough for long Hermes +
Lean batches (e.g. ``fep_lean``). Override with ``ANALYSIS_SCRIPT_TIMEOUT_SEC`` or
disable the timeout (``0`` / ``none`` / ``unlimited``).
"""

from __future__ import annotations

import os
from typing import Mapping

_DEFAULT_SEC = 7200.0


def parse_analysis_script_timeout_sec(
    environ: Mapping[str, str] | None = None,
) -> float | None:
    """Resolve ``ANALYSIS_SCRIPT_TIMEOUT_SEC`` for ``subprocess.run(timeout=...)``.

    Returns:
        Positive seconds as float, or ``None`` for unlimited (no subprocess timeout).

    Resolution:
        * Unset or empty: ``7200`` (2 hours).
        * ``0``, ``none``, ``unlimited``, ``inf`` (case-insensitive): unlimited.
        * Positive number: that many seconds (fractional allowed).
        * Negative or invalid: fall back to ``7200``.
    """
    env = environ if environ is not None else os.environ
    raw = (env.get("ANALYSIS_SCRIPT_TIMEOUT_SEC") or "").strip()
    if not raw:
        return _DEFAULT_SEC
    low = raw.lower()
    if low in ("0", "none", "unlimited", "inf"):
        return None
    try:
        v = float(raw)
    except ValueError:
        return _DEFAULT_SEC
    if v < 0:
        return _DEFAULT_SEC
    if v == 0:
        return None
    return v
