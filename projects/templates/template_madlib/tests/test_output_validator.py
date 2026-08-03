from __future__ import annotations

import json
from pathlib import Path

from src.config import SECTION_KEYS, load_madlib_config
from src.output_validator import (
    DECLARED_FIGURE_FILES,
    OutputValidationResult,
    validate_generated_outputs,
    write_validation_report,
)
from .helpers import base_payload, write_config

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _codes(result: OutputValidationResult) -> set[str]:
    """Return the set of issue codes for assertion-friendly checks."""
    return {issue.code for issue in result.issues}


def _write_minimal_outputs(root: Path) -> None:
    """Write a coherent minimal Stage 02 artifact tree for base_payload()."""
    write_config(root, base_payload())
    config = load_madlib_config(root)

    data = root / "output" / "data"
    figures = root / "output" / "figures"
    reports = root / "output" / "reports"
    manuscript = root / "output" / "manuscript"
    for directory in (data, figures, reports, manuscript):
        directory.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    provenance: dict[str, dict[str, str]] = {}
    for slot in config.slots:
        for ordinal in range(1, slot.count + 1):
            name = slot.name.upper() if slot.count == 1 else f"{slot.name.upper()}_{ordinal}"
            rows.append(
                {
                    "variable_name": name,
                    "slot_name": slot.name,
                    "category": slot.category,
                    "value": f"value-{name.lower()}",
                    "section": slot.section,
                    "ordinal": ordinal,
                    "source_key": f"manuscript/config.yaml#madlib.lexicon.{slot.category}[0]",
                }
            )
            provenance[name] = {
                "category": slot.category,
                "value": f"value-{name.lower()}",
                "section": slot.section,
                "source": f"manuscript/config.yaml#madlib.lexicon.{slot.category}[0]",
            }
    (data / "token_inventory.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    (data / "section_plan.json").write_text(
        json.dumps(
            {
                "section_token_counts": {
                    section: sum(1 for row in rows if row["section"] == section)
                    for section in SECTION_KEYS
                    if any(row["section"] == section for row in rows)
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    inventory = [
        {"origin": "explicit", "path": path, "scope": "schema", "summary": "x"} for path in config.explicit_paths
    ]
    inventory += [
        {"origin": "defaulted", "path": path, "scope": "schema", "summary": "x"} for path in config.defaulted_paths
    ]
    (data / "configured_field_inventory.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    (data / "manuscript_variables.json").write_text(
        json.dumps(
            {"PROJECT_TITLE": config.title, "CONFIG_SEED": str(config.seed), "TOKEN_CHOICE_COUNT": str(len(rows))},
            indent=2,
        ),
        encoding="utf-8",
    )
    (reports / "injection_trace.json").write_text(
        json.dumps(
            {"seed": config.seed, "composition_depth": config.composition_depth, "provenance": provenance}, indent=2
        ),
        encoding="utf-8",
    )
    (reports / "madlib_summary.md").write_text("# summary\n", encoding="utf-8")
    (reports / "configured_field_summary.md").write_text("# fields\n", encoding="utf-8")
    for filename in DECLARED_FIGURE_FILES:
        if filename != "figure_registry.json":
            (figures / filename).write_bytes(b"")
    registry = {
        "fig:" + filename.removesuffix(".png").replace("_", "-"): {
            "filename": filename,
            "caption": filename,
            "label": "fig:" + filename.removesuffix(".png").replace("_", "-"),
            "section": "Results",
            "generated_by": "tests",
        }
        for filename in DECLARED_FIGURE_FILES
        if filename != "figure_registry.json"
    }
    (figures / "figure_registry.json").write_text(json.dumps(registry, indent=2), encoding="utf-8")
    (manuscript / "06_evaluation.md").write_text(
        "Evaluation prose. " + ", ".join(probe.name for probe in config.quality_probes) + "\n", encoding="utf-8"
    )
    (manuscript / "10_authoring_contract.md").write_text(
        "Contract prose. " + ", ".join(obligation.name for obligation in config.authoring_obligations) + "\n",
        encoding="utf-8",
    )
    (manuscript / "03_results.md").write_text("![density](../output/figures/token_density.png)\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Valid-tree acceptance
# ---------------------------------------------------------------------------


def test_validator_passes_on_committed_outputs() -> None:
    """The regenerated, committed Stage 02 outputs must validate cleanly."""
    result = validate_generated_outputs(PROJECT_ROOT)
    assert result.passed, [issue.message for issue in result.issues]
    assert len(result.issues) == 0


def test_validator_passes_on_minimal_fixture(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    result = validate_generated_outputs(tmp_path)
    assert result.passed, [issue.message for issue in result.issues]
    assert result.measured["token_choices"] == 4
    assert result.measured["figure_entries"] == 9
    assert result.measured["figure_references"] == 1


def test_write_validation_report_roundtrip(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    report = write_validation_report(tmp_path)
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["passed"] is True
    assert payload["issue_count"] == 0
    assert payload["schema_version"] == 1
    assert report.is_file()


# ---------------------------------------------------------------------------
# Hydrated placeholder and manuscript surface
# ---------------------------------------------------------------------------


def test_unresolved_placeholder_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    manuscript = tmp_path / "output" / "manuscript"
    (manuscript / "03_results.md").write_text(
        "![density](../output/figures/token_density.png)\n\n{{STRAY_TOKEN}}\n", encoding="utf-8"
    )
    assert "unresolved-placeholder" in _codes(validate_generated_outputs(tmp_path))


def test_manuscript_dir_missing_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    import shutil

    shutil.rmtree(tmp_path / "output" / "manuscript")
    assert "manuscript-dir-missing" in _codes(validate_generated_outputs(tmp_path))


def test_obligation_missing_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    (tmp_path / "output" / "manuscript" / "10_authoring_contract.md").write_text(
        "Contract prose without obligations.\n", encoding="utf-8"
    )
    assert "obligation-missing" in _codes(validate_generated_outputs(tmp_path))


def test_probe_missing_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    (tmp_path / "output" / "manuscript" / "06_evaluation.md").write_text(
        "Evaluation prose without probes.\n", encoding="utf-8"
    )
    assert "probe-missing" in _codes(validate_generated_outputs(tmp_path))


def test_contract_file_missing_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    (tmp_path / "output" / "manuscript" / "10_authoring_contract.md").unlink()
    assert "contract-file-missing" in _codes(validate_generated_outputs(tmp_path))


# ---------------------------------------------------------------------------
# Token provenance bindings
# ---------------------------------------------------------------------------


def test_token_inventory_missing_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    (tmp_path / "output" / "data" / "token_inventory.json").unlink()
    assert "token-inventory-missing" in _codes(validate_generated_outputs(tmp_path))


def test_token_count_mismatch_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    rows = json.loads((tmp_path / "output" / "data" / "token_inventory.json").read_text(encoding="utf-8"))
    (tmp_path / "output" / "data" / "token_inventory.json").write_text(json.dumps(rows[:3]), encoding="utf-8")
    assert "token-count-mismatch" in _codes(validate_generated_outputs(tmp_path))


def test_token_section_unknown_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    rows = json.loads((tmp_path / "output" / "data" / "token_inventory.json").read_text(encoding="utf-8"))
    rows[0]["section"] = "appendix"
    (tmp_path / "output" / "data" / "token_inventory.json").write_text(json.dumps(rows), encoding="utf-8")
    assert "token-section-unknown" in _codes(validate_generated_outputs(tmp_path))


def test_token_source_key_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    rows = json.loads((tmp_path / "output" / "data" / "token_inventory.json").read_text(encoding="utf-8"))
    rows[0]["source_key"] = "output/handwritten.txt"
    (tmp_path / "output" / "data" / "token_inventory.json").write_text(json.dumps(rows), encoding="utf-8")
    assert "token-source-key" in _codes(validate_generated_outputs(tmp_path))


def test_trace_missing_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    (tmp_path / "output" / "reports" / "injection_trace.json").unlink()
    assert "trace-missing" in _codes(validate_generated_outputs(tmp_path))


def test_trace_seed_mismatch_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    trace_path = tmp_path / "output" / "reports" / "injection_trace.json"
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    trace["seed"] = 999
    trace_path.write_text(json.dumps(trace), encoding="utf-8")
    assert "trace-seed-mismatch" in _codes(validate_generated_outputs(tmp_path))


def test_trace_provenance_gap_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    trace_path = tmp_path / "output" / "reports" / "injection_trace.json"
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    trace["provenance"] = dict(list(trace["provenance"].items())[:-1])
    trace_path.write_text(json.dumps(trace), encoding="utf-8")
    assert "trace-provenance-gap" in _codes(validate_generated_outputs(tmp_path))


def test_section_plan_missing_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    (tmp_path / "output" / "data" / "section_plan.json").unlink()
    assert "section-plan-missing" in _codes(validate_generated_outputs(tmp_path))


def test_section_token_count_mismatch_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    plan_path = tmp_path / "output" / "data" / "section_plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["section_token_counts"]["abstract"] += 1
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    assert "section-token-count-mismatch" in _codes(validate_generated_outputs(tmp_path))


# ---------------------------------------------------------------------------
# Figure registry bindings
# ---------------------------------------------------------------------------


def test_registry_missing_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    (tmp_path / "output" / "figures" / "figure_registry.json").unlink()
    assert "registry-missing" in _codes(validate_generated_outputs(tmp_path))


def test_registry_file_missing_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    (tmp_path / "output" / "figures" / "token_density.png").unlink()
    codes = _codes(validate_generated_outputs(tmp_path))
    assert "registry-file-missing" in codes
    assert "figure-set-incomplete" in codes


def test_figure_ref_unregistered_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    (tmp_path / "output" / "manuscript" / "03_results.md").write_text(
        "![ghost](../output/figures/ghost.png)\n", encoding="utf-8"
    )
    assert "figure-ref-unregistered" in _codes(validate_generated_outputs(tmp_path))


def test_undeclared_figure_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    (tmp_path / "output" / "figures" / "extra.png").write_bytes(b"")
    assert "artifact-undeclared" in _codes(validate_generated_outputs(tmp_path))


def test_figures_dir_missing_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    import shutil

    shutil.rmtree(tmp_path / "output" / "figures")
    assert "figures-dir-missing" in _codes(validate_generated_outputs(tmp_path))


# ---------------------------------------------------------------------------
# Configured-field and stale-artifact guards
# ---------------------------------------------------------------------------


def test_field_inventory_missing_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    (tmp_path / "output" / "data" / "configured_field_inventory.json").unlink()
    assert "field-inventory-missing" in _codes(validate_generated_outputs(tmp_path))


def test_field_row_schema_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    path = tmp_path / "output" / "data" / "configured_field_inventory.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    rows[0]["origin"] = "handwritten"
    path.write_text(json.dumps(rows), encoding="utf-8")
    assert "field-row-schema" in _codes(validate_generated_outputs(tmp_path))


def test_field_origin_count_mismatch_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    path = tmp_path / "output" / "data" / "configured_field_inventory.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    rows.append({"origin": "explicit", "path": "madlib.extra", "scope": "schema", "summary": "x"})
    path.write_text(json.dumps(rows), encoding="utf-8")
    assert "field-origin-count-mismatch" in _codes(validate_generated_outputs(tmp_path))


def test_undeclared_data_file_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    (tmp_path / "output" / "data" / "extra.json").write_text("{}", encoding="utf-8")
    assert "artifact-undeclared" in _codes(validate_generated_outputs(tmp_path))


def test_missing_declared_data_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    (tmp_path / "output" / "data" / "section_plan.json").unlink()
    assert "artifact-missing" in _codes(validate_generated_outputs(tmp_path))


def test_data_dir_missing_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    import shutil

    shutil.rmtree(tmp_path / "output" / "data")
    assert "data-dir-missing" in _codes(validate_generated_outputs(tmp_path))


def test_report_missing_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    (tmp_path / "output" / "reports" / "madlib_summary.md").unlink()
    assert "report-missing" in _codes(validate_generated_outputs(tmp_path))


# ---------------------------------------------------------------------------
# Variable binding and config load
# ---------------------------------------------------------------------------


def test_variables_missing_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    (tmp_path / "output" / "data" / "manuscript_variables.json").unlink()
    assert "variables-missing" in _codes(validate_generated_outputs(tmp_path))


def test_variable_mismatch_reported(tmp_path: Path) -> None:
    _write_minimal_outputs(tmp_path)
    path = tmp_path / "output" / "data" / "manuscript_variables.json"
    variables = json.loads(path.read_text(encoding="utf-8"))
    variables["PROJECT_TITLE"] = "Wrong Title"
    path.write_text(json.dumps(variables), encoding="utf-8")
    assert "variable-mismatch" in _codes(validate_generated_outputs(tmp_path))


def test_config_load_failure_reported(tmp_path: Path) -> None:
    result = validate_generated_outputs(tmp_path)
    assert "config-load" in _codes(result)


def test_injected_config_skips_reload(tmp_path: Path) -> None:
    """An injected MadlibConfig avoids reloading manuscript/config.yaml."""
    _write_minimal_outputs(tmp_path)
    config = load_madlib_config(tmp_path)
    result = validate_generated_outputs(tmp_path, config=config)
    assert result.passed
