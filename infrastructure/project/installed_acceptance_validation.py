"""Require bound actual installed observations across every supported minor."""

from __future__ import annotations

import base64
import hashlib
import re
import zipfile
from dataclasses import replace
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any

from infrastructure.core.implementation_custody import _format_bytecode_audit_bootstrap
from infrastructure.project.acceptance_payload import format_acceptance_payload_loader, validate_acceptance_payload
from infrastructure.project.installed_acceptance_artifacts import INSTALLED_PROBE
from infrastructure.project.installed_acceptance_artifacts import inspect_wheel_bytes
from infrastructure.project.installed_domain_acceptance import validate_autopoiesis_observation
from infrastructure.project.public_package_dependencies import local_dependency_closure, package_metadata
from infrastructure.project.public_capabilities import CANONICAL_CI_PYTHON_VERSIONS
from infrastructure.reporting.release_readiness_artifacts import validate_wheel_members, validate_wheel_source

if TYPE_CHECKING:
    from infrastructure.reporting.release_readiness_profile import Requirement
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def _object(binding: object, reader: SnapshotReader) -> dict[str, Any]:
    if not isinstance(binding, dict) or set(binding) != {"path", "sha256"}:
        raise ValueError("installed execution requires an exact artifact binding")
    observed = reader.read(binding["path"])
    if observed.sha256 != binding["sha256"]:
        raise ValueError("installed execution artifact differs from its bound bytes")
    return observed.json_object()


def _custody_matches_wheel(custody: object, binding: object, scope: str, reader: SnapshotReader) -> None:
    if not isinstance(custody, dict) or custody.get("binding_kind") != "installed-distribution":
        raise ValueError("installed execution requires genuine distribution custody")
    if custody.get("bytecode_binding") != "fresh-owned-prefix" or not isinstance(binding, dict):
        raise ValueError("installed execution lacks its fresh source/wheel binding")
    wheel = reader.read(binding["path"])
    if wheel.sha256 != binding["sha256"]:
        raise ValueError("installed custody wheel bytes changed")
    with zipfile.ZipFile(BytesIO(wheel.content)) as archive:
        validate_wheel_members(archive, [])
        validate_wheel_source(scope, archive, reader)
        python = {
            name: hashlib.sha256(archive.read(name)).hexdigest() for name in archive.namelist() if name.endswith(".py")
        }
        metadata = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        if len(metadata) != 1:
            raise ValueError("installed custody wheel has ambiguous metadata")
        metadata_sha = hashlib.sha256(archive.read(metadata[0])).hexdigest()
        companion_names = {"__init__.py"} if scope == "templates/template_autopoiesis" else set()
        companion_bytes = {name: archive.read(name) for name in companion_names if name in python}
    distribution = custody.get("distribution")
    if not isinstance(distribution, dict) or distribution.get("metadata_sha256") != metadata_sha:
        raise ValueError("installed distribution differs from admitted wheel metadata")
    actual = distribution.get("public_python")
    companions = distribution.get("companion_python")
    if (
        not isinstance(companions, dict)
        or set(companions) != companion_names
        or set(companion_bytes) != companion_names
    ):
        raise ValueError("installed distribution differs from Source-declared companion modules")
    file_hashes = distribution.get("file_sha256")
    declared_files = distribution.get("declared_files")
    if not isinstance(file_hashes, dict) or not isinstance(declared_files, dict):
        raise ValueError("installed distribution lacks its exact RECORD file inventory")
    for name, content in companion_bytes.items():
        digest = hashlib.sha256(content).hexdigest()
        encoded = "sha256=" + base64.urlsafe_b64encode(bytes.fromhex(digest)).decode().rstrip("=")
        if (
            companions[name] != digest
            or file_hashes.get(name) != digest
            or declared_files.get(name) != [encoded, str(len(content))]
        ):
            raise ValueError("installed companion differs from its exact wheel and RECORD bytes")
    if not isinstance(actual, dict) or not actual or len(actual) + len(companions) != len(python):
        raise ValueError("installed distribution omits its actual wheel source")
    matched: set[str] = set()
    for relative, digest in actual.items():
        if not isinstance(relative, str) or Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError("installed custody contains an unconfined source path")
        candidates = {
            name
            for name, expected in python.items()
            if name not in companion_names
            and digest == expected
            and (name == relative or name.endswith("/" + relative))
        }
        if len(candidates) != 1 or matched & candidates:
            raise ValueError("installed distribution source differs from admitted wheel")
        matched.update(candidates)
    if matched & companion_names:
        raise ValueError("installed companion overlaps package source custody")
    matched.update(companion_names)
    if matched != set(python):
        raise ValueError("installed custody omits admitted wheel Python")


def _validate_meta_replay(
    domain: object, prefix: Path, site: Path, members: dict[str, str], reader: SnapshotReader
) -> None:
    """Bind genuine installed default replay to its exact authored JSON resource."""
    member = "template_literature_meta_analysis/deep_research/fixtures/recorded_report.json"
    source = reader.read(
        "projects/templates/template_literature_meta_analysis/src/deep_research/fixtures/recorded_report.json"
    )
    payload = source.json_object()
    citations = [{"title": item.get("title"), "url": item.get("url")} for item in payload.get("citations", [])]
    expected = {
        "provider": str(payload["provider"]),
        "job_id": str(payload.get("job_id", "")),
        "status": str(payload.get("status", "completed")),
        "query": str((payload.get("request", {}) or {}).get("query", "")),
        "output_text": str(payload.get("output_text", "")),
        "citations": citations,
        "citation_count": len(citations),
    }
    if (
        not isinstance(domain, dict)
        or set(domain) != {"fixture_path", "fixture_sha256", "replay"}
        or domain["fixture_path"] != str(site / member)
        or not (site / member).is_relative_to(prefix)
        or domain["fixture_sha256"] != source.sha256
        or members.get(member) != source.sha256
        or domain["replay"] != expected
    ):
        raise ValueError("installed Meta replay differs from its admitted authored fixture")


def _cell(requirement: Requirement, cell: dict[str, Any], reader: SnapshotReader) -> None:
    from infrastructure.reporting.release_readiness_validators import validate_installed_wheel

    runtime = cell["python_version"]
    details = cell.get("details")
    if cell.get("status") != "pass" or cell.get("scope") != requirement.scope or not isinstance(details, dict):
        raise ValueError("installed runtime cell did not pass for the required scope")
    validate_installed_wheel(requirement, details, reader)
    raw = _object(details.get("runtime_artifact"), reader)
    process = _object(details.get("process_artifact"), reader)
    spec = _object(details.get("probe_spec_artifact"), reader)
    wheel = reader.read(details["wheel_artifact"]["path"])
    targets, members = inspect_wheel_bytes(reader.root, requirement, wheel.content, reader=reader)
    admitted = dict(members)
    namespace_targets = list(targets)
    metadata_path = "pyproject.toml" if requirement.scope == "root" else f"projects/{requirement.scope}/pyproject.toml"
    closure = (
        local_dependency_closure(reader.root, requirement.scope, reader=reader)
        if (reader.root / metadata_path).is_file()
        else ()
    )
    providers = spec.get("dependency_providers")
    if (
        spec.get("targets") != list(targets)
        or spec.get("wheel_members") != members
        or not isinstance(providers, list)
        or len(providers) != len(closure)
        or [provider.get("scope") for provider in providers if isinstance(provider, dict)] != list(closure)
    ):
        raise ValueError("installed specification omits or invents admitted source/provider members")
    for provider in providers:
        identity = package_metadata(reader.root, provider["scope"], reader)["project"]
        observed = next(
            (
                item
                for item in raw.get("dependency_providers", [])
                if isinstance(item, dict) and item.get("scope") == provider["scope"]
            ),
            None,
        )
        if (
            observed is None
            or any(provider.get(name) != observed.get(name) for name in ("package", "version", "wheel_artifact"))
            or provider.get("package") != identity["name"]
            or provider.get("version") != identity["version"]
        ):
            raise ValueError("installed provider observation differs from source-owned identity")
        binding = provider["wheel_artifact"]
        snapshot = reader.read(binding["path"])
        if snapshot.sha256 != binding["sha256"]:
            raise ValueError("installed provider wheel differs from its bound bytes")
        provider_requirement = replace(
            requirement, scope=provider["scope"], package=identity["name"], version=identity["version"]
        )
        provider_targets, provider_members = inspect_wheel_bytes(
            reader.root, provider_requirement, snapshot.content, reader=reader
        )
        if (
            provider.get("targets") != list(provider_targets)
            or provider.get("wheel_members") != provider_members
            or set(admitted) & set(provider_members)
        ):
            raise ValueError("installed provider wheel surface is changed or overlapping")
        admitted.update(provider_members)
        namespace_targets.extend(provider_targets)
    required = {
        "schema_version": "template-installed-probe-v2",
        "execution_exit_code": 0,
        "isolated": True,
        "source_path_contamination": False,
        "bytecode_binding": "fresh-owned-prefix",
        "package": requirement.package,
        "version": requirement.version,
        "python_version": runtime,
    }
    for name, expected in required.items():
        if type(raw.get(name)) is not type(expected) or raw[name] != expected:
            raise ValueError("installed probe differs from its intended runtime/package execution")
    for name in ("interpreter", "interpreter_sha256", "imported_modules", "origins", "domain", "build_policy"):
        if raw.get(name) != details.get(name):
            raise ValueError("installed runtime summary differs from its actual probe")
    nonce = spec.get("run_nonce")
    full = raw.get("python_full_version")
    audit = spec.get("audit")
    if (
        not isinstance(nonce, str)
        or re.fullmatch(r"[0-9a-f]{32}", nonce) is None
        or raw.get("run_nonce") != nonce
        or raw.get("probe_spec_sha256") != details["probe_spec_artifact"]["sha256"]
        or spec.get("python_version") != runtime
        or not isinstance(full, str)
        or re.fullmatch(re.escape(runtime) + r"\.[0-9]+(?:[abrc]+[0-9]+)?", full) is None
        or raw.get("implementation") != "CPython"
        or not isinstance(audit, dict)
        or set(audit) != {"roots", "path", "prefix", "sha256"}
        or not isinstance(audit["roots"], list)
        or not audit["roots"]
        or any(
            not isinstance(path, str) or not Path(path).is_absolute() or ".." in Path(path).parts
            for path in audit["roots"]
        )
        or any(
            not isinstance(audit[name], str) or not Path(audit[name]).is_absolute() or ".." in Path(audit[name]).parts
            for name in ("path", "prefix")
        )
    ):
        raise ValueError("installed probe is not bound to its exact run/specification/runtime")
    hook = reader.read("infrastructure/core/bytecode_audit.py")
    if audit["sha256"] != hook.sha256:
        raise ValueError("installed launcher audit differs from current admitted hook bytes")
    installed_prefix = Path(raw["prefix"])
    site = installed_prefix / (
        "Lib/site-packages" if "\\" in raw["interpreter"] else f"lib/python{runtime}/site-packages"
    )
    expected_roots = [str(site / name) for name in admitted if name.endswith(".py")] + [
        str(site / target) for target in namespace_targets if target + ".py" not in admitted
    ]
    expected_hook = (
        site / "infrastructure/core/bytecode_audit.py"
        if requirement.scope == "root" or "root" in closure
        else Path(raw["spec_path"]).parent / "bytecode_audit.py"
    )
    if (
        len(audit["roots"]) != len(expected_roots)
        or set(audit["roots"]) != set(expected_roots)
        or audit["path"] != str(expected_hook)
    ):
        raise ValueError("installed audit omits or invents its actual wheel source roots")
    bootstrap = _format_bytecode_audit_bootstrap(
        hook.content, Path(audit["path"]), tuple(Path(path) for path in audit["roots"]), Path(audit["prefix"])
    )
    payload_bytes = (bootstrap + "\n" + INSTALLED_PROBE).encode()
    payload_binding = details.get("probe_payload_artifact")
    if not isinstance(payload_binding, dict) or set(payload_binding) != {"path", "sha256"}:
        raise ValueError("installed probe requires its exact retained Source payload artifact")
    expected_artifact = (Path(details["probe_spec_artifact"]["path"]).parent / "installed-probe-payload.py").as_posix()
    if payload_binding["path"] != expected_artifact:
        raise ValueError("installed probe payload artifact has a different fixed evidence path")
    held_payload = reader.read(payload_binding["path"])
    if held_payload.content != payload_bytes or held_payload.sha256 != payload_binding["sha256"]:
        raise ValueError("installed probe payload artifact differs from the regenerated Source body")
    payload = validate_acceptance_payload(
        payload_bytes,
        spec.get("probe_payload"),
        expected_path=Path(raw["spec_path"]).parent / "installed-probe-payload.py",
    )
    if any(Path(payload["path"]).is_relative_to(Path(root)) for root in spec.get("forbidden_roots", [])):
        raise ValueError("installed probe payload is inside a forbidden Source tree")
    expected_command = [
        raw.get("interpreter"),
        "-I",
        "-X",
        f"pycache_prefix={audit['prefix']}",
        "-c",
        format_acceptance_payload_loader(payload),
        raw.get("spec_path"),
        raw.get("observation_path"),
    ]
    command = details.get("command")
    if (
        not isinstance(command, list)
        or len(command) != 8
        or not all(isinstance(argument, str) for argument in command)
        or command[0] != raw.get("interpreter")
        or command[1:3] != ["-I", "-X"]
        or not command[3].startswith("pycache_prefix=")
        or command[4] != "-c"
        or command != expected_command
        or process.get("command") != command
        or type(process.get("returncode")) is not int
        or process["returncode"] != 0
        or process.get("timed_out") is not False
        or process.get("detail")
        or process.get("project_name") != "installed-probe"
    ):
        raise ValueError("installed probe lacks a successful bound isolated child process")
    prefix = raw.get("prefix")
    interpreter_sha = raw.get("interpreter_sha256")
    origins = raw.get("origins")
    if (
        not isinstance(prefix, str)
        or not Path(prefix).is_absolute()
        or not isinstance(interpreter_sha, str)
        or re.fullmatch(r"[0-9a-f]{64}", interpreter_sha) is None
        or interpreter_sha != details.get("selected_interpreter_sha256")
        or not isinstance(origins, dict)
        or set(origins) != set(raw.get("imported_modules", []))
        or spec.get("scope") != requirement.scope
        or spec.get("package") != requirement.package
        or spec.get("version") != requirement.version
        or spec.get("targets") != raw.get("imported_modules")
        or not isinstance(spec.get("forbidden_roots"), list)
        or not spec["forbidden_roots"]
    ):
        raise ValueError("installed interpreter/import observation is incomplete or stale")
    for locations in origins.values():
        if not isinstance(locations, list) or not locations:
            raise ValueError("installed package import origins are missing")
        for location in locations:
            if (
                not isinstance(location, str)
                or not Path(location).is_absolute()
                or not Path(location).is_relative_to(prefix)
                or any(Path(location).is_relative_to(forbidden) for forbidden in spec["forbidden_roots"])
            ):
                raise ValueError("installed package imported from source or outside its environment")
    if requirement.scope == "templates/template_literature_meta_analysis":
        _validate_meta_replay(raw.get("domain"), Path(prefix), site, members, reader)
    if requirement.scope == "templates/template_autopoiesis":
        receipt = validate_autopoiesis_observation(raw.get("domain"))
        base = reader.root / "projects" / requirement.scope
        references = [
            base / "manuscript/config.yaml",
            *sorted((base / "src").rglob("*.py")),
            *sorted((base / "tests/primitives").glob("test_primitives_*.py")),
        ]
        if receipt.get("source_sha256") != {
            path.relative_to(base).as_posix(): reader.read(path.relative_to(reader.root).as_posix()).sha256
            for path in references
        }:
            raise ValueError("installed child execution consumed different project reference inputs")
        _custody_matches_wheel(
            receipt["active_generator_custody"], details["wheel_artifact"], requirement.scope, reader
        )
        providers = raw.get("dependency_providers", [])
        platform = [
            provider for provider in providers if isinstance(provider, dict) and provider.get("scope") == "root"
        ]
        if len(platform) != 1:
            raise ValueError("installed child execution lacks its admitted platform wheel")
        _custody_matches_wheel(receipt["platform_custody"], platform[0]["wheel_artifact"], "root", reader)
        from infrastructure.project.installed_reference_oracle import verify_autopoiesis_reference_results

        verify_autopoiesis_reference_results(raw["domain"], reader)


def validate_installed_matrix(requirement: Requirement, details: dict[str, Any], reader: SnapshotReader) -> None:
    """A current wheel alone cannot stand in for three actual installed runtimes."""
    cells = details.get("runtime_observations")
    expected = list(CANONICAL_CI_PYTHON_VERSIONS)
    if (
        details.get("source_current") is not True
        or details.get("tested_python_versions") != expected
        or not isinstance(cells, list)
        or len(cells) != len(expected)
        or [cell.get("python_version") for cell in cells if isinstance(cell, dict)] != expected
    ):
        raise ValueError("installed acceptance requires all supported runtime observations")
    for cell in cells:
        _cell(requirement, cell, reader)
