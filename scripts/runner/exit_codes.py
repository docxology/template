#!/usr/bin/env python3
"""Canonical exit-code contract for orchestrator scripts.

The pipeline stages and standalone orchestrators in ``scripts/`` have
long agreed on an exit-code convention *in prose docstrings* — but the contract
was never expressed as code, so an agent (or a calling script) had to read each
docstring to learn what ``2`` means for a given stage. This module names that
existing contract so it becomes programmatically discoverable via introspection.

``ExitCode`` is an :class:`enum.IntEnum`: every member compares equal to the
plain integer the scripts already return, so importing and using it changes no
behavior anywhere. It only gives the integers names.

Observed conventions this enum unifies (see the cited docstrings):

* ``pipeline/stage_00_setup.py`` — ``0`` success, ``1`` failure.
* ``pipeline/stage_06_llm_review.py`` — ``0`` success, ``1`` hard failure, ``2`` graceful
  skip (Ollama unavailable / no model installed; callers treat as non-fatal).
* ``publish/publish_project_release.py`` — ``0`` success, ``1`` publish/render failure,
  ``2`` missing PDF / credentials / invalid inputs.

Usage::

    from scripts.runner.exit_codes import ExitCode

    if ollama_unavailable:
        return ExitCode.SKIP          # == 2
    return ExitCode.SUCCESS           # == 0

    # Classify another process's result without parsing its docstring:
    if ExitCode(proc.returncode) is ExitCode.SKIP:
        ...
"""

from __future__ import annotations

from enum import IntEnum

__all__ = ["ExitCode"]


class ExitCode(IntEnum):
    """Named exit codes shared by ``scripts/`` orchestrators.

    Members are plain integers (``IntEnum``); ``ExitCode.SUCCESS == 0`` etc., so
    returning a member is identical to returning the bare int the scripts
    already use. The enum exists to make the contract introspectable, not to
    change any return value.
    """

    SUCCESS = 0
    """The operation completed successfully."""

    FAILURE = 1
    """A hard, unrecoverable failure (config error, runtime error, publish/render failure)."""

    SKIP = 2
    """A graceful, non-fatal skip — e.g. an optional dependency (Ollama) is
    unavailable. Callers should treat this as success-with-no-work, not as an
    error. Also used by some scripts for "missing inputs/credentials"; consult
    the individual script's docstring for its precise ``2`` meaning."""

    VALIDATION_FAILED = 3
    """Inputs were present but failed validation (reserved; available to new
    orchestrators that want to distinguish validation failure from FAILURE)."""

    MISSING_DEPENDENCY = 4
    """A required tool, credential, or artifact is missing (reserved; available
    to new orchestrators that want a distinct code from the SKIP soft-path)."""

    @property
    def is_success(self) -> bool:
        """True for :attr:`SUCCESS`."""
        return self is ExitCode.SUCCESS

    @property
    def is_soft_skip(self) -> bool:
        """True for :attr:`SKIP` — the non-fatal "no work performed" path."""
        return self is ExitCode.SKIP
