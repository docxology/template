"""Actual source witnesses and EPUB bytes retain interface failures and blockers."""

from __future__ import annotations

import copy
import json
from typing import Any

import pytest

from infrastructure.reporting.native_epub_observer import epub_control_bytes
from infrastructure.reporting.native_epub_source_spine import (
    inspect_source_reference_epub_spine,
    replay_source_reference_epub_spine,
)
from infrastructure.reporting.native_format_acceptance_contracts import unsupported_native_controls
from infrastructure.reporting.native_format_observer_outcome import native_observer_outcome
from infrastructure.reporting.native_office_content_witness import inspect_office_source_survival
from infrastructure.reporting.native_office_full_observer import SCHEMA, office_full_outcome


def _inlines(text: str) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for ordinal, word in enumerate(text.split()):
        if ordinal:
            nodes.append({"t": "Space"})
        nodes.append({"t": "Str", "c": word})
    return nodes


def _source_ast() -> bytes:
    blocks = []
    for title, paragraph in (
        ("First measurement", "Measured offset -3.25 mV."),
        ("Independent repetition", "Repeated offset -3.25 mV."),
    ):
        blocks.append({"t": "Header", "c": [1, ["", [], []], _inlines(title)]})
        blocks.append({"t": "Para", "c": _inlines(paragraph)})
    return json.dumps({"pandoc-api-version": [1, 23, 1], "meta": {}, "blocks": blocks}).encode()


def _reference_survival(reference: bytes, *, residual: str | None = None) -> dict[str, Any]:
    source = _source_ast()
    native = source
    if residual == "blocker":
        document = json.loads(source)
        document["blocks"].append({"t": "RawBlock", "c": ["html", "<aside>Unclassified source role.</aside>"]})
        source = json.dumps(document).encode()
    elif residual == "finding":
        document = json.loads(native)
        document["blocks"] = document["blocks"][:-1]
        native = json.dumps(document).encode()
    return inspect_office_source_survival(source, source, native, reference, "epub", (), {})


def _complete_observer(
    kind: str,
    survival: dict[str, Any],
    *,
    spine: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = office_full_outcome(
        {"blockers": []},
        survival,
        {"findings": [], "blockers": []},
        {"findings": [], "blockers": []},
        {"findings": [], "blockers": []},
    )
    complete = {"schema_version": SCHEMA, "observation": result, "spine": spine}
    observer = {"format": kind, "office_complete_source": complete, "observation": result}
    if kind == "epub":
        observer["spine"] = spine
    return observer


@pytest.mark.parametrize("kind", ("docx", "epub"))
def test_complete_source_status_is_adapted_without_granting_full_acceptance(kind: str) -> None:
    reference, _ = epub_control_bytes("baseline")
    survival = _reference_survival(reference)
    assert survival["status"] == "observed", survival
    spine = inspect_source_reference_epub_spine(reference, reference, survival) if kind == "epub" else None
    observer = _complete_observer(kind, survival, spine=spine)
    assert observer["observation"]["status"] == "observed"
    assert native_observer_outcome(observer) == {"status": "pass", "findings": [], "blockers": []}
    assert observer["observation"]["status"] == "observed"
    assert unsupported_native_controls("templates/template_code_project", (kind,))


@pytest.mark.parametrize("residual,expected", (("finding", "fail"), ("blocker", "blocked")))
def test_complete_source_failure_and_unknown_role_survive_status_adaptation(residual: str, expected: str) -> None:
    reference, _ = epub_control_bytes("baseline")
    survival = _reference_survival(reference, residual=residual)
    observer = _complete_observer("docx", survival)
    outcome = native_observer_outcome(observer)
    assert outcome["status"] == expected
    assert outcome["findings"] == survival["findings"]
    assert outcome["blockers"] == survival["blockers"]
    assert survival["findings"] or survival["blockers"]


def test_complete_source_forged_status_and_observation_alias_are_rejected() -> None:
    reference, _ = epub_control_bytes("baseline")
    survival = _reference_survival(reference, residual="finding")
    observer = _complete_observer("docx", survival)
    observer["observation"]["status"] = "observed"
    with pytest.raises(ValueError, match="conceals findings"):
        native_observer_outcome(observer)
    observer = _complete_observer("docx", survival)
    observer["observation"] = {"status": "observed", "findings": [], "blockers": []}
    with pytest.raises(ValueError, match="source-owned observation schema"):
        native_observer_outcome(observer)
    observer = _complete_observer("docx", survival)
    observer["office_complete_source"]["schema_version"] = "template-native-office-complete-source-observer-v2"
    with pytest.raises(ValueError, match="source-owned observation schema"):
        native_observer_outcome(observer)


@pytest.mark.parametrize("name", ("baseline", "changed-number", "reordered-spine", "omitted-text"))
def test_source_reference_spine_uses_actual_ordered_epub_bytes(name: str) -> None:
    reference, _ = epub_control_bytes("baseline")
    candidate, _ = epub_control_bytes(name)
    survival = _reference_survival(reference)
    assert survival["status"] == "observed", survival
    observed = inspect_source_reference_epub_spine(reference, candidate, survival)
    assert len(observed["candidate"]["spine"]) == 2
    assert len(observed["chapter_contracts"]) == 2
    if name == "baseline":
        assert observed["status"] == "pass"
        assert observed["findings"] == observed["blockers"] == []
    else:
        assert observed["status"] == "fail"
        assert {row["code"] for row in observed["findings"]} == {"epub.spine.content"}
    assert replay_source_reference_epub_spine(reference, candidate, survival, observed) == observed
    changed = copy.deepcopy(observed)
    changed["candidate"]["spine"].reverse()
    with pytest.raises(ValueError, match="spine replay differs"):
        replay_source_reference_epub_spine(reference, candidate, survival, changed)


def test_epub_missing_or_changed_spine_cannot_be_hidden_by_complete_office_layout() -> None:
    reference, _ = epub_control_bytes("baseline")
    candidate, _ = epub_control_bytes("reordered-spine")
    survival = _reference_survival(reference)
    spine = inspect_source_reference_epub_spine(reference, candidate, survival)
    observer = _complete_observer("epub", survival, spine=spine)
    assert observer["observation"]["status"] == "observed"
    assert native_observer_outcome(observer)["status"] == "fail"
    del observer["spine"]
    with pytest.raises(ValueError, match="omits or changes its original spine"):
        native_observer_outcome(observer)
    observer["spine"] = {"status": "pass", "findings": [], "blockers": []}
    with pytest.raises(ValueError, match="omits or changes its original spine"):
        native_observer_outcome(observer)


@pytest.mark.parametrize("residual,expected", (("finding", "fail"), ("blocker", "blocked")))
def test_reference_source_residuals_cannot_be_cleared_by_equal_packages(residual: str, expected: str) -> None:
    reference, _ = epub_control_bytes("baseline")
    survival = _reference_survival(reference, residual=residual)
    observed = inspect_source_reference_epub_spine(reference, reference, survival)
    assert observed["reference"]["status"] == "pass"
    assert observed["candidate"]["status"] == "pass"
    assert observed["status"] == expected
    assert survival["findings"] or survival["blockers"]
    wrong = {**survival, "package_sha256": "0" * 64}
    with pytest.raises(ValueError, match="exact independent source-survival witness"):
        inspect_source_reference_epub_spine(reference, reference, wrong)
    missing_source = {key: value for key, value in survival.items() if key != "source_ast_sha256"}
    with pytest.raises(ValueError, match="exact independent source-survival witness"):
        inspect_source_reference_epub_spine(reference, reference, missing_source)
