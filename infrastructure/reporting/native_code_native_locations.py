"""One real own-format ordinal capture per selected Code artifact/phase.

The existing producer or authenticated Original reader supplies Source and
clock custody. Complete format/native/control qualification remains with the
existing phase collector. No receipt creates a native owner or pass.
"""

from __future__ import annotations

from typing import Any

import yaml

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_reference_git import remaining
from infrastructure.rendering._pdf_combined_markdown import preprocess_combined_markdown
from infrastructure.rendering._pdf_title_page_config import _rendering_options
from infrastructure.rendering.manuscript_hydration_replay import combine_held_manuscripts
from infrastructure.rendering.manuscript_ordinal_anchors import (
    annotate_manuscript_ordinals,
    require_complete_ordinal_ast_equivalence,
    require_unannotated_parser_bytes,
)
from infrastructure.reporting.native_code_native_endpoints import office_native_endpoints, pdf_native_endpoints
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_format_acceptance_evidence import _file, _tool
from infrastructure.reporting.native_format_pdf_source import pdf_source_inputs
from infrastructure.reporting.native_hydration_reconstruction import replay_native_pdf_recomposition
from infrastructure.reporting.native_office_hydration_ordinals import observe_office_hydration_ordinals
from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime
from infrastructure.reporting.native_pdf_hydration_ordinals import observe_pdf_hydration_ordinals
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

CODE_SCOPE = "templates/template_code_project"


def _binding(snapshot: ArtifactSnapshot) -> dict[str, Any]:
    return {"path": snapshot.relative, "sha256": snapshot.sha256, "bytes": len(snapshot.content)}


def _inputs(artifact: NativeArtifact, observer: dict[str, Any], reader: SnapshotReader) -> list[dict[str, Any]]:
    if artifact.format in {"docx", "epub"}:
        rows = observer["office_complete_source"]["reference"]["source"]["sources"]
    elif artifact.format == "html":
        rows = observer["semantic_source"]["body"]["contract"]["sources"]
    else:
        rows = observer["scientific_pdf_source"]["semantic_plan"]["sources"]
    result = []
    for row in rows:
        path, digest = (row["path"], row["sha256"]) if isinstance(row, dict) else row
        snapshot = reader.read(path)
        if snapshot.sha256 != digest:
            raise ValueError("selected native locations changed its complete own-format input roster")
        if path.endswith((".md", ".tex")):
            result.append(_binding(snapshot))
    if not result or len({row["path"] for row in result}) != len(result):
        raise ValueError("selected native locations omitted/repeated its complete own Source input roster")
    return result


def _selected(
    hydration: dict[str, Any], inputs: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], tuple[tuple[int, int, str, int, int, str], ...]]:
    consumed = {row["consumed"]["path"]: row for row in hydration["ordered_inputs"]}
    if len(consumed) != len(hydration["ordered_inputs"]):
        raise ValueError("selected native locations repeated an actual hydration input")
    rows: list[dict[str, Any]] = []
    selected: list[tuple[int, int, str, int, int, str]] = []
    for index, binding in enumerate(inputs):
        row = consumed[binding["path"]]
        if row["consumed"] != binding:
            raise ValueError("selected native locations changed the actual complete hydration input body")
        if row["transformation"] == "shared-uppercase-token-hydration":
            for token in row["hydration"]["occurrences"]:
                if token["resolved"] is not True:
                    raise ValueError("selected native locations cannot confer unresolved generated values")
                rows.append({"source": row["source"], "consumed": binding, **token})
                selected.append(
                    (
                        index,
                        token["ordinal"],
                        token["key"],
                        token["output_start_byte"],
                        token["output_end_byte"],
                        token["replacement_sha256"],
                    )
                )
        elif row["transformation"] not in {"exact-authored-source-body", "Source-generated-transmission-boundary"}:
            raise ValueError("selected native locations requires its actual qualified Source hydration adapter")
    return rows, tuple(selected)


def _endpoints(
    artifact: NativeArtifact,
    ordinal: dict[str, Any],
    observer: dict[str, Any],
    pdf: dict[str, Any] | None,
    reader: SnapshotReader,
) -> list[dict[str, Any]]:
    ast = _file(ordinal["actual_parser_ast"], reader)
    result = []
    for occurrence in ordinal["occurrences"]:
        if artifact.format == "pdf":
            predicates = (observer.get("current_whole_pdf") or pdf or {}).get("source_predicates")
            if not isinstance(predicates, dict):
                endpoints = {"roles": [], "residuals": ["selected-PDF-complete-native-predicates-unavailable"]}
            else:
                endpoints = pdf_native_endpoints(ast.content, occurrence["ast"], predicates)
        elif artifact.format in {"docx", "epub"}:
            endpoints = office_native_endpoints(
                ast.content, occurrence["ast"], observer["observation"]["source_survival"]
            )
        else:
            from infrastructure.reporting.native_html_hydration_ordinals import html_native_endpoints

            original_ast = _file(ordinal["actual_original_ast"], reader)
            endpoints = html_native_endpoints(
                original_ast.content,
                occurrence["original_ast"],
                observer,
                reader,
                ordinal_occurrence=occurrence,
            )
        result.append({**occurrence, **endpoints})
    return result


def observe_code_native_locations(
    source: NativeSourceContext,
    reader: SnapshotReader,
    analysis: dict[str, Any],
    hydration: dict[str, Any],
    artifacts: tuple[tuple[NativeArtifact, dict[str, Any], dict[str, Any] | None], ...],
    *,
    env: dict[str, str],
    deadline: float,
) -> dict[str, Any] | None:
    """Capture under the actual existing live Source owner; never repeat Core."""
    if analysis["scope"] != CODE_SCOPE:
        return None
    owner = current_native_producer_operation()
    if (
        owner is None
        or owner.source is not source
        or reader.native_producer_operation is not owner
        or owner.deadline != deadline
    ):
        raise ValueError("selected native locations needs its actual Source owner/reader/clock")
    if any(analysis[name] != hydration[name] for name in ("scope", "source_binding", "pipeline_run_id", "plan_digest")):
        raise ValueError("selected native locations changed its complete actual Source graph join")
    owner.verify(reader, run_id=owner.run_id, deadline=deadline)
    rows = []
    for index, (artifact, observer, pdf) in enumerate(artifacts):
        inputs = _inputs(artifact, observer, reader)
        selected, _ = _selected(hydration, inputs)
        row: dict[str, Any] = {
            "artifact_id": artifact.id,
            "format": artifact.format,
            "source_inputs": inputs,
            "ordinal_observation": None,
            "dotted_variables": None,
            "occurrences": [],
        }
        if selected:
            runtime = CitationRuntime(
                reader.root,
                owner.stage_scope_directory(CODE_SCOPE) / f"code-native-ordinals-{index}",
                env=env,
                deadline=deadline,
                run_id=owner.run_id,
            )
            if artifact.format == "pdf":
                source_row = observer["scientific_pdf_source"]["source"]
                plan = pdf_source_inputs(
                    reader.root, runtime.directory / "own-pdf-inputs", CODE_SCOPE, artifact, reader
                )
                if [_binding(reader.read(path)) for path, _ in plan.sources] != inputs:
                    raise ValueError("selected PDF ordinals changed its actual own input factory")
                ordinal = observe_pdf_hydration_ordinals(
                    CODE_SCOPE,
                    plan,
                    hydration,
                    _file(source_row["markdown"], reader),
                    _file(source_row["ast"], reader),
                    source_row["parser_artifact"],
                    reader,
                    runtime,
                    source=source,
                )
            elif artifact.format in {"docx", "epub"}:
                ordinal = observe_office_hydration_ordinals(
                    CODE_SCOPE,
                    artifact,
                    observer["office_complete_source"]["reference"]["source"],
                    hydration,
                    reader,
                    runtime,
                    source=source,
                )
            elif artifact.format == "html":
                from infrastructure.reporting.native_html_hydration_ordinals import observe_html_hydration_ordinals

                ordinal = observe_html_hydration_ordinals(
                    CODE_SCOPE, artifact, observer["semantic_source"], hydration, reader, runtime, source=source
                )
            else:
                raise ValueError("selected Code artifact has no own-format complete ordinal adapter")
            if [item["hydration"] for item in ordinal["occurrences"]] != selected:
                raise ValueError("selected native ordinal omitted/reordered the complete own input occurrence roster")
            dotted = runtime.directory / "manuscript_vars.yaml"
            row["dotted_variables"] = (
                _binding(reader.read(dotted.relative_to(reader.root).as_posix())) if dotted.exists() else None
            )
            row["ordinal_observation"] = ordinal
            row["occurrences"] = _endpoints(artifact, ordinal, observer, pdf, reader)
            runtime.unchanged()
        rows.append(row)
    if len({row["artifact_id"] for row in rows}) != len(rows):
        raise ValueError("selected native locations repeated its complete artifact roster")
    owner.verify(reader, run_id=owner.run_id, deadline=deadline)
    source.verify_correspondence(source.reference, reader.root, reader, deadline)
    if not reader.unchanged():
        raise ValueError("selected native locations changed before actual closing custody")
    body = {
        "scope": CODE_SCOPE,
        "run_id": owner.run_id,
        "source_binding": analysis["source_binding"],
        "pipeline_run_id": analysis["pipeline_run_id"],
        "plan_digest": analysis["plan_digest"],
        "analysis_digest": analysis["content_digest"],
        "hydration_digest": hydration["content_digest"],
        "artifacts": rows,
    }
    return {**body, "content_digest": canonical_digest(body)}


def replay_code_native_locations(
    capture: dict[str, Any] | None,
    execution: ArtifactSnapshot,
    reader: SnapshotReader,
    analysis: dict[str, Any],
    hydration: dict[str, Any],
    artifacts: tuple[tuple[NativeArtifact, dict[str, Any], dict[str, Any] | None], ...],
    *,
    custody: dict[str, str],
) -> dict[str, Any] | None:
    """Reconstruct actual Original bytes/sites and authenticate retained Tools."""
    if analysis["scope"] != CODE_SCOPE:
        if capture is not None:
            raise ValueError("non-Code scope has a foreign selected native location capture")
        return None
    from infrastructure.reporting.native_format_joint_source import require_native_operation
    from infrastructure.reporting.native_format_portable_custody import producer_path
    from infrastructure.reporting.native_tool_replay import validate_original_native_tool

    operation = require_native_operation(reader)
    original = operation.originals[CODE_SCOPE]
    graph, _ = replay_native_pdf_recomposition(CODE_SCOPE, execution, reader)
    if graph != hydration or not isinstance(capture, dict):
        raise ValueError("selected Original native locations omitted its genuine complete Source reconstruction")
    expected = {
        "scope": CODE_SCOPE,
        "run_id": original.run_id,
        "source_binding": analysis["source_binding"],
        "pipeline_run_id": analysis["pipeline_run_id"],
        "plan_digest": analysis["plan_digest"],
        "analysis_digest": analysis["content_digest"],
        "hydration_digest": hydration["content_digest"],
    }
    if (
        any(capture.get(name) != value for name, value in expected.items())
        or capture.get("content_digest")
        != canonical_digest({key: value for key, value in capture.items() if key != "content_digest"})
        or [row["artifact_id"] for row in capture["artifacts"]] != [artifact.id for artifact, _, _ in artifacts]
    ):
        raise ValueError("selected Original native locations changed its actual Source/run/complete artifact roster")
    for retained, (artifact, observer, pdf) in zip(capture["artifacts"], artifacts, strict=True):
        inputs = _inputs(artifact, observer, reader)
        selected, selectors = _selected(hydration, inputs)
        if retained["source_inputs"] != inputs or retained["format"] != artifact.format:
            raise ValueError("selected Original native locations changed its complete own-format input roster")
        ordinal = retained["ordinal_observation"]
        if not selected:
            if ordinal is not None or retained["occurrences"] != [] or retained["dotted_variables"] is not None:
                raise ValueError("selected Source absence cannot mint a native ordinal capture")
            continue
        if not isinstance(ordinal, dict) or ordinal["comparison_completed"] is not True:
            raise ValueError("selected Original native locations lack a complete genuine own-format ordinal parse")
        if artifact.format == "html":
            from infrastructure.reporting.native_html_hydration_ordinals import replay_html_hydration_ordinals

            checked = replay_html_hydration_ordinals(
                artifact,
                ordinal,
                hydration,
                inputs,
                reader,
                custody=custody,
                run_id=original.run_id,
                html_source=observer["semantic_source"],
            )
            if checked != ordinal or retained["occurrences"] != _endpoints(artifact, checked, observer, pdf, reader):
                raise ValueError(
                    "selected Original HTML endpoints changed its complete actual own Source/parser/native join"
                )
            continue
        annotated = _file(ordinal["annotated_markdown"], reader)
        ast = _file(ordinal["annotated_ast"], reader)
        actual_md, actual_ast = (
            _file(ordinal["actual_parser_input"], reader),
            _file(ordinal["actual_parser_ast"], reader),
        )
        bodies, anchors = annotate_manuscript_ordinals(
            tuple(reader.read(row["path"]).content for row in inputs), selectors
        )
        dotted = retained["dotted_variables"]
        if dotted is not None:
            dotted_snapshot = _file(dotted, reader)
            if dotted_snapshot.path != annotated.path.parent / "manuscript_vars.yaml":
                raise ValueError("selected Original ordinal dotted variables escaped the actual parser input directory")
        config = _file(hydration["config"], reader)
        separator = (
            "\n```{=latex}\n\\newpage\n```\n"
            if _rendering_options(yaml.safe_load(config.content))["section_breaks"]
            else ""
        )
        joined = combine_held_manuscripts(bodies, separator=separator).decode()
        expected_md = preprocess_combined_markdown(joined, manuscript_dir=annotated.path.parent).content.encode()
        if annotated.content != expected_md:
            raise ValueError("selected Original ordinal anchors changed their actual Source payload position")
        ranges = require_unannotated_parser_bytes(annotated.content, actual_md.content, anchors)
        mapping = require_complete_ordinal_ast_equivalence(ast.content, actual_ast.content, anchors)
        if artifact.format == "pdf":
            own_source = observer["scientific_pdf_source"]["source"]
            parser_bindings = (own_source["markdown"], own_source["ast"], own_source["parser_artifact"])
            variables = [
                item
                for item in own_source["source_inputs"]
                if item["role"] == "auxiliary" and item["path"].endswith("/manuscript_vars.yaml")
            ]
        elif artifact.format in {"docx", "epub"}:
            own_source = observer["office_complete_source"]["reference"]["source"]
            parser_bindings = (own_source["source"], own_source["ast"], own_source["tool"]["artifact"])
            variables = [] if own_source["variables"] is None else [own_source["variables"]]
            if _file(ordinal["unfiltered_source_ast"], reader) != _file(own_source["source_coverage_ast"], reader):
                raise ValueError("selected Original Office endpoint relabeled its genuine unfiltered Source AST")
        else:
            own_source = observer["semantic_source"]["body"]
            parser_bindings = (own_source["source"], own_source["ast"], own_source["tool"]["artifact"])
            variables = []
        if (
            actual_md != _file(parser_bindings[0], reader)
            or actual_ast != _file(parser_bindings[1], reader)
            or ordinal["actual_parser_tool"] != parser_bindings[2]
        ):
            raise ValueError("selected Original endpoint relabeled a foreign actual own-format Source parser")
        if artifact.format != "html" and (
            len(variables) > 1
            or bool(variables) != (dotted is not None)
            or variables
            and _file(variables[0], reader).content != _file(dotted, reader).content
        ):
            raise ValueError("selected Original dotted variables changed its actual Source input bytes")
        original_tool = _file(ordinal["actual_parser_tool"], reader).json_object()
        original_process = _file(original_tool["native_process_artifact"], reader).json_object()
        observed_tools = ordinal["tool_bindings"]
        if len(observed_tools) != 1:
            raise ValueError("selected Original ordinal requires its one complete actual parser ToolAPI")
        binding = observed_tools[0]
        observed = _file(binding, reader).json_object()
        helper = {"pdf": "native_pdf_hydration_ordinals.py", "html": "native_html_hydration_ordinals.py"}.get(
            artifact.format, "native_office_hydration_ordinals.py"
        )
        validate_original_native_tool(
            binding,
            observed,
            reader,
            run_id=original.run_id,
            required_sdk_modules=(
                "reporting/native_tool_process.py",
                "reporting/native_pdf_citation_runtime.py",
                "reporting/native_code_native_locations.py",
                "reporting/" + helper,
                "rendering/manuscript_ordinal_anchors.py",
            ),
        )
        purpose = {"pdf": "source-hydration-ordinal-ast", "html": "source-hydration-ordinal-html-ast"}.get(
            artifact.format, "source-hydration-ordinal-office-ast"
        )
        arguments = [str(producer_path(custody, reader.root, annotated.path)), *original_tool["command"][2:]]
        _tool(binding, reader, original.run_id, "pandoc", purpose, arguments)
        if observed["stdout"].encode() != ast.content or any(
            observed[name] != original_tool[name] for name in ("executable", "executable_sha256", "environment_digest")
        ):
            raise ValueError("selected Original ordinal changed its genuine own-format filter runtime/output")
        if observed["cwd"] != original_process["cwd"]:
            raise ValueError("selected Original ordinal changed its actual own-filter CWD")
        reconstructed = [
            {
                "hydration": token,
                "parser_byte_range": list(span),
                "parser_carrier_byte_range": [span[0] - len(anchor.prefix), span[1] + len(anchor.suffix)],
                "ast": position,
            }
            for token, span, position, anchor in zip(selected, ranges, mapping, anchors, strict=True)
        ]
        if ordinal["occurrences"] != reconstructed or retained["occurrences"] != _endpoints(
            artifact, ordinal, observer, pdf, reader
        ):
            raise ValueError(
                "selected Original native locations differ from complete actual Source/parser/native reconstruction"
            )
    operation.verify(reader)
    if not reader.unchanged():
        raise ValueError("selected Original native locations changed before closing custody")
    remaining(operation.deadline)
    return capture
