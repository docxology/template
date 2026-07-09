"""Live-sourced facts about ``infrastructure/`` itself, for the deck's own
"what's actually inside infrastructure/" content.

Reuses `infrastructure.documentation.counts_doc`'s existing introspection
functions (`infrastructure_packages`, `tracked_infra_python_count`) rather
than re-deriving the same filesystem/git facts a second way — those are the
same functions `docs/_generated/COUNTS.md` itself is built from, so this
deck's `INFRA_*` tokens and that generated factsheet can never silently
disagree.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from infrastructure.documentation.counts_doc import infrastructure_packages, tracked_infra_python_count


class InfraIntrospectionError(RuntimeError):
    """Raised when live introspection of ``infrastructure/`` fails.

    Wraps the underlying ``git`` subprocess failure (e.g. ``repo_root`` isn't
    a git repository) in a domain-specific exception, matching this project's
    other user-facing failures (`DeckAuditFailure`, `DiligenceAuditFailure`)
    instead of surfacing a raw `subprocess.CalledProcessError` (red-team
    finding, 2026-07-09).
    """


def infra_subpackage_python_counts(repo_root: Path) -> list[tuple[str, int]]:
    """Return ``(subpackage_name, tracked_python_file_count)`` for every
    importable ``infrastructure/`` subpackage, sorted by count descending.

    Uses ``git ls-files`` scoped to each subpackage directory — the same
    tracked-file source `tracked_infra_python_count` uses for the repo-wide
    total, just partitioned per subpackage instead of summed.
    """
    packages = infrastructure_packages(repo_root)
    rows: list[tuple[str, int]] = []
    for package in packages:
        try:
            tracked = subprocess.run(  # noqa: S603 - fixed argv, repo-local git
                ["git", "ls-files", f"infrastructure/{package}"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.splitlines()
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            raise InfraIntrospectionError(
                f"Could not list tracked files under infrastructure/{package} "
                f"(is {repo_root} a git repository with git on PATH?)"
            ) from exc
        count = sum(1 for path in tracked if path.endswith(".py"))
        if count > 0:
            rows.append((package, count))
    return sorted(rows, key=lambda row: row[1], reverse=True)


def build_infra_tokens(repo_root: Path) -> dict[str, str]:
    """Return `{{INFRA_*}}` token values, every one read live from the repo."""
    packages = infrastructure_packages(repo_root)
    total_py = tracked_infra_python_count(repo_root)
    subpackage_rows = infra_subpackage_python_counts(repo_root)
    top_three = sorted(subpackage_rows, key=lambda row: row[1], reverse=True)[:3]
    # The per-subpackage donut chart's total is the sum of only the rows
    # above — narrower than the repo-wide `total_py` by however many tracked
    # .py files sit directly under infrastructure/ without belonging to any
    # importable subpackage (e.g. infrastructure/__init__.py). Computing this
    # live (rather than hand-typing "2" in deck prose, which the fabrication
    # audit would rightly flag) keeps the deck's own explanation of the two
    # numbers' relationship honest if that count ever changes.
    unattributed_count = total_py - sum(count for _, count in subpackage_rows)
    return {
        "INFRA_SUBPACKAGE_COUNT": str(len(packages)),
        "INFRA_PYTHON_FILE_COUNT": str(total_py),
        "INFRA_LARGEST_SUBPACKAGE": top_three[0][0] if top_three else "",
        "INFRA_LARGEST_SUBPACKAGE_COUNT": str(top_three[0][1]) if top_three else "0",
        "INFRA_UNATTRIBUTED_FILE_COUNT": str(unattributed_count),
    }


__all__ = ["InfraIntrospectionError", "infra_subpackage_python_counts", "build_infra_tokens"]
