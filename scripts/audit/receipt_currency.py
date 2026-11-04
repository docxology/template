#!/usr/bin/env python3
"""Report every mainline commit whose receipts do not describe their own tree.

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

Usage
-----
    python scripts/audit/receipt_currency.py                  # mainline since last tag
    python scripts/audit/receipt_currency.py --since v5.0.0
    python scripts/audit/receipt_currency.py --limit 40 --json
    python scripts/audit/receipt_currency.py --require-current   # exit 1 on any STALE

Exit codes: 0 clean (or report-only), 1 stale with ``--require-current``,
2 the environment could not answer (never reported as clean).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT = "templates/template_code_project"
RECEIPT = f"projects/{PROJECT}/output/reports/rendered_provenance.json"


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False)


@dataclass(frozen=True)
class Row:
    commit: str
    stored: str | None
    computed: str | None
    verdict: str
    detail: str = ""


def _stored_config(commit: str) -> str | None:
    result = _git("show", f"{commit}:{RECEIPT}")
    if result.returncode != 0:
        return None
    try:
        payload = json.loads(result.stdout)
        digest = payload["fingerprints"]["config"]["sha256"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return None
    return digest if isinstance(digest, str) else None


def _computed_config(commit: str) -> str | None:
    """Fingerprint the commit's own tree, using the repository's real implementation."""
    scratch = Path(tempfile.mkdtemp(dir="/tmp")).resolve()
    try:
        checkout = subprocess.run(
            ["git", "--work-tree", str(scratch), "checkout", commit, "--", "."],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if checkout.returncode != 0:
            return None
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        from infrastructure.validation.rendered_snapshot._records import _fingerprint, _project_records

        project_root = (scratch / "projects" / PROJECT).resolve()
        if not project_root.is_dir():
            return None
        _source, config = _project_records(scratch, project_root, lexical_project_root=project_root)
        return _fingerprint(config).sha256
    except Exception:  # noqa: BLE001 - a failed measurement must not read as clean
        return None
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def _commits(since: str | None, limit: int, ref: str) -> list[str]:
    revision_range = f"{since}^..{ref}" if since else ref
    result = _git("rev-list", "--first-parent", f"--max-count={limit}", revision_range)
    if result.returncode != 0:
        raise SystemExit(f"cannot resolve commits for {revision_range!r}: {result.stderr.strip()}")
    return result.stdout.split()


def _last_tag() -> str | None:
    result = _git("describe", "--tags", "--abbrev=0", "--match", "v*")
    return result.stdout.strip() or None if result.returncode == 0 else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--since", default=None, help="Revision to sample from (default: the newest v* tag).")
    parser.add_argument("--limit", type=int, default=40, help="Maximum number of first-parent commits.")
    parser.add_argument(
        "--ref",
        default="origin/main",
        help="Revision to sample (default: origin/main). Never HEAD by default: a canonical checkout "
        "may sit on a stale branch, which would silently sample the wrong history.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table.")
    parser.add_argument(
        "--require-current",
        action="store_true",
        help="Exit non-zero when any sampled commit carries a stale receipt.",
    )
    args = parser.parse_args(argv)

    since = args.since or _last_tag()
    commits = _commits(since, args.limit, args.ref)
    if not commits:
        raise SystemExit("no commits to sample; refusing to report a clean result")

    rows: list[Row] = []
    for commit in commits:
        stored = _stored_config(commit)
        if stored is None:
            rows.append(Row(commit, None, None, "SKIP", "no readable receipt"))
            continue
        computed = _computed_config(commit)
        if computed is None:
            rows.append(Row(commit, stored, None, "UNAVAILABLE", "could not materialize the tree"))
            continue
        rows.append(Row(commit, stored, computed, "STALE" if stored != computed else "CURRENT"))

    stale = [row for row in rows if row.verdict == "STALE"]
    unavailable = [row for row in rows if row.verdict == "UNAVAILABLE"]

    if args.json:
        print(json.dumps({"since": since, "rows": [asdict(row) for row in rows]}, indent=2))
    else:
        print(f"receipt currency on {args.ref} since {since or '(beginning)'} — {len(rows)} commit(s)\n")
        print(f"{'commit':13s} {'stored':18s} {'computed':18s} verdict")
        print("-" * 66)
        for row in rows:
            print(f"{row.commit[:12]:13s} {str(row.stored)[:16]:18s} {str(row.computed)[:16]:18s} {row.verdict}")
        print(
            f"\nRESULT: {len(rows) - len(stale) - len(unavailable)} current, "
            f"{len(stale)} STALE, {len(unavailable)} unavailable"
        )

    if unavailable:
        print(
            f"\n{len(unavailable)} commit(s) could not be measured; this is not a clean result.",
            file=sys.stderr,
        )
        return 2
    if stale and args.require_current:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
