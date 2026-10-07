"""Native artifact controls reproduced from fresh independent review findings."""

from __future__ import annotations

import base64
import csv
import hashlib
import json
import os
import subprocess
import zipfile
from io import BytesIO, StringIO
from pathlib import Path

import pytest

from infrastructure.reporting.release_readiness_profile import Requirement
from infrastructure.project.installed_acceptance_artifacts import inspect_wheel_bytes
from infrastructure.reporting.release_readiness_artifacts import (
    validate_source_archive,
    validate_wheel_members,
    validate_wheel_source,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.reporting.release_readiness_validators import validate_acceptance, validate_installed_wheel
from infrastructure.reporting.native_format_acceptance_checks import parse_native_bytes

PROJECT = "templates/template_code_project"


def _file(root: Path, name: str, content: bytes) -> dict[str, str]:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return {"path": name, "sha256": hashlib.sha256(content).hexdigest()}


def _json(root: Path, name: str, content: dict) -> dict[str, str]:
    return _file(root, name, json.dumps(content).encode())


def _zip(members: dict[str, bytes]) -> bytes:
    output = BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    return output.getvalue()


def _wheel(implementation: bytes, extra: dict[str, bytes] | None = None) -> bytes:
    members = {
        "model.py": implementation,
        "exemplar-2.0.0.dist-info/METADATA": b"Metadata-Version: 2.1\nName: exemplar\nVersion: 2.0.0\n",
        "exemplar-2.0.0.dist-info/WHEEL": b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
    }
    members.update(extra or {})
    record = StringIO()
    writer = csv.writer(record)
    for name, data in members.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip("=")
        writer.writerow([name, "sha256=" + digest, len(data)])
    writer.writerow(["exemplar-2.0.0.dist-info/RECORD", "", ""])
    members["exemplar-2.0.0.dist-info/RECORD"] = record.getvalue().encode()
    return _zip(members)


def _requirement(kind: str, **kwargs) -> Requirement:
    return Requirement(f"{PROJECT}:{kind}", kind, PROJECT, "2.0.0", "4.0.0", "a" * 64, package="exemplar", **kwargs)


def test_metadata_only_and_stale_wheels_cannot_grant_installed_acceptance(tmp_path: Path) -> None:
    implementation = b"def model():\n    return 2\n"
    _file(tmp_path, f"projects/{PROJECT}/src/model.py", implementation)
    details = {
        "execution_exit_code": 0,
        "package": "exemplar",
        "version": "2.0.0",
        "isolated": True,
        "source_path_contamination": False,
        "imported_modules": ["model"],
    }
    requirement = _requirement("installed")
    for name, body in [
        ("metadata.whl", _zip({"exemplar-2.0.0.dist-info/METADATA": b"Name: exemplar\nVersion: 2.0.0\n"})),
        ("stale.whl", _wheel(b"def model():\n    return 1\n")),
    ]:
        binding = _file(tmp_path, "output/readiness/" + name, body)
        with pytest.raises(ValueError):
            validate_acceptance(
                requirement, {"details": dict(details, wheel_artifact=binding)}, SnapshotReader(tmp_path)
            )
    valid = _file(tmp_path, "output/readiness/current.whl", _wheel(implementation))
    validate_installed_wheel(requirement, dict(details, wheel_artifact=valid), SnapshotReader(tmp_path))
    with pytest.raises(ValueError, match="all supported runtime observations"):
        validate_acceptance(requirement, {"details": dict(details, wheel_artifact=valid)}, SnapshotReader(tmp_path))
    with pytest.raises(ValueError, match="module does not belong"):
        validate_acceptance(
            requirement,
            {"details": dict(details, wheel_artifact=valid, imported_modules=["invented"])},
            SnapshotReader(tmp_path),
        )


def test_docx_member_names_do_not_substitute_for_native_xml(tmp_path: Path) -> None:
    body = _zip({"[Content_Types].xml": b"not XML", "word/document.xml": b"not XML"})
    binding = _file(tmp_path, f"projects/{PROJECT}/output/docx/main.docx", body)
    details = {"execution_exit_code": 0, "formats": {"docx": dict(binding, validated=True)}}
    with pytest.raises(ValueError, match="native docx parser"):
        parse_native_bytes("docx", body)
    with pytest.raises(ValueError, match="exact artifact"):
        validate_acceptance(_requirement("formats", formats=("docx",)), {"details": details}, SnapshotReader(tmp_path))


def test_header_only_pdf_does_not_substitute_for_native_pages(tmp_path: Path) -> None:
    binding = _file(tmp_path, f"projects/{PROJECT}/output/pdf/main.pdf", b"%PDF-1.7\nnot a PDF")
    details = {"execution_exit_code": 0, "formats": {"pdf": dict(binding, validated=True)}}
    with pytest.raises(ValueError, match="native pdf parser"):
        parse_native_bytes("pdf", (tmp_path / binding["path"]).read_bytes())
    with pytest.raises(ValueError, match="exact artifact"):
        validate_acceptance(_requirement("formats", formats=("pdf",)), {"details": details}, SnapshotReader(tmp_path))


def test_export_and_remote_pairs_require_current_complete_source_archive(tmp_path: Path) -> None:
    source = b"def model():\n    return 2\n"
    _file(tmp_path, f"projects/{PROJECT}/src/model.py", source)
    req = _requirement("export")
    exported = _file(tmp_path, "output/readiness/source.zip", _zip({"src/model.py": source}))
    manifest = _json(
        tmp_path,
        "output/readiness/manifest.json",
        {
            "version": "2.0.0",
            "platform_version": "4.0.0",
            "source_identity": "a" * 64,
            "deliverables_identity": "",
            "bundle_sha256": exported["sha256"],
            "files": {"src/model.py": hashlib.sha256(source).hexdigest()},
        },
    )
    details = {"execution_exit_code": 0, "bundle_artifact": exported, "manifest_artifact": manifest}
    reader = SnapshotReader(tmp_path)
    validate_acceptance(req, {"details": details}, reader)
    retrieved = _file(tmp_path, "output/readiness/retrieved.zip", (tmp_path / exported["path"]).read_bytes())
    transfer = {
        "execution_exit_code": 0,
        "destination_kind": "sandbox",
        "remote_verified": True,
        "export_artifact": exported,
        "retrieved_artifact": retrieved,
    }
    # Local byte parity cannot replace the required actual GitHub transfer custody.
    with pytest.raises(ValueError, match="sandbox transfer needs exact artifact bindings"):
        validate_acceptance(_requirement("transfer"), {"details": transfer}, reader)
    unrelated = _file(tmp_path, "output/readiness/unrelated.txt", b"unrelated identical bytes")
    publication = {
        "execution_exit_code": 0,
        "actual_tag": "v2.0.0",
        "published_version": "2.0.0",
        "remote_verified": True,
        "source_commit": "c" * 40,
        "tag_commit": "c" * 40,
        "remote_commit": "c" * 40,
        "export_artifact": unrelated,
        "retrieved_artifact": unrelated,
    }
    with pytest.raises(ValueError, match="validated source/version export"):
        validate_acceptance(_requirement("publication"), {"details": publication}, reader)
    invalid = _file(tmp_path, "output/readiness/incomplete.zip", _zip({"other.py": source}))
    invalid_manifest = _json(
        tmp_path,
        "output/readiness/incomplete.json",
        {
            "version": "2.0.0",
            "platform_version": "4.0.0",
            "source_identity": "a" * 64,
            "deliverables_identity": "",
            "bundle_sha256": invalid["sha256"],
            "files": {"other.py": hashlib.sha256(source).hexdigest()},
        },
    )
    with pytest.raises(ValueError, match="omitted or invented"):
        validate_acceptance(
            req,
            {"details": dict(details, bundle_artifact=invalid, manifest_artifact=invalid_manifest)},
            SnapshotReader(tmp_path),
        )


def test_actual_standalone_publication_binds_distinct_commit_to_monorepo_export(tmp_path: Path) -> None:
    root = tmp_path / "monorepo"
    root.mkdir()
    environment = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
    for key in tuple(environment):
        if key.startswith("GIT_") and key not in {"GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM"}:
            environment.pop(key)

    def git(directory: Path, *args: str) -> bytes:
        return subprocess.run(
            ["git", "-c", "user.name=Invented fixture", "-c", "user.email=fixture@example.invalid", *args],
            cwd=directory,
            env=environment,
            check=True,
            capture_output=True,
            timeout=15,
        ).stdout

    source = b"def model():\n    return 2\n"
    _file(root, f"projects/{PROJECT}/src/model.py", source)
    git(root, "init", "--template=")
    git(root, "add", f"projects/{PROJECT}/src/model.py")
    git(root, "commit", "-m", "Invented source fixture")
    source_commit = git(root, "rev-parse", "HEAD").decode().strip()
    files = {"src/model.py": hashlib.sha256(source).hexdigest()}
    metadata = {
        "schema_version": 2,
        "source_project": PROJECT,
        "exported_project": Path(PROJECT).name,
        "source_commit": source_commit,
        "infrastructure_version": "4.0.0",
        "resource_dependencies": [],
        "files": files,
    }
    standalone = tmp_path / "standalone"
    standalone.mkdir()
    _file(standalone, "src/model.py", source)
    _json(standalone, ".template-export.json", metadata)
    git(standalone, "init", "--template=")
    git(standalone, "add", ".")
    git(standalone, "commit", "-m", "Invented standalone export")
    git(standalone, "tag", "v2.0.0")
    tag_commit = git(standalone, "rev-parse", "v2.0.0^{commit}").decode().strip()
    assert source_commit != tag_commit
    remote = tmp_path / "remote.git"
    git(tmp_path, "clone", "--bare", str(standalone), str(remote))
    remote_commit = git(remote, "rev-parse", "v2.0.0^{commit}").decode().strip()
    exported = _file(root, "output/readiness/source.zip", git(standalone, "archive", "--format=zip", "v2.0.0"))
    retrieved = _file(root, "output/readiness/retrieved.zip", git(remote, "archive", "--format=zip", "v2.0.0"))
    manifest = _json(
        root,
        "output/readiness/source-manifest.json",
        {
            "version": "2.0.0",
            "platform_version": "4.0.0",
            "source_identity": "a" * 64,
            "deliverables_identity": "",
            "source_commit": source_commit,
            "bundle_sha256": exported["sha256"],
            "files": files,
        },
    )
    reader = SnapshotReader(root)
    validate_acceptance(
        _requirement("export"),
        {"details": {"execution_exit_code": 0, "bundle_artifact": exported, "manifest_artifact": manifest}},
        reader,
    )
    details = {
        "execution_exit_code": 0,
        "actual_tag": "v2.0.0",
        "published_version": "2.0.0",
        "remote_verified": True,
        "source_commit": source_commit,
        "tag_commit": tag_commit,
        "remote_commit": remote_commit,
        "export_artifact": exported,
        "retrieved_artifact": retrieved,
    }
    validate_acceptance(_requirement("publication"), {"details": details}, reader)
    with pytest.raises(ValueError, match="monorepo source commit"):
        validate_acceptance(_requirement("publication"), {"details": dict(details, source_commit=tag_commit)}, reader)
    with pytest.raises(ValueError, match="commit parity"):
        validate_acceptance(
            _requirement("publication"), {"details": dict(details, remote_commit=source_commit)}, reader
        )
    changed = _file(root, "output/readiness/changed.zip", _zip({"src/model.py": b"def model(): return 3\n"}))
    with pytest.raises(ValueError, match="retrieval differs"):
        validate_acceptance(_requirement("publication"), {"details": dict(details, retrieved_artifact=changed)}, reader)


def test_other_project_coverage_and_partial_runtime_cannot_pass(tmp_path: Path) -> None:
    wrong = _json(
        tmp_path,
        "output/readiness/coverage.json",
        {
            "totals": {"percent_covered": 99, "num_branches": 2},
            "files": {"projects/templates/template_other/src/tiny.py": {}},
        },
    )
    req = _requirement("coverage", source_files=(f"projects/{PROJECT}/src/model.py",), python_version="3.14")
    details = {
        "execution_exit_code": 0,
        "percent": 99,
        "branch_coverage": True,
        "python_version": "3.14",
        "coverage_artifact": wrong,
    }
    with pytest.raises(ValueError, match="source scope"):
        validate_acceptance(req, {"details": details}, SnapshotReader(tmp_path))
    runtime = {
        "execution_exit_code": 0,
        "python_version": "3.14",
        "collected": 100,
        "passed": 1,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
        "deselected": 99,
        "test_files": ["tests/test_model.py"],
    }
    with pytest.raises(ValueError, match="collection is incomplete"):
        validate_acceptance(
            _requirement("runtime", python_version="3.14", test_files=("tests/test_model.py",)),
            {"details": runtime},
            SnapshotReader(tmp_path),
        )


@pytest.mark.parametrize("directory", ["../../escape/", "/absolute/", "unsafe\\directory/", "./"])
def test_source_archive_rejects_unsafe_directory_members(tmp_path: Path, directory: str) -> None:
    source = b"def model():\n    return 2\n"
    _file(tmp_path, f"projects/{PROJECT}/src/model.py", source)
    manifest = {"files": {"src/model.py": hashlib.sha256(source).hexdigest()}}
    with pytest.raises(ValueError, match="unsafe"):
        validate_source_archive(
            PROJECT, manifest, _zip({"src/model.py": source, directory: b""}), SnapshotReader(tmp_path)
        )


def test_embedded_export_metadata_requires_exact_public_producer_binding(tmp_path: Path) -> None:
    source = b"def model():\n    return 2\n"
    _file(tmp_path, f"projects/{PROJECT}/src/model.py", source)
    files = {"src/model.py": hashlib.sha256(source).hexdigest()}
    manifest = {"files": files, "source_commit": "c" * 40, "platform_version": "4.0.0"}
    metadata = {
        "schema_version": 2,
        "source_project": PROJECT,
        "exported_project": "template_code_project",
        "source_commit": "c" * 40,
        "infrastructure_version": "4.0.0",
        "resource_dependencies": [],
        "files": files,
    }
    valid = _zip({"src/model.py": source, "src/": b"", ".template-export.json": json.dumps(metadata).encode()})
    validate_source_archive(PROJECT, manifest, valid, SnapshotReader(tmp_path))
    invalid_metadata = [
        b"private fixture, not JSON",
        b"[]",
        json.dumps(dict(metadata, credential="private fixture")).encode(),
        json.dumps(dict(metadata, schema_version=True)).encode(),
        json.dumps(dict(metadata, source_commit="d" * 40)).encode(),
        json.dumps(dict(metadata, infrastructure_version="3.0.0")).encode(),
        json.dumps(dict(metadata, files={})).encode(),
    ]
    for content in invalid_metadata:
        invalid = _zip({"src/model.py": source, ".template-export.json": content})
        with pytest.raises(ValueError, match="embedded export metadata"):
            validate_source_archive(PROJECT, manifest, invalid, SnapshotReader(tmp_path))


@pytest.mark.parametrize(
    "raw",
    [
        {"status": "failed", "capability": "fresh-kernel", "execution_kind": "actual"},
        {"status": "passed", "capability": "fresh-kernel"},
        {"status": "passed", "execution_kind": "actual", "capability": "different"},
    ],
)
def test_failed_unknown_or_unrelated_live_receipt_cannot_pass(tmp_path: Path, raw: dict) -> None:
    binding = _json(tmp_path, "output/readiness/live.json", raw)
    details = {
        "execution_exit_code": 0,
        "paid": False,
        "capability": "fresh-kernel",
        "execution_kind": "actual",
        "execution_artifact": binding,
    }
    with pytest.raises(ValueError, match="actual capability"):
        validate_acceptance(
            _requirement("live", capability="fresh-kernel"), {"details": details}, SnapshotReader(tmp_path)
        )


@pytest.mark.timeout(240)
def test_runtime_counts_require_the_bound_actual_selected_interpreter(tmp_path: Path) -> None:
    from tests.infra_tests.reporting.test_runtime_case_evidence import _produce_runtime_case_evidence

    root, requirement, measured = _produce_runtime_case_evidence(tmp_path)
    details = measured[0]
    raw = json.loads((root / details["runtime_artifact"]["path"]).read_text())
    validate_acceptance(requirement, {"details": details}, SnapshotReader(root))
    for change in (
        {"executable": "/unrelated/python"},
        {"execution_exit_code": 1},
        {"interpreter_sha256": ""},
        {"missing": ["pytest"]},
        {"python_full_version": "0.0.0"},
    ):
        binding = _json(root, "output/readiness/runtime-invalid.json", dict(raw, **change))
        with pytest.raises(ValueError):
            validate_acceptance(requirement, {"details": dict(details, runtime_artifact=binding)}, SnapshotReader(root))


@pytest.mark.parametrize(
    "name", ["model/.env", "model/private.txt", "invented.py", "exemplar-2.0.0.dist-info/private.txt"]
)
def test_wheel_invented_private_or_extra_members_cannot_grant_acceptance(tmp_path: Path, name: str) -> None:
    implementation = b"def model():\n    return 2\n"
    _file(tmp_path, f"projects/{PROJECT}/src/model.py", implementation)
    wheel = _file(tmp_path, "output/readiness/extra.whl", _wheel(implementation, {name: b"private fixture only"}))
    details = {
        "execution_exit_code": 0,
        "package": "exemplar",
        "version": "2.0.0",
        "isolated": True,
        "source_path_contamination": False,
        "imported_modules": ["model"],
        "wheel_artifact": wheel,
    }
    with pytest.raises(ValueError, match="unbound or private"):
        validate_acceptance(_requirement("installed"), {"details": details}, SnapshotReader(tmp_path))


def test_wheel_public_data_must_match_source_and_remains_allowed(tmp_path: Path) -> None:
    implementation = b"def model():\n    return 2\n"
    _file(tmp_path, f"projects/{PROJECT}/src/model.py", implementation)
    _file(tmp_path, f"projects/{PROJECT}/src/public_data.txt", b"public input")
    requirement = _requirement("installed")
    details = {
        "execution_exit_code": 0,
        "package": "exemplar",
        "version": "2.0.0",
        "isolated": True,
        "source_path_contamination": False,
        "imported_modules": ["model"],
    }
    for content in (b"public input", b"different unbound data"):
        wheel = _file(tmp_path, "output/readiness/data.whl", _wheel(implementation, {"public_data.txt": content}))
        if content == b"public input":
            validate_installed_wheel(requirement, dict(details, wheel_artifact=wheel), SnapshotReader(tmp_path))
        else:
            with pytest.raises(ValueError, match="unbound or private"):
                validate_acceptance(
                    requirement, {"details": dict(details, wheel_artifact=wheel)}, SnapshotReader(tmp_path)
                )


def test_installed_pools_bundle_requires_exact_complete_declared_resources(tmp_path: Path) -> None:
    scope = "templates/template_pools_rules_tools"
    implementation = b"def model():\n    return 2\n"
    _file(tmp_path, f"projects/{scope}/src/model.py", implementation)
    _file(
        tmp_path,
        f"projects/{scope}/export.toml",
        b'[template_export]\ncross_root_dependencies=["fonds/templates","rules/templates","tools/templates"]\n',
    )
    resources = {}
    for kind in ("fonds", "rules", "tools"):
        relative = f"{kind}/templates/public/input.txt"
        content = f"public {kind} resource".encode()
        _file(tmp_path, relative, content)
        resources[f"template_pools_rules_tools/_template_resources/{relative}"] = content
    requirement = Requirement(f"{scope}:installed", "installed", scope, "2.0.0", "4.0.0", "a" * 64, package="exemplar")
    details = {
        "execution_exit_code": 0,
        "package": "exemplar",
        "version": "2.0.0",
        "isolated": True,
        "source_path_contamination": False,
        "imported_modules": ["model"],
    }
    wheel = _file(tmp_path, "output/readiness/pools.whl", _wheel(implementation, resources))
    validate_installed_wheel(requirement, dict(details, wheel_artifact=wheel), SnapshotReader(tmp_path))
    missing = dict(resources)
    missing.pop(next(iter(missing)))
    wheel = _file(tmp_path, "output/readiness/pools-missing.whl", _wheel(implementation, missing))
    with pytest.raises(ValueError, match="omitted declared public"):
        validate_acceptance(requirement, {"details": dict(details, wheel_artifact=wheel)}, SnapshotReader(tmp_path))
    changed = dict(resources)
    changed[next(iter(changed))] = b"unbound resource data"
    wheel = _file(tmp_path, "output/readiness/pools-changed.whl", _wheel(implementation, changed))
    with pytest.raises(ValueError, match="unbound or private"):
        validate_acceptance(requirement, {"details": dict(details, wheel_artifact=wheel)}, SnapshotReader(tmp_path))


@pytest.mark.parametrize("change", ["current", "old-layout", "stale", "private"])
def test_declared_namespaced_package_directory_binds_exact_wheel_members(tmp_path: Path, change: str) -> None:
    scope = "templates/template_literature_meta_analysis"
    _file(
        tmp_path,
        f"projects/{scope}/pyproject.toml",
        b'[project]\nname="template-literature-meta-analysis"\nversion="0.2.0"\n'
        b'[tool.setuptools.package-dir]\ntemplate_literature_meta_analysis="src"\n',
    )
    source = b"def value():\n    return 17\n"
    _file(tmp_path, f"projects/{scope}/src/__init__.py", source)
    _file(tmp_path, f"projects/{scope}/src/public_data.txt", b"public input")
    prefix = "" if change == "old-layout" else "template_literature_meta_analysis/"
    members = {
        prefix + "__init__.py": b"def value():\n    return 99\n" if change == "stale" else source,
        prefix + "public_data.txt": b"public input",
        "example-0.2.0.dist-info/METADATA": b"Name: example\nVersion: 0.2.0\n",
    }
    if change == "private":
        members[prefix + "private.txt"] = b"private fixture only"
    with zipfile.ZipFile(BytesIO(_zip(members))) as archive:
        if change == "current":
            validate_wheel_source(scope, archive, SnapshotReader(tmp_path))
        else:
            with pytest.raises(ValueError):
                validate_wheel_source(scope, archive, SnapshotReader(tmp_path))


@pytest.mark.parametrize(
    "change",
    [
        "complete",
        "missing-native-source",
        "missing-typing-marker",
        "changed-native-source",
        "bin",
        "lib",
        "obj",
        "logger/obj",
        "utils/obj",
    ],
)
def test_root_wheel_requires_authored_sdk_bytes_and_excludes_local_native_products(tmp_path: Path, change: str) -> None:
    """Real owned ZIP/RECORD controls exercise the production admission boundary."""
    authored = {
        "infrastructure/__init__.py": b"def measured_value():\n    return 17\n",
        "infrastructure/py.typed": b"",
        "infrastructure/steganography/kmyth/src/main/seal.c": b"int seal(void) { return 17; }\n",
        "infrastructure/steganography/kmyth/include/seal.h": b"int seal(void);\n",
        "infrastructure/config/public-data.json": b'{"measured_value":17}\n',
        "infrastructure/README.md": b"Owned authored SDK documentation.\n",
    }
    for name, content in authored.items():
        _file(tmp_path, name, content)
    native = {
        "infrastructure/steganography/kmyth/" + relative + "/owned-product": b"owned local native product"
        for relative in ("bin", "lib", "obj", "logger/obj", "utils/obj")
    }
    for name, content in native.items():
        _file(tmp_path, name, content)
    requirement = Requirement("root:installed", "installed", "root", "2.0.0", "4.0.0", "a" * 64, package="exemplar")

    def recorded_wheel(source_members: dict[str, bytes]) -> bytes:
        members = dict(source_members)
        members.update(
            {
                "exemplar-2.0.0.dist-info/METADATA": b"Metadata-Version: 2.1\nName: exemplar\nVersion: 2.0.0\n",
                "exemplar-2.0.0.dist-info/WHEEL": b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
            }
        )
        rows = StringIO()
        writer = csv.writer(rows, lineterminator="\n")
        for name, content in sorted(members.items()):
            digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).decode().rstrip("=")
            writer.writerow([name, "sha256=" + digest, len(content)])
        writer.writerow(["exemplar-2.0.0.dist-info/RECORD", "", ""])
        members["exemplar-2.0.0.dist-info/RECORD"] = rows.getvalue().encode()
        return _zip(members)

    targets, admitted = inspect_wheel_bytes(tmp_path, requirement, recorded_wheel(authored))
    assert targets == ("infrastructure",)
    assert admitted == {name: hashlib.sha256(content).hexdigest() for name, content in authored.items()}
    if change != "complete":
        altered = dict(authored)
        if change == "missing-native-source":
            altered.pop("infrastructure/steganography/kmyth/src/main/seal.c")
        elif change == "missing-typing-marker":
            altered.pop("infrastructure/py.typed")
        elif change == "changed-native-source":
            altered["infrastructure/steganography/kmyth/src/main/seal.c"] = b"int seal(void) { return 99; }\n"
        else:
            altered["infrastructure/steganography/kmyth/" + change + "/owned-product"] = b"owned local native product"
        content = recorded_wheel(altered)
        with zipfile.ZipFile(BytesIO(content)) as archive:
            validate_wheel_members(archive, ["infrastructure"])
        expected = "omitted current exact SDK" if change.startswith("missing-") else "unbound or private"
        with pytest.raises(ValueError, match=expected):
            inspect_wheel_bytes(tmp_path, requirement, content)
    assert all((tmp_path / name).read_bytes() == content for name, content in (authored | native).items())
