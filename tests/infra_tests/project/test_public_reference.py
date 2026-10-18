"""Genuine complete-source DATA controls; these are not installed acceptance."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

import infrastructure
from infrastructure.core.pipeline.artifacts._inventory import collect_stable_output_inventory
from infrastructure.core.project_paths import find_repo_root
from infrastructure.project.public_acceptance_scope import RuntimeScope
from infrastructure.project.public_reference import _canonical_inventory, admit_public_reference, reference_binding
from infrastructure.project.public_reference_git import inventory, native_git, remaining
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.readiness_receipts import public_source_paths

pytestmark = pytest.mark.timeout(1800)


def _git(root: Path, *arguments: str) -> bytes:
    """Owned fixture setup uses actual native Git and invented public author data."""
    executable = shutil.which("git", path=os.defpath)
    assert executable is not None
    result = subprocess.run(
        [
            executable,
            "-c",
            "user.name=Public reference fixture",
            "-c",
            "user.email=fixture@example.invalid",
            *arguments,
        ],
        cwd=root,
        env={"PATH": os.defpath, "LC_ALL": "C", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"},
        capture_output=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, (result.returncode, result.stderr)
    return result.stdout


@pytest.fixture(scope="module")
def complete_reference(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, str, str]:
    """Copy the true complete canonical public bytes, then commit the owned fixture.

    Expectations originate in this owned harness's genuine commit and actual
    original source fingerprint. They are deliberately not a production
    candidate or an independently published release identity.
    """
    original = find_repo_root()
    root = tmp_path_factory.mktemp("complete-public-source-data").resolve()
    source = RuntimeScope(original, "root").source_identity()
    submodule = "infrastructure/steganography/kmyth"
    pinned = _git(original, "ls-files", "--stage", "--", submodule).decode().strip().split()
    assert pinned[0] == "160000" and pinned[2] == "0" and pinned[3] == submodule
    (root / submodule).parent.mkdir(parents=True, exist_ok=True)
    # Clone only the actual owned local checkout, without hardlinks or network.
    _git(root, "clone", "--quiet", "--no-hardlinks", "--no-checkout", str(original / submodule), submodule)
    _git(root / submodule, "checkout", "--quiet", "--detach", pinned[1])
    paths = list(public_source_paths(original))
    for project in PUBLIC_PROJECT_NAMES:
        output = original / "projects" / project / "output"
        if output.exists():
            stable = collect_stable_output_inventory(output)
            assert not stable.issues
            paths.extend(stable.files)
    for path in sorted(set(paths)):
        target = root / path.relative_to(original)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    # Canonical inventory includes empty public directories as well as files.
    for relative, kind, _ in _canonical_inventory(original):
        if kind == "directory":
            (root / relative).mkdir(parents=True, exist_ok=True)
    _git(root, "init", "--quiet")
    # Reproduce the tracked tree exactly: a historically tracked file can match
    # a later ignore rule (for example a committed replay cache), and a fresh
    # clone still contains and tracks it.
    _git(root, "add", "--all", "--force")
    _git(root, "commit", "--quiet", "-m", "Owned complete public source DATA fixture")
    commit = _git(root, "rev-parse", "HEAD").decode().strip()
    assert RuntimeScope(root, "root").source_identity() == source
    return root, commit, source


def _clone_complete_reference(fixture: tuple[Path, str, str], destination: Path, *, deadline: float) -> Path:
    """Clone actual owned Git objects through Git, never copy its live object DB."""
    original, commit, source = fixture
    expected = inventory(original, commit, deadline)
    assert not destination.exists()
    remaining(deadline)
    _git(destination.parent, "clone", "--quiet", "--no-local", "--no-hardlinks", str(original), str(destination))
    assert len(expected.gitlinks) == 1
    link = expected.gitlinks[0]
    assert link.path == "infrastructure/steganography/kmyth"
    remaining(deadline)
    _git(
        destination,
        "clone",
        "--quiet",
        "--no-local",
        "--no-hardlinks",
        "--no-checkout",
        str(original / link.path),
        link.path,
    )
    _git(destination / link.path, "checkout", "--quiet", "--detach", link.oid)
    # Git has no empty-directory objects. Preserve the actual public topology,
    # rather than inventing placeholders or weakening its separate Source check.
    for relative, kind, _ in _canonical_inventory(original):
        if kind == "directory":
            (destination / relative).mkdir(parents=True, exist_ok=True)
    assert inventory(destination, commit, deadline) == expected == inventory(original, commit, deadline)
    assert _canonical_inventory(destination) == _canonical_inventory(original)
    assert RuntimeScope(destination, "root").source_identity() == source
    for root in (destination, destination / link.path):
        assert not (root / ".git/objects/info/alternates").exists()
    remaining(deadline)
    return destination


def test_normal_clone_retains_complete_native_git_inventory_and_source(
    complete_reference: tuple[Path, str, str], tmp_path: Path
) -> None:
    destination = _clone_complete_reference(complete_reference, tmp_path / "current", deadline=time.monotonic() + 300)
    assert destination.is_dir() and destination != complete_reference[0]


def _admit(fixture: tuple[Path, str, str]):
    root, commit, source = fixture
    return admit_public_reference(
        root, expected_commit=commit, expected_source_identity=source, deadline=time.monotonic() + 300
    )


def test_complete_actual_reference_keeps_sdk_import_authority_and_held_bytes(
    complete_reference: tuple[Path, str, str],
) -> None:
    root, commit, source = complete_reference
    before = tuple(sys.path)
    selected = infrastructure.__file__
    reference = _admit(complete_reference)
    assert reference.commit == commit and reference.source_identity == source
    assert len(reference.git.submodules) == 1
    nested_path, nested = reference.git.submodules[0]
    assert nested_path == "infrastructure/steganography/kmyth"
    assert nested.commit == reference.git.gitlinks[0].oid
    assert nested.files and not nested.gitlinks
    assert all(not relative.endswith("/.git") for relative, _, _ in reference.records)
    assert infrastructure.__file__ == selected and tuple(sys.path) == before
    assert not Path(selected).resolve().is_relative_to(root)
    assert reference.read("pyproject.toml") == (root / "pyproject.toml").read_bytes()
    for project in PUBLIC_PROJECT_NAMES:
        assert reference.read("projects/" + project + "/pyproject.toml")
        assert any(row[0].startswith("projects/" + project + "/tests/") for row in reference.records)
        assert any(row[0].startswith("projects/" + project + "/manuscript/") for row in reference.records)
    reference.verify_unchanged(deadline=time.monotonic() + 300)
    with pytest.raises(ValueError):
        reference.read("projects/working/invented-private.txt")


@pytest.mark.parametrize("field", ["commit", "source"])
def test_external_identity_is_required_not_computed_and_self_approved(
    complete_reference: tuple[Path, str, str], field: str
) -> None:
    root, commit, source = complete_reference
    with pytest.raises(ValueError):
        admit_public_reference(
            root,
            expected_commit="a" * len(commit) if field == "commit" else commit,
            expected_source_identity="a" * 64 if field == "source" else source,
            deadline=time.monotonic() + 300,
        )


def test_actual_promisor_configuration_is_refused_before_object_traversal(
    complete_reference: tuple[Path, str, str],
) -> None:
    root, _, _ = complete_reference
    try:
        _git(root, "config", "remote.owned-uncontacted.promisor", "true")
        with pytest.raises(ValueError, match="partial/promisor"):
            _admit(complete_reference)
    finally:
        _git(root, "config", "--unset", "remote.owned-uncontacted.promisor")


@pytest.mark.parametrize("flag", ["assume-unchanged", "skip-worktree"])
def test_actual_index_flags_cannot_hide_changed_committed_bytes(
    complete_reference: tuple[Path, str, str], flag: str
) -> None:
    root, commit, _ = complete_reference
    target = root / "README.md"
    original = target.read_bytes()
    try:
        _git(root, "update-index", "--" + flag, "README.md")
        target.write_bytes(original + b"\nInvented changed public reference.\n")
        source = RuntimeScope(root, "root").source_identity()
        with pytest.raises(ValueError, match="index flags"):
            admit_public_reference(
                root, expected_commit=commit, expected_source_identity=source, deadline=time.monotonic() + 300
            )
    finally:
        _git(root, "update-index", "--no-" + flag, "README.md")
        target.write_bytes(original)


@pytest.mark.parametrize("fault", ["change", "remove", "rename", "add", "aba", "directory-aba", "leaf-link"])
def test_actual_source_mutations_refuse_current_reference(
    complete_reference: tuple[Path, str, str], fault: str
) -> None:
    root, _, _ = complete_reference
    reference = _admit(complete_reference)
    target = root / "README.md"
    renamed = root / "README-owned-renamed.md"
    added = root / "infrastructure/owned_public_reference_probe.py"
    directory = root / "infrastructure/owned_public_reference_directory"
    original = target.read_bytes()
    try:
        if fault in {"change", "aba"}:
            target.write_bytes(original + b"\nInvented public mutation.\n")
            if fault == "aba":
                target.write_bytes(original)
                assert RuntimeScope(root, "root").source_identity() == reference.source_identity
        elif fault == "remove":
            target.unlink()
        elif fault == "rename":
            target.rename(renamed)
        elif fault == "add":
            added.write_text("INVENTED_PUBLIC_PROBE = True\n")
        elif fault == "directory-aba":
            directory.mkdir()
            directory.rmdir()
            assert RuntimeScope(root, "root").source_identity() == reference.source_identity
        else:
            target.unlink()
            target.symlink_to(root / "AGENTS.md")
        assert reference.read("README.md") == original
        with pytest.raises(ValueError):
            reference.verify_unchanged(deadline=time.monotonic() + 300)
    finally:
        if target.is_symlink():
            target.unlink()
        if renamed.exists():
            renamed.rename(target)
        target.write_bytes(original)
        added.unlink(missing_ok=True)
        if directory.exists():
            directory.rmdir()


def test_actual_partial_roster_and_physical_root_replacement_are_refused(
    complete_reference: tuple[Path, str, str],
) -> None:
    root, commit, source = complete_reference
    marker = root / "projects" / PUBLIC_PROJECT_NAMES[-1] / "tests"
    saved_marker = marker.with_name("tests-owned-removed")
    try:
        marker.rename(saved_marker)
        with pytest.raises(ValueError, match="complete canonical"):
            admit_public_reference(
                root, expected_commit=commit, expected_source_identity=source, deadline=time.monotonic() + 300
            )
    finally:
        saved_marker.rename(marker)
    reference = _admit(complete_reference)
    saved = root.with_name(root.name + "-original-physical-reference")
    try:
        root.rename(saved)
        shutil.copytree(saved, root)
        assert RuntimeScope(root, "root").source_identity() == source
        with pytest.raises(ValueError, match="changed after admission"):
            reference.verify_unchanged(deadline=time.monotonic() + 300)
    finally:
        if saved.exists():
            if root.exists():
                shutil.rmtree(root)
            saved.rename(root)


def test_genuine_data_shadow_marker_is_live_but_never_selected_as_sdk(
    complete_reference: tuple[Path, str, str],
) -> None:
    root, commit, _ = complete_reference
    package = root / "infrastructure/__init__.py"
    original = package.read_bytes()
    marker = root / "output/readiness/owned-data-shadow-marker"
    marker.parent.mkdir(parents=True, exist_ok=True)
    selected = infrastructure.__file__
    before = tuple(sys.path)
    try:
        package.write_bytes(
            (
                "from pathlib import Path\nPath("
                + repr(str(marker))
                + ").write_text('actual owned data shadow')\nraise RuntimeError('owned source DATA must not be SDK')\n"
            ).encode()
            + original
        )
        _git(root, "add", "infrastructure/__init__.py")
        _git(root, "commit", "--quiet", "-m", "Owned genuine data-shadow negative")
        changed = _git(root, "rev-parse", "HEAD").decode().strip()
        source = RuntimeScope(root, "root").source_identity()
        child = subprocess.run(
            [sys.executable, "-I", "-c", "import sys;sys.path.insert(0," + repr(str(root)) + ");import infrastructure"],
            capture_output=True,
            timeout=60,
            check=False,
        )
        assert child.returncode == 1 and marker.read_text() == "actual owned data shadow"
        marker.unlink()
        with pytest.raises(ValueError, match="actual selected SDK"):
            admit_public_reference(
                root, expected_commit=changed, expected_source_identity=source, deadline=time.monotonic() + 300
            )
        assert not marker.exists()
        assert infrastructure.__file__ == selected and tuple(sys.path) == before
    finally:
        _git(root, "reset", "--hard", commit)
        marker.unlink(missing_ok=True)


def test_plain_archive_and_partial_explicit_bindings_cannot_invent_git_custody(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname="research-project-template"\nversion="4.0.1"\n')
    with pytest.raises(ValueError):
        admit_public_reference(
            tmp_path.resolve(),
            expected_commit="a" * 40,
            expected_source_identity="a" * 64,
            deadline=time.monotonic() + 30,
        )
    assert reference_binding({}) is None
    with pytest.raises(ValueError):
        reference_binding({"TEMPLATE_PUBLIC_REFERENCE_ROOT": str(tmp_path)})
    complete = {
        "TEMPLATE_PUBLIC_REFERENCE_ROOT": str(tmp_path),
        "TEMPLATE_PUBLIC_REFERENCE_COMMIT": "a" * 40,
        "TEMPLATE_PUBLIC_REFERENCE_FINGERPRINT": "b" * 64,
    }
    assert reference_binding(complete) == (tmp_path, "a" * 40, "b" * 64)
    with pytest.raises(TimeoutError):
        native_git(tmp_path, time.monotonic() - 1, "rev-parse", "HEAD")


def test_real_private_filename_open_control_is_live_before_guarded_admission(
    complete_reference: tuple[Path, str, str],
) -> None:
    root, commit, source = complete_reference
    target = root / "infrastructure/.env"
    marker = root / "output/readiness/invented-private-read-observed"
    actual_sdk = Path(infrastructure.__file__).resolve().parent.parent
    target.write_bytes(b"invented_public_fixture_only=not_a_real_secret\n")
    program = f"""
import sys,time
from pathlib import Path
sys.path.insert(0,{str(actual_sdk)!r})
import infrastructure
assert Path(infrastructure.__file__).resolve().parent.parent == Path({str(actual_sdk)!r})
from infrastructure.project.public_acceptance_scope import RuntimeScope
from infrastructure.project.public_reference import admit_public_reference
marker=Path({str(marker)!r})
def observe(event,args):
    if event == 'open' and args and str(args[0]) in ('.env',{str(target)!r}):
        marker.parent.mkdir(parents=True,exist_ok=True)
        marker.write_text('actual private-filename open observed')
sys.addaudithook(observe)
if sys.argv[1]=='ordinary':
    RuntimeScope(Path({str(root)!r}),'root').source_identity()
    assert marker.read_text()=='actual private-filename open observed'
else:
    try:
        admit_public_reference(Path({str(root)!r}),expected_commit={commit!r},expected_source_identity={source!r},deadline=time.monotonic()+300)
    except ValueError:
        pass
    else:
        raise AssertionError('private control filename was accepted')
    assert not marker.exists(), 'guard must refuse before consumed-byte open'
"""
    try:
        ordinary = subprocess.run(
            [sys.executable, "-I", "-c", program, "ordinary"], capture_output=True, timeout=300, check=False
        )
        assert ordinary.returncode == 0, ordinary.stderr
        assert marker.read_text() == "actual private-filename open observed"
        marker.unlink()
        guarded = subprocess.run(
            [sys.executable, "-I", "-c", program, "guarded"], capture_output=True, timeout=360, check=False
        )
        assert guarded.returncode == 0, guarded.stderr
        assert not marker.exists()
    finally:
        target.unlink(missing_ok=True)
        marker.unlink(missing_ok=True)


@pytest.mark.parametrize("fault", ["blob", "head", "flags", "missing"])
def test_genuine_pinned_submodule_custody_cannot_be_flattened_or_tampered(
    complete_reference: tuple[Path, str, str], fault: str
) -> None:
    root, commit, _ = complete_reference
    admitted = _admit(complete_reference)
    name, nested = admitted.git.submodules[0]
    checkout = root / name
    saved = checkout.with_name("kmyth-owned-missing")
    target = checkout / "README.md"
    original = target.read_bytes()
    try:
        if fault == "blob":
            target.write_bytes(original + b"\nInvented nested public source mutation.\n")
        elif fault == "head":
            target.write_bytes(original + b"\nInvented owned alternate nested commit.\n")
            _git(checkout, "add", "README.md")
            _git(checkout, "commit", "--quiet", "-m", "Owned nested pin negative")
        elif fault == "flags":
            _git(checkout, "update-index", "--assume-unchanged", "README.md")
        else:
            checkout.rename(saved)
        # Even a nominated current byte digest cannot replace the committed pin.
        current_source = RuntimeScope(root, "root").source_identity()
        with pytest.raises((ValueError, FileNotFoundError)):
            admit_public_reference(
                root, expected_commit=commit, expected_source_identity=current_source, deadline=time.monotonic() + 300
            )
        with pytest.raises((ValueError, FileNotFoundError)):
            admitted.verify_unchanged(deadline=time.monotonic() + 300)
    finally:
        if saved.exists():
            saved.rename(checkout)
        if fault == "flags":
            _git(checkout, "update-index", "--no-assume-unchanged", "README.md")
        _git(checkout, "reset", "--hard", nested.commit)
        assert target.read_bytes() == original


def test_actual_git_control_metadata_is_separate_from_public_source_data(
    complete_reference: tuple[Path, str, str],
) -> None:
    root, _, source = complete_reference
    reference = _admit(complete_reference)
    name, _ = reference.git.submodules[0]
    try:
        _git(root / name, "config", "owned.public-reference-note", "invented control metadata")
        assert RuntimeScope(root, "root").source_identity() == source
        reference.verify_unchanged(deadline=time.monotonic() + 300)
        with pytest.raises(ValueError):
            reference.read(name + "/.git/config")
    finally:
        _git(root / name, "config", "--unset", "owned.public-reference-note")


@pytest.mark.parametrize("fault", ["path", "url", "extra-declaration", "execution-option"])
def test_actual_committed_submodule_declaration_is_not_ambient_routing_authority(
    complete_reference: tuple[Path, str, str], fault: str
) -> None:
    root, original_commit, _ = complete_reference
    _admit(complete_reference)
    declaration = root / ".gitmodules"
    original = declaration.read_text()
    assert "path = infrastructure/steganography/kmyth" in original
    assert "url = https://github.com/docxology/kmyth.git" in original
    try:
        if fault == "path":
            changed = original.replace(
                "path = infrastructure/steganography/kmyth", "path = infrastructure/owned-wrong-existing"
            )
        elif fault == "url":
            changed = original.replace(
                "url = https://github.com/docxology/kmyth.git",
                "url = https://invalid.example/owned-never-contacted.git",
            )
        elif fault == "extra-declaration":
            changed = (
                original
                + '\n[submodule "owned-unrelated"]\npath = infrastructure/owned-unrelated\nurl = https://invalid.example/never-contacted.git\n'
            )
        else:
            changed = original + "\tupdate = !owned-never-executed\n"
        declaration.write_text(changed)
        _git(root, "add", ".gitmodules")
        _git(root, "commit", "--quiet", "-m", "Owned committed declaration negative")
        current_commit = _git(root, "rev-parse", "HEAD").decode().strip()
        current_source = RuntimeScope(root, "root").source_identity()
        with pytest.raises(ValueError, match="actual declaration"):
            admit_public_reference(
                root,
                expected_commit=current_commit,
                expected_source_identity=current_source,
                deadline=time.monotonic() + 300,
            )
    finally:
        _git(root, "reset", "--hard", original_commit)
        assert declaration.read_text() == original


@pytest.mark.parametrize("nested", [False, True])
def test_actual_worktree_promisor_configuration_is_refused_before_object_traversal(
    complete_reference: tuple[Path, str, str], nested: bool
) -> None:
    root, _, _ = complete_reference
    checkout = root / "infrastructure/steganography/kmyth" if nested else root
    try:
        _git(checkout, "config", "extensions.worktreeConfig", "true")
        _git(checkout, "config", "--worktree", "remote.owned-never-contacted.promisor", "true")
        with pytest.raises(ValueError, match="partial/promisor"):
            _admit(complete_reference)
    finally:
        _git(checkout, "config", "--worktree", "--unset", "remote.owned-never-contacted.promisor")
        _git(checkout, "config", "--unset", "extensions.worktreeConfig")


@pytest.mark.parametrize(
    "relative",
    ["projects/working/owned-private.txt", "fonds/archive/owned-private.txt", "infrastructure/.env.owned-private"],
)
def test_genuine_private_committed_inventory_refuses_without_content_read(
    complete_reference: tuple[Path, str, str], relative: str
) -> None:
    root, commit, source = complete_reference
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"invented owned private-scope fixture; no credential\n")
    marker = root / "output/readiness/owned-private-content-read"
    marker.parent.mkdir(parents=True, exist_ok=True)
    sdk_root = Path(infrastructure.__file__).resolve().parent.parent
    child = r"""
import sys, time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from infrastructure.project.public_reference import admit_public_reference
source, marker = Path(sys.argv[3]), Path(sys.argv[4])
def audit(event, args):
    if event == "open" and args and str(args[0]) == str(source):
        marker.write_text("actual owned private byte open")
sys.addaudithook(audit)
if sys.argv[7] == "ordinary":
    assert source.read_bytes()
else:
    try:
        admit_public_reference(
            Path(sys.argv[2]), expected_commit=sys.argv[5],
            expected_source_identity=sys.argv[6], deadline=time.monotonic()+300
        )
    except ValueError as exc:
        assert "private/control" in str(exc), str(exc)
    else:
        raise AssertionError("private committed DATA was admitted")
"""
    try:
        _git(root, "add", "--force", "--", relative)
        _git(root, "commit", "--quiet", "-m", "Owned private inventory negative")
        changed = _git(root, "rev-parse", "HEAD").decode().strip()
        arguments = [
            sys.executable,
            "-I",
            "-c",
            child,
            str(sdk_root),
            str(root),
            str(target),
            str(marker),
            changed,
            source,
        ]
        positive = subprocess.run([*arguments, "ordinary"], capture_output=True, check=False, timeout=330)
        assert positive.returncode == 0, positive.stderr
        assert marker.read_text() == "actual owned private byte open"
        marker.unlink()
        refused = subprocess.run([*arguments, "guarded"], capture_output=True, check=False, timeout=330)
        assert refused.returncode == 0, refused.stderr
        assert not marker.exists()
    finally:
        _git(root, "reset", "--hard", commit)
        target.unlink(missing_ok=True)
        marker.unlink(missing_ok=True)
