"""Telemetry retention policy.

Rotates the previous run's ``telemetry.json`` (if any) into an archive
sub-directory and prunes archived files beyond a configurable retention
window. The in-flight ``telemetry.json`` for the current run is never
touched by ``rotate()`` — it only acts on files that already exist
*before* the current write.

Naming and semantics intentionally mirror
``infrastructure.core.files.cleanup``:

* ``rotate(reports_dir, *, keep=10, archive_subdir=".history")`` — moves
  the previous ``telemetry.json`` into ``<reports_dir>/<archive_subdir>/``
  with a ``telemetry-<unix_ts>.json`` filename, then prunes the oldest
  archived files until at most ``keep`` remain.
* ``RotationResult`` — frozen dataclass summarizing what happened so
  callers (and tests) can assert outcomes deterministically.

The function is idempotent: running it twice in a row when no new
``telemetry.json`` is present returns ``RotationResult(0, 0, n)``, where
``n`` is the count already in the archive (capped at ``keep``).

Thin-orchestrator boundary: this module is pure file-system bookkeeping.
It performs no formatting, contains no business logic, and never imports
the collector — the collector imports it.
"""

import time
from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

__all__ = [
    "RotationResult",
    "rotate",
]


@dataclass(frozen=True)
class RotationResult:
    """Outcome of a single ``rotate()`` call.

    Attributes:
        archived: Number of ``telemetry.json`` files moved into the
            archive sub-directory during this call. ``0`` when there was
            no previous run to rotate (idempotent re-entry).
        pruned: Number of archived files deleted because they exceeded
            the ``keep`` retention window. Pruning happens oldest-first.
        kept: Number of archived files remaining in the archive
            sub-directory after the call. Always ``<= keep`` (and ``0``
            when ``keep == 0``).
    """

    archived: int
    pruned: int
    kept: int


def _archive_filename(timestamp: float) -> str:
    """Build the canonical archived-telemetry filename for ``timestamp``.

    Uses an integer Unix timestamp so filenames sort lexicographically in
    chronological order.
    """

    return f"telemetry-{int(timestamp)}.json"


def _next_archive_path(archive_dir: Path, timestamp: float) -> Path:
    """Return a non-colliding archive path for ``timestamp``.

    When two rotations happen within the same second (e.g. tests, fast
    re-runs), append a ``-N`` discriminator so neither file is lost.
    """

    candidate = archive_dir / _archive_filename(timestamp)
    if not candidate.exists():
        return candidate

    # Same-second collision: append a deterministic suffix.
    suffix = 1
    while True:
        alt = archive_dir / f"telemetry-{int(timestamp)}-{suffix}.json"
        if not alt.exists():
            return alt
        suffix += 1


def _list_archived(archive_dir: Path) -> list[Path]:
    """Return archived telemetry files sorted oldest-first.

    Sort is by filename (lexicographic on ``telemetry-<ts>[-N].json``),
    which is equivalent to chronological order because ``<ts>`` is a
    zero-padding-free integer of identical width for any realistic
    timeframe and the optional ``-N`` discriminator only orders within
    the same second.
    """

    if not archive_dir.is_dir():
        return []
    return sorted(
        p for p in archive_dir.iterdir() if p.is_file() and p.name.startswith("telemetry-") and p.suffix == ".json"
    )


def rotate(
    reports_dir: Path,
    *,
    keep: int = 10,
    archive_subdir: str = ".history",
) -> RotationResult:
    """Rotate the previous ``telemetry.json`` into an archive folder.

    Behaviour:

    * If ``reports_dir`` does not exist, the call is a no-op and returns
      ``RotationResult(0, 0, 0)``. The directory is *not* created — that
      is the responsibility of the caller that is about to write the
      next ``telemetry.json``.
    * If ``reports_dir/telemetry.json`` exists, it is moved to
      ``reports_dir/<archive_subdir>/telemetry-<unix_ts>.json``. The
      timestamp is the file's modification time so the archive filename
      reflects when that report was produced, not when it was rotated.
    * After the optional move, archived files in
      ``reports_dir/<archive_subdir>/`` are pruned oldest-first until
      at most ``keep`` remain. ``keep=0`` archives everything and then
      prunes everything, leaving the archive empty.

    The in-flight ``telemetry.json`` is never created or removed by this
    function — only any *previous* run's file is rotated.

    Args:
        reports_dir: Directory holding ``telemetry.json``. Typically
            ``projects/<name>/output/reports/`` or
            ``output/<name>/reports/``.
        keep: Maximum number of archived files to retain in the archive
            sub-directory after rotation. Must be ``>= 0``. Defaults to
            ``10``.
        archive_subdir: Name of the archive sub-directory, relative to
            ``reports_dir``. Defaults to ``".history"`` (hidden so it
            does not pollute interactive listings of the reports
            folder).

    Returns:
        A ``RotationResult`` describing how many files were archived,
        how many were pruned, and how many remain in the archive.

    Raises:
        ValueError: If ``keep`` is negative.
    """

    if keep < 0:
        raise ValueError(f"keep must be >= 0, got {keep}")

    if not reports_dir.is_dir():
        logger.debug(f"Telemetry retention: reports_dir does not exist, skipping: {reports_dir}")
        return RotationResult(archived=0, pruned=0, kept=0)

    archive_dir = reports_dir / archive_subdir
    live_report = reports_dir / "telemetry.json"

    archived = 0
    if live_report.is_file():
        archive_dir.mkdir(parents=True, exist_ok=True)
        try:
            mtime = live_report.stat().st_mtime
        except OSError:
            mtime = time.time()
        target = _next_archive_path(archive_dir, mtime)
        live_report.rename(target)
        archived = 1
        logger.debug(f"Telemetry retention: archived {live_report} -> {target}")

    archived_files = _list_archived(archive_dir)

    pruned = 0
    if len(archived_files) > keep:
        excess = len(archived_files) - keep
        for old in archived_files[:excess]:
            try:
                old.unlink()
                pruned += 1
                logger.debug(f"Telemetry retention: pruned {old}")
            except OSError as e:
                logger.warning(f"Telemetry retention: failed to prune {old}: {e}")
        archived_files = archived_files[excess:]

    return RotationResult(archived=archived, pruned=pruned, kept=len(archived_files))
