"""Run pymdp sophisticated-inference T-maze simulation (facade)."""

from __future__ import annotations

from simulation.si_artifacts import run_and_persist, write_si_artifacts
from simulation.si_loop import SIRunResult, pymdp_available, run_si_tmaze


__all__ = [
    "SIRunResult",
    "pymdp_available",
    "run_and_persist",
    "run_si_tmaze",
    "write_si_artifacts",
]
