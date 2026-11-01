"""Real three-level process proof for the bounded preflight clock and its tails.

The hosted `native-preflight` failure was a true deadline exhaustion whose outer
watcher killed the inner owner at the same instant, so the inner owner never
retained its worker process, cleanup or guardian receipts. These cases run the
real `run_native_tool_process` watcher at every level with a real grandchild
that deliberately outlives every clock:

* outer  - `native_installed_launcher`, whose operation clock is the bounded
  preflight budget;
* inner  - the preflight owner, which must return its receipts inside that
  clock, so it takes `LAUNCH_RETENTION_RESERVE_SECONDS` off its own deadline;
* worker - the supervised native worker, which takes
  `WORKER_RETENTION_RESERVE_SECONDS` off the preflight deadline so its watcher
  reaps it and retains `original-native-worker.native-process.json` before the
  preflight owner's own clock ends.

`test_reserved_tails_retain_the_inner_owner_and_worker_receipts` uses the actual
production reserves. `test_one_shared_clock_loses_the_inner_owners_receipt`
keeps the original one-clock arrangement as the negative control that reproduces
the hosted retention loss.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import time

import pytest

from infrastructure.reporting.native_preflight_budget import (
    LAUNCH_RETENTION_RESERVE_SECONDS,
    PREFLIGHT_MAX_OPERATION_SECONDS,
    WORKER_RETENTION_RESERVE_SECONDS,
    preflight_inner_timeout_seconds,
)

ROOT = Path(__file__).resolve().parents[3]

_DRIVER = textwrap.dedent(
    """
    import json, os, sys, time
    from pathlib import Path

    root, role, outer_text, inner_text, leaf_text, inner_dir_text, outer_dir_text = sys.argv[1:8]
    sys.path.insert(0, root)
    from infrastructure.reporting.native_tool_process import run_native_tool_process

    LEAF = "import time\\ntime.sleep(120)\\n"
    inner_dir = Path(inner_dir_text)
    outer_dir = Path(outer_dir_text)
    if role == "leaf-watcher":
        try:
            result = run_native_tool_process(
                inner_dir,
                sys.executable,
                ["-c", LEAF],
                cwd=inner_dir,
                env=dict(os.environ),
                deadline=float(leaf_text),
                purpose="original-native-worker",
                preserve_nominated_launcher=True,
            )
        except BaseException as error:
            result = {"raised": type(error).__name__}
        (inner_dir / "inner-owner-retained.json").write_text(
            json.dumps(
                {
                    key: result.get(key)
                    for key in ("pid", "original_exit_code", "timed_out", "accepted", "diagnostics", "cleanup")
                },
                sort_keys=True,
            )
            + "\\n"
        )
        raise SystemExit(124 if result.get("timed_out") else 0)
    result = run_native_tool_process(
        outer_dir,
        sys.executable,
        [
            sys.argv[0], root, "leaf-watcher", outer_text, inner_text, leaf_text,
            str(inner_dir), str(outer_dir),
        ],
        cwd=inner_dir,
        env=dict(os.environ),
        deadline=float(inner_text),
        purpose="installed-native-original",
        preserve_nominated_launcher=True,
    )
    (outer_dir / "outer-owner-observed.json").write_text(
        json.dumps(
            {key: result.get(key) for key in ("original_exit_code", "timed_out", "accepted", "diagnostics", "cleanup")},
            sort_keys=True,
        )
        + "\\n"
    )
    """
)


def _run_nested(
    tmp_path: Path, *, leaf_seconds: float, launch_reserve: float, worker_reserve: float
) -> tuple[Path, Path]:
    """Run outer -> inner -> worker watchers with real deadlines; return both evidence roots."""
    driver = tmp_path / "nested_deadline_driver.py"
    driver.write_text(_DRIVER)
    inner_dir = tmp_path / "inner-owner"
    outer_dir = tmp_path / "outer-owner"
    inner_dir.mkdir(mode=0o700)
    outer_dir.mkdir(mode=0o700)
    started = time.monotonic()
    leaf_deadline = started + leaf_seconds
    inner_deadline = leaf_deadline + worker_reserve
    outer_deadline = inner_deadline + launch_reserve
    result = subprocess.run(
        [
            sys.executable,
            str(driver),
            str(ROOT),
            "outer",
            str(outer_deadline),
            str(inner_deadline),
            str(leaf_deadline),
            str(inner_dir),
            str(outer_dir),
        ],
        cwd=tmp_path,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
        capture_output=True,
        text=True,
        timeout=leaf_seconds + launch_reserve + worker_reserve + 60,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return inner_dir, outer_dir


def test_preflight_clock_is_bounded_and_strictly_reserves_its_retention_tails() -> None:
    assert 900 < PREFLIGHT_MAX_OPERATION_SECONDS <= 14400
    assert 0 < WORKER_RETENTION_RESERVE_SECONDS < LAUNCH_RETENTION_RESERVE_SECONDS < 120
    inner = preflight_inner_timeout_seconds(PREFLIGHT_MAX_OPERATION_SECONDS)
    assert inner == PREFLIGHT_MAX_OPERATION_SECONDS - LAUNCH_RETENTION_RESERVE_SECONDS
    assert inner > WORKER_RETENTION_RESERVE_SECONDS
    for refused in (0, -1, PREFLIGHT_MAX_OPERATION_SECONDS + 1, 14400):
        with pytest.raises(ValueError):
            preflight_inner_timeout_seconds(refused)


def test_both_owners_bind_the_audited_budget_and_worker_reserve() -> None:
    """Structural binding: the owners name the audited budget and reserve.

    This proves the shipped wiring references one budget owner, not that a full
    native pass occurred; the nested-process cases prove the reserve mechanism,
    and only a hosted preflight run can prove the complete lifecycle.
    """
    from infrastructure.reporting.native_format_acceptance import _run_original_native_cells
    from infrastructure.reporting.native_installed_launcher import main as launch_main
    from infrastructure.reporting.native_installed_preflight import main as preflight_main

    assert "PREFLIGHT_MAX_OPERATION_SECONDS" in launch_main.__code__.co_names
    assert "preflight_inner_timeout_seconds" in launch_main.__code__.co_names
    assert "PREFLIGHT_MAX_OPERATION_SECONDS" in preflight_main.__code__.co_names
    assert "WORKER_RETENTION_RESERVE_SECONDS" in _run_original_native_cells.__code__.co_names


@pytest.mark.skipif(os.name != "posix", reason="the native watcher requires owned POSIX evidence")
@pytest.mark.timeout(180)
def test_reserved_tails_retain_the_inner_owner_and_worker_receipts(tmp_path: Path) -> None:
    inner_dir, outer_dir = _run_nested(
        tmp_path,
        leaf_seconds=8.0,
        launch_reserve=float(LAUNCH_RETENTION_RESERVE_SECONDS),
        worker_reserve=float(WORKER_RETENTION_RESERVE_SECONDS),
    )
    retained = json.loads((inner_dir / "inner-owner-retained.json").read_text())
    observed = json.loads((outer_dir / "outer-owner-observed.json").read_text())
    assert retained["timed_out"] is True
    assert retained["cleanup"]["root_reaped"] is True
    assert (inner_dir / "original-native-worker.native-process.json").exists()
    assert observed["original_exit_code"] == 124
    assert observed["timed_out"] is False
    assert observed["accepted"] is True
    assert observed["cleanup"]["guardian_finished"] is True
    assert observed["cleanup"]["root_reaped"] is True


@pytest.mark.skipif(os.name != "posix", reason="the native watcher requires owned POSIX evidence")
@pytest.mark.timeout(180)
def test_one_shared_clock_loses_the_inner_owners_receipt(tmp_path: Path) -> None:
    inner_dir, outer_dir = _run_nested(tmp_path, leaf_seconds=8.0, launch_reserve=0.0, worker_reserve=0.0)
    assert not (inner_dir / "inner-owner-retained.json").exists()
    assert not (inner_dir / "original-native-worker.native-process.json").exists()
    observed = json.loads((outer_dir / "outer-owner-observed.json").read_text())
    assert observed["accepted"] is False
    assert observed["cleanup"]["root_reaped"] is True
    assert any("retention exceeded the original deadline" in item for item in observed["diagnostics"])
