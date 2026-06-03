"""Claim ledger gate negative controls."""

from __future__ import annotations

import json
from pathlib import Path

from gates.validation import validate_manuscript
from gate_support import refresh_generated_gate_artifacts


def test_validate_manuscript_claim_ledger_missing_file_negative(project_root: Path, tmp_path: Path) -> None:
    ledger = project_root / "data" / "claim_ledger.yaml"
    backup = tmp_path / "claim_ledger.yaml.bak"
    backup.write_text(ledger.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        ledger.unlink()
        checks = validate_manuscript(project_root)
        assert checks["claim_ledger_valid"] is False
    finally:
        ledger.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
        refresh_generated_gate_artifacts(project_root)


def test_validate_manuscript_claim_ledger_negative(project_root: Path) -> None:
    target = project_root / "output" / "figures" / "sheaf_layers_overview.png"
    backup_exists = target.is_file()
    backup_bytes = target.read_bytes() if backup_exists else b""
    try:
        if backup_exists:
            target.unlink()
        checks = validate_manuscript(project_root)
        assert checks["claim_ledger_valid"] is False
    finally:
        if backup_exists:
            target.write_bytes(backup_bytes)
        refresh_generated_gate_artifacts(project_root)


def test_typed_claim_evidence_exercises_success_predicates(tmp_path: Path) -> None:
    from gates.claim_ledger import typed_claim_evidence_issues

    data_dir = tmp_path / "output" / "data"
    data_dir.mkdir(parents=True)
    payload = data_dir / "predicate_payload.json"
    payload.write_text(
        json.dumps(
            {
                "exists_value": "present",
                "truthy_value": 1,
                "zero_value": 0,
                "positive_value": 2,
                "flags": [True, True],
                "flag_map": {"a": True, "b": True},
                "rows": [{"ok": False}, {"ok": True}],
                "score": 1.01,
                "text": "needle in haystack",
                "items": ["a", "b", "c"],
            }
        ),
        encoding="utf-8",
    )
    yaml_payload = data_dir / "predicate_payload.yaml"
    yaml_payload.write_text("values:\n  - alpha\n  - beta\n", encoding="utf-8")
    text_payload = data_dir / "predicate_payload.txt"
    text_payload.write_text("plain evidence text", encoding="utf-8")
    ledger = tmp_path / "claim_ledger.yaml"
    ledger.write_text(
        "\n".join(
            [
                "claims:",
                "  - id: file_exists",
                "    statement: file exists",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      predicate: file_exists",
                "  - id: exists_predicate",
                "    statement: value exists",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: exists_value",
                "      predicate: exists",
                "  - id: truthy_predicate",
                "    statement: value truthy",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: truthy_value",
                "      predicate: truthy",
                "  - id: zero_predicate",
                "    statement: value zero",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: zero_value",
                "      predicate: zero",
                "  - id: positive_predicate",
                "    statement: value positive",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: positive_value",
                "      predicate: positive",
                "  - id: all_true_list",
                "    statement: all flags true",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: flags",
                "      predicate: all_true",
                "  - id: all_true_map",
                "    statement: all map flags true",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: flag_map",
                "      predicate: all_true",
                "  - id: any_ok",
                "    statement: at least one row ok",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: rows",
                "      any:",
                "        field: ok",
                "        equals: true",
                "  - id: numeric_bounds",
                "    statement: score bounded",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: score",
                "      min: 1",
                "      max: 2",
                "  - id: text_contains",
                "    statement: text contains needle",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: text",
                "      contains: needle",
                "  - id: list_len_min",
                "    statement: list has enough items",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: items",
                "      len_min: 3",
                "  - id: yaml_load",
                "    statement: yaml can be inspected",
                "    path: output/data/predicate_payload.yaml",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: values",
                "      set_equals: [beta, alpha]",
                "  - id: text_load",
                "    statement: text can be inspected",
                "    path: output/data/predicate_payload.txt",
                "    tracks: [sheaf]",
                "    evidence:",
                "      contains: plain",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert typed_claim_evidence_issues(tmp_path, ledger_path=ledger) == []


def test_typed_claim_evidence_reports_structured_failures(tmp_path: Path) -> None:
    from gates.claim_ledger import typed_claim_evidence_issues

    data_dir = tmp_path / "output" / "data"
    data_dir.mkdir(parents=True)
    payload = data_dir / "predicate_payload.json"
    payload.write_text(json.dumps({"items": ["a"], "rows": [{"ok": False}], "value": 1}), encoding="utf-8")
    invalid = data_dir / "invalid.json"
    invalid.write_text("{", encoding="utf-8")
    ledger = tmp_path / "claim_ledger.yaml"
    ledger.write_text(
        "\n".join(
            [
                "claims:",
                "  - id: missing_path",
                "    statement: no path",
                "    tracks: [sheaf]",
                "  - id: missing_artifact",
                "    statement: missing artifact",
                "    path: output/data/missing.json",
                "    tracks: [sheaf]",
                "  - id: unreadable_json",
                "    statement: invalid json",
                "    path: output/data/invalid.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: value",
                "      equals: 1",
                "  - id: field_missing",
                "    statement: field missing",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: absent",
                "      equals: 1",
                "  - id: set_wrong_type",
                "    statement: set_equals needs a list",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: value",
                "      set_equals: [1]",
                "  - id: len_min_fails",
                "    statement: len_min fails",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: items",
                "      len_min: 2",
                "  - id: all_wrong_shape",
                "    statement: all requires list",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: value",
                "      all:",
                "        equals: 1",
                "  - id: any_fails",
                "    statement: any nested predicate fails",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: rows",
                "      any:",
                "        field: ok",
                "        equals: true",
                "  - id: tracks_empty",
                "    statement: tracks empty",
                "    path: output/data/predicate_payload.json",
                "    tracks: []",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    issues = typed_claim_evidence_issues(tmp_path, ledger_path=ledger)

    assert len(issues) == 9
    assert any("missing path" in issue for issue in issues)
    assert any("cannot load evidence" in issue for issue in issues)
    assert any("tracks must not be empty" in issue for issue in issues)
