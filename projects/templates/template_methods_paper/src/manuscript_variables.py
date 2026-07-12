"""Manuscript variable generation for the template_methods_paper exemplar.

Reads:
- ``manuscript/config.yaml``                       — paper metadata
- ``output/data/compiled_plans.json``               — per-example-method compiled plan summaries
- ``output/reports/gate_report.json``                — validation-gate pass counts
- ``output/reports/trust_chain_report.json``         — demo provenance-chain verification result

Returns a flat ``dict[str, str]`` of UPPERCASE_KEY -> value for ``{{TOKEN}}``
substitution via
:func:`infrastructure.rendering.manuscript_injection.write_resolved_manuscript_tree`.

Domain ``src/`` (this file included) stays standalone — no ``infrastructure``
import — per the same convention ``template_code_project`` documents; the
project's one sanctioned exception is ``src/methods_dsl/_logging.py``,
declared in ``manuscript/layer_contract.yaml``.

Called exclusively by ``scripts/z_generate_manuscript_variables.py``
(thin orchestrator).
"""

from __future__ import annotations

import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .methods_dsl import StepKind, Target, all_example_methods, compile_method, known_units

CONFIG_HASH_LENGTH = 16


def _build_timestamp() -> str:
    """Build timestamp, honoring ``SOURCE_DATE_EPOCH`` for reproducible builds."""
    import os

    epoch = os.environ.get("SOURCE_DATE_EPOCH", "").strip()
    if epoch.isdigit():
        return datetime.fromtimestamp(int(epoch), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# I/O helpers — thin readers, no business logic
# ---------------------------------------------------------------------------


def _load_config(project_root: Path) -> dict[str, Any]:
    config_path = project_root / "manuscript" / "config.yaml"
    if not config_path.exists():
        return {}
    with config_path.open("r") as f:
        return yaml.safe_load(f) or {}


def _load_json_list(project_root: Path, name: str) -> list[dict[str, Any]]:
    json_path = project_root / "output" / "data" / name
    if not json_path.exists():
        return []
    with json_path.open("r") as f:
        loaded: list[dict[str, Any]] = json.load(f)
        return loaded


def _load_json_report(project_root: Path, name: str) -> dict[str, Any]:
    report_path = project_root / "output" / "reports" / name
    if not report_path.exists():
        return {}
    with report_path.open("r") as f:
        result: dict[str, Any] = json.load(f)
        return result


def _compute_config_hash(project_root: Path) -> str:
    config_path = project_root / "manuscript" / "config.yaml"
    if not config_path.exists():
        return "N/A"
    return hashlib.sha256(config_path.read_bytes()).hexdigest()[:CONFIG_HASH_LENGTH]


def _count_output_artifacts(project_root: Path) -> dict[str, int]:
    _SUFFIXES: dict[str, set[str]] = {
        "figures": {".png", ".pdf", ".svg"},
        "data": {".csv", ".json"},
        "reports": {".json", ".md"},
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


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_variables(project_root: Path, *, require_analysis_outputs: bool = False) -> dict[str, str]:
    """Generate all manuscript variables from config and analysis outputs.

    Args:
        project_root: Root directory of the methods-paper project (the
            directory containing ``manuscript/`` and ``output/``).
        require_analysis_outputs: When True, raise if
            ``output/data/compiled_plans.json`` is missing or empty.

    Returns:
        ``dict[str, str]`` with plain UPPERCASE_KEY keys (no surrounding
        braces), ready for
        :func:`infrastructure.rendering.manuscript_injection.write_resolved_manuscript_tree`.
    """
    config = _load_config(project_root)
    plans = _load_json_list(project_root, "compiled_plans.json")
    if require_analysis_outputs and not plans:
        json_path = project_root / "output" / "data" / "compiled_plans.json"
        raise FileNotFoundError(
            f"Analysis outputs required but missing or empty: {json_path}. "
            "Run projects/templates/template_methods_paper/scripts/methods_analysis.py first."
        )
    gate_report = _load_json_report(project_root, "gate_report.json")
    trust_report = _load_json_report(project_root, "trust_chain_report.json")
    artifact_counts = _count_output_artifacts(project_root)

    variables: dict[str, str] = {}

    # ---- Configuration-derived ----
    paper = config.get("paper", {})
    variables["CONFIG_VERSION"] = paper.get("version", "1.0")
    authors = config.get("authors", [])
    variables["CONFIG_FIRST_AUTHOR"] = authors[0].get("name", "Unknown") if authors else "Unknown"
    variables["CONFIG_KEYWORDS"] = ", ".join(config.get("keywords", []))

    # ---- DSL constants (always available — pure, no I/O) ----
    variables["DSL_UNIT_COUNT"] = str(len(known_units()))
    variables["DSL_STEP_KIND_COUNT"] = str(len(StepKind))
    variables["DSL_TARGET_COUNT"] = str(len(Target))
    variables["DSL_GATE_COUNT"] = "4"

    # ---- Live determinism check — the manuscript's central reproducibility claim ----
    examples = all_example_methods()
    variables["EXAMPLE_METHOD_COUNT"] = str(len(examples))
    determinism_ok = all(compile_method(m).plan_hash == compile_method(m).plan_hash for m in examples)
    variables["DETERMINISM_CHECK"] = "Yes" if determinism_ok else "No"

    # ---- Results-derived (from output/data/compiled_plans.json) ----
    by_name = {p["method_name"]: p for p in plans}
    pbs = by_name.get("PBSPreparation")
    if pbs:
        variables["PBS_STEP_COUNT"] = str(pbs["step_count"])
        variables["PBS_PLAN_HASH"] = str(pbs["plan_hash"])[:12]
        variables["PBS_TARGET"] = str(pbs["target"])
    else:
        variables["PBS_STEP_COUNT"] = "N/A"
        variables["PBS_PLAN_HASH"] = "N/A"
        variables["PBS_TARGET"] = "N/A"

    calibration = by_name.get("SensorCalibrationSweep")
    if calibration:
        variables["CALIBRATION_STEP_COUNT"] = str(calibration["step_count"])
        variables["CALIBRATION_PLAN_HASH"] = str(calibration["plan_hash"])[:12]
        variables["CALIBRATION_TARGET"] = str(calibration["target"])
    else:
        variables["CALIBRATION_STEP_COUNT"] = "N/A"
        variables["CALIBRATION_PLAN_HASH"] = "N/A"
        variables["CALIBRATION_TARGET"] = "N/A"

    # ---- Gate-report-derived ----
    variables["TOTAL_GATES_RUN"] = str(gate_report.get("total_gates_run", "N/A"))
    variables["TOTAL_GATES_PASSED"] = str(gate_report.get("total_gates_passed", "N/A"))

    # ---- Trust-chain-derived ----
    variables["TRUST_CHAIN_LENGTH"] = str(trust_report.get("chain_length", "N/A"))
    verified = trust_report.get("verified")
    variables["TRUST_CHAIN_VERIFIED"] = "Yes" if verified is True else ("No" if verified is False else "N/A")

    # ---- Artifact counts ----
    variables["ARTIFACT_FIGURES"] = str(artifact_counts.get("figures", 0))
    variables["ARTIFACT_DATA_FILES"] = str(artifact_counts.get("data", 0))
    variables["ARTIFACT_REPORTS"] = str(artifact_counts.get("reports", 0))
    variables["ARTIFACT_TOTAL"] = str(sum(artifact_counts.values()))

    # ---- Provenance ----
    variables["CONFIG_HASH"] = _compute_config_hash(project_root)
    variables["GENERATION_TIMESTAMP"] = _build_timestamp()
    variables["PYTHON_VERSION"] = platform.python_version()
    variables["PLATFORM"] = f"{platform.system()} {platform.machine()}"

    return variables


def save_variables(variables: dict[str, str], output_path: Path) -> Path:
    """Persist *variables* as JSON for downstream rendering and debugging."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(variables, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )
    return output_path
