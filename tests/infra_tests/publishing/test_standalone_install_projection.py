"""Real committed public fixtures prove opt-in projection custody, without transfers."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

from infrastructure.publishing.publication_tree import publication_export_sha256
from infrastructure.publishing.standalone_install_lock import META_PACKAGE, PROVIDER_URLS, ROOT_PACKAGE
from infrastructure.publishing.standalone_install_projection import (
    PROJECTION_NAME,
    PROJECTION_SCHEMA,
    GitInstallProvider,
    project_standalone_installation,
    validate_standalone_installation,
)
from infrastructure.publishing._standalone_mirror_verify import _assert_source_current
from infrastructure.publishing.standalone_mirror import (
    _git as publication_git,
    populate_mirror_tree,
    sync_exemplar,
)


def _git(root: Path, *args: str) -> str:
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(
        GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1", GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0"
    )
    return subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", *args],
        cwd=root,
        env=environment,
        text=True,
        capture_output=True,
        timeout=20,
        check=True,
    ).stdout.strip()


def _commit(root: Path, origin: str) -> str:
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "Public fixture")
    _git(root, "config", "user.email", "fixture@example.invalid")
    _git(root, "remote", "add", "origin", origin)
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "Commit invented public source fixture")
    return _git(root, "rev-parse", "HEAD")


def _project(root: Path, slug: str, *, with_root: bool = True, with_meta: bool = False) -> Path:
    project = root / "projects/templates" / slug
    (project / "src").mkdir(parents=True)
    (project / "src/science.py").write_text("RESULT = 7\n")
    (project / "src/science.py").chmod(0o755)
    (project / "manuscript").mkdir()
    (project / "manuscript/01_results.md").write_text("# Invented public numerical fixture\nResult: seven.\n")
    (project / "README.md").write_text("# Invented public fixture\n")
    (project / "CITATION.cff").write_text(f"repository-code: https://github.com/docxology/{slug}\n")
    own = slug.replace("_", "-")
    providers = ([ROOT_PACKAGE] if with_root else []) + ([META_PACKAGE] if with_meta else [])
    versions = {ROOT_PACKAGE: "4.0.1", META_PACKAGE: "0.2.0"}
    paths = {ROOT_PACKAGE: "../../..", META_PACKAGE: "../template_literature_meta_analysis"}
    dependencies = [f"{name}=={versions[name]}" for name in providers]
    metadata = f'[project]\nname = "{own}"\nversion = "0.2.0"\nrequires-python = ">=3.12"\n'
    metadata += f"dependencies = {json.dumps(dependencies)}\n"
    metadata += (
        '\n[build-system]\nrequires = ["setuptools"]\nbuild-backend = "setuptools.build_meta"\n'
        f'\n[tool.setuptools]\npackages = ["{slug}"]\n'
        f'\n[tool.setuptools.package-dir]\n{slug} = "src"\n'
    )
    if providers:
        metadata += "\n[tool.uv.sources]\n"
        metadata += "".join(f'{name} = {{ path = "{paths[name]}", editable = true }}\n' for name in providers)
    (project / "pyproject.toml").write_text(metadata)
    lock = 'version = 1\nrevision = 3\nrequires-python = ">=3.12"\n\n'
    for name in providers:
        lock += f'[[package]]\nname = "{name}"\nversion = "{versions[name]}"\n'
        lock += f'source = {{ editable = "{paths[name]}/" }}\n\n'
    lock += f'[[package]]\nname = "{own}"\nversion = "0.2.0"\nsource = {{ virtual = "." }}\n'
    lock += "dependencies = [\n" + "".join(f'    {{ name = "{name}" }},\n' for name in providers) + "]\n"
    lock += "[package.metadata]\nrequires-dist = [\n"
    lock += "".join(f'    {{ name = "{name}", editable = "{paths[name]}" }},\n' for name in providers)
    lock += "]\n\n"
    lock += '[[package]]\nname = "unchanged-scientific-fixture"\nversion = "1.0.0"\n'
    lock += 'source = { registry = "https://pypi.org/simple" }\n\n'
    (project / "uv.lock").write_text(lock)
    return project


def _tree_signature(root: Path) -> tuple:
    records = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if ".git" in relative.parts:
            continue
        metadata = path.lstat()
        assert not path.is_symlink()
        if stat.S_ISREG(metadata.st_mode):
            records.append(
                (relative.as_posix(), hashlib.sha256(path.read_bytes()).hexdigest(), stat.S_IMODE(metadata.st_mode))
            )
        else:
            assert stat.S_ISDIR(metadata.st_mode)
    return tuple(records)


def _provider_signature(provider: GitInstallProvider) -> tuple:
    root = provider.checkout
    assert root == root.resolve(strict=True) and (root / ".git").is_dir()
    assert _git(root, "rev-parse", "HEAD") == provider.commit
    assert _git(root, "status", "--porcelain", "--untracked-files=all") == ""
    return (
        _tree_signature(root),
        _git(root, "ls-files", "--stage", "-z"),
        _git(root, "ls-files", "-v", "-z"),
        (root / ".git/config").read_bytes(),
        (root / ".git/index").read_bytes(),
    )


def _assert_baseline(baseline: tuple) -> None:
    root, meta, original, root_signature, meta_signature, original_signature = baseline
    assert _provider_signature(root) == root_signature
    assert _provider_signature(meta) == meta_signature
    assert _tree_signature(original) == original_signature


def _clone_provider(provider: GitInstallProvider, destination: Path, package: str) -> GitInstallProvider:
    before = _provider_signature(provider)
    _git(
        destination.parent, "clone", "--quiet", "--no-local", "--no-hardlinks", str(provider.checkout), str(destination)
    )
    assert (destination / ".git").is_dir()
    assert not (destination / ".git/objects/info/alternates").exists()
    assert not tuple((destination / ".git").glob("sharedindex.*"))
    _git(destination, "remote", "set-url", "origin", PROVIDER_URLS[package])
    _git(destination, "config", "user.name", "Public fixture")
    _git(destination, "config", "user.email", "fixture@example.invalid")
    assert _git(destination, "rev-parse", "HEAD") == provider.commit
    assert _git(destination, "ls-files", "--stage", "-z") == _git(provider.checkout, "ls-files", "--stage", "-z")
    assert all(row.startswith("H ") for row in _git(destination, "ls-files", "-v", "-z").split("\0") if row)
    for relative, _, _ in _tree_signature(provider.checkout):
        source, copied = (provider.checkout / relative).stat(), (destination / relative).stat()
        assert (source.st_dev, source.st_ino) != (copied.st_dev, copied.st_ino)
    source_objects = {
        (path.stat().st_dev, path.stat().st_ino)
        for path in (provider.checkout / ".git/objects").rglob("*")
        if path.is_file()
    }
    assert all(
        (path.stat().st_dev, path.stat().st_ino) not in source_objects
        for path in (destination / ".git/objects").rglob("*")
        if path.is_file()
    )
    source_index, copied_index = (provider.checkout / ".git/index").stat(), (destination / ".git/index").stat()
    assert (source_index.st_dev, source_index.st_ino) != (copied_index.st_dev, copied_index.st_ino)
    assert _provider_signature(provider) == before
    return GitInstallProvider(destination, provider.commit)


def _copy_fixture_tree(source: Path, destination: Path) -> None:
    before = _tree_signature(source)
    shutil.copytree(source, destination, copy_function=shutil.copy2, ignore=shutil.ignore_patterns(".git"))
    assert _tree_signature(destination) == before == _tree_signature(source)
    for relative, _, _ in before:
        original, copied = (source / relative).stat(), (destination / relative).stat()
        assert (original.st_dev, original.st_ino) != (copied.st_dev, copied.st_ino)


def _commit_changes(root: Path, message: str) -> str:
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", message)
    return _git(root, "rev-parse", "HEAD")


@pytest.fixture(scope="module", autouse=True)
def _projection_baseline(tmp_path_factory):
    # Real production setup is paid once, including when only one case is selected.
    parent = tmp_path_factory.mktemp("standalone-projection-baseline").resolve()
    root = parent / "root"
    root.mkdir()
    (root / "pyproject.toml").write_text('[project]\nname = "research-project-template"\nversion = "4.0.1"\n')
    _project(root, "template_code_project", with_root=False)
    _project(root, "template_literature_meta_analysis")
    _project(root, "template_advanced_literature_review", with_meta=True)
    provider = GitInstallProvider(root, _commit(root, PROVIDER_URLS[ROOT_PACKAGE]))
    original = _original(provider, parent / "meta-original")
    checkout = parent / "meta-provider"
    manifest = project_standalone_installation(original, checkout, root_provider=provider)
    assert json.loads((checkout / PROJECTION_NAME).read_text()) == manifest
    meta = GitInstallProvider(checkout, _commit(checkout, PROVIDER_URLS[META_PACKAGE]))
    baseline = (
        provider,
        meta,
        original,
        _provider_signature(provider),
        _provider_signature(meta),
        _tree_signature(original),
    )
    yield baseline
    _assert_baseline(baseline)


@pytest.fixture
def committed_root(_projection_baseline, tmp_path: Path) -> Iterator[GitInstallProvider]:
    _assert_baseline(_projection_baseline)
    yield _clone_provider(_projection_baseline[0], tmp_path.resolve() / "root", ROOT_PACKAGE)
    _assert_baseline(_projection_baseline)


@pytest.fixture
def committed_meta(_projection_baseline, committed_root, tmp_path):
    assert committed_root.commit == _projection_baseline[0].commit
    return _clone_provider(_projection_baseline[1], tmp_path.resolve() / "meta-provider", META_PACKAGE)


@pytest.fixture
def prepared_meta_projection(_projection_baseline, committed_root, tmp_path):
    assert committed_root.commit == _projection_baseline[0].commit
    original, projected = tmp_path.resolve() / "original", tmp_path.resolve() / "projected"
    _copy_fixture_tree(_projection_baseline[2], original)
    _copy_fixture_tree(_projection_baseline[1].checkout, projected)
    return original, projected, json.loads((projected / PROJECTION_NAME).read_text())


@pytest.fixture(scope="module")
def _advanced_projection_seed(_projection_baseline, tmp_path_factory):
    # The first selected case needing Advanced pays this real setup.
    root, meta = _projection_baseline[:2]
    _assert_baseline(_projection_baseline)
    parent = tmp_path_factory.mktemp("standalone-advanced-projection").resolve()
    original = _original(root, parent / "original", "template_advanced_literature_review")
    projected = parent / "projected"
    manifest = project_standalone_installation(original, projected, root_provider=root, meta_provider=meta)
    assert json.loads((projected / PROJECTION_NAME).read_text()) == manifest
    signature = (_tree_signature(original), _tree_signature(projected))
    yield original, projected, (projected / PROJECTION_NAME).read_bytes()
    assert (_tree_signature(original), _tree_signature(projected)) == signature
    _assert_baseline(_projection_baseline)


@pytest.fixture
def prepared_advanced_projection(_advanced_projection_seed, committed_root, committed_meta, tmp_path):
    original, projected = tmp_path.resolve() / "advanced-original", tmp_path.resolve() / "advanced"
    _copy_fixture_tree(_advanced_projection_seed[0], original)
    _copy_fixture_tree(_advanced_projection_seed[1], projected)
    return original, projected, json.loads(_advanced_projection_seed[2])


def _original(provider: GitInstallProvider, parent: Path, slug: str = "template_literature_meta_analysis") -> Path:
    destination = parent.resolve() / slug
    populate_mirror_tree(provider.checkout, f"projects/templates/{slug}", destination, source_revision=provider.commit)
    return destination


def _projection(provider: GitInstallProvider, tmp_path: Path) -> tuple[Path, Path, dict]:
    original = _original(provider, tmp_path / "original")
    destination = tmp_path.resolve() / "projected"
    manifest = project_standalone_installation(original, destination, root_provider=provider)
    return original, destination, manifest


def test_projection_preserves_original_scientific_bytes_and_exact_schema_two(committed_root, tmp_path):
    original, projected, manifest = _projection(committed_root, tmp_path)
    assert manifest["schema_version"] == PROJECTION_SCHEMA
    assert manifest["source_commit"] == committed_root.commit
    assert set(manifest["transformations"]) == {"pyproject.toml", "uv.lock"}
    assert (projected / ".template-export.json").read_bytes() == (original / ".template-export.json").read_bytes()
    assert manifest["original_export_sha256"] == publication_export_sha256(original)
    for name, record in manifest["original_files"].items():
        if name not in manifest["transformations"]:
            assert (projected / name).read_bytes() == (original / name).read_bytes()
            assert manifest["projected_files"][name] == record
    assert (projected / "src/science.py").stat().st_mode & 0o111
    assert validate_standalone_installation(original, projected, root_provider=committed_root) == manifest


def test_source_only_exemplar_has_explicit_empty_transformation(committed_root, tmp_path):
    original = _original(committed_root, tmp_path / "original", "template_code_project")
    projected = tmp_path.resolve() / "projected"
    manifest = project_standalone_installation(original, projected, root_provider=committed_root)
    assert manifest["install_providers"] == {}
    assert manifest["transformations"] == {}
    assert manifest["original_files"] == manifest["projected_files"]


@pytest.mark.parametrize("fault", ["source", "lock", "manifest", "missing", "extra", "mode", "link"])
def test_verifier_refuses_changed_projected_bytes_names_modes_and_provenance(
    committed_root, prepared_meta_projection, fault
):
    original, projected, _ = prepared_meta_projection
    target = projected / "src/science.py"
    if fault == "source":
        target.write_text("RESULT = -7\n")
    elif fault == "lock":
        with (projected / "uv.lock").open("a") as stream:
            stream.write("# unsolicited lock change\n")
    elif fault == "manifest":
        payload = json.loads((projected / PROJECTION_NAME).read_text())
        payload["source_commit"] = "0" * 40
        (projected / PROJECTION_NAME).write_text(json.dumps(payload))
    elif fault == "missing":
        target.unlink()
    elif fault == "extra":
        (projected / "extra.py").write_text("UNDECLARED = True\n")
    elif fault == "mode":
        target.chmod(0o644)
    else:
        target.unlink()
        target.symlink_to(original / "src/science.py")
    with pytest.raises(ValueError):
        validate_standalone_installation(original, projected, root_provider=committed_root)


@pytest.mark.parametrize("fault", ["dirty", "hidden-metadata", "wrong-origin", "wrong-commit", "linked-root"])
def test_refuse_provider_substitution_before_destination_creation(committed_root, tmp_path, fault):
    original = _original(committed_root, tmp_path / "original")
    provider = committed_root
    if fault == "dirty":
        (provider.checkout / "untracked.txt").write_text("Unadmitted source\n")
    elif fault == "hidden-metadata":
        _git(provider.checkout, "update-index", "--assume-unchanged", "pyproject.toml")
        (provider.checkout / "pyproject.toml").write_text(
            '[project]\nname="research-project-template"\nversion="4.0.1"\n# mutation\n'
        )
    elif fault == "wrong-origin":
        _git(provider.checkout, "remote", "set-url", "origin", "https://github.com/example/substituted")
    elif fault == "wrong-commit":
        provider = GitInstallProvider(provider.checkout, "0" * 40)
    else:
        link = tmp_path / "linked-root"
        link.symlink_to(provider.checkout, target_is_directory=True)
        provider = GitInstallProvider(link, provider.commit)
    destination = tmp_path.resolve() / "refused"
    with pytest.raises((ValueError, RuntimeError)):
        project_standalone_installation(original, destination, root_provider=provider)
    assert not destination.exists()


def test_refuse_rewritten_provider_transport_without_transfer(committed_root, tmp_path):
    original = _original(committed_root, tmp_path / "original")
    _git(
        committed_root.checkout,
        "config",
        "url.https://github.com/example/rewritten.insteadOf",
        "https://github.com/docxology/",
    )
    with pytest.raises(ValueError, match="rewrites"):
        project_standalone_installation(original, tmp_path.resolve() / "refused", root_provider=committed_root)


def test_refuse_linked_destination_parent_before_creating_any_tree(committed_root, tmp_path):
    original = _original(committed_root, tmp_path / "original")
    outside = tmp_path.resolve() / "outside"
    outside.mkdir()
    link = tmp_path / "destination-link"
    link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="destination parent"):
        project_standalone_installation(original, link / "must-not-exist", root_provider=committed_root)
    assert not tuple(outside.iterdir())


def test_original_manifest_tampering_cannot_authorize_source_changes(committed_root, tmp_path):
    original = _original(committed_root, tmp_path / "original")
    (original / "src/science.py").write_text("RESULT = -7\n")
    payload = json.loads((original / ".template-export.json").read_text())
    payload["files"]["src/science.py"] = hashlib.sha256((original / "src/science.py").read_bytes()).hexdigest()
    (original / ".template-export.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    with pytest.raises(ValueError, match="actual committed canonical public source"):
        project_standalone_installation(original, tmp_path.resolve() / "refused", root_provider=committed_root)


def test_provider_admission_windows_recheck_dirty_and_advanced_head(committed_root):
    from infrastructure.publishing._standalone_provider_admission import (
        _git_provider_closing,
        _git_provider_opening,
    )

    parent = committed_root.checkout.parent
    for index in range(4):
        parent /= f"provider {index}-" + "é" * 52
    parent.mkdir(parents=True)
    checkout = committed_root.checkout.rename(parent / "root")
    assert len(os.fsencode(str(checkout))) > 512
    revision = committed_root.commit
    repository = PROVIDER_URLS[ROOT_PACKAGE]
    assert _git_provider_opening(checkout, revision, repository) == repository
    assert _git_provider_closing(checkout, revision) == _git(checkout, "rev-parse", f"{revision}^{{tree}}")
    target = checkout / "projects/templates/template_code_project/src/science.py"
    target.write_text("RESULT = 11\n")
    with pytest.raises(ValueError, match="clean source working tree"):
        _git_provider_closing(checkout, revision)
    _git(checkout, "add", "--", "projects/templates/template_code_project/src/science.py")
    _git(checkout, "commit", "-qm", "Advance the invented provider after admission")
    advanced = _git(checkout, "rev-parse", "HEAD")
    assert advanced != revision
    with pytest.raises(ValueError, match="differs from current HEAD"):
        _git_provider_closing(checkout, revision)
    assert _git_provider_opening(checkout, advanced, repository) == repository
    assert _git_provider_closing(checkout, advanced) == _git(checkout, "rev-parse", f"{advanced}^{{tree}}")


def test_advanced_requires_actual_meta_projection_from_same_root(
    committed_root, committed_meta, prepared_advanced_projection
):
    _, _, manifest = prepared_advanced_projection
    assert manifest["install_providers"][META_PACKAGE]["commit"] == committed_meta.commit
    assert manifest["install_providers"][ROOT_PACKAGE]["commit"] == committed_root.commit


def test_advanced_requires_actual_meta_provider_before_destination_creation(committed_root, tmp_path):
    advanced = _original(committed_root, tmp_path / "advanced-original", "template_advanced_literature_review")
    destination = tmp_path.resolve() / "missing-meta"
    with pytest.raises(ValueError, match="actual committed Meta provider"):
        project_standalone_installation(advanced, destination, root_provider=committed_root)
    assert not destination.exists()


def test_advanced_independent_verifier_rebuilds_from_actual_providers(
    committed_root, committed_meta, prepared_advanced_projection
):
    advanced, projected, manifest = prepared_advanced_projection
    assert (
        validate_standalone_installation(
            advanced, projected, root_provider=committed_root, meta_provider=committed_meta
        )
        == manifest
    )


def test_advanced_verifier_refuses_hidden_meta_source_change(
    committed_root, committed_meta, prepared_advanced_projection
):
    advanced, projected, _ = prepared_advanced_projection
    _git(committed_meta.checkout, "update-index", "--assume-unchanged", "src/science.py")
    (committed_meta.checkout / "src/science.py").write_text("RESULT = -7\n")
    with pytest.raises(ValueError, match="exact reviewed projection"):
        validate_standalone_installation(
            advanced, projected, root_provider=committed_root, meta_provider=committed_meta
        )


def test_prepared_meta_provider_cannot_follow_a_different_root_commit(committed_root, committed_meta, tmp_path):
    _git(committed_root.checkout, "commit", "--allow-empty", "-qm", "Advance actual Root identity only")
    revision = _git(committed_root.checkout, "rev-parse", "HEAD")
    assert revision != committed_root.commit
    advanced_root = GitInstallProvider(committed_root.checkout, revision)
    advanced = _original(advanced_root, tmp_path / "advanced-original", "template_advanced_literature_review")
    destination = tmp_path.resolve() / "refused"
    with pytest.raises(ValueError, match="exact reviewed projection"):
        project_standalone_installation(
            advanced, destination, root_provider=advanced_root, meta_provider=committed_meta
        )
    assert not destination.exists()


@pytest.mark.parametrize("fault", ["missing-committed-path", "committed-mode"])
def test_advanced_refuses_meta_worktree_hiding_a_committed_path_or_mode(
    committed_root, committed_meta, tmp_path, fault
):
    checkout = committed_meta.checkout
    target = checkout / "src/science.py"
    content = target.read_bytes()
    if fault == "missing-committed-path":
        _git(checkout, "rm", "--cached", "--", "src/science.py")
        with (checkout / ".git/info/exclude").open("a") as stream:
            stream.write("\nsrc/science.py\n")
    else:
        _git(checkout, "config", "core.fileMode", "false")
        _git(checkout, "update-index", "--chmod=-x", "src/science.py")
    _git(checkout, "commit", "-qm", "Commit invented provider index divergence")
    revision = _git(checkout, "rev-parse", "HEAD")
    assert _git(checkout, "status", "--porcelain", "--untracked-files=all") == ""
    assert target.read_bytes() == content
    assert target.stat().st_mode & 0o111
    advanced = _original(committed_root, tmp_path / "advanced-original", "template_advanced_literature_review")
    destination = tmp_path.resolve() / "refused"
    with pytest.raises(ValueError, match="committed path or mode"):
        project_standalone_installation(
            advanced, destination, root_provider=committed_root, meta_provider=GitInstallProvider(checkout, revision)
        )
    assert not destination.exists()


@pytest.mark.parametrize(
    "extra",
    [
        "src/unreviewed.py",
        "src/history/unreviewed.py",
        "setup.py",
        "setup.cfg",
        "MANIFEST.in",
        "LICENSE.unreviewed",
        "LICENSE.pdf",
        "provider.egg-info/SOURCES.txt",
        "unreviewed_build_helper.py",
    ],
)
def test_advanced_refuses_extra_committed_meta_installation_inputs(committed_root, committed_meta, tmp_path, extra):
    checkout = committed_meta.checkout
    target = checkout / extra
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("UNREVIEWED = True\n")
    revision = _commit_changes(checkout, "Commit actual Meta fixture divergence")
    advanced = _original(committed_root, tmp_path / "advanced-original", "template_advanced_literature_review")
    destination = tmp_path.resolve() / "refused"
    with pytest.raises(ValueError, match="installation inputs outside"):
        project_standalone_installation(
            advanced, destination, root_provider=committed_root, meta_provider=GitInstallProvider(checkout, revision)
        )
    assert not destination.exists()


def test_advanced_keeps_committed_meta_publication_evidence_outside_package_inputs(
    committed_root, committed_meta, tmp_path
):
    checkout = committed_meta.checkout
    evidence = checkout / "output/history/invented-publication.pdf"
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b"invented retained publication fixture\n")
    inventory = checkout / ".template-publication-tree.json"
    inventory.write_text('{"invented_fixture": "retained publication ownership"}\n')
    revision = _commit_changes(checkout, "Commit actual Meta fixture divergence")
    advanced = _original(committed_root, tmp_path / "advanced-original", "template_advanced_literature_review")
    meta = GitInstallProvider(checkout, revision)
    manifest = project_standalone_installation(
        advanced, tmp_path.resolve() / "projected", root_provider=committed_root, meta_provider=meta
    )
    assert manifest["install_providers"][META_PACKAGE]["commit"] == revision
    assert evidence.read_bytes() == b"invented retained publication fixture\n"
    assert json.loads(inventory.read_text()) == {"invented_fixture": "retained publication ownership"}


def test_advanced_refuses_committed_link_disguised_as_retained_publication_evidence(
    committed_root, committed_meta, tmp_path
):
    checkout = committed_meta.checkout
    evidence = checkout / "output/history/invented-publication.pdf"
    evidence.parent.mkdir(parents=True)
    evidence.symlink_to(checkout / "src/science.py")
    revision = _commit_changes(checkout, "Commit actual Meta fixture divergence")
    advanced = _original(committed_root, tmp_path / "advanced-original", "template_advanced_literature_review")
    destination = tmp_path.resolve() / "refused"
    with pytest.raises(ValueError, match="regular committed source"):
        project_standalone_installation(
            advanced, destination, root_provider=committed_root, meta_provider=GitInstallProvider(checkout, revision)
        )
    assert not destination.exists()


def test_replacement_refs_cannot_substitute_objects_under_original_public_commit(committed_root, tmp_path, monkeypatch):
    original = committed_root.commit
    source = "projects/templates/template_literature_meta_analysis/src/science.py"
    old_blob = _git(committed_root.checkout, "rev-parse", f"{original}:{source}")
    (committed_root.checkout / source).write_text("RESULT = -7\n")
    _git(committed_root.checkout, "add", "-A")
    _git(committed_root.checkout, "commit", "-qm", "Owned replacement source")
    replacement = _git(committed_root.checkout, "rev-parse", "HEAD")
    _git(committed_root.checkout, "replace", original, replacement)
    _git(committed_root.checkout, "update-ref", "HEAD", original)
    assert _git(committed_root.checkout, "status", "--porcelain") == ""
    assert _git(committed_root.checkout, "rev-parse", f"{original}:{source}") != old_blob
    monkeypatch.setenv("GIT_NO_REPLACE_OBJECTS", "0")
    assert publication_git(["rev-parse", f"{original}:{source}"], committed_root.checkout).stdout.strip() == old_blob
    destination = tmp_path.resolve() / "must-not-exist"
    with pytest.raises(ValueError, match="clean source working tree"):
        populate_mirror_tree(
            committed_root.checkout,
            "projects/templates/template_literature_meta_analysis",
            destination,
            source_revision=original,
        )
    assert not destination.exists()


def test_mirror_source_recheck_rebuilds_projection_from_actual_providers(committed_root, tmp_path):
    _, projected, _ = _projection(committed_root, tmp_path)
    digest = publication_export_sha256(projected)
    _assert_source_current(
        committed_root.checkout,
        "projects/templates/template_literature_meta_analysis",
        committed_root.commit,
        digest,
        tmp_path.resolve(),
        install_projection=True,
    )
    with pytest.raises(ValueError, match="whole standalone export changed"):
        _assert_source_current(
            committed_root.checkout,
            "projects/templates/template_literature_meta_analysis",
            committed_root.commit,
            "0" * 64,
            tmp_path.resolve(),
            install_projection=True,
        )


def test_meta_provider_cannot_be_ignored_in_source_only_mirror_mode(committed_root):
    with pytest.raises(ValueError, match="explicit installation projection"):
        sync_exemplar(
            committed_root.checkout,
            "template_code_project",
            commit=False,
            source_revision=committed_root.commit,
            meta_provider=committed_root,
        )
