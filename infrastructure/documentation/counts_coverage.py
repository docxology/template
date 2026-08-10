"""Coverage snapshot measurement and source-tree provenance.

The factsheet renderer imports this module's stable public names so collection
documentation and coverage evidence can evolve independently. Coverage is
always measured in the exemplar's isolated environment; source hashes include
tracked and non-ignored working-tree files before a refresh is accepted.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.pytest_orchestration import (
    build_profile_marker_expression,
    resolve_test_profile,
)
from infrastructure.core.runtime.environment import get_subprocess_env
from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy

COVERAGE_PROVENANCE_RELATIVE_PATH = Path("docs/_generated/coverage_snapshot.json")
COVERAGE_PROVENANCE_SCHEMA_VERSION = 3
COVERAGE_SOURCE_INVENTORY_MODE = "tracked-and-nonignored-working-tree"
EXEMPLAR_SNAPSHOT_DATE = "2026-08-09"
COVERAGE_MEASUREMENT_TIMEOUT_SECONDS = 1800


def _coverage_process_policy(policy_id: str, timeout_seconds: float) -> SubprocessPolicy:
    """Return the shared bounded policy for one coverage subprocess."""
    return SubprocessPolicy(
        policy_id=policy_id,
        source_path="infrastructure/documentation/counts_coverage.py",
        timeout_seconds=timeout_seconds,
        capture_output=True,
        credential_free=True,
    )


_SOURCE_INVENTORY_EXCLUDED_PARTS = frozenset(
    {
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".coverage",
        ".tox",
        ".venv",
        "build",
        "dist",
    }
)


@dataclass(frozen=True)
class ExemplarSnapshot:
    """One measured coverage row; collection count is always derived live."""

    name: str
    coverage_pct: str


EXEMPLAR_SNAPSHOT: tuple[ExemplarSnapshot, ...] = (
    ExemplarSnapshot("template_active_inference", "92.85 %"),
    ExemplarSnapshot("template_advanced_literature_review", "94.65 %"),
    ExemplarSnapshot("template_autopoiesis", "97.60 %"),
    ExemplarSnapshot("template_autoresearch_project", "96.33 %"),
    ExemplarSnapshot("template_autoscientists", "97.56 %"),
    ExemplarSnapshot("template_code_project", "95.84 %"),
    ExemplarSnapshot("template_data_descriptor", "95.81 %"),
    ExemplarSnapshot("template_eda_notebook", "92.21 %"),
    ExemplarSnapshot("template_formal", "94.39 %"),
    ExemplarSnapshot("template_gold_refinement", "92.19 %"),
    ExemplarSnapshot("template_literature_meta_analysis", "93.97 %"),
    ExemplarSnapshot("template_madlib", "98.79 %"),
    ExemplarSnapshot("template_methods_paper", "99.00 %"),
    ExemplarSnapshot("template_newspaper", "99.24 %"),
    ExemplarSnapshot("template_pitch_deck", "97.19 %"),
    ExemplarSnapshot("template_pools_rules_tools", "93.67 %"),
    ExemplarSnapshot("template_prose_project", "92.85 %"),
    ExemplarSnapshot("template_redacted_report", "94.77 %"),
    ExemplarSnapshot("template_registered_report", "94.13 %"),
    ExemplarSnapshot("template_search_project", "96.71 %"),
    ExemplarSnapshot("template_sia", "96.39 %"),
    ExemplarSnapshot("template_storybook", "93.54 %"),
    ExemplarSnapshot("template_template", "97.66 %"),
    ExemplarSnapshot("template_textbook", "93.35 %"),
)


def _coverage_measurement_command(project_dir: Path) -> list[str]:
    """Build the bounded release-profile pytest command for one exemplar."""
    profile = resolve_test_profile("release")
    marker_expression = build_profile_marker_expression(profile)
    command = [
        "uv",
        "run",
        "--directory",
        str(project_dir),
        "pytest",
        "tests/",
        "--cov=src",
        "--cov-report=",
        "-q",
    ]
    if marker_expression:
        command.extend(["-m", marker_expression])
    return command


def _coverage_measurement_data_file(repo_root: Path, name: str) -> Path:
    """Return an absolute, project-local coverage data path."""
    project_dir = repo_root.resolve() / "projects" / "templates" / name
    return project_dir / f".coverage.measure_{name}"


def measure_exemplar_coverage(repo_root: Path, name: str) -> str:
    """Run one exemplar's release-profile coverage gate and return its total."""
    project_dir = repo_root.resolve() / "projects" / "templates" / name
    if not project_dir.is_dir():
        raise RuntimeError(f"exemplar not checked out: {name}")
    data_file = _coverage_measurement_data_file(repo_root, name)
    env = dict(get_subprocess_env())
    env["COVERAGE_FILE"] = str(data_file)
    profile = resolve_test_profile("release")
    command = _coverage_measurement_command(project_dir)
    try:
        run = run_with_policy(
            command,
            cwd=repo_root,
            env=env,
            policy=_coverage_process_policy("coverage-measurement", COVERAGE_MEASUREMENT_TIMEOUT_SECONDS),
        )
        if run.timed_out:
            raise RuntimeError(
                f"coverage run timed out for {name} after {COVERAGE_MEASUREMENT_TIMEOUT_SECONDS}s "
                f"using the {profile.name} profile"
            )
        if run.returncode != 0:
            tail = "\n".join((run.stdout + run.stderr).splitlines()[-8:])
            raise RuntimeError(f"coverage run failed for {name} (exit {run.returncode}):\n{tail}")
        report = run_with_policy(
            ["uv", "run", "--directory", str(project_dir), "coverage", "report", "--precision=2"],
            cwd=repo_root,
            env=env,
            policy=_coverage_process_policy("coverage-report", 300),
        )
        for line in report.stdout.splitlines():
            if line.startswith("TOTAL"):
                return f"{line.split()[-1].rstrip('%')} %"
        raise RuntimeError(f"no TOTAL row in coverage report for {name}")
    finally:
        data_file.unlink(missing_ok=True)


def verify_exemplar_coverage(repo_root: Path, *, rewrite: bool = False) -> tuple[bool, str]:
    """Re-measure every exemplar's coverage and compare with its snapshot."""
    measured: dict[str, str] = {}
    failures: list[str] = []
    for row in EXEMPLAR_SNAPSHOT:
        try:
            measured[row.name] = measure_exemplar_coverage(repo_root, row.name)
        except RuntimeError as exc:
            failures.append(f"{row.name}: {exc}")

    lines = [f"{'exemplar':44} {'recorded':>10} {'measured':>10}  status"]
    mismatched: list[tuple[str, str, str]] = []
    for row in EXEMPLAR_SNAPSHOT:
        actual = measured.get(row.name)
        if actual is None:
            lines.append(f"{row.name:44} {row.coverage_pct:>10} {'-':>10}  NOT MEASURED")
            continue
        ok = actual.replace(" ", "") == row.coverage_pct.replace(" ", "")
        if not ok:
            mismatched.append((row.name, row.coverage_pct, actual))
        lines.append(f"{row.name:44} {row.coverage_pct:>10} {actual:>10}  {'ok' if ok else 'DRIFTED'}")

    if rewrite and measured:
        _rewrite_exemplar_snapshot(measured)
        lines.append(f"\nrewrote EXEMPLAR_SNAPSHOT with {len(measured)} measured values")
    for failure in failures:
        lines.append(f"MEASUREMENT FAILED — {failure}")
    lines.append(f"\n{len(mismatched)} drifted, {len(failures)} failed, {len(measured)} measured")
    return (not mismatched and not failures), "\n".join(lines)


def _rewrite_exemplar_snapshot(measured: dict[str, str], source_path: Path | None = None) -> None:
    """Rewrite an ``EXEMPLAR_SNAPSHOT`` tuple with measured percentages."""
    source_path = source_path or Path(__file__)
    text = source_path.read_text(encoding="utf-8")

    def _replace(match: re.Match[str]) -> str:
        name = match.group("name")
        actual = measured.get(name)
        return match.group(0) if actual is None else f'ExemplarSnapshot("{name}", "{actual}")'

    updated = re.sub(
        r'ExemplarSnapshot\(\s*"(?P<name>[^"]+)"\s*,\s*"[^"]*"\s*\)',
        _replace,
        text,
    )
    if updated != text:
        source_path.write_text(updated, encoding="utf-8")


def exemplar_source_hash(repo_root: Path, name: str) -> str:
    """Hash tracked and non-ignored source/test files that determine coverage."""
    project_root = repo_root / "projects" / "templates" / name
    digest = hashlib.sha256()
    for logical_path, physical_path in _exemplar_source_files(repo_root, project_root):
        if physical_path.is_symlink() and physical_path.is_dir():
            for child_logical, child_physical in _tracked_symlink_children(repo_root, logical_path, physical_path):
                digest.update(child_logical.relative_to(project_root).as_posix().encode("utf-8"))
                digest.update(b"\0")
                digest.update(child_physical.read_bytes())
                digest.update(b"\0")
            continue
        if not physical_path.is_file():
            continue
        digest.update(logical_path.relative_to(project_root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(physical_path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _exemplar_source_files(repo_root: Path, project_root: Path) -> list[tuple[Path, Path]]:
    """Return logical/physical source files for a coverage inventory."""
    relative_roots = [(project_root / root_name).relative_to(repo_root).as_posix() for root_name in ("src", "tests")]
    tracked = run_with_policy(
        ["git", "ls-files", "--", *relative_roots],
        cwd=repo_root,
        env=None,
        policy=_coverage_process_policy("coverage-source-inventory", 30),
    )
    untracked = run_with_policy(
        ["git", "ls-files", "--others", "--exclude-standard", "--", *relative_roots],
        cwd=repo_root,
        env=None,
        policy=_coverage_process_policy("coverage-source-inventory", 30),
    )
    if tracked.returncode == 0 and untracked.returncode == 0:
        relative_paths = sorted({*tracked.stdout.splitlines(), *untracked.stdout.splitlines()})
        candidates = [(repo_root / relative, repo_root / relative) for relative in relative_paths]
    else:
        candidates = sorted(
            (path, path) for root_name in ("src", "tests") for path in (project_root / root_name).rglob("*")
        )
    return [
        (logical, physical)
        for logical, physical in candidates
        if _is_source_inventory_path(logical, project_root)
        and (physical.is_file() or (physical.is_symlink() and physical.is_dir()))
    ]


def _is_source_inventory_path(path: Path, project_root: Path) -> bool:
    """Return whether *path* belongs to the meaningful source/test surface."""
    try:
        relative = path.relative_to(project_root)
    except ValueError:
        return False
    if not relative.parts or relative.parts[0] not in {"src", "tests"}:
        return False
    if any(part in _SOURCE_INVENTORY_EXCLUDED_PARTS for part in relative.parts):
        return False
    return not any(part.endswith(".egg-info") for part in relative.parts)


def _tracked_symlink_children(repo_root: Path, logical_path: Path, symlink_path: Path) -> list[tuple[Path, Path]]:
    """Return inventoried regular files reached through an in-repository symlink."""
    repo_root = repo_root.resolve()
    target_root = symlink_path.resolve()
    try:
        target_rel = target_root.relative_to(repo_root).as_posix()
    except ValueError:
        return []
    tracked = run_with_policy(
        ["git", "ls-files", "--", target_rel],
        cwd=repo_root,
        env=None,
        policy=_coverage_process_policy("coverage-source-inventory", 30),
    )
    untracked = run_with_policy(
        ["git", "ls-files", "--others", "--exclude-standard", "--", target_rel],
        cwd=repo_root,
        env=None,
        policy=_coverage_process_policy("coverage-source-inventory", 30),
    )
    if tracked.returncode == 0 and untracked.returncode == 0:
        relatives = sorted({*tracked.stdout.splitlines(), *untracked.stdout.splitlines()})
        physical_files = sorted((repo_root / relative).resolve() for relative in relatives)
    else:
        physical_files = sorted(
            path
            for path in target_root.rglob("*")
            if path.is_file() and not any(part in _SOURCE_INVENTORY_EXCLUDED_PARTS for part in path.parts)
        )
    return [
        (logical_path / physical.relative_to(target_root), physical)
        for physical in physical_files
        if physical.is_file()
    ]


def build_coverage_provenance(repo_root: Path) -> dict[str, object]:
    """Build provenance for the checked-in coverage percentages."""
    source_commit = run_with_policy(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        env=None,
        policy=_coverage_process_policy("coverage-source-inventory", 30),
    )
    if source_commit.returncode != 0:
        raise RuntimeError(f"could not resolve source commit: {source_commit.stderr.strip()}")
    source_revision = source_commit.stdout.strip()
    if not source_revision:
        raise RuntimeError("could not resolve source commit: empty revision")
    source_hashes = {row.name: exemplar_source_hash(repo_root, row.name) for row in EXEMPLAR_SNAPSHOT}
    return {
        "schema_version": COVERAGE_PROVENANCE_SCHEMA_VERSION,
        "source_inventory_mode": COVERAGE_SOURCE_INVENTORY_MODE,
        "source_tree_identity": {
            "algorithm": "sha256",
            "inventory_mode": COVERAGE_SOURCE_INVENTORY_MODE,
            "projects": source_hashes,
        },
        "measured_at": EXEMPLAR_SNAPSHOT_DATE,
        "source_commit": source_revision,
        "projects": {
            row.name: {"coverage_pct": row.coverage_pct, "source_hash": source_hashes[row.name]}
            for row in EXEMPLAR_SNAPSHOT
        },
    }


def write_coverage_provenance(repo_root: Path) -> Path:
    """Write coverage source provenance after coverage gates have run."""
    target = repo_root / COVERAGE_PROVENANCE_RELATIVE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(build_coverage_provenance(repo_root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


def validate_coverage_provenance(repo_root: Path) -> None:
    """Fail closed when a coverage percentage is stale for its source tree."""
    path = repo_root / COVERAGE_PROVENANCE_RELATIVE_PATH
    if not path.is_file():
        raise RuntimeError(f"missing coverage provenance: {COVERAGE_PROVENANCE_RELATIVE_PATH}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("coverage provenance root must be a mapping")
    if payload.get("schema_version") != COVERAGE_PROVENANCE_SCHEMA_VERSION:
        raise RuntimeError(f"coverage provenance schema mismatch: expected {COVERAGE_PROVENANCE_SCHEMA_VERSION}")
    if payload.get("source_inventory_mode") != COVERAGE_SOURCE_INVENTORY_MODE:
        raise RuntimeError("coverage provenance source inventory mode is missing or unsupported")
    source_tree_identity = payload.get("source_tree_identity")
    if not isinstance(source_tree_identity, dict):
        raise RuntimeError("coverage provenance source-tree identity is missing")
    if source_tree_identity.get("algorithm") != "sha256":
        raise RuntimeError("coverage provenance source-tree identity algorithm is unsupported")
    if source_tree_identity.get("inventory_mode") != COVERAGE_SOURCE_INVENTORY_MODE:
        raise RuntimeError("coverage provenance source-tree identity inventory mode is unsupported")
    source_hashes = source_tree_identity.get("projects")
    if not isinstance(source_hashes, dict):
        raise RuntimeError("coverage provenance source-tree identity has no project mapping")
    projects = payload.get("projects")
    if not isinstance(projects, dict):
        raise RuntimeError("coverage provenance has no projects mapping")
    expected_names = {row.name for row in EXEMPLAR_SNAPSHOT}
    if set(projects) != expected_names:
        raise RuntimeError("coverage provenance project roster does not match the public snapshot")
    for row in EXEMPLAR_SNAPSHOT:
        record = projects.get(row.name)
        if not isinstance(record, dict) or record.get("coverage_pct") != row.coverage_pct:
            raise RuntimeError(f"coverage provenance percentage mismatch: {row.name}")
        if record.get("source_hash") != source_hashes.get(row.name):
            raise RuntimeError(f"coverage provenance source-tree identity disagrees with project row: {row.name}")
        if record.get("source_hash") != exemplar_source_hash(repo_root, row.name):
            raise RuntimeError(
                f"stale coverage snapshot for {row.name}: source hash changed; "
                "rerun its coverage gate, then refresh coverage provenance"
            )


__all__ = [
    "COVERAGE_MEASUREMENT_TIMEOUT_SECONDS",
    "COVERAGE_PROVENANCE_RELATIVE_PATH",
    "COVERAGE_PROVENANCE_SCHEMA_VERSION",
    "COVERAGE_SOURCE_INVENTORY_MODE",
    "EXEMPLAR_SNAPSHOT",
    "EXEMPLAR_SNAPSHOT_DATE",
    "ExemplarSnapshot",
    "_coverage_measurement_command",
    "_coverage_measurement_data_file",
    "_rewrite_exemplar_snapshot",
    "build_coverage_provenance",
    "exemplar_source_hash",
    "measure_exemplar_coverage",
    "validate_coverage_provenance",
    "verify_exemplar_coverage",
    "write_coverage_provenance",
]
