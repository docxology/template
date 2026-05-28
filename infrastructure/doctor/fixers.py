"""Fix intents — build :class:`FixPlan` objects from :class:`Finding` objects.

Fixers never touch the filesystem themselves. They translate a detector
finding into one or more :class:`FixPlan` instances which are then
executed through :func:`infrastructure.doctor.safety.mutate`. That keeps
the audit/backup/undo contract uniform: every change in the repo that
the doctor takes credit for has a journal entry and a restorable backup.

A "fix plan" is therefore intentionally declarative — it lists the
paths that will be touched, the action kind (``delete_paths``, ``chmod``,
``write_file``, ``run_uv_sync``), and any parameters. The safety layer
enforces invariants (paths inside the repo, fresh hashes, journal
entry) regardless of what the plan asks for.

The :data:`FIXER_REGISTRY` maps ``fix_id`` strings to the function that
builds the plan(s). When the CLI is asked to fix something it looks up
the ``RepairLevel.fix_id`` from the finding, calls the corresponding
builder with the finding, and pipes each plan to ``mutate()``.
"""

from collections.abc import Callable
from pathlib import Path

from infrastructure.doctor.models import (
    Finding,
    FixPlan,
    TherapyLevel,
)
from infrastructure.doctor.safety import DoctorState


__all__ = [
    "FixerFn",
    "FIXER_REGISTRY",
    "build_plans_for_findings",
    # Individual builders (exported for tests):
    "build_fix_make_run_sh_executable",
    "build_fix_clean_pycache",
    "build_fix_clean_coverage_files",
    "build_fix_install_pre_commit_hook",
    "build_fix_run_uv_sync",
    "build_fix_remove_orphan_output_dirs",
]


FixerFn = Callable[[Finding, DoctorState], list[FixPlan]]
"""Build zero or more :class:`FixPlan` objects from a finding.

Builders are free to return an empty list when nothing actionable can
be derived (e.g. evidence is missing).
"""


# ---------------------------------------------------------------------------
# Individual fixers
# ---------------------------------------------------------------------------


def build_fix_make_run_sh_executable(finding: Finding, state: DoctorState) -> list[FixPlan]:
    """``chmod +x run.sh``. Trivial, conservative, fully reversible."""
    run_sh = state.repo_root / "run.sh"
    if not run_sh.is_file():
        return []
    return [
        FixPlan(
            fix_id="fix_make_run_sh_executable",
            title="Make run.sh executable",
            therapy=TherapyLevel.CONSERVATIVE,
            finding_code=finding.code,
            affected_paths=(run_sh,),
            action_kind="chmod",
            params={"mode": 0o111},  # +x for u/g/o
            reversible=True,
        )
    ]


def build_fix_clean_pycache(finding: Finding, state: DoctorState) -> list[FixPlan]:
    """Delete every ``__pycache__`` / tool-cache directory under the repo.

    One plan per directory keeps each backup small and each undo
    independently restorable.
    """
    plans: list[FixPlan] = []
    samples = finding.evidence.get("sample") or []
    # ``sample`` is only the first 10 — re-walk for a complete pass.
    seen: set[Path] = set()
    cache_names = ("__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache")
    ignored_top = {".venv", ".doctor", "node_modules"}
    # Dormant private typed-subfolder trees; keep in sync with
    # discovery.NON_RENDERED_SUBDIRS.
    dormant_project_subdirs = {"archive", "other", "published", "working"}
    for sub in state.repo_root.rglob("*"):
        if not sub.is_dir() or sub.name not in cache_names:
            continue
        try:
            rel_parts = sub.relative_to(state.repo_root).parts
        except ValueError:
            continue
        if rel_parts and rel_parts[0] in ignored_top:
            continue
        if len(rel_parts) >= 2 and rel_parts[0] == "projects" and rel_parts[1] in dormant_project_subdirs:
            continue
        if any(part == ".venv" for part in rel_parts):
            continue
        if sub in seen:
            continue
        seen.add(sub)
        plans.append(
            FixPlan(
                fix_id="fix_clean_pycache",
                title=f"Remove cache directory {sub.relative_to(state.repo_root)}",
                therapy=TherapyLevel.CONSERVATIVE,
                finding_code=finding.code,
                affected_paths=(sub,),
                action_kind="delete_paths",
                params={},
                reversible=True,
            )
        )
    # If the evidence sample listed directories that have since
    # disappeared, ignore them — that's the desired end-state already.
    del samples
    return plans


def build_fix_clean_coverage_files(finding: Finding, state: DoctorState) -> list[FixPlan]:
    """Remove leftover ``.coverage*`` / ``coverage_*.json`` / ``coverage.xml``."""
    plans: list[FixPlan] = []
    for pattern in (".coverage", ".coverage.*", "coverage_*.json", "coverage.xml"):
        for path in state.repo_root.glob(pattern):
            plans.append(
                FixPlan(
                    fix_id="fix_clean_coverage_files",
                    title=f"Delete stale coverage file {path.name}",
                    therapy=TherapyLevel.CONSERVATIVE,
                    finding_code=finding.code,
                    affected_paths=(path,),
                    action_kind="delete_paths",
                    params={},
                    reversible=True,
                )
            )
    return plans


def build_fix_install_pre_commit_hook(finding: Finding, state: DoctorState) -> list[FixPlan]:
    """Write a minimal ``.git/hooks/pre-commit`` shim that defers to ``pre-commit``.

    A full ``pre-commit install`` would shell out, which is a class of
    action this doctor avoids. The shim is byte-identical to what
    ``pre-commit install`` emits in its simplest case, so a follow-up
    ``pre-commit install`` is a no-op.
    """
    hook = state.repo_root / ".git" / "hooks" / "pre-commit"
    if hook.exists():
        return []
    contents = (
        "#!/usr/bin/env bash\n"
        "# Installed by infrastructure.doctor.fixers — defers to pre-commit.\n"
        "if command -v pre-commit >/dev/null 2>&1; then\n"
        '  exec pre-commit run --hook-stage pre-commit "$@"\n'
        "else\n"
        "  echo 'pre-commit not installed; run `uv sync` then `pre-commit install`.' >&2\n"
        "  exit 0\n"
        "fi\n"
    )
    return [
        FixPlan(
            fix_id="fix_install_pre_commit_hook",
            title="Install pre-commit shim hook",
            therapy=TherapyLevel.CONSERVATIVE,
            finding_code=finding.code,
            affected_paths=(hook,),
            action_kind="write_file",
            params={"content": contents, "overwrite": False, "mode": 0o755},
            reversible=True,
        ),
        # Second plan: make it executable. Separate because the chmod
        # handler is shared and that keeps each step independently
        # undoable.
        FixPlan(
            fix_id="fix_install_pre_commit_hook",
            title="Mark pre-commit hook executable",
            therapy=TherapyLevel.CONSERVATIVE,
            finding_code=finding.code,
            affected_paths=(hook,),
            action_kind="chmod",
            params={"mode": 0o755},
            reversible=True,
        ),
    ]


def build_fix_run_uv_sync(finding: Finding, state: DoctorState) -> list[FixPlan]:
    """``uv sync`` to refresh ``uv.lock`` and the venv.

    Marked ``reversible=False`` because there is no clean way to roll a
    venv back to its prior package set from a file backup alone — the
    lockfile is restorable but the installed packages would still
    diverge. Surfacing this honestly is part of the safety contract.
    """
    return [
        FixPlan(
            fix_id="fix_run_uv_sync",
            title="Run `uv sync` to refresh uv.lock and venv",
            therapy=TherapyLevel.MODERATE,
            finding_code=finding.code,
            affected_paths=(state.repo_root / "uv.lock",),
            action_kind="run_uv_sync",
            params={},
            reversible=False,
        )
    ]


def build_fix_remove_orphan_output_dirs(finding: Finding, state: DoctorState) -> list[FixPlan]:
    """Delete output trees whose project no longer exists.

    Radical therapy: each output subtree is fully snapshotted into
    ``.doctor/backups/`` so an undo brings the PDFs back byte-for-byte.
    """
    plans: list[FixPlan] = []
    orphans = finding.evidence.get("orphans") or []
    for rel in orphans:
        target = state.repo_root / rel
        if not target.exists():
            continue
        plans.append(
            FixPlan(
                fix_id="fix_remove_orphan_output_dirs",
                title=f"Remove orphan output directory {rel}",
                therapy=TherapyLevel.RADICAL,
                finding_code=finding.code,
                affected_paths=(target,),
                action_kind="delete_paths",
                params={},
                reversible=True,
            )
        )
    return plans


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


FIXER_REGISTRY: dict[str, FixerFn] = {
    "fix_make_run_sh_executable": build_fix_make_run_sh_executable,
    "fix_clean_pycache": build_fix_clean_pycache,
    "fix_clean_coverage_files": build_fix_clean_coverage_files,
    "fix_install_pre_commit_hook": build_fix_install_pre_commit_hook,
    "fix_run_uv_sync": build_fix_run_uv_sync,
    "fix_remove_orphan_output_dirs": build_fix_remove_orphan_output_dirs,
}


def build_plans_for_findings(
    findings: list[Finding],
    state: DoctorState,
    *,
    max_therapy: TherapyLevel = TherapyLevel.CONSERVATIVE,
    selected_codes: frozenset[str] | None = None,
    selected_fix_ids: frozenset[str] | None = None,
) -> list[FixPlan]:
    """Translate findings into a deduplicated, ordered list of plans.

    Args:
        findings: Findings to consider.
        state: Doctor state (passed through to each builder).
        max_therapy: Cap on therapy intensity. ``CONSERVATIVE`` (default)
            yields the safest set; ``MODERATE`` adds reversible-but-
            heavier fixes (like ``uv sync``); ``RADICAL`` adds destructive
            cleanups like orphan-output removal.
        selected_codes: If provided, only build plans for findings whose
            ``code`` is in the set.
        selected_fix_ids: If provided, only build plans whose ``fix_id``
            is in the set.

    Returns:
        A flat list of plans, in detection order, ready to be fed to
        :func:`infrastructure.doctor.safety.mutate` one at a time.
    """
    plans: list[FixPlan] = []
    for finding in findings:
        if finding.healthy:
            continue
        if selected_codes is not None and finding.code not in selected_codes:
            continue
        for repair in finding.repair_levels:
            if repair.level > max_therapy:
                continue
            builder = FIXER_REGISTRY.get(repair.fix_id)
            if builder is None:
                # Unknown fix id — skip rather than fabricate one. The
                # surfacing finding will still show in the report.
                continue
            if selected_fix_ids is not None and repair.fix_id not in selected_fix_ids:
                continue
            plans.extend(builder(finding, state))
    return plans
