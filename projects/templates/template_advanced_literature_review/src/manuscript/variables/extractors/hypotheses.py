"""Hypothesis scores, assertions, and config-driven hypothesis tables."""

from __future__ import annotations

from manuscript.variables._logging import logger
from manuscript.variables.context import ExtractContext
from manuscript.variables.formatters import latex_number


def extract_hypotheses(ctx: ExtractContext) -> dict[str, str]:
    """Process extract hypotheses."""
    variables: dict[str, str] = {}
    assertion = ctx.load_json("assertion_summary.json")
    if assertion:
        total_assertions = assertion.get("total_assertions", 0)
        variables["TOTAL_ASSERTIONS"] = latex_number(total_assertions)
        variables["TOTAL_ASSERTIONS_RAW"] = str(total_assertions)
        hyp_counts = assertion.get("per_hypothesis", assertion.get("hypothesis_counts", {}))
        for hid, hdata in hyp_counts.items():
            if isinstance(hdata, dict):
                sup = hdata.get("supports", 0)
                con = hdata.get("contradicts", 0)
                neu = hdata.get("neutral", 0)
                variables[f"{hid}_SUPPORT"] = str(sup)
                variables[f"{hid}_CONTRADICT"] = str(con)
                variables[f"{hid}_NEUTRAL"] = str(neu)
                variables[f"{hid}_TOTAL"] = str(sup + con + neu)
        type_counts = assertion.get("type_counts", {})
        total_sup = type_counts.get("supports", 0)
        total_con = type_counts.get("contradicts", 0)
        total_sc = total_sup + total_con
        if total_sc > 0:
            variables["ASSERTION_SUPPORT_PCT"] = f"{(total_sup / total_sc * 100):.1f}"
            variables["ASSERTION_CONTRADICT_PCT"] = f"{(total_con / total_sc * 100):.1f}"
        else:
            variables["ASSERTION_SUPPORT_PCT"] = "0.0"
            variables["ASSERTION_CONTRADICT_PCT"] = "0.0"
    else:
        logger.info("assertion_summary.json not found; assertion variables skipped")
        variables["TOTAL_ASSERTIONS"] = "pending"
        variables["TOTAL_ASSERTIONS_RAW"] = "0"

    scores = ctx.load_json("hypothesis_scores.json")
    if scores:
        for hid, score_val in scores.items():
            if isinstance(score_val, (int, float)):
                variables[f"{hid}_SCORE"] = f"{score_val:+.2f}"
            elif isinstance(score_val, dict):
                variables[f"{hid}_SCORE"] = f"{score_val.get('score', 0):+.2f}"
    else:
        logger.info("hypothesis_scores.json not found; score variables skipped")

    hyp_defs = ctx.cfg.get("project_config", {}).get("hypothesis_definitions", {}) or {}
    variables["N_HYPOTHESES"] = str(len(hyp_defs))
    score_lookup: dict[str, float] = {}
    if scores:
        for hid, sv in scores.items():
            if isinstance(sv, (int, float)):
                score_lookup[hid] = float(sv)
            elif isinstance(sv, dict) and isinstance(sv.get("score"), (int, float)):
                score_lookup[hid] = float(sv["score"])
    try:
        from knowledge_graph.hypothesis import config_key_to_hypothesis_id
    except ImportError:  # pragma: no cover

        def config_key_to_hypothesis_id(key: str, name: str = "") -> str:
            """Process config key to hypothesis id."""
            return key

    def score_for(hid: str, hname: str) -> str:
        """Process score for."""
        mapped = config_key_to_hypothesis_id(hid, hname)
        for key in (hid, mapped, hname, hname.upper().replace(" ", "_")):
            if key in score_lookup:
                return f"{score_lookup[key]:+.2f}"
        return "pending"

    hyp_list_parts: list[str] = []
    hyp_table = [
        "| ID | Hypothesis | Scope | Evidence score |",
        "| --- | --- | --- | --- |",
    ]
    for hid, hdef in hyp_defs.items():
        hname = str((hdef or {}).get("name", hid)) if isinstance(hdef, dict) else str(hdef)
        hscope = str((hdef or {}).get("scope", "")) if isinstance(hdef, dict) else ""
        hyp_list_parts.append(f"{hid} {hname}")
        hyp_table.append(f"| {hid} | {hname} | {hscope} | {score_for(hid, hname)} |")
    variables["HYPOTHESIS_LIST"] = "; ".join(hyp_list_parts)
    variables["HYPOTHESIS_TABLE"] = "\n".join(hyp_table)
    return variables
