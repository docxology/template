"""Real source/distribution and poisoned-cache controls; no provider substitution."""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import os
import py_compile
import shutil
import subprocess
import sys
import time
import venv
from pathlib import Path

import pytest

from infrastructure.core.implementation_custody import _regular_bytes, bytecode_audit_bootstrap, source_file_manifest

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("wrong_identity", [False, True])
def test_source_only_platform_identity_is_checked_without_distribution_metadata(
    tmp_path: Path, wrong_identity: bool
) -> None:
    runtime = tmp_path / "empty-runtime"
    venv.EnvBuilder(with_pip=False).create(runtime)
    platform = tmp_path.resolve() / "source-platform"
    shutil.copytree(ROOT / "infrastructure", platform / "infrastructure", ignore=shutil.ignore_patterns("__pycache__"))
    for name in ("pyproject.toml", "uv.lock", ".python-version"):
        shutil.copy2(ROOT / name, platform / name)
    if wrong_identity:
        metadata = platform / "pyproject.toml"
        metadata.write_text(
            metadata.read_text().replace('name = "research-project-template"', 'name = "wrong-platform"')
        )
    code = """
import sys
from importlib.metadata import PackageNotFoundError, distribution
sys.path.insert(0,sys.argv[1])
try:
    distribution('research-project-template')
except PackageNotFoundError:
    pass
else:
    raise AssertionError('control must not inherit installed platform metadata')
from infrastructure.core.implementation_custody import capture_implementation_custody
observation=capture_implementation_custody()
assert observation['binding_kind']=='source-checkout'
assert observation['distribution'] is None
print('actual metadata-absent platform admitted')
"""
    result = subprocess.run(
        [str(runtime / "bin/python"), "-I", "-c", code, str(platform)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if wrong_identity:
        assert (
            result.returncode != 0
            and "checkout package identity disagrees with loaded platform identity" in result.stderr
        )
        assert "actual metadata-absent platform admitted" not in result.stdout
    else:
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "actual metadata-absent platform admitted"


@pytest.mark.parametrize("fault", [None, "duplicate", "metadata", "version", "record", "symlink"])
def test_checkout_uses_unique_actual_installed_metadata_despite_generated_source_egg_info(
    tmp_path: Path, fault: str | None
) -> None:
    """Exercise real editable metadata in an empty same-ABI owned environment."""
    runtime = tmp_path / "runtime"
    venv.EnvBuilder(with_pip=False).create(runtime)
    python = runtime / "bin/python"
    site = Path(
        subprocess.check_output(
            [str(python), "-I", "-c", "import sysconfig;print(sysconfig.get_path('purelib'))"], text=True
        ).strip()
    )
    checkout = tmp_path / "checkout"
    source = checkout / "src/canonical_engine"
    source.mkdir(parents=True)
    (source / "__init__.py").write_text("VALUE = 7\n")
    (checkout / "pyproject.toml").write_text('[project]\nname="canonical-engine"\nversion="0.2.0"\n')
    (checkout / "uv.lock").write_text("version = 1\n")
    egg = checkout / "src/canonical_engine.egg-info"
    egg.mkdir()
    pkg_info = "Metadata-Version: 2.3\nName: canonical-engine\nVersion: 0.2.0\n"
    (egg / "PKG-INFO").write_text(pkg_info)
    (egg / "SOURCES.txt").write_text("README.md\n")
    editable = site / "canonical_engine.pth"
    editable.write_text(str(source.parent) + "\n")
    metadata = site / "canonical_engine-0.2.0.dist-info"
    metadata.mkdir()
    (metadata / "METADATA").write_text(pkg_info)
    if fault == "metadata":
        (metadata / "METADATA").write_text(pkg_info + "Name: wrong\n")
    elif fault == "version":
        (metadata / "METADATA").write_text(pkg_info.replace("0.2.0", "0.3.0"))

    def seal(directory: Path) -> None:
        output = io.StringIO()
        writer = csv.writer(output)
        for path in (editable, directory / "METADATA"):
            raw = path.read_bytes()
            digest = base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).decode().rstrip("=")
            writer.writerow([path.relative_to(site).as_posix(), "sha256=" + digest, len(raw)])
        writer.writerow([directory.relative_to(site).as_posix() + "/RECORD", "", ""])
        (directory / "RECORD").write_text(output.getvalue())

    seal(metadata)
    if fault == "duplicate":
        duplicate = site / "canonical_engine-0.2.1.dist-info"
        duplicate.mkdir()
        (duplicate / "METADATA").write_text(pkg_info.replace("0.2.0", "0.2.1"))
        seal(duplicate)
    elif fault == "record":
        editable.write_text(editable.read_text() + "# original bytes changed\n")
    elif fault == "symlink":
        external = tmp_path / "external-METADATA"
        (metadata / "METADATA").rename(external)
        (metadata / "METADATA").symlink_to(external)
    code = f"""
import sys,json
from pathlib import Path
from importlib.metadata import distribution
sys.path.insert(0,{str(ROOT)!r})
sys.path.insert(0,{str(source.parent)!r})
assert distribution('canonical-engine').read_text('PKG-INFO') == {pkg_info!r}
import canonical_engine
assert Path(canonical_engine.__file__).parent == Path({str(source)!r})
assert canonical_engine.VALUE == 7
from infrastructure.core.implementation_custody import capture_dependency_custody
value=capture_dependency_custody('canonical-engine',Path(canonical_engine.__file__).parent,
    checkout_root=Path({str(checkout)!r}))
assert value['binding_kind']=='source-checkout'
assert value['distribution']['version']=='0.2.0'
assert value['distribution']['record_sha256']
assert value['files']['__init__.py']
print('actual editable custody passed')
"""
    result = subprocess.run(
        [str(python), "-I", "-c", code], cwd=tmp_path, capture_output=True, text=True, timeout=30, check=False
    )
    if fault is None:
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "actual editable custody passed"
    else:
        assert result.returncode != 0
        reason = {
            "duplicate": "metadata is ambiguous",
            "metadata": "METADATA identity is ambiguous or inconsistent",
            "version": "checkout version differs from selected installed metadata",
            "record": "differs from its declared RECORD",
            "symlink": "Too many levels of symbolic links",
        }[fault]
        assert reason in result.stderr, result.stderr
        assert "actual editable custody passed" not in result.stdout


def installed_fixture(tmp_path: Path) -> Path:
    """Materialize actual minimal platform import closure and a valid RECORD."""
    site = tmp_path.resolve() / "installed"
    for name in (
        "__init__.py",
        "_version.py",
        "core/__init__.py",
        "core/pipeline/__init__.py",
        "core/pipeline/fingerprints.py",
        "core/pipeline/fingerprint_files.py",
        "core/implementation_custody.py",
        "core/bytecode_audit.py",
    ):
        target = site / "infrastructure" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "infrastructure" / name, target)
    (site / "infrastructure/custody_probe.py").write_text("VALUE = 1\n")
    metadata = site / "research_project_template-4.0.1.dist-info"
    metadata.mkdir()
    (metadata / "METADATA").write_text("Metadata-Version: 2.3\nName: research-project-template\nVersion: 4.0.1\n")
    update_record(site)
    return site


def update_record(site: Path) -> None:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    for path in sorted(site.rglob("*")):
        if path.is_file() and path.name != "RECORD" and "__pycache__" not in path.parts:
            raw = path.read_bytes()
            value = base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).decode().rstrip("=")
            writer.writerow([path.relative_to(site).as_posix(), "sha256=" + value, len(raw)])
    writer.writerow(["research_project_template-4.0.1.dist-info/RECORD", "", ""])
    (site / "research_project_template-4.0.1.dist-info/RECORD").write_text(buffer.getvalue())


def probe(
    site: Path, tmp_path: Path, code: str, *, fresh: bool = True, audit: bool = True
) -> subprocess.CompletedProcess:
    arguments = [sys.executable, "-I"]
    if fresh:
        prefix = tmp_path.resolve() / "fresh-cache"
        prefix.mkdir()
        arguments += ["-X", f"pycache_prefix={prefix}"]
    bootstrap = ""
    if fresh and audit:
        bootstrap = bytecode_audit_bootstrap((site,), prefix, audit_path=site / "infrastructure/core/bytecode_audit.py")
    bootstrap += "import sys;sys.path.insert(0,sys.argv.pop(1));" + code
    return subprocess.run(
        arguments + ["-c", bootstrap, str(site)], cwd=tmp_path.resolve(), capture_output=True, text=True, timeout=30
    )


def test_actual_installed_source_record_and_fresh_bytecode_are_bound(tmp_path):
    site = installed_fixture(tmp_path)
    result = probe(
        site,
        tmp_path,
        "import json;from pathlib import Path;from infrastructure.core.implementation_custody import "
        "capture_implementation_custody;print(json.dumps(capture_implementation_custody("
        "fresh_pycache_prefix=Path(sys.pycache_prefix))))",
    )
    assert result.returncode == 0, result.stderr
    receipt = json.loads(result.stdout)
    assert receipt["binding_kind"] == "installed-distribution"
    assert receipt["bytecode_binding"] == "fresh-owned-prefix"
    assert receipt["distribution"]["public_python"] == {
        name.removeprefix("infrastructure/"): digest for name, digest in receipt["files"].items()
    }
    assert not any(name in receipt["files"] for name in ("pyproject.toml", "uv.lock", ".python-version"))


@pytest.mark.parametrize("installed", [False, True])
def test_distribution_source_inventory_runs_only_for_its_installed_comparison(tmp_path, installed):
    """Profile the real helper; both metadata planes retain identical verified bytes."""
    site = installed_fixture(tmp_path)
    code = """
import json
from pathlib import Path
import infrastructure.core.implementation_custody as custody
prefix = Path(sys.pycache_prefix)
before = custody.capture_implementation_custody(fresh_pycache_prefix=prefix)
assert before['binding_kind'] == 'installed-distribution'
source = Path(custody.__file__).parent.parent
actual_code = custody._python_files.__code__
previous = sys.getprofile()
calls = 0
def observe(frame, event, argument):
    global calls
    if event == 'call' and frame.f_code is actual_code:
        calls += 1
    if previous is not None:
        previous(frame, event, argument)
try:
    sys.setprofile(observe)
    observed = custody._distribution_custody(source, installed=INSTALLED)
finally:
    sys.setprofile(previous)
assert observed == before['distribution']
assert observed['public_python'] == custody.source_file_manifest(source, frozenset({'.py'}))
assert custody.capture_implementation_custody(fresh_pycache_prefix=prefix) == before
assert sys.getprofile() is previous
print(json.dumps({'source_inventory_calls': calls, 'distribution_unchanged': True}))
""".replace("INSTALLED", repr(installed))
    result = probe(site, tmp_path, code)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"source_inventory_calls": int(installed), "distribution_unchanged": True}


@pytest.mark.parametrize("fault", [None, "modified", "extra", "metadata", "escape", "origin"])
def test_declared_dependency_uses_its_own_installed_record(tmp_path, fault):
    site = installed_fixture(tmp_path)
    source = site / "canonical_engine"
    source.mkdir()
    (source / "__init__.py").write_text("VALUE = 1\n")
    metadata = site / "canonical_engine-0.2.0.dist-info"
    metadata.mkdir()
    (metadata / "METADATA").write_text("Metadata-Version: 2.3\nName: canonical-engine\nVersion: 0.2.0\n")
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    for path in (source / "__init__.py", metadata / "METADATA"):
        raw = path.read_bytes()
        digest = base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).decode().rstrip("=")
        writer.writerow([path.relative_to(site).as_posix(), "sha256=" + digest, len(raw)])
    writer.writerow(["canonical_engine-0.2.0.dist-info/RECORD", "", ""])
    record = metadata / "RECORD"
    record.write_text(buffer.getvalue())
    if fault == "modified":
        (source / "__init__.py").write_text("VALUE = 9\n")
    elif fault == "extra":
        (source / "undeclared.py").write_text("VALUE = 9\n")
    elif fault == "metadata":
        (metadata / "METADATA").write_text((metadata / "METADATA").read_text() + "Name: wrong\n")
    elif fault == "escape":
        record.write_text(record.read_text() + "../escape.py,,\n")
    prefix = ""
    if fault == "origin":
        other = tmp_path / "other-provider"
        shutil.copytree(source, other / "canonical_engine")
        prefix = (
            "from importlib.metadata import distribution;"
            "assert distribution('canonical-engine').version == '0.2.0';"
            f"sys.path.insert(0,{str(other)!r});"
        )
    result = probe(
        site,
        tmp_path,
        prefix + "import canonical_engine,json;from pathlib import Path;"
        "from infrastructure.core.implementation_custody import capture_dependency_custody;"
        "print(json.dumps(capture_dependency_custody('canonical-engine',"
        "Path(canonical_engine.__file__).parent,fresh_pycache_prefix=Path(sys.pycache_prefix))))",
    )
    if fault is not None:
        assert result.returncode != 0
        if fault == "origin":
            assert (
                "MissingSelectedDistributionMetadata: installed implementation lacks selected distribution metadata"
                in result.stderr
            )
        else:
            assert "MissingSelectedDistributionMetadata" not in result.stderr
        return
    assert result.returncode == 0, result.stderr
    receipt = json.loads(result.stdout)
    assert receipt["binding_kind"] == "installed-distribution"
    assert receipt["distribution"]["name"] == "canonical-engine"
    assert receipt["distribution"]["public_python"] == receipt["files"]
    assert receipt["bytecode_binding"] == "fresh-owned-prefix"


def test_mutated_fresh_cache_is_rejected_without_decoding_its_body(tmp_path):
    site = installed_fixture(tmp_path)
    result = probe(
        site,
        tmp_path,
        "import infrastructure.custody_probe as p;from pathlib import Path;"
        "cache=Path(p.__cached__);raw=cache.read_bytes();cache.write_bytes(raw[:16]+b'not marshal data');"
        "from infrastructure.core.implementation_custody import capture_implementation_custody;"
        "capture_implementation_custody(fresh_pycache_prefix=Path(sys.pycache_prefix))",
    )
    assert result.returncode != 0 and "differs from execution-time bytes" in result.stderr


@pytest.mark.parametrize("fault", ["modified", "extra", "missing", "metadata", "escape", "duplicate", "symlink"])
def test_actual_installed_record_or_source_violation_is_rejected(tmp_path, fault):
    site = installed_fixture(tmp_path)
    source = site / "infrastructure/custody_probe.py"
    record = site / "research_project_template-4.0.1.dist-info/RECORD"
    if fault == "modified":
        source.write_text("VALUE = 2\n")
    elif fault == "extra":
        (site / "infrastructure/undeclared.py").write_text("VALUE = 1\n")
    elif fault == "missing":
        source.unlink()
    elif fault == "metadata":
        metadata = record.parent / "METADATA"
        metadata.write_text(metadata.read_text() + "Name: inconsistent\n")
    elif fault == "escape":
        record.write_text(record.read_text() + "../../secret.py,,\n")
    elif fault == "duplicate":
        record.write_text(record.read_text() + record.read_text().splitlines()[0] + "\n")
    else:
        outside = tmp_path / "outside.py"
        outside.write_bytes(source.read_bytes())
        source.unlink()
        source.symlink_to(outside)
    result = probe(
        site,
        tmp_path,
        "from pathlib import Path;from infrastructure.core.implementation_custody import capture_implementation_custody;"
        "capture_implementation_custody(fresh_pycache_prefix=Path(sys.pycache_prefix))",
    )
    assert result.returncode != 0
    assert "ModuleNotFoundError" not in result.stderr, result.stderr


def poison_timestamp_cache(source: Path) -> None:
    before = source.stat()
    source.write_text("VALUE = 9\n")
    os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns))
    py_compile.compile(str(source), doraise=True, invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP)
    source.write_text("VALUE = 1\n")
    os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns))


def test_real_poisoned_cache_executes_old_code_but_fresh_owned_prefix_reads_source(tmp_path):
    site = installed_fixture(tmp_path)
    poison_timestamp_cache(site / "infrastructure/custody_probe.py")
    old = probe(site, tmp_path, "from infrastructure.custody_probe import VALUE;print(VALUE)", fresh=False)
    assert old.returncode == 0 and old.stdout.strip() == "9"
    fresh = probe(
        site,
        tmp_path,
        "from infrastructure.custody_probe import VALUE;from pathlib import Path;"
        "from infrastructure.core.implementation_custody import capture_implementation_custody;"
        "capture_implementation_custody(fresh_pycache_prefix=Path(sys.pycache_prefix));print(VALUE)",
    )
    assert fresh.returncode == 0, fresh.stderr
    assert fresh.stdout.strip() == "1"


def test_setting_fresh_prefix_after_poisoned_import_cannot_certify_loaded_source(tmp_path):
    site = installed_fixture(tmp_path)
    poison_timestamp_cache(site / "infrastructure/custody_probe.py")
    prefix = tmp_path.resolve() / "late-prefix"
    prefix.mkdir()
    result = probe(
        site,
        tmp_path,
        "from infrastructure.custody_probe import VALUE;from pathlib import Path;"
        f"sys.pycache_prefix={str(prefix)!r};"
        "from infrastructure.core.implementation_custody import capture_implementation_custody;"
        "capture_implementation_custody(fresh_pycache_prefix=Path(sys.pycache_prefix))",
        fresh=False,
    )
    assert result.returncode != 0 and "pre-import executed-code audit" in result.stderr


def test_fresh_prefix_without_preimport_audit_cannot_certify_execution(tmp_path):
    site = installed_fixture(tmp_path)
    result = probe(
        site,
        tmp_path,
        "from pathlib import Path;from infrastructure.core.implementation_custody import capture_implementation_custody;"
        "capture_implementation_custody(fresh_pycache_prefix=Path(sys.pycache_prefix))",
        audit=False,
    )
    assert result.returncode != 0 and "pre-import executed-code audit" in result.stderr


def test_audited_timestamp_valid_poison_in_owned_prefix_fails_actual_code_binding(tmp_path):
    site = installed_fixture(tmp_path)
    result = probe(
        site,
        tmp_path,
        "import os,py_compile;from pathlib import Path;"
        "source=Path(sys.path[0])/'infrastructure/custody_probe.py';before=source.stat();"
        "source.write_text('VALUE = 9\\n');os.utime(source,ns=(before.st_atime_ns,before.st_mtime_ns));"
        "py_compile.compile(str(source),doraise=True,invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP);"
        "source.write_text('VALUE = 1\\n');"
        "os.utime(source,ns=(before.st_atime_ns,before.st_mtime_ns));"
        "from infrastructure.custody_probe import VALUE;assert VALUE==9;"
        "from infrastructure.core.implementation_custody import capture_implementation_custody;"
        "capture_implementation_custody(fresh_pycache_prefix=Path(sys.pycache_prefix))",
    )
    assert result.returncode != 0 and "executed public module differs from current source bytes" in result.stderr


def test_removed_module_still_binds_its_actual_executed_source(tmp_path):
    site = installed_fixture(tmp_path)
    marker = tmp_path / "removed-module-control-reached"
    result = probe(
        site,
        tmp_path,
        "from pathlib import Path;"
        "from infrastructure.custody_probe import VALUE;assert VALUE==1;"
        "del sys.modules['infrastructure.custody_probe'];"
        "source=Path(sys.path[0])/'infrastructure/custody_probe.py';source.write_text('VALUE = 9\\n');"
        f"Path({str(marker)!r}).write_text('actual module removed before final source check');"
        "_audit_scope['verify_executed_source_code'](source.parent,Path(sys.pycache_prefix))",
    )
    assert marker.read_text() == "actual module removed before final source check"
    assert result.returncode != 0 and "executed public module differs from current source bytes" in result.stderr


def test_no_follow_ancestry_and_bounded_file_reads(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "public.py").write_text("VALUE = 1\n")
    alias = tmp_path / "alias"
    alias.symlink_to(source, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        _regular_bytes(alias / "public.py")
    with pytest.raises(ValueError, match="bounded"):
        _regular_bytes(source / "public.py", max_bytes=1)


@pytest.mark.parametrize("kind", ["root", "ancestor", "directory", "in-root-cache"])
def test_source_directory_links_are_rejected_before_python_suffix_selection(tmp_path, kind):
    root = tmp_path.resolve() / "public"
    root.mkdir()
    (root / "safe.py").write_text("VALUE = 1\n")
    cache = tmp_path.resolve() / "cache"
    cache.mkdir()
    (cache / "used.py").write_text("VALUE = 17\n")
    if kind == "root":
        alias = tmp_path.resolve() / "alias"
        alias.symlink_to(root, target_is_directory=True)
        selected = alias
    elif kind == "ancestor":
        alias = tmp_path.resolve() / "alias"
        alias.symlink_to(tmp_path.resolve(), target_is_directory=True)
        selected = alias / "public"
    else:
        if kind == "in-root-cache":
            cache = root / "__pycache__"
            cache.mkdir()
            (cache / "used.py").write_text("VALUE = 17\n")
        (root / "domain").symlink_to(cache, target_is_directory=True)
        selected = root
    with pytest.raises(ValueError):
        source_file_manifest(selected, frozenset({".py"}))


def test_manifest_optional_limits_preserve_actual_default_inventory(tmp_path):
    root = tmp_path.resolve() / "source"
    (root / "nested").mkdir(parents=True)
    (root / "public.py").write_text("VALUE = 1\n")
    (root / "ignored.txt").write_text("public data\n")
    (root / "nested/used.py").write_text("VALUE = 2\n")
    ordinary = source_file_manifest(root, frozenset({".py"}))
    bounded = source_file_manifest(root, frozenset({".py"}), deadline=time.monotonic() + 5, max_entries=4, max_depth=1)
    assert (
        ordinary
        == bounded
        == {
            "public.py": hashlib.sha256(b"VALUE = 1\n").hexdigest(),
            "nested/used.py": hashlib.sha256(b"VALUE = 2\n").hexdigest(),
        }
    )


def test_manifest_width_counts_actual_nonselected_entries(tmp_path):
    root = tmp_path.resolve() / "wide"
    root.mkdir()
    for index in range(32):
        (root / f"{index:02}.txt").write_text("not Python\n")
    (root / "public.py").write_text("VALUE = 1\n")
    with pytest.raises(ValueError, match="entry ceiling"):
        source_file_manifest(root, frozenset({".py"}), max_entries=8)
    assert list(source_file_manifest(root, frozenset({".py"}))) == ["public.py"]


def test_manifest_depth_refuses_actual_nested_directory_before_suffix_selection(tmp_path):
    root = tmp_path.resolve() / "deep"
    directory = root
    for index in range(5):
        directory = directory / str(index)
        directory.mkdir(parents=True)
    (directory / "used.py").write_text("VALUE = 1\n")
    with pytest.raises(ValueError, match="depth ceiling"):
        source_file_manifest(root, frozenset({".py"}), max_depth=2)
    with pytest.raises(ValueError, match="depth ceiling"):
        source_file_manifest(root, frozenset({".txt"}), max_depth=0)


@pytest.mark.parametrize("missing", [False, True])
def test_manifest_expired_monotonic_deadline_refuses_actual_admission(tmp_path, missing):
    root = tmp_path.resolve() / "source"
    if not missing:
        root.mkdir()
        (root / "public.py").write_text("VALUE = 1\n")
    with pytest.raises(ValueError, match="deadline exhausted"):
        source_file_manifest(root, frozenset({".py"}), deadline=time.monotonic() - 1)


@pytest.mark.parametrize(
    "limits",
    [
        {"deadline": True},
        {"deadline": float("nan")},
        {"deadline": float("inf")},
        {"deadline": "tomorrow"},
        {"max_entries": True},
        {"max_entries": 0},
        {"max_entries": 1.5},
        {"max_entries": 1_000_001},
        {"max_depth": True},
        {"max_depth": -1},
        {"max_depth": 1.5},
        {"max_depth": 257},
    ],
)
def test_manifest_limits_require_exact_finite_types_before_admission(tmp_path, limits):
    with pytest.raises(ValueError, match="must be"):
        source_file_manifest(tmp_path.resolve() / "absent", frozenset({".py"}), **limits)


def test_budgeted_manifest_still_refuses_linked_nonpython_directory(tmp_path):
    root = tmp_path.resolve() / "source"
    root.mkdir()
    cache = tmp_path.resolve() / "cache"
    cache.mkdir()
    (root / "not-python").symlink_to(cache, target_is_directory=True)
    with pytest.raises(ValueError, match="symlinks"):
        source_file_manifest(root, frozenset({".py"}), max_entries=8, max_depth=8)


@pytest.mark.parametrize("control", ("allowed", "not-selected", "changed-bytes", "unrelated-module"))
def test_installed_dependency_companion_requires_nomination_and_exact_record(tmp_path: Path, control: str) -> None:
    site = installed_fixture(tmp_path)
    companion = site / "__init__.py"
    source = ROOT / "projects/templates/template_autopoiesis/src/__init__.py"
    companion.write_bytes(source.read_bytes())
    if control == "unrelated-module":
        (site / "unselected.py").write_text("VALUE = 7\n")
    update_record(site)
    if control == "changed-bytes":
        companion.write_bytes(companion.read_bytes() + b"\n# actual altered distribution bytes\n")
    selected = frozenset() if control == "not-selected" else frozenset({"__init__"})
    program = (
        "from pathlib import Path;import infrastructure;"
        "from infrastructure.core.implementation_custody import capture_dependency_custody;"
        "observation=capture_dependency_custody('research-project-template',"
        f"Path(infrastructure.__file__).parent,public_modules={selected!r});"
        "assert '__init__.py' in observation['distribution']['file_sha256'];"
        "assert observation['binding_kind']=='installed-distribution';"
        "print('actual declared companion admitted')"
    )
    observed = probe(site, tmp_path, program)
    if control == "allowed":
        assert observed.returncode == 0, observed.stderr
        assert observed.stdout.strip() == "actual declared companion admitted"
    else:
        assert observed.returncode != 0
        expected = "RECORD size" if control == "changed-bytes" else "RECORD escapes"
        assert expected in observed.stderr
        assert "actual declared companion admitted" not in observed.stdout
