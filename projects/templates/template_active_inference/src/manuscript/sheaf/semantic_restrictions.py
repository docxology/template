"""Low-level restriction helpers for semantic gluing certificates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gnn.parser import parse_gnn_file
from ontology.bindings import (
    load_section_ontology,
)

from manuscript.sheaf.semantic_maps import SEMANTIC_RESTRICTION_LANES


def _rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"malformed JSON artifact: {path}") from exc
    return data


def _configured_analysis_scripts(root: Path) -> list[str]:
    import yaml

    config_path = root / "manuscript" / "config.yaml"
    if not config_path.is_file():
        return []
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    analysis = data.get("analysis") or {}
    scripts = analysis.get("scripts") or []
    return [str(script) for script in scripts]


def _claim_records(root: Path) -> list[dict[str, Any]]:
    import yaml

    path = root / "data" / "claim_ledger.yaml"
    if not path.is_file():
        return []
    ledger = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    records: list[dict[str, Any]] = []
    for claim in ledger.get("claims") or []:
        records.append(
            {
                "id": claim.get("id"),
                "statement": claim.get("statement"),
                "path": claim.get("path"),
                "section": claim.get("section"),
                "tracks": claim.get("tracks") or [],
                "evidence": claim.get("evidence") or {},
            }
        )
    return records


def _claims_by_path(root: Path) -> dict[str, list[str]]:
    claims: dict[str, list[str]] = {}
    for claim in _claim_records(root):
        path = claim.get("path")
        claim_id = claim.get("id")
        if path and claim_id:
            claims.setdefault(str(path), []).append(str(claim_id))
    return claims


def _animation_frame_count(root: Path) -> int:
    gif_path = root / "output" / "figures" / "si_belief_trajectory.gif"
    if not gif_path.is_file():
        return 0
    try:
        from PIL import Image, ImageSequence

        with Image.open(gif_path) as image:
            return sum(1 for _ in ImageSequence.Iterator(image))
    except (ImportError, OSError, ValueError, EOFError):
        return 0


def _lean_status(root: Path) -> dict[str, Any]:
    try:
        from visualizations.lean_boundary import load_lean_boundary_rows

        rows = load_lean_boundary_rows(root)
    except (ImportError, OSError, ValueError):
        return {"module_count": 0, "proved_count": 0, "all_proved": False, "names": []}
    return {
        "module_count": len(rows),
        "proved_count": sum(1 for row in rows if row.status == "proved"),
        "all_proved": bool(rows) and all(row.status == "proved" for row in rows),
        "names": sorted(row.name for row in rows),
    }


def _policy_comparison_restrictions(root: Path) -> dict[str, Any]:
    path = root / "output" / "data" / "si_policy_comparison.json"
    data = _load_json(path)
    runs = data.get("runs") or []
    return {
        "run_count": int((data.get("summary") or {}).get("run_count", len(runs)) or 0),
        "modes": sorted({str(row.get("mode")) for row in runs if row.get("mode")}),
        "horizons": sorted({int(row.get("horizon")) for row in runs if row.get("horizon") is not None}),
        "goal_reached_count": sum(1 for row in runs if row.get("goal_reached") is True),
        "complete_grid": (data.get("summary") or {}).get("complete_grid") is True,
        "all_efe_rows_explained": (data.get("summary") or {}).get("all_efe_rows_explained") is True,
    }


def _policy_posterior_restrictions(root: Path) -> dict[str, Any]:
    data = _load_json(root / "output" / "data" / "pymdp_policy_posterior_grid.json")
    return {
        "row_count": int(data.get("row_count", 0) or 0),
        "available_row_count": int(data.get("available_row_count", 0) or 0),
        "all_available_posteriors_normalized": data.get("all_available_posteriors_normalized") is True,
        "all_unavailable_rows_explained": data.get("all_unavailable_rows_explained") is True,
    }


def _runtime_diagnostics_restrictions(root: Path) -> dict[str, Any]:
    data = _load_json(root / "output" / "reports" / "pymdp_runtime_diagnostics.json")
    return {
        "ok": data.get("ok") is True,
        "phase_rows_ok": data.get("all_phase_rows_ok") is True,
        "construction_count": int(data.get("construction_count", 0) or 0),
        "known_warning_count": int(data.get("known_warning_count", 0) or 0),
        "unexpected_warning_count": int(data.get("unexpected_warning_count", 0) or 0),
    }


def _restriction_class(restriction: str) -> str:
    if "security" in restriction or "secret" in restriction:
        return "artifact_contract"
    if restriction.startswith(("blocked_", "scope_")) or "empirical" in restriction:
        return "scope_boundary"
    if any(token in restriction for token in ("proof", "theorem", "lean", "model_checking", "interop")):
        return "formal_witness"
    if any(token in restriction for token in ("provenance", "dependency", "release", "evidence", "gate")):
        return "artifact_contract"
    if any(token in restriction for token in ("visualization", "figure", "animation", "statistical")):
        return "rendered_artifact"
    return "semantic_restriction"


def _restriction_lane(restriction: str) -> str:
    if "security" in restriction or "secret" in restriction:
        return "release"
    if any(token in restriction for token in ("pymdp", "policy", "posterior", "graph_world", "efe")):
        return "pymdp"
    if any(token in restriction for token in ("proof", "theorem", "lean", "model_checking", "interop")):
        return "formal"
    if any(token in restriction for token in ("visualization", "figure", "animation", "statistical")):
        return "visualization"
    if any(
        token in restriction
        for token in (
            "analytical",
            "assumption",
            "sensitivity",
            "uncertainty",
            "benchmark",
            "state_space",
            "state_transition",
            "ablation",
        )
    ):
        return "analytical"
    if restriction.startswith(("blocked_", "scope_")) or "empirical" in restriction or "versioned" in restriction:
        return "scope"
    if any(
        token in restriction
        for token in ("artifact", "provenance", "dependency", "release", "evidence", "gate", "replay", "bundle")
    ):
        return "release"
    return "semantic"


def _restriction_lane_assignments(restrictions: dict[str, Any]) -> dict[str, str]:
    return {restriction: _restriction_lane(restriction) for restriction in sorted(restrictions)}


def _restriction_value_ok(restriction: str, value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if restriction in {
        "adversarial_known_bad_passed",
        "coverage_missing",
        "pymdp_runtime_unexpected_warning_count",
        "security_posture_high_risk_gap_count",
        "security_posture_secret_finding_count",
    }:
        return int(value or 0) == 0
    if restriction.endswith("_count") or restriction in {"claim_count", "section_count", "track_count"}:
        return int(value or 0) >= 0
    return bool(value)


def _restriction_lane_summaries(
    restrictions: dict[str, Any],
    lanes: dict[str, str],
) -> dict[str, dict[str, Any]]:
    summaries: dict[str, dict[str, Any]] = {}
    for lane in SEMANTIC_RESTRICTION_LANES:
        keys = sorted(key for key, assigned_lane in lanes.items() if assigned_lane == lane)
        summaries[lane] = {
            "restrictions": keys,
            "restriction_count": len(keys),
            "ok_count": sum(1 for key in keys if _restriction_value_ok(key, restrictions.get(key))),
            "all_ok": bool(keys) and all(_restriction_value_ok(key, restrictions.get(key)) for key in keys),
        }
    return summaries


def _proof_obligation_rows(restrictions: dict[str, bool]) -> list[dict[str, Any]]:
    return [
        {
            "restriction": restriction,
            "class": _restriction_class(restriction),
            "obligation": f"prove_{restriction}",
            "ok": bool(ok),
        }
        for restriction, ok in sorted(restrictions.items())
    ]


def _graph_world_restrictions(root: Path) -> dict[str, Any]:
    summary = _load_json(root / "output" / "data" / "si_graph_world_summary.json")
    trace = _load_json(root / "output" / "data" / "si_graph_world_trace.json")
    trace_steps = trace.get("steps") or []
    summary_steps = int(summary.get("steps", 0) or 0)
    return {
        "steps": summary_steps,
        "trace_steps": len(trace_steps),
        "steps_match": summary_steps == len(trace_steps) and summary_steps > 0,
        "goal_reached": summary.get("goal_reached") is True,
    }


def _pymdp_hash_restrictions(root: Path) -> dict[str, Any]:
    summary = _load_json(root / "output" / "data" / "si_tmaze_summary.json")
    stats = _load_json(root / "output" / "data" / "analysis_statistics.json")
    return {
        "mode_match": not summary or not stats or summary.get("mode") == stats.get("pymdp_mode"),
        "config_hash_match": not summary or not stats or summary.get("config_hash") == stats.get("pymdp_config_hash"),
    }


def _gnn_symbols(root: Path, rel_path: str) -> dict[str, str]:
    path = root / rel_path
    if not path.is_file():
        return {}
    return dict(parse_gnn_file(path).ontology)


def _section_ontology_symbols(root: Path, rel_path: str) -> dict[str, str]:
    symbols = load_section_ontology(root / rel_path)
    return {str(key): str(value) for key, value in symbols.items()}


def _expected_symbol_gaps(
    *,
    label: str,
    gnn_symbols: dict[str, str],
    section_symbols: dict[str, str],
    symbol_map: dict[str, str],
    expected_terms: dict[str, str],
) -> list[str]:
    gaps: list[str] = []
    for _, variable in symbol_map.items():
        expected = expected_terms.get(variable)
        if expected is None:
            continue
        gnn_term = gnn_symbols.get(variable)
        section_term = section_symbols.get(variable)
        if gnn_term != expected:
            gaps.append(f"{label}: GNN variable {variable!r} annotated {gnn_term!r}, expected {expected!r}")
        if section_term != expected:
            gaps.append(
                f"{label}: section ontology variable {variable!r} annotated {section_term!r}, expected {expected!r}"
            )
    return gaps
