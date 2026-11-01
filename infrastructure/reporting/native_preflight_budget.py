"""Bounded diagnostic preflight clock and its per-boundary retention tails.

The earlier 900-second diagnostic bound was measured below the cold lifecycle's
actual cost.  Two hosted 900-second runs spent 406-564 seconds before the
supervised worker started; one worker still lacked a complete execution
outcome after 182 seconds and the other after 367 seconds.  The outer and inner
watchers also shared one absolute deadline, so the outer watcher killed the
inner owner before it could write its worker process, cleanup or guardian
receipts.

This module owns the single bounded diagnostic budget and the tails reserved at
the launch boundary (the inner preflight may return and retain its evidence
before the outer watcher ends) and at the supervised worker boundary (the worker
may be reaped and its process receipt retained before the preflight deadline).
The release path's 14,400-second whole-operation budget is unchanged.
"""

from __future__ import annotations

PREFLIGHT_MAX_OPERATION_SECONDS = 1800
LAUNCH_RETENTION_RESERVE_SECONDS = 30
WORKER_RETENTION_RESERVE_SECONDS = 15


def preflight_inner_timeout_seconds(outer_timeout_seconds: int) -> int:
    """Return the inner preflight clock leaving the outer launch retention tail."""
    if type(outer_timeout_seconds) is not int or not 0 < outer_timeout_seconds <= PREFLIGHT_MAX_OPERATION_SECONDS:
        raise ValueError("diagnostic preflight outer budget is outside its bounded operation")
    inner = outer_timeout_seconds - LAUNCH_RETENTION_RESERVE_SECONDS
    if inner <= 0:
        raise ValueError("diagnostic preflight outer budget cannot leave a positive inner operation")
    return inner


__all__ = [
    "LAUNCH_RETENTION_RESERVE_SECONDS",
    "PREFLIGHT_MAX_OPERATION_SECONDS",
    "WORKER_RETENTION_RESERVE_SECONDS",
    "preflight_inner_timeout_seconds",
]
