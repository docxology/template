"""One finite source DATA admission shared by an own project's consumers."""

from __future__ import annotations

import math
import os
import time
from collections.abc import Mapping
from pathlib import Path

from infrastructure.project.public_reference import PublicReference, admit_public_reference, reference_binding


class ReferenceSession:
    """Retain an explicit reference and the original operation deadline.

    No binding leaves ordinary checkout discovery to the caller and grants no
    DATA acceptance. An admitted binding cannot be removed or replaced halfway
    through an operation. This class is not a process/resource supervisor.
    """

    def __init__(self, environment: Mapping[str, str] | None = None, *, timeout_seconds: float = 7200.0) -> None:
        if (
            type(timeout_seconds) not in (int, float)
            or not math.isfinite(timeout_seconds)
            or not 0 < timeout_seconds <= 14400
        ):
            raise ValueError("source DATA session requires a positive finite budget at most 14400 seconds")
        self.environment = os.environ if environment is None else environment
        self.timeout_seconds = timeout_seconds
        self.binding: tuple[Path, str, str] | None = None
        self.reference: PublicReference | None = None
        self.deadline: float | None = None

    def current(self, *, explicit_root: Path | None = None) -> PublicReference | None:
        """Admit once and refuse subsequent binding changes or a conflicting locator."""
        binding = reference_binding(self.environment)
        if self.binding is not None and binding != self.binding:
            raise ValueError("source DATA binding changed after the original admission")
        if binding is None:
            return None
        if explicit_root is not None and explicit_root.absolute() != binding[0].absolute():
            raise ValueError("source DATA binding conflicts with the explicit repository locator")
        if self.deadline is None:
            self.deadline = time.monotonic() + self.timeout_seconds
            self.binding = binding
        if time.monotonic() >= self.deadline:
            raise TimeoutError("source DATA session exhausted its original deadline")
        if self.reference is None:
            self.reference = admit_public_reference(
                binding[0], expected_commit=binding[1], expected_source_identity=binding[2], deadline=self.deadline
            )
        if self.deadline is None or time.monotonic() >= self.deadline:
            raise TimeoutError("source DATA session exhausted its original deadline")
        return self.reference

    def tracked_paths(self, *, explicit_root: Path | None = None) -> tuple[str, ...] | None:
        """Return original Root index paths from this same admitted reference.

        A Root gitlink contributes its one original path. Nested submodule files
        are not expanded: numerical consumers retain native Root ``ls-files``
        membership. The final source/SDK verification remains required.
        """
        reference = self.current(explicit_root=explicit_root)
        if reference is None:
            return None
        return tuple(sorted(row.path for row in (*reference.git.files, *reference.git.gitlinks)))

    def verify(self) -> None:
        """Require the original binding, complete source and selected SDK before success."""
        reference = self.current()
        if reference is not None:
            if self.deadline is None:
                raise ValueError("admitted source DATA session lacks its original deadline")
            reference.verify_unchanged(deadline=self.deadline)


__all__ = ["ReferenceSession"]
