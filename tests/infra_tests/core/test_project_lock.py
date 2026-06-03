"""Tests for the per-project output lock (no mocks; real fcntl + real env)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from infrastructure.core.files.project_lock import (
    _env_var,
    _lock_key,
    _lock_path,
    project_output_lock,
)


def test_uncontended_acquire_sets_and_clears_env_marker(tmp_path: Path) -> None:
    """Holding the lock exports the re-entrancy marker; exit clears it."""
    env_var = _env_var(_lock_key(tmp_path))
    assert env_var not in os.environ
    with project_output_lock(tmp_path):
        assert os.environ.get(env_var) == "1"
    assert env_var not in os.environ


def test_reentrant_acquire_is_noop_while_marker_present(tmp_path: Path) -> None:
    """A nested acquire on the same project does not block or re-lock.

    Simulates the pipeline-executor (outer) spawning its test stage (inner):
    the inner acquisition must be a no-op so it cannot deadlock against the
    outer holder. With the marker present, the inner context returns even
    though the OS lock is already held.
    """
    with project_output_lock(tmp_path):
        # Inner acquire returns immediately (no-op) — would hang on a real
        # blocking lock if re-entrancy were broken.
        with project_output_lock(tmp_path, timeout=0.5):
            assert os.environ.get(_env_var(_lock_key(tmp_path))) == "1"


def test_mutual_exclusion_times_out_when_held_by_another_descriptor(tmp_path: Path) -> None:
    """A second, independent holder cannot acquire while the lock is held."""
    import fcntl

    lock_file = _lock_path(_lock_key(tmp_path))
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    holder = open(lock_file, "w", encoding="utf-8")  # noqa: SIM115 - explicit lifetime
    try:
        fcntl.flock(holder.fileno(), fcntl.LOCK_EX)
        # The env marker is NOT set (a different "process"/descriptor holds it),
        # so project_output_lock must contend on the real OS lock and time out.
        with pytest.raises(TimeoutError):
            with project_output_lock(tmp_path, timeout=0.4):
                pass
    finally:
        fcntl.flock(holder.fileno(), fcntl.LOCK_UN)
        holder.close()


def test_acquires_after_holder_releases(tmp_path: Path) -> None:
    """Once the prior holder releases, acquisition succeeds normally."""
    import fcntl

    lock_file = _lock_path(_lock_key(tmp_path))
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_file, "w", encoding="utf-8") as holder:
        fcntl.flock(holder.fileno(), fcntl.LOCK_EX)
        fcntl.flock(holder.fileno(), fcntl.LOCK_UN)
    # Lock is free now; this should acquire without raising.
    with project_output_lock(tmp_path, timeout=1.0):
        assert os.environ.get(_env_var(_lock_key(tmp_path))) == "1"
