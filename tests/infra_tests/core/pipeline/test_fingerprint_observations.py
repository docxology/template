"""File-observation reuse still detects real filesystem content changes."""

from __future__ import annotations

import hashlib
import os
import sys
from collections import Counter
from pathlib import Path
from types import FrameType

import pytest

from infrastructure.core.pipeline.fingerprints import paths_digest, tree_records
from infrastructure.core.pipeline.fingerprint_files import anchored_parent, open_directory


def _recorded_hash(path: Path) -> str:
    records = tree_records(path)
    assert len(records) == 1 and records[0][:2] == (".", "file")
    return records[0][2]


def test_repeated_binary_observations_preserve_exact_content_hash(tmp_path: Path) -> None:
    binary = tmp_path / "tool"
    content = bytes(range(256)) * 8192
    binary.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()
    assert _recorded_hash(binary) == expected
    assert _recorded_hash(binary) == expected


def test_same_length_overwrite_with_restored_mtime_invalidates_reuse(tmp_path: Path) -> None:
    source = tmp_path / "model.py"
    source.write_bytes(b"original")
    before = source.stat()
    first = _recorded_hash(source)
    source.write_bytes(b"modified")
    os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns))
    assert source.stat().st_mtime_ns == before.st_mtime_ns
    assert _recorded_hash(source) != first
    assert _recorded_hash(source) == hashlib.sha256(b"modified").hexdigest()


def test_atomic_replacement_invalidates_same_path_size_and_mtime(tmp_path: Path) -> None:
    source = tmp_path / "lock"
    source.write_bytes(b"first!")
    before = source.stat()
    first = _recorded_hash(source)
    replacement = tmp_path / "replacement"
    replacement.write_bytes(b"second")
    os.utime(replacement, ns=(before.st_atime_ns, before.st_mtime_ns))
    replacement.replace(source)
    assert _recorded_hash(source) != first
    assert _recorded_hash(source) == hashlib.sha256(b"second").hexdigest()


def test_directory_add_delete_and_rename_change_content_identity(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    item = source / "first.py"
    item.write_text("result = 1\n", encoding="utf-8")
    original = paths_digest((source,))
    item.rename(source / "renamed.py")
    renamed = paths_digest((source,))
    assert renamed != original
    extra = source / "second.py"
    extra.write_text("result = 2\n", encoding="utf-8")
    assert paths_digest((source,)) != renamed
    extra.unlink()
    assert paths_digest((source,)) == renamed
    (source / "renamed.py").unlink()
    assert paths_digest((source,)) != renamed


@pytest.mark.parametrize(
    "name", [".hypothesis", ".mypy_cache", "htmlcov", ".coverage.project", "coverage_project.json", "build", "dist"]
)
def test_source_controls_apply_only_at_the_nominated_root(tmp_path: Path, name: str) -> None:
    root = tmp_path / "project"
    root.mkdir()
    before = paths_digest((root,), source=True)
    generated = root / name
    generated.write_text("runtime first", encoding="utf-8")
    assert paths_digest((root,), source=True) == before
    generated.write_text("runtime second", encoding="utf-8")
    assert paths_digest((root,), source=True) == before
    authored = root / "data" / name
    authored.parent.mkdir()
    authored.write_text("scientific first", encoding="utf-8")
    bound = paths_digest((root,), source=True)
    authored.write_text("scientific second", encoding="utf-8")
    assert paths_digest((root,), source=True) != bound


def test_only_direct_source_package_metadata_is_a_control(tmp_path: Path) -> None:
    root = tmp_path / "project"
    (root / "src").mkdir(parents=True)
    before = paths_digest((root,), source=True)
    generated = root / "src" / "installed.egg-info"
    generated.mkdir()
    (generated / "PKG-INFO").write_text("runtime metadata", encoding="utf-8")
    assert paths_digest((root,), source=True) == before
    authored = root / "src" / "fixtures" / "installed.egg-info"
    authored.mkdir(parents=True)
    (authored / "PKG-INFO").write_text("scientific input", encoding="utf-8")
    first = paths_digest((root,), source=True)
    (authored / "PKG-INFO").write_text("changed input", encoding="utf-8")
    assert paths_digest((root,), source=True) != first


@pytest.mark.parametrize("name", (".git", ".DS_Store"))
def test_nested_repository_metadata_is_not_authored_source(tmp_path: Path, name: str) -> None:
    root = tmp_path / "source"
    nested = root / "infrastructure" / "vendor"
    nested.mkdir(parents=True)
    authored = nested / "model.py"
    authored.write_text("result = 1\n")
    before = paths_digest((root,), source=True)
    metadata = nested / name
    metadata.write_text("local repository metadata")
    assert paths_digest((root,), source=True) == before
    assert any(row[0].endswith(name) for row in tree_records(root))
    metadata.unlink()
    metadata.mkdir()
    (metadata / "HEAD").write_text("local repository revision")
    assert paths_digest((root,), source=True) == before
    authored.write_text("result = 2\n")
    assert paths_digest((root,), source=True) != before
    before = paths_digest((root,), source=True)
    (nested / (name + "-authored")).write_text("public authored input")
    assert paths_digest((root,), source=True) != before


@pytest.mark.parametrize("source", [False, True])
@pytest.mark.parametrize(
    ("nominated", "package_root", "source_files"),
    [
        (
            "fixture é with spaces",
            "src",
            ("plain.txt", "kept.egg-info/PKG-INFO", "nested/build", "src/fixtures/owned.egg-info/PKG-INFO"),
        ),
        (
            "src",
            "SRC",
            (
                "plain.txt",
                "kept.egg-info/PKG-INFO",
                "nested/build",
                "SRC/owned.egg-info/PKG-INFO",
                "SRC/fixtures/owned.egg-info/PKG-INFO",
            ),
        ),
    ],
)
def test_source_control_depths_case_and_explicit_exclusions_preserve_literal_inventory(
    tmp_path: Path, source: bool, nominated: str, package_root: str, source_files: tuple[str, ...]
) -> None:
    root = tmp_path / nominated
    contents = {
        "plain.txt": b"public input",
        "build": b"root packaging control",
        "kept.egg-info/PKG-INFO": b"authored root metadata",
        "nested/build": b"authored nested input",
        f"{package_root}/owned.egg-info/PKG-INFO": b"direct package metadata",
        f"{package_root}/fixtures/owned.egg-info/PKG-INFO": b"authored package fixture",
        "__pycache__/ignored.py": b"root cache",
        "nested/__pycache__/ignored.py": b"nested cache",
        "nested/cache.pyc": b"compiled cache",
        "excluded subtree/input.txt": b"explicitly excluded tree",
        "nested/drop.name": b"explicitly excluded name",
    }
    for name, content in contents.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    rows = tree_records(
        root,
        source=source,
        excluded_roots=frozenset({root.absolute(), (root / "excluded subtree").absolute()}),
        excluded_names=frozenset({"drop.name"}),
    )
    assert rows[0] == (".", "directory", "")
    expected = source_files if source else tuple(contents)[:-2]
    assert {name: digest for name, kind, digest in rows if kind == "file"} == {
        "./" + name: hashlib.sha256(contents[name]).hexdigest() for name in expected
    }


@pytest.mark.parametrize("name", ["build", "dist"])
def test_packaging_controls_do_not_hide_explicit_consumed_inputs(tmp_path: Path, name: str) -> None:
    root = tmp_path / "project"
    root.mkdir()
    original = paths_digest((root,), source=True)
    package = root / name
    package.mkdir()
    payload = package / "model.py"
    payload.write_text("value = 1\n", encoding="utf-8")
    assert paths_digest((root,), source=True) == original
    consumed = paths_digest((package,), source=True)
    payload.write_text("value = 2\n", encoding="utf-8")
    assert paths_digest((root,), source=True) == original
    assert paths_digest((package,), source=True) != consumed


def test_cached_path_replaced_by_symlink_is_refused(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.write_text("public", encoding="utf-8")
    _recorded_hash(source)
    outside = tmp_path / "outside"
    outside.write_text("private sentinel", encoding="utf-8")
    source.unlink()
    source.symlink_to(outside)
    with pytest.raises(ValueError, match="symlink"):
        tree_records(source)
    assert outside.read_text() == "private sentinel"


def test_symlink_ancestor_cannot_admit_external_content(tmp_path: Path) -> None:
    source = tmp_path / "public"
    source.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "model.py").write_text("private sentinel", encoding="utf-8")
    (source / "linked").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        tree_records(source / "linked" / "model.py")
    assert (outside / "model.py").read_text() == "private sentinel"
    ancestor = tmp_path.resolve(strict=True) / "search-only"
    selected = ancestor / "selected"
    selected.mkdir(parents=True)
    item = selected / "model.py"
    content = b"readable selected Source bytes\n"
    item.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()
    if os.name == "posix" and os.geteuid() != 0:
        ancestor.chmod(0o111)
        try:
            with pytest.raises(PermissionError):
                list(ancestor.iterdir())
            if hasattr(os, "O_PATH"):
                assert _recorded_hash(item) == expected
                assert tree_records(selected) == ((".", "directory", ""), ("./model.py", "file", expected))
            else:
                with pytest.raises(ValueError, match="ancestor") as refusal:
                    tree_records(item)
                assert isinstance(refusal.value.__cause__, PermissionError)
        finally:
            ancestor.chmod(0o755)
        selected.chmod(0o111)
        try:
            with anchored_parent(selected) as parent:
                assert parent is not None
                with pytest.raises(ValueError, match="non-directory component") as refusal:
                    with open_directory(parent, selected.name):
                        pytest.fail("unreadable nominated Source directory was admitted")
                assert isinstance(refusal.value.__cause__, PermissionError)
            with pytest.raises(ValueError, match="non-directory component") as refusal:
                tree_records(selected)
            assert isinstance(refusal.value.__cause__, PermissionError)
        finally:
            selected.chmod(0o755)
    not_directory = ancestor / "not-directory"
    not_directory.write_bytes(b"a file cannot be an ancestor")
    with pytest.raises(ValueError, match="non-directory ancestor"):
        tree_records(not_directory / "model.py")
    with pytest.raises(ValueError, match="directory changed"):
        with anchored_parent(item) as parent:
            assert parent is not None
            with open_directory(parent, ".") as directory:
                assert os.fstat(directory).st_ino == selected.stat().st_ino
                with os.scandir(directory) as entries:
                    assert [entry.name for entry in entries] == ["model.py"]
            selected.rename(ancestor / "held-selected")
            selected.mkdir()
            item.write_bytes(b"replacement selected Source bytes\n")
    assert _recorded_hash(item) == hashlib.sha256(b"replacement selected Source bytes\n").hexdigest() != expected


@pytest.mark.skipif(os.name != "posix", reason="FIFO is a POSIX filesystem control")
def test_fifo_cannot_be_admitted_as_fingerprint_content(tmp_path: Path) -> None:
    source = tmp_path / "pipe"
    os.mkfifo(source)
    with pytest.raises(ValueError, match="Unsupported content type"):
        tree_records(source)


def _source_oracle(repo_root: Path, project: Path) -> str:
    """Independently reconstruct the original complete source payload."""
    from infrastructure.core.pipeline import fingerprints

    implementation = Path(fingerprints.__file__).resolve().parents[2]
    roots = [repo_root / "infrastructure", repo_root / "scripts", project]
    if implementation != (repo_root / "infrastructure").resolve():
        roots.append(implementation)
    roots.extend(repo_root / name for name in ("pyproject.toml", "uv.lock", ".python-version", "pipeline.yaml"))
    return paths_digest(tuple(roots), source=True, excluded_roots=frozenset({(project / "output").absolute()}))


@pytest.mark.parametrize("source", [False, True])
def test_literal_unusual_names_follow_actual_runtime_suffix_rules(tmp_path: Path, source: bool) -> None:
    """Retain authored dot/case/Unicode names under the selected Python minor."""
    root = tmp_path / "source é\nroot"
    root.mkdir()
    names = (
        ".pyc",
        "..pyc",
        "...pyc",
        ".pyo",
        "..pyo",
        "...pyo",
        ".hidden.pyc",
        "..hidden.pyo",
        "ordinary.pyc",
        "ordinary.pyo",
        "uppercase.PYC",
        "uppercase.PYO",
        "trailing.pyc.",
        "trailing.pyo.",
        "é.pyc",
        "é.pyo",
        "line\n.pyc",
        "line\n.PYO",
        "model.py",
        "drop\n.name",
    )
    for name in names:
        (root / name).write_bytes(name.encode())
    visited: list[Path] = []
    rows = tree_records(root, source=source, excluded_names=frozenset({"drop\n.name"}), path_admission=visited.append)
    admitted = sorted(
        name for name in names if name != "drop\n.name" and not (source and Path(name).suffix in {".pyc", ".pyo"})
    )
    assert rows == (
        (".", "directory", ""),
        *(("./" + name, "file", hashlib.sha256(name.encode()).hexdigest()) for name in admitted),
    )
    assert visited == [root, *(root / name for name in admitted)]


def test_path_admission_still_observes_selected_paths_and_detects_new_directory_entries(tmp_path: Path) -> None:
    root = tmp_path / "source"
    root.mkdir()
    (root / "observed.py").write_text("original")
    excluded = root / "excluded"
    excluded.symlink_to(tmp_path / "never-consumed")
    visited: list[Path] = []

    def consume(path: Path) -> None:
        visited.append(path)
        if path.name == "observed.py":
            (root / "added.py").write_text("new entry during admission")

    with pytest.raises(ValueError, match="contents changed"):
        tree_records(root, excluded_roots=frozenset({excluded}), path_admission=consume)
    assert visited == [root, root / "observed.py"]
    assert excluded.is_symlink()


@pytest.mark.parametrize("nominated_root", ["actual-implementation", "separate-owned-root"])
def test_single_boundary_tree_rows_preserve_source_payload_and_every_fresh_observation(
    tmp_path: Path, nominated_root: str
) -> None:
    from infrastructure.core.pipeline import fingerprints

    implementation = Path(fingerprints.__file__).resolve().parents[2]
    root = implementation.parent if nominated_root == "actual-implementation" else tmp_path / "root"
    project = tmp_path / "project"
    (project / "src").mkdir(parents=True)
    source = project / "src/model.py"
    source.write_text("result = 1\n")
    expected = _source_oracle(root, project)
    original = sys.getprofile()
    counts: Counter[str] = Counter()
    code = fingerprints.tree_records.__code__

    def observe(frame: FrameType, event: str, argument: object) -> None:
        if event == "call" and frame.f_code is code:
            counts[str(frame.f_locals["path"].absolute())] += 1
        if original is not None:
            original(frame, event, argument)

    try:
        sys.setprofile(observe)
        first = fingerprints.source_content_fingerprint(root, project)
    finally:
        sys.setprofile(original)
    assert first == expected
    assert counts[str(implementation)] == 1
    assert counts[str(implementation.parent / "scripts")] == 1
    source.write_text("result = 2\n")
    second_expected = _source_oracle(root, project)
    try:
        sys.setprofile(observe)
        second = fingerprints.source_content_fingerprint(root, project)
    finally:
        sys.setprofile(original)
    assert second == second_expected and second != first
    assert counts[str(implementation)] == 2
    assert counts[str(implementation.parent / "scripts")] == 2
    assert fingerprints.verify_loaded_implementation() is None


def test_explicit_project_output_exclusion_is_preserved_when_it_overlaps_loaded_source() -> None:
    from infrastructure.core.pipeline import fingerprints

    implementation = Path(fingerprints.__file__).resolve().parents[2]
    assert fingerprints.source_content_fingerprint(implementation.parent, implementation) == _source_oracle(
        implementation.parent, implementation
    )


@pytest.mark.parametrize("mutation", ["bytes", "addition", "removal", "rename", "link"])
@pytest.mark.timeout(180)
def test_next_boundary_refuses_actual_changed_loaded_source_after_prior_matching_payload(
    tmp_path: Path, mutation: str
) -> None:
    import shutil

    from infrastructure.core.pipeline import fingerprints
    from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy
    from infrastructure.core.execution_boundary import build_bounded_env

    original = Path(fingerprints.__file__).resolve().parents[3]
    owned = tmp_path / "provider"
    shutil.copytree(
        original / "infrastructure",
        owned / "infrastructure",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".venv", ".git"),
    )
    shutil.copytree(original / "scripts", owned / "scripts", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name in ("pyproject.toml", "uv.lock", ".python-version"):
        shutil.copyfile(original / name, owned / name)
    (owned / "infrastructure/config/owned-source-control.txt").write_text("source first\n")
    outside = tmp_path / "external-sentinel"
    outside.write_text("private invented sentinel\n")
    code = (
        "import sys\nfrom pathlib import Path\n"
        f"sys.path.insert(0,{str(owned)!r})\n"
        "from infrastructure.core.pipeline.fingerprints import source_content_fingerprint\n"
        f"root=Path({str(owned)!r});project=root/'projects/demo'\n"
        "(project/'src').mkdir(parents=True);(project/'src/model.py').write_text('result=1\\n')\n"
        "first=source_content_fingerprint(root,project)\n"
        "target=root/'infrastructure/config/owned-source-control.txt'\n"
        f"mutation={mutation!r}\n"
        "if mutation=='bytes':target.write_text('source changed\\n')\n"
        "elif mutation=='addition':target.with_name('added-source.yml').write_text('value: 2\\n')\n"
        "elif mutation=='removal':target.unlink()\n"
        "elif mutation=='rename':target.rename(target.with_name('renamed-source.yml'))\n"
        f"else:target.unlink();target.symlink_to({str(outside)!r})\n"
        "try:source_content_fingerprint(root,project)\n"
        "except ValueError as error:\n"
        "    assert 'changed after import' in str(error) or 'symlink' in str(error)\n"
        "    print('actual-current-source-refused')\n"
        "else:raise AssertionError('changed loaded source accepted by next boundary')\n"
    )
    result = run_with_policy(
        [sys.executable, "-I", "-B", "-c", code],
        cwd=owned,
        env=build_bounded_env(),
        policy=SubprocessPolicy(
            policy_id="source-observation-next-boundary",
            source_path="tests/infra_tests/core/pipeline/test_fingerprint_observations.py",
            timeout_seconds=120,
            credential_free=True,
        ),
    )
    assert result.returncode == result.original_returncode == 0, result.stderr
    assert not result.timed_out and not result.custody_refused
    assert "actual-current-source-refused" in result.stdout
    assert outside.read_text() == "private invented sentinel\n"


def test_declared_lean_build_is_runtime_without_hiding_nested_authored_inputs(tmp_path: Path) -> None:
    from infrastructure.core.pipeline.fingerprint_files import declared_lean_runtime_roots
    from infrastructure.core.pipeline.fingerprints import source_content_fingerprint

    repository = Path(__file__).resolve().parents[4]
    project = tmp_path / "project"
    lean = project / "lean"
    lean.mkdir(parents=True)
    (lean / "lakefile.lean").write_text("import Lake\nopen Lake DSL\npackage Owned where\n")
    (lean / "lean-toolchain").write_text("leanprover/lean4:v4.35.0\n")
    (lean / "lake-manifest.json").write_text('{"packages": []}\n')
    (lean / "Model.lean").write_text("theorem owned : True := True.intro\n")
    before = source_content_fingerprint(repository, project)
    generated = lean / ".lake/build/lib/Model.olean"
    generated.parent.mkdir(parents=True)
    generated.write_bytes(b"owned compiled output")
    assert declared_lean_runtime_roots(project) == frozenset({lean / ".lake"})
    assert source_content_fingerprint(repository, project) == before
    generated.write_bytes(b"rebuilt compiled output")
    assert source_content_fingerprint(repository, project) == before
    # Generic trees still observe the name; only the declared project boundary
    # classifies this exact build root as runtime.
    assert any(".lake" in row[0] for row in tree_records(project, source=True))
    authored = project / "data/.lake/model.py"
    authored.parent.mkdir(parents=True)
    authored.write_text("measurement = 1\n")
    assert source_content_fingerprint(repository, project) != before


@pytest.mark.parametrize("link", ["declaration", "ancestor"])
def test_declared_lean_runtime_refuses_symbolic_source_components(tmp_path: Path, link: str) -> None:
    from infrastructure.core.pipeline.fingerprint_files import declared_lean_runtime_roots

    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "lakefile.lean").write_text("outside Source must not be selected\n")
    if link == "ancestor":
        (project / "lean").symlink_to(outside, target_is_directory=True)
    else:
        (project / "lean").mkdir()
        (project / "lean/lakefile.lean").symlink_to(outside / "lakefile.lean")
    with pytest.raises(ValueError, match="symlink|no-follow"):
        declared_lean_runtime_roots(project)
    assert (outside / "lakefile.lean").read_text() == "outside Source must not be selected\n"
