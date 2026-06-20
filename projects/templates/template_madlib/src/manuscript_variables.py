from __future__ import annotations

import hashlib
import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path

from analysis import artifact_markdown_tables, configured_field_counts, configured_field_inventory
from composition import build_imrad_sections, section_title_variables
from config import load_madlib_config
from tokens import generate_token_plan


def generate_variables(project_root: Path | str) -> dict[str, str]:
    root = Path(project_root)
    config = load_madlib_config(root)
    plan = generate_token_plan(config)
    sections = build_imrad_sections(config, plan)
    tables = artifact_markdown_tables(root)
    titles = section_title_variables(config)
    field_counts = configured_field_counts(config, configured_field_inventory(config, plan))

    variables: dict[str, str] = {
        **sections,
        **tables,
        **titles,
        "PROJECT_TITLE": config.title,
        "CONFIG_SEED": str(config.seed),
        "COMPOSITION_DEPTH": config.composition_depth,
        "AUDIT_RULE_COUNT": str(len(config.audit_rules)),
        "CONTRIBUTION_CLAIM_COUNT": str(len(config.contribution_claims)),
        "EVALUATION_CRITERION_COUNT": str(len(config.evaluation_criteria)),
        "FAILURE_MODE_COUNT": str(len(config.failure_modes)),
        "DESIGN_PRINCIPLE_COUNT": str(len(config.design_principles)),
        "PIPELINE_PHASE_COUNT": str(len(config.pipeline_phases)),
        "QUALITY_PROBE_COUNT": str(len(config.quality_probes)),
        "AUTHORING_OBLIGATION_COUNT": str(len(config.authoring_obligations)),
        "CONFIGURED_FIELD_EXPLICIT_COUNT": str(field_counts["explicit"]),
        "CONFIGURED_FIELD_DEFAULTED_COUNT": str(field_counts["defaulted"]),
        "CONFIGURED_FIELD_VISUALIZED_COUNT": str(field_counts["visualized"]),
        "CONFIGURED_FIELD_SECTION_LEVEL_COUNT": str(field_counts["section_level"]),
        "CONFIGURED_FIELD_LEXICON_LEVEL_COUNT": str(field_counts["lexicon_level"]),
        "CONFIGURED_FIELD_SLOT_LEVEL_COUNT": str(field_counts["slot_level"]),
        "METHOD_STEP_COUNT": str(len(config.method_protocol)),
        "NARRATIVE_MOVE_COUNT": str(sum(len(moves) for moves in config.narrative_moves.values())),
        "LEXICON_CATEGORY_COUNT": str(len(config.lexicon)),
        "SLOT_RULE_COUNT": str(len(config.slots)),
        "TOKEN_CHOICE_COUNT": str(len(plan.choices)),
        "ENABLED_SECTION_COUNT": str(len(config.enabled_sections)),
        "CONFIG_HASH": _config_hash(config.config_path),
        "GENERATION_TIMESTAMP": _build_timestamp(),
        "PYTHON_VERSION": platform.python_version(),
        "PLATFORM": f"{platform.system()} {platform.machine()}",
    }
    for choice in plan.choices:
        variables[choice.variable_name] = choice.value
    return variables


def save_variables(variables: dict[str, str], output_path: Path | str) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(variables, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _config_hash(config_path: Path) -> str:
    return hashlib.sha256(config_path.read_bytes()).hexdigest()[:16]


def _build_timestamp() -> str:
    epoch = os.environ.get("SOURCE_DATE_EPOCH", "").strip()
    if epoch.isdigit():
        return datetime.fromtimestamp(int(epoch), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
