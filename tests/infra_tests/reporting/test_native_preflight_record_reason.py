"""The retained preflight record names why the run refused, or says nothing."""

from __future__ import annotations

import json
import time

import pytest

from infrastructure.reporting.native_installed_preflight import (
    PREFLIGHT_SCOPE,
    diagnostic_record,
    refusal_reason,
)

_REASON = "native Source reference lacks strict published rendered evidence"


def _result(**summary_overrides: object) -> dict[str, object]:
    """The shape the preflight actually holds after a refused exemplar.

    Modelled on run 41681646093, where the reason reached this process in
    ``native_formats.results`` and was dropped at the record write.
    """
    summary: dict[str, object] = {
        "complete_selection": False,
        "observed_projects": 1,
        "run_id": "run",
        "selected_projects": [PREFLIGHT_SCOPE],
        "source_current": False,
        "source_digest": "digest",
        "results": [
            {
                "project": PREFLIGHT_SCOPE,
                "status": "fail",
                "diagnostic": _REASON,
                "execution_exit_code": 1,
                "blockers": [],
                "conformance_validated": False,
            }
        ],
    }
    summary.update(summary_overrides)
    return {"exit_code": 1, "native_formats": summary}


def _record(result: dict[str, object]) -> dict[str, object]:
    return diagnostic_record(
        result,
        code=1,
        provider_scopes=[PREFLIGHT_SCOPE],
        operation_started=time.monotonic() - 5,
        environment_nomination="commit",
    )


def test_record_names_the_reason_the_result_already_held() -> None:
    """The reason is present in this process; the record must carry it."""
    record = _record(_result())
    assert record["refused_because"] == f"{PREFLIGHT_SCOPE}: {_REASON}"
    assert record["exit_code"] == 1


def test_record_preserves_every_preexisting_field() -> None:
    """Readers must not have to migrate: the old fields are unchanged."""
    record = _record(_result())
    assert set(record) == {
        "schema_version",
        "reference_commit_nomination",
        "provider_scopes",
        "preparation_profile",
        "representative_scope",
        "exit_code",
        "complete_release_acceptance",
        "publication_authorized",
        "elapsed_seconds",
        "refused_because",
    }
    assert record["schema_version"] == "template-native-diagnostic-preflight-v2"
    assert record["representative_scope"] == PREFLIGHT_SCOPE
    assert record["complete_release_acceptance"] is False
    assert record["publication_authorized"] is False
    assert record["reference_commit_nomination"] == "commit"
    assert record["provider_scopes"] == [PREFLIGHT_SCOPE]


@pytest.mark.parametrize(
    "result",
    [
        pytest.param({"exit_code": 1}, id="no-native-formats"),
        pytest.param({"exit_code": 1, "native_formats": None}, id="null-native-formats"),
        pytest.param({"exit_code": 1, "native_formats": {}}, id="no-results"),
        pytest.param({"exit_code": 1, "native_formats": {"results": []}}, id="empty-results"),
        pytest.param({"exit_code": 1, "native_formats": {"results": "text"}}, id="results-not-a-list"),
        pytest.param({"exit_code": 1, "native_formats": {"results": [None, 3, "x"]}}, id="results-not-mappings"),
        pytest.param(
            {"exit_code": 1, "native_formats": {"results": [{"project": PREFLIGHT_SCOPE}]}}, id="no-diagnostic-key"
        ),
        pytest.param(
            {"exit_code": 1, "native_formats": {"results": [{"project": PREFLIGHT_SCOPE, "diagnostic": ""}]}},
            id="blank-diagnostic",
        ),
        pytest.param(
            {"exit_code": 1, "native_formats": {"results": [{"project": PREFLIGHT_SCOPE, "diagnostic": None}]}},
            id="null-diagnostic",
        ),
    ],
)
def test_absent_or_unexpected_shape_writes_no_reason_instead_of_guessing(result: dict[str, object]) -> None:
    """A missing reason is honest; an invented one is worse than the gap."""
    assert refusal_reason(result) is None
    record = _record(result)
    assert "refused_because" not in record
    # The record is still complete and writable, never absent or partial.
    assert record["exit_code"] == 1
    assert json.dumps(record)


def test_every_refused_project_is_named_not_only_the_first() -> None:
    """A multi-project refusal must not silently hide the later reasons."""
    result = {
        "exit_code": 1,
        "native_formats": {
            "results": [
                {"project": "a", "diagnostic": "first reason"},
                {"project": "b", "diagnostic": ""},
                {"project": "c", "diagnostic": "third reason"},
            ]
        },
    }
    assert refusal_reason(result) == "a: first reason; c: third reason"


def test_reason_without_a_project_name_is_still_reported() -> None:
    result = {"exit_code": 1, "native_formats": {"results": [{"diagnostic": "bare reason"}]}}
    assert refusal_reason(result) == "bare reason"
