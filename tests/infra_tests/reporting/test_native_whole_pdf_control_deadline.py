"""One whole-PDF control phase stays inside its cell without starving its suite.

The hosted native inventory truncated a control phase at 600.7 s while the
original caller clock still held 4,418 s; its nested child was squeezed to
241.2 s and timed out. This pins the replacement arithmetic and the provisioned
cell fit as DATA predicates rather than re-testing the launch path.
"""

from __future__ import annotations

import time

from infrastructure.reporting.native_pdf_whole_control_supervisor import (
    CONTROL_PHASE_CEILING_SECONDS,
    control_phase_deadline,
)


def test_control_phase_uses_the_ceiling_when_the_caller_clock_is_farther() -> None:
    now = time.monotonic()
    assert control_phase_deadline(12_000.0, now=0.0) == CONTROL_PHASE_CEILING_SECONDS
    assert control_phase_deadline(now + 60_000.0, now=now) == now + CONTROL_PHASE_CEILING_SECONDS


def test_control_phase_never_extends_the_original_caller_clock() -> None:
    assert control_phase_deadline(100.0, now=0.0) == 100.0
    assert control_phase_deadline(0.0, now=0.0) == 0.0
    assert control_phase_deadline(-5.0, now=10.0) == -5.0


def test_control_ceiling_fits_the_provisioned_per_project_cell() -> None:
    """Three phases fit the minimum 12,000 s cell and stay below stage policy."""
    assert CONTROL_PHASE_CEILING_SECONDS * 3 <= 12_000.0
    assert CONTROL_PHASE_CEILING_SECONDS < 86_400.0
    assert CONTROL_PHASE_CEILING_SECONDS > 600.7
