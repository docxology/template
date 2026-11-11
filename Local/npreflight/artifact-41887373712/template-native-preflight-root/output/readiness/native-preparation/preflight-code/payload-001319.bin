"""Source-owned Root v2 case cells and original selected-interpreter acceptance."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from infrastructure.project.public_root_case_admission import load_policy
from infrastructure.project.public_root_case_units import required_cells
from infrastructure.project.public_root_runtime_producer import read_selected_runtime
from infrastructure.project.public_root_runtime_contract import runtime_projection
from infrastructure.project.public_root_case_contract import _artifact, _json
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

if TYPE_CHECKING:
    from infrastructure.reporting.release_readiness_profile import Requirement


def case_requirements(
    reader: SnapshotReader,
    *,
    version: str,
    package: str,
    fingerprint: str,
    deliverables: str,
    source_files: tuple[str, ...],
    test_files: tuple[str, ...],
) -> tuple[Requirement, ...]:
    """Declare every source-owned unit/platform/minor; no unavailable obligation can disappear."""
    from infrastructure.reporting.release_readiness_profile import Requirement

    policy, _, _, prerequisites = load_policy(reader)
    common: dict[str, Any] = {
        "scope": "root",
        "version": version,
        "platform_version": version,
        "source_identity": fingerprint,
        "deliverables_identity": deliverables,
        "package": package,
        "source_files": source_files,
        "case_policy_sha256": policy.sha256,
    }
    rows = [Requirement("root:case-policy", "root-policy", test_files=test_files, **common)]
    for cell in required_cells(policy, prerequisites):
        rows.append(
            Requirement(
                cell.id,
                "root-case",
                python_version=cell.runtime,
                case_unit=cell.unit,
                case_platform=cell.platform,
                case_nodes=cell.nodeids,
                case_obligations=cell.obligations,
                test_files=tuple(sorted({node.split("::", 1)[0] for node in cell.nodeids})),
                **common,
            )
        )
    return tuple(rows)


def validate_root_cases(requirement: Requirement, details: dict[str, Any], reader: SnapshotReader) -> dict[str, Any]:
    """Re-run the true source-audited original reader, never reinterpret another Python minor."""
    if requirement.scope != "root" or requirement.kind not in {"root-policy", "root-case", "coverage"}:
        raise ValueError("Root v2 acceptance requires an exact source-owned Root case or coverage requirement")
    if reader.hosted_origin is not None:
        from infrastructure.project.public_root_portable import read_portable_runtime

        actual = read_portable_runtime(
            reader, details.get("portable_root_artifact"), details.get("root_case_bundle_artifact")
        )
    else:
        actual = read_selected_runtime(reader, details.get("root_case_bundle_artifact"))
    policy, _, _, prerequisites = load_policy(reader)
    probe = _json(_artifact(reader, details.get("runtime_artifact")))
    if (
        runtime_projection(probe) != actual["runtime"]
        or type(probe.get("execution_exit_code")) is not int
        or probe["execution_exit_code"] != 0
        or actual["source_identity"] != requirement.source_identity
        or actual["deliverables_identity"] != requirement.deliverables_identity
        or actual["policy_artifact"]["sha256"] != details.get("policy_artifact_sha256")
        or details.get("case_policy_sha256") != policy.sha256
        or (requirement.case_policy_sha256 and requirement.case_policy_sha256 != policy.sha256)
        or details.get("python_version") != actual["runtime"]["python_version"]
        or details.get("interpreter") != actual["runtime"]["executable"]
    ):
        raise ValueError("Root v2 case evidence has stale policy/source/selected-runtime bindings")
    if requirement.kind == "root-case":
        cell = next((cell for cell in required_cells(policy, prerequisites) if cell.id == requirement.id), None)
        if (
            cell is None
            or actual["platform"] != cell.platform
            or actual["runtime"]["python_version"] != cell.runtime
            or requirement.case_unit != cell.unit
            or requirement.case_platform != cell.platform
            or requirement.case_nodes != cell.nodeids
            or requirement.case_obligations != cell.obligations
            or cell.unit not in actual["selected_units"]
            or actual["passed_counts"].get(cell.unit) != len(cell.nodeids)
            or any(
                type(details.get(key)) is not int or details[key] != len(cell.nodeids)
                for key in ("collected", "passed")
            )
            or any(
                type(details.get(key)) is not int or details[key] != 0
                for key in ("failed", "errors", "skipped", "deselected")
            )
            or details.get("test_files") != list(requirement.test_files)
        ):
            raise ValueError("Root v2 original case unit did not completely pass its exact required host/minor/members")
    elif requirement.kind == "coverage":
        if actual["runtime"]["python_version"] != requirement.python_version or actual[
            "coverage_artifact"
        ] != details.get("coverage_artifact"):
            raise ValueError(
                "Root v2 branch coverage was not independently derived from the required runtime's original arcs"
            )
    return actual
