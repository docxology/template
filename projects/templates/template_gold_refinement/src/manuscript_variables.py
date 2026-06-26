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
    from .purity import format_purity, purity_to_nines
    from .refinery import run_refinery
except ImportError:  # pragma: no cover
    from composition import generate_token_plan  # type: ignore[no-redef]
    from config import load_gold_refinement_config  # type: ignore[no-redef]
    from purity import format_purity, purity_to_nines  # type: ignore[no-redef]
    from refinery import run_refinery  # type: ignore[no-redef]

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

    # Run the refinery
    refinery_result = run_refinery()

    # Load optional analysis outputs
    analysis_path = project_root / "output" / "data" / "refinery_results.json"
    if analysis_path.exists():
        with analysis_path.open("r") as f:
            json.load(f)  # Validate file is readable JSON
    elif require_analysis_outputs:
        raise FileNotFoundError(
            f"Analysis outputs required but missing: {analysis_path}. "
            "Run projects/templates/template_gold_refinement/scripts/refinement_analysis.py first."
        )

    # Generate the token plan
    token_plan = generate_token_plan(gr_config)

    artifact_counts = _count_output_artifacts(project_root)

    variables: dict[str, str] = {}

    # ---- Paper metadata ----
    paper = config.get("paper", {})
    variables["CONFIG_VERSION"] = paper.get("version", "0.1.0")

    # ---- Refinery stage variables ----
    variables["REFINERY_NUM_STAGES"] = str(refinery_result.stage_count)
    variables["REFINERY_FINAL_PURITY"] = format_purity(refinery_result.final_purity)
    variables["REFINERY_FINAL_KARAT"] = refinery_result.final_karat.label
    variables["REFINERY_TOTAL_GAIN"] = format_purity(refinery_result.total_purity_gain)
    variables["REFINERY_IS_CERTIFIED"] = "Yes" if refinery_result.is_nine_nines_certified else "No"
    variables["REFINERY_FINAL_NINES"] = str(purity_to_nines(refinery_result.final_purity))

    # Stage labels
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

    # Stage label table rows for manuscript tables
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

    # Purity sequence for figures
    variables["PURITY_SEQUENCE"] = ", ".join(f"{p:.6f}" for p in refinery_result.purity_sequence)

    # ---- Token plan variables ----
    variables["TOKEN_COUNT"] = str(len(token_plan.choices))
    variables["TOKEN_SEED"] = str(token_plan.seed)

    # Category counts table
    cat_rows = []
    for cat, count in sorted(token_plan.category_counts.items()):
        cat_rows.append(f"| {cat} | {count} |")
    variables["TOKEN_CATEGORY_TABLE"] = "\n".join(cat_rows)

    # Section counts table
    sec_rows = []
    for sec, count in sorted(token_plan.section_counts.items()):
        sec_rows.append(f"| {sec} | {count} |")
    variables["TOKEN_SECTION_TABLE"] = "\n".join(sec_rows)

    # Individual token values for manuscript injection
    for choice in token_plan.choices:
        variables[choice.variable_name] = choice.value

    # Provenance table
    prov_rows = []
    for var_name, prov in sorted(token_plan.provenance.items()):
        prov_rows.append(
            f"| {var_name} | {prov['category']} | {prov['value']} | {prov['section']} | {prov['source']} |"
        )
    variables["TOKEN_PROVENANCE_TABLE"] = "\n".join(prov_rows)

    # ---- Config-derived ----
    variables["CONFIG_SEED"] = str(gr_config.seed)
    variables["CONFIG_DEPTH"] = gr_config.composition_depth
    variables["CONFIG_NUM_ENABLED_SECTIONS"] = str(len(gr_config.enabled_sections))
    variables["CONFIG_ENABLED_SECTIONS"] = ", ".join(gr_config.enabled_sections)
    variables["CONFIG_NUM_LEXICON_CATEGORIES"] = str(len(gr_config.lexicon))
    variables["CONFIG_NUM_SLOTS"] = str(len(gr_config.slots))
    variables["CONFIG_TOTAL_TOKEN_COUNT"] = str(gr_config.total_token_count)

    # Lexicon inventory counts
    lex_rows = []
    for cat, vals in sorted(gr_config.lexicon.items()):
        lex_rows.append(f"| {cat} | {len(vals)} | {', '.join(vals[:3])}... |")
    variables["LEXICON_TABLE"] = "\n".join(lex_rows)

    # ---- Artifact counts ----
    variables["ARTIFACT_FIGURES"] = str(artifact_counts.get("figures", 0))
    variables["ARTIFACT_DATA_FILES"] = str(artifact_counts.get("data", 0))
    variables["ARTIFACT_REPORTS"] = str(artifact_counts.get("reports", 0))
    variables["ARTIFACT_TOTAL"] = str(sum(artifact_counts.values()))

    # ---- Provenance ----
    variables["CONFIG_HASH"] = _compute_config_hash(project_root)
    variables["GENERATION_TIMESTAMP"] = _build_timestamp()
    variables["PYTHON_VERSION"] = platform.python_version()

    # ---- Author / keyword metadata ----
    authors = config.get("authors", [])
    variables["CONFIG_FIRST_AUTHOR"] = authors[0].get("name", "Unknown") if authors else "Unknown"
    variables["CONFIG_KEYWORDS"] = ", ".join(config.get("keywords", []))

    # ---- Section titles ----
    for section, title in gr_config.section_titles.items():
        upper = section.upper()
        variables[f"TITLE_{upper}"] = title

    # ---- Figure references ----
    # Figure images with labels — each appears only once in the manuscript
    # to avoid pandoc-crossref duplicate label errors.
    variables["FIGURE_PURITY_PROGRESSION"] = (
        "![Purity progression across refinery stages](../output/figures/purity_progression.png)"
        "{#fig:purity_progression}"
    )
    variables["FIGURE_KARAT_GRADING"] = (
        "![Gold karat grading scale with refinery stage markers](../output/figures/karat_grading.png)"
        "{#fig:karat_grading}"
    )
    variables["FIGURE_TOKEN_DENSITY"] = (
        "![Mega-madlib token distribution](../output/figures/token_density.png){#fig:token_density}"
    )
    variables["FIGURE_PROVENANCE_SANKEY"] = (
        "![Provenance flow diagram](../output/figures/provenance_sankey.png){#fig:provenance_sankey}"
    )
    variables["FIGURE_PURITY_CLAIM_SCATTER"] = (
        "![Purity vs claim support](../output/figures/purity_claim_scatter.png){#fig:purity_claim_scatter}"
    )
    variables["FIGURE_TOKEN_HEATMAP"] = (
        "![Token selection heatmap](../output/figures/token_heatmap.png){#fig:token_heatmap}"
    )

    # ---- Contribution claims table ----
    claim_rows = []
    for claim in gr_config.contribution_claims:
        claim_rows.append(
            f"| {claim.get('name', '')} "
            f"| {claim.get('claim', '')} "
            f"| {claim.get('evidence', '')} "
            f"| {claim.get('boundary', '')} |"
        )
    variables["CONTRIBUTION_CLAIMS_TABLE"] = "\n".join(claim_rows)

    # ---- Pipeline phases table ----
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

    # ---- Audit rules table ----
    audit_rows = []
    for rule in gr_config.audit_rules:
        audit_rows.append(f"| {rule.get('name', '')} | {rule.get('check', '')} | {rule.get('test', '')} |")
    variables["AUDIT_RULES_TABLE"] = "\n".join(audit_rows)

    # ---- Design principles table ----
    principle_rows = []
    for p in gr_config.design_principles:
        principle_rows.append(f"| {p.get('name', '')} | {p.get('rationale', '')} |")
    variables["DESIGN_PRINCIPLES_TABLE"] = "\n".join(principle_rows)

    # ---- Quality probes table ----
    probe_rows = []
    for probe in gr_config.quality_probes:
        probe_rows.append(
            f"| {probe.get('name', '')} "
            f"| {probe.get('question', '')} "
            f"| {probe.get('passing_signal', '')} "
            f"| {probe.get('artifact', '')} |"
        )
    variables["QUALITY_PROBES_TABLE"] = "\n".join(probe_rows)

    # ---- Failure modes table ----
    failure_rows = []
    for fm in gr_config.failure_modes:
        failure_rows.append(
            f"| {fm.get('name', '')} | {fm.get('risk', '')} | {fm.get('detection', '')} | {fm.get('mitigation', '')} |"
        )
    variables["FAILURE_MODES_TABLE"] = "\n".join(failure_rows)

    # ---- Manuscript staleness detection ----
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
