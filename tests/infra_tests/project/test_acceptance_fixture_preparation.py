"""Real Git, archive and filesystem controls for the stdlib fixture producer."""

from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import shutil
import subprocess
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any

import pytest

from infrastructure.project.acceptance_fixture_preparation import (
    MANIFEST_PATH,
    SCHEMA_VERSION,
    _archive_bodies,
    _committed_bytes,
    _held_parent,
    _read_regular,
    _verify_created,
    _verify_directory_snapshot,
    _write_new,
    parse_fixture_manifest,
    prepare_acceptance_fixtures,
)

ROOT = Path(__file__).resolve().parents[3]


def _tar(group: dict[str, Any], entries: list[tuple[str, bytes | None, str]]) -> bytes:
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz") as archive:
        for path, body, kind in entries:
            member = tarfile.TarInfo(group["archive"]["root"] + "/" + path)
            member.mode = 0o755 if kind == "directory" else 0o644
            if kind == "directory":
                member.type = tarfile.DIRTYPE
            elif kind == "symlink":
                member.type = tarfile.SYMTYPE
                member.linkname = "../../owned-outside"
            else:
                assert body is not None
                member.size = len(body)
            archive.addfile(member, io.BytesIO(body) if kind == "file" and body is not None else None)
    return output.getvalue()


def _owned_fixture(tmp_path: Path) -> tuple[Path, Path, dict[str, Any], dict[str, list[tuple[str, bytes | None, str]]]]:
    """Commit mini test trees and actual seed copies; make no upstream claim."""
    root = (tmp_path / "source").resolve()
    root.mkdir()
    archives = (tmp_path / "archives").resolve()
    archives.mkdir()
    manifest = json.loads((ROOT / MANIFEST_PATH).read_text())
    all_entries: dict[str, list[tuple[str, bytes | None, str]]] = {}
    for group in manifest["groups"]:
        if group["id"] == "timeseries":
            for record in group["files"]:
                target = root / record["source"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / record["source"], target)
            continue
        package = "src/requests/__init__.py" if group["id"] == "requests" else "fastapi/__init__.py"
        bodies = {"LICENSE": b"Owned non-upstream test fixture license.\n", package: b"# Owned test archive body.\n"}
        group["directories"] = sorted(
            {str(parent) for name in bodies for parent in PurePosixPath(name).parents if str(parent) != "."}
        )
        group["files"] = [
            {
                "path": path,
                "member": group["archive"]["root"] + "/" + path,
                "bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
                "executable": False,
            }
            for path, body in sorted(bodies.items())
        ]
        entries = [(path, None, "directory") for path in group["directories"]]
        entries.extend((path, body, "file") for path, body in sorted(bodies.items()))
        all_entries[group["id"]] = entries
        content = _tar(group, entries)
        group["archive"]["bytes"] = len(content)
        group["archive"]["sha256"] = hashlib.sha256(content).hexdigest()
        (archives / (group["id"] + ".tar.gz")).write_bytes(content)
    target = root / MANIFEST_PATH
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(manifest))
    executable = shutil.which("git", path=os.defpath)
    assert executable, "The fixture contract requires actual native Git"
    for arguments in (
        ("init", "--quiet"),
        ("add", "--all"),
        ("commit", "--quiet", "-m", "Owned fixture preparation test"),
    ):
        result = subprocess.run(
            [executable, "-c", "user.name=Owned fixture", "-c", "user.email=fixture@example.invalid", *arguments],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, result.stderr
    return root, archives, manifest, all_entries


def test_stdlib_entrypoint_runs_before_platform_dependencies(tmp_path: Path) -> None:
    executable = shutil.which("python3", path=os.defpath)
    assert executable, "Hosted fixture preparation requires preinstalled Python3"
    program = (
        "import runpy,sys;"
        "sys.argv=[sys.argv[1],'--help'];"
        "\ntry: runpy.run_path(sys.argv[0],run_name='__main__')"
        "\nexcept SystemExit as outcome: assert outcome.code==0"
        "\nassert not any(name=='infrastructure' or name.startswith('infrastructure.') for name in sys.modules)"
    )
    result = subprocess.run(
        [executable, "-S", "-c", program, str(ROOT / "scripts/fixtures/prepare_acceptance.py")],
        cwd=tmp_path,
        env=dict(os.environ, PYTHONPATH="", PYTHONHOME=""),
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "--archives" in result.stdout


def test_preparation_retains_exact_committed_seed_and_archive_bodies(tmp_path: Path) -> None:
    root, archives, manifest, _ = _owned_fixture(tmp_path)
    result = prepare_acceptance_fixtures(root, archives=archives)
    assert result["groups"] == {"requests": 2, "fastapi": 2, "timeseries": 10}
    assert result["acceptance"] is False
    for group in manifest["groups"]:
        for record in group["files"]:
            target = root / group["root"] / record["path"]
            assert target.is_file() and not target.is_symlink()
            if group["id"] == "timeseries":
                assert target.read_bytes() == (root / record["source"]).read_bytes()
            else:
                assert len(target.read_bytes()) == record["bytes"]
                assert hashlib.sha256(target.read_bytes()).hexdigest() == record["sha256"]
            assert not target.stat().st_mode & 0o111
    with pytest.raises(ValueError, match="existing target"):
        prepare_acceptance_fixtures(root, archives=archives)


def test_preparation_refuses_changed_git_inputs_and_existing_or_linked_paths(tmp_path: Path) -> None:
    for fault in ("manifest", "seed", "seed-symlink", "parent-symlink", "existing-target"):
        case = tmp_path / fault
        case.mkdir()
        root, archives, _, _ = _owned_fixture(case)
        sentinel: Path | None = None
        if fault == "manifest":
            target = root / MANIFEST_PATH
            target.write_bytes(target.read_bytes() + b" ")
        elif fault == "seed":
            (root / "tests/fixtures/timeseries_seed/synthetic_001.json").write_bytes(b"owned corrupt seed")
        elif fault == "seed-symlink":
            target = root / "tests/fixtures/timeseries_seed/synthetic_001.json"
            outside = case / "outside-seed"
            outside.write_bytes(target.read_bytes())
            target.unlink()
            target.symlink_to(outside)
        elif fault == "parent-symlink":
            outside = case / "outside-target"
            outside.mkdir()
            (root / "tests/fixtures/real_codebases").symlink_to(outside, target_is_directory=True)
        else:
            sentinel = root / "tests/fixtures/real_codebases/requests/owned-existing"
            sentinel.parent.mkdir(parents=True)
            sentinel.write_bytes(b"preserve existing input")
        with pytest.raises((OSError, ValueError)) as refusal:
            prepare_acceptance_fixtures(root, archives=archives)
        if fault in {"manifest", "seed"}:
            assert "differs from its committed raw Git blob" in str(refusal.value)
        elif fault == "seed-symlink":
            assert "not a bounded regular file" in str(refusal.value)
        elif fault == "parent-symlink":
            assert "substituted target ancestor" in str(refusal.value)
        else:
            assert "existing target" in str(refusal.value)
        assert not (root / "tests/fixtures/real_codebases/fastapi").exists()
        assert not (root / "tests/fixtures/timeseries").exists()
        if sentinel is not None:
            assert sentinel.read_bytes() == b"preserve existing input"

    case = tmp_path / "commit-aba"
    case.mkdir()
    root, _, _, _ = _owned_fixture(case)
    executable = shutil.which("git", path=os.defpath)
    assert executable

    def git(*arguments: str) -> str:
        result = subprocess.run(
            [executable, "-c", "user.name=Owned ABA fixture", "-c", "user.email=fixture@example.invalid", *arguments],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        return result.stdout.strip()

    original = git("rev-parse", "HEAD")
    relative = "tests/fixtures/timeseries_seed/synthetic_001.json"
    (root / relative).write_bytes(b"Owned different committed test seed body; not scientific data.\n")
    git("add", "--", relative)
    git("commit", "--quiet", "-m", "Owned alternate seed commit")
    alternate = git("rev-parse", "HEAD")
    assert alternate != original
    assert _committed_bytes(root, relative, commit=alternate)[0] == (root / relative).read_bytes()
    with pytest.raises(ValueError, match="differs from its committed raw Git blob"):
        _committed_bytes(root, relative, commit=original)
    # Only this owned fixture's ref/index is restored, retaining dirty B bytes.
    git("reset", "--mixed", original)
    assert git("rev-parse", "HEAD") == original
    with pytest.raises(ValueError, match="differs from its committed raw Git blob"):
        _committed_bytes(root, relative, commit=original)


def test_exact_archive_member_census_refuses_real_tar_faults(tmp_path: Path) -> None:
    _, archives, manifest, original = _owned_fixture(tmp_path)
    selected = manifest["groups"][0]
    assert len(_archive_bodies(selected, (archives / "requests.tar.gz").read_bytes())) == 2
    for fault in ("changed-bytes", "extra", "missing", "duplicate", "symlink", "traversal", "empty-directory"):
        group = copy.deepcopy(selected)
        entries = list(original["requests"])
        if fault == "changed-bytes":
            entries[-1] = (entries[-1][0], b"changed actual archive member", "file")
        elif fault == "extra":
            entries.append(("src/requests/extra.py", b"owned unexpected body", "file"))
        elif fault == "missing":
            entries.pop()
        elif fault == "duplicate":
            entries.append(entries[-1])
        elif fault == "symlink":
            entries[-1] = (entries[-1][0], None, "symlink")
        elif fault == "traversal":
            entries.append(("src/requests/../../outside", b"owned outside body", "file"))
        else:
            entries.append(("src/requests/undeclared-empty", None, "directory"))
        content = _tar(group, entries)
        # Authenticate the actual owned fault archive so member checks, rather
        # than only the outer compressed digest, must reject its wrong input.
        group["archive"]["bytes"] = len(content)
        group["archive"]["sha256"] = hashlib.sha256(content).hexdigest()
        with pytest.raises(ValueError):
            _archive_bodies(group, content)


def test_manifest_requires_complete_fixed_roster_and_confined_declarations() -> None:
    content = (ROOT / MANIFEST_PATH).read_bytes()
    original = parse_fixture_manifest(content)
    assert original["schema_version"] == SCHEMA_VERSION
    repeated = content.replace(b'"schema_version":', b'"schema_version":"duplicate","schema_version":', 1)
    with pytest.raises(ValueError, match="repeats"):
        parse_fixture_manifest(repeated)
    for fault in ("group", "root", "url", "member", "directories", "seed"):
        manifest = copy.deepcopy(original)
        if fault == "group":
            manifest["groups"].pop()
        elif fault == "root":
            manifest["groups"][0]["root"] = "tests/fixtures/real_codebases/../outside"
        elif fault == "url":
            manifest["groups"][0]["archive"]["url"] = "https://example.invalid/owned-not-contacted"
        elif fault == "member":
            manifest["groups"][0]["files"][0]["member"] = "../outside"
        elif fault == "directories":
            manifest["groups"][0]["directories"].append("__pycache__")
        else:
            manifest["groups"][2]["files"].pop()
        with pytest.raises(ValueError):
            parse_fixture_manifest(json.dumps(manifest).encode())


def test_real_fifo_inputs_are_refused_without_blocking(tmp_path: Path) -> None:
    executable = shutil.which("python3", path=os.defpath)
    assert executable
    for target in ("manifest", "seed", "archive"):
        case = tmp_path / target
        case.mkdir()
        root, archives, _, _ = _owned_fixture(case)
        path = (
            root / MANIFEST_PATH
            if target == "manifest"
            else (
                root / "tests/fixtures/timeseries_seed/synthetic_001.json"
                if target == "seed"
                else archives / "requests.tar.gz"
            )
        )
        path.unlink()
        os.mkfifo(path, mode=0o600)
        result = subprocess.run(
            [
                executable,
                "-S",
                str(ROOT / "scripts/fixtures/prepare_acceptance.py"),
                "--repo-root",
                str(root),
                "--archives",
                str(archives),
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        assert result.returncode == 1, result.stderr
        assert "not a bounded regular file" in result.stderr
        assert not (root / "tests/fixtures/real_codebases/fastapi").exists()


def test_held_namespaces_and_created_inode_readback_refuse_replacement(tmp_path: Path) -> None:
    root = (tmp_path / "source").resolve()
    root.mkdir()
    directory = root / "owned"
    directory.mkdir()
    original_root = (root.stat().st_dev, root.stat().st_ino)
    with pytest.raises(ValueError, match="namespace changed"):
        with _held_parent(root, "owned/body", expected_root=original_root):
            directory.rename(root / "detached")
            directory.mkdir()
    directory.rmdir()
    (root / "detached").rename(directory)
    created = _write_new(root, "owned/body", b"held actual bytes", False, expected_root=original_root)
    assert _read_regular(root, "owned/body", expected_root=original_root, expected_observation=created) == (
        b"held actual bytes",
        False,
    )
    (directory / "body").unlink()
    (directory / "body").write_bytes(b"held actual bytes")
    with pytest.raises(ValueError, match="held file identity changed"):
        _read_regular(root, "owned/body", expected_root=original_root, expected_observation=created)
    with pytest.raises(FileExistsError):
        _write_new(root, "owned/body", b"must not replace", False, expected_root=original_root)
    assert (directory / "body").read_bytes() == b"held actual bytes"
    current = directory / "body"
    identity = tuple(
        getattr(current.stat(), name)
        for name in ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns", "st_mode")
    )
    directories = {"owned": (directory.stat().st_dev, directory.stat().st_ino)}
    groups = [{"id": "owned", "root": "owned"}]
    prepared = {"owned": {"body": (b"held actual bytes", False)}}
    _verify_created(root, groups, prepared, directories, {"owned/body": identity}, original_root)
    (directory / "__pycache__").mkdir()
    with pytest.raises(ValueError, match="directory differs"):
        _verify_created(root, groups, prepared, directories, {"owned/body": identity}, original_root)
    with _held_parent(root, "owned", expected_root=original_root) as (parent, name):
        descriptor = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        try:
            before = os.fstat(descriptor)
            names = os.listdir(descriptor)
            transient = directory / "owned-extra"
            transient.write_bytes(b"owned actual filesystem ABA")
            transient.unlink()
            assert os.listdir(descriptor) == names
            assert (os.fstat(descriptor).st_dev, os.fstat(descriptor).st_ino) == (before.st_dev, before.st_ino)
            with pytest.raises(ValueError, match="directory changed during census"):
                _verify_directory_snapshot(parent, name, descriptor, before)
        finally:
            os.close(descriptor)
    root.rename(tmp_path / "old-source")
    root.mkdir()
    with pytest.raises(ValueError, match="Root changed"):
        with _held_parent(root, "body", expected_root=original_root):
            pass
