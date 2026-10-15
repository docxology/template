"""Bounded diagnostic observations, never native admission authority."""

from __future__ import annotations

import json
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
