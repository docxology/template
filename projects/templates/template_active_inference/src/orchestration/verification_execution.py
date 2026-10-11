"""Existing-runtime selection and a finite budget for one verifier session."""

from __future__ import annotations

import math
import os
import sys
import time
from pathlib import Path


class VerificationRuntimeUnavailable(RuntimeError):
    """A nominated existing interpreter cannot execute the verification flow."""


class VerificationDeadlineExceeded(TimeoutError):
    """The whole verifier or one of its supervised commands exhausted its budget."""


class VerificationCommandFailed(RuntimeError):
    """Retain an actual command exit separately from its supervisory outcome."""

    def __init__(
        self,
        diagnostic: str,
        *,
        original_exit_code: int | None,
        timed_out: bool = False,
        custody_refused: bool = False,
    ) -> None:
        super().__init__(diagnostic)
        self.original_exit_code = original_exit_code
        self.timed_out = timed_out
        self.custody_refused = custody_refused
        self.attempt_exit_codes = (original_exit_code,) if original_exit_code is not None else ()

    @property
    def exit_code(self) -> int:
        if self.original_exit_code in {130, -2}:
            return 130
        if self.timed_out or self.original_exit_code == 124:
            return 124
        if self.original_exit_code not in {None, 0, 75}:
            return 1
        return 75 if self.custody_refused or self.original_exit_code == 75 else 1


def selected_verification_python(project_root: Path, *, receipt_bound: bool = False) -> str:
    """Keep the outer pinned test stack, or nominate an existing lexical venv."""
    if receipt_bound:
        selected = Path(sys.executable).absolute()
    else:
        environment = project_root.absolute() / ".venv"
        if os.path.lexists(environment):
            if environment.is_symlink() or not environment.is_dir():
                raise VerificationRuntimeUnavailable("Project .venv must be an existing real directory")
            configuration = environment / "pyvenv.cfg"
            if configuration.is_symlink() or not configuration.is_file():
                raise VerificationRuntimeUnavailable("Project runtime configuration is unavailable")
            binary = environment / ("Scripts" if os.name == "nt" else "bin")
            if binary.is_symlink() or not binary.is_dir():
                raise VerificationRuntimeUnavailable("Project runtime binary directory is unavailable")
            selected = binary / ("python.exe" if os.name == "nt" else "python")
        else:
            selected = Path(sys.executable).absolute()
    if not selected.is_file() or not os.access(selected, os.X_OK):
        raise VerificationRuntimeUnavailable("Selected verification interpreter is unavailable; prepare it explicitly")
    return str(selected)


def verification_deadline(start: float, command_budgets: list[int], *, requested: float | None = None) -> float:
    """Compose finite command ceilings within the declared 6900-second verifier."""
    if requested is not None and (type(requested) not in (int, float) or not math.isfinite(requested)):
        raise ValueError("Verification deadline must be a finite monotonic value")
    budget = min(6900, sum(command_budgets))
    if budget <= 0:
        raise ValueError("Verification requires a nonempty positive command budget")
    return min(start + budget, requested) if requested is not None else start + budget


def remaining_verification_budget(deadline: float) -> float:
    """Refuse a child or success promotion after the original session deadline."""
    if type(deadline) not in (int, float) or not math.isfinite(deadline):
        raise ValueError("Verification deadline must be a finite monotonic value")
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise VerificationDeadlineExceeded("Whole-verifier deadline exhausted")
    return remaining
