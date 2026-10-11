"""One per-scope join of actual Code plot writes to selected Source assets.

This runs only within the caller's already genuine complete analysis role. Its
DATA return cannot admit a role or replace native image/layout/library controls.
Unknown selected generated figures retain their own precise residual.
"""

from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_code_consumed_value_join import _scalar_config
from infrastructure.reporting.native_code_figure_domains import (
    SELECTED,
    expected_figure_payloads,
    validate_figure_payload,
)
from infrastructure.reporting.native_code_stability_domain import _sdk_execution
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

SCOPE = "templates/template_code_project"
PROJECT = "projects/" + SCOPE
SRC = PROJECT + "/src/template_code_project"
CAPTURE = "core/analysis_figure_custody.py"
PRODUCERS = {
    "convergence_plot.png": ("convergence.py", "generate_convergence_plot"),
    "convergence_rate_comparison.png": ("convergence.py", "generate_convergence_rate_plot"),
    "step_size_sensitivity.png": ("sensitivity.py", "generate_step_size_sensitivity_plot"),
    "algorithm_complexity.png": ("scientific_complexity.py", "generate_complexity_visualization"),
    "stability_analysis.png": ("scientific_stability.py", "generate_stability_visualization"),
    "performance_benchmark.png": ("scientific_stability.py", "generate_benchmark_visualization"),
}


def _binding(item: ArtifactSnapshot) -> dict[str, Any]:
    return {"path": item.relative, "sha256": item.sha256, "bytes": len(item.content)}


def _source_actor(actor: dict[str, Any], source: NativeSourceContext, path: str, function: str) -> None:
    if (
        actor["source"] != path
        or actor["function"] != function
        or actor["source_sha256"] != hashlib.sha256(source.reference.read(path)).hexdigest()
    ):
        raise ValueError("Code figure event lost its actual admitted Source frame/body")


def _actual_body(event: dict[str, Any], snapshot: ArtifactSnapshot) -> None:
    if (event["sha256"], event["bytes"]) != (snapshot.sha256, len(snapshot.content)):
        raise ValueError("Code figure body differs from the actual completed Source API event")


def _capture_execution(
    source: NativeSourceContext, reader: SnapshotReader, stage: dict[str, Any], *, deadline: float
) -> dict[str, Any] | None:
    """Reopen the enclosing authenticated stage's actual executed SDK body."""
    binding = stage["native_stage_original"]["source_closure"]
    snapshot = reader.read(binding["path"], max_bytes=64 * 1024 * 1024)
    if snapshot.sha256 != binding["sha256"]:
        raise ValueError("Code figure actual stage Source closure changed")
    closure = snapshot.json_object()
    nominated = str(Path(closure["source_roots"][0]) / CAPTURE)
    expected = source.reference.read("infrastructure/" + CAPTURE)
    found = []
    for row in closure["executions"]:
        remaining(deadline)
        if row["source_path"] != nominated:
            continue
        held = reader.read(
            (snapshot.path.parent / row["source"]["path"]).relative_to(reader.root).as_posix(), max_bytes=1024 * 1024
        )
        if (
            not row["runs"]
            or held.sha256 != row["source"]["sha256"]
            or len(held.content) != row["source"]["bytes"]
            or held.content != expected
        ):
            raise ValueError("Code figure executed SDK capture body differs from admitted Source")
        found.append({"closure": binding, "execution": row, "held_source": _binding(held)})
    if len(found) > 1:
        raise ValueError("Code figure actual capture execution roster is duplicated")
    return found[0] if found else None


def join_code_figure_domains(
    source: NativeSourceContext,
    reader: SnapshotReader,
    analysis: dict[str, Any],
    selected_assets: tuple[tuple[str, dict[str, str]], ...],
    *,
    deadline: float,
) -> dict[str, Any]:
    """Use one genuine graph/Source roster and one independent model per scope.

    selected_assets is the actual complete Source/native asset return, retained
    by the enclosing observer. It nominates consumption, never an authority.
    The enclosing Original/live Current role authenticates graph/owner and all
    Source/native asset predicates before and after this direct DATA function.
    """
    remaining(deadline)
    if (
        reader.root != source.bindings.current_root
        or analysis["scope"] != SCOPE
        or analysis["source_binding"] != [source.reference.commit, source.reference.source_identity]
        or analysis["content_digest"] != canonical_digest({k: v for k, v in analysis.items() if k != "content_digest"})
    ):
        raise ValueError("Code figure join lost its exact actual Source/analysis graph")
    selected: dict[str, list[dict[str, Any]]] = {}
    residuals = []
    for identity, binding in selected_assets:
        remaining(deadline)
        if not isinstance(identity, str) or not identity or set(binding) != {"path", "sha256"}:
            raise ValueError("Code figure join lacks an exact actual Source occurrence/asset binding")
        path = PurePosixPath(binding["path"])
        if not path.is_relative_to(PurePosixPath(PROJECT + "/output/figures")):
            continue
        if path.name not in SELECTED or path != PurePosixPath(PROJECT + "/output/figures") / path.name:
            residuals.append("consumed-code-figure-domain-adapter:" + identity + ":" + binding["path"])
            continue
        selected.setdefault(path.name, []).append({"identity": identity, "asset": binding})
    result = []
    if selected:
        config = reader.read(PROJECT + "/manuscript/config.yaml", max_bytes=1024 * 1024)
        if config.content != source.reference.read(config.relative):
            raise ValueError("Code figure configured domain differs from admitted authored Source")
        csv = reader.read(PROJECT + "/output/data/optimization_results.csv", max_bytes=1024 * 1024)
        report = reader.read(PROJECT + "/output/reports/stability_analysis.json", max_bytes=1024 * 1024)
        expected = expected_figure_payloads(
            _scalar_config(config.content), csv.content, report.json_object(), deadline=deadline
        )
        capture_executions: dict[str, dict[str, Any] | None] = {}
        for name, occurrences in selected.items():
            remaining(deadline)
            png = reader.read(PROJECT + "/output/figures/" + name, max_bytes=32 * 1024 * 1024)
            companion = reader.read(
                PROJECT + "/output/data/native_figure_" + name[:-4] + ".json", max_bytes=8 * 1024 * 1024
            )
            observation = companion.json_object()
            validate_figure_payload(name, observation, expected[name], deadline=deadline)
            file, function = PRODUCERS[name]
            producer_path = SRC + "/figures/" + file
            actor = observation["producer"]
            if (
                actor["source"] != "src/template_code_project/figures/" + file
                or actor["function"] != function
                or actor["source_sha256"] != hashlib.sha256(source.reference.read(producer_path)).hexdigest()
            ):
                raise ValueError("Code observed Figure/Axes lost its actual selected Source generator")
            if observation["png"] != {
                "path": "output/figures/" + name,
                "sha256": png.sha256,
                "bytes": len(png.content),
            } or any(row["asset"] != {"path": png.relative, "sha256": png.sha256} for row in occurrences):
                raise ValueError("Code plotted payload/PNG differs from the complete selected native asset binding")
            stages = []
            for stage in analysis["ordered_stages"]:
                writes = stage["registered_returned_reads"]["completed_writes"]["records"]
                if any(row["path"] == "output/figures/" + name for row in writes):
                    stages.append(stage)
            if len(stages) != 1:
                residuals.append("consumed-code-figure-completed-origin:" + png.relative)
                continue
            stage = stages[0]
            key = stage["stage_key"]
            if key not in capture_executions:
                capture_executions[key] = _capture_execution(source, reader, stage, deadline=deadline)
            capture_execution = capture_executions[key]
            if capture_execution is None:
                residuals.append("consumed-code-figure-SDK-capture-execution:" + png.relative)
                continue
            events = stage["registered_returned_reads"]
            writes = events["completed_writes"]["records"]
            reads = events["records"]
            groups = [
                [row for row in writes if row["path"] == "output/figures/" + name],
                [row for row in reads if row["path"] == "output/figures/" + name],
                [row for row in writes if row["path"] == companion.relative[len(PROJECT) + 1 :]],
                [row for row in reads if row["path"] == companion.relative[len(PROJECT) + 1 :]],
                [row for row in writes if row["path"] == "output/data/optimization_results.csv"],
            ]
            if any(len(rows) != 1 for rows in groups):
                residuals.append("consumed-code-figure-write-read-chain:" + png.relative)
                continue
            written, returned, captured, captured_read, csv_write = [rows[0] for rows in groups]
            for event, snapshot, role in (
                (written, png, "producer"),
                (returned, png, "consumer"),
                (captured, companion, "producer"),
                (captured_read, companion, "consumer"),
            ):
                _actual_body(event, snapshot)
                _source_actor(event[role], source, producer_path, function)
            _actual_body(csv_write, csv)
            _source_actor(csv_write["producer"], source, SRC + "/analysis/experiments.py", "save_optimization_results")
            config_reads = [
                row
                for row in reads
                if row["path"] == "manuscript/config.yaml"
                and row["ordinal"] <= written["prior_registered_read_count"]
                and row["consumer"]["source"] == SRC + "/core/experiment_config.py"
                and row["consumer"]["function"] == "load_experiment_config"
            ]
            if not config_reads:
                residuals.append("consumed-code-figure-config-return:" + png.relative)
                continue
            for row in config_reads:
                _actual_body(row, config)
                _source_actor(row["consumer"], source, SRC + "/core/experiment_config.py", "load_experiment_config")
            if (
                returned["native_identity"] != written["native_identity"]
                or captured_read["native_identity"] != captured["native_identity"]
                or returned["origin"] != f"actual-completed-Source-write:{written['ordinal']}"
                or captured_read["origin"] != f"actual-completed-Source-write:{captured['ordinal']}"
                or written["ordinal"] >= captured["ordinal"]
                or not written["prior_registered_read_count"]
                < returned["ordinal"]
                <= captured["prior_registered_read_count"]
                or captured_read["ordinal"] <= captured["prior_registered_read_count"]
            ):
                raise ValueError("Code actual Figure/Axes/PNG lost its real completed write/read temporal identity")
            score_origin = None
            if name == "stability_analysis.png":
                report_writes = [
                    row
                    for row in writes
                    if row["path"] == "output/reports/stability_analysis.json" and row["ordinal"] < written["ordinal"]
                ]
                report_reads = [
                    row
                    for row in reads
                    if row["path"] == "output/reports/stability_analysis.json"
                    and row["ordinal"] <= written["prior_registered_read_count"]
                    and row["consumer"]["source"] == producer_path
                    and row["consumer"]["function"] == function
                ]
                if len(report_writes) != 1 or len(report_reads) != 1:
                    residuals.append("consumed-code-figure-SDK-score-origin:" + png.relative)
                    continue
                rw, rr = report_writes[0], report_reads[0]
                _actual_body(rw, report)
                _actual_body(rr, report)
                _source_actor(rw["producer"], source, SRC + "/analysis/scientific_reports.py", "run_stability_analysis")
                _source_actor(rr["consumer"], source, producer_path, function)
                if (
                    rr["native_identity"] != rw["native_identity"]
                    or rr["origin"] != f"actual-completed-Source-write:{rw['ordinal']}"
                    or rr["ordinal"] <= rw["prior_registered_read_count"]
                ):
                    raise ValueError("Code actual plotted SDK score lost its completed report-return identity")
                score_origin = _sdk_execution(
                    source, reader, {"native_stage_original": stage["native_stage_original"]}, deadline=deadline
                )
                if score_origin is None:
                    residuals.append("consumed-code-figure-SDK-score-execution:" + png.relative)
                    continue
            result.append(
                {
                    "png": _binding(png),
                    "observation": _binding(companion),
                    "selected_occurrences": occurrences,
                    "producer_stage": stage["stage_key"],
                    "producer_nonce": stage["analysis_nonce"],
                    "producer_process": stage["observed_process"],
                    "native_stage_original": stage["native_stage_original"],
                    "SDK_capture_execution": capture_execution,
                    "config": _binding(config),
                    "config_reads": config_reads,
                    "checked_csv": _binding(csv),
                    "csv_write": csv_write,
                    "PNG_write": written,
                    "PNG_return": returned,
                    "observation_write": captured,
                    "observation_return": captured_read,
                    "SDK_score_execution": score_origin,
                    "domain": "complete-selected-Source-plot-series-panels-labels-scales",
                }
            )
    if not reader.unchanged():
        raise ValueError("Code figure actual Source/output/event bodies changed during the direct join")
    remaining(deadline)
    body = {
        "scope": SCOPE,
        "source_binding": analysis["source_binding"],
        "pipeline_run_id": analysis["pipeline_run_id"],
        "analysis_digest": analysis["content_digest"],
        "figures": result,
        "residuals": residuals,
        "claim_boundary": (
            "selected-Source-plot-domain-and-write/asset-correspondence DATA; "
            "complete native/library/control admission stays enclosing"
        ),
    }
    return {**body, "content_digest": canonical_digest(body)}
