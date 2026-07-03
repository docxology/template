"""Manuscript variable generation for the template_gold_refinement exemplar.

Reads:
- ``manuscript/config.yaml`` — gold_refinement block and paper metadata
- ``src/refinery.py`` — canonical refinery stages and purity values
- ``src/purity.py`` — karat grades and nine-nines
- ``src/composition.py`` — token plan and section bodies

Returns a flat ``dict[str, str]`` of UPPERCASE_KEY → value for
``{{TOKEN}}`` substitution via
:func:`infrastructure.rendering.manuscript_injection.write_resolved_manuscript_tree`.

Called exclusively by ``scripts/z_generate_manuscript_variables.py``.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

try:
    from .composition import generate_token_plan
    from .config import load_gold_refinement_config
    from .evidence import build_evidence_registry
    from .formalisms import (
        equation_labels,
        formalism_count,
        formalism_equation_blocks,
        formalism_table_rows,
        formalism_traceability_rows,
    )
    from .integrity import (
        build_evidence_tiers,
        build_integrity_dimensions,
        evidence_tier_table_rows,
        integrity_dimension_table_rows,
        integrity_owner_table_rows,
        integrity_summary_line,
    )
    from .purity import format_purity, purity_to_nines
    from .refinery import run_refinery
    from .security_assay import (
        build_security_assay,
        security_assay_summary_line,
        security_assay_table_rows,
    )
except ImportError:  # pragma: no cover
    from composition import generate_token_plan  # type: ignore[no-redef]
    from config import load_gold_refinement_config  # type: ignore[no-redef]
    from evidence import build_evidence_registry  # type: ignore[no-redef]
    from formalisms import (  # type: ignore[no-redef]
        equation_labels,
        formalism_count,
        formalism_equation_blocks,
        formalism_table_rows,
        formalism_traceability_rows,
    )
    from integrity import (  # type: ignore[no-redef]
        build_evidence_tiers,
        build_integrity_dimensions,
        evidence_tier_table_rows,
        integrity_dimension_table_rows,
        integrity_owner_table_rows,
        integrity_summary_line,
    )
    from purity import format_purity, purity_to_nines  # type: ignore[no-redef]
    from refinery import run_refinery  # type: ignore[no-redef]
    from security_assay import (  # type: ignore[no-redef]
        build_security_assay,
        security_assay_summary_line,
        security_assay_table_rows,
    )

import logging

logger = logging.getLogger(__name__)


def _build_timestamp() -> str:
    """Build timestamp, honoring ``SOURCE_DATE_EPOCH`` for reproducible builds."""
    epoch = os.environ.get("SOURCE_DATE_EPOCH", "").strip()
    if epoch.isdigit():
        return datetime.fromtimestamp(int(epoch), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------- #
# I/O helpers — thin readers, no business logic
# --------------------------------------------------------------------------- #


def _load_config(project_root: Path) -> dict[str, Any]:
    config_path = project_root / "manuscript" / "config.yaml"
    if not config_path.exists():
        logger.warning("Config file not found: %s", config_path)
        return {}
    with config_path.open("r") as f:
        return yaml.safe_load(f) or {}


def _compute_config_hash(project_root: Path) -> str:
    config_path = project_root / "manuscript" / "config.yaml"
    if not config_path.exists():
        return "N/A"
    return hashlib.sha256(config_path.read_bytes()).hexdigest()[:16]


def _count_output_artifacts(project_root: Path) -> dict[str, int]:
    """Count generated artifacts by category."""
    _SUFFIXES: dict[str, set[str]] = {
        "figures": {".png", ".pdf", ".svg", ".jpg", ".jpeg"},
        "data": {".csv", ".npz", ".json", ".parquet"},
        "reports": {".json", ".md", ".html", ".txt"},
    }
    counts: dict[str, int] = {}
    output_dir = project_root / "output"
    for subdir, suffixes in _SUFFIXES.items():
        dir_path = output_dir / subdir
        if dir_path.exists():
            counts[subdir] = sum(1 for f in dir_path.iterdir() if f.is_file() and f.suffix.lower() in suffixes)
        else:
            counts[subdir] = 0
    return counts


def _load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def _shared_evidence_kind_rows(shared_evidence: dict[str, Any]) -> str:
    kind_counts = shared_evidence.get("kind_counts", {})
    if not isinstance(kind_counts, dict) or not kind_counts:
        return "| not generated | 0 |"
    return "\n".join(f"| {kind} | {count} |" for kind, count in sorted(kind_counts.items()))


def _figure_quality_table_rows(figure_quality: dict[str, Any]) -> str:
    records = figure_quality.get("records", [])
    if not isinstance(records, list) or not records:
        return "| not generated | no | no | 0x0 | 0.000 | 0.00000000 | missing |"
    rows = []
    for record in sorted(
        (item for item in records if isinstance(item, dict)),
        key=lambda item: str(item.get("name", "")),
    ):
        width = int(record.get("width_px", 0) or 0)
        height = int(record.get("height_px", 0) or 0)
        status = "pass" if record.get("passes_quality") else "fail"
        rows.append(
            f"| {record.get('name', '')} "
            f"| {'yes' if record.get('png_exists') else 'no'} "
            f"| {'yes' if record.get('svg_exists') else 'no'} "
            f"| {width}x{height} "
            f"| {float(record.get('nonwhite_fraction', 0.0) or 0.0):.3f} "
            f"| {float(record.get('color_variance', 0.0) or 0.0):.8f} "
            f"| {status} |"
        )
    return "\n".join(rows)


def _add_refinery_variables(variables: dict[str, str], refinery_result: Any) -> None:
    variables["REFINERY_NUM_STAGES"] = str(refinery_result.stage_count)
    variables["REFINERY_FINAL_PURITY"] = format_purity(refinery_result.final_purity)
    variables["REFINERY_FINAL_KARAT"] = refinery_result.final_karat.label
    variables["REFINERY_TOTAL_GAIN"] = format_purity(refinery_result.total_purity_gain)
    variables["REFINERY_IS_CERTIFIED"] = "Yes" if refinery_result.is_nine_nines_certified else "No"
    variables["REFINERY_FINAL_NINES"] = str(purity_to_nines(refinery_result.final_purity))

    for i, stage in enumerate(refinery_result.stages):
        prefix = f"STAGE_{i + 1}"
        variables[f"{prefix}_NAME"] = stage.name
        variables[f"{prefix}_METAL_OP"] = stage.metallurgical_operation
        variables[f"{prefix}_MANUSCRIPT_OP"] = stage.manuscript_operation
        variables[f"{prefix}_INPUT_PURITY"] = format_purity(stage.input_purity)
        variables[f"{prefix}_OUTPUT_PURITY"] = format_purity(stage.output_purity)
        variables[f"{prefix}_KARAT"] = stage.karat_grade.label
        variables[f"{prefix}_GAIN"] = format_purity(stage.purity_gain)

    variables["REFINERY_STAGE_LABELS"] = "\n".join(f"- {label}" for label in refinery_result.stage_labels)

    table_rows = []
    for stage in refinery_result.stages:
        table_rows.append(
            f"| {stage.order} "
            f"| {stage.name} "
            f"| {format_purity(stage.output_purity)} "
            f"| {stage.karat_grade.label} "
            f"| {stage.metallurgical_operation} |"
        )
    variables["STAGE_TABLE_ROWS"] = "\n".join(table_rows)
    variables["PURITY_SEQUENCE"] = ", ".join(f"{p:.6f}" for p in refinery_result.purity_sequence)


def _add_token_variables(variables: dict[str, str], token_plan: Any) -> None:
    variables["TOKEN_COUNT"] = str(len(token_plan.choices))
    variables["TOKEN_SEED"] = str(token_plan.seed)

    cat_rows = []
    for cat, count in sorted(token_plan.category_counts.items()):
        cat_rows.append(f"| {cat} | {count} |")
    variables["TOKEN_CATEGORY_TABLE"] = "\n".join(cat_rows)

    sec_rows = []
    for sec, count in sorted(token_plan.section_counts.items()):
        sec_rows.append(f"| {sec} | {count} |")
    variables["TOKEN_SECTION_TABLE"] = "\n".join(sec_rows)

    for choice in token_plan.choices:
        variables[choice.variable_name] = choice.value

    prov_rows = []
    for var_name, prov in sorted(token_plan.provenance.items()):
        prov_rows.append(
            f"| {var_name} | {prov['category']} | {prov['value']} | {prov['section']} | {prov['source']} |"
        )
    variables["TOKEN_PROVENANCE_TABLE"] = "\n".join(prov_rows)


def _add_config_variables(
    variables: dict[str, str],
    config: dict[str, Any],
    gr_config: Any,
    artifact_counts: dict[str, int],
    project_root: Path,
) -> None:
    paper = config.get("paper", {})
    variables["CONFIG_VERSION"] = paper.get("version", "0.1.0")

    variables["CONFIG_SEED"] = str(gr_config.seed)
    variables["CONFIG_DEPTH"] = gr_config.composition_depth
    variables["CONFIG_NUM_ENABLED_SECTIONS"] = str(len(gr_config.enabled_sections))
    variables["CONFIG_ENABLED_SECTIONS"] = ", ".join(gr_config.enabled_sections)
    variables["CONFIG_NUM_LEXICON_CATEGORIES"] = str(len(gr_config.lexicon))
    variables["CONFIG_NUM_SLOTS"] = str(len(gr_config.slots))
    variables["CONFIG_TOTAL_TOKEN_COUNT"] = str(gr_config.total_token_count)

    lex_rows = []
    for cat, vals in sorted(gr_config.lexicon.items()):
        lex_rows.append(f"| {cat} | {len(vals)} | {', '.join(vals[:3])}... |")
    variables["LEXICON_TABLE"] = "\n".join(lex_rows)

    variables["ARTIFACT_FIGURES"] = str(artifact_counts.get("figures", 0))
    variables["ARTIFACT_DATA_FILES"] = str(artifact_counts.get("data", 0))
    variables["ARTIFACT_REPORTS"] = str(artifact_counts.get("reports", 0))
    variables["ARTIFACT_TOTAL"] = str(sum(artifact_counts.values()))

    variables["CONFIG_HASH"] = _compute_config_hash(project_root)
    variables["GENERATION_TIMESTAMP"] = _build_timestamp()
    variables["PYTHON_VERSION"] = platform.python_version()

    authors = config.get("authors", [])
    variables["CONFIG_FIRST_AUTHOR"] = authors[0].get("name", "Unknown") if authors else "Unknown"
    variables["CONFIG_KEYWORDS"] = ", ".join(config.get("keywords", []))

    for section, title in gr_config.section_titles.items():
        upper = section.upper()
        variables[f"TITLE_{upper}"] = title


def _add_figure_variables(variables: dict[str, str], project_root: Path) -> None:
    variables["FIGURE_PURITY_PROGRESSION"] = (
        "![Purity progression across refinery stages](../output/figures/purity_progression.png)"
        "{#fig:purity_progression}"
    )
    variables["FIGURE_KARAT_GRADING"] = (
        "![Gold karat grading scale with refinery stage markers](../output/figures/karat_grading.png)"
        "{#fig:karat_grading}"
    )
    variables["FIGURE_TOKEN_DENSITY"] = (  # nosec B105
        "![Mega-madlib token distribution](../output/figures/token_density.png){#fig:token_density}"
    )
    variables["FIGURE_PROVENANCE_SANKEY"] = (
        "![Provenance flow diagram](../output/figures/provenance_sankey.png){#fig:provenance_sankey}"
    )
    variables["FIGURE_PURITY_CLAIM_SCATTER"] = (
        "![Purity vs claim support](../output/figures/purity_claim_scatter.png){#fig:purity_claim_scatter}"
    )
    variables["FIGURE_TOKEN_HEATMAP"] = (  # nosec B105
        "![Token selection heatmap](../output/figures/token_heatmap.png){#fig:token_heatmap}"
    )
    variables["FIGURE_INTEGRITY_GATE_MATRIX"] = (
        "![Integrity-gate matrix](../output/figures/integrity_gate_matrix.png){#fig:integrity_gate_matrix}"
    )
    variables["FIGURE_FORMALISM_TRACEABILITY"] = (
        "![Formalism traceability](../output/figures/formalism_traceability.png){#fig:formalism_traceability}"
    )
    variables["FIGURE_IMPLEMENTATION_CIRCUIT"] = (
        "![Gold-refinement implementation circuit](../output/figures/implementation_circuit.png)"
        "{#fig:implementation_circuit}"
    )
    variables["FIGURE_CLAIM_EVIDENCE_ASSAY"] = (
        "![Claim-evidence assay](../output/figures/claim_evidence_assay.png){#fig:claim_evidence_assay}"
    )
    variables["FIGURE_INTEGRITY_RISK_MATRIX"] = (
        "![Scientific-integrity risk matrix](../output/figures/integrity_risk_matrix.png){#fig:integrity_risk_matrix}"
    )
    variables["FIGURE_EVIDENCE_TIER_LADDER"] = (
        "![Evidence-tier ladder](../output/figures/evidence_tier_ladder.png){#fig:evidence_tier_ladder}"
    )

    figure_quality = _load_json_object(project_root / "output" / "reports" / "figure_quality_report.json")
    figure_count = int(figure_quality.get("figure_count", 0) or 0)
    passing_count = int(figure_quality.get("passing_count", 0) or 0)
    registry_parity = bool(figure_quality.get("registry_parity", False))
    if figure_count == 0:
        quality_status = "not generated"
    elif passing_count == figure_count and registry_parity:
        quality_status = "passing"
    else:
        quality_status = "failing"
    variables["FIGURE_QUALITY_REPORT_PATH"] = "output/reports/figure_quality_report.json"
    variables["FIGURE_QUALITY_TOTAL"] = str(figure_count)
    variables["FIGURE_QUALITY_PNG_COUNT"] = str(int(figure_quality.get("png_count", 0) or 0))
    variables["FIGURE_QUALITY_SVG_COUNT"] = str(int(figure_quality.get("svg_count", 0) or 0))
    variables["FIGURE_QUALITY_PASSING_COUNT"] = str(passing_count)
    variables["FIGURE_QUALITY_REGISTRY_PARITY"] = "Yes" if registry_parity else "No"
    variables["FIGURE_QUALITY_STATUS"] = quality_status
    variables["FIGURE_QUALITY_TABLE"] = _figure_quality_table_rows(figure_quality)


def _add_claim_and_evidence_variables(variables: dict[str, str], gr_config: Any, project_root: Path) -> dict[str, Any]:
    claim_rows = []
    for claim in gr_config.contribution_claims:
        claim_rows.append(
            f"| {claim.get('name', '')} "
            f"| {claim.get('claim', '')} "
            f"| {claim.get('evidence', '')} "
            f"| {claim.get('boundary', '')} |"
        )
    variables["CONTRIBUTION_CLAIMS_TABLE"] = "\n".join(claim_rows)

    phase_rows = []
    for phase in gr_config.pipeline_phases:
        phase_rows.append(
            f"| {phase.get('name', '')} "
            f"| {phase.get('input_artifact', '')} "
            f"| {phase.get('transformation', '')} "
            f"| {phase.get('output_artifact', '')} "
            f"| {phase.get('guard', '')} |"
        )
    variables["PIPELINE_PHASES_TABLE"] = "\n".join(phase_rows)

    audit_rows = []
    for rule in gr_config.audit_rules:
        audit_rows.append(f"| {rule.get('name', '')} | {rule.get('check', '')} | {rule.get('test', '')} |")
    variables["AUDIT_RULES_TABLE"] = "\n".join(audit_rows)

    principle_rows = []
    for p in gr_config.design_principles:
        principle_rows.append(f"| {p.get('name', '')} | {p.get('rationale', '')} |")
    variables["DESIGN_PRINCIPLES_TABLE"] = "\n".join(principle_rows)

    probe_rows = []
    for probe in gr_config.quality_probes:
        probe_rows.append(
            f"| {probe.get('name', '')} "
            f"| {probe.get('question', '')} "
            f"| {probe.get('passing_signal', '')} "
            f"| {probe.get('artifact', '')} |"
        )
    variables["QUALITY_PROBES_TABLE"] = "\n".join(probe_rows)

    failure_rows = []
    for fm in gr_config.failure_modes:
        failure_rows.append(
            f"| {fm.get('name', '')} | {fm.get('risk', '')} | {fm.get('detection', '')} | {fm.get('mitigation', '')} |"
        )
    variables["FAILURE_MODES_TABLE"] = "\n".join(failure_rows)

    security_records = build_security_assay(gr_config)
    variables["SECURITY_ASSAY_COUNT"] = str(len(security_records))
    variables["SECURITY_ASSAY_SUMMARY"] = security_assay_summary_line(security_records)
    variables["SECURITY_ASSAY_TABLE"] = security_assay_table_rows(security_records)
    variables["SECURITY_ASSAY_BOUNDARY"] = (
        "No Codex Security or Deep Security Scan findings are claimed unless a scan artifact is generated, "
        "validated, and cited."
    )

    labels = equation_labels()
    variables["FORMALISM_COUNT"] = str(formalism_count())
    variables["FORMALISM_TABLE_ROWS"] = formalism_table_rows()
    variables["FORMALISM_EQUATION_BLOCKS"] = formalism_equation_blocks()
    variables["FORMALISM_TRACEABILITY_TABLE"] = formalism_traceability_rows()
    variables["FORMALISM_EQUATION_LABELS"] = ", ".join(labels)
    variables["FORMALISM_EQUATION_REFS"] = ", ".join(f"[@{label}]" for label in labels)

    claim_registry = build_evidence_registry(gr_config, project_root)
    variables["CLAIM_SUPPORT_TOTAL"] = str(claim_registry.total_claims)
    variables["CLAIM_SUPPORT_SUPPORTED"] = str(claim_registry.supported_claims)
    variables["CLAIM_SUPPORT_UNSUPPORTED"] = str(claim_registry.unsupported_claims)
    variables["CLAIM_SUPPORT_RATE"] = f"{claim_registry.support_rate:.2%}"
    variables["CLAIM_SUPPORT_STATUS"] = "passing" if claim_registry.is_passing else "failing"
    variables["CLAIM_SUPPORT_REGISTRY_PATH"] = "output/reports/claim_support_registry.json"

    shared_evidence = _load_json_object(project_root / "output" / "reports" / "evidence_registry.json")
    variables["SHARED_EVIDENCE_FACT_COUNT"] = str(shared_evidence.get("fact_count", 0))
    variables["SHARED_EVIDENCE_KIND_TABLE"] = _shared_evidence_kind_rows(shared_evidence)
    variables["SHARED_EVIDENCE_SCHEMA"] = str(shared_evidence.get("schema", "not generated"))
    return shared_evidence


def _add_integrity_variables(variables: dict[str, str], gr_config: Any, shared_evidence: dict[str, Any]) -> None:
    integrity_dimensions = build_integrity_dimensions(gr_config)
    evidence_tiers = build_evidence_tiers(shared_evidence, integrity_dimensions)
    variables["INTEGRITY_DIMENSION_COUNT"] = str(len(integrity_dimensions))
    variables["INTEGRITY_RISK_SUMMARY"] = integrity_summary_line(integrity_dimensions)
    variables["INTEGRITY_DIMENSION_TABLE"] = integrity_dimension_table_rows(integrity_dimensions)
    variables["INTEGRITY_OWNER_TABLE"] = integrity_owner_table_rows(integrity_dimensions)
    variables["EVIDENCE_TIER_TABLE"] = evidence_tier_table_rows(evidence_tiers)


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #


def generate_variables(project_root: Path, *, require_analysis_outputs: bool = False) -> dict[str, str]:
    """Generate all manuscript variables from config and refinery computation.

    Args:
        project_root: Root directory of the project (containing ``manuscript/``
            and ``output/``).
        require_analysis_outputs: When True, raise if
            ``output/data/refinery_results.json`` is missing.

    Returns:
        ``dict[str, str]`` with UPPERCASE_KEY → value mapping for
        ``{{TOKEN}}`` substitution.
    """
    config = _load_config(project_root)
    gr_config = load_gold_refinement_config(project_root)
    refinery_result = run_refinery()

    analysis_path = project_root / "output" / "data" / "refinery_results.json"
    if analysis_path.exists():
        with analysis_path.open("r") as f:
            json.load(f)  # Validate file is readable JSON
    elif require_analysis_outputs:
        raise FileNotFoundError(
            f"Analysis outputs required but missing: {analysis_path}. "
            "Run projects/templates/template_gold_refinement/scripts/refinement_analysis.py first."
        )

    token_plan = generate_token_plan(gr_config)
    artifact_counts = _count_output_artifacts(project_root)

    variables: dict[str, str] = {}
    _add_refinery_variables(variables, refinery_result)
    _add_token_variables(variables, token_plan)
    _add_config_variables(variables, config, gr_config, artifact_counts, project_root)
    _add_figure_variables(variables, project_root)
    shared_evidence = _add_claim_and_evidence_variables(variables, gr_config, project_root)
    _add_integrity_variables(variables, gr_config, shared_evidence)
    variables["MANUSCRIPT_STALENESS"] = _detect_staleness(project_root)

    logger.info("Generated %d manuscript variables", len(variables))
    return variables


def _detect_staleness(project_root: Path) -> str:
    """Detect if output/manuscript/ is stale relative to source manuscript/.

    Returns a status string: 'fresh' or 'stale' with details.
    """
    source_dir = project_root / "manuscript"
    output_dir = project_root / "output" / "manuscript"

    if not output_dir.exists():
        return "stale: output/manuscript/ does not exist — run z_generate_manuscript_variables.py"

    stale_files: list[str] = []
    for src_file in sorted(source_dir.glob("*.md")):
        if src_file.name in ("AGENTS.md", "README.md", "SYNTAX.md"):
            continue
        out_file = output_dir / src_file.name
        if not out_file.exists():
            stale_files.append(f"{src_file.name}: missing from output")
        elif src_file.stat().st_mtime > out_file.stat().st_mtime:
            stale_files.append(f"{src_file.name}: source newer than output")

    if stale_files:
        return "stale: " + "; ".join(stale_files)
    return "fresh"


def save_variables(variables: dict[str, str], output_path: Path) -> Path:
    """Persist *variables* as JSON for downstream rendering and debugging."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(variables, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Saved %d variables to %s", len(variables), output_path)
    return output_path


__all__ = ["generate_variables", "save_variables"]
