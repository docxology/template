"""Composable evaluation of the two independent promotion contracts."""

from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path

from infrastructure.project.promotion.attestation import load_promotion_attestation
from infrastructure.project.promotion.models import PromotionCompositeReport
from infrastructure.project.promotion.security_gate import check_private_project_promotion


def evaluate_promotion_candidate(
    project_root: Path,
    *,
    project_name: str,
    orchestration_attestation: Path,
    security_attestation: Path | None = None,
    as_of: date | None = None,
) -> PromotionCompositeReport:
    """Evaluate orchestration evidence and candidate security in one report."""
    root = project_root.resolve()
    qualified_project = project_name.strip()
    project_parts = Path(qualified_project).parts
    if (
        not qualified_project
        or Path(qualified_project).is_absolute()
        or ".." in project_parts
        or len(project_parts) < 2
    ):
        raise ValueError("promotion project name must be qualified and non-absolute")
    if not project_parts or project_parts[-1] != root.name:
        raise ValueError("promotion project name must identify the candidate directory")
    attestation = load_promotion_attestation(orchestration_attestation, as_of=as_of)
    if attestation.project != qualified_project:
        raise ValueError(
            f"promotion attestation project does not match candidate: {attestation.project} != {qualified_project}"
        )
    security_evidence = security_attestation or root / "promotion-security.yaml"
    candidate_commit = _candidate_commit(
        root,
        allowed_dirty_paths=(orchestration_attestation, security_evidence),
    )
    if attestation.source_commit.lower() != candidate_commit.lower():
        raise ValueError(
            "promotion attestation source_commit does not match candidate HEAD: "
            f"{attestation.source_commit} != {candidate_commit}"
        )
    security = check_private_project_promotion(
        root,
        attestation_path=security_evidence,
        as_of=as_of,
    )
    return PromotionCompositeReport(attestation=attestation, security=security)


def _candidate_commit(project_root: Path, *, allowed_dirty_paths: tuple[Path | None, ...]) -> str:
    """Return candidate HEAD after rejecting unbound working-tree changes."""

    head = _git(project_root, "rev-parse", "--verify", "HEAD")
    git_root = Path(_git(project_root, "rev-parse", "--show-toplevel")).resolve()
    allowed: set[str] = set()
    for path in allowed_dirty_paths:
        if path is None:
            continue
        try:
            allowed.add(path.resolve().relative_to(git_root).as_posix())
        except ValueError:
            continue
    try:
        candidate_scope = project_root.relative_to(git_root).as_posix()
    except ValueError as exc:  # pragma: no cover - git itself should make this impossible.
        raise ValueError("promotion candidate is outside its Git checkout") from exc
    status = _git(
        git_root,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--",
        candidate_scope,
        strip=False,
    )
    changed = _porcelain_changed_paths(status) - allowed
    if changed:
        raise ValueError(
            "promotion candidate has uncommitted changes outside attestation files: " + ", ".join(sorted(changed))
        )
    return head


def _porcelain_changed_paths(status: str) -> set[str]:
    """Return every path encoded by ``git status --porcelain=v1 -z``.

    Rename and copy records contain a second NUL-delimited path without the
    leading ``XY `` status prefix.  Both paths are security-relevant: allowing
    only the destination attestation must not hide a renamed source file.
    """

    records = status.split("\0")
    changed: set[str] = set()
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        if len(record) < 4 or record[2] != " ":
            raise ValueError("promotion candidate returned malformed Git status data")
        code = record[:2]
        changed.add(record[3:])
        if "R" in code or "C" in code:
            if index >= len(records) or not records[index]:
                raise ValueError("promotion candidate returned an incomplete Git rename record")
            changed.add(records[index])
            index += 1
    return changed


def _git(project_root: Path, *args: str, strip: bool = True) -> str:
    process = subprocess.run(  # noqa: S603 - fixed git executable and argv.
        ["git", *args],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if process.returncode != 0:
        detail = (process.stderr or process.stdout).strip()
        raise ValueError(f"promotion candidate is not a readable Git checkout: {detail}")
    return process.stdout.strip() if strip else process.stdout


__all__ = ["evaluate_promotion_candidate"]
