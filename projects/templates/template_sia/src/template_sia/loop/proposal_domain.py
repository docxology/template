"""Finite numeric mutation and independent scoring for the mini-classify task."""

from __future__ import annotations

import ast
import csv
import io
import math
from pathlib import Path
from typing import Any


class LiveCapabilityBlocked(RuntimeError):
    """A required Docker, pinned-image, or local-model capability is unavailable."""


class LiveProposalFailed(RuntimeError):
    """A required live proposal, execution, or evidence contract failed."""


def validated_threshold(value: Any) -> float:
    """Reject booleans, nonnumeric values, infinities, and out-of-domain values."""
    if type(value) not in {int, float} or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("threshold must be a finite numeric value in [0, 1]")
    return float(value)


def threshold_assignment(source: str) -> ast.Constant:
    """Locate the sole literal THRESHOLD assignment in the fixed scaffold."""
    assignments = [
        node
        for node in ast.parse(source).body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "THRESHOLD" for target in node.targets)
    ]
    if len(assignments) != 1 or not isinstance(assignments[0].value, ast.Constant):
        raise ValueError("scaffold must contain one literal THRESHOLD assignment")
    value = assignments[0].value
    validated_threshold(value.value)
    return value


def mutate_threshold(source: str, threshold: float) -> str:
    """Change one numeric literal; model responses can never supply executable code."""
    value = validated_threshold(threshold)
    assignment = threshold_assignment(source)
    lines = source.splitlines(keepends=True)
    if assignment.end_lineno != assignment.lineno:
        raise ValueError("THRESHOLD literal must occupy one source line")
    line = lines[assignment.lineno - 1]
    lines[assignment.lineno - 1] = line[: assignment.col_offset] + repr(value) + line[assignment.end_col_offset :]
    return "".join(lines)


def read_dataset(path: Path) -> tuple[dict[str, str], ...]:
    """Validate unique labelled synthetic cases before any selection or prompt."""
    return read_dataset_bytes(path.read_bytes())


def read_dataset_bytes(source: bytes) -> tuple[dict[str, str], ...]:
    """Parse exactly the frozen bytes whose digest is recorded by the controller."""
    rows = tuple(dict(row) for row in csv.DictReader(io.StringIO(source.decode("utf-8"), newline="")))
    if not rows or len({row.get("id") for row in rows}) != len(rows):
        raise ValueError("dataset requires nonempty cases with unique ids")
    for row in rows:
        if not row.get("id") or row.get("label") not in {"positive", "negative"}:
            raise ValueError("dataset requires ids and binary labels")
        validated_threshold(float(row["feature_0"]))
    return rows


def score_predictions(rows: tuple[dict[str, str], ...], predictions: Path) -> float:
    """Require exact prediction membership; missing cases never inflate accuracy."""
    with predictions.open(newline="", encoding="utf-8") as handle:
        predicted_rows = tuple(csv.DictReader(handle))
    if len(predicted_rows) != len(rows) or len({row.get("id") for row in predicted_rows}) != len(rows):
        raise LiveProposalFailed("predictions must contain every case exactly once")
    predicted = {row.get("id"): row.get("label") for row in predicted_rows}
    if set(predicted) != {row["id"] for row in rows}:
        raise LiveProposalFailed("prediction ids differ from the evaluation dataset")
    if any(label not in {"positive", "negative"} for label in predicted.values()):
        raise LiveProposalFailed("predictions contain an unsupported label")
    return float(sum(predicted[row["id"]] == row["label"] for row in rows) / len(rows))


def public_prompt(rows: tuple[dict[str, str], ...], threshold: float, accuracy: float) -> str:
    """Use only the fixed public selection dataset and public score."""
    import json

    return (
        "Propose a different finite THRESHOLD in [0,1] for this fixed classifier. "
        "Labels are positive when feature_0 >= THRESHOLD. Return JSON with exactly "
        "threshold (number) and rationale (short string); never return code or paths. "
        "The held-out evaluation is unavailable to you. A changed parameter may show no improvement.\n"
        + json.dumps({"public_cases": rows, "current_threshold": threshold, "public_accuracy": accuracy})
    )
