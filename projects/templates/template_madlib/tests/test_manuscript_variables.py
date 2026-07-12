from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from src.config import load_madlib_config
from src.manuscript_variables import _build_timestamp, generate_variables, save_variables

DOC_ONLY = frozenset({"AGENTS.md", "README.md", "SYNTAX.md"})
TOKEN_RE = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_generate_variables_contains_sections_tables_and_provenance_tokens() -> None:
    config = load_madlib_config(PROJECT_ROOT)
    variables = generate_variables(PROJECT_ROOT)

    assert "ABSTRACT_BODY" in variables
    assert "METHODS_BODY" in variables
    assert "EVALUATION_BODY" in variables
    assert "LIMITATIONS_BODY" in variables
    assert "AUTHORING_CONTRACT_BODY" in variables
    assert "TITLE_METHODS" in variables
    assert "TITLE_AUTHORING_CONTRACT" in variables
    assert "METHODS_FIGURES" in variables
    assert "RESULTS_FIGURES" in variables
    assert "CONFIGURATION_FIGURES" in variables
    assert "EVALUATION_FIGURES" in variables
    assert "CONFIGURED_FIELD_FIGURES" in variables
    assert "CONFIGURED_FIELD_SUMMARY_TABLE" in variables
    assert "CONFIGURED_FIELD_TABLE" in variables
    assert "DESIGN_PRINCIPLE_TABLE" in variables
    assert "PIPELINE_PHASE_TABLE" in variables
    assert "METHOD_PROTOCOL_TABLE" in variables
    assert "EVALUATION_CRITERIA_TABLE" in variables
    assert "QUALITY_PROBE_TABLE" in variables
    assert "FAILURE_MODE_TABLE" in variables
    assert "AUTHORING_OBLIGATION_TABLE" in variables
    assert "PROVENANCE_MATRIX_TABLE" in variables
    assert "TOKEN_INVENTORY_TABLE" in variables
    assert "STUDY_ADJECTIVE" in variables
    assert variables["CONFIG_SEED"] == "431"
    assert variables["TOKEN_CHOICE_COUNT"] == "40"
    assert variables["METHOD_STEP_COUNT"] == str(len(config.method_protocol))
    assert variables["EVALUATION_CRITERION_COUNT"] == str(len(config.evaluation_criteria))
    assert variables["FAILURE_MODE_COUNT"] == str(len(config.failure_modes))
    assert variables["DESIGN_PRINCIPLE_COUNT"] == str(len(config.design_principles))
    assert variables["PIPELINE_PHASE_COUNT"] == str(len(config.pipeline_phases))
    assert variables["QUALITY_PROBE_COUNT"] == str(len(config.quality_probes))
    assert variables["AUTHORING_OBLIGATION_COUNT"] == str(len(config.authoring_obligations))
    assert int(variables["CONFIGURED_FIELD_EXPLICIT_COUNT"]) > 0
    assert int(variables["CONFIGURED_FIELD_DEFAULTED_COUNT"]) > 0
    assert variables["CONFIGURED_FIELD_VISUALIZED_COUNT"] == "7"
    assert int(variables["CONFIGURED_FIELD_SECTION_LEVEL_COUNT"]) > 0
    assert int(variables["CONFIGURED_FIELD_LEXICON_LEVEL_COUNT"]) > 0
    assert int(variables["CONFIGURED_FIELD_SLOT_LEVEL_COUNT"]) > 0


def test_all_manuscript_tokens_are_generated() -> None:
    variables = generate_variables(PROJECT_ROOT)
    found: set[str] = set()
    for path in (PROJECT_ROOT / "manuscript").glob("*.md"):
        if path.name in DOC_ONLY:
            continue
        found.update(TOKEN_RE.findall(path.read_text(encoding="utf-8")))

    assert found
    assert found <= set(variables), sorted(found - set(variables))


def test_save_variables_round_trip(tmp_path: Path) -> None:
    variables = generate_variables(PROJECT_ROOT)
    output = save_variables(variables, tmp_path / "vars.json")

    loaded = json.loads(output.read_text(encoding="utf-8"))

    assert loaded["PROJECT_TITLE"].startswith("Template Madlib")
    assert loaded["CONFIG_HASH"] == variables["CONFIG_HASH"]


def test_source_date_epoch_controls_timestamp() -> None:
    assert _build_timestamp("0") == "1970-01-01T00:00:00Z"


def test_missing_source_date_epoch_is_explicit_and_deterministic() -> None:
    assert _build_timestamp("") == "not-recorded (set SOURCE_DATE_EPOCH)"


def test_z_generate_script_resolves_output_manuscript_without_touching_tracked_outputs(tmp_path: Path) -> None:
    isolated_project = tmp_path / "template_madlib"
    for directory in ("manuscript", "scripts", "src"):
        shutil.copytree(PROJECT_ROOT / directory, isolated_project / directory)
    script = isolated_project / "scripts" / "z_generate_manuscript_variables.py"
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(PROJECT_ROOT.parents[2]), environment.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    environment["SOURCE_DATE_EPOCH"] = "0"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=isolated_project,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
        env=environment,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    output_dir = isolated_project / "output" / "manuscript"
    unresolved = [path for path in output_dir.glob("*.md") if TOKEN_RE.search(path.read_text(encoding="utf-8"))]
    assert unresolved == []
