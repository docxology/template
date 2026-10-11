"""Per-script subprocess timeout for Stage 02 (``scripts/pipeline/stage_02_analysis.py``).

Default is **2 hours** per discovered analysis script. Override with a positive,
finite ``ANALYSIS_SCRIPT_TIMEOUT_SEC``. Invalid or retired unlimited settings
are configuration errors; they cannot silently disable supervision.
"""

import math
import os
from typing import Mapping

_DEFAULT_SEC = 7200.0


def parse_analysis_script_timeout_sec(
    environ: Mapping[str, str] | None = None,
) -> float:
    """Resolve a positive finite deadline before starting analysis producers.

    Returns:
        Positive finite seconds as a float.

    Resolution:
        * Unset or empty: ``7200`` (2 hours).
        * Positive number: that many seconds (fractional allowed).
        * Nonpositive, nonfinite, or invalid: raise ``ValueError``.
    """
    env = environ if environ is not None else os.environ
    raw = (env.get("ANALYSIS_SCRIPT_TIMEOUT_SEC") or "").strip()
    if not raw:
        return _DEFAULT_SEC
    try:
        v = float(raw)
    except ValueError as exc:
        raise ValueError("ANALYSIS_SCRIPT_TIMEOUT_SEC must be positive finite seconds") from exc
    if not math.isfinite(v) or v <= 0:
        raise ValueError("ANALYSIS_SCRIPT_TIMEOUT_SEC must be positive finite seconds")
    return v


def analysis_run_timeout_seconds(script_count: int, environ: Mapping[str, str] | None = None) -> float:
    """Validate the composed budget before any configured producer executes."""
    if type(script_count) is not int or script_count < 0:
        raise ValueError("Analysis script count must be a nonnegative integer")
    timeout = parse_analysis_script_timeout_sec(environ) * script_count
    if not math.isfinite(timeout):
        raise ValueError("Composed analysis run timeout must be finite")
    return timeout
