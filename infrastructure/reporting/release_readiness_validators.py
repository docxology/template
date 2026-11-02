"""Kind-specific acceptance oracles; structural receipts alone cannot pass."""

from __future__ import annotations

import math
import re
import zipfile
from email.parser import Parser
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.release_readiness_artifacts import (
    validate_wheel_members,
    validate_wheel_source,
    validate_source_archive,
)
from infrastructure.reporting.release_readiness_dependencies import validate_runtime_dependencies
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

if TYPE_CHECKING:
    from infrastructure.reporting.release_readiness_profile import Requirement


def _integer(value: object, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError("execution evidence requires exact nonnegative integers")
    return value


def _hash(value: object, *, length: int = 64) -> str:
    if not isinstance(value, str) or re.fullmatch(f"[0-9a-f]{{{length}}}", value) is None:
        raise ValueError("evidence identity has an invalid digest")
    return value


def _file(binding: object, reader: SnapshotReader) -> ArtifactSnapshot:
    if not isinstance(binding, dict):
        raise ValueError("an exact public artifact binding is required")
    snapshot = reader.read(binding.get("path", ""))
    if _hash(binding.get("sha256")) != snapshot.sha256 or not snapshot.content:
        raise ValueError("artifact bytes do not match their evidence binding")
    return snapshot


def _oracles(details: dict[str, Any], reader: SnapshotReader) -> None:
    assertions = details.get("assertions")
    controls = details.get("negative_controls")
    if (
        not isinstance(assertions, dict)
        or not assertions
        or any(not isinstance(key, str) or not key or value is not True for key, value in assertions.items())
        or not isinstance(controls, list)
        or not controls
    ):
        raise ValueError("positive assertions and real failing negative controls are required")
    for control in controls:
        if not isinstance(control, dict) or not isinstance(control.get("name"), str) or not control["name"]:
            raise ValueError("negative control must have a stable name")
        expected = _integer(control.get("expected_exit_code"), minimum=1)
        if _integer(control.get("observed_exit_code"), minimum=1) != expected:
            raise ValueError("negative control did not produce the expected failure")
        observed = _file(control.get("artifact"), reader).json_object()
        if type(observed.get("exit_code")) is not int or observed["exit_code"] != expected:
            raise ValueError("negative-control artifact differs from the observed process exit")


def _runtime(requirement: Requirement, details: dict[str, Any]) -> None:
    if details.get("python_version") != requirement.python_version:
        raise ValueError("runtime evidence differs from the declared supported runtime")
    counts = {
        key: _integer(details.get(key)) for key in ("collected", "passed", "failed", "errors", "skipped", "deselected")
    }
    if (
        not counts["passed"]
        or counts["failed"]
        or counts["errors"]
        or counts["skipped"]
        or counts["deselected"]
        or counts["collected"] != sum(counts[key] for key in ("passed", "failed", "errors", "skipped", "deselected"))
    ):
        raise ValueError("runtime tests failed or their collection is incomplete")
    if not requirement.test_files or details.get("test_files") != list(requirement.test_files):
        raise ValueError("runtime execution did not cover the complete source-owned test file selection")


def _runtime_probe(requirement: Requirement, details: dict[str, Any], reader: SnapshotReader) -> None:
    """Bind passing measurements to the actual selected installed interpreter."""
    raw = _file(details.get("runtime_artifact"), reader).json_object()
    minor = details.get("python_version")
    executable = details.get("interpreter")
    implementation = details.get("implementation")
    full_version = details.get("python_full_version")
    if (
        raw.get("schema_version") != "template-public-runtime-v1"
        or type(raw.get("execution_exit_code")) is not int
        or raw["execution_exit_code"] != 0
        or raw.get("missing") != []
        or minor not in {"3.14", "3.15"}
        or (requirement.python_version and minor != requirement.python_version)
        or not isinstance(executable, str)
        or not Path(executable).is_absolute()
        or raw.get("executable") != executable
        or raw.get("python_version") != minor
        or not isinstance(implementation, str)
        or not implementation
        or raw.get("implementation") != implementation
        or not isinstance(full_version, str)
        or not full_version.startswith(str(minor) + ".")
        or raw.get("python_full_version") != full_version
        or not isinstance(raw.get("packages"), dict)
        or not raw["packages"]
    ):
        raise ValueError("runtime measurement differs from its selected installed interpreter probe")
    _hash(raw.get("interpreter_sha256"))


def _coverage(requirement: Requirement, details: dict[str, Any], reader: SnapshotReader) -> None:
    percentage = details.get("percent")
    floor = 60 if requirement.scope == "root" else 90
    if (
        not isinstance(percentage, (int, float))
        or isinstance(percentage, bool)
        or not math.isfinite(percentage)
        or not floor <= percentage <= 100
        or details.get("branch_coverage") is not True
        or (requirement.python_version and details.get("python_version") != requirement.python_version)
    ):
        raise ValueError("coverage does not meet the declared runtime/source floor")
    data = _file(details.get("coverage_artifact"), reader).json_object()
    files = data.get("files")
    if not isinstance(files, dict) or not files or not requirement.source_files:
        raise ValueError("coverage must measure the declared source file scope")
    normalized = set()
    for name in files:
        if not isinstance(name, str) or name.startswith("/") or ".." in name.split("/"):
            raise ValueError("coverage contains unbound/private file paths")
        normalized.add(
            f"projects/{requirement.scope}/{name}" if name.startswith("src/") and requirement.scope != "root" else name
        )
    if normalized != set(requirement.source_files) or len(normalized) != len(files):
        raise ValueError("coverage measured a different or incomplete source scope")
    totals = data.get("totals")
    if (
        not isinstance(totals, dict)
        or type(totals.get("percent_covered")) not in {int, float}
        or totals["percent_covered"] != percentage
        or _integer(totals.get("num_branches"), minimum=1) < 1
    ):
        raise ValueError("coverage summary differs from the exact branch-coverage artifact")


def _formats(requirement: Requirement, details: dict[str, Any], reader: SnapshotReader) -> None:
    from infrastructure.reporting.native_format_acceptance_validation import validate_native_acceptance
    from infrastructure.reporting.native_format_joint_source import require_native_operation
    from infrastructure.reporting.native_current_reader_inputs import NativeCurrentAnalysisInputs

    operation = require_native_operation(reader)
    current = operation.current_analysis
    if not isinstance(current, NativeCurrentAnalysisInputs):
        raise ValueError("full native acceptance needs the actual reader's distinct admitted Current Source inputs")
    if current.terminal_failure_exit() is not None:
        raise ValueError("a genuine Current interruption/timeout ended execution for the remaining format scopes")
    provider, runtime, fonts, tools = current.verified_nominees(
        operation.source, set(operation.originals), requirement.scope, operation.deadline
    )
    try:
        validate_native_acceptance(
            requirement,
            details,
            reader,
            current_source=current.source,
            current_directory=current.scope_directories[requirement.scope],
            provider_wheels=current.provider_wheels,
            pdfium_provider=provider,
            pdfium_runtime=runtime,
            office_font_files=fonts,
            current_observer_tools=tools,
        )
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as error:
        current.retain_failure(error)
        raise


def validate_installed_wheel(requirement: Requirement, details: dict[str, Any], reader: SnapshotReader) -> None:
    """Admit current wheel bytes only; this does not establish installed execution."""
    if (
        details.get("package") != requirement.package
        or details.get("version") != requirement.version
        or details.get("isolated") is not True
        or details.get("source_path_contamination") is not False
        or not isinstance(details.get("imported_modules"), list)
        or not details["imported_modules"]
        or any(not isinstance(module, str) or not module for module in details["imported_modules"])
    ):
        raise ValueError("installed-package acceptance must run the intended wheel in isolation")
    wheel = _file(details.get("wheel_artifact"), reader)
    with zipfile.ZipFile(BytesIO(wheel.content)) as archive:
        validate_wheel_members(archive, details["imported_modules"])
        validate_wheel_source(requirement.scope, archive, reader)
        metadata = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        if len(metadata) != 1:
            raise ValueError("installed version differs from wheel metadata")
        fields = Parser().parsestr(archive.read(metadata[0]).decode())

        def normalized(name: str) -> str:
            return re.sub(r"[-_.]+", "-", name).lower()

        if fields.get("Version") != requirement.version or normalized(fields.get("Name", "")) != normalized(
            requirement.package
        ):
            raise ValueError("installed package/version differs from wheel metadata")


def _installed(requirement: Requirement, details: dict[str, Any], reader: SnapshotReader) -> None:
    from infrastructure.project.installed_acceptance_validation import validate_installed_matrix

    validate_installed_wheel(requirement, details, reader)
    validate_installed_matrix(requirement, details, reader)


def _export(requirement: Requirement, details: dict[str, Any], reader: SnapshotReader) -> None:
    bundle = _file(details.get("bundle_artifact"), reader)
    manifest = _file(details.get("manifest_artifact"), reader).json_object()
    if (
        manifest.get("version") != requirement.version
        or manifest.get("platform_version") != requirement.platform_version
        or manifest.get("source_identity") != requirement.source_identity
        or manifest.get("bundle_sha256") != bundle.sha256
        or manifest.get("deliverables_identity", "") != requirement.deliverables_identity
    ):
        raise ValueError("export source/version/bytes parity is not established")
    validate_source_archive(requirement.scope, manifest, bundle.content, reader)
    reader.validated_exports[requirement.scope] = bundle.sha256
    reader.validated_export_commits.pop(requirement.scope, None)
    if requirement.scope != "root":
        with zipfile.ZipFile(BytesIO(bundle.content)) as archive:
            if ".template-export.json" in archive.namelist():
                reader.validated_export_commits[requirement.scope] = _hash(manifest.get("source_commit"), length=40)


def _live(requirement: Requirement, details: dict[str, Any], reader: SnapshotReader) -> None:
    if (
        details.get("capability") != requirement.capability
        or details.get("paid") is not False
        or details.get("execution_kind") != "actual"
    ):
        raise ValueError("a declared unpaid capability requires actual execution acceptance")
    raw = _file(details.get("execution_artifact"), reader).json_object()
    native_sia = (
        requirement.capability == "local-proposals"
        and raw.get("schema_version") == "template-sia/numeric-proposal-receipt/1"
        and raw.get("execution_mode") == "ollama_docker_numeric_proposals"
    )
    native_docker = requirement.capability == "docker-sandbox" and raw.get("runner") == "docker"
    if (
        not (raw.get("execution_kind") == "actual" or native_sia or native_docker)
        or raw.get("status") not in {"pass", "passed"}
        or not (native_sia or native_docker or raw.get("capability") == requirement.capability)
    ):
        raise ValueError("live artifact requires explicit successful actual capability execution")
    _oracles(details, reader)
    if requirement.capability == "local-proposals":
        if (
            raw.get("status") != "passed"
            or raw.get("frozen_inputs_verified") is not True
            or raw.get("execution_mode") != "ollama_docker_numeric_proposals"
            or raw.get("rollback_verified") is not True
            or raw.get("production_source_applied") is not False
            or raw.get("holdout_used_for_selection") is not False
        ):
            raise ValueError("local proposals require model, frozen-input, sandbox and rollback acceptance")
        _hash(raw.get("model_sha256"))
        _integer(raw.get("mutation_count"), minimum=1)
        _integer(raw.get("heldout_cases"), minimum=1)
    if requirement.capability == "docker-sandbox":
        if (
            raw.get("runner") != "docker"
            or raw.get("cleanup_verified") is not True
            or raw.get("status") != "passed"
            or type(raw.get("returncode")) is not int
            or raw["returncode"] != 0
            or raw.get("network") != "none"
            or raw.get("read_only_root") is not True
            or raw.get("host_credentials_forwarded") is not False
        ):
            raise ValueError("Docker capability must verify execution and daemon cleanup")
        identity = raw.get("image_id")
        if not isinstance(identity, str) or not identity.startswith("sha256:"):
            raise ValueError("Docker image must use immutable identity")
        _hash(identity.removeprefix("sha256:"))


def _publication(requirement: Requirement, details: dict[str, Any], reader: SnapshotReader) -> None:
    if requirement.draft:
        if (
            details.get("unpublished") is not True
            or details.get("intended_version") != requirement.version
            or details.get("doi") not in {None, ""}
            or details.get("actual_tag") is not None
            or details.get("published_version") is not None
        ):
            raise ValueError("draft publication evidence must remain explicitly unpublished")
        return
    if (
        details.get("actual_tag") != f"v{requirement.version}"
        or details.get("published_version") != requirement.version
        or details.get("remote_verified") is not True
    ):
        raise ValueError("actual tag and published version must be verified separately from intended metadata")
    source_commit, tag_commit, remote_commit = (
        _hash(details.get(key), length=40) for key in ("source_commit", "tag_commit", "remote_commit")
    )
    if tag_commit != remote_commit or requirement.scope == "root" and source_commit != tag_commit:
        raise ValueError("published remote/tag/source commit parity differs")
    exported = _file(details.get("export_artifact"), reader)
    retrieved = _file(details.get("retrieved_artifact"), reader)
    if exported.sha256 != retrieved.sha256:
        raise ValueError("publication retrieval differs from the verified export bytes")
    if reader.validated_exports.get(requirement.scope) != exported.sha256:
        raise ValueError("publication is not linked to the validated source/version export")
    if requirement.scope != "root" and reader.validated_export_commits.get(requirement.scope) != source_commit:
        raise ValueError("publication monorepo source commit differs from the validated canonical export origin")


def validate_acceptance(requirement: Requirement, payload: dict[str, Any], reader: SnapshotReader) -> None:
    """Validate positively reported execution, while leaving provenance with its producer."""
    details = payload.get("details")
    if not isinstance(details, dict) or _integer(details.get("execution_exit_code")) != 0:
        raise ValueError("successful acceptance requires a real zero-exit execution record")
    kind = requirement.kind
    if re.fullmatch(r"4\.\d+\.\d+", requirement.platform_version) is None:
        raise ValueError("acceptance requires a current platform 4 source contract")
    if kind in {"root-policy", "root-case"}:
        from infrastructure.reporting.release_readiness_root_cases import validate_root_cases

        _runtime_probe(requirement, details, reader)
        validate_root_cases(requirement, details, reader)
    elif kind == "runtime":
        _runtime(requirement, details)
        _runtime_probe(requirement, details, reader)
        validate_runtime_dependencies(requirement, details, reader)
    elif kind == "coverage":
        if requirement.scope == "root" and not isinstance(details.get("root_case_bundle_artifact"), dict):
            raise ValueError("Root coverage requires its complete case-policy runtime bundle")
        _coverage(requirement, details, reader)
        _runtime_probe(requirement, details, reader)
        if requirement.scope == "root":
            from infrastructure.reporting.release_readiness_root_cases import validate_root_cases

            validate_root_cases(requirement, details, reader)
        else:
            validate_runtime_dependencies(requirement, details, reader)
    elif kind == "roster":
        if details.get("projects") != list(PUBLIC_PROJECT_NAMES):
            raise ValueError("acceptance roster is incomplete")
    elif kind == "docs":
        if any(details.get(key) != [] for key in ("mermaid", "broken_links", "consistency", "doc_pairs")):
            raise ValueError("documentation lint did not execute every required category successfully")
    elif kind == "pipeline":
        from infrastructure.project.public_acceptance_auxiliary_pipeline import SCHEMA, validate_portable_pipeline

        if details.get("pipeline_schema") != SCHEMA:
            raise ValueError("pipeline requires complete portable source/process custody")
        validate_portable_pipeline(requirement.scope, details, reader)
    elif kind == "formats":
        _formats(requirement, details, reader)
    elif kind in {"domain", "oracle"}:
        _oracles(details, reader)
    elif kind == "installed":
        _installed(requirement, details, reader)
    elif kind == "export":
        _export(requirement, details, reader)
    elif kind == "live":
        _live(requirement, details, reader)
    elif kind == "publication":
        _publication(requirement, details, reader)
    elif kind == "transfer":
        from infrastructure.project.public_acceptance_auxiliary_validation import validate_sandbox_transfer

        validate_sandbox_transfer(details, reader)
        if details.get("destination_kind") != "sandbox" or details.get("remote_verified") is not True:
            raise ValueError("candidate transfer must execute against the authorized sandbox")
        exported = _file(details.get("export_artifact"), reader)
        if exported.sha256 != _file(details.get("retrieved_artifact"), reader).sha256:
            raise ValueError("sandbox retrieval differs from the source-bound exported bytes")
        if reader.validated_exports.get(requirement.scope) != exported.sha256:
            raise ValueError("sandbox transfer is not linked to the validated source/version export")
    elif kind == "platform":
        if details.get("platform") != "macos":
            raise ValueError("supported macOS platform execution is required")
        _oracles(details, reader)
    else:
        raise ValueError("unsupported required acceptance kind")
    # Every auxiliary producer requires retained original supervision.
    auxiliary_kinds = {"docs", "pipeline", "domain", "oracle", "live", "platform", "roster"}
    if kind in auxiliary_kinds:
        from infrastructure.project.public_acceptance_auxiliary_validation import validate_auxiliary_process

        validate_auxiliary_process(requirement.id, _hash(payload.get("source_fingerprint")), details, reader)
