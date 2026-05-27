from pathlib import Path
import json

import pytest

from gates.validation import build_lean, lean_project_present, validate_manuscript, validate_outputs
from ontology.bindings import load_section_ontology, validate_gnn_ontology
from orchestration.pipeline_manifest import analysis_scripts, DEFAULT_ANALYSIS_SCRIPTS
from simulation.logging_utils import RunLogger


def test_run_logger_emit_and_records(tmp_path: Path) -> None:
    log = RunLogger(tmp_path / "runs.jsonl")
    log.fresh()
    log.emit({"event": "test", "value": 1})
    records = log.records()
    assert len(records) == 1
    assert records[0]["event"] == "test"


def test_validate_outputs_after_analysis() -> None:
    root = Path(__file__).resolve().parents[1]
    from analysis import run_analysis

    run_analysis(root)
    checks = validate_outputs(root)
    assert checks.get("output/data/parameter_sweep.csv")


def test_validate_manuscript_contract() -> None:
    root = Path(__file__).resolve().parents[1]
    from manuscript.sheaf import compose_all_sections
    from manuscript.variables import generate_variables
    from manuscript.hydrate import write_resolved_manuscript

    compose_all_sections(root)
    write_resolved_manuscript(root, generate_variables(root, require_analysis_outputs=False))
    checks = validate_manuscript(root)
    assert checks["sheaf_manifest"]
    assert checks["sheaf_registry"]
    assert checks["sheaf_valid"]
    assert checks["coverage_matrix_valid"]
    assert checks["full_sheaf_appendix_tracks"]
    assert checks["imrad_groups_present"]
    assert checks["claim_ledger_valid"]
    assert checks["gnn_concordance"]
    assert checks["sheaf_coverage_page"]
    assert checks["sheaf_coverage_json"]
    assert checks["sheaf_coverage_heatmap"]
    assert checks["methods_sheaf_layers"]
    assert checks["manuscript_tokens_registered"]
    assert checks["resolved_manuscript_hydrated"]


def test_validate_manuscript_methods_sheaf_layers_negative(project_root: Path) -> None:
    from manuscript.sheaf import compose_all_sections

    path = project_root / "manuscript" / "08_methods_sheaf.md"
    compose_all_sections(project_root)
    original = path.read_text(encoding="utf-8")
    try:
        path.write_text(original.replace("<!-- sheaf-layers:registry -->", ""), encoding="utf-8")
        checks = validate_manuscript(project_root)
        assert checks["methods_sheaf_layers"] is False
    finally:
        path.write_text(original, encoding="utf-8")


@pytest.mark.parametrize(
    ("needle", "replacement"),
    [
        ("<!-- sheaf-layers:binding-matrix -->", ""),
        ("<!-- sheaf-layers:legend -->", ""),
        ("sheaf_layers_overview.png", "broken_layers_overview.png"),
    ],
)
def test_validate_manuscript_methods_sheaf_layers_negative_markers(
    project_root: Path,
    needle: str,
    replacement: str,
) -> None:
    from manuscript.sheaf import compose_all_sections

    path = project_root / "manuscript" / "08_methods_sheaf.md"
    compose_all_sections(project_root)
    original = path.read_text(encoding="utf-8")
    try:
        path.write_text(original.replace(needle, replacement), encoding="utf-8")
        checks = validate_manuscript(project_root)
        assert checks["methods_sheaf_layers"] is False
    finally:
        path.write_text(original, encoding="utf-8")


def test_validate_manuscript_full_sheaf_appendix_tracks_negative(project_root: Path) -> None:
    path = project_root / "manuscript" / "16_appendix_full_sheaf.md"
    original = path.read_text(encoding="utf-8")
    try:
        path.write_text(original.replace("sheaf-track:prose", "sheaf-track:broken"), encoding="utf-8")
        checks = validate_manuscript(project_root)
        assert checks["full_sheaf_appendix_tracks"] is False
    finally:
        path.write_text(original, encoding="utf-8")


def test_validate_manuscript_resolved_hydrated_negative(project_root: Path) -> None:
    from manuscript.hydrate import write_resolved_manuscript
    from manuscript.variables import generate_variables

    resolved = project_root / "output" / "manuscript" / "00_abstract.md"
    if not resolved.is_file():
        write_resolved_manuscript(project_root, generate_variables(project_root, require_analysis_outputs=False))
    original = resolved.read_text(encoding="utf-8")
    try:
        resolved.write_text(original + "\n{{unresolved_test_token}}\n", encoding="utf-8")
        checks = validate_manuscript(project_root)
        assert checks["resolved_manuscript_hydrated"] is False
    finally:
        resolved.write_text(original, encoding="utf-8")


def test_validate_outputs_required_artifacts(project_root: Path) -> None:
    from analysis import run_analysis

    run_analysis(project_root)
    checks = validate_outputs(project_root)
    required = (
        "output/data/parameter_sweep.csv",
        "output/data/analysis_statistics.json",
        "output/data/sheaf_coverage_matrix.json",
        "output/data/si_tmaze_summary.json",
        "output/figures/ising_mi_curve.png",
        "output/figures/sheaf_coverage_heatmap.png",
        "output/figures/sheaf_layers_overview.png",
        "output/reports/si_invariants.json",
        "output/reports/si_tmaze_run_report.json",
    )
    for key in required:
        assert checks.get(key), f"missing validate_outputs key: {key}"
    assert checks.get("si_invariants_all_pass") is True
    assert checks.get("invariants_all_pass") is True


def test_validate_outputs_negative_si_invariants_fail(project_root: Path, tmp_path: Path) -> None:
    path = project_root / "output" / "reports" / "si_invariants.json"
    if not path.is_file():
        pytest.skip("SI invariants report missing; run analysis first")
    backup = tmp_path / "si_invariants.json.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    payload = json.loads(backup.read_text(encoding="utf-8"))
    payload["all_pass"] = False
    payload["invariants"] = {name: False for name in payload.get("invariants", {})}
    try:
        path.write_text(json.dumps(payload), encoding="utf-8")
        checks = validate_outputs(project_root)
        assert checks["si_invariants_all_pass"] is False
        assert checks["experiment_plan_metrics"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


def test_validate_outputs_negative_analytical_invariants_fail(project_root: Path, tmp_path: Path) -> None:
    path = project_root / "output" / "reports" / "invariants.json"
    if not path.is_file():
        pytest.skip("invariants report missing; run analysis first")
    backup = tmp_path / "invariants.json.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    payload = json.loads(backup.read_text(encoding="utf-8"))
    payload["all_pass"] = False
    analytical = payload.get("invariants") or {}
    payload["invariants"] = {name: False for name in analytical}
    try:
        path.write_text(json.dumps(payload), encoding="utf-8")
        checks = validate_outputs(project_root)
        assert checks["invariants_all_pass"] is False
        assert checks["experiment_plan_metrics"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


def test_write_invariants_report_preserves_simulation_merge(project_root: Path) -> None:
    from orchestration.analysis import write_invariants_report

    inv_path = project_root / "output" / "reports" / "invariants.json"
    si_summary = project_root / "output" / "data" / "si_tmaze_summary.json"
    if not inv_path.is_file() or not si_summary.is_file():
        from analysis import run_analysis
        from simulation.si_runner import pymdp_available, run_and_persist

        run_analysis(project_root)
        if not pymdp_available():
            pytest.skip("pymdp not installed")
        run_and_persist(project_root)

    before = json.loads(inv_path.read_text(encoding="utf-8"))
    assert before.get("simulation"), "expected merged simulation invariants before rewrite"

    write_invariants_report(project_root)
    after = json.loads(inv_path.read_text(encoding="utf-8"))
    assert after.get("simulation")
    assert after.get("all_pass") is True


def test_validate_outputs_negative_missing_si_invariants_report(project_root: Path, tmp_path: Path) -> None:
    summary = project_root / "output" / "data" / "si_tmaze_summary.json"
    si_inv = project_root / "output" / "reports" / "si_invariants.json"
    if not summary.is_file():
        pytest.skip("SI summary missing; run analysis first")
    backup = tmp_path / "si_invariants.json.bak"
    had_si_inv = si_inv.is_file()
    if had_si_inv:
        backup.write_text(si_inv.read_text(encoding="utf-8"), encoding="utf-8")
        si_inv.unlink()
    try:
        checks = validate_outputs(project_root)
        assert checks["si_invariants_all_pass"] is False
        assert checks["experiment_plan_metrics"] is False
    finally:
        if had_si_inv:
            si_inv.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


def test_validate_outputs_negative_missing_sheaf_matrix(project_root: Path, tmp_path: Path) -> None:
    matrix = project_root / "output" / "data" / "sheaf_coverage_matrix.json"
    backup = tmp_path / "sheaf_coverage_matrix.json.bak"
    if matrix.is_file():
        backup.write_bytes(matrix.read_bytes())
        matrix.unlink()
    try:
        checks = validate_outputs(project_root)
        assert checks.get("output/data/sheaf_coverage_matrix.json") is False
    finally:
        if backup.is_file():
            matrix.write_bytes(backup.read_bytes())


def test_validate_outputs_negative_missing_sweep(project_root: Path, tmp_path: Path) -> None:
    sweep = project_root / "output" / "data" / "parameter_sweep.csv"
    backup = tmp_path / "parameter_sweep.csv.bak"
    if sweep.is_file():
        backup.write_bytes(sweep.read_bytes())
        sweep.unlink()
    try:
        checks = validate_outputs(project_root)
        assert checks.get("output/data/parameter_sweep.csv") is False
    finally:
        if backup.is_file():
            sweep.write_bytes(backup.read_bytes())


def test_validate_manuscript_gnn_concordance_negative(project_root: Path) -> None:
    gnn = project_root / "gnn" / "bernoulli_toy.gnn.md"
    original = gnn.read_text(encoding="utf-8")
    try:
        gnn.write_text(original.replace("pi1=Stream1PolicyVector\n", ""), encoding="utf-8")
        checks = validate_manuscript(project_root)
        assert checks["gnn_concordance"] is False
    finally:
        gnn.write_text(original, encoding="utf-8")


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


def test_validate_manuscript_tokens_registered_negative(project_root: Path) -> None:
    path = project_root / "manuscript" / "00_abstract.md"
    original = path.read_text(encoding="utf-8")
    try:
        path.write_text(original + "\n{{not_a_registered_token}}\n", encoding="utf-8")
        checks = validate_manuscript(project_root)
        assert checks["manuscript_tokens_registered"] is False
    finally:
        path.write_text(original, encoding="utf-8")


def test_sheaf_package_exports_public_symbols() -> None:
    from manuscript.sheaf import (
        GENERATED_RENDERERS,
        ImradBlock,
        SectionKind,
        coverage_cell_symbol,
        resolve_track_body,
    )

    assert coverage_cell_symbol("black") == "P"
    assert "section_figures" in GENERATED_RENDERERS
    assert resolve_track_body.__name__ == "resolve_track_body"
    assert ImradBlock is not None
    assert SectionKind is not None


def test_ontology_helpers() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "manuscript" / "sections" / "imrad" / "intro_contributions" / "ontology.yaml"
    terms = load_section_ontology(path)
    assert "location" in terms
    discussion = root / "manuscript" / "sections" / "imrad" / "discussion_outlook" / "ontology.yaml"
    discussion_terms = load_section_ontology(discussion)
    assert discussion_terms["pedagogical_scope"] == "Pedagogical scope"
    gnn = root / "gnn" / "bernoulli_toy.gnn.md"
    assert not validate_gnn_ontology(gnn)


def test_pipeline_manifest_lists_scripts() -> None:
    root = Path(__file__).resolve().parents[1]
    scripts = analysis_scripts(root)
    assert len(scripts) == len(DEFAULT_ANALYSIS_SCRIPTS)


def test_build_lean_when_present_must_succeed() -> None:
    root = Path(__file__).resolve().parents[1]
    assert lean_project_present(root)
    code, msg = build_lean(root)
    assert code == 0, msg


def test_build_lean_skips_without_lakefile(tmp_path: Path) -> None:
    assert not lean_project_present(tmp_path)
    code, msg = build_lean(tmp_path)
    assert code == 0
    assert "skipped" in msg.lower()
