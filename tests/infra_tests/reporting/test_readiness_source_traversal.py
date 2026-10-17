"""Exact metadata pruning preserves logical identity and real traversal custody."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.core.pipeline.fingerprints import paths_digest, tree_records
from infrastructure.core.pipeline.fingerprint_files import digest_path
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.readiness_receipts import (
    _public_roots,
    deliverable_identity,
    project_source_identity,
    public_source_paths,
    source_fingerprint,
)

_NAMES = frozenset({".DS_Store"})
_SCOPE = "templates/template_code_project"


@pytest.mark.parametrize("traversal", [False, True])
def test_deliverable_identity_refuses_outside_project_scope(tmp_path: Path, traversal: bool) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "outside"
    (outside / "output").mkdir(parents=True)
    sentinel = outside / "output/result.txt"
    sentinel.write_bytes(b"outside evidence must stay outside")
    (root / "projects").mkdir()
    scope = "../../outside" if traversal else str(outside)
    with pytest.raises(ValueError, match="confined|confinement"):
        deliverable_identity(root, scope)
    assert sentinel.read_bytes() == b"outside evidence must stay outside"


def test_bounded_digest_reobserves_same_size_bytes_even_with_restored_mtime(tmp_path: Path) -> None:
    path = tmp_path / "observed.bin"
    path.write_bytes(b"original")
    original = path.stat()
    assert digest_path(tmp_path, path, max_bytes=8) == hashlib.sha256(b"original").hexdigest()
    assert digest_path(tmp_path, path, max_bytes=8) == hashlib.sha256(b"original").hexdigest()
    path.write_bytes(b"replaced")
    os.utime(path, ns=(original.st_atime_ns, original.st_mtime_ns))
    assert digest_path(tmp_path, path, max_bytes=8) == hashlib.sha256(b"replaced").hexdigest()
    with pytest.raises(ValueError, match="read budget"):
        digest_path(tmp_path, path, max_bytes=7)


@pytest.mark.parametrize("ancestor", [False, True])
def test_bounded_digest_refuses_symlink_after_warm_observation(tmp_path: Path, ancestor: bool) -> None:
    directory = tmp_path / "current"
    directory.mkdir()
    path = directory / "observed.bin"
    path.write_bytes(b"original")
    digest_path(tmp_path, path, max_bytes=8)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / path.name).write_bytes(b"outside!")
    if ancestor:
        directory.rename(tmp_path / "held-original")
        directory.symlink_to(outside, target_is_directory=True)
    else:
        path.unlink()
        path.symlink_to(outside / path.name)
    with pytest.raises(ValueError, match="symlink|regular file"):
        digest_path(tmp_path, path, max_bytes=8)
    assert (outside / path.name).read_bytes() == b"outside!"


def _source(root: Path) -> Path:
    source = root / "source"
    (source / "nested/empty").mkdir(parents=True)
    (source / "empty").mkdir()
    for name, content in (
        ("flat.py", b"flat = 1\n"),
        ("nested/deep.py", b"deep = 2\n"),
        (".DS_Store.py", b"authored = 3\n"),
        (".DS_Store", b"root finder metadata"),
        ("nested/.DS_Store", b"nested finder metadata"),
    ):
        (source / name).write_bytes(content)
    return source


def _public(root: Path) -> Path:
    source = root / "projects" / _SCOPE / "src"
    (source / "nested").mkdir(parents=True)
    (source / "model.py").write_text("model = 1\n")
    (source / "nested/model.py").write_text("nested = 2\n")
    (source / ".DS_Store").write_bytes(b"invented metadata")
    (source / "nested/.DS_Store").write_bytes(b"nested invented metadata")
    (root / "README.md").write_text("Invented public fixture.\n")
    return source


def _explicit_reference(root: Path) -> tuple[tuple[Path, ...], frozenset[Path]]:
    """Small owned fixture oracle for the previous exact-path exclusion policy."""
    roots, excluded = _public_roots(root)
    metadata = {
        path.absolute()
        for boundary in roots
        if boundary.is_dir()
        for path in boundary.rglob("*")
        if path.name == ".DS_Store"
    }
    return roots, excluded | frozenset(metadata)


def _reference_fingerprint(root: Path) -> str:
    roots, excluded = _explicit_reference(root)
    payload = {
        "sources": paths_digest(roots, source=True, excluded_roots=excluded),
        "deliverables": {scope: deliverable_identity(root, scope) for scope in PUBLIC_PROJECT_NAMES},
    }
    # Serialize/hash independently instead of invoking the production digest helper.
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def test_exact_name_pruning_has_independent_record_and_hash_parity(tmp_path: Path) -> None:
    source = _source(tmp_path)
    expected = (
        (".", "directory", ""),
        ("./.DS_Store.py", "file", hashlib.sha256(b"authored = 3\n").hexdigest()),
        ("./empty", "directory", ""),
        ("./flat.py", "file", hashlib.sha256(b"flat = 1\n").hexdigest()),
        ("./nested", "directory", ""),
        ("./nested/deep.py", "file", hashlib.sha256(b"deep = 2\n").hexdigest()),
        ("./nested/empty", "directory", ""),
    )
    explicit = frozenset((source / ".DS_Store", source / "nested/.DS_Store"))
    assert tree_records(source, source=True, excluded_names=_NAMES) == expected
    assert tree_records(source, source=True, excluded_roots=explicit) == expected
    encoded = json.dumps([("source", expected)], sort_keys=True, separators=(",", ":")).encode()
    assert paths_digest((source,), source=True, excluded_names=_NAMES) == hashlib.sha256(encoded).hexdigest()


@pytest.mark.parametrize("nested", [False, True])
def test_authored_add_delete_and_rename_remain_bound(tmp_path: Path, nested: bool) -> None:
    source = _source(tmp_path)
    directory = source / "nested" if nested else source
    original = paths_digest((source,), source=True, excluded_names=_NAMES)
    extra = directory / "new.py"
    extra.write_bytes(b"new input")
    added = paths_digest((source,), source=True, excluded_names=_NAMES)
    assert added != original
    extra.rename(directory / "renamed.py")
    renamed = paths_digest((source,), source=True, excluded_names=_NAMES)
    assert renamed != added and renamed != original
    (directory / "renamed.py").unlink()
    assert paths_digest((source,), source=True, excluded_names=_NAMES) == original


def test_only_exact_metadata_names_change_readiness_behavior(tmp_path: Path) -> None:
    source = _source(tmp_path)
    metadata = source / ".DS_Store"
    ignored = paths_digest((source,), source=True, excluded_names=_NAMES)
    default = paths_digest((source,), source=True)
    metadata.write_bytes(b"changed actual metadata")
    assert paths_digest((source,), source=True, excluded_names=_NAMES) == ignored
    assert paths_digest((source,), source=True) == default
    neighbor = source / ".DS_Store.py"
    neighbor.write_bytes(b"changed authored source")
    assert paths_digest((source,), source=True, excluded_names=_NAMES) != ignored
    scope_source = _public(tmp_path)
    before = project_source_identity(tmp_path, _SCOPE)
    (scope_source / ".DS_Store").write_bytes(b"changed Finder metadata remains outside source identity")
    assert project_source_identity(tmp_path, _SCOPE) == before
    (scope_source / ".DS_Store.py").write_bytes(b"authored neighboring source stays bound")
    assert project_source_identity(tmp_path, _SCOPE) != before


def test_public_inventory_and_fingerprint_match_explicit_path_oracle(tmp_path: Path) -> None:
    source = _public(tmp_path)
    metadata_dir = source / "nested/.DS_Store"
    metadata_dir.unlink()
    metadata_dir.mkdir()
    (metadata_dir / "payload.py").write_text("unconsumed metadata directory\n")
    metadata_link = source / ".DS_Store"
    metadata_link.unlink()
    outside = tmp_path / "outside-metadata"
    outside.write_bytes(b"invented unconsumed sentinel")
    metadata_link.symlink_to(outside)
    previous = source_fingerprint(tmp_path)
    assert previous == _reference_fingerprint(tmp_path)
    roots, excluded = _explicit_reference(tmp_path)
    expected_paths = {
        boundary if relative == "." else boundary / relative
        for boundary in roots
        for relative, kind, _ in tree_records(boundary, source=True, excluded_roots=excluded)
        if kind == "file"
    }
    assert public_source_paths(tmp_path) == tuple(sorted(expected_paths))
    for name in ("new.py", "nested/new.py"):
        path = source / name
        path.write_bytes(b"real new input")
        current = source_fingerprint(tmp_path)
        assert current != previous and current == _reference_fingerprint(tmp_path)
        renamed = path.with_name("renamed.py")
        path.rename(renamed)
        next_identity = source_fingerprint(tmp_path)
        assert next_identity != current and next_identity == _reference_fingerprint(tmp_path)
        renamed.unlink()
        assert source_fingerprint(tmp_path) == previous == _reference_fingerprint(tmp_path)
    assert outside.read_bytes() == b"invented unconsumed sentinel"


def _child(root: Path, body: str) -> subprocess.CompletedProcess[str]:
    import infrastructure

    assert infrastructure.__file__ is not None
    sdk = Path(infrastructure.__file__).resolve().parent.parent
    prefix = root / "owned-bytecode"
    bootstrap = (
        "import os,sys,json\nfrom pathlib import Path\n"
        "sys.dont_write_bytecode=True\n"
        "sys.pycache_prefix=str(Path(sys.argv[2])/'owned-bytecode')\n"
        "sys.path.insert(0,sys.argv[1])\n"
        "import infrastructure\n"
        "assert Path(infrastructure.__file__).resolve()==Path(sys.argv[1])/'infrastructure/__init__.py'\n"
        "root=Path(sys.argv[2])\n"
    )
    assert not prefix.exists()
    environment = dict(os.environ)
    environment.pop("PYTEST_CURRENT_TEST", None)
    return subprocess.run(
        [sys.executable, "-I", "-c", bootstrap + body, str(sdk), str(root)],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
    )


@pytest.mark.timeout(90)
@pytest.mark.parametrize("runtime", [".venv", ".lake", "node_modules", "output"])
def test_public_source_inventory_never_traverses_exact_runtime_boundary(tmp_path: Path, runtime: str) -> None:
    _public(tmp_path)
    boundary = tmp_path / "projects" / _SCOPE / runtime
    (boundary / "deep").mkdir(parents=True)
    sentinel = boundary / "deep/sentinel.py"
    sentinel.write_bytes(b"runtime byte sentinel; never consumed")
    body = f"""
from infrastructure.reporting.readiness_receipts import public_source_paths
boundary=root/'projects/{_SCOPE}/{runtime}'
metadata=boundary.stat();blocked=(metadata.st_dev,metadata.st_ino)
events=[]
def audit(event,args):
    if event not in ('os.scandir','os.listdir') or not args: return
    value=args[0]
    if type(value) is int:
        observed=os.fstat(value); forbidden=(observed.st_dev,observed.st_ino)==blocked
    elif isinstance(value,(str,bytes,os.PathLike)):
        forbidden=Path(os.fsdecode(value)).absolute().is_relative_to(boundary)
    else: forbidden=False
    if forbidden:
        events.append(event)
        raise AssertionError('actual traversal entered excluded runtime boundary')
sys.addaudithook(audit)
paths=public_source_paths(root,'{_SCOPE}')
assert not events
assert root/'projects/{_SCOPE}/src/model.py' in paths
assert not any(path.is_relative_to(boundary) for path in paths)
print(json.dumps({{'runtime':'{runtime}','forbidden_traversals':len(events),'files':len(paths)}}))
"""
    child = _child(tmp_path, body)
    assert child.returncode == 0, child.stdout + child.stderr
    result = json.loads(child.stdout)
    assert result["forbidden_traversals"] == 0 and result["files"] >= 2
    assert sentinel.read_bytes() == b"runtime byte sentinel; never consumed"


@pytest.mark.timeout(90)
@pytest.mark.parametrize("mutation", ["addition", "deletion", "rename", "directory-substitution"])
def test_real_directory_mutation_during_filtered_traversal_is_rejected(tmp_path: Path, mutation: str) -> None:
    source = _source(tmp_path)
    body = f"""
from infrastructure.core.pipeline.fingerprints import tree_records
source=root/'source';target=source/'nested'
metadata=target.stat();identity=(metadata.st_dev,metadata.st_ino)
count=0;mutated=False
def audit(event,args):
    global count,mutated
    if event!='os.listdir' or not args or type(args[0]) is not int: return
    observed=os.fstat(args[0])
    if (observed.st_dev,observed.st_ino)!=identity: return
    count+=1
    if count!=2: return
    mutated=True
    action={mutation!r}
    if action=='addition': (target/'added.py').write_text('real new input')
    elif action=='deletion': (target/'deep.py').unlink()
    elif action=='rename': (target/'deep.py').rename(target/'renamed.py')
    else:
        target.rename(source/'held-original');target.mkdir()
sys.addaudithook(audit)
try:
    tree_records(source,source=True,excluded_names=frozenset({{'.DS_Store'}}))
except ValueError as exc:
    assert mutated and 'Fingerprint directory' in str(exc)
    print(json.dumps({{'mutation':{mutation!r},'refused':True}}))
else: raise AssertionError('real directory mutation was accepted')
"""
    child = _child(tmp_path, body)
    assert child.returncode == 0, child.stdout + child.stderr
    assert json.loads(child.stdout) == {"mutation": mutation, "refused": True}
    if mutation == "directory-substitution":
        assert (source / "held-original/deep.py").read_bytes() == b"deep = 2\n"


@pytest.mark.parametrize("ancestor", [False, True])
def test_unexcluded_symlinks_are_still_rejected(tmp_path: Path, ancestor: bool) -> None:
    source = _source(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "sentinel.py"
    sentinel.write_bytes(b"unconsumed outside source")
    link = source / "linked"
    link.symlink_to(outside if ancestor else sentinel, target_is_directory=ancestor)
    nominated = link / "sentinel.py" if ancestor else source
    with pytest.raises(ValueError, match="symlink"):
        tree_records(nominated, source=True, excluded_names=_NAMES)
    assert sentinel.read_bytes() == b"unconsumed outside source"


@pytest.mark.timeout(90)
@pytest.mark.parametrize("relative", ["bin", "lib", "obj", "logger/obj", "utils/obj"])
def test_local_kmyth_build_products_are_pruned_without_hiding_authored_sources(tmp_path: Path, relative: str) -> None:
    _public(tmp_path)
    kmyth = tmp_path / "infrastructure/steganography/kmyth"
    boundary = kmyth / relative
    (boundary / "deep").mkdir(parents=True)
    sentinel = boundary / "deep/local-native-product"
    sentinel.write_bytes(b"owned runtime sentinel")
    authored = [
        kmyth / "src/main/seal.c",
        kmyth / "include/seal.h",
        kmyth / "test/fixture.json",
        kmyth / "src/lib/authored.c",
        tmp_path / "infrastructure/another/bin/authored.py",
    ]
    for path in authored:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"authored input\n")
    before = source_fingerprint(tmp_path)
    sentinel.write_bytes(b"changed owned runtime sentinel")
    assert source_fingerprint(tmp_path) == before
    paths = public_source_paths(tmp_path)
    assert all(path in paths for path in authored)
    for path in authored:
        original = path.read_bytes()
        path.write_bytes(original + b"actual source mutation\n")
        assert source_fingerprint(tmp_path) != before
        path.write_bytes(original)
        assert source_fingerprint(tmp_path) == before
    body = f"""
from infrastructure.reporting.readiness_receipts import public_source_paths,source_fingerprint
boundary=root/'infrastructure/steganography/kmyth/{relative}'
observed=boundary.stat();blocked=(observed.st_dev,observed.st_ino)
events=[]
def audit(event,args):
    if event not in ('os.scandir','os.listdir','open') or not args: return
    value=args[0]
    if type(value) is int:
        metadata=os.fstat(value);forbidden=(metadata.st_dev,metadata.st_ino)==blocked
    elif isinstance(value,(str,bytes,os.PathLike)):
        forbidden=Path(os.fsdecode(value)).absolute().is_relative_to(boundary)
    else: forbidden=False
    if forbidden:
        events.append(event)
        raise AssertionError('actual traversal or read entered a local build directory')
sys.addaudithook(audit)
paths=public_source_paths(root)
assert root/'infrastructure/steganography/kmyth/src/main/seal.c' in paths
assert not any(path.is_relative_to(boundary) for path in paths)
source_fingerprint(root)
assert not events
print(json.dumps({{'forbidden_operations':len(events)}}))
"""
    child = _child(tmp_path, body)
    assert child.returncode == 0, child.stdout + child.stderr
    assert json.loads(child.stdout) == {"forbidden_operations": 0}
    assert sentinel.read_bytes() == b"changed owned runtime sentinel"
