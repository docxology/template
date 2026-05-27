"""Interval and paired-comparison diagnostics for the ML task."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np

from .diagnostics_records import _candidate_predictions, _evaluated_candidates
from .ml_task import CandidateResult, MLTaskResult, load_mnist_arrays, load_mnist_task_config


def candidate_accuracy_intervals(result: MLTaskResult) -> dict[str, object]:
    """Return Wilson intervals for baseline and evaluated candidate accuracies."""
    rows = [
        _candidate_interval_row(
            identifier=result.baseline.identifier,
            model_type=result.baseline.model_type,
            status="baseline",
            matrix=np.asarray(result.baseline.confusion_matrix, dtype=float),
        )
    ]
    rows.extend(
        _candidate_interval_row(
            identifier=candidate.identifier,
            model_type=candidate.model_type,
            status=candidate.status,
            matrix=np.asarray(candidate.confusion_matrix, dtype=float),
        )
        for candidate in _evaluated_candidates(result)
    )
    return {
        "schema": "template-autoresearch-candidate-intervals-v1",
        "method": "Wilson 95% binomial interval",
        "metric": result.task_config.metric_name,
        "accepted_candidate_id": result.accepted_candidate_id,
        "baseline_id": result.baseline.identifier,
        "rows": rows,
        "claim_boundary": "Intervals summarize binomial uncertainty on the fixed local test split.",
    }


def bootstrap_intervals(project_root: Path, result: MLTaskResult, *, resamples: int | None = None) -> dict[str, object]:
    """Return deterministic percentile bootstrap intervals for accepted-candidate metrics."""
    config = load_mnist_task_config(project_root, result.task_config.source_path)
    _x_train, _y_train, _x_test, y_test = load_mnist_arrays(project_root, config)
    predictions = _candidate_predictions(result.accepted_candidate, expected_rows=y_test.size)
    resolved_resamples = resamples or config.diagnostics.bootstrap_resamples
    seed = result.task_config.seed + config.diagnostics.bootstrap_seed_offset
    rng = np.random.default_rng(seed)
    accuracy_values: list[float] = []
    macro_f1_values: list[float] = []
    for _ in range(resolved_resamples):
        indices = rng.integers(0, y_test.size, size=y_test.size)
        sampled_true = y_test[indices]
        sampled_pred = predictions[indices]
        accuracy_values.append(float(np.mean(sampled_true == sampled_pred)))
        macro_f1_values.append(_macro_f1(sampled_true, sampled_pred))
    macro_f1 = _macro_f1(y_test, predictions)
    return {
        "schema": "template-autoresearch-bootstrap-intervals-v1",
        "accepted_candidate_id": result.accepted_candidate_id,
        "resamples": resolved_resamples,
        "seed": seed,
        "method": "deterministic percentile bootstrap",
        "intervals": [
            _interval_row("accuracy", result.best_accuracy, accuracy_values),
            _interval_row("macro_f1", macro_f1, macro_f1_values),
        ],
        "claim_boundary": "Intervals describe sampling variability on the fixed local test split.",
    }


def candidate_rank_stability(
    project_root: Path,
    result: MLTaskResult,
    *,
    resamples: int | None = None,
) -> dict[str, object]:
    """Return deterministic bootstrap rank-stability diagnostics for evaluated candidates."""
    config = load_mnist_task_config(project_root, result.task_config.source_path)
    _x_train, _y_train, _x_test, y_test = load_mnist_arrays(project_root, config)
    candidates = _evaluated_candidates(result)
    resolved_resamples = resamples or config.diagnostics.bootstrap_resamples
    seed = result.task_config.seed + config.diagnostics.bootstrap_seed_offset + 97
    rng = np.random.default_rng(seed)
    predictions_by_id = {
        candidate.identifier: _candidate_predictions(candidate, expected_rows=y_test.size) for candidate in candidates
    }
    observed = _rank_candidate_ids(candidates, y_test, predictions_by_id, np.arange(y_test.size))
    runner_up_id = next((candidate_id for candidate_id in observed if candidate_id != result.accepted_candidate_id), "")
    top_counts = {candidate.identifier: 0 for candidate in candidates}
    rank_sums = {candidate.identifier: 0.0 for candidate in candidates}
    pairwise_wins = {
        (candidate.identifier, opponent.identifier): 0
        for candidate in candidates
        for opponent in candidates
        if candidate.identifier != opponent.identifier
    }
    delta_values: list[float] = []
    for _ in range(resolved_resamples):
        indices = rng.integers(0, y_test.size, size=y_test.size)
        ranked_ids = _rank_candidate_ids(candidates, y_test, predictions_by_id, indices)
        top_counts[ranked_ids[0]] += 1
        rank_by_id = {candidate_id: rank for rank, candidate_id in enumerate(ranked_ids, start=1)}
        for candidate_id in ranked_ids:
            rank_sums[candidate_id] += rank_by_id[candidate_id]
        for candidate_id, opponent_id in pairwise_wins:
            if rank_by_id[candidate_id] < rank_by_id[opponent_id]:
                pairwise_wins[(candidate_id, opponent_id)] += 1
        if runner_up_id:
            accepted_accuracy = _sampled_accuracy(predictions_by_id[result.accepted_candidate_id], y_test, indices)
            runner_up_accuracy = _sampled_accuracy(predictions_by_id[runner_up_id], y_test, indices)
            delta_values.append(accepted_accuracy - runner_up_accuracy)
    observed_delta = (
        _sampled_accuracy(predictions_by_id[result.accepted_candidate_id], y_test, np.arange(y_test.size))
        - _sampled_accuracy(predictions_by_id[runner_up_id], y_test, np.arange(y_test.size))
        if runner_up_id
        else 0.0
    )
    delta_interval = _interval_row("accuracy_delta_vs_runner_up", observed_delta, delta_values or [0.0])
    delta_interval["observed_delta"] = delta_interval["observed"]
    return {
        "schema": "template-autoresearch-candidate-rank-stability-v1",
        "accepted_candidate_id": result.accepted_candidate_id,
        "runner_up_id": runner_up_id,
        "resamples": resolved_resamples,
        "seed": seed,
        "method": "deterministic paired bootstrap over the fixed local test split",
        "accepted_top_rank_frequency": round(top_counts.get(result.accepted_candidate_id, 0) / resolved_resamples, 6),
        "rank_frequencies": [
            {
                "candidate_id": candidate.identifier,
                "observed_rank": observed.index(candidate.identifier) + 1,
                "rank_1_frequency": round(top_counts[candidate.identifier] / resolved_resamples, 6),
                "mean_rank": round(rank_sums[candidate.identifier] / resolved_resamples, 6),
                "test_accuracy": round(float(candidate.test_accuracy or 0.0), 6),
            }
            for candidate in candidates
        ],
        "pairwise_win_rates": [
            {
                "candidate_id": candidate_id,
                "opponent_id": opponent_id,
                "win_rate": round(win_count / resolved_resamples, 6),
                "win_count": win_count,
            }
            for (candidate_id, opponent_id), win_count in sorted(pairwise_wins.items())
        ],
        "accepted_vs_runner_up_delta_interval": delta_interval,
        "claim_boundary": "Rank stability is a local resampling diagnostic, not external model-selection proof.",
    }


def paired_comparison_report(project_root: Path, result: MLTaskResult) -> dict[str, object]:
    """Return matched accepted-vs-baseline correctness diagnostics."""
    config = load_mnist_task_config(project_root, result.task_config.source_path)
    _x_train, _y_train, _x_test, y_test = load_mnist_arrays(project_root, config)
    accepted_predictions = _candidate_predictions(result.accepted_candidate, expected_rows=y_test.size)
    baseline_predictions = np.asarray(result.baseline.test_predictions, dtype=np.int64)
    if baseline_predictions.shape != (y_test.size,):
        raise ValueError("baseline predictions do not match test-set size")
    accepted_correct = accepted_predictions == y_test
    baseline_correct = baseline_predictions == y_test
    accepted_only = int(np.sum(accepted_correct & ~baseline_correct))
    baseline_only = int(np.sum(~accepted_correct & baseline_correct))
    both_correct = int(np.sum(accepted_correct & baseline_correct))
    both_wrong = int(np.sum(~accepted_correct & ~baseline_correct))
    return {
        "schema": "template-autoresearch-paired-comparison-v1",
        "accepted_candidate_id": result.accepted_candidate_id,
        "baseline_id": result.baseline.identifier,
        "test_size": int(y_test.size),
        "both_correct": both_correct,
        "accepted_only_correct": accepted_only,
        "baseline_only_correct": baseline_only,
        "both_wrong": both_wrong,
        "discordant_count": accepted_only + baseline_only,
        "exact_mcnemar_p": _exact_mcnemar_p(accepted_only, baseline_only),
        "net_accuracy_gain": round((accepted_only - baseline_only) / y_test.size, 6),
        "claim_boundary": "Matched comparison over the fixed local test split; not an external benchmark claim.",
    }


def _candidate_interval_row(
    *,
    identifier: str,
    model_type: str,
    status: str,
    matrix: np.ndarray,
) -> dict[str, int | float | str]:
    successes = int(np.trace(matrix))
    total = int(matrix.sum())
    ci_low, ci_high = _wilson_interval(successes, total)
    accuracy = successes / total if total else 0.0
    return {
        "candidate_id": identifier,
        "model_type": model_type,
        "status": status,
        "successes": successes,
        "test_size": total,
        "accuracy": round(float(accuracy), 6),
        "ci_low": ci_low,
        "ci_high": ci_high,
    }


def _wilson_interval(successes: int, total: int, *, z_score: float = 1.96) -> tuple[float, float]:
    if total <= 0:
        return 0.0, 0.0
    p_hat = successes / total
    denominator = 1.0 + (z_score * z_score) / total
    center = p_hat + (z_score * z_score) / (2.0 * total)
    margin = z_score * math.sqrt((p_hat * (1.0 - p_hat) + (z_score * z_score) / (4.0 * total)) / total)
    return round((center - margin) / denominator, 6), round((center + margin) / denominator, 6)


def _macro_f1(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    values: list[float] = []
    for label in range(10):
        true_positive = int(np.sum((y_true == label) & (y_pred == label)))
        predicted = int(np.sum(y_pred == label))
        support = int(np.sum(y_true == label))
        precision = true_positive / predicted if predicted else 0.0
        recall = true_positive / support if support else 0.0
        values.append((2.0 * precision * recall / (precision + recall)) if (precision + recall) else 0.0)
    return float(np.mean(values))


def _rank_candidate_ids(
    candidates: tuple[CandidateResult, ...],
    y_true: np.ndarray,
    predictions_by_id: dict[str, np.ndarray],
    indices: np.ndarray,
) -> list[str]:
    scored = []
    sampled_true = y_true[indices]
    for candidate in candidates:
        sampled_accuracy = _sampled_accuracy(predictions_by_id[candidate.identifier], y_true, indices)
        scored.append(
            (
                -sampled_accuracy,
                candidate.parameter_count,
                candidate.identifier,
                candidate.identifier,
                sampled_true.size,
            )
        )
    return [row[3] for row in sorted(scored)]


def _sampled_accuracy(predictions: np.ndarray, y_true: np.ndarray, indices: np.ndarray) -> float:
    if indices.size == 0:
        return 0.0
    return float(np.mean(predictions[indices] == y_true[indices]))


def _interval_row(metric: str, observed: float, values: list[float]) -> dict[str, str | float | int]:
    array = np.asarray(values, dtype=float)
    return {
        "metric": metric,
        "observed": round(float(observed), 6),
        "ci_low": round(float(np.quantile(array, 0.025)), 6),
        "ci_high": round(float(np.quantile(array, 0.975)), 6),
        "resample_mean": round(float(np.mean(array)), 6),
    }


def _interval_summary(bootstrap: dict[str, object], metric: str) -> dict[str, float | str]:
    for row in _mapping_list(bootstrap.get("intervals")):
        if row.get("metric") == metric:
            return {
                "metric": metric,
                "ci_low": _float_value(row.get("ci_low")),
                "ci_high": _float_value(row.get("ci_high")),
                "observed": _float_value(row.get("observed")),
            }
    return {"metric": metric, "ci_low": 0.0, "ci_high": 0.0, "observed": 0.0}


def _exact_mcnemar_p(accepted_only: int, baseline_only: int) -> float:
    discordant = accepted_only + baseline_only
    if discordant == 0:
        return 1.0
    smaller = min(accepted_only, baseline_only)
    tail = sum(math.comb(discordant, index) for index in range(smaller + 1)) / (2**discordant)
    return float(round(min(1.0, 2.0 * tail), 6))


def _float_value(value: object) -> float:
    return float(value) if isinstance(value, int | float | str) else 0.0


def _mapping_list(value: object) -> list[dict[str, Any]]:
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


__all__ = [
    "candidate_accuracy_intervals",
    "bootstrap_intervals",
    "candidate_rank_stability",
    "paired_comparison_report",
    "_candidate_interval_row",
    "_wilson_interval",
    "_macro_f1",
    "_rank_candidate_ids",
    "_sampled_accuracy",
    "_interval_row",
    "_interval_summary",
    "_exact_mcnemar_p",
    "_float_value",
    "_mapping_list",
]
