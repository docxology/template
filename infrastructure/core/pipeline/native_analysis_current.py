"""Fresh Current execution through the existing complete native core controller.

The outer custodian supplies independently admitted Current Source, its held
separate full-Git root, and the actual live producer scope. This module does not
clone a tree, install a runtime, mint Original authority or select a test subset.
"""

from __future__ import annotations

import math
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from infrastructure.core.files.project_lock import project_output_lock
from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.plan import ExecutionPlan, compile_execution_plan
from infrastructure.core.pipeline.types import PipelineConfig
from infrastructure.project.public_acceptance_evidence import evidence_directory, write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_analysis_boundary_replay import (
    observe_native_analysis_boundary_graph,
    replay_native_analysis_boundary_graph,
)
from infrastructure.reporting.native_analysis_semantic_compare import (
    native_analysis_semantics,
    native_hydration_semantics,
    require_native_analysis_equivalence,
)
from infrastructure.reporting.native_format_joint_source import require_native_operation
from infrastructure.reporting.native_hydration_reconstruction import (
    observe_native_hydration_reconstruction,
    replay_native_hydration_reconstruction,
)
from infrastructure.reporting.native_project_domain import (
    MODULES as DOMAIN_MODULES,
    _validate as validate_project_suite,
    observe_native_project_domain,
)
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.native_tool_replay import authenticate_original_native_artifact
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

from infrastructure.validation.publication.audit import build_native_published_audit

SCHEMA = "template-native-current-analysis-reexecution-v2"


class NativeCurrentFailed(ValueError):
    """Direct failure DATA; no successful current or Original authority."""

    native_current_pipeline: dict[str, Any]


class NativeCurrentTimedOut(TimeoutError):
    """Actual returned Current timeout plus separately retained failure DATA."""

    native_current_pipeline: dict[str, Any]


class NativeCurrentInterrupted(InterruptedError):
    """Actual returned Current interruption plus failure DATA."""

    native_current_pipeline: dict[str, Any]


def _binding(value: object, reader: SnapshotReader) -> ArtifactSnapshot:
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise ValueError("current analysis needs an exact nominated held artifact binding")
    item = reader.read(value["path"])
    if item.sha256 != value["sha256"]:
        raise ValueError("current analysis nominated held artifact changed")
    return item


def _plan_meaning(plan: ExecutionPlan) -> dict[str, Any]:
    # The fresh compiler separately admits its current environment and physical
    # executable targets. Only that physical environment digest differs here;
    # the finite budget and every stage/hook/policy/contract remain exact.
    body = plan.to_dict()
    return {key: value for key, value in body.items() if key != "environment_identity"}


def _require_core(plan: ExecutionPlan) -> None:
    from infrastructure.reporting.native_format_acceptance_worker import require_canonical_native_stages

    require_canonical_native_stages(plan)
    if plan.mode != "core" or any({"paid", "live", "llm"}.intersection(stage.tags) for stage in plan.stages):
        raise ValueError("current analysis uses the existing complete local core plan only")


def _original_suite(
    value: object,
    scope: str,
    reader: SnapshotReader,
    *,
    run_id: str,
    deadline: float,
) -> dict[str, Any]:
    authority = authenticate_original_native_artifact(value, reader, run_id=run_id, required_sdk_modules=DOMAIN_MODULES)
    packet = authority["event"].json_object()
    if packet.get("scope") != scope or packet.get("run_id") != run_id:
        raise ValueError("current analysis original suite belongs to another held scope/run")
    return validate_project_suite(
        packet,
        reader,
        authority["operation"].source,
        original=True,
        deadline=deadline,
        source_labels=authority["source"],
    )


def replay_current_native_analysis(
    scope: str,
    native_execution: ArtifactSnapshot,
    original_reader: SnapshotReader,
    current_source: NativeSourceContext,
    *,
    directory: Path,
    original_domain: object,
    provider_wheels: Mapping[str, Path],
    current_domain: object | None = None,
) -> dict[str, Any]:
    """Rerun all current stages once for this scope, then compare whole graphs.

    An optional Current suite is only nomination DATA. It is reused exclusively
    while its real current ToolAPI owner remains live and validates the complete
    configured suite, Source/body selection and clock. Otherwise this operation
    executes one full configured cell for this scope using the existing adapter.
    There is no per-leaf or all-project sweep and no status-based reuse.
    """
    operation = require_native_operation(original_reader)
    original = operation.originals.get(scope)
    owner = current_native_producer_operation()
    if (
        scope not in PUBLIC_PROJECT_NAMES
        or not isinstance(current_source, NativeSourceContext)
        or original is None
        or owner is None
        or owner.source is not current_source
        or owner.deadline != operation.deadline
        or owner.run_id == original.run_id
        or directory != owner.stage_scope_directory(scope)
    ):
        raise ValueError("current analysis needs its actual independent Source owner, scope and original live clock")
    root = current_source.bindings.current_root
    if (
        root == original_reader.root
        or root.is_relative_to(original_reader.root)
        or original_reader.root.is_relative_to(root)
        or current_source.bindings.current_root_identity == operation.source.bindings.current_root_identity
        or current_source.reference.commit != operation.source.reference.commit
        or current_source.reference.source_identity != operation.source.reference.source_identity
        or current_source.bindings.expected_implementation_bytes
        != operation.source.bindings.expected_implementation_bytes
        or native_execution.relative != original.native_execution_relative
        or native_execution.sha256 != original.native_execution_sha256
        or original_reader.read(native_execution.relative) != native_execution
    ):
        raise ValueError("current analysis cannot mutate transported Original or change its exact Source/selected SDK")
    remaining(operation.deadline)
    current_reader = SnapshotReader(root, native_producer_operation=owner)
    owner.verify(current_reader, run_id=owner.run_id, deadline=operation.deadline)
    original_graph = replay_native_analysis_boundary_graph(scope, native_execution, original_reader)
    original_semantics = native_analysis_semantics(original_graph, original_reader, deadline=operation.deadline)
    original_hydration = replay_native_hydration_reconstruction(scope, native_execution, original_reader)
    original_hydration_semantics = native_hydration_semantics(original_hydration)
    original_cases = _original_suite(
        original_domain,
        scope,
        original_reader,
        run_id=original.run_id,
        deadline=operation.deadline,
    )
    raw = native_execution.json_object()
    pipeline = raw["pipeline"]
    if pipeline.get("selection") != {"skip_clean": True, "skip_infra": True}:
        raise ValueError("current analysis refuses a different original canonical core selection")
    original_plan = ExecutionPlan.from_dict(pipeline["plan"], expected_digest=pipeline["plan_digest"])
    _require_core(original_plan)
    budget = original_plan.run_timeout_seconds
    if type(budget) not in (int, float) or not math.isfinite(budget) or budget <= 0:
        raise ValueError("current analysis original configured plan lacks its finite Source budget")
    config = PipelineConfig(scope, root, clean=False, skip_infra=True, mode="core", run_timeout_seconds=budget)
    plan = compile_execution_plan(config)
    _require_core(plan)
    plan.admit_targets(root)
    if _plan_meaning(plan) != _plan_meaning(original_plan):
        raise ValueError("current analysis changed the complete original Source stage/hook/policy/contract plan")
    current_reader.read(plan.provenance)
    evidence = evidence_directory(root, directory / "current-analysis", fresh=True)

    pipeline_record: dict[str, Any] | None = None
    pipeline_binding: dict[str, str] | None = None
    try:
        with project_output_lock(config.project_dir, timeout=remaining(operation.deadline)):
            published = build_native_published_audit(
                current_source,
                scope,
                current_reader,
                deadline=operation.deadline,
            )
            published_binding = write_json(root, evidence / "published-source-audit.json", published.to_dict())
            executor = PipelineExecutor(config)
            results = executor.execute_plan(plan, deadline_monotonic=operation.deadline)
            outcome = executor.run_result(results)
            pipeline_record = {
                "mode": "core",
                "run_id": executor.run_id,
                "plan": plan.to_dict(),
                "plan_digest": plan.digest,
                "expected_stage_keys": list(plan.expected_stage_keys),
                "outcomes": [item.to_dict() for item in outcome.outcomes],
                "execution_exit_code": outcome.exit_code,
                "deadline_monotonic": operation.deadline,
                "published_source_audit_artifact": published_binding,
            }
            if (
                not outcome.complete
                or outcome.exit_code
                or any(item.status.value != "succeeded" for item in outcome.outcomes)
            ):
                # These directly returned outcomes are DATA. Do not ask an expired
                # admission getter to authorize child/tool custody before retaining
                # actual failure, or turn absent post-deadline nominations into [].
                pipeline_record.update(
                    stage_children=None,
                    tool_artifacts=None,
                    nomination_diagnostic="successful live-owner custody not admitted for failed Current core",
                )
                failure: NativeCurrentFailed | NativeCurrentTimedOut | NativeCurrentInterrupted = (
                    NativeCurrentInterrupted("fresh Current core execution was interrupted")
                    if outcome.exit_code == 130
                    else NativeCurrentTimedOut("fresh Current core execution exhausted its actual clock")
                    if outcome.exit_code == 124
                    else NativeCurrentFailed("fresh Current complete core plan did not succeed")
                )
                persistence_diagnostic = "original Current deadline expired; no post-deadline persistence attempted"
                retained = None
                if time.monotonic() < operation.deadline:
                    try:
                        retained = write_json(root, evidence / "pipeline.json", pipeline_record)
                        persistence_diagnostic = ""
                    except (OSError, ValueError, TimeoutError) as error:
                        persistence_diagnostic = str(error)
                # Direct failure DATA survives unavailable persistence. This field
                # is never inspected by an Original authentication or success role.
                failure.native_current_pipeline = {
                    "observation": pipeline_record,
                    "artifact": retained,
                    "persistence_diagnostic": persistence_diagnostic,
                }
                raise failure
            pipeline_binding = write_json(
                root,
                evidence / "pipeline.json",
                {
                    **pipeline_record,
                    "stage_children": list(owner.stage_children),
                    "tool_artifacts": list(owner.retained_tool_bindings),
                },
            )
            graph_reader = SnapshotReader(root, native_producer_operation=owner)
            current_graph = observe_native_analysis_boundary_graph(
                current_source,
                scope,
                executor.run_id,
                plan.digest,
                graph_reader,
                deadline=operation.deadline,
            )
            current_semantics = native_analysis_semantics(current_graph, graph_reader, deadline=operation.deadline)
            if scope != "templates/template_code_project":
                require_native_analysis_equivalence(original_semantics, current_semantics)
            current_hydration = observe_native_hydration_reconstruction(
                current_source,
                scope,
                executor.run_id,
                plan.digest,
                graph_reader,
                deadline=operation.deadline,
            )
            if scope != "templates/template_code_project":
                require_native_analysis_equivalence(
                    original_hydration_semantics, native_hydration_semantics(current_hydration)
                )
            graph_binding = write_json(root, evidence / "analysis-graph.json", current_graph)
            hydration_binding = write_json(root, evidence / "hydration-graph.json", current_hydration)
            if not graph_reader.unchanged():
                raise ValueError("Current graph bodies changed before full configured suite consumption")
            if current_domain is None:
                current_domain = observe_native_project_domain(
                    current_source,
                    scope,
                    evidence / "domain",
                    SnapshotReader(root),
                    deadline=operation.deadline,
                    provider_wheels=provider_wheels,
                )
            suite_reader = SnapshotReader(root, native_producer_operation=owner)
            current_suite = _binding(current_domain, suite_reader)
            current_packet = current_suite.json_object()
            if current_packet.get("scope") != scope or current_packet.get("run_id") != owner.run_id:
                raise ValueError("Current configured suite belongs to another real owner scope/run")
            current_cases = validate_project_suite(
                current_packet,
                suite_reader,
                current_source,
                original=False,
                deadline=operation.deadline,
            )
            if current_cases != original_cases:
                raise ValueError("fresh Current complete configured suite/case union differs from actual Original")
            # Full suites may exercise generated files. Rebuild afterwards rather
            # than allowing a prior graph to approve newly changed deliverables.
            final_reader = SnapshotReader(root, native_producer_operation=owner)
            final_graph = observe_native_analysis_boundary_graph(
                current_source,
                scope,
                executor.run_id,
                plan.digest,
                final_reader,
                deadline=operation.deadline,
            )
            final_semantics = native_analysis_semantics(final_graph, final_reader, deadline=operation.deadline)
            if scope != "templates/template_code_project":
                require_native_analysis_equivalence(original_semantics, final_semantics)
            final_hydration = observe_native_hydration_reconstruction(
                current_source,
                scope,
                executor.run_id,
                plan.digest,
                final_reader,
                deadline=operation.deadline,
            )
            if scope != "templates/template_code_project":
                require_native_analysis_equivalence(
                    original_hydration_semantics, native_hydration_semantics(final_hydration)
                )
            # An actual suite can replace a Current named output with identical
            # bytes. Reauthenticate retained leaves/roles and every current body;
            # do not mistake the earlier named inode for immutable evidence.
            if (
                final_graph != current_graph
                or final_hydration != current_hydration
                or _binding(graph_binding, final_reader).json_object() != current_graph
                or _binding(hydration_binding, final_reader).json_object() != current_hydration
                or not suite_reader.unchanged()
                or not final_reader.unchanged()
            ):
                raise ValueError("Current graph/suite retained bodies changed across full configured qualification")
            code_value_join = None
            if scope == "templates/template_code_project":
                from infrastructure.reporting.native_code_consumed_value_join import join_code_consumed_value

                original_value = join_code_consumed_value(
                    operation.source,
                    original_reader,
                    original_graph,
                    original_hydration,
                    deadline=operation.deadline,
                )
                current_value = join_code_consumed_value(
                    current_source,
                    final_reader,
                    final_graph,
                    final_hydration,
                    deadline=operation.deadline,
                )
                from infrastructure.reporting.native_code_contextual_compare import code_contextual_semantics

                original_comparable = code_contextual_semantics(
                    operation.source,
                    original_reader,
                    original_graph,
                    original_hydration,
                    original_value,
                    deadline=operation.deadline,
                )
                current_comparable = code_contextual_semantics(
                    current_source,
                    final_reader,
                    final_graph,
                    final_hydration,
                    current_value,
                    deadline=operation.deadline,
                )
                require_native_analysis_equivalence(original_comparable[0], current_comparable[0])
                require_native_analysis_equivalence(original_comparable[1], current_comparable[1])

                from infrastructure.reporting.native_code_scalar_domains import code_consumed_value_meaning

                if code_consumed_value_meaning(
                    original_value, deadline=operation.deadline
                ) != code_consumed_value_meaning(current_value, deadline=operation.deadline):
                    raise ValueError("fresh Current selected Code field meaning differs from checked Original")
                code_value_join = {"original": original_value, "current": current_value}
            owner.verify(final_reader, run_id=owner.run_id, deadline=operation.deadline)
        if not original_reader.unchanged():
            raise ValueError("transported Original evidence changed during separate Current execution")
        operation.verify(original_reader)
        remaining(operation.deadline)
        return write_json(
            root,
            evidence / "current-analysis-comparison.json",
            {
                "schema_version": SCHEMA,
                "scope": scope,
                "original_execution": {"path": native_execution.relative, "sha256": native_execution.sha256},
                "current_pipeline": pipeline_binding,
                "current_graph": graph_binding,
                "current_domain": current_domain,
                "current_hydration": hydration_binding,
                "semantic_comparison_digest": original_semantics["content_digest"],
                "hydration_comparison_digest": original_hydration_semantics["content_digest"],
                "complete_configured_cases": current_cases,
                "current_run_id": owner.run_id,
                "deadline_monotonic": operation.deadline,
                "code_consumed_value_join": code_value_join,
                "unresolved_edges": [
                    *original_graph["unresolved_edges"],
                    *([] if code_value_join is None else code_value_join["original"]["residuals"]),
                    *([] if code_value_join is None else code_value_join["current"]["residuals"]),
                ],
                "claim_boundary": (
                    "fresh-complete-current-core-and-declared-suite-equivalence; "
                    "not-full-native-or-all-domain-admission"
                ),
            },
        )
    except BaseException as error:
        # This is the already returned Core outcome, including an actual 0.
        # A later graph/suite/custody refusal must not rewrite it or erase a
        # distinct Source Common suite attempt carried by the same exception.
        if pipeline_record is not None and not isinstance(getattr(error, "native_current_pipeline", None), dict):
            setattr(
                error,
                "native_current_pipeline",
                {
                    "observation": pipeline_record,
                    "artifact": pipeline_binding,
                    "persistence_diagnostic": ""
                    if pipeline_binding is not None
                    else "Core outcome observed; pipeline retention unavailable",
                },
            )
        raise
