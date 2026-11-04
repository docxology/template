"""Receipt currency must measure history without mutating the caller's repository.

The defect these tests pin: ``computed_config`` materialized a commit with
``git --work-tree <scratch> checkout <commit> -- .``. That alternate work-tree
still writes into the caller's real ``.git/index``, so measuring one commit
staged every entry of it. Sampling forty commits left hundreds of ``MM`` paths
that nobody authored, which then read as "someone else is editing" during
release work and corrupted every later tree measurement.

The invariant is narrow and absolute: measuring history may read the repository
and must never write to it. These are real Git repositories on ``tmp_path``; no
mocks and no dependence on this checkout's own history.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from infrastructure.reporting.receipt_currency import computed_config, stored_config

_RECEIPT = "projects/templates/template_code_project/output/reports/rendered_provenance.json"

_RECEIPT_BODY = """{
  "fingerprints": {
    "config": {
      "sha256": "da31a2b1775f2a096b901d72af78e9d8077eec39e5fca91fb69d998dc8c199c3"
    }
  }
}
"""


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)


def _seed_repository(root: Path) -> tuple[str, str]:
    """Create two commits, returning ``(sampled_commit, head_commit)``.

    The sampled commit is deliberately *not* ``HEAD``. An earlier version of
    this fixture sampled ``HEAD`` itself, and every assertion passed on the
    broken code: staging the same blobs the index already held leaves
    ``git diff --cached`` empty, so the test proved nothing. The defect is only
    observable when measuring a commit the index does not already describe.
    """
    repo = root / "repo"
    (repo / "projects/templates/template_code_project/manuscript").mkdir(parents=True)
    (repo / "projects/templates/template_code_project/manuscript/config.yaml").write_text(
        "paper:\n  title: fixture\n", encoding="utf-8"
    )
    receipt = repo / _RECEIPT
    receipt.parent.mkdir(parents=True)
    receipt.write_text(_RECEIPT_BODY, encoding="utf-8")
    (repo / "README.md").write_text("# fixture\n", encoding="utf-8")
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "fixture@example.invalid")
    _git(repo, "config", "user.name", "fixture")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed")
    sampled = _git(repo, "rev-parse", "HEAD").stdout.strip()

    # Move HEAD forward so the measured commit is historical, as it is in the
    # real check (which samples origin/main history from a working checkout).
    (repo / "README.md").write_text("# fixture\n\nlater work\n", encoding="utf-8")
    (repo / "LATER.md").write_text("unrelated follow-up\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "later")
    return sampled, _git(repo, "rev-parse", "HEAD").stdout.strip()


def _staged(repo: Path) -> list[str]:
    return [line for line in _git(repo, "diff", "--cached", "--name-only").stdout.splitlines() if line]


def test_measurement_never_stages_anything_in_the_caller(tmp_path: Path) -> None:
    sampled, head = _seed_repository(tmp_path)
    repo = tmp_path / "repo"
    assert sampled != head
    assert _staged(repo) == []

    stored_config(repo, sampled, receipt=_RECEIPT)
    computed_config(repo, sampled)

    assert _staged(repo) == [], "measuring a commit staged entries into the caller's own index"


def test_repeated_measurement_leaves_the_index_and_worktree_unchanged(tmp_path: Path) -> None:
    sampled, _head = _seed_repository(tmp_path)
    repo = tmp_path / "repo"
    before_status = _git(repo, "status", "--porcelain").stdout

    for _ in range(3):
        computed_config(repo, sampled)

    assert _git(repo, "status", "--porcelain").stdout == before_status
    assert (repo / "README.md").read_text(encoding="utf-8") == "# fixture\n\nlater work\n"


def test_unreadable_receipt_still_writes_nothing(tmp_path: Path) -> None:
    """A refused measurement is the case most likely to leave residue behind."""
    sampled, _head = _seed_repository(tmp_path)
    repo = tmp_path / "repo"

    assert stored_config(repo, sampled, receipt="projects/absent/reports/none.json") is None
    assert _staged(repo) == []
