"""Line-count scanning for Layer 1 and project script directories."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LineCountThresholds:
    warn_at: int
    fail_at: int


DEFAULT_INFRA_THRESHOLDS = LineCountThresholds(warn_at=800, fail_at=950)
DEFAULT_PROJECT_SCRIPT_THRESHOLDS = LineCountThresholds(warn_at=150, fail_at=250)
DEFAULT_TEST_THRESHOLDS = LineCountThresholds(warn_at=800, fail_at=10_000)


def count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def scan_line_counts(
    repo_root: Path,
    roots: tuple[str, ...],
    *,
    thresholds: LineCountThresholds,
    allowlist: frozenset[str] = frozenset(),
) -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
    """Return (warnings, failures) as lists of (relative_path, line_count)."""
    warnings: list[tuple[str, int]] = []
    failures: list[tuple[str, int]] = []
    for root_name in roots:
        root = repo_root / root_name
        if not root.is_dir():
            continue
        for py_file in root.rglob("*.py"):
            rel = py_file.relative_to(repo_root).as_posix()
            if rel in allowlist:
                continue
            count = count_lines(py_file)
            if count >= thresholds.fail_at:
                failures.append((rel, count))
            elif count >= thresholds.warn_at:
                warnings.append((rel, count))
    return warnings, failures


def scan_infrastructure_and_scripts(
    repo_root: Path,
    *,
    allowlist: frozenset[str] = frozenset(),
) -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
    return scan_line_counts(
        repo_root,
        ("infrastructure", "scripts"),
        thresholds=DEFAULT_INFRA_THRESHOLDS,
        allowlist=allowlist,
    )


def scan_project_scripts(
    repo_root: Path,
    *,
    allowlist: frozenset[str] = frozenset(),
) -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
    from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

    warnings: list[tuple[str, int]] = []
    failures: list[tuple[str, int]] = []
    for name in PUBLIC_PROJECT_NAMES:
        scripts_dir = repo_root / "projects" / name / "scripts"
        if not scripts_dir.is_dir():
            continue
        rel_root = scripts_dir.relative_to(repo_root).as_posix()
        part_warnings, part_failures = scan_line_counts(
            repo_root,
            (rel_root,),
            thresholds=DEFAULT_PROJECT_SCRIPT_THRESHOLDS,
            allowlist=allowlist,
        )
        warnings.extend(part_warnings)
        failures.extend(part_failures)
    return warnings, failures


def scan_project_src(
    repo_root: Path,
    *,
    allowlist: frozenset[str] = frozenset(),
) -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
    """Scan ``projects/*/src/`` with the same thresholds as Layer 1."""
    from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

    warnings: list[tuple[str, int]] = []
    failures: list[tuple[str, int]] = []
    for name in PUBLIC_PROJECT_NAMES:
        src_dir = repo_root / "projects" / name / "src"
        if not src_dir.is_dir():
            continue
        rel_root = src_dir.relative_to(repo_root).as_posix()
        part_warnings, part_failures = scan_line_counts(
            repo_root,
            (rel_root,),
            thresholds=DEFAULT_INFRA_THRESHOLDS,
            allowlist=allowlist,
        )
        warnings.extend(part_warnings)
        failures.extend(part_failures)
    return warnings, failures


def scan_repository_tests(
    repo_root: Path,
    *,
    allowlist: frozenset[str] = frozenset(),
) -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
    """Advisory scan of infra and public project test modules (warn-only by default)."""
    from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

    warnings: list[tuple[str, int]] = []
    infra_warnings, _ = scan_line_counts(
        repo_root,
        ("tests",),
        thresholds=DEFAULT_TEST_THRESHOLDS,
        allowlist=allowlist,
    )
    warnings.extend(infra_warnings)

    for name in PUBLIC_PROJECT_NAMES:
        tests_dir = repo_root / "projects" / name / "tests"
        if not tests_dir.is_dir():
            continue
        rel_root = tests_dir.relative_to(repo_root).as_posix()
        part_warnings, _ = scan_line_counts(
            repo_root,
            (rel_root,),
            thresholds=DEFAULT_TEST_THRESHOLDS,
            allowlist=allowlist,
        )
        warnings.extend(part_warnings)
    return warnings, []
