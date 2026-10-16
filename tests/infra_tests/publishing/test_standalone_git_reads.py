"""Actual configured Git fsmonitor must not mutate a held publication index."""

from __future__ import annotations

import hashlib
import shlex
import subprocess
from pathlib import Path

import pytest

from infrastructure.publishing._standalone_git import (
    _git,
    _git_environment,
    _git_clean_source_inventory,
    _git_head_status,
    _git_source_inventory,
)
from infrastructure.publishing._standalone_provider_admission import _git_provider_closing_metadata
from infrastructure.publishing.standalone_install_lock import PROVIDER_URLS, ROOT_PACKAGE
from infrastructure.publishing.standalone_install_projection import GitInstallProvider, _admit_provider
from infrastructure.publishing.standalone_mirror import _validate_git_destination_current


def _index_identity(path: Path) -> tuple[int, int, int, int, int, int, str]:
    observed = path.stat()
    return (
        observed.st_dev,
        observed.st_ino,
        observed.st_mode,
        observed.st_size,
        observed.st_mtime_ns,
        observed.st_ctime_ns,
        hashlib.sha256(path.read_bytes()).hexdigest(),
    )


def test_metadata_reads_disable_actual_fsmonitor_and_optional_index_writes(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    def fixture_git(args: list[str]) -> None:
        subprocess.run(
            ["git", "--no-replace-objects", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", *args],
            cwd=repo,
            env=_git_environment(),
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        )

    fixture_git(["init", "-q"])
    (repo / "infrastructure").mkdir()
    (repo / "infrastructure" / "witness.py").write_text("VALUE = 1\n", encoding="utf-8")
    fixture_git(["add", "-A"])
    fixture_git(["-c", "user.name=Test", "-c", "user.email=t@example.com", "commit", "-qm", "fixture"])
    marker = repo / ".git" / "fsmonitor-invoked"
    hook = repo / ".git" / "fixture-fsmonitor"
    hook.write_text(
        f"#!/bin/sh\nprintf 'actual-fsmonitor\\n' > {shlex.quote(str(marker))}\nprintf 'fixture-token\\000/\\000'\n",
        encoding="utf-8",
    )
    hook.chmod(0o700)
    fixture_git(["config", "core.fsmonitor", str(hook)])
    # Real positive control proves this exact repository hook can run.
    original = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=repo,
        env={**_git_environment(), "GIT_OPTIONAL_LOCKS": "1"},
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    assert original.stdout == "" and marker.read_text(encoding="utf-8") == "actual-fsmonitor\n"
    marker.unlink()
    index = repo / ".git" / "index"
    before = _index_identity(index)
    assert _git_environment()["GIT_OPTIONAL_LOCKS"] == "0"
    head, label, status = _git_head_status(repo)
    assert label is None and status == ""
    assert _git(["status", "--porcelain", "--untracked-files=all"], repo).stdout == ""
    tracked, tree = _git_source_inventory(repo, head)
    assert tracked == ["infrastructure/witness.py"]
    assert "infrastructure/witness.py" in tree
    assert not marker.exists()
    assert _index_identity(index) == before
    assert _git(["config", "--local", "--get", "core.fsmonitor"], repo).stdout.strip() == str(hook)


def _actual_repository(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _fixture_git(repo, ["init", "-q"])
    (repo / "infrastructure").mkdir()
    (repo / "infrastructure/witness.py").write_text("VALUE = 1\n", encoding="utf-8")
    _fixture_git(repo, ["add", "-A"])
    _fixture_git(repo, ["-c", "user.name=Test", "-c", "user.email=t@example.com", "commit", "-qm", "fixture"])
    head = _fixture_git(repo, ["rev-parse", "--verify", "HEAD^{commit}"]).stdout.strip()
    return repo, head


def _fixture_git(repo: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "--no-replace-objects", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", *args],
        cwd=repo,
        env=_git_environment(),
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )


def test_actual_clean_inventory_cohort_preserves_index_and_fsmonitor(tmp_path: Path) -> None:
    repo, head = _actual_repository(tmp_path)
    marker = repo / ".git/fsmonitor-invoked"
    hook = repo / ".git/fixture-fsmonitor"
    hook.write_text(
        f"#!/bin/sh\nprintf 'actual-fsmonitor\\n' > {shlex.quote(str(marker))}\nprintf 'fixture-token\\000/\\000'\n",
        encoding="utf-8",
    )
    hook.chmod(0o700)
    _fixture_git(repo, ["config", "core.fsmonitor", str(hook)])
    subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=repo,
        env={**_git_environment(), "GIT_OPTIONAL_LOCKS": "1"},
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    assert marker.read_text(encoding="utf-8") == "actual-fsmonitor\n"
    marker.unlink()
    before = _index_identity(repo / ".git/index")
    actual_head, tracked, tree = _git_clean_source_inventory(repo, head[:12])
    assert actual_head == head and tracked == ["infrastructure/witness.py"]
    assert "infrastructure/witness.py" in tree
    assert not marker.exists()
    assert _index_identity(repo / ".git/index") == before
    assert _fixture_git(repo, ["config", "--local", "--get", "core.fsmonitor"]).stdout.strip() == str(hook)


@pytest.mark.parametrize("fault", ["tracked", "untracked", "revision"])
def test_actual_clean_inventory_cohort_refuses_unadmitted_source(tmp_path: Path, fault: str) -> None:
    repo, head = _actual_repository(tmp_path)
    if fault == "untracked":
        (repo / "untracked.txt").write_text("unadmitted\n", encoding="utf-8")
    else:
        (repo / "infrastructure/witness.py").write_text("VALUE = 2\n", encoding="utf-8")
        if fault == "revision":
            _fixture_git(repo, ["add", "-A"])
            _fixture_git(repo, ["-c", "user.name=Test", "-c", "user.email=t@example.com", "commit", "-qm", "next"])
    before = _index_identity(repo / ".git/index")
    refusal = "differs from current HEAD" if fault == "revision" else "requires a clean source working tree"
    with pytest.raises(ValueError, match=refusal):
        _git_clean_source_inventory(repo, head)
    assert _index_identity(repo / ".git/index") == before


def test_actual_destination_cohort_preserves_unrelated_routing_and_configuration(tmp_path: Path) -> None:
    repo, _ = _actual_repository(tmp_path)
    admitted = "https://github.com/example/admitted.git"
    _fixture_git(repo, ["remote", "add", "origin", admitted])
    _fixture_git(repo, ["remote", "add", "unrelated", "https://github.com/example/unrelated.git"])
    before = (repo / ".git/config").read_bytes()
    index_before = _index_identity(repo / ".git/index")
    _validate_git_destination_current(admitted, repo)
    assert (repo / ".git/config").read_bytes() == before
    assert _index_identity(repo / ".git/index") == index_before


@pytest.mark.parametrize("fault", ["insteadOf", "pushInsteadOf", "origin", "additional"])
def test_actual_destination_cohort_refuses_rewrite_and_origin_redirection(tmp_path: Path, fault: str) -> None:
    repo, _ = _actual_repository(tmp_path)
    admitted = "https://github.com/example/admitted.git"
    other = "https://github.com/example/unreviewed.git"
    _fixture_git(repo, ["remote", "add", "origin", admitted])
    if fault in {"insteadOf", "pushInsteadOf"}:
        _fixture_git(repo, ["config", f"url.{other}.{fault}", admitted])
    else:
        if fault == "additional":
            _fixture_git(repo, ["config", "--add", "remote.origin.pushurl", admitted])
        _fixture_git(repo, ["config", "--add", "remote.origin.pushurl", other])
    before = (repo / ".git/config").read_bytes()
    refusal = "Git rewrites" if fault in {"insteadOf", "pushInsteadOf"} else "origin push destination differs"
    with pytest.raises(ValueError, match=refusal):
        _validate_git_destination_current(admitted, repo)
    assert (repo / ".git/config").read_bytes() == before


def test_actual_clean_inventory_cohort_retains_native_git_failure(tmp_path: Path) -> None:
    repo = tmp_path / "empty"
    repo.mkdir()
    _fixture_git(repo, ["init", "-q"])
    with pytest.raises(RuntimeError, match="original native Git return code: 128"):
        _git_clean_source_inventory(repo, "0" * 40)


def _actual_install_provider(tmp_path: Path) -> GitInstallProvider:
    repo, _ = _actual_repository(tmp_path)
    (repo / "pyproject.toml").write_text(
        '[project]\nname = "research-project-template"\nversion = "4.0.2"\n', encoding="utf-8"
    )
    _fixture_git(repo, ["remote", "add", "origin", PROVIDER_URLS[ROOT_PACKAGE]])
    _fixture_git(repo, ["add", "--", "pyproject.toml"])
    _fixture_git(repo, ["-c", "user.name=Test", "-c", "user.email=t@example.com", "commit", "-qm", "provider metadata"])
    return GitInstallProvider(repo, _fixture_git(repo, ["rev-parse", "HEAD"]).stdout.strip())


def test_actual_provider_metadata_cohort_preserves_nul_record_tree_and_custody(tmp_path: Path) -> None:
    parent = tmp_path
    for index in range(4):
        parent /= f"provider {index}-" + "é" * 52
    parent.mkdir(parents=True)
    provider = _actual_install_provider(parent)
    repo, revision = provider.checkout, provider.commit
    assert len(str(repo).encode("utf-8")) > 512
    content = (repo / "pyproject.toml").read_bytes()
    native_metadata = _fixture_git(repo, ["ls-tree", "-z", revision, "--", "pyproject.toml"]).stdout
    native_tree = _fixture_git(repo, ["rev-parse", revision + "^{tree}"]).stdout.strip()
    assert native_metadata.endswith("\tpyproject.toml\0") and native_metadata.count("\0") == 1
    marker = repo / ".git/provider-fsmonitor-invoked"
    hook = repo / ".git/provider-fsmonitor"
    hook.write_text(
        f"#!/bin/sh\nprintf 'actual-fsmonitor\\n' > {shlex.quote(str(marker))}\nprintf 'fixture-token\\000/\\000'\n",
        encoding="utf-8",
    )
    hook.chmod(0o700)
    _fixture_git(repo, ["config", "core.fsmonitor", shlex.quote(str(hook))])
    original = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=repo,
        env={**_git_environment(), "GIT_OPTIONAL_LOCKS": "1"},
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    assert original.stdout == "" and marker.read_text(encoding="utf-8") == "actual-fsmonitor\n"
    marker.unlink()
    before = _index_identity(repo / ".git/index")
    configuration = (repo / ".git/config").read_bytes()
    assert _git_provider_closing_metadata(repo, revision) == (native_metadata, native_tree)
    assert _admit_provider(provider, ROOT_PACKAGE, "4.0.2") == {
        "package": ROOT_PACKAGE,
        "version": "4.0.2",
        "repository": PROVIDER_URLS[ROOT_PACKAGE],
        "commit": revision,
        "tree": native_tree,
        "metadata_sha256": hashlib.sha256(content).hexdigest(),
    }
    assert not marker.exists()
    assert _index_identity(repo / ".git/index") == before
    assert (repo / ".git/config").read_bytes() == configuration


@pytest.mark.parametrize("fault", ["dirty", "moved-head", "hidden-metadata", "missing-metadata", "committed-link"])
def test_actual_provider_metadata_cohort_refuses_changed_native_or_metadata_binding(tmp_path: Path, fault: str) -> None:
    provider = _actual_install_provider(tmp_path)
    repo, supplied = provider.checkout, provider.commit
    metadata = repo / "pyproject.toml"
    content = metadata.read_bytes()
    if fault in {"dirty", "moved-head"}:
        (repo / "infrastructure/witness.py").write_text("VALUE = 2\n", encoding="utf-8")
        if fault == "moved-head":
            _fixture_git(repo, ["add", "-A"])
            _fixture_git(
                repo, ["-c", "user.name=Test", "-c", "user.email=t@example.com", "commit", "-qm", "advance provider"]
            )
            assert _fixture_git(repo, ["rev-parse", "HEAD"]).stdout.strip() != supplied
    elif fault == "hidden-metadata":
        _fixture_git(repo, ["update-index", "--assume-unchanged", "pyproject.toml"])
        metadata.write_bytes(content + b"# hidden uncommitted metadata\n")
    else:
        if fault == "missing-metadata":
            _fixture_git(repo, ["rm", "--cached", "--", "pyproject.toml"])
            with (repo / ".git/info/exclude").open("a", encoding="utf-8") as stream:
                stream.write("\npyproject.toml\n")
        else:
            # Genuine Git supports its committed symlink body as a regular worktree
            # file when core.symlinks=false. Admission still must reject mode120000.
            _fixture_git(repo, ["config", "core.symlinks", "false"])
            blob = _fixture_git(repo, ["rev-parse", supplied + ":pyproject.toml"]).stdout.strip()
            _fixture_git(repo, ["update-index", "--cacheinfo", f"120000,{blob},pyproject.toml"])
        _fixture_git(
            repo, ["-c", "user.name=Test", "-c", "user.email=t@example.com", "commit", "-qm", "commit metadata fault"]
        )
        supplied = _fixture_git(repo, ["rev-parse", "HEAD"]).stdout.strip()
        assert metadata.read_bytes() == content and not metadata.is_symlink()
    if fault != "dirty":
        assert _fixture_git(repo, ["status", "--porcelain", "--untracked-files=all"]).stdout == ""
    before = _index_identity(repo / ".git/index")
    configuration = (repo / ".git/config").read_bytes()
    if fault in {"dirty", "moved-head"}:
        refusal = "clean source working tree" if fault == "dirty" else "differs from current HEAD"
        with pytest.raises(ValueError, match=refusal):
            _git_provider_closing_metadata(repo, supplied)
    else:
        native_metadata = _fixture_git(repo, ["ls-tree", "-z", supplied, "--", "pyproject.toml"]).stdout
        if fault == "missing-metadata":
            assert native_metadata == ""
            refusal = None
        else:
            refusal = (
                "consumed bytes differ" if fault == "hidden-metadata" else "metadata must be a committed regular file"
            )
            if fault == "committed-link":
                assert native_metadata.startswith("120000 blob ") and native_metadata.endswith("\tpyproject.toml\0")
        with pytest.raises(ValueError, match=refusal):
            _admit_provider(GitInstallProvider(repo, supplied), ROOT_PACKAGE, "4.0.2")
    assert _index_identity(repo / ".git/index") == before
    assert (repo / ".git/config").read_bytes() == configuration
