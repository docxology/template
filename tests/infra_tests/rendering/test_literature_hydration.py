"""Real literature entrypoints preserve ownership and validated output lifecycle."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
PROJECTS = ("template_literature_meta_analysis", "template_advanced_literature_review")


@pytest.fixture(scope="module")
def installed_meta_provider(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build/install the real dependency once; entrypoint families require uv-cli."""
    scratch = tmp_path_factory.mktemp("hydration-installed-provider").resolve()
    original = ROOT / "projects/templates/template_literature_meta_analysis"
    source = scratch / "source"
    source.mkdir()
    for name in ("pyproject.toml", "README.md", "LICENSE"):
        shutil.copy2(original / name, source / name)
    shutil.copytree(original / "src", source / "src", ignore=shutil.ignore_patterns("__pycache__", "*.egg-info"))
    wheels = scratch / "wheels"
    wheels.mkdir()

    def run(name: str, command: list[str]) -> None:
        stdout_path, stderr_path = scratch / f"{name}.stdout.log", scratch / f"{name}.stderr.log"
        with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
            result = subprocess.run(
                command,
                cwd=source,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                timeout=90,
                check=False,
            )
        assert result.returncode == 0, (
            f"{name} failed; retained diagnostics: {scratch}\n"
            + stdout_path.read_text()[-2000:]
            + stderr_path.read_text()[-2000:]
        )

    run(
        "build",
        [
            sys.executable,
            "-I",
            "-c",
            "import sys;from setuptools.build_meta import build_wheel;print(build_wheel(sys.argv[1]))",
            str(wheels),
        ],
    )
    artifacts = list(wheels.glob("*.whl"))
    assert len(artifacts) == 1
    uv = shutil.which("uv")
    assert uv is not None, "actual offline dependency installation requires uv"
    site = scratch / "installed-site"
    run(
        "install",
        [
            uv,
            "pip",
            "install",
            "--offline",
            "--no-config",
            "--no-deps",
            "--no-build",
            "--python",
            sys.executable,
            "--target",
            str(site),
            str(artifacts[0]),
        ],
    )
    run(
        "installed-origin",
        [
            sys.executable,
            "-I",
            "-c",
            "import importlib.metadata,sys;from pathlib import Path;"
            "sys.path.insert(0,sys.argv[1]);import template_literature_meta_analysis as provider;"
            "assert Path(provider.__file__).resolve().is_relative_to(Path(sys.argv[1]).resolve());"
            "print(provider.__file__);print(importlib.metadata.version('template-literature-meta-analysis'))",
            str(site),
        ],
    )
    return site


@pytest.fixture(params=PROJECTS)
def project(request: pytest.FixtureRequest, tmp_path: Path) -> Path:
    """Copy real public source into a fresh typed workspace with minimal authored input."""
    name = request.param
    original = ROOT / "projects/templates" / name
    copied = tmp_path / "projects/templates" / name
    (copied / "scripts").mkdir(parents=True)
    for filename in ("_bootstrap.py", "05_inject_variables.py"):
        shutil.copy2(original / "scripts" / filename, copied / "scripts" / filename)
    shutil.copy2(original / "pyproject.toml", copied / "pyproject.toml")
    shutil.copytree(original / "src", copied / "src", ignore=shutil.ignore_patterns("__pycache__", "*.egg-info"))
    (copied / "manuscript").mkdir()
    (copied / "manuscript/01_main.md").write_text("# Actual fixture\n")
    (copied / "manuscript/MANUSCRIPT_STATUS.md").write_text("{{DOCUMENTATION_EXAMPLE}}\n")
    (copied / "manuscript/.env").write_text("PRIVATE_FIXTURE_ONLY=1\n")
    (copied / "manuscript/unrelated.json").write_text("{}\n")
    (copied / "output/data").mkdir(parents=True)
    return copied


def invoke(project: Path, *args: str, provider_site: Path) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ, TEMPLATE_REPO_ROOT=str(ROOT), PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import runpy,sys;sys.path.insert(0,sys.argv.pop(1));"
            "sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name='__main__')",
            str(provider_site),
            str(project / "scripts/05_inject_variables.py"),
            *args,
        ],
        env=environment,
        cwd=project,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def snapshot(root: Path) -> dict[str, bytes | None]:
    return {p.relative_to(root).as_posix(): p.read_bytes() if p.is_file() else None for p in root.rglob("*")}


@pytest.mark.timeout(180)
def test_actual_hydration_dry_run_stale_sections_and_strict_failure_preserve_source(
    project: Path, installed_meta_provider: Path
) -> None:
    source = snapshot(project / "manuscript")
    before = snapshot(project / "output")
    result = invoke(
        project, "--project", f"templates/{project.name}", "--dry-run", provider_site=installed_meta_provider
    )
    assert result.returncode == 0, result.stderr
    assert snapshot(project / "output") == before
    rendered = project / "output/manuscript"
    rendered.mkdir()
    (rendered / "00_deleted_section.md").write_text("# Former generated section\n")
    (rendered / "notes.md").write_text("Unrelated owned notes\n")
    before = snapshot(project / "output")
    for arguments in (("--dry-run",), ()):
        result = invoke(project, "--project", project.name, *arguments, provider_site=installed_meta_provider)
        assert result.returncode != 0 and "unowned rendered manuscript section" in result.stderr
        assert "move it outside output/manuscript" in result.stderr
        assert snapshot(project / "output") == before
    # The owner explicitly retains the unowned bytes outside the render inputs.
    (rendered / "00_deleted_section.md").rename(project / "output/retained_deleted_section.md")
    result = invoke(project, "--project", project.name, provider_site=installed_meta_provider)
    assert result.returncode == 0, result.stderr
    assert (project / "output/retained_deleted_section.md").read_text() == "# Former generated section\n"
    assert not (rendered / "MANUSCRIPT_STATUS.md").exists()
    assert not (rendered / ".env").exists()
    assert not (rendered / "unrelated.json").exists()
    assert (rendered / "notes.md").read_text() == "Unrelated owned notes\n"
    assert (rendered / "01_main.md").read_text() == "# Actual fixture\n"
    assert snapshot(project / "manuscript") == source
    # Manifest-owned sections disappear only when the exact generated bytes remain.
    (project / "manuscript/02_removed.md").write_text("# Remove on subsequent regeneration\n")
    assert invoke(project, provider_site=installed_meta_provider).returncode == 0
    (project / "manuscript/02_removed.md").unlink()
    assert invoke(project, provider_site=installed_meta_provider).returncode == 0
    assert not (rendered / "02_removed.md").exists()
    before = snapshot(project / "output")
    # A later section fails after the first source has rendered. No prepared file
    # or stale section may mutate the last successful artifact tree.
    (project / "manuscript/99_invalid.md").write_text("{{UNKNOWN_REQUIRED_METRIC}}\n")
    result = invoke(project, provider_site=installed_meta_provider)
    assert result.returncode != 0 and "Unresolved variables" in result.stderr
    assert snapshot(project / "output") == before


@pytest.mark.parametrize("selection", ["other", "lifecycle", "traversal", "absolute", "sidecar"])
@pytest.mark.timeout(180)
def test_actual_project_context_refuses_other_owner_before_writing(
    project: Path, selection: str, installed_meta_provider: Path
) -> None:
    if selection == "sidecar":
        from infrastructure.rendering.manuscript_injection import validate_project_selection

        owner = project.parents[2] / "external/working/owner"
        owner.mkdir(parents=True)
        assert validate_project_selection(owner, "working/owner") == owner
        assert validate_project_selection(owner, "owner") == owner
        with pytest.raises(ValueError, match="only supports"):
            validate_project_selection(owner, "archive/owner")
        return
    supplied = {
        "other": "templates/template_code_project",
        "lifecycle": f"archive/{project.name}",
        "traversal": f"templates/../templates/{project.name}",
        "absolute": str(project),
    }[selection]
    before = snapshot(project / "output")
    result = invoke(project, "--project", supplied, provider_site=installed_meta_provider)
    assert result.returncode != 0 and "only supports" in result.stderr
    assert snapshot(project / "output") == before


@pytest.mark.parametrize("link", ["output", "destination", "member", "source", "sdk_source", "sdk_scripts"])
@pytest.mark.timeout(180)
def test_actual_hydration_refuses_source_and_destination_links(
    project: Path, tmp_path: Path, link: str, installed_meta_provider: Path
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "01_main.md").write_text("Original external bytes\n")
    output = project / "output"
    rendered = output / "manuscript"
    if link == "output":
        shutil.rmtree(output)
        output.symlink_to(outside, target_is_directory=True)
    elif link == "destination":
        rendered.symlink_to(outside, target_is_directory=True)
    elif link == "member":
        rendered.mkdir()
        (rendered / "01_main.md").symlink_to(outside / "01_main.md")
    elif link in {"sdk_source", "sdk_scripts"}:
        directory = project / ("src" if link == "sdk_source" else "scripts")
        (directory / "infrastructure.py").write_text(
            "from pathlib import Path\n"
            + f"Path({str(outside / 'poison-executed')!r}).write_text('counterfeit SDK executed')\n"
            + "raise RuntimeError('project DATA must not provide the SDK')\n"
        )
    else:
        (project / "manuscript/01_main.md").unlink()
        (project / "manuscript/01_main.md").symlink_to(outside / "01_main.md")
    before = snapshot(outside)
    result = invoke(project, provider_site=installed_meta_provider)
    if link in {"sdk_source", "sdk_scripts"}:
        assert result.returncode == 0, result.stdout + result.stderr
    else:
        assert result.returncode != 0, result.stdout + result.stderr
        assert "link" in result.stderr.lower()
    assert snapshot(outside) == before


@pytest.mark.parametrize("fault", ["changed", "traversal", "unrelated", "hidden", "extra", "notes", "unrelated_bib"])
def test_manifest_cannot_remove_edited_or_unrelated_output(tmp_path: Path, fault: str) -> None:
    import json

    from infrastructure.rendering.manuscript_injection import hydrate_manuscript_tree, stale_hydration_paths

    project = tmp_path / "owner"
    source = project / "manuscript"
    source.mkdir(parents=True)
    section = source / "01_main.md"
    section.write_text("Original source\n")
    hydrate_manuscript_tree(project, lambda _name, content: content)
    output = project / "output/manuscript"
    manifest_path = output / "hydration_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if fault == "changed":
        section.unlink()
        (output / "01_main.md").write_text("Concurrent human edit\n")
    elif fault == "extra":
        manifest["extra"] = True
        manifest_path.write_text(json.dumps(manifest))
    else:
        name = {
            "traversal": "../outside.md",
            "unrelated": "private.txt",
            "hidden": ".env",
            "notes": "notes.md",
            "unrelated_bib": "human_notes.bib",
        }[fault]
        if fault in {"notes", "unrelated_bib"}:
            import hashlib

            content = b"Human-owned material\n"
            (output / name).write_bytes(content)
            manifest["files"][name] = hashlib.sha256(content).hexdigest()
        else:
            manifest["files"][name] = "a" * 64
        manifest_path.write_text(json.dumps(manifest))
    before = snapshot(output)
    with pytest.raises(ValueError, match="edited|manifest"):
        stale_hydration_paths(project)
    assert snapshot(output) == before
    with pytest.raises(ValueError, match="edited|manifest"):
        hydrate_manuscript_tree(project, lambda _name, content: content)
    assert snapshot(output) == before


def test_large_unicode_ownership_manifest_roundtrips_real_files(tmp_path: Path) -> None:
    from infrastructure.rendering.manuscript_injection import hydrate_manuscript_tree, stale_hydration_paths

    project = tmp_path / "owner"
    source = project / "manuscript"
    source.mkdir(parents=True)
    # Valid Unicode filenames fit the filesystem's per-component byte bound;
    # JSON escaping makes their complete manifest exceed the former 128 KiB.
    for index in range(300):
        (source / (f"{index % 100:02d}_" + "章" * 75 + f"{index:03d}.md")).write_text("Authored source\n")
    hydrate_manuscript_tree(project, lambda _name, content: content)
    output = project / "output/manuscript"
    assert 128 * 1024 < (output / "hydration_manifest.json").stat().st_size < 512 * 1024
    before = snapshot(output)
    assert stale_hydration_paths(project) == ()
    assert snapshot(output) == before
    hydrate_manuscript_tree(project, lambda _name, content: content)
    assert snapshot(output) == before


def test_late_actual_stale_edit_survives_after_prepared_write(tmp_path: Path) -> None:
    from infrastructure.core.files.secure_write import atomic_write_bytes_confined
    from infrastructure.rendering.manuscript_injection import hydrate_manuscript_tree, stale_hydration_paths

    project = tmp_path / "owner"
    source = project / "manuscript"
    source.mkdir(parents=True)
    (source / "01_main.md").write_text("Authored source\n")
    (source / "02_deleted.md").write_text("Previously generated\n")
    hydrate_manuscript_tree(project, lambda _name, content: content)
    (source / "02_deleted.md").unlink()
    stale = project / "output/manuscript/02_deleted.md"
    assert stale_hydration_paths(project) == (stale,)
    observed = []

    def after_actual_write(frame, event, _arg):
        # Observe the genuine confined writer's completed first file. Perform
        # a real late filesystem edit; no function/provider is replaced.
        if (
            event == "return"
            and frame.f_code is atomic_write_bytes_confined.__code__
            and frame.f_locals["target"].name == "01_main.md"
        ):
            stale.write_text("Late human edit\n")
            observed.append(True)

    previous_profile = sys.getprofile()
    sys.setprofile(after_actual_write)
    try:
        with pytest.raises(ValueError, match="changed before removal"):
            hydrate_manuscript_tree(project, lambda _name, content: content)
    finally:
        sys.setprofile(previous_profile)
    assert observed == [True]
    assert stale.read_text() == "Late human edit\n"


@pytest.mark.parametrize("with_manifest", [False, True])
def test_unowned_numbered_render_input_is_preserved_and_refused(tmp_path: Path, with_manifest: bool) -> None:
    from infrastructure.rendering.manuscript_discovery import discover_manuscript_files
    from infrastructure.rendering.manuscript_injection import hydrate_manuscript_tree, stale_hydration_paths

    project = tmp_path / "owner"
    source = project / "manuscript"
    source.mkdir(parents=True)
    (source / "01_main.md").write_text("Current source\n")
    output = project / "output/manuscript"
    output.mkdir(parents=True)
    if with_manifest:
        hydrate_manuscript_tree(project, lambda _name, content: content)
    unowned = output / "7_old_section.MD"
    unowned.write_text("Unowned former content\n")
    assert unowned in discover_manuscript_files(output)
    before = snapshot(project)
    with pytest.raises(ValueError, match="unowned rendered manuscript section"):
        stale_hydration_paths(project)
    assert snapshot(project) == before
    for dry_run in (True, False):
        with pytest.raises(ValueError, match="unowned rendered manuscript section"):
            hydrate_manuscript_tree(project, lambda _name, content: content, dry_run=dry_run)
        assert snapshot(project) == before


@pytest.mark.parametrize("claimed", [False, True])
def test_actual_enabled_renderer_bookends_remain_owned_by_the_render_stage(tmp_path: Path, claimed: bool) -> None:
    import hashlib
    import json

    from infrastructure.rendering._manuscript_source import resolve_manuscript_dir
    from infrastructure.rendering.manuscript_injection import hydrate_manuscript_tree, stale_hydration_paths
    from infrastructure.transmission.transmission_bookends import write_transmission_bookends
    from tests.infra_tests.publishing.test_transmission_bookends import _write_project

    project = tmp_path / "owner"
    _write_project(project, enabled=True)
    generated = write_transmission_bookends(project, project.name, repo_root=tmp_path)
    assert generated is not None
    originals = {path: path.read_bytes() for path in generated}
    hydrate_manuscript_tree(project, lambda _name, content: content)
    manifest = json.loads((project / "output/manuscript/hydration_manifest.json").read_text())
    assert all(path.name not in manifest["files"] for path in generated)
    assert all(path.read_bytes() == content for path, content in originals.items())
    output = project / "output/manuscript"
    assert resolve_manuscript_dir(project) == output
    if claimed:
        # Even exact prior-byte bindings cannot transfer these enabled reserved
        # filenames from their real render-stage owner to the hydration receipt.
        manifest["files"].update(
            {path.name: hashlib.sha256(content).hexdigest() for path, content in originals.items()}
        )
        (output / "hydration_manifest.json").write_text(json.dumps(manifest))
    before = snapshot(output)
    assert stale_hydration_paths(project) == ()
    assert snapshot(output) == before
    hydrate_manuscript_tree(project, lambda _name, content: content)
    assert all(path.read_bytes() == content for path, content in originals.items())
    manifest = json.loads((output / "hydration_manifest.json").read_text())
    assert all(path.name not in manifest["files"] for path in generated)
    # Disabled bookends have no current renderer owner; preserve and refuse them.
    config = project / "manuscript/config.yaml"
    config.write_text(config.read_text().replace("enabled: true", "enabled: false"))
    before = snapshot(project / "output")
    with pytest.raises(ValueError, match="unowned rendered manuscript section"):
        stale_hydration_paths(project)
    assert snapshot(project / "output") == before
    with pytest.raises(ValueError, match="unowned rendered manuscript section"):
        hydrate_manuscript_tree(project, lambda _name, content: content)
    assert snapshot(project / "output") == before


@pytest.mark.parametrize(
    "name,body",
    [
        ("01_main.md", "Evidence at /Users/alice/research/result.json\n"),
        ("config.yaml", "paper:\n  title: Portable\n# asset: /home/alice/research/cover.png\n"),
        ("preamble.md", "```latex\n% Source: /Users/alice/research/preamble.tex\n```\n"),
    ],
)
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_portability_normalization_precedes_hydration_ownership_hashes(
    tmp_path: Path,
    name: str,
    body: str,
    newline: str,
) -> None:
    import hashlib
    import json

    from infrastructure.core.files.portability import sanitize_machine_local_paths
    from infrastructure.rendering._manuscript_source import resolve_manuscript_dir
    from infrastructure.rendering.manuscript_injection import hydrate_manuscript_tree, stale_hydration_paths

    project = tmp_path / "owner"
    source = project / "manuscript"
    source.mkdir(parents=True)
    (source / "99_keep.md").write_bytes(b"# Retained Source\n")
    (source / name).write_bytes(body.replace("\n", newline).encode("utf-8"))
    authored = snapshot(source)
    assert hydrate_manuscript_tree(project, lambda _name, text: text) == (1, 0)
    output = project / "output/manuscript"
    content = (output / name).read_bytes()
    assert b"<home>/research/" in content
    assert snapshot(source) == authored
    manifest = json.loads((output / "hydration_manifest.json").read_text())
    before = snapshot(output)
    assert resolve_manuscript_dir(project) == output
    assert snapshot(output) == before
    assert snapshot(source) == authored
    assert all(
        digest == hashlib.sha256((output / member).read_bytes()).hexdigest()
        for member, digest in manifest["files"].items()
    )
    assert sanitize_machine_local_paths(output) == ()
    assert stale_hydration_paths(project) == ()
    assert snapshot(output) == before
    (source / name).unlink()
    assert stale_hydration_paths(project) == (output / name,)
    assert snapshot(output) == before
    assert hydrate_manuscript_tree(project, lambda _name, text: text, dry_run=True) == (0, 0)
    assert snapshot(output) == before
    assert hydrate_manuscript_tree(project, lambda _name, text: text) == (0, 0)
    assert not (output / name).exists()
    remaining = json.loads((output / "hydration_manifest.json").read_text())["files"]
    assert remaining == {"99_keep.md": hashlib.sha256((output / "99_keep.md").read_bytes()).hexdigest()}
    assert stale_hydration_paths(project) == ()


def test_stale_hydration_paths_do_not_create_output_without_prior_ownership(tmp_path: Path) -> None:
    from infrastructure.rendering.manuscript_injection import hydrate_manuscript_tree, stale_hydration_paths

    project = tmp_path / "owner"
    source = project / "manuscript"
    source.mkdir(parents=True)
    (source / "01_main.md").write_text("Authored Source\n")
    (source / "README.md").write_text("Documentation only\n")
    (source / "notes.md").write_text("Unadmitted notes\n")
    before = snapshot(project)
    assert stale_hydration_paths(project) == ()
    assert hydrate_manuscript_tree(project, lambda _name, text: text, dry_run=True) == (0, 0)
    assert snapshot(project) == before
    assert not (project / "output").exists()


def test_stale_hydration_paths_match_actual_writer_membership(tmp_path: Path) -> None:
    from infrastructure.rendering._manuscript_source import resolve_manuscript_dir
    from infrastructure.rendering.manuscript_injection import hydrate_manuscript_tree, stale_hydration_paths

    project = tmp_path / "owner"
    source = project / "manuscript"
    source.mkdir(parents=True)
    for name, content in {
        "01_main.md": "# Current Source\n",
        "02_deleted.md": "# Former Source\n",
        "03_already_missing.md": "# Already missing output\n",
        "config.yaml": "paper:\n  title: Authored\n",
        "preamble.md": "```latex\n% Authored preamble\n```\n",
        "references.bib": "@book{source,title={Source}}\n",
    }.items():
        (source / name).write_text(content)
    hydrate_manuscript_tree(project, lambda _name, text: text)
    output = project / "output/manuscript"
    assert resolve_manuscript_dir(project) == output
    stale_names = ("02_deleted.md", "config.yaml", "preamble.md", "references.bib")
    for name in (*stale_names, "03_already_missing.md"):
        (source / name).unlink()
    (output / "03_already_missing.md").unlink()
    # A directory with an admitted filename is not admitted file Source.
    (source / "02_deleted.md").mkdir()
    unowned = {"notes.md": b"Human notes\n", "human_notes.bib": b"Human bibliography\n", "private.txt": b"Private\n"}
    for name, content in unowned.items():
        (output / name).write_bytes(content)
    before = snapshot(project)
    expected = tuple(output / name for name in stale_names)
    assert stale_hydration_paths(project) == expected
    assert snapshot(project) == before
    hydrate_manuscript_tree(project, lambda _name, text: text, dry_run=True)
    assert snapshot(project) == before
    hydrate_manuscript_tree(project, lambda _name, text: text)
    assert all(not path.exists() for path in expected)
    assert (output / "01_main.md").read_bytes() == (source / "01_main.md").read_bytes()
    assert all((output / name).read_bytes() == content for name, content in unowned.items())
    assert stale_hydration_paths(project) == ()


@pytest.mark.parametrize("link", ["project", "source", "output", "destination", "member", "manifest"])
def test_stale_hydration_paths_refuse_linked_authority_without_writes(tmp_path: Path, link: str) -> None:
    from infrastructure.rendering.manuscript_injection import hydrate_manuscript_tree, stale_hydration_paths

    project = tmp_path / "owner"
    source = project / "manuscript"
    source.mkdir(parents=True)
    (source / "01_main.md").write_text("# Current Source\n")
    (source / "02_deleted.md").write_text("# Former Source\n")
    hydrate_manuscript_tree(project, lambda _name, text: text)
    (source / "02_deleted.md").unlink()
    output = project / "output/manuscript"
    target = {
        "project": project,
        "source": source,
        "output": project / "output",
        "destination": output,
        "member": output / "02_deleted.md",
        "manifest": output / "hydration_manifest.json",
    }[link]
    retained = tmp_path / "retained"
    target.rename(retained)
    target.symlink_to(retained, target_is_directory=retained.is_dir())
    before = snapshot(tmp_path)
    with pytest.raises(ValueError, match="linked|regular"):
        stale_hydration_paths(project)
    assert snapshot(tmp_path) == before


def test_prior_stale_plan_cannot_remove_restored_current_source(tmp_path: Path) -> None:
    from infrastructure.rendering.manuscript_injection import hydrate_manuscript_tree, stale_hydration_paths

    project = tmp_path / "owner"
    source = project / "manuscript"
    source.mkdir(parents=True)
    (source / "01_main.md").write_text("# Current Source\n")
    restored = source / "02_restored.md"
    restored.write_text("# Former Source\n")
    hydrate_manuscript_tree(project, lambda _name, text: text)
    restored.unlink()
    output = project / "output/manuscript"
    planned = stale_hydration_paths(project)
    assert planned == (output / restored.name,)
    restored.write_text("# Restored current Source\n")
    hydrate_manuscript_tree(project, lambda _name, text: text)
    assert planned[0].read_bytes() == restored.read_bytes()
    assert stale_hydration_paths(project) == ()


@pytest.mark.parametrize("operation", ["plan", "write"])
def test_stale_membership_rechecks_source_before_return_or_write(tmp_path: Path, operation: str) -> None:
    from infrastructure.core.files.secure_write import read_bytes_confined
    from infrastructure.rendering.manuscript_injection import hydrate_manuscript_tree, stale_hydration_paths

    project = tmp_path / "owner"
    source = project / "manuscript"
    source.mkdir(parents=True)
    current = source / "01_main.md"
    current.write_text("# Current Source\n")
    (source / "02_deleted.md").write_text("# Former Source\n")
    hydrate_manuscript_tree(project, lambda _name, text: text)
    (source / "02_deleted.md").unlink()
    output = project / "output/manuscript"
    stale = output / "02_deleted.md"
    before = snapshot(output)
    observed = []

    def after_stale_read(frame, event, _arg):
        if event == "return" and frame.f_code is read_bytes_confined.__code__ and frame.f_locals["target"] == stale:
            # Edit real Source after the actual stale-byte validation; neither
            # the confined reader nor the owner being exercised is replaced.
            current.write_text("# Late Source edit\n")
            observed.append(True)

    previous_profile = sys.getprofile()
    sys.setprofile(after_stale_read)
    try:
        with pytest.raises(ValueError, match="source changed during hydration"):
            if operation == "plan":
                stale_hydration_paths(project)
            else:
                hydrate_manuscript_tree(project, lambda _name, text: text)
    finally:
        sys.setprofile(previous_profile)
    assert observed == [True]
    assert current.read_text() == "# Late Source edit\n"
    assert snapshot(output) == before


@pytest.mark.parametrize("home", ["/home/", "/Users/"])
@pytest.mark.parametrize("dry_run", [False, True])
def test_hydration_rejects_raw_config_tokens_before_home_normalization(
    tmp_path: Path,
    home: str,
    dry_run: bool,
) -> None:
    from infrastructure.rendering.manuscript_injection import hydrate_manuscript_tree

    project = tmp_path / "owner"
    source = project / "manuscript"
    source.mkdir(parents=True)
    (source / "01_main.md").write_text("# Existing scientific evidence\n", encoding="utf-8")
    config = source / "config.yaml"
    config.write_text('paper:\n  title: "Resolved"\n', encoding="utf-8")
    hydrate_manuscript_tree(project, lambda _name, text: text)
    before = snapshot(project / "output")
    content = f'paper:\n  title: "{home}{{{{MISSING}}}}"\n'
    config.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match="MISSING"):
        hydrate_manuscript_tree(project, lambda _name, text: text, dry_run=dry_run)

    assert config.read_text(encoding="utf-8") == content
    assert snapshot(project / "output") == before
