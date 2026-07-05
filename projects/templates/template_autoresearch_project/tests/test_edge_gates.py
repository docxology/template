"""Edge-case tests for substance gates, benchmark grading, and security render."""

from __future__ import annotations

import json
from pathlib import Path

from src.artifact_content import _json_is_substantive, _value_is_substantive
from src.research_object import research_object_manifest_payload
from src.security.render import render_security_review_markdown
from src.writers.benchmark import _benchmark_score, _has_supported_claim
from src.writers.io import relative_path

def test_research_object_manifest_excludes_out_of_tree_paths(tmp_path: Path) -> None:

    """Paths outside project_root are silently excluded from the manifest."""

    project = tmp_path / "project"

    project.mkdir()

    (project / "output" / "data").mkdir(parents=True)

    inside = project / "output" / "data" / "inside.json"

    inside.write_text('{"ok": true}', encoding="utf-8")

    outside = tmp_path / "outside.json"

    outside.write_text('{"ok": true}', encoding="utf-8")

    payload = research_object_manifest_payload(project, [inside, outside], generated_at="t")

    artifact_paths = [a["path"] for a in payload["artifacts"]]

    assert any("inside.json" in p for p in artifact_paths)

    assert not any("outside.json" in p for p in artifact_paths)

def test_research_object_manifest_excludes_nonexistent_paths(tmp_path: Path) -> None:

    """Paths that do not exist are silently excluded."""

    project = tmp_path / "project"

    project.mkdir()

    nonexistent = project / "output" / "data" / "ghost.json"

    payload = research_object_manifest_payload(project, [nonexistent], generated_at="t")

    assert payload["artifact_count"] == 0

    assert payload["artifacts"] == []

# ---------------------------------------------------------------------------

# security/render.py — non-list non_claims

# ---------------------------------------------------------------------------

def test_render_security_review_markdown_handles_non_list_non_claims() -> None:

    """When non_claims is not a list the renderer should not crash and should skip items."""

    profile = {

        "mode": "test",

        "network_policy": "offline",

        "integrity_algorithm": "sha256",

        "external_signing": False,

        "claim_scope": "local only",

        "non_claims": "not_a_list",  # intentionally wrong type

    }

    threat_model = {"summary": {"asset_count": 0, "threat_count": 0, "control_count": 0}}

    inventory = {"inputs": [], "generated_artifacts": []}

    attestation = {"status": "passed", "checked_count": 0, "missing_count": 0, "mismatch_count": 0}

    markdown = render_security_review_markdown(profile, threat_model, inventory, attestation)

    assert "# AutoResearch Security Review" in markdown

    # No crash; non_claims treated as empty

    assert "## Non-Claims" in markdown

# ---------------------------------------------------------------------------

# writers/io.py — relative_path when path is outside project root

# ---------------------------------------------------------------------------

def test_relative_path_returns_absolute_string_when_outside_root(tmp_path: Path) -> None:

    """relative_path falls back to str(path) when path is outside project_root."""

    project_root = tmp_path / "project"

    project_root.mkdir()

    outside = tmp_path / "external" / "file.json"

    outside.parent.mkdir()

    outside.write_text("{}", encoding="utf-8")

    result = relative_path(project_root, outside)

    # Not relative to project_root → falls back to absolute string

    assert "external" in result

# ---------------------------------------------------------------------------

# writers/benchmark.py — _benchmark_score and _has_supported_claim edge cases

# ---------------------------------------------------------------------------

def test_benchmark_score_returns_none_for_missing_file(tmp_path: Path) -> None:

    path = tmp_path / "nonexistent.json"

    assert _benchmark_score(path) is None

def test_benchmark_score_returns_none_for_invalid_json(tmp_path: Path) -> None:

    path = tmp_path / "bad.json"

    path.write_text("not json", encoding="utf-8")

    assert _benchmark_score(path) is None

def test_benchmark_score_returns_none_for_non_dict_json(tmp_path: Path) -> None:

    path = tmp_path / "list.json"

    path.write_text("[1, 2, 3]", encoding="utf-8")

    assert _benchmark_score(path) is None

def test_benchmark_score_returns_none_for_non_numeric_score(tmp_path: Path) -> None:

    path = tmp_path / "no_score.json"

    path.write_text('{"score": "high"}', encoding="utf-8")

    assert _benchmark_score(path) is None

def test_has_supported_claim_returns_false_for_missing_claims(tmp_path: Path) -> None:

    assert _has_supported_claim(tmp_path) is False

def test_has_supported_claim_returns_false_for_hollow_claims_file(tmp_path: Path) -> None:

    (tmp_path / "output" / "data").mkdir(parents=True)

    (tmp_path / "output" / "data" / "autoresearch_claims.json").write_text("{}", encoding="utf-8")

    assert _has_supported_claim(tmp_path) is False

def test_has_supported_claim_returns_false_when_evidence_file_hollow(tmp_path: Path) -> None:

    """supported=true claim whose evidence_path points to an empty file → False."""

    (tmp_path / "output" / "data").mkdir(parents=True)

    evidence = tmp_path / "output" / "data" / "evidence.json"

    evidence.write_text("", encoding="utf-8")  # hollow

    claims = [{"identifier": "c1", "supported": True, "evidence_path": "output/data/evidence.json"}]

    (tmp_path / "output" / "data" / "autoresearch_claims.json").write_text(

        json.dumps(claims), encoding="utf-8"

    )

    assert _has_supported_claim(tmp_path) is False

def test_has_supported_claim_returns_true_for_substantive_evidence(tmp_path: Path) -> None:

    """supported=true claim whose evidence_path points to real content → True."""

    (tmp_path / "output" / "data").mkdir(parents=True)

    evidence = tmp_path / "output" / "data" / "evidence.json"

    evidence.write_text('{"result": "real"}', encoding="utf-8")

    claims = [{"identifier": "c1", "supported": True, "evidence_path": "output/data/evidence.json"}]

    (tmp_path / "output" / "data" / "autoresearch_claims.json").write_text(

        json.dumps(claims), encoding="utf-8"

    )

    assert _has_supported_claim(tmp_path) is True

def test_has_supported_claim_returns_false_when_all_claims_unsupported(tmp_path: Path) -> None:

    (tmp_path / "output" / "data").mkdir(parents=True)

    claims = [{"identifier": "c1", "supported": False, "evidence_path": "output/data/evidence.json"}]

    (tmp_path / "output" / "data" / "autoresearch_claims.json").write_text(

        json.dumps(claims), encoding="utf-8"

    )

    assert _has_supported_claim(tmp_path) is False

# ---------------------------------------------------------------------------

# artifact_content.py — deeper edge cases

# ---------------------------------------------------------------------------

def test_json_is_substantive_bare_string_true() -> None:

    """A bare top-level JSON string with content is substantive."""

    assert _json_is_substantive("hello") is True

def test_json_is_substantive_bare_string_whitespace_only() -> None:

    """A bare top-level JSON string of whitespace is NOT substantive."""

    assert _json_is_substantive("   ") is False

def test_json_is_substantive_bare_number_false() -> None:

    """A bare top-level number (not in container) is NOT substantive."""

    assert _json_is_substantive(42) is False

def test_json_is_substantive_bare_null_false() -> None:

    assert _json_is_substantive(None) is False

def test_value_is_substantive_nan_float_false() -> None:

    import math

    assert _value_is_substantive(float("nan")) is False

def test_value_is_substantive_inf_float_false() -> None:

    import math

    assert _value_is_substantive(float("inf")) is False

def test_value_is_substantive_list_of_nones_false() -> None:

    """A list containing only None values is not substantive."""

    assert _value_is_substantive([None, None]) is False

def test_value_is_substantive_nested_all_null_dict_false() -> None:

    """Deeply nested all-null dict is not substantive."""

    assert _value_is_substantive({"a": {"b": None}}) is False

def test_value_is_substantive_nested_with_real_value_true() -> None:

    """Nested dict with at least one real value IS substantive."""

    assert _value_is_substantive({"a": {"b": 42}}) is True

def test_value_is_substantive_bool_true() -> None:

    """A boolean value (even False) is substantive — it carries intent."""

    assert _value_is_substantive(False) is True

    assert _value_is_substantive(True) is True
