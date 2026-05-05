"""Real-data tests for ``infrastructure.core.telemetry.retention``.

Zero-Mock policy: every test creates real files in a ``tmp_path``
``reports/`` directory and asserts on the actual file-system state after
``rotate()``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.core.telemetry.retention import RotationResult, rotate


def _make_archived(reports_dir: Path, count: int, *, archive_subdir: str = ".history") -> list[Path]:
    """Populate ``reports_dir/<archive_subdir>/`` with ``count`` synthetic
    ``telemetry-<ts>.json`` files at distinct, monotonically increasing
    timestamps.

    Returns the created paths in oldest-first order so callers can
    assert on which were pruned.
    """

    archive_dir = reports_dir / archive_subdir
    archive_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    # Spread synthetic timestamps over a large window so lexicographic
    # sort matches chronological order even on filesystems with
    # second-resolution mtimes.
    base = 1_700_000_000
    for i in range(count):
        ts = base + i
        path = archive_dir / f"telemetry-{ts}.json"
        path.write_text(json.dumps({"synthetic": True, "index": i}), encoding="utf-8")
        created.append(path)
    return created


def _live_file(reports_dir: Path) -> Path:
    """Create a synthetic in-flight ``telemetry.json`` inside ``reports_dir``."""

    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / "telemetry.json"
    path.write_text(json.dumps({"current_run": True}), encoding="utf-8")
    return path


# ── 12-run scenario (acceptance criterion) ──────────────────────────


class TestTwelveRunScenario:
    """Acceptance: running rotate 12 times keeps at most 10 archived files."""

    def test_twelve_historical_files_pruned_to_keep(self, tmp_path: Path) -> None:
        reports_dir = tmp_path / "reports"
        # Simulate 11 prior runs already archived plus one in-flight file
        # left over from the 12th run, which rotate() will move into the
        # archive — totaling 12 archived candidates before pruning.
        _make_archived(reports_dir, 11)
        _live_file(reports_dir)

        result = rotate(reports_dir, keep=10)

        assert isinstance(result, RotationResult)
        assert result.archived == 1
        # 12 candidates - keep=10 -> prune 2
        assert result.pruned == 2
        assert result.kept == 10

        # Live file is gone (rotated)
        assert not (reports_dir / "telemetry.json").exists()
        # Exactly 10 files remain in the archive
        archive_files = sorted((reports_dir / ".history").iterdir())
        assert len(archive_files) == 10
        for p in archive_files:
            assert p.name.startswith("telemetry-")
            assert p.suffix == ".json"


# ── Idempotence ────────────────────────────────────────────────────


class TestIdempotence:
    """Re-entry without a new live file is a no-op for archiving."""

    def test_second_call_does_not_archive(self, tmp_path: Path) -> None:
        reports_dir = tmp_path / "reports"
        _make_archived(reports_dir, 5)
        _live_file(reports_dir)

        first = rotate(reports_dir, keep=10)
        assert first.archived == 1
        assert first.pruned == 0
        assert first.kept == 6

        # No new live file → second call is a no-op for archiving and pruning.
        second = rotate(reports_dir, keep=10)
        assert second.archived == 0
        assert second.pruned == 0
        assert second.kept == 6

        # Archive contents unchanged.
        archive_files = sorted((reports_dir / ".history").iterdir())
        assert len(archive_files) == 6


# ── Edge cases ──────────────────────────────────────────────────────


class TestEdgeCases:
    """Empty / missing / keep=0 boundary behaviours."""

    def test_missing_reports_dir_is_noop(self, tmp_path: Path) -> None:
        missing = tmp_path / "does" / "not" / "exist"
        result = rotate(missing, keep=10)
        assert result == RotationResult(archived=0, pruned=0, kept=0)
        assert not missing.exists()  # function does NOT create the dir

    def test_empty_reports_dir_is_noop(self, tmp_path: Path) -> None:
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        result = rotate(reports_dir, keep=10)
        assert result == RotationResult(archived=0, pruned=0, kept=0)
        # Function may not create archive subdir when there is nothing to rotate.
        assert list(reports_dir.iterdir()) == []

    def test_keep_zero_prunes_everything(self, tmp_path: Path) -> None:
        reports_dir = tmp_path / "reports"
        _make_archived(reports_dir, 3)
        _live_file(reports_dir)

        result = rotate(reports_dir, keep=0)

        # Live file rotated, then everything pruned.
        assert result.archived == 1
        assert result.pruned == 4
        assert result.kept == 0
        assert not (reports_dir / "telemetry.json").exists()
        archive_dir = reports_dir / ".history"
        # Archive directory may exist but must be empty.
        if archive_dir.exists():
            assert list(archive_dir.iterdir()) == []

    def test_negative_keep_raises(self, tmp_path: Path) -> None:
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        with pytest.raises(ValueError):
            rotate(reports_dir, keep=-1)

    def test_no_live_file_only_prunes(self, tmp_path: Path) -> None:
        reports_dir = tmp_path / "reports"
        _make_archived(reports_dir, 12)

        result = rotate(reports_dir, keep=10)
        assert result.archived == 0
        assert result.pruned == 2
        assert result.kept == 10

    def test_custom_archive_subdir(self, tmp_path: Path) -> None:
        reports_dir = tmp_path / "reports"
        _live_file(reports_dir)

        result = rotate(reports_dir, keep=10, archive_subdir="archive")
        assert result.archived == 1
        assert (reports_dir / "archive").is_dir()
        assert not (reports_dir / ".history").exists()
        archived = list((reports_dir / "archive").iterdir())
        assert len(archived) == 1
        assert archived[0].name.startswith("telemetry-")

    def test_same_second_collision_does_not_overwrite(self, tmp_path: Path) -> None:
        """Two rotations in the same second must keep both archived files."""

        reports_dir = tmp_path / "reports"
        archive_dir = reports_dir / ".history"

        # First rotation: produces telemetry-<ts>.json under archive/.
        live1 = _live_file(reports_dir)
        live1_mtime = live1.stat().st_mtime

        first = rotate(reports_dir, keep=10)
        assert first.archived == 1
        assert first.kept == 1

        # Second rotation: write a new live file and force the same mtime
        # so the archive candidate filename collides with the previous one.
        live2 = _live_file(reports_dir)
        import os as _os

        _os.utime(live2, (live1_mtime, live1_mtime))

        second = rotate(reports_dir, keep=10)
        assert second.archived == 1
        # Both rotations preserved — collision suffix kicked in.
        assert second.kept == 2
        archived_files = sorted(archive_dir.iterdir())
        assert len(archived_files) == 2
        assert archived_files[0].name != archived_files[1].name


# ── Collector integration ──────────────────────────────────────────


class TestCollectorIntegration:
    """End-to-end: ``TelemetryCollector.finalize()`` triggers rotation."""

    def test_collector_finalize_rotates_previous_report(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from infrastructure.core.telemetry.collector import TelemetryCollector
        from infrastructure.core.telemetry.config import TelemetryConfig

        output_dir = tmp_path / "out"
        reports_dir = output_dir / "reports"
        reports_dir.mkdir(parents=True)
        # Pre-existing previous telemetry.json from a prior run.
        prior = reports_dir / "telemetry.json"
        prior.write_text(json.dumps({"prior_run": True}), encoding="utf-8")

        monkeypatch.setenv("TELEMETRY_KEEP", "5")

        config = TelemetryConfig(
            enabled=True,
            track_resources=False,
            track_diagnostics=False,
            output_formats=["json"],
            persist_report=True,
        )
        collector = TelemetryCollector(config, "p", output_dir)
        collector.finalize(total_duration=0.0)

        # Prior report rotated into archive.
        archived = list((reports_dir / ".history").iterdir())
        assert len(archived) == 1
        assert archived[0].name.startswith("telemetry-")
        # New telemetry.json written for the current run.
        assert (reports_dir / "telemetry.json").exists()
        loaded = json.loads((reports_dir / "telemetry.json").read_text(encoding="utf-8"))
        # The new file is the current report, not the prior one.
        assert "prior_run" not in loaded
        assert loaded["project_name"] == "p"
