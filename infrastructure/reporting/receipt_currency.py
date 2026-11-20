"""Receipt currency across mainline history.

Why this exists
---------------
Every gate in this repository inspects *the current checkout*. None inspects
*the history*, so a commit that claimed verified receipts and was not could be
pushed, merged, and tagged without any check ever looking at it.

It has happened: nineteen of twenty-one first-parent commits since ``v5.0.0``
carried a ``config`` fingerprint from a tree that no longer existed, over a
window of roughly seventeen hours, including a published tag.

The check
---------
For each sampled commit, materialize that commit's blobs into a scratch
directory (no submodule, no dirty state, no dependence on the caller's working
copy), run the repository's own ``_project_records``/``_fingerprint`` on it, and
compare against the receipt committed at that same revision.

A commit is ``STALE`` when the stored digest differs from the digest its own
tree produces. That is the whole definition; there is no expected-value table to
keep current, because the expected value is computed from the artifact.

Boundaries
----------
This module owns the sampling, materialization and comparison. The CLI stays in
``scripts/audit/receipt_currency.py``, which parses arguments and prints. Exit
codes are the caller's decision: 0 clean (or report-only), 1 stale under
``--require-current``, 2 the environment could not answer. A ``SKIP`` or
``UNAVAILABLE`` verdict never reads as clean.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_PROJECT = "templates/template_code_project"


class CommitRangeError(ValueError):
    """The requested revision range could not be resolved."""


def receipt_path(project: str = DEFAULT_PROJECT) -> str:
    """Return the repository-relative receipt path for *project*."""
    return f"projects/{project}/output/reports/rendered_provenance.json"


@dataclass(frozen=True)
class Row:
    """One sampled commit, with its stored and self-computed config digest."""

    commit: str
    stored: str | None
    computed: str | None
    verdict: str
    detail: str = ""


@dataclass(frozen=True)
class CurrencyReport:
    """The sampled rows plus the selection they came from."""

    ref: str
    since: str | None
    rows: tuple[Row, ...]

    @property
    def stale(self) -> tuple[Row, ...]:
        """Rows whose stored digest does not describe their own tree."""
        return tuple(row for row in self.rows if row.verdict == "STALE")

    @property
    def unavailable(self) -> tuple[Row, ...]:
        """Rows the environment could not measure; never evidence of clean."""
        return tuple(row for row in self.rows if row.verdict == "UNAVAILABLE")

    def to_dict(self) -> dict[str, object]:
        """Return the historical JSON shape: ``since`` plus the row list."""
        return {"since": self.since, "rows": [asdict(row) for row in self.rows]}

    def to_json(self) -> str:
        """Render the JSON form quoted as evidence."""
        return json.dumps(self.to_dict(), indent=2)

    def format_table(self) -> str:
        """Render the commit table and ``RESULT:`` line, unchanged."""
        current = sum(1 for row in self.rows if row.verdict == "CURRENT")
        lines = [
            f"receipt currency on {self.ref} since {self.since or '(beginning)'} — {len(self.rows)} commit(s)\n",
            f"{'commit':13s} {'stored':18s} {'computed':18s} verdict",
            "-" * 66,
        ]
        lines.extend(
            f"{row.commit[:12]:13s} {str(row.stored)[:16]:18s} {str(row.computed)[:16]:18s} {row.verdict}"
            for row in self.rows
        )
        lines.append(f"\nRESULT: {current} current, {len(self.stale)} STALE, {len(self.unavailable)} unavailable")
        return "\n".join(lines)

    def unavailable_warning(self) -> str | None:
        """Return the stderr line for unmeasurable rows, or None when there are none."""
        if not self.unavailable:
            return None
        return f"\n{len(self.unavailable)} commit(s) could not be measured; this is not a clean result."

    def exit_code(self, *, require_current: bool) -> int:
        """Return 2 when unmeasurable, 1 for stale/skipped under ``require_current``, else 0."""
        if self.unavailable:
            return 2
        if require_current and any(row.verdict in ("STALE", "SKIP") for row in self.rows):
            return 1
        return 0


def git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run one read-only Git query against *repo_root*."""
    return subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=True, check=False)


def last_tag(repo_root: Path) -> str | None:
    """Return the newest reachable ``v*`` tag, or None when there is none."""
    result = git(repo_root, "describe", "--tags", "--abbrev=0", "--match", "v*")
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def sample_commits(repo_root: Path, *, since: str | None, limit: int, ref: str) -> list[str]:
    """Return up to *limit* first-parent commits from *since* to *ref*."""
    revision_range = f"{since}^..{ref}" if since else ref
    result = git(repo_root, "rev-list", "--first-parent", f"--max-count={limit}", revision_range)
    if result.returncode != 0:
        raise CommitRangeError(f"cannot resolve commits for {revision_range!r}: {result.stderr.strip()}")
    return result.stdout.split()


def stored_config(repo_root: Path, commit: str, *, receipt: str) -> str | None:
    """Return the config digest committed at *commit*, or None when unreadable."""
    result = git(repo_root, "show", f"{commit}:{receipt}")
    if result.returncode != 0:
        return None
    try:
        payload = json.loads(result.stdout)
        digest = payload["fingerprints"]["config"]["sha256"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return None
    return digest if isinstance(digest, str) else None


def computed_config(repo_root: Path, commit: str, *, project: str = DEFAULT_PROJECT) -> str | None:
    """Fingerprint the commit's own tree, using the repository's real implementation."""
    # Resolved, not a literal "/tmp": on macOS the temporary root is a symlink,
    # and the fingerprint walk compares resolved paths against the tree root.
    # Letting `mkdtemp` choose the directory also keeps the location under the
    # platform's own policy rather than a hardcoded one.
    scratch = Path(tempfile.mkdtemp()).resolve()
    # An alternate work-tree alone still writes the checkout into the caller's
    # real index: `git --work-tree X checkout <commit> -- .` stages every entry
    # into `.git/index`, so measuring 40 commits leaves the repository with
    # hundreds of `MM` paths that nobody authored. Point the index inside the
    # scratch directory so measurement cannot mutate the caller's repository.
    env = {**os.environ, "GIT_INDEX_FILE": str(scratch / ".git-index")}
    try:
        checkout = subprocess.run(
            ["git", "--work-tree", str(scratch), "checkout", commit, "--", "."],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        if checkout.returncode != 0:
            return None
        from infrastructure.validation.rendered_snapshot._records import _fingerprint, _project_records

        project_root = (scratch / "projects" / project).resolve()
        if not project_root.is_dir():
            return None
        _source, config = _project_records(scratch, project_root, lexical_project_root=project_root)
        return _fingerprint(config).sha256
    except Exception:  # noqa: BLE001 - a failed measurement must not read as clean
        return None
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def collect(
    repo_root: Path,
    *,
    since: str | None,
    limit: int,
    ref: str,
    project: str = DEFAULT_PROJECT,
) -> CurrencyReport:
    """Compare every sampled commit's stored receipt against its own tree."""
    receipt = receipt_path(project)
    rows: list[Row] = []
    for commit in sample_commits(repo_root, since=since, limit=limit, ref=ref):
        stored = stored_config(repo_root, commit, receipt=receipt)
        if stored is None:
            rows.append(Row(commit, None, None, "SKIP", "no readable receipt"))
            continue
        computed = computed_config(repo_root, commit, project=project)
        if computed is None:
            rows.append(Row(commit, stored, None, "UNAVAILABLE", "could not materialize the tree"))
            continue
        rows.append(Row(commit, stored, computed, "STALE" if stored != computed else "CURRENT"))
    return CurrencyReport(ref=ref, since=since, rows=tuple(rows))
