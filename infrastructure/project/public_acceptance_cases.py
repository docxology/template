"""Source-owned pytest invocation and consumed-source contracts for runtime cells."""

from __future__ import annotations

from pathlib import Path
import re
from typing import TYPE_CHECKING

from infrastructure.project.public_acceptance_evidence import bootstrap_command
from infrastructure.project.public_acceptance_scope import RuntimeScope

if TYPE_CHECKING:
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

PYTEST_SPEC_SCHEMA = "template-public-pytest-spec-v1"


def project_python_hashes(root: Path, scope: str, reader: SnapshotReader | None = None) -> dict[str, str]:
    """Snapshot all owned Python in the consumed implementation and test lanes."""
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

    reader = reader or SnapshotReader(root)
    resolved = RuntimeScope(root, scope)
    roots = resolved.python_roots()
    paths = sorted(
        [path.relative_to(root).as_posix() for lane in roots[:3] for path in lane.rglob("*.py")]
        + [path.relative_to(root).as_posix() for path in roots[3:]]
    )
    if not paths or len(set(paths)) != len(paths):
        raise ValueError("runtime execution requires a nonempty unique owned Python source inventory")
    result = {path: reader.read(path).sha256 for path in paths}
    if not reader.unchanged():
        raise ValueError("owned Python changed while admitted for pytest execution")
    return result


def pytest_command(
    interpreter: Path,
    root: Path,
    directory: Path,
    run_id: str,
    scope: str,
    receipt: Path,
    spec: Path,
    selectors: list[str],
    *,
    spec_sha256: str,
    collect: bool,
    test_timeout: int,
    audit_roots: tuple[Path, ...] = (),
) -> tuple[str, ...]:
    """Build the exact current pytest launch without executing a project planner."""
    if re.fullmatch(r"[0-9a-f]{64}", spec_sha256) is None:
        raise ValueError("pytest execution requires the original specification SHA-256")
    resolved = RuntimeScope(root, scope)
    project = resolved.base
    base = [
        "-c",
        str(project / "pyproject.toml"),
        "--rootdir",
        str(project),
        "--confcutdir",
        str(project),
        "-o",
        "addopts=",
        "-o",
        "python_files=test_*.py *_test.py",
        "-q",
        "--tb=short",
        "--assert=plain",
        "--benchmark-storage=" + str(directory / "benchmarks"),
        *selectors,
    ]
    if collect:
        base.extend(["--collect-only", "--no-cov"])
    else:
        stem = receipt.stem
        index = stem.removeprefix("chunk-")
        base.extend(
            [
                "--cov=" + resolved.coverage_source,
                "--cov-branch",
                "--cov-append",
                "--cov-report=",
                "--cov-fail-under=0",
                "--cov-config=" + str(project / "pyproject.toml"),
                f"--timeout={test_timeout}",
                "--junitxml=" + str(directory / (stem + ".xml")),
                "--basetemp=" + str(directory / ("tmp-" + index)),
            ]
        )
    return bootstrap_command(
        interpreter,
        root,
        "infrastructure.project.public_acceptance_pytest",
        "--root",
        str(root),
        "--project-root",
        str(project),
        "--receipt",
        str(receipt),
        "--run-id",
        run_id,
        "--dependency-spec",
        str(directory / "dependency-spec.json"),
        "--execution-spec",
        str(spec),
        "--execution-spec-sha256",
        spec_sha256,
        "--",
        *base,
        audit_roots=audit_roots,
    )
