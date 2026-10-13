"""Offline genuine Git/physical-tree controls for declared Source fixture DATA."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

from infrastructure.project.acceptance_fixture_preparation import MANIFEST_PATH, SCHEMA_VERSION
from infrastructure.project.public_reference import _canonical_inventory
from infrastructure.project.public_reference_git import inventory
from infrastructure.project.public_source_body_admission import (
    FixtureAdmission,
    admit_source_bodies,
    admit_source_fixtures,
)
from infrastructure.reporting.native_installed_preparation import admitted_source_files
from infrastructure.reporting.readiness_receipts import _public_roots
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

pytestmark = pytest.mark.timeout(120)


def _git(root: Path, *arguments: str) -> bytes:
    executable = shutil.which("git", path=os.defpath)
    assert executable is not None
    result = subprocess.run(
        [executable, "-c", "user.name=Source fixture", "-c", "user.email=fixture@example.invalid", *arguments],
        cwd=root,
        env={"PATH": os.defpath, "LC_ALL": "C", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"},
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def _commit(root: Path) -> str:
    _git(root, "add", "--all")
    _git(root, "commit", "--quiet", "-m", "Owned offline declaration")
    return _git(root, "rev-parse", "HEAD").decode().strip()


def _source(tmp_path: Path) -> tuple[Path, str, dict[str, bytes]]:
    """Author miniature declarations in genuine Git before ignored DATA exists.

    These invented archive body rosters test admission, not provenance of the
    production upstream archives. Separate retained reproduction uses their
    authenticated real 92-body subset.
    """
    root = (tmp_path / "source").resolve()
    root.mkdir()
    for base in _public_roots(root)[0]:
        base.mkdir(parents=True, exist_ok=True)
    (root / ".gitignore").write_text(
        "tests/fixtures/real_codebases/requests/\ntests/fixtures/real_codebases/fastapi/\ntests/fixtures/timeseries/\n"
    )
    (root / "README.md").write_bytes(b"# Owned source declaration\n")
    groups = []
    bodies: dict[str, bytes] = {}
    for name, owner, package in (
        ("requests", "psf/requests", "src/requests"),
        ("fastapi", "fastapi/fastapi", "fastapi"),
    ):
        base = "tests/fixtures/real_codebases/" + name
        commit = "1" * 40
        archive_root = name + "-" + commit
        files = []
        for relative, content in sorted(
            {"LICENSE": b"Owned license\n", package + "/__init__.py": b"VALUE = 1\n"}.items()
        ):
            bodies[base + "/" + relative] = content
            files.append(
                {
                    "path": relative,
                    "member": archive_root + "/" + relative,
                    "bytes": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "executable": False,
                }
            )
        groups.append(
            {
                "id": name,
                "root": base,
                "directories": sorted(
                    {
                        parent.as_posix()
                        for row in files
                        for parent in Path(row["path"]).parents
                        if parent.as_posix() != "."
                    }
                ),
                "archive": {
                    "url": "https://codeload.github.com/" + owner + "/tar.gz/" + commit,
                    "bytes": 1,
                    "sha256": hashlib.sha256(b"owned archive declaration").hexdigest(),
                    "root": archive_root,
                },
                "selections": ["LICENSE", package],
                "files": files,
            }
        )
    seeds = []
    for number in range(1, 11):
        filename = f"synthetic_{number:03}.json"
        source = "tests/fixtures/timeseries_seed/" + filename
        content = json.dumps({"owned_series": number}).encode() + b"\n"
        (root / source).parent.mkdir(parents=True, exist_ok=True)
        (root / source).write_bytes(content)
        relative = "synthetic/" + filename
        bodies["tests/fixtures/timeseries/" + relative] = content
        seeds.append({"path": relative, "source": source})
    groups.append(
        {"id": "timeseries", "root": "tests/fixtures/timeseries", "directories": ["synthetic"], "files": seeds}
    )
    (root / MANIFEST_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / MANIFEST_PATH).write_text(json.dumps({"schema_version": SCHEMA_VERSION, "groups": groups}))
    _git(root, "init", "--quiet")
    return root, _commit(root), bodies


def _prepare(root: Path, bodies: dict[str, bytes]) -> None:
    for relative, content in bodies.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        # The real Source mirror copier intentionally creates DATA at 0600.
        path.chmod(0o600)


def test_complete_ignored_fixture_data_is_bound_without_force_committing(tmp_path: Path) -> None:
    root, commit, bodies = _source(tmp_path)
    _prepare(root, bodies)
    assert _git(root, "ls-files", "--", *bodies) == b""
    reader = SnapshotReader(root)
    deadline = time.monotonic() + 60
    reference = inventory(root, commit, deadline)
    admitted, fixtures = admit_source_bodies(root, reader, reference, _canonical_inventory(root), deadline)
    assert set(dict(fixtures.files)) == set(bodies)
    assert all(admitted[name] == hashlib.sha256(content).hexdigest() for name, content in bodies.items())
    assert admitted_source_files(root, SnapshotReader(root), reference, deadline) == admitted
    fixtures.verify(deadline)
    rogue = "tests/fixtures/undeclared-body.txt"
    (root / rogue).write_bytes(b"Untrusted DATA\n")
    forged = FixtureAdmission(
        root,
        reader,
        reference,
        ((rogue, (len(b"Untrusted DATA\n"), hashlib.sha256(b"Untrusted DATA\n").hexdigest(), False)),),
        (),
        (),
    )
    records = _canonical_inventory(root)
    # A constructible DATA observation cannot be supplied as admission authority.
    with pytest.raises(TypeError):
        admit_source_bodies(root, reader, reference, records, deadline, fixtures=forged)  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="untracked"):
        admit_source_bodies(root, reader, reference, records, deadline)


def test_absent_fixture_groups_still_authenticate_the_committed_declaration(tmp_path: Path) -> None:
    root, commit, _ = _source(tmp_path)
    deadline = time.monotonic() + 60
    reference = inventory(root, commit, deadline)
    fixtures = admit_source_fixtures(root, SnapshotReader(root), reference, deadline)
    assert fixtures.files == () and len(fixtures.absent_groups) == 3
    fixtures.verify(deadline)
    manifest = root / MANIFEST_PATH
    manifest.write_bytes(manifest.read_bytes() + b" ")
    with pytest.raises(ValueError, match="original committed blob"):
        admit_source_fixtures(root, SnapshotReader(root), reference, deadline)


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "edited",
        "executable",
        "extra",
        "hidden-cache",
        "hidden-git",
        "hidden-venv",
        "empty-directory",
        "linked-file",
        "linked-directory",
        "fifo",
        "file-as-directory",
        "seed-edited",
        "manifest-edited",
        "manifest-missing",
        "manifest-untracked",
        "tracked-mismatch",
        "tracked-partial",
    ],
)
def test_fixture_admission_refuses_real_tree_and_raw_git_faults(tmp_path: Path, fault: str) -> None:
    root, commit, bodies = _source(tmp_path)
    _prepare(root, bodies)
    base = root / "tests/fixtures/real_codebases/requests"
    target = base / "LICENSE"
    if fault == "missing":
        target.unlink()
    elif fault == "edited":
        target.write_bytes(b"Edited body\n")
    elif fault == "executable":
        target.chmod(0o700)
    elif fault in {"extra", "hidden-cache"}:
        extra = base / ("unexpected.py" if fault == "extra" else "__pycache__/body.pyc")
        extra.parent.mkdir(parents=True, exist_ok=True)
        extra.write_bytes(b"Extra body\n")
    elif fault in {"hidden-git", "hidden-venv", "empty-directory"}:
        (base / {"hidden-git": ".git", "hidden-venv": ".venv", "empty-directory": "empty"}[fault]).mkdir()
    elif fault == "linked-file":
        target.unlink()
        target.symlink_to(root / "README.md")
    elif fault == "linked-directory":
        shutil.rmtree(base / "src")
        (base / "src").symlink_to(root / "tests/fixtures/timeseries", target_is_directory=True)
    elif fault == "fifo":
        target.unlink()
        os.mkfifo(target)
    elif fault == "file-as-directory":
        target.unlink()
        target.mkdir()
    elif fault == "seed-edited":
        (root / "tests/fixtures/timeseries_seed/synthetic_001.json").write_bytes(b"Edited seed\n")
    elif fault == "manifest-edited":
        manifest = root / MANIFEST_PATH
        manifest.write_bytes(manifest.read_bytes() + b" ")
    elif fault == "manifest-missing":
        (root / MANIFEST_PATH).unlink()
    elif fault == "manifest-untracked":
        _git(root, "rm", "--cached", "--", MANIFEST_PATH)
        _git(root, "commit", "--quiet", "-m", "Owned manifest removed from Git")
        commit = _git(root, "rev-parse", "HEAD").decode().strip()
    elif fault == "tracked-mismatch":
        target.write_bytes(b"Different committed fixture body\n")
        _git(root, "add", "--force", "--", target.relative_to(root).as_posix())
        commit = _commit(root)
        target.write_bytes(bodies[target.relative_to(root).as_posix()])
    else:
        _git(root, "add", "--force", "--", "tests/fixtures/real_codebases/requests")
        commit = _commit(root)
        target.unlink()
    reference = inventory(root, commit, time.monotonic() + 60)
    with pytest.raises((ValueError, FileNotFoundError)):
        admitted_source_files(root, SnapshotReader(root), reference, time.monotonic() + 60)


@pytest.mark.parametrize(
    "fault",
    [
        "hidden-addition",
        "hidden-aba",
        "entire-group-deletion",
        "absent-group-prepared",
        "absent-group-aba",
    ],
)
def test_held_fixture_admission_rechecks_full_physical_census(tmp_path: Path, fault: str) -> None:
    root, commit, bodies = _source(tmp_path)
    if fault not in {"absent-group-prepared", "absent-group-aba"}:
        _prepare(root, bodies)
    deadline = time.monotonic() + 60
    fixtures = admit_source_fixtures(root, SnapshotReader(root), inventory(root, commit, deadline), deadline)
    base = root / "tests/fixtures/real_codebases/requests"
    if fault in {"hidden-addition", "hidden-aba"}:
        extra = base / "__pycache__"
        extra.mkdir()
        if fault == "hidden-aba":
            extra.rmdir()
    elif fault == "entire-group-deletion":
        shutil.rmtree(base)
    elif fault == "absent-group-prepared":
        _prepare(root, bodies)
    else:
        # Missing real_codebases itself makes tests/fixtures the held ancestor.
        ancestor = root / "tests/fixtures/real_codebases"
        ancestor.mkdir()
        base.mkdir()
        base.rmdir()
        ancestor.rmdir()
    with pytest.raises(ValueError):
        fixtures.verify(deadline)
