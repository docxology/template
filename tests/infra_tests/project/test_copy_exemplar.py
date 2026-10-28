"""Tests for clean exemplar copy helpers."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.project.copy_exemplar import _contained_destination, copy_exemplar, export_exemplar, plan_copy
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.slow
@pytest.mark.parametrize("project_name", PUBLIC_PROJECT_NAMES)
def test_every_public_exemplar_exports_as_a_standalone_tree(tmp_path: Path, project_name: str) -> None:
    """Every declared exemplar must survive the same clean export contract."""
    destination = tmp_path / project_name.split("/")[-1]

    export_exemplar(REPO_ROOT, project_name, destination)

    manifest = json.loads((destination / ".template-export.json").read_text(encoding="utf-8"))
    assert manifest["source_project"] == project_name
    assert (destination / "README.md").is_file()
    assert (destination / "pyproject.toml").is_file()
    assert not (destination / ".venv").exists()
    assert not (destination / "output").exists()


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _scaffold_git_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    source = root / "projects" / "templates" / "template_code_project"
    source.mkdir(parents=True)
    (source / "README.md").write_text("template_code_project\n", encoding="utf-8")
    (source / "STANDALONE.md").write_text("# Standalone\n", encoding="utf-8")
    (source / "pyproject.toml").write_text("[project]\nname = 'template-code-project'\n", encoding="utf-8")
    (source / "docs").mkdir()
    (source / "docs" / "quickstart.md").write_text(
        "Run `uv run pytest projects/templates/template_code_project/tests/`.\n",
        encoding="utf-8",
    )
    (source / "docs" / "logo.bin").write_bytes(b"\xff\x00template_code_project")
    (source / ".venv").mkdir()
    (source / ".venv" / "ignored.py").write_text("ignored\n", encoding="utf-8")
    (source / "output").mkdir()
    (source / "output" / "artifact.txt").write_text("ignored\n", encoding="utf-8")
    (source / ".DS_Store").write_text("ignored\n", encoding="utf-8")
    _git("init", cwd=root)
    # Set a repo-local identity so the fixture commit works on CI runners that
    # have no global git user configured (e.g. ubuntu-latest). macOS dev hosts
    # usually have a global identity, which is why this only bit in CI.
    _git("config", "user.email", "fixture@example.com", cwd=root)
    _git("config", "user.name", "Fixture", cwd=root)
    _git("add", "projects/templates/template_code_project/README.md", cwd=root)
    _git("add", "projects/templates/template_code_project/STANDALONE.md", cwd=root)
    _git("add", "projects/templates/template_code_project/pyproject.toml", cwd=root)
    _git("add", "projects/templates/template_code_project/docs/quickstart.md", cwd=root)
    _git("add", "projects/templates/template_code_project/docs/logo.bin", cwd=root)
    _git("commit", "-m", "fixture", cwd=root)
    return root


def test_rename_text_preserves_unrelated_tokens() -> None:
    from infrastructure.project.copy_exemplar import _rename_text

    source = (
        "doi:10.5281/zenodo.12345678\n"
        "Discuss template_code_project_extra without renaming the suffix token.\n"
        "Run projects/templates/template_code_project/tests/\n"
        "name = 'template-code-project'\n"
    )
    renamed = _rename_text(
        source,
        "template_code_project",
        "my_project",
        old_project_path="projects/templates/template_code_project",
        new_project_path="projects/working/my_project",
    )
    assert "10.5281/zenodo.12345678" in renamed
    assert "template_code_project_extra" in renamed
    assert "name = 'my-project'" in renamed
    assert "projects/working/my_project" in renamed


def test_dry_run_reports_copy_plan_without_writing_destination(tmp_path: Path) -> None:
    repo_root = _scaffold_git_repo(tmp_path)
    dest = tmp_path / "fork"

    result = plan_copy(repo_root, "templates/template_code_project", dest, new_name="my_project", dry_run=True)

    assert result.dry_run is True
    assert dest.exists() is False
    assert {path.as_posix() for path in result.relative_files} == {
        "README.md",
        "STANDALONE.md",
        "docs/quickstart.md",
        "docs/logo.bin",
        "pyproject.toml",
    }


def test_clean_copy_excludes_local_artifacts_and_preserves_binaries(tmp_path: Path) -> None:
    repo_root = _scaffold_git_repo(tmp_path)
    dest = tmp_path / "fork"

    result = copy_exemplar(repo_root, "templates/template_code_project", dest, new_name="my_project")

    assert result.dry_run is False
    assert (dest / "README.md").read_text(encoding="utf-8") == "my_project\n"
    assert (dest / "STANDALONE.md").is_file()
    assert (dest / "docs" / "logo.bin").read_bytes() == b"\xff\x00template_code_project"
    assert not (dest / ".venv").exists()
    assert not (dest / "output").exists()
    assert not (dest / ".DS_Store").exists()


def test_export_writes_content_addressed_provenance_manifest(tmp_path: Path) -> None:
    repo_root = _scaffold_git_repo(tmp_path)
    dest = tmp_path / "fork"

    export_exemplar(repo_root, "templates/template_code_project", dest, new_name="my_project")

    payload = json.loads((dest / ".template-export.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == 2
    assert payload["source_project"] == "templates/template_code_project"
    assert payload["exported_project"] == "my_project"
    assert payload["source_commit"] != "unknown"
    assert payload["infrastructure_version"] == "unknown"
    assert payload["resource_dependencies"] == []
    readme = dest / "README.md"
    assert payload["files"]["README.md"] == hashlib.sha256(readme.read_bytes()).hexdigest()
    assert ".template-export.json" not in payload["files"]


def test_export_bundles_declared_cross_root_resources(tmp_path: Path) -> None:
    """Declared public pools are copied and included in the manifest hashes."""
    repo_root = _scaffold_git_repo(tmp_path)
    project = repo_root / "projects/templates/template_code_project"
    (project / "export.toml").write_text(
        '[template_export]\ncross_root_dependencies = ["fonds/templates"]\n',
        encoding="utf-8",
    )
    fond = repo_root / "fonds/templates/template_bibliography"
    fond.mkdir(parents=True)
    (fond / "fonds.yaml").write_text("name: bibliography\n", encoding="utf-8")
    dest = tmp_path / "fork"

    export_exemplar(repo_root, "templates/template_code_project", dest)

    resource = dest / "_template_resources/fonds/templates/template_bibliography/fonds.yaml"
    assert resource.read_text(encoding="utf-8") == "name: bibliography\n"
    payload = json.loads((dest / ".template-export.json").read_text(encoding="utf-8"))
    rel = resource.relative_to(dest).as_posix()
    assert payload["resource_dependencies"] == ["fonds/templates"]
    assert payload["files"][rel] == hashlib.sha256(resource.read_bytes()).hexdigest()


def test_export_bundles_declared_infrastructure_dependency(tmp_path: Path) -> None:
    repo_root = _scaffold_git_repo(tmp_path)
    project = repo_root / "projects/templates/template_code_project"
    (project / "export.toml").write_text(
        '[template_export]\ncross_root_dependencies = ["infrastructure"]\n',
        encoding="utf-8",
    )
    module = repo_root / "infrastructure" / "feature.py"
    module.parent.mkdir()
    module.write_text("VALUE = 1\n", encoding="utf-8")
    output_module = repo_root / "infrastructure" / "validation" / "output" / "gate.py"
    output_module.parent.mkdir(parents=True)
    output_module.write_text("VALUE = 2\n", encoding="utf-8")
    dest = tmp_path / "fork"

    export_exemplar(repo_root, "templates/template_code_project", dest)

    bundled = dest / "_template_resources/infrastructure/feature.py"
    assert bundled.read_text(encoding="utf-8") == "VALUE = 1\n"
    assert (dest / "_template_resources/infrastructure/validation/output/gate.py").is_file()
    payload = json.loads((dest / ".template-export.json").read_text(encoding="utf-8"))
    assert payload["resource_dependencies"] == ["infrastructure"]


def test_project_only_export_omits_declared_resources(tmp_path: Path) -> None:
    repo_root = _scaffold_git_repo(tmp_path)
    project = repo_root / "projects/templates/template_code_project"
    (project / "export.toml").write_text(
        '[template_export]\ncross_root_dependencies = ["fonds/templates"]\n',
        encoding="utf-8",
    )
    dest = tmp_path / "fork"

    export_exemplar(repo_root, "templates/template_code_project", dest, project_only=True)

    assert not (dest / "_template_resources").exists()
    payload = json.loads((dest / ".template-export.json").read_text(encoding="utf-8"))
    assert payload["resource_dependencies"] == []


def test_new_name_rewrites_qualified_template_paths_to_destination(tmp_path: Path) -> None:
    repo_root = _scaffold_git_repo(tmp_path)
    dest = repo_root / "projects" / "working" / "my_project"

    copy_exemplar(repo_root, "templates/template_code_project", dest, new_name="my_project")

    quickstart = (dest / "docs" / "quickstart.md").read_text(encoding="utf-8")
    assert "projects/working/my_project/tests/" in quickstart
    assert "projects/templates/my_project" not in quickstart
    assert "projects/templates/template_code_project" not in quickstart


def test_new_name_rewrites_python_and_package_slug_spellings(tmp_path: Path) -> None:
    repo_root = _scaffold_git_repo(tmp_path)
    dest = tmp_path / "fork"

    copy_exemplar(repo_root, "templates/template_code_project", dest, new_name="my_project")

    pyproject = (dest / "pyproject.toml").read_text(encoding="utf-8")
    assert "my-project" in pyproject
    assert "template-code-project" not in pyproject
    assert "template_code_project" not in pyproject


def test_copy_rejects_symlinked_source_files(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    source = repo_root / "projects" / "templates" / "template_code_project"
    source.mkdir(parents=True)
    outside = tmp_path / "private.txt"
    outside.write_text("private\n", encoding="utf-8")
    (source / "README.md").symlink_to(outside)
    dest = tmp_path / "fork"

    with pytest.raises(ValueError, match="refusing to dereference"):
        copy_exemplar(repo_root, "templates/template_code_project", dest, new_name="my_project")


def test_copy_materializes_symlinked_public_exemplar_source(tmp_path: Path) -> None:
    """A tracked public-to-public sharing link exports as regular files."""
    repo_root = _scaffold_git_repo(tmp_path)
    source = repo_root / "projects/templates/template_code_project"
    shared = repo_root / "projects/templates/template_prose_project/src"
    shared.mkdir(parents=True)
    (shared / "shared_logic.py").write_text("VALUE = 7\n", encoding="utf-8")
    (source / "src").mkdir()
    (source / "src/shared").symlink_to("../../template_prose_project/src")
    _git("add", "projects/templates/template_code_project/src/shared", cwd=repo_root)
    _git("add", "projects/templates/template_prose_project/src/shared_logic.py", cwd=repo_root)
    destination = tmp_path / "fork"

    copy_exemplar(repo_root, "templates/template_code_project", destination)

    copied = destination / "src/shared/shared_logic.py"
    assert copied.read_text(encoding="utf-8") == "VALUE = 7\n"
    assert not copied.is_symlink()


def test_fallback_walk_excludes_common_ignored_artifacts(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    source = repo_root / "projects" / "templates" / "template_textbook"
    (source / "src").mkdir(parents=True)
    (source / "src" / "__init__.py").write_text('"""template_textbook."""\n', encoding="utf-8")
    (source / ".pytest_cache").mkdir()
    (source / ".pytest_cache" / "cache").write_text("ignored\n", encoding="utf-8")
    (source / ".lake").mkdir()
    (source / ".lake" / "build").write_text("ignored\n", encoding="utf-8")
    dest = tmp_path / "fork"

    result = copy_exemplar(repo_root, "templates/template_textbook", dest, new_name="my_textbook")

    assert {path.as_posix() for path in result.relative_files} == {"src/__init__.py"}
    assert (dest / "src" / "__init__.py").read_text(encoding="utf-8") == '"""my_textbook."""\n'
    assert not (dest / ".pytest_cache").exists()
    assert not (dest / ".lake").exists()


def test_live_exemplar_copy_keeps_required_forkability_files(tmp_path: Path) -> None:
    dest = tmp_path / "fork"

    result = copy_exemplar(REPO_ROOT, "templates/template_code_project", dest, new_name="copied_code_project")

    assert len(result.relative_files) > 10
    for rel in ("README.md", "AGENTS.md", "STANDALONE.md", "domain_profile.yaml", "experiment_plan.yaml"):
        assert (dest / rel).is_file(), rel
    for rel in ("pyproject.toml", "uv.lock"):
        path = dest / rel
        if path.is_file():
            source_text = (REPO_ROOT / "projects" / "templates" / "template_code_project" / rel).read_text(
                encoding="utf-8"
            )
            text = path.read_text(encoding="utf-8")
            if "template-code-project" in source_text:
                assert "copied-code-project" in text
            if "template_code_project" in source_text:
                assert "copied_code_project" in text
            assert "template-code-project" not in text
            assert "template_code_project" not in text


def test_documented_script_path_runs_from_repo_root(tmp_path: Path) -> None:
    dest = tmp_path / "fork"

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/audit/copy_exemplar.py",
            "--source",
            "templates/template_code_project",
            "--dest",
            str(dest),
            "--dry-run",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Would copy" in proc.stdout
    assert not dest.exists()


def test_live_textbook_copy_excludes_rendered_outputs(tmp_path: Path) -> None:
    dest = tmp_path / "fork"

    result = plan_copy(REPO_ROOT, "templates/template_textbook", dest, new_name="copied_textbook", dry_run=True)

    copied = {path.as_posix() for path in result.relative_files}
    assert copied
    assert not any(path == "rendered" or path.startswith("rendered/") for path in copied)


def test_rejects_non_template_source(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="source must be qualified as templates/"):
        plan_copy(REPO_ROOT, "working/private_project", tmp_path / "fork")


@pytest.mark.parametrize(
    "bad_name", ["../outside", "../../outside", "/tmp/outside", "Uppercase", "has/slash", ".hidden"]
)
def test_rejects_unsafe_new_name_values(tmp_path: Path, bad_name: str) -> None:
    with pytest.raises(ValueError, match="--new-name must be a lowercase project slug"):
        plan_copy(REPO_ROOT, "templates/template_template", tmp_path / "fork", new_name=bad_name, dry_run=True)


def test_containment_guard_rejects_escaping_target(tmp_path: Path) -> None:
    dest = (tmp_path / "fork").resolve()
    with pytest.raises(ValueError, match="copy target would escape destination"):
        _contained_destination(dest, Path("../outside"))


def _scaffold_pinned_resource_repo(tmp_path: Path) -> tuple[Path, Path]:
    """Create actual committed Gitlink custody without network or ambient identity."""
    root = _scaffold_git_repo(tmp_path)
    project = root / "projects/templates/template_code_project"
    (project / "export.toml").write_text('[template_export]\ncross_root_dependencies = ["infrastructure"]\n')
    (root / "pyproject.toml").write_text('[project]\nversion="4.0.1"\n')
    child = root / "infrastructure/steganography/kmyth"
    child.mkdir(parents=True)
    (child / "README.md").write_text("Actual owned pinned resource fixture\n")
    (child / "owned.c").write_text("int owned_value(void) { return 7; }\n")
    (child / ".gitignore").write_text("bin/\nlib/\nobj/\nlogger/obj/\nutils/obj/\n")
    _git("init", cwd=child)
    _git("config", "user.email", "fixture@example.com", cwd=child)
    _git("config", "user.name", "Fixture", cwd=child)
    _git("add", "README.md", "owned.c", ".gitignore", cwd=child)
    _git("commit", "-m", "owned pinned source", cwd=child)
    (root / ".gitmodules").write_text(
        '[submodule "infrastructure/steganography/kmyth"]\n'
        "\tpath = infrastructure/steganography/kmyth\n"
        "\turl = https://github.com/docxology/kmyth.git\n"
    )
    _git("add", ".gitmodules", "infrastructure/steganography/kmyth", cwd=root)
    _git("commit", "-m", "pin actual owned source", cwd=root)
    for relative in ("bin/program", "lib/owned.a", "obj/owned.o", "logger/obj/logger.o", "utils/obj/util.o"):
        artifact = child / relative
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_bytes(b"actual owned local build product")
    authored = root / "infrastructure/validation/output/owned.py"
    authored.parent.mkdir(parents=True)
    authored.write_text("VALUE = 11\n")
    return root, child


def _resource_archive(destination: Path, *, fault: str = "") -> tuple[dict[str, object], bytes]:
    """Bind real exported bytes, including deliberately dishonest closed controls."""
    from io import BytesIO
    import zipfile

    embedded = json.loads((destination / ".template-export.json").read_bytes())
    payloads = {relative: (destination / relative).read_bytes() for relative in embedded["files"]}
    member = "_template_resources/infrastructure/steganography/kmyth/owned.c"
    if fault == "omitted-archive":
        del payloads[member]
    elif fault == "changed-archive":
        payloads[member] = b"int owned_value(void) { return 99; }\n"
    files = {relative: hashlib.sha256(content).hexdigest() for relative, content in payloads.items()}
    embedded["files"] = files
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for relative, content in payloads.items():
            archive.writestr(relative, content)
        archive.writestr(".template-export.json", json.dumps(embedded))
    return {"platform_version": "4.0.1", "source_commit": embedded["source_commit"], "files": files}, buffer.getvalue()


def test_pinned_resource_export_preserves_complete_source_and_independent_archive_admission(tmp_path: Path) -> None:
    from infrastructure.reporting.readiness_receipts import public_resource_source_paths
    from infrastructure.reporting.release_readiness_artifacts import validate_source_archive
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

    root, child = _scaffold_pinned_resource_repo(tmp_path)
    destination = tmp_path / "template_code_project"
    export_exemplar(root, "templates/template_code_project", destination)
    bundled = destination / "_template_resources/infrastructure"
    for name in ("README.md", "owned.c", ".gitignore"):
        assert (bundled / "steganography/kmyth" / name).read_bytes() == (child / name).read_bytes()
    assert (bundled / "validation/output/owned.py").read_text() == "VALUE = 11\n"
    assert not list(bundled.rglob(".git"))
    for relative in ("bin", "lib", "obj", "logger/obj", "utils/obj"):
        assert not (bundled / "steganography/kmyth" / relative).exists()
    expected = {
        path.relative_to(root / "infrastructure") for path in public_resource_source_paths(root, "infrastructure")
    }
    assert {path.relative_to(bundled) for path in bundled.rglob("*") if path.is_file()} == expected
    manifest, content = _resource_archive(destination)
    reader = SnapshotReader(root)
    validate_source_archive("templates/template_code_project", manifest, content, reader)
    assert reader.unchanged()


@pytest.mark.parametrize(
    "fault",
    [
        "modified-source",
        "missing-source",
        "changed-head",
        "changed-index",
        "changed-declaration",
        "unadmitted-source",
        "private-control",
        "omitted-archive",
        "changed-archive",
    ],
)
def test_pinned_resource_export_and_archive_refuse_actual_custody_faults(tmp_path: Path, fault: str) -> None:
    from infrastructure.reporting.release_readiness_artifacts import validate_source_archive
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

    root, child = _scaffold_pinned_resource_repo(tmp_path)
    destination = tmp_path / "template_code_project"
    if fault in {"omitted-archive", "changed-archive"}:
        export_exemplar(root, "templates/template_code_project", destination)
        manifest, content = _resource_archive(destination, fault=fault)
        with pytest.raises(ValueError):
            validate_source_archive("templates/template_code_project", manifest, content, SnapshotReader(root))
        return
    if fault == "private-control":
        private = child / ".env"
        private.write_text("owned marker only; no credential\n")
        opened = []
        active = [True]

        def refuse_private_open(event: str, arguments: tuple[object, ...]) -> None:
            if (
                active[0]
                and event == "open"
                and isinstance(arguments[0], str)
                and Path(arguments[0]) in {private, Path(".env")}
            ):
                opened.append(event)
                raise AssertionError("private control content must not be opened")

        sys.addaudithook(refuse_private_open)
        try:
            with pytest.raises(ValueError, match="private credential/control filename"):
                export_exemplar(root, "templates/template_code_project", destination)
        finally:
            active[0] = False
        assert opened == []
        return
    if fault == "missing-source":
        (child / "owned.c").unlink()
    elif fault in {"modified-source", "changed-head", "changed-index"}:
        (child / "owned.c").write_text("int owned_value(void) { return 8; }\n")
        if fault in {"changed-head", "changed-index"}:
            _git("add", "owned.c", cwd=child)
        if fault == "changed-head":
            _git("commit", "-m", "different actual child commit", cwd=child)
    elif fault == "changed-declaration":
        declaration = root / ".gitmodules"
        declaration.write_bytes(declaration.read_bytes() + b"\n# actual changed declaration\n")
    else:
        (child / "unadmitted.c").write_text("int unadmitted_value(void) { return 9; }\n")
    with pytest.raises(ValueError):
        export_exemplar(root, "templates/template_code_project", destination)


def test_pinned_resource_export_preserves_original_expired_deadline(tmp_path: Path) -> None:
    import time

    root, _ = _scaffold_pinned_resource_repo(tmp_path)
    destination = tmp_path / "template_code_project"
    with pytest.raises(TimeoutError, match="deadline exhausted"):
        export_exemplar(root, "templates/template_code_project", destination, deadline_monotonic=time.monotonic() - 1)
    assert not destination.exists()


def test_fork_sdk_source_url_replaces_the_parent_relative_path(tmp_path: Path) -> None:
    destination = tmp_path / "fork"
    export_exemplar(
        REPO_ROOT,
        "templates/template_code_project",
        destination,
        project_only=True,
        sdk_source="url:https://example.org/template-sdk.git",
    )
    text = (destination / "pyproject.toml").read_text(encoding="utf-8")
    assert 'research-project-template = { url = "https://example.org/template-sdk.git" }' in text
    assert 'path = "../../.."' not in text


def test_fork_sdk_source_version_only_keeps_the_pin_and_drops_the_source(tmp_path: Path) -> None:
    destination = tmp_path / "fork"
    export_exemplar(
        REPO_ROOT,
        "templates/template_code_project",
        destination,
        project_only=True,
        sdk_source="version-only",
    )
    text = (destination / "pyproject.toml").read_text(encoding="utf-8")
    assert '"research-project-template==4.3.0"' in text
    assert "research-project-template = {" not in text


def test_fork_sdk_source_path_accepts_this_checkout(tmp_path: Path) -> None:
    destination = tmp_path / "fork"
    export_exemplar(
        REPO_ROOT,
        "templates/template_code_project",
        destination,
        project_only=True,
        sdk_source=f"path:{REPO_ROOT}",
    )
    text = (destination / "pyproject.toml").read_text(encoding="utf-8")
    assert f'research-project-template = {{ path = "{REPO_ROOT.as_posix()}", editable = true }}' in text


@pytest.mark.parametrize("spec", ["path:/nonexistent-sdk", "path:", "url:", "registry:pypi", "bogus"])
def test_fork_sdk_source_rejects_unusable_specs(tmp_path: Path, spec: str) -> None:
    with pytest.raises(ValueError):
        plan_copy(REPO_ROOT, "templates/template_code_project", tmp_path / "fork", sdk_source=spec)


def test_fork_copy_rewrites_the_relative_sdk_path_for_its_depth() -> None:
    from infrastructure.project.fork_identity import _rewrite_sdk_source

    destination = REPO_ROOT / "projects" / "working" / "deep" / "project"
    source_path = 'research-project-template = { path = "../../..", editable = true }\n'
    rewritten = _rewrite_sdk_source(source_path, destination=destination, repo_root=REPO_ROOT, sdk_source=None)
    assert 'path = "../../../.."' in rewritten


def test_fork_author_rewrite_replaces_identity_and_drops_source_identifiers(tmp_path: Path) -> None:
    destination = tmp_path / "fork"
    export_exemplar(
        REPO_ROOT,
        "templates/template_code_project",
        destination,
        project_only=True,
        author_name="Ada Lovelace",
        author_email="ada@example.org",
    )
    import yaml

    pyproject = (destination / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "Ada Lovelace"' in pyproject and "ada@example.org" in pyproject
    assert "Friedman" not in pyproject
    citation = yaml.safe_load((destination / "CITATION.cff").read_text(encoding="utf-8"))
    assert citation["authors"] == [{"family-names": "Lovelace", "given-names": "Ada", "email": "ada@example.org"}]
    assert "doi" not in citation and "repository-code" not in citation
    assert citation["version"] == "3.0.0"
    zenodo = json.loads((destination / ".zenodo.json").read_text(encoding="utf-8"))
    assert zenodo["creators"] == [{"name": "Lovelace, Ada", "email": "ada@example.org"}]
    assert "related_identifiers" not in zenodo
    codemeta = json.loads((destination / "codemeta.json").read_text(encoding="utf-8"))
    assert codemeta["author"][0]["familyName"] == "Lovelace"
    assert "identifier" not in codemeta and "codeRepository" not in codemeta
    for name in ("CITATION.cff", ".zenodo.json", "codemeta.json"):
        text = (destination / name).read_text(encoding="utf-8")
        assert "Friedman" not in text and "10.5281" not in text, name
