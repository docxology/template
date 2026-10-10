"""Real-file DATA comparisons never construct original process authority.

These fixtures exercise the fixed semantic predicate after authentication.
They deliberately provide no NativeSourceContext, NativeOriginalLaunch or live
producer. Root's actual stage/suite qualification remains separately required.
"""

from __future__ import annotations

import hashlib
import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.core.pipeline.native_analysis_current import replay_current_native_analysis
from infrastructure.reporting.native_analysis_boundary_replay import SCHEMA
from infrastructure.reporting.native_analysis_semantic_compare import (
    native_analysis_semantics,
    native_hydration_semantics,
    require_native_analysis_equivalence,
)
from infrastructure.reporting.native_hydration_reconstruction import SCHEMA as HYDRATION_SCHEMA
from infrastructure.reporting.native_projection_contracts import ProjectionSourceUnsupported
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SCOPE = "templates/template_code_project"
HASH = hashlib.sha256(b"whole-body").hexdigest()


def _seal(body: dict[str, Any]) -> dict[str, Any]:
    body.pop("content_digest", None)
    return {**body, "content_digest": canonical_digest(body)}


def _graph(root: Path, run_id: str, *, present: bool = True) -> dict[str, Any]:
    prefix = f"projects/{SCOPE}"
    retained = f"{prefix}/output/.pipeline/analysis-data/{run_id}/blobs/{HASH}"
    identity = [1, len(run_id), 10, 12, 13]
    file = {
        "path": "data/input.csv",
        "sha256": HASH,
        "bytes": 10,
        "native_identity": identity,
        "retained_path": retained,
        "retained": {"path": retained, "sha256": HASH, "bytes": 10},
    }
    frame = {"source": f"{prefix}/src/analysis.py", "source_sha256": HASH, "function": "calculate", "line": 7}
    code = {"path": frame["source"], "sha256": HASH, "bytes": 10}
    read = {**file, "ordinal": 1, "origin": "original-incoming-body", "consumer": frame, "consumer_source": code}
    write = {
        **file,
        "ordinal": 1,
        "path": "output/data/variables.json",
        "producer": frame,
        "producer_source": {"path": frame["source"], "sha256": HASH},
        "prior_observed": None,
        "prior_observation_authority": "prior-path-observation-only; not-compare-and-swap-history",
        "prior_registered_read_count": 1,
        "prior_registered_read_prefix_digest": canonical_digest([read]),
    }
    raw_boundary = {
        "root_policy": ["data"],
        "file_policy": [],
        "present_roots": ["data"] if present else [],
        "output_policy": "stable-shippable-output-v1",
        "claim_boundary": "boundary-only",
    }
    runtime = {
        "schema": "template-selected-python-runtime/1",
        "executable": str(root / "runtime/bin/python"),
        "resolved_executable": "/selected/python",
        "binary_sha256": HASH,
        "prefix": str(root / "runtime"),
        "python_minor": "3.13",
        "configuration_sha256": HASH,
        "site_roots": [str(root / "runtime/site-packages")],
        "installation_metadata": {"0/dependency.dist-info/RECORD": HASH},
        "dependency_scope": "metadata-record-declarations",
    }
    leaf_body = {
        "worker": {
            "request": {"runtime_binding": runtime, "data_before": raw_boundary},
            "completion": {
                "actual_runtime": {"python_version": "3.13.0", "implementation": "cpython"},
                "data_after": raw_boundary,
            },
        }
    }
    leaf = root / prefix / "output/.pipeline/semantic-fixture" / run_id / "leaf.json"
    leaf.parent.mkdir(parents=True)
    content = json.dumps(leaf_body, sort_keys=True).encode()
    leaf.write_bytes(content)
    stage = {
        "stage_key": "analysis:scripts/analysis.py",
        "leaf": {
            "path": leaf.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(content).hexdigest(),
            "bytes": len(content),
        },
        "request_digest": run_id,
        "analysis_nonce": run_id,
        "observed_process": {"pid": len(run_id)},
        "native_stage_original": {"actual_signed_os_exit": 0, "script_completion_intent": 0},
        "incoming": {"content_digest": run_id, "records": [file], "total_bytes": 10},
        "outgoing": {"content_digest": run_id, "records": [file], "total_bytes": 10},
        "registered_returned_reads": {
            "content_digest": run_id,
            "records": [read],
            "total_returned_bytes": 10,
            "coverage_boundary": "registered-reads-only",
            "completed_writes": {
                "content_digest": run_id,
                "records": [write],
                "total_written_bytes": 10,
                "coverage_boundary": "registered-writes-only",
            },
        },
        "script": {"path": f"{prefix}/scripts/analysis.py", "sha256": HASH, "bytes": 10},
    }
    return _seal(
        {
            "schema_version": SCHEMA,
            "scope": SCOPE,
            "pipeline_run_id": run_id,
            "plan_digest": run_id,
            "source_binding": ["source-commit", HASH],
            "aggregate": {"path": f"{run_id}/run.json", "sha256": run_id},
            "ordered_stages": [stage],
            "produced_current_bodies": [],
            "source_registry_reconstruction": None,
            "unresolved_edges": ["full-scientific-domain-still-required"],
        }
    )


def _semantics(graph: dict[str, Any], root: Path) -> dict[str, Any]:
    return native_analysis_semantics(graph, SnapshotReader(root), deadline=time.monotonic() + 30)


def test_fresh_physical_roots_and_retained_run_labels_compare_full_data(tmp_path: Path) -> None:
    original = tmp_path / "original"
    current = tmp_path / "current"
    before = _graph(original, "original-run")
    after = _graph(current, "new-current-run")
    require_native_analysis_equivalence(_semantics(before, original), _semantics(after, current))


@pytest.mark.parametrize(
    "change",
    [
        "body",
        "consumer",
        "read-order",
        "write-producer",
        "prior-read-prefix",
        "claim-boundary",
        "source",
        "registry",
        "unresolved",
    ],
)
def test_complete_semantic_mutations_cannot_compare_equal(tmp_path: Path, change: str) -> None:
    original = tmp_path / "original"
    current = tmp_path / "current"
    before, after = _graph(original, "original-run"), _graph(current, "current-run")
    stage = after["ordered_stages"][0]
    events = stage["registered_returned_reads"]
    if change == "body":
        stage["outgoing"]["records"][0]["sha256"] = "f" * 64
    elif change == "consumer":
        events["records"][0]["consumer"]["line"] += 1
    elif change == "read-order":
        events["records"].append(deepcopy(events["records"][0]))
        events["records"][1]["ordinal"] = 2
        events["total_returned_bytes"] += 10
    elif change == "write-producer":
        events["completed_writes"]["records"][0]["producer"]["function"] = "other_calculation"
    elif change == "prior-read-prefix":
        events["completed_writes"]["records"][0]["prior_registered_read_count"] = 0
    elif change == "claim-boundary":
        events["coverage_boundary"] = "all-reads"
    elif change == "source":
        after["source_binding"][1] = "f" * 64
    elif change == "registry":
        after["source_registry_reconstruction"] = {"complete_declared_records": {"extra": "figure"}}
    else:
        after["unresolved_edges"] = []
    with pytest.raises(ValueError, match="complete authenticated Original semantics"):
        require_native_analysis_equivalence(_semantics(before, original), _semantics(_seal(after), current))


def test_empty_declared_root_presence_remains_semantic(tmp_path: Path) -> None:
    before = _graph(tmp_path / "original", "original", present=True)
    after = _graph(tmp_path / "current", "current", present=False)
    with pytest.raises(ValueError, match="complete authenticated Original semantics"):
        require_native_analysis_equivalence(
            _semantics(before, tmp_path / "original"), _semantics(after, tmp_path / "current")
        )


@pytest.mark.parametrize("field", ["actual_signed_os_exit", "script_completion_intent"])
def test_os_failure_and_script_intent_remain_distinct_refusals(tmp_path: Path, field: str) -> None:
    graph = _graph(tmp_path, "run")
    graph["ordered_stages"][0]["native_stage_original"][field] = 17
    with pytest.raises(ValueError, match="incomplete original/current execution"):
        _semantics(_seal(graph), tmp_path)


def test_retained_leaf_body_mutation_is_refused(tmp_path: Path) -> None:
    graph = _graph(tmp_path, "run")
    (tmp_path / graph["ordered_stages"][0]["leaf"]["path"]).write_bytes(b"{}")
    with pytest.raises(ValueError, match="leaf changed"):
        _semantics(graph, tmp_path)


def test_future_semantic_field_cannot_silently_disappear(tmp_path: Path) -> None:
    graph = _graph(tmp_path, "run")
    graph["ordered_stages"][0]["incoming"]["records"][0]["new_semantic_field"] = "retained"
    with pytest.raises(ValueError, match="semantic fields differ"):
        _semantics(_seal(graph), tmp_path)


def _hydration(run_id: str) -> dict[str, Any]:
    return _seal(
        {
            "schema_version": HYDRATION_SCHEMA,
            "scope": SCOPE,
            "pipeline_run_id": run_id,
            "plan_digest": run_id,
            "source_binding": ["source-commit", HASH],
            "variables": {"path": "variables.json", "sha256": HASH},
            "config": {"path": "config.yaml", "sha256": HASH},
            "ordered_inputs": [
                {"ordinal": 1, "consumed": {"path": "body.md", "sha256": HASH}, "hydration": {"tokens": ["MEAN"]}}
            ],
            "composition": {"path": "composition.json", "sha256": HASH},
            "algorithm": "web-renderer-combine-v1",
            "combined": {"path": "combined.md", "sha256": HASH},
            "dotted_variables": None,
            "independent_combined_sha256": HASH,
            "pdf_recomposition": {"sha256": HASH, "bytes": 10},
            "unresolved_edges": ["all-native-consumption-still-required"],
        }
    )


def test_hydration_compares_every_source_occurrence_and_combined_body() -> None:
    before, after = _hydration("original"), _hydration("current")
    require_native_analysis_equivalence(native_hydration_semantics(before), native_hydration_semantics(after))
    after["ordered_inputs"][0]["hydration"]["tokens"].append("EXTRA")
    with pytest.raises(ValueError, match="complete authenticated Original semantics"):
        require_native_analysis_equivalence(
            native_hydration_semantics(before), native_hydration_semantics(_seal(after))
        )


def test_hydration_retains_unknown_field_and_digest_refusals() -> None:
    graph = _hydration("run")
    graph["variables"]["sha256"] = "f" * 64
    with pytest.raises(ValueError, match="paired schema/digest"):
        native_hydration_semantics(graph)
    graph = _seal({**graph, "new_semantic_field": 1})
    with pytest.raises(ValueError, match="semantic fields differ"):
        native_hydration_semantics(graph)


def test_current_controller_cannot_launch_from_serialized_original_or_source(tmp_path: Path) -> None:
    reader = SnapshotReader(tmp_path, native_operation={"status": "pass"})
    with pytest.raises(ProjectionSourceUnsupported, match="externally admitted source and original launch custody"):
        replay_current_native_analysis(
            SCOPE,
            {"status": "pass"},  # type: ignore[arg-type]
            reader,
            {"status": "pass"},  # type: ignore[arg-type]
            directory=tmp_path / "output/readiness/current",
            original_domain={"status": "pass"},
            provider_wheels={},
        )
    assert list(tmp_path.iterdir()) == []
