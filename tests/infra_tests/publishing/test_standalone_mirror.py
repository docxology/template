"""Tests for standalone-mirror syncing.

Two properties carry real consequences and are pinned in both directions:

1. **Update-only.** The mirror holds published artifacts the monorepo does not
   track (exemplar ``output/`` is gitignored in the monorepo but published in the
   mirror). A replace-style sync would have deleted 224 such files from
   ``template_advanced_literature_review`` alone on 2026-07-28.
2. **Symlinks are dereferenced.** Exemplars that share source by symlinking into
   a sibling must arrive self-contained; copying the link leaves it dangling,
   which is why one mirror was missing four whole source trees.

Real git repositories and real files under ``tmp_path`` — no mocks.
"""

from __future__ import annotations

import os
import json
import shutil
import subprocess
import sys

import pytest
from pathlib import Path

from infrastructure.publishing.standalone_mirror import (
    _git as _mirror_git,
    declared_repository,
    populate_mirror_tree,
    tracked_relative_paths,
    clean_source_revision,
    sync_exemplar,
    validate_git_destination,
)
from infrastructure.publishing.publication_tree import PublicationTarget, update_publication_tree
from infrastructure.project.copy_exemplar import export_exemplar
from infrastructure.fonds.public_scope import PUBLIC_FOND_NAMES
from infrastructure.rules.public_scope import PUBLIC_RULE_NAMES
from infrastructure.tools.public_scope import PUBLIC_TOOL_NAMES


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def _monorepo(tmp_path: Path) -> Path:
    root = tmp_path / "monorepo"
    project = root / "projects" / "templates" / "template_code_project"
    (project / "src").mkdir(parents=True)
    (project / "output" / "data").mkdir(parents=True)
    (project / "src" / "core.py").write_text("VALUE = 1\n", encoding="utf-8")
    (project / "README.md").write_text("# Demo\n", encoding="utf-8")
    (project / "CITATION.cff").write_text(
        "cff-version: 1.2.0\ntitle: Demo\nrepository-code: https://github.com/example/template_code_project\n",
        encoding="utf-8",
    )
    # Gitignored build output: present on disk, never tracked.
    (root / ".gitignore").write_text("projects/templates/*/output/*\n", encoding="utf-8")
    (project / "output" / "data" / "local_only.json").write_text("{}\n", encoding="utf-8")

    _git(["init", "-q"], root)
    _git(["config", "user.email", "t@example.com"], root)
    _git(["config", "user.name", "Test"], root)
    _git(["add", "-A"], root)
    _git(["commit", "-qm", "init"], root)
    return root.resolve()


def test_tracked_paths_exclude_gitignored_output(tmp_path: Path) -> None:
    root = _monorepo(tmp_path)
    paths = tracked_relative_paths(root, "projects/templates/template_code_project")
    assert "src/core.py" in paths
    assert "README.md" in paths
    assert not any(path.startswith("output/") for path in paths), "gitignored output must never be mirrored"


def test_declared_repository_reads_citation_cff(tmp_path: Path) -> None:
    root = _monorepo(tmp_path)
    project = root / "projects" / "templates" / "template_code_project"
    assert declared_repository(project) == "https://github.com/example/template_code_project"
    assert declared_repository(tmp_path / "absent") == ""


def test_sync_is_update_only_and_preserves_mirror_only_files(tmp_path: Path) -> None:
    """The behaviour that protects published artifacts.

    A mirror-only file (a published output artifact the monorepo does not track)
    must survive a sync. This is the control for the failure mode that would have
    deleted 224 real artifacts.
    """
    root = _monorepo(tmp_path)
    mirror = tmp_path / "mirror"
    (mirror / "output" / "pdf").mkdir(parents=True)
    published = mirror / "output" / "pdf" / "published_paper.pdf"
    published.write_bytes(b"%PDF-1.7 published artifact\n")
    (mirror / "README.md").write_text("# stale\n", encoding="utf-8")

    populate_mirror_tree(root, "projects/templates/template_code_project", mirror)

    assert published.is_file(), "a published mirror-only artifact must not be deleted"
    assert published.read_bytes() == b"%PDF-1.7 published artifact\n"
    assert (mirror / "README.md").read_text(encoding="utf-8") == "# Demo\n", "tracked files must be updated"
    assert (mirror / "src" / "core.py").is_file()


def test_directory_symlinks_are_dereferenced_into_real_files(tmp_path: Path) -> None:
    """A standalone mirror has no sibling to resolve a cross-project symlink."""
    root = _monorepo(tmp_path)
    templates = root / "projects" / "templates"
    sibling = templates / "template_literature_meta_analysis" / "src" / "analysis"
    sibling.mkdir(parents=True)
    (sibling / "engine.py").write_text("SHARED = True\n", encoding="utf-8")

    link = templates / "template_code_project" / "src" / "analysis"
    link.symlink_to(Path("../../template_literature_meta_analysis/src/analysis"))
    _git(["add", "-A"], root)
    _git(["commit", "-qm", "add shared symlink"], root)

    mirror = tmp_path / "mirror2"
    mirror.mkdir()
    populate_mirror_tree(root, "projects/templates/template_code_project", mirror)

    mirrored = mirror / "src" / "analysis" / "engine.py"
    assert mirrored.is_file(), "symlinked source tree must be materialized in the mirror"
    assert not mirrored.is_symlink(), "the mirror must not contain a dangling link"
    assert mirrored.read_text(encoding="utf-8") == "SHARED = True\n"


def test_populate_reports_files_written(tmp_path: Path) -> None:
    root = _monorepo(tmp_path)
    mirror = tmp_path / "mirror3"
    mirror.mkdir()
    written = populate_mirror_tree(root, "projects/templates/template_code_project", mirror)
    assert written == len(tracked_relative_paths(root, "projects/templates/template_code_project")) + 1
    assert written > 0
    assert json.loads((mirror / ".template-export.json").read_text())["source_commit"] == "unknown"


def _pools_monorepo(tmp_path: Path) -> Path:
    """Use the real public resource roster and complete declared sibling contract."""
    root = _monorepo(tmp_path)
    project = root / "projects/templates/template_pools_rules_tools"
    (project / "src").mkdir(parents=True)
    (project / "src/analysis.py").write_text("PUBLIC_POOLS = True\n")
    (project / "README.md").write_text("# Public pools fixture\n")
    (project / "pyproject.toml").write_text('[project]\nname="template-pools-rules-tools"\nversion="2.0.0"\n')
    (project / "CITATION.cff").write_text(
        "cff-version: 1.2.0\nrepository-code: https://github.com/example/template_pools_rules_tools\n"
    )
    (project / "export.toml").write_text(
        '[template_export]\ncross_root_dependencies=["fonds/templates","rules/templates","tools/templates"]\n'
    )
    (root / "pyproject.toml").write_text('[project]\nname="research-project-template"\nversion="4.0.1"\n')
    for kind, names in (("fonds", PUBLIC_FOND_NAMES), ("rules", PUBLIC_RULE_NAMES), ("tools", PUBLIC_TOOL_NAMES)):
        for name in names:
            resource = root / kind / name / "data/public.txt"
            resource.parent.mkdir(parents=True)
            resource.write_text(f"invented public resource {kind}/{name}\n")
    # Clean canonical exports exclude even a tracked generated artifact.
    generated = project / "output/data/old-run.json"
    generated.parent.mkdir(parents=True)
    generated.write_text('{"generated":true}\n')
    _git(["add", "-A"], root)
    _git(["add", "-f", str(generated.relative_to(root))], root)
    _git(["commit", "-qm", "declare complete public resource pools"], root)
    return root


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(root).parts
    }


def test_bound_pools_export_matches_complete_canonical_export(tmp_path: Path) -> None:
    root = _pools_monorepo(tmp_path)
    revision = clean_source_revision(root)
    expected = tmp_path / "canonical/template_pools_rules_tools"
    export_exemplar(root, "templates/template_pools_rules_tools", expected)
    mirror = tmp_path / "mirror/template_pools_rules_tools"
    mirror.mkdir(parents=True)
    count = populate_mirror_tree(
        root, "projects/templates/template_pools_rules_tools", mirror, source_revision=revision
    )
    assert _tree_bytes(mirror) == _tree_bytes(expected)
    assert count == len(_tree_bytes(expected))
    assert "output/data/old-run.json" not in _tree_bytes(mirror)
    metadata = json.loads((mirror / ".template-export.json").read_text())
    assert metadata["source_commit"] == revision
    assert metadata["infrastructure_version"] == "4.0.1"
    assert metadata["resource_dependencies"] == ["fonds/templates", "rules/templates", "tools/templates"]
    assert len([name for name in metadata["files"] if name.startswith("_template_resources/")]) == 9


def test_bound_infrastructure_dependency_keeps_layer_one_output_source(tmp_path: Path) -> None:
    root = _monorepo(tmp_path)
    project = root / "projects/templates/template_code_project"
    (project / "export.toml").write_text('[template_export]\ncross_root_dependencies=["infrastructure"]\n')
    (root / "pyproject.toml").write_text('[project]\nversion="4.0.1"\n')
    helper = root / "infrastructure/output/helpers.py"
    helper.parent.mkdir(parents=True)
    helper.write_text("SOURCE_IMPLEMENTATION = True\n")
    _git(["add", "-A"], root)
    _git(["commit", "-qm", "declare Layer-1 implementation dependency"], root)
    expected = tmp_path / "canonical/template_code_project"
    export_exemplar(root, "templates/template_code_project", expected)
    mirror = tmp_path / "mirror/template_code_project"
    mirror.mkdir(parents=True)
    populate_mirror_tree(
        root, "projects/templates/template_code_project", mirror, source_revision=clean_source_revision(root)
    )
    assert _tree_bytes(mirror) == _tree_bytes(expected)
    assert (mirror / "_template_resources/infrastructure/output/helpers.py").read_text() == helper.read_text()


@pytest.mark.parametrize("fault", ["omitted", "tampered", "mode"])
def test_bound_pools_export_refuses_hidden_changed_sibling(tmp_path: Path, fault: str) -> None:
    root = _pools_monorepo(tmp_path)
    revision = clean_source_revision(root)
    relative = "tools/templates/template_code_executor/data/public.txt"
    _git(["update-index", "--assume-unchanged", relative], root)
    source = root / relative
    if fault == "omitted":
        source.unlink()
    elif fault == "tampered":
        source.write_text("invented concurrent public change\n")
    else:
        source.chmod(0o755)
    assert clean_source_revision(root, revision) == revision
    mirror = tmp_path / "mirror"
    mirror.mkdir()
    with pytest.raises((FileNotFoundError, ValueError)):
        populate_mirror_tree(root, "projects/templates/template_pools_rules_tools", mirror, source_revision=revision)
    assert not tuple(mirror.iterdir()), "failed admission must not write a partial destination"


def test_bound_export_refuses_hidden_platform_metadata_change(tmp_path: Path) -> None:
    root = _pools_monorepo(tmp_path)
    revision = clean_source_revision(root)
    _git(["update-index", "--assume-unchanged", "pyproject.toml"], root)
    (root / "pyproject.toml").write_text('[project]\nversion="99.0.0"\n')
    assert clean_source_revision(root, revision) == revision
    mirror = tmp_path / "mirror"
    mirror.mkdir()
    with pytest.raises(ValueError, match="admitted source commit"):
        populate_mirror_tree(root, "projects/templates/template_pools_rules_tools", mirror, source_revision=revision)
    assert not tuple(mirror.iterdir())


@pytest.mark.parametrize("fault", ["root-link", "unknown", "private-link"])
def test_pools_export_refuses_nonpublic_resource_provider(tmp_path: Path, fault: str) -> None:
    root = _pools_monorepo(tmp_path)
    outside = tmp_path / "invented-private-resource"
    outside.mkdir()
    (outside / "secret.txt").write_text("invented private fixture\n")
    if fault == "root-link":
        shutil.rmtree(root / "tools/templates")
        (root / "tools/templates").symlink_to(outside, target_is_directory=True)
    elif fault == "unknown":
        unknown = root / "tools/templates/unknown/secret.txt"
        unknown.parent.mkdir()
        unknown.write_text("invented unadmitted fixture\n")
    else:
        source = root / "tools/templates/template_code_executor/data/public.txt"
        source.unlink()
        source.symlink_to(outside / "secret.txt")
    _git(["add", "-A"], root)
    _git(["commit", "-qm", "admit invalid resource fixture"], root)
    mirror = tmp_path / "mirror"
    mirror.mkdir()
    with pytest.raises((FileNotFoundError, ValueError), match="public|confined|resource"):
        populate_mirror_tree(
            root, "projects/templates/template_pools_rules_tools", mirror, source_revision=clean_source_revision(root)
        )
    assert not tuple(mirror.iterdir())


@pytest.mark.parametrize("provider", ["external", "working", "unknown", "untracked"])
def test_mirror_refuses_nonpublic_file_providers(tmp_path: Path, provider: str) -> None:
    root = _monorepo(tmp_path)
    project = root / "projects/templates/template_code_project"
    targets = {
        "external": tmp_path / "private.txt",
        "working": root / "projects/working/private/src/secret.py",
        "unknown": root / "projects/templates/unknown/src/secret.py",
        "untracked": root / "projects/templates/template_literature_meta_analysis/src/untracked.py",
    }
    source = targets[provider]
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("invented private fixture bytes\n")
    (project / "src/provider.py").symlink_to(source)
    _git(["add", "projects/templates/template_code_project/src/provider.py"], root)
    if provider in {"working", "unknown"}:
        _git(["add", "-f", str(source.relative_to(root))], root)
    mirror = (tmp_path / "mirror").resolve()
    mirror.mkdir()
    with pytest.raises(ValueError, match="public|tracked"):
        populate_mirror_tree(root, "projects/templates/template_code_project", mirror)
    assert not (mirror / "src/provider.py").exists()


def test_mirror_refuses_private_directory_provider(tmp_path: Path) -> None:
    root = _monorepo(tmp_path)
    provider = root / "projects/working/private/src"
    provider.mkdir(parents=True)
    (provider / "secret.py").write_text("invented bytes\n")
    project = root / "projects/templates/template_code_project"
    (project / "src/provider").symlink_to(provider, target_is_directory=True)
    _git(["add", "-f", str(provider.relative_to(root)), "projects/templates/template_code_project/src/provider"], root)
    mirror = tmp_path / "mirror"
    mirror.mkdir()
    with pytest.raises(ValueError, match="public rosters"):
        populate_mirror_tree(root, "projects/templates/template_code_project", mirror)
    assert not (mirror / "src/provider").exists()


def test_mirror_materializes_public_resource_provider_and_spaced_paths(tmp_path: Path) -> None:
    root = _monorepo(tmp_path)
    provider = root / "tools/templates/template_code_executor/src"
    provider.mkdir(parents=True)
    script = provider / "run tool.py"
    script.write_text("print('public resource')\n")
    script.chmod(0o755)
    project = root / "projects/templates/template_code_project"
    (project / "src/tool.py").symlink_to(script)
    (project / "src/spaced file.py").write_text("PUBLIC = True\n")
    _git(["add", "-A"], root)
    mirror = tmp_path / "mirror"
    mirror.mkdir()
    populate_mirror_tree(root, "projects/templates/template_code_project", mirror)
    assert (mirror / "src/tool.py").read_text() == script.read_text()
    assert not (mirror / "src/tool.py").is_symlink()
    assert (mirror / "src/tool.py").stat().st_mode & 0o111
    assert (mirror / "src/spaced file.py").read_text() == "PUBLIC = True\n"


@pytest.mark.parametrize("relative", ["README.md", "src"])
def test_mirror_refuses_destination_symlinks(tmp_path: Path, relative: str) -> None:
    root = _monorepo(tmp_path)
    mirror = tmp_path / "mirror"
    mirror.mkdir()
    outside = tmp_path / "outside"
    if relative == "src":
        outside.mkdir()
        (outside / "core.py").write_text("PRESERVED = True\n")
    else:
        outside.write_text("PRESERVED\n")
    (mirror / relative).symlink_to(outside)
    with pytest.raises(ValueError, match="symlink"):
        populate_mirror_tree(root, "projects/templates/template_code_project", mirror)
    preserved = outside / "core.py" if relative == "src" else outside
    assert "PRESERVED" in preserved.read_text()


def test_mirror_refuses_tracked_fifo_without_waiting(tmp_path: Path) -> None:
    root = _monorepo(tmp_path)
    source = root / "projects/templates/template_code_project/src/core.py"
    source.unlink()
    os.mkfifo(source)
    mirror = tmp_path / "mirror"
    mirror.mkdir()
    with pytest.raises(ValueError, match="regular file"):
        populate_mirror_tree(root, "projects/templates/template_code_project", mirror)


@pytest.mark.parametrize("project_rel", ["projects/working/private", "projects/templates/unknown", "../outside"])
def test_mirror_refuses_unadmitted_project(tmp_path: Path, project_rel: str) -> None:
    root = _monorepo(tmp_path)
    with pytest.raises(ValueError, match="canonical public"):
        tracked_relative_paths(root, project_rel)


def test_repository_citation_link_cannot_read_private_bytes(tmp_path: Path) -> None:
    root = _monorepo(tmp_path)
    project = root / "projects/templates/template_code_project"
    outside = tmp_path / "private-citation"
    outside.write_text("repository-code: https://github.com/private/fixture\n")
    (project / "CITATION.cff").unlink()
    (project / "CITATION.cff").symlink_to(outside)
    with pytest.raises((OSError, ValueError)):
        declared_repository(project)


@pytest.mark.parametrize(
    "url", ["https://user:invented@github.com/example/repo", "file:///private", "https://github.com.evil/example/repo"]
)
def test_repository_citation_rejects_noncanonical_urls(tmp_path: Path, url: str) -> None:
    root = _monorepo(tmp_path)
    project = root / "projects/templates/template_code_project"
    (project / "CITATION.cff").write_text(f"repository-code: {url}\n")
    with pytest.raises(ValueError, match="credential-free"):
        declared_repository(project)


def test_mirror_git_ignores_inherited_repository_and_index(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _monorepo(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    _git(["init", "-q"], outside)
    _git(["config", "user.name", "Test"], outside)
    _git(["config", "user.email", "test@example.com"], outside)
    (outside / "private.txt").write_text("invented private fixture\n")
    _git(["add", "-A"], outside)
    _git(["commit", "-qm", "initial"], outside)
    outside_head = (outside / ".git/HEAD").read_bytes()
    outside_ref = (outside / ".git" / outside_head.decode().strip().removeprefix("ref: ")).read_bytes()
    outside_index = (outside / ".git/index").read_bytes()
    pollution = {
        "GIT_DIR": str(outside / ".git"),
        "GIT_WORK_TREE": str(outside),
        "GIT_COMMON_DIR": str(outside / ".git"),
        "GIT_INDEX_FILE": str(outside / ".git/index"),
        "GIT_OBJECT_DIRECTORY": str(outside / ".git/objects"),
        "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(outside / ".git/objects"),
        "GIT_CEILING_DIRECTORIES": str(tmp_path),
        "GIT_DISCOVERY_ACROSS_FILESYSTEM": "1",
    }
    for name, value in pollution.items():
        monkeypatch.setenv(name, value)
    (root / "projects/templates/template_code_project/src/core.py").write_text("VALUE = 2\n")
    before = _mirror_git(["rev-parse", "HEAD"], root).stdout
    _mirror_git(["add", "-A"], root)
    _mirror_git(["commit", "-qm", "reviewed mirror update"], root)
    assert _mirror_git(["rev-parse", "HEAD"], root).stdout != before
    assert (outside / ".git/HEAD").read_bytes() == outside_head
    assert (outside / ".git" / outside_head.decode().strip().removeprefix("ref: ")).read_bytes() == outside_ref
    assert (outside / ".git/index").read_bytes() == outside_index


@pytest.mark.parametrize("selector", ["GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM"])
def test_mirror_git_refuses_inherited_configuration_worktree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, selector: str
) -> None:
    root = _monorepo(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    _git(["init", "-q"], outside)
    _git(["config", "user.name", "Test"], outside)
    _git(["config", "user.email", "test@example.com"], outside)
    (outside / "private-record.txt").write_text("invented private fixture\n")
    private_core = outside / "projects/templates/template_code_project/src/core.py"
    private_core.parent.mkdir(parents=True)
    private_core.write_text("invented private fixture bytes at colliding path\n")
    _git(["add", "-A"], outside)
    _git(["commit", "-qm", "initial"], outside)
    outside_head = (outside / ".git/HEAD").read_bytes()
    ref_path = outside / ".git" / outside_head.decode().strip().removeprefix("ref: ")
    outside_ref, outside_index = ref_path.read_bytes(), (outside / ".git/index").read_bytes()
    chosen_config = tmp_path / "chosen-config"
    chosen_config.write_text(f"[core]\n\tworktree = {outside}\n")
    monkeypatch.setenv(selector, str(chosen_config))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "0")
    (root / "projects/templates/template_code_project/src/core.py").write_text("VALUE = 2\n")
    _mirror_git(["add", "-A"], root)
    _mirror_git(["commit", "-qm", "reviewed change"], root)
    assert (
        _mirror_git(["show", "HEAD:projects/templates/template_code_project/src/core.py"], root).stdout == "VALUE = 2\n"
    )
    assert "private-record.txt" not in _mirror_git(["ls-tree", "-r", "--name-only", "HEAD"], root).stdout
    assert (outside / ".git/HEAD").read_bytes() == outside_head
    assert ref_path.read_bytes() == outside_ref
    assert (outside / ".git/index").read_bytes() == outside_index


def test_mirror_git_ignores_inherited_helper_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _monorepo(tmp_path)
    selected_helpers = tmp_path / "selected-helpers"
    selected_helpers.mkdir()
    monkeypatch.setenv("GIT_EXEC_PATH", str(selected_helpers))
    actual = _mirror_git(["--exec-path"], root).stdout.strip()
    assert Path(actual).is_dir()
    assert Path(actual) != selected_helpers


def test_bound_export_rejects_assume_unchanged_dirty_provider_bytes(tmp_path: Path) -> None:
    root = _monorepo(tmp_path)
    revision = clean_source_revision(root)
    relative = "projects/templates/template_code_project/src/core.py"
    _git(["update-index", "--assume-unchanged", relative], root)
    (root / relative).write_text("VALUE = 'hidden dirty bytes'\n")
    assert clean_source_revision(root, revision) == revision
    mirror = tmp_path / "bound"
    mirror.mkdir()
    with pytest.raises(ValueError, match="admitted source commit"):
        populate_mirror_tree(root, "projects/templates/template_code_project", mirror, source_revision=revision)
    assert not (mirror / "src/core.py").exists()
    # Explicitly unbound local drafting remains possible and makes no commit claim.
    local = tmp_path / "local-unbound"
    local.mkdir()
    populate_mirror_tree(root, "projects/templates/template_code_project", local)
    assert (local / "src/core.py").read_text() == "VALUE = 'hidden dirty bytes'\n"


@pytest.mark.parametrize("fault", ["old-revision", "dirty-source", "invented-revision"])
def test_sync_admission_rejects_source_identity_before_clone(tmp_path: Path, fault: str) -> None:
    root = _monorepo(tmp_path)
    revision = clean_source_revision(root)
    if fault == "old-revision":
        _git(["commit", "--allow-empty", "-qm", "new actual HEAD"], root)
    elif fault == "dirty-source":
        (root / "projects/templates/template_code_project/README.md").write_text("dirty source\n")
    else:
        revision = "unverified-public-label"
    with pytest.raises(ValueError, match="revision|clean source"):
        sync_exemplar(root, "template_code_project", commit=True, source_revision=revision)


def _owned_transport(
    tmp_path: Path, root: Path, *, mutation: str = "", exemplar: str = "template_code_project"
) -> tuple[Path, dict[str, str], str]:
    """Only route an invented public URL to an owned bare repo; execute real Git."""
    bare = tmp_path / "remote.git"
    _git(["init", "--bare", str(bare)], tmp_path)
    _git(["symbolic-ref", "HEAD", "refs/heads/main"], bare)
    seed = tmp_path / "seed"
    seed.mkdir()
    project_rel = f"projects/templates/{exemplar}"
    repository = f"https://github.com/example/{exemplar}"
    populate_mirror_tree(root, project_rel, seed)
    exported = tmp_path / "seed-export"
    exported.mkdir()
    populate_mirror_tree(root, project_rel, exported)
    target = PublicationTarget(repository, "main")
    update_publication_tree(exported, seed, target)
    _git(["init", "-b", "main"], seed)
    _git(["config", "user.name", "Public fixture"], seed)
    _git(["config", "user.email", "fixture@example.com"], seed)
    _git(["add", "-A"], seed)
    _git(["commit", "-qm", "original managed export"], seed)
    _git(["remote", "add", "origin", str(bare)], seed)
    _git(["push", "-q", "origin", "main"], seed)
    original = subprocess.run(
        ["git", "rev-parse", "refs/heads/main"], cwd=bare, check=True, capture_output=True, text=True, timeout=20
    ).stdout.strip()
    other = tmp_path / "unreviewed.git"
    if mutation == "pushurl":
        _git(["clone", "--bare", str(bare), str(other)], tmp_path)
    native = shutil.which("git")
    assert native is not None
    tools = tmp_path / "owned-transport"
    tools.mkdir()
    shim = tools / "git"
    shim.write_text(
        f"#!{sys.executable}\n"
        "import os,pathlib,subprocess,sys\n"
        f"native={native!r}\nroot=pathlib.Path({str(root)!r})\n"
        f"remote={str(bare)!r}\nmutation={mutation!r}\nadmitted={repository + '.git'!r}\n"
        'transport=any(command in sys.argv[1:] for command in ("clone","push"))\n'
        "args=[remote if transport and value==admitted else value for value in sys.argv[1:]]\n"
        "if 'clone' in args and admitted in sys.argv[1:]:\n"
        "    completed=subprocess.run([native,*args],check=False,timeout=20)\n"
        "    if completed.returncode==0:\n"
        "        subprocess.run([native,'remote','set-url','origin',admitted],cwd=args[-1],check=True,timeout=20)\n"
        "    raise SystemExit(completed.returncode)\n"
        "if 'commit' in args and pathlib.Path.cwd()!=root and mutation:\n"
        "    completed=subprocess.run([native,*args],check=False,timeout=20)\n"
        "    if completed.returncode==0:\n"
        f"        pathlib.Path({str(tools / 'actual-mirror-commit')!r}).write_text('real Git commit completed\\n')\n"
        "        if mutation=='hidden-provider':\n"
        "            relative='projects/templates/template_code_project/src/core.py'\n"
        "            subprocess.run([native,'update-index','--assume-unchanged',relative],cwd=root,check=True,timeout=20)\n"
        "            (root/relative).write_text('ACTUAL_CHILD_DIRTY_PROVIDER = True\\n')\n"
        "        elif mutation in {'sibling-tampered','sibling-omitted'}:\n"
        "            relative='tools/templates/template_code_executor/data/public.txt'\n"
        "            subprocess.run([native,'update-index','--assume-unchanged',relative],cwd=root,check=True,timeout=20)\n"
        "            if mutation=='sibling-omitted': (root/relative).unlink()\n"
        "            else: (root/relative).write_text('ACTUAL_CHILD_CHANGED_SIBLING\\n')\n"
        "        elif mutation=='head':\n"
        "            subprocess.run([native,'commit','--allow-empty','-qm','actual concurrent source HEAD'],cwd=root,check=True,timeout=20)\n"
        "        elif mutation=='destination':\n"
        "            pathlib.Path('concurrent-record').write_text('ACTUAL_CHILD_ADDITION\\n')\n"
        "        elif mutation=='pushurl':\n"
        f"            subprocess.run([native,'config','remote.origin.pushurl',{str(other)!r}],check=True,timeout=20)\n"
        "    raise SystemExit(completed.returncode)\n"
        "os.execv(native,[native,*args])\n"
    )
    shim.chmod(0o755)
    env = dict(os.environ)
    env["PATH"] = str(tools) + os.pathsep + env.get("PATH", "")
    env.update(
        GIT_AUTHOR_NAME="Public fixture",
        GIT_AUTHOR_EMAIL="fixture@example.com",
        GIT_COMMITTER_NAME="Public fixture",
        GIT_COMMITTER_EMAIL="fixture@example.com",
    )
    return bare, env, original


def _install_actual_cli(root: Path) -> Path:
    implementation = Path(__file__).resolve().parents[3]
    script = root / "scripts/publish/sync_standalone_mirrors.py"
    script.parent.mkdir(parents=True)
    shutil.copyfile(implementation / "scripts/publish/sync_standalone_mirrors.py", script)
    shutil.copyfile(implementation / "pyproject.toml", root / "pyproject.toml")
    (root / "infrastructure").symlink_to(implementation / "infrastructure", target_is_directory=True)
    _git(["add", "-A"], root)
    _git(["commit", "-qm", "actual CLI and metadata authority"], root)
    return script


def test_actual_commit_cli_blocks_unreviewed_removal_with_plan_and_remote_unchanged(tmp_path: Path) -> None:
    root = _monorepo(tmp_path)
    script = _install_actual_cli(root)
    bare, env, original = _owned_transport(tmp_path, root)
    _git(["rm", "projects/templates/template_code_project/src/core.py"], root)
    _git(["commit", "-qm", "retire prior managed source"], root)
    actual = subprocess.run(
        [sys.executable, str(script), "--project", "template_code_project", "--commit"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )
    assert actual.returncode == 1, actual.stdout + actual.stderr
    assert "REVIEW REQUIRED: stale managed files" in actual.stdout
    assert "removal-plan-sha256:" in actual.stdout
    marker = "  removal-plan-sha256: "
    remainder = actual.stdout.split(marker, 1)[1]
    expected_hash, serialized_plan = remainder.split("\n", 1)
    plan, _ = json.JSONDecoder().raw_decode(serialized_plan.lstrip())
    from infrastructure.publishing.publication_tree import review_plan_sha256

    assert review_plan_sha256(plan) == expected_hash.strip()
    assert "src/core.py" in plan["removals"]
    assert plan["destination"]["repository"] == "https://github.com/example/template_code_project"
    assert str(bare) not in json.dumps(plan)
    assert (
        subprocess.run(
            ["git", "rev-parse", "refs/heads/main"], cwd=bare, check=True, capture_output=True, text=True, timeout=20
        ).stdout.strip()
        == original
    )


@pytest.mark.parametrize("mutation", ["hidden-provider", "head", "destination", "pushurl"])
def test_actual_post_commit_source_or_destination_change_refuses_push(tmp_path: Path, mutation: str) -> None:
    root = _monorepo(tmp_path)
    script = _install_actual_cli(root)
    bare, env, original = _owned_transport(tmp_path, root, mutation=mutation)
    (root / "projects/templates/template_code_project/README.md").write_text("new committed public source\n")
    _git(["add", "-A"], root)
    _git(["commit", "-qm", "admit changed public source"], root)
    actual = subprocess.run(
        [sys.executable, str(script), "--project", "template_code_project", "--commit"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )
    assert actual.returncode != 0, actual.stdout + actual.stderr
    assert (tmp_path / "owned-transport/actual-mirror-commit").read_text() == "real Git commit completed\n"
    assert (
        subprocess.run(
            ["git", "rev-parse", "refs/heads/main"], cwd=bare, check=True, capture_output=True, text=True, timeout=20
        ).stdout.strip()
        == original
    )
    if mutation == "pushurl":
        assert "origin push destination differs" in actual.stderr
        assert (
            subprocess.run(
                ["git", "rev-parse", "refs/heads/main"],
                cwd=tmp_path / "unreviewed.git",
                check=True,
                capture_output=True,
                text=True,
                timeout=20,
            ).stdout.strip()
            == original
        )


def test_actual_commit_cli_binds_retrieved_managed_bytes_to_full_source_head(tmp_path: Path) -> None:
    root = _monorepo(tmp_path)
    script = _install_actual_cli(root)
    bare, env, original = _owned_transport(tmp_path, root)
    (root / "projects/templates/template_code_project/README.md").write_text("new admitted source bytes\n")
    _git(["add", "-A"], root)
    _git(["commit", "-qm", "admitted source change"], root)
    revision = clean_source_revision(root)
    actual = subprocess.run(
        [sys.executable, str(script), "--project", "template_code_project", "--commit"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )
    assert actual.returncode == 0, actual.stdout + actual.stderr
    assert "SYNCED" in actual.stdout
    retrieved = subprocess.run(
        ["git", "show", "refs/heads/main:README.md"], cwd=bare, check=True, capture_output=True, text=True, timeout=20
    ).stdout
    assert retrieved == "new admitted source bytes\n"
    message = subprocess.run(
        ["git", "log", "-1", "--format=%B", "refs/heads/main"],
        cwd=bare,
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    ).stdout
    assert f"Source: {revision}\n" in message and "Export-SHA256:" in message
    _git(["merge-base", "--is-ancestor", original, "refs/heads/main"], bare)


def test_actual_pools_mirror_transfers_and_retrieves_complete_canonical_export(tmp_path: Path) -> None:
    root = _pools_monorepo(tmp_path)
    script = _install_actual_cli(root)
    bare, env, original = _owned_transport(tmp_path, root, exemplar="template_pools_rules_tools")
    project = root / "projects/templates/template_pools_rules_tools"
    (project / "README.md").write_text("# Current public pools fixture\n")
    _git(["add", "-A"], root)
    _git(["commit", "-qm", "current public pools source"], root)
    revision = clean_source_revision(root)
    expected = tmp_path / "canonical/template_pools_rules_tools"
    export_exemplar(root, "templates/template_pools_rules_tools", expected)
    actual = subprocess.run(
        [sys.executable, str(script), "--project", "template_pools_rules_tools", "--commit"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )
    assert actual.returncode == 0, actual.stdout + actual.stderr
    assert "SYNCED" in actual.stdout
    retrieved = tmp_path / "retrieved"
    _git(["clone", "--quiet", str(bare), str(retrieved)], tmp_path)
    current = _tree_bytes(retrieved)
    current.pop(".template-publication-tree.json")
    assert current == _tree_bytes(expected)
    remote_revision = subprocess.run(
        ["git", "rev-parse", "refs/heads/main"], cwd=bare, check=True, capture_output=True, text=True, timeout=20
    ).stdout.strip()
    assert remote_revision != revision
    _git(["merge-base", "--is-ancestor", original, remote_revision], bare)
    metadata = json.loads(current[".template-export.json"])
    assert metadata["source_commit"] == revision
    assert metadata["resource_dependencies"] == ["fonds/templates", "rules/templates", "tools/templates"]


@pytest.mark.parametrize("mutation", ["sibling-tampered", "sibling-omitted"])
def test_actual_post_commit_sibling_change_refuses_pools_push(tmp_path: Path, mutation: str) -> None:
    root = _pools_monorepo(tmp_path)
    script = _install_actual_cli(root)
    bare, env, original = _owned_transport(tmp_path, root, exemplar="template_pools_rules_tools", mutation=mutation)
    (root / "projects/templates/template_pools_rules_tools/README.md").write_text("# Current public pools\n")
    _git(["add", "-A"], root)
    _git(["commit", "-qm", "admit current public pools"], root)
    actual = subprocess.run(
        [sys.executable, str(script), "--project", "template_pools_rules_tools", "--commit"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )
    assert actual.returncode != 0, actual.stdout + actual.stderr
    assert (tmp_path / "owned-transport/actual-mirror-commit").read_text() == "real Git commit completed\n"
    assert (
        subprocess.run(
            ["git", "rev-parse", "refs/heads/main"], cwd=bare, check=True, capture_output=True, text=True, timeout=20
        ).stdout.strip()
        == original
    )


@pytest.mark.parametrize("setting", ["insteadOf", "pushInsteadOf"])
def test_actual_global_git_url_rewriting_refuses_destination_before_clone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, setting: str
) -> None:
    root = _monorepo(tmp_path)
    other = tmp_path / "unreviewed.git"
    _git(["init", "--bare", str(other)], tmp_path)
    configured = tmp_path / "isolated-global/git"
    configured.mkdir(parents=True)
    config = configured / "config"
    _git(
        [
            "config",
            "--file",
            str(config),
            f"url.{other}.{setting}",
            "https://github.com/example/template_code_project.git",
        ],
        root,
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(configured.parent))
    with pytest.raises(ValueError, match="Git rewrites the admitted publication destination"):
        sync_exemplar(root, "template_code_project", commit=True, source_revision=clean_source_revision(root))
    assert not tuple((other / "refs/heads").iterdir())


@pytest.mark.parametrize("require_origin", [False, True])
def test_actual_destination_resolution_preserves_configuration_and_unrelated_remotes(
    tmp_path: Path, require_origin: bool
) -> None:
    root = _monorepo(tmp_path)
    admitted = "https://github.com/example/template_code_project.git"
    _git(["remote", "add", "origin", admitted], root)
    _git(["remote", "add", "unrelated", "https://github.com/example/unrelated.git"], root)
    configuration = (root / ".git/config").read_bytes()
    inventory = _mirror_git(["remote", "-v"], root).stdout
    validate_git_destination(admitted, lambda args: _mirror_git(args, root), require_origin=require_origin)
    assert (root / ".git/config").read_bytes() == configuration
    assert _mirror_git(["remote", "-v"], root).stdout == inventory


@pytest.mark.parametrize("setting", ["insteadOf", "pushInsteadOf"])
def test_actual_local_url_rewriting_refuses_destination_without_configuration_mutation(
    tmp_path: Path, setting: str
) -> None:
    root = _monorepo(tmp_path)
    admitted = "https://github.com/example/template_code_project.git"
    _git(["config", f"url.https://github.com/example/unreviewed.git.{setting}", admitted], root)
    configuration = (root / ".git/config").read_bytes()
    with pytest.raises(ValueError, match="Git rewrites the admitted publication destination"):
        validate_git_destination(admitted, lambda args: _mirror_git(args, root), require_origin=False)
    assert (root / ".git/config").read_bytes() == configuration


@pytest.mark.parametrize("additional", [False, True], ids=["redirected", "additional"])
def test_actual_origin_push_destinations_remain_required(tmp_path: Path, additional: bool) -> None:
    root = _monorepo(tmp_path)
    admitted = "https://github.com/example/template_code_project.git"
    _git(["remote", "add", "origin", admitted], root)
    if additional:
        _git(["config", "--add", "remote.origin.pushurl", admitted], root)
    _git(["config", "--add", "remote.origin.pushurl", "https://github.com/example/unreviewed.git"], root)
    configuration = (root / ".git/config").read_bytes()
    # Direct URL admission before cloning is independent of an unrelated origin.
    validate_git_destination(admitted, lambda args: _mirror_git(args, root), require_origin=False)
    with pytest.raises(ValueError, match="origin push destination differs"):
        validate_git_destination(admitted, lambda args: _mirror_git(args, root))
    assert (root / ".git/config").read_bytes() == configuration
