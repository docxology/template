"""Native preparation binds only canonical public source bodies to committed blobs."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

from infrastructure.project.public_reference_git import inventory
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_installed_preparation import admitted_source_files
from infrastructure.reporting.readiness_receipts import _public_roots
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

pytestmark = pytest.mark.timeout(120)


def _git(root: Path, *arguments: str) -> bytes:
    """Owned fixture setup uses actual native Git and invented public author data."""
    executable = shutil.which("git", path=os.defpath)
    assert executable is not None
    result = subprocess.run(
        [executable, "-c", "user.name=Preparation fixture", "-c", "user.email=fixture@example.invalid", *arguments],
        cwd=root,
        env={"PATH": os.defpath, "LC_ALL": "C", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"},
        capture_output=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, (result.returncode, result.stderr)
    return result.stdout


def _committed_fixture(tmp_path: Path) -> tuple[Path, str]:
    """Commit every canonical public root plus tracked files outside the public policy."""
    root = (tmp_path / "source").resolve()
    root.mkdir()
    roots, _ = _public_roots(root)
    for base in roots:
        base.mkdir(parents=True, exist_ok=True)
    (root / "README.md").write_bytes(b"# owned public root\n")
    (root / "infrastructure/witness.py").write_bytes(b"VALUE = 1\n")
    (root / ".agents/skills/owned/SKILL.md").parent.mkdir(parents=True)
    (root / ".agents/skills/owned/SKILL.md").write_bytes(b"# owned public skill\n")
    # Tracked, but outside the public artifact policy: never public source DATA.
    (root / ".agents/AGENTS.md").write_bytes(b"owned agent note\n")
    (root / ".cursor").mkdir()
    (root / ".cursor/rules.md").write_bytes(b"owned editor note\n")
    (root / "fonds/README.md").write_bytes(b"owned resource note\n")
    (root / "projects/README.md").write_bytes(b"owned project note\n")
    # Canonical source excludes runtime controls and compiled cache bodies.
    (root / "infrastructure/.venv").mkdir()
    (root / "infrastructure/.venv/runtime.txt").write_bytes(b"owned runtime control\n")
    (root / "infrastructure/__pycache__").mkdir()
    (root / "infrastructure/__pycache__/witness.pyc").write_bytes(b"owned bytecode control\n")
    deliverable = root / "projects" / PUBLIC_PROJECT_NAMES[0] / "output/html/witness.html"
    deliverable.parent.mkdir(parents=True)
    deliverable.write_bytes(b"<p>owned stable deliverable</p>\n")
    _git(root, "init", "--quiet")
    _git(root, "add", "--all", "--force")
    _git(root, "commit", "--quiet", "-m", "Owned public source fixture")
    return root, _git(root, "rev-parse", "HEAD").decode().strip()


def test_admitted_source_files_bind_only_canonical_public_bodies(tmp_path: Path) -> None:
    root, commit = _committed_fixture(tmp_path)
    reader = SnapshotReader(root)
    reference = inventory(root, commit, time.monotonic() + 60)
    for relative in (".agents/AGENTS.md", ".cursor/rules.md", "fonds/README.md", "projects/README.md"):
        with pytest.raises(ValueError):
            reader.public_path(relative)
    files = admitted_source_files(root, reader, reference, time.monotonic() + 60)
    assert set(files) == {
        "README.md",
        "infrastructure/witness.py",
        ".agents/skills/owned/SKILL.md",
        "projects/" + PUBLIC_PROJECT_NAMES[0] + "/output/html/witness.html",
    }
    assert files["infrastructure/witness.py"] == hashlib.sha256(b"VALUE = 1\n").hexdigest()
    assert reader.unchanged()


@pytest.mark.parametrize("fault", ["untracked", "edited", "deleted", "deleted-root", "deleted-output"])
def test_admitted_source_files_refuse_untracked_or_edited_public_body(tmp_path: Path, fault: str) -> None:
    root, commit = _committed_fixture(tmp_path)
    if fault == "untracked":
        (root / "infrastructure/extra.py").write_bytes(b"VALUE = 2\n")
        refusal = "untracked"
    elif fault == "edited":
        (root / "infrastructure/witness.py").write_bytes(b"VALUE = 2\n")
        refusal = "differs from its original committed blob"
    else:
        target = {
            "deleted": root / "infrastructure/witness.py",
            "deleted-root": root / "README.md",
            "deleted-output": root / "projects" / PUBLIC_PROJECT_NAMES[0] / "output/html/witness.html",
        }[fault]
        target.unlink()
        refusal = "missing a committed canonical body"
    reference = inventory(root, commit, time.monotonic() + 60)
    with pytest.raises(ValueError, match=refusal):
        admitted_source_files(root, SnapshotReader(root), reference, time.monotonic() + 60)
