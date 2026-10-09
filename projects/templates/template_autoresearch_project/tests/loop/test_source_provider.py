"""Real checkout controls for standalone source-integration provider selection."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from autoresearch_source_provider import (
    PROJECT_PATH,
    SOURCE_COMMIT_ENV,
    SOURCE_ROOT_ENV,
    _SOURCE_ROOTS,
    _read_source,
    _source_records,
    _validate_metadata,
    resolve_source_provider,
    source_identity,
)
from infrastructure.project.copy_exemplar import export_exemplar


def _git(root: Path, *arguments: str) -> str:
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    result = subprocess.run(
        [
            "git",
            "-c",
            "user.name=Autoresearch source fixture",
            "-c",
            "user.email=source-fixture@example.invalid",
            "-c",
            "core.hooksPath=/dev/null",
            "-C",
            str(root),
            *arguments,
        ],
        env=environment,
        check=True,
        text=True,
        capture_output=True,
        timeout=30,
    )
    return result.stdout.strip()


@pytest.fixture(scope="module")
def committed_actual_provider(repo_root: Path, tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, str]:
    """Commit actual current Root bytes locally; this is not remote release evidence."""
    root = (tmp_path_factory.mktemp("actual-platform-provider") / "root").resolve()
    root.mkdir()
    ignored = shutil.ignore_patterns(
        ".git",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        "htmlcov",
        "output",
        "dist",
        "build",
        ".coverage*",
        "*.egg-info",
        "*.pyc",
    )
    for relative in _SOURCE_ROOTS:
        source = repo_root / relative
        destination = root / relative
        if source.is_dir():
            shutil.copytree(source, destination, ignore=ignored)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    assert source_identity(root) == source_identity(repo_root)
    _git(root, "init", "--initial-branch=main")
    # The admitted inventory includes actual bytes hidden by nested Git ignore
    # rules. Commit exactly those owned inputs; ignored extras must still fail
    # production admission rather than silently disappearing from this fixture.
    files = [name for name, kind, _, _ in _source_records(root) if kind == "file"]
    for offset in range(0, len(files), 128):
        _git(root, "--literal-pathspecs", "add", "--force", "--", *files[offset : offset + 128])
    _git(root, "commit", "--no-gpg-sign", "-m", "Actual platform source fixture")
    return root, _git(root, "rev-parse", "HEAD")


def _nomination(root: Path, commit: str) -> dict[str, str]:
    return {SOURCE_ROOT_ENV: str(root), SOURCE_COMMIT_ENV: commit}


def test_actual_source_only_export_requires_and_accepts_exact_provider(
    committed_actual_provider: tuple[Path, str],
) -> None:
    root, commit = committed_actual_provider
    # A root-nominated pytest --basetemp may itself be inside the monorepo.
    # Use a physically independent workspace, preserving the ancestor control.
    with tempfile.TemporaryDirectory(prefix="autoresearch-provider-export-") as workspace:
        exported = Path(workspace).resolve() / "standalone"
        export_exemplar(root, "templates/template_autoresearch_project", exported)
        assert not (exported / "output").exists()
        assert all(not (ancestor / "infrastructure").exists() for ancestor in (exported, *exported.parents))
        with pytest.raises(ValueError, match="standalone source integration requires"):
            resolve_source_provider(exported, {})
        provider = resolve_source_provider(exported, _nomination(root, commit))
        assert provider.root == root
        assert provider.commit == commit
        assert provider.identity == source_identity(root)
        provider.assert_unchanged()


def test_unrelated_infrastructure_ancestor_cannot_nominate_provider(tmp_path: Path) -> None:
    (tmp_path / "infrastructure").mkdir()
    project = tmp_path / "unrelated" / "template_autoresearch_project"
    project.mkdir(parents=True)
    with pytest.raises(ValueError, match="standalone source integration requires"):
        resolve_source_provider(project, {})


@pytest.mark.parametrize(
    "environment",
    [
        {SOURCE_ROOT_ENV: "/unused"},
        {SOURCE_COMMIT_ENV: "0" * 40},
        _nomination(Path("relative"), "0" * 40),
        _nomination(Path("/unused"), "HEAD"),
    ],
)
def test_external_provider_requires_exact_pair(environment: dict[str, str], tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="absolute path|path must be absolute|exact 40-hex"):
        resolve_source_provider(tmp_path, environment)


def test_actual_provider_reads_native_blobs_despite_local_git_replacement(
    committed_actual_provider: tuple[Path, str], tmp_path: Path
) -> None:
    original, _ = committed_actual_provider
    root = (tmp_path / "provider").resolve()
    _git(original, "clone", "--no-hardlinks", "--", str(original), str(root))
    commit = _git(root, "rev-parse", "HEAD")
    relative = "infrastructure/_version.py"
    source = root / relative
    original_content = source.read_bytes()
    replacement_content = original_content + b"\n# actual Git replacement control\n"
    source.write_bytes(replacement_content)
    _git(root, "add", "--", relative)
    _git(root, "commit", "--no-gpg-sign", "-m", "Actual source replacement control")
    replacement_commit = _git(root, "rev-parse", "HEAD")
    _git(root, "reset", "--hard", commit)
    _git(root, "replace", commit, replacement_commit)
    # Ordinary Git demonstrably resolves substituted bytes while HEAD and the
    # physical source remain original. Admission must use the native object view.
    assert _git(root, "show", f"{commit}:{relative}") == replacement_content.decode().strip()
    assert _git(root, "rev-parse", "HEAD") == commit
    assert source.read_bytes() == original_content
    provider = resolve_source_provider(tmp_path, _nomination(root, commit))
    provider.assert_unchanged()
    # Align the owned index and physical source with the replacement so ordinary
    # Git reports clean under the old label. Native custody must still refuse it.
    _git(root, "read-tree", replacement_commit)
    source.write_bytes(replacement_content)
    assert _git(root, "status", "--porcelain", "--untracked-files=all") == ""
    with pytest.raises(ValueError, match="must have clean committed source"):
        resolve_source_provider(tmp_path, _nomination(root, commit))


def test_actual_provider_rejects_wrong_commit(committed_actual_provider: tuple[Path, str], tmp_path: Path) -> None:
    root, _ = committed_actual_provider
    with pytest.raises(ValueError, match="HEAD differs"):
        resolve_source_provider(tmp_path, _nomination(root, "0" * 40))


@pytest.mark.parametrize(
    "relative,marker,diagnostic",
    [
        ("pyproject.toml", b'version = "4.0.1"', "research-project-template 4.0.1"),
        ((PROJECT_PATH / "pyproject.toml").as_posix(), b'platform_version = "4.0.1"', "canonical Autoresearch 4.0.1"),
    ],
)
def test_metadata_validation_binds_actual_held_bytes_across_file_replacement(
    relative: str,
    marker: bytes,
    diagnostic: str,
    committed_actual_provider: tuple[Path, str],
    tmp_path: Path,
) -> None:
    original, _ = committed_actual_provider
    root = (tmp_path / "provider").resolve()
    _git(original, "clone", "--no-hardlinks", "--", str(original), str(root))
    metadata = root / relative
    held_valid = _read_source(metadata)
    assert marker in held_valid
    metadata.write_bytes(held_valid.replace(marker, marker.replace(b"4.0.1", b"3.8.0"), 1))
    held_invalid = _read_source(metadata)
    assert held_invalid != held_valid
    # Parsing the admitted valid buffer never rereads the now-invalid file.
    _validate_metadata(relative, held_valid)
    # The source fingerprint must validate its own current held bytes too;
    # separate old metadata validation cannot admit this replacement.
    with pytest.raises(ValueError, match=diagnostic):
        source_identity(root)
    metadata.write_bytes(held_valid)
    with pytest.raises(ValueError, match=diagnostic):
        _validate_metadata(relative, held_invalid)
    provider = resolve_source_provider(tmp_path, _nomination(root, _git(root, "rev-parse", "HEAD")))
    assert provider.identity == source_identity(root)
    provider.assert_unchanged()


def test_dirty_canonical_monorepo_remains_explicit_local_source(committed_actual_provider: tuple[Path, str]) -> None:
    original, _ = committed_actual_provider
    # This control uses its own real clone so no other test/provider source is changed.
    with_clone = original.parent / "dirty-monorepo"
    _git(original, "clone", "--no-hardlinks", "--", str(original), str(with_clone))
    selected = with_clone / "infrastructure/_version.py"
    selected.write_bytes(selected.read_bytes() + b"\n# genuine local diagnostic source edit\n")
    provider = resolve_source_provider(with_clone / PROJECT_PATH, {})
    assert provider.root == with_clone.resolve()
    assert provider.commit is None
    provider.assert_unchanged()
    selected.write_bytes(selected.read_bytes() + b"# later source mutation\n")
    with pytest.raises(ValueError, match="changed after test admission"):
        provider.assert_unchanged()


@pytest.mark.parametrize(
    "mutation", ["dirty", "assume-unchanged", "deleted", "ignored-untracked", "symlink", "wrong-version"]
)
def test_real_external_provider_rejects_source_substitution(
    mutation: str,
    committed_actual_provider: tuple[Path, str],
    tmp_path: Path,
) -> None:
    original, _ = committed_actual_provider
    root = (tmp_path / "provider").resolve()
    _git(original, "clone", "--no-hardlinks", "--", str(original), str(root))
    commit = _git(root, "rev-parse", "HEAD")
    selected = root / "infrastructure/_version.py"
    if mutation == "assume-unchanged":
        _git(root, "update-index", "--assume-unchanged", "infrastructure/_version.py")
        selected.write_bytes(selected.read_bytes() + b"\n# hidden changed source\n")
        assert _git(root, "status", "--porcelain") == ""
    elif mutation == "deleted":
        _git(root, "update-index", "--assume-unchanged", "infrastructure/autoresearch/planner.py")
        (root / "infrastructure/autoresearch/planner.py").unlink()
        assert _git(root, "status", "--porcelain") == ""
    elif mutation == "ignored-untracked":
        (root / ".git/info/exclude").write_text("infrastructure/uncommitted_provider.py\n", encoding="utf-8")
        (root / "infrastructure/uncommitted_provider.py").write_text("raise RuntimeError('uncommitted')\n")
        assert _git(root, "status", "--porcelain") == ""
    elif mutation == "symlink":
        selected.unlink()
        selected.symlink_to(original / "infrastructure/_version.py")
        _git(root, "add", "--all")
        _git(root, "commit", "--no-gpg-sign", "-m", "Unsupported source link")
        commit = _git(root, "rev-parse", "HEAD")
    elif mutation == "wrong-version":
        metadata = root / "pyproject.toml"
        source = metadata.read_text()
        assert 'version = "4.0.1"' in source
        metadata.write_text(source.replace('version = "4.0.1"', 'version = "3.8.0"', 1))
        _git(root, "add", "--all")
        _git(root, "commit", "--no-gpg-sign", "-m", "Actual invalid version control")
        commit = _git(root, "rev-parse", "HEAD")
    else:
        selected.write_bytes(selected.read_bytes() + b"\n# changed source\n")
    with pytest.raises(ValueError, match="source|research-project-template 4.0.1"):
        resolve_source_provider(tmp_path, _nomination(root, commit))
