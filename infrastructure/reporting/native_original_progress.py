"""Best-effort Original phase diagnostics; never custody or execution authority."""

from __future__ import annotations

import json
import math
import os
import sys
import time

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES


def original_cell_progress(phase: str, scope: str, deadline: float) -> None:
    """Observe the unchanged clock without masking an actual expired outcome.

    Fixed labels and public scope only: no argv, environment, paths or receipts.
    A closed diagnostic stream cannot replace the retained OS/custody failure.
    """
    if (
        not isinstance(phase, str)
        or phase not in {"selection-start", "worker-start", "worker-completed", "terminal-observed"}
        or not isinstance(scope, str)
        or scope not in PUBLIC_PROJECT_NAMES
        or type(deadline) not in (float, int)
        or not math.isfinite(deadline)
    ):
        raise ValueError("Original progress requires fixed public phase/scope and the finite existing clock")
    observed = time.monotonic()
    value = {
        "schema_version": "template-native-original-progress-v1",
        "phase": phase,
        "scope": scope,
        "pid": os.getpid(),
        "observed_monotonic": observed,
        "remaining_seconds": deadline - observed,
    }
    try:
        print(json.dumps(value, sort_keys=True, allow_nan=False), file=sys.stderr, flush=True)
    except OSError, ValueError:
        # Diagnostics grant no authority and must not launder the primary exit.
        pass
