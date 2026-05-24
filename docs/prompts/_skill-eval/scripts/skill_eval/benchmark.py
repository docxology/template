"""Benchmark aggregation for skill-eval harness runs."""

from __future__ import annotations


def aggregate_benchmark(results_summary: dict, evals: list, *, run_dir: str) -> dict:
    def mean_rate(rows: list) -> float:
        if not rows:
            return 0.0
        return sum(r["pass_rate"] for r in rows) / len(rows)

    pos_evals = [e for e in evals if not e.get("negative")]
    neg_evals = [e for e in evals if e.get("negative")]
    neg_names = {e.get("eval_name", f"eval-{e['id']}") for e in neg_evals}

    ws = results_summary["with_skill"]
    wo = results_summary["without_skill"]
    ws_pos = [r for r in ws if r["eval_name"] not in neg_names]
    wo_pos = [r for r in wo if r["eval_name"] not in neg_names]

    return {
        "skill_name": "template-workflows",
        "run_dir": run_dir,
        "configurations": [
            {
                "name": "with_skill",
                "mean_pass_rate": mean_rate(ws),
                "mean_pass_rate_positive_only": mean_rate(ws_pos),
                "evals": ws,
            },
            {
                "name": "without_skill",
                "mean_pass_rate": mean_rate(wo),
                "mean_pass_rate_positive_only": mean_rate(wo_pos),
                "evals": wo,
            },
        ],
        "summary": {
            "with_skill_mean_pass_rate": mean_rate(ws),
            "without_skill_mean_pass_rate": mean_rate(wo),
            "with_skill_positive_only_pass_rate": mean_rate(ws_pos),
            "without_skill_positive_only_pass_rate": mean_rate(wo_pos),
            "delta_pass_rate": mean_rate(ws) - mean_rate(wo),
            "delta_positive_only_pass_rate": mean_rate(ws_pos) - mean_rate(wo_pos),
            "positive_eval_count": len(pos_evals),
            "negative_eval_count": len(neg_evals),
        },
    }
