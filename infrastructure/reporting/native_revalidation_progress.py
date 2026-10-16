"""Finite process-owned revalidation observations; never admission authority."""

from __future__ import annotations

import json
import math
import os
import sys
import time

from infrastructure.project.public_reference_git import remaining
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_source_external_admission import NativeSourceContext


class RevalidationProgress:
    """Count only actual calls in this one fixed owner/window, never cache GO."""

    def __init__(self, source: NativeSourceContext, group: str, scopes: tuple[str, ...], deadline: float) -> None:
        if (
            not isinstance(source, NativeSourceContext)
            or group not in {"reader-runtimes", "current-nominations"}
            or not isinstance(scopes, tuple)
            or not scopes
            or len(scopes) > len(PUBLIC_PROJECT_NAMES)
            or len(set(scopes)) != len(scopes)
            or any(scope not in PUBLIC_PROJECT_NAMES for scope in scopes)
            or type(deadline) not in {int, float}
            or not math.isfinite(deadline)
        ):
            raise ValueError("native revalidation requires fixed genuine Source/scopes/clock")
        remaining(deadline)
        self.source, self.group, self.scopes, self.deadline = source, group, scopes, deadline
        self.owner_pid = os.getpid()
        self.started = time.monotonic()
        self.source_started = self.source_completed = self.member_observations = 0

    def emit(self, phase: str, scope: str | None = None) -> None:
        if (
            os.getpid() != self.owner_pid
            or phase
            not in {
                "source-opening",
                "source-middle",
                "source-closing",
                "selection",
                "selection-closing",
                "selected-closing",
                "completed",
                "failed",
            }
            or (scope is not None and scope not in self.scopes)
        ):
            raise ValueError("native revalidation diagnostic lost its fixed process/window")
        print(
            json.dumps(
                {
                    "schema_version": "template-native-revalidation-progress-v1",
                    "group": self.group,
                    "phase": phase,
                    "scope": scope,
                    "pid": self.owner_pid,
                    "scope_count": len(self.scopes),
                    "observed_monotonic": time.monotonic(),
                    "elapsed_seconds": time.monotonic() - self.started,
                    "remaining_seconds": max(0.0, self.deadline - time.monotonic()),
                    "source_calls_started": self.source_started,
                    "source_calls_completed": self.source_completed,
                    "member_observations": self.member_observations,
                },
                sort_keys=True,
                allow_nan=False,
            ),
            file=sys.stderr,
            flush=True,
        )

    def source_check(self, phase: str) -> None:
        remaining(self.deadline)
        self.source_started += 1
        self.emit(phase)
        self.source.verify_correspondence(
            self.source.reference,
            self.source.bindings.current_root,
            self.source.current_source_reader,
            self.deadline,
        )
        self.source_completed += 1
        remaining(self.deadline)

    def member(self, phase: str, scope: str) -> None:
        remaining(self.deadline)
        self.member_observations += 1
        self.emit(phase, scope)
