"""Bounded diagnostic observations, never native admission authority."""

from __future__ import annotations

import json
import math
import os
import sys
import time

from infrastructure.project.public_reference_git import remaining
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES


def preparation_progress(group: str, phase: str, deadline: float, scope: str | None = None) -> None:
    """Emit one finite phase observation under the caller's original clock.

    Only fixed labels and a canonical public scope reach stderr. No environment,
    command, receipt, provider path, or capability is serialized here.
    """
    if (
        group not in {"project-providers", "pdfium-providers", "pdfium-runtimes"}
        or phase not in {"source-opening", "profile", "selection", "selection-closing", "source-closing", "completed"}
        or (scope is not None and scope not in PUBLIC_PROJECT_NAMES)
    ):
        raise ValueError("native preparation progress requires finite public phase labels")
    print(
        json.dumps(
            {
                "schema_version": "template-native-preparation-progress-v1",
                "group": group,
                "phase": phase,
                "scope": scope,
                "pid": os.getpid(),
                "observed_monotonic": time.monotonic(),
                "remaining_seconds": remaining(deadline),
            },
            sort_keys=True,
            allow_nan=False,
        ),
        file=sys.stderr,
        flush=True,
    )


def export_timing_progress(phase: str, ordinal: int, scope: str, deadline: float) -> None:
    """Observe one actual export interval; never admit work or change its clock.

    Invalid/oversized diagnostics and closed streams remain silent. The caller
    emits at most two records for each root/public scope; no end means incomplete.
    """
    if (
        not isinstance(phase, str)
        or phase not in {"begin", "end"}
        or type(ordinal) is not int
        or not 0 <= ordinal <= len(PUBLIC_PROJECT_NAMES)
        or not isinstance(scope, str)
        or (scope != "root" if ordinal == 0 else scope not in PUBLIC_PROJECT_NAMES)
        or type(deadline) is not float
        or not math.isfinite(deadline)
    ):
        return
    observed = time.monotonic()
    value = {
        "schema_version": "template-native-export-timing-v1",
        "phase": phase,
        "ordinal": ordinal,
        "scope": scope,
        "pid": os.getpid(),
        "observed_monotonic": observed,
        "remaining_seconds": deadline - observed,
    }
    try:
        record = json.dumps(value, sort_keys=True, allow_nan=False)
        # Two records per existing scope fit one16-KiB diagnostic allowance.
        maximum = 16 * 1024 // (2 * (len(PUBLIC_PROJECT_NAMES) + 1))
        if len(record.encode("utf-8")) + 1 <= maximum:
            print(record, file=sys.stderr, flush=True)
    except (OSError, ValueError):
        pass
