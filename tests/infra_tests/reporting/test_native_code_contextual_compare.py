"""Fixed projection DATA controls, retaining raw evidence and unknown bodies."""

from __future__ import annotations

import copy
import hashlib
import time

import pytest

from infrastructure.rendering.manuscript_hydration_replay import reconstruct_shared_hydration, require_shared_hydration
from infrastructure.reporting.native_code_contextual_compare import _remap
from infrastructure.reporting.native_code_metadata_domains import PROJECT


def test_exact_proven_body_triples_are_projected_without_mutating_raw_data() -> None:
    path = "output/data/manuscript_variables.json"
    raw = {
        "records": [{"path": path, "sha256": "a" * 64, "bytes": 20, "ordinal": 1}],
        "total_returned_bytes": 20,
        "content_digest": "raw-original-digest",
    }
    held = copy.deepcopy(raw)
    replacements = {
        (PROJECT + "/" + path, "a" * 64, 20): {"path": PROJECT + "/" + path, "sha256": "b" * 64, "bytes": 30}
    }
    projected = _remap(raw, replacements, deadline=time.monotonic() + 10)
    assert projected["records"][0] == {**raw["records"][0], "sha256": "b" * 64, "bytes": 30}
    assert projected["total_returned_bytes"] == 30
    assert raw == held and projected["content_digest"] == "raw-original-digest"


@pytest.mark.parametrize("mutation", ["other-path", "other-sha", "other-size"])
def test_unproven_or_scientific_body_differences_are_never_normalized(mutation: str) -> None:
    record = {"path": "output/data/manuscript_variables.json", "sha256": "a" * 64, "bytes": 20}
    replacements = {(PROJECT + "/" + record["path"], record["sha256"], 20): {"sha256": "b" * 64, "bytes": 30}}
    if mutation == "other-path":
        record["path"] = "output/data/optimization_results.csv"
    elif mutation == "other-sha":
        record["sha256"] = "c" * 64
    else:
        record["bytes"] = 21
    assert _remap(record, replacements, deadline=time.monotonic() + 10) == record


def test_prior_body_and_temporal_fields_keep_their_exact_unproven_meaning() -> None:
    record = {
        "path": "output/data/manuscript_variables.json",
        "sha256": "a" * 64,
        "bytes": 20,
        "ordinal": 2,
        "prior_registered_read_count": 5,
        "prior_observed": {"sha256": "c" * 64, "bytes": 10},
        "producer": {"source": "actual Source DATA", "function": "save_variables", "line": 1},
    }
    replacements = {(PROJECT + "/" + record["path"], record["sha256"], 20): {"sha256": "b" * 64, "bytes": 30}}
    projected = _remap(record, replacements, deadline=time.monotonic() + 10)
    assert projected["prior_observed"] == record["prior_observed"]
    assert all(projected[key] == record[key] for key in ("ordinal", "prior_registered_read_count", "producer"))


@pytest.mark.parametrize("context", ["short", "different runtime label"])
def test_complete_source_reconstruction_canonicalizes_context_and_all_later_offsets(context: str) -> None:
    source = b"{{PLATFORM}} then science {{RESULT_MIN_ITERATIONS}} and again {{PLATFORM}}"
    variables = {"PLATFORM": context, "RESULT_MIN_ITERATIONS": "7"}
    actual = reconstruct_shared_hydration(source, variables)
    assert require_shared_hydration(source, variables, actual.output).data() == actual.data()
    canonical = reconstruct_shared_hydration(source, {**variables, "PLATFORM": "{{PLATFORM}}"})
    assert canonical.output == b"{{PLATFORM}} then science 7 and again {{PLATFORM}}"
    assert [(row.ordinal, row.key, row.source_start_byte, row.source_end_byte) for row in actual.occurrences] == [
        (row.ordinal, row.key, row.source_start_byte, row.source_end_byte) for row in canonical.occurrences
    ]
    assert hashlib.sha256(actual.output).hexdigest() != hashlib.sha256(canonical.output).hexdigest()


def test_complete_source_reconstruction_retains_scientific_payload_drift() -> None:
    source = b"{{PLATFORM}} science {{RESULT_MIN_ITERATIONS}}"
    first = reconstruct_shared_hydration(source, {"PLATFORM": "{{PLATFORM}}", "RESULT_MIN_ITERATIONS": "7"})
    second = reconstruct_shared_hydration(source, {"PLATFORM": "{{PLATFORM}}", "RESULT_MIN_ITERATIONS": "8"})
    assert first.output != second.output and first.data() != second.data()
