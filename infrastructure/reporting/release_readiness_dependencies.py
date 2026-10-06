"""Bind runtime acceptance to current declared installed public providers."""

from __future__ import annotations

import base64
import csv
import hashlib
import re
import zipfile
from email.parser import BytesParser
from io import BytesIO, StringIO
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Any

from packaging.utils import canonicalize_name

from infrastructure.reporting.release_readiness_runtime import validate_runtime_cases
from infrastructure.project.public_acceptance_evidence import aggregate_pytest
from infrastructure.project.public_package_dependencies import (
    declared_local_dependencies,
    local_dependency_closure,
    package_metadata,
)
from infrastructure.reporting.release_readiness_artifacts import validate_wheel_members, validate_wheel_source
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

if TYPE_CHECKING:
    from infrastructure.reporting.release_readiness_profile import Requirement


def _artifact(binding: object, reader: SnapshotReader) -> ArtifactSnapshot:
    if not isinstance(binding, dict) or set(binding) != {"path", "sha256"}:
        raise ValueError("provider evidence requires an exact artifact binding")
    snapshot = reader.read(binding["path"])
    if not snapshot.content or snapshot.sha256 != binding["sha256"]:
        raise ValueError("provider artifact differs from its exact bytes")
    return snapshot


def _providers(scope: str, reader: SnapshotReader) -> dict[str, tuple[str, str]]:
    relative = "pyproject.toml" if scope == "root" else f"projects/{scope}/pyproject.toml"
    # Minimal direct artifact oracles may omit metadata. The whole profile
    # requires and snapshots every canonical project pyproject before this call.
    if not (reader.root / relative).exists():
        return {}
    closure = local_dependency_closure(reader.root, scope, reader=reader)
    result = {}
    for provider in closure:
        project = package_metadata(reader.root, provider, reader).get("project", {})
        package, version = project.get("name"), project.get("version")
        if not isinstance(package, str) or not package or not isinstance(version, str) or not version:
            raise ValueError("provider lacks current source-owned package/version metadata")
        for parent in (*closure, scope):
            declaration = declared_local_dependencies(reader.root, parent, reader=reader).get(provider)
            if declaration is not None and not declaration.specifier.contains(version, prereleases=True):
                raise ValueError("provider version violates a source-owned dependency declaration")
        if provider != "root":
            result[provider] = package, version
    return result


def _wheel(scope: str, package: str, version: str, binding: object, reader: SnapshotReader) -> dict[str, bytes]:
    snapshot = _artifact(binding, reader)
    with zipfile.ZipFile(BytesIO(snapshot.content)) as archive:
        validate_wheel_members(archive, [])
        validate_wheel_source(scope, archive, reader)
        members = {item.filename: archive.read(item) for item in archive.infolist() if not item.is_dir()}
    metadata = [name for name in members if name.endswith(".dist-info/METADATA")]
    if len(metadata) != 1:
        raise ValueError("provider wheel has ambiguous distribution metadata")
    fields = BytesParser().parsebytes(members[metadata[0]])
    if (
        fields.get_all("Name") != [package]
        and (len(fields.get_all("Name", [])) != 1 or canonicalize_name(fields["Name"]) != canonicalize_name(package))
        or fields.get_all("Version") != [version]
    ):
        raise ValueError("provider wheel differs from current declared package/version")
    return members


def _record(content: bytes) -> dict[str, list[str]]:
    rows: dict[str, list[str]] = {}
    for row in csv.reader(StringIO(content.decode())):
        if (
            len(row) != 3
            or not row[0]
            or row[0] in rows
            or "\\" in row[0]
            or "\x00" in row[0]
            or PurePosixPath(row[0]).is_absolute()
            or ".." in PurePosixPath(row[0]).parts
        ):
            raise ValueError("installed provider RECORD has unsafe or duplicate members")
        rows[row[0]] = row[1:]
    return rows


def _custody(
    package: str,
    version: str,
    members: dict[str, bytes],
    raw: object,
    artifacts: object,
    reader: SnapshotReader,
) -> None:
    if not isinstance(raw, dict) or set(raw) != {"before", "after"} or raw["before"] != raw["after"]:
        raise ValueError("provider changed between actual pytest custody observations")
    capture = raw["before"]
    if (
        not isinstance(capture, dict)
        or capture.get("name") != package
        or capture.get("binding_kind") != "installed-distribution"
        or capture.get("bytecode_binding") != "fresh-owned-prefix"
    ):
        raise ValueError("provider was not consumed as an installed distribution with fresh bytecode")
    distribution = capture.get("distribution")
    if (
        not isinstance(distribution, dict)
        or distribution.get("name") != package
        or distribution.get("version") != version
        or not isinstance(artifacts, dict)
        or set(artifacts) != {"metadata", "record"}
    ):
        raise ValueError("actual provider distribution metadata is missing or stale")
    metadata = _artifact(artifacts["metadata"], reader)
    record = _artifact(artifacts["record"], reader)
    metadata_name = next(name for name in members if name.endswith(".dist-info/METADATA"))
    record_name = next(name for name in members if name.endswith(".dist-info/RECORD"))
    if (
        metadata.content != members[metadata_name]
        or distribution.get("metadata_sha256") != metadata.sha256
        or distribution.get("record_sha256") != record.sha256
    ):
        raise ValueError("actual installed provider metadata differs from its admitted current wheel")
    rows = _record(record.content)
    hashes = distribution.get("file_sha256")
    if (
        rows != distribution.get("declared_files")
        or not isinstance(hashes, dict)
        or rows.get(record_name) != ["", ""]
        or hashes.get(record_name) != record.sha256
    ):
        raise ValueError("actual installed provider RECORD differs from its custody capture")
    wheel_hashes = {
        name: hashlib.sha256(content).hexdigest() for name, content in members.items() if name != record_name
    }
    if any(hashes.get(name) != digest or name not in rows for name, digest in wheel_hashes.items()):
        raise ValueError("installed provider members differ from the admitted current wheel")
    metadata_root = metadata_name.rsplit("/", 1)[0]
    generated = {f"{metadata_root}/{name}" for name in ("INSTALLER", "REQUESTED", "direct_url.json", "uv_cache.json")}
    caches = {name for name in rows if "__pycache__" in PurePosixPath(name).parts and name.endswith(".pyc")}
    for name in caches:
        path = PurePosixPath(name)
        if (
            path.parent.name != "__pycache__"
            or rows[name] != ["", ""]
            or not any(
                path.parent.parent == PurePosixPath(source).parent
                and path.name.startswith(PurePosixPath(source).stem + ".")
                for source in members
                if source.endswith(".py")
            )
        ):
            raise ValueError("installed provider cache row is outside its declared Python implementation")
    if (
        set(rows) - set(members) - generated - caches
        or set(hashes) != set(rows) - caches
        or not set(members) <= set(rows)
    ):
        raise ValueError("installed provider invents files outside its wheel and installer metadata")
    for name, (digest, size) in rows.items():
        if name in caches or name == record_name:
            continue
        actual_hash = hashes.get(name)
        if not isinstance(actual_hash, str) or re.fullmatch("[0-9a-f]{64}", actual_hash) is None:
            raise ValueError("installed provider lacks exact member hashes")
        encoded = "sha256=" + base64.urlsafe_b64encode(bytes.fromhex(actual_hash)).decode().rstrip("=")
        if digest != encoded or not size.isdecimal() or name in members and size != str(len(members[name])):
            raise ValueError("installed provider RECORD does not bind its actual member bytes")
    files = capture.get("files")
    if not isinstance(files, dict) or not files or files != distribution.get("public_python"):
        raise ValueError("actual consumed provider Python inventory differs from its distribution")
    python_members = {name: digest for name, digest in wheel_hashes.items() if name.endswith(".py")}
    matched: set[str] = set()
    for relative, digest in files.items():
        if (
            not isinstance(relative, str)
            or not relative.endswith(".py")
            or PurePosixPath(relative).is_absolute()
            or ".." in PurePosixPath(relative).parts
        ):
            raise ValueError("provider source inventory has an invalid member")
        candidates = {
            name
            for name, expected in python_members.items()
            if expected == digest and (name == relative or name.endswith("/" + relative))
        }
        if len(candidates) != 1 or matched & candidates:
            raise ValueError("consumed provider source differs from its current admitted wheel")
        matched.update(candidates)
    if matched != set(python_members):
        raise ValueError("provider custody omitted current wheel Python implementation")


def validate_runtime_dependencies(requirement: Requirement, details: dict[str, Any], reader: SnapshotReader) -> None:
    """Validate source-owned non-root providers in every actual pytest process."""
    expected = _providers(requirement.scope, reader)
    providers = details.get("dependency_providers", {})
    if not isinstance(providers, dict) or set(providers) != set(expected):
        raise ValueError("runtime evidence omits or invents declared installed dependency providers")
    receipts = validate_runtime_cases(requirement, details, reader)
    if not expected:
        for receipt in receipts:
            if receipt.get("dependency_custody") != {} or receipt.get("dependency_artifacts") != {}:
                raise ValueError("pytest receipt invents undeclared installed providers")
        return
    _validate_provider_receipts(requirement, details, reader, receipts)


def _validate_provider_receipts(
    requirement: Requirement,
    details: dict[str, Any],
    reader: SnapshotReader,
    receipts: list[dict[str, Any]],
) -> None:
    """Check installed provider custody; this helper alone does not admit a runtime gate."""
    expected = _providers(requirement.scope, reader)
    providers = details.get("dependency_providers", {})
    if not isinstance(providers, dict) or set(providers) != set(expected):
        raise ValueError("runtime evidence omits or invents declared installed dependency providers")
    run_id = details.get("run_id")
    if not isinstance(run_id, str) or not run_id or len(receipts) < 2:
        raise ValueError("provider observation requires full collection and case receipts")
    counts = aggregate_pytest(receipts[0], receipts[1:], run_id)
    if any(counts[key] for key in ("failed", "errors", "skipped", "deselected")):
        raise ValueError("provider-bound actual pytest selection did not pass completely")
    if requirement.kind == "runtime" and any(
        details.get(key) != counts[key] for key in ("collected", "passed", "failed", "errors", "skipped", "deselected")
    ):
        raise ValueError("provider-bound pytest counts differ from its custody control")
    runtime = _artifact(details.get("runtime_artifact"), reader).json_object()
    runtime.pop("execution_exit_code", None)
    runtime.pop("command", None)
    if any(
        type(item.get("exit_code")) is not int or item["exit_code"] != 0 or item.get("runtime") != runtime
        for item in receipts
    ):
        raise ValueError("provider observation differs from its actual selected runtime")
    wheels = {}
    for scope, (package, version) in expected.items():
        declaration = providers[scope]
        if (
            not isinstance(declaration, dict)
            or set(declaration) != {"package", "version", "wheel_artifact"}
            or declaration["package"] != package
            or declaration["version"] != version
        ):
            raise ValueError("runtime provider differs from current source-owned identity")
        wheels[scope] = _wheel(scope, package, version, declaration["wheel_artifact"], reader)
    for receipt in receipts:
        custody, artifacts = receipt.get("dependency_custody"), receipt.get("dependency_artifacts")
        if (
            not isinstance(custody, dict)
            or not isinstance(artifacts, dict)
            or set(custody) != set(expected)
            or set(artifacts) != set(expected)
        ):
            raise ValueError("actual pytest receipt lacks its exact declared provider closure")
        for scope, (package, version) in expected.items():
            _custody(package, version, wheels[scope], custody[scope], artifacts[scope], reader)
