"""Shared formatters and JSON helpers for manuscript token hydration."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .json_coerce import mapping_list


def load_json_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"required JSON artifact is missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must contain a mapping: {path}")
    return payload


def load_optional_json_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return load_json_mapping(path)


def string_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def percent_value(value: object) -> str:
    if not isinstance(value, int | float):
        return "N/A"
    return f"{float(value) * 100:.1f}%"


def currency_value(value: object) -> str:
    if not isinstance(value, int | float):
        return "N/A"
    return f"{float(value):.2f}"


def decimal_value(value: object) -> str:
    if not isinstance(value, int | float):
        return "N/A"
    return f"{float(value):.3f}"


def accuracy_interval(classification: dict[str, Any]) -> str:
    low = classification.get("accuracy_ci_low")
    high = classification.get("accuracy_ci_high")
    if not isinstance(low, int | float) or not isinstance(high, int | float):
        return "N/A"
    return f"{percent_value(low)} to {percent_value(high)}"


def top_confusion_pair_label(classification: dict[str, Any]) -> str:
    pairs = mapping_list(classification.get("top_confusion_pairs"))
    if not pairs:
        return "none"
    first = pairs[0]
    return (
        f"{string_value(first.get('true_label', 'N/A'))} -> "
        f"{string_value(first.get('predicted_label', 'N/A'))} "
        f"({string_value(first.get('count', 'N/A'))})"
    )


def bootstrap_interval(bootstrap: dict[str, Any], metric: str) -> str:
    for row in mapping_list(bootstrap.get("intervals")):
        if row.get("metric") == metric:
            return f"{percent_value(row.get('ci_low'))} to {percent_value(row.get('ci_high'))}"
    return "N/A"


def p_value(value: object) -> str:
    if not isinstance(value, int | float):
        return "N/A"
    return f"{float(value):.3f}"


def last_coverage_value(statistical: dict[str, Any], key: str) -> float | None:
    rows = mapping_list(statistical.get("coverage_curve"))
    if not rows:
        return None
    value = rows[-1].get(key)
    return float(value) if isinstance(value, int | float) else None


def dataset_short_name(dataset_name: str) -> str:
    return dataset_name.split(maxsplit=1)[0] if dataset_name and dataset_name != "N/A" else dataset_name


def image_shape(value: object) -> str:
    if isinstance(value, list | tuple) and len(value) == 2:
        return f"{value[0]} by {value[1]}"
    return "N/A"


def model_type_label(value: object) -> str:
    labels = {
        "mlp": "MLP",
        "nearest_centroid": "nearest-centroid",
        "softmax_regression": "softmax regression",
        "tiny_patch_transformer": "tiny patch-attention",
    }
    return labels.get(string_value(value), string_value(value).replace("_", " "))


def candidate_display_label(value: object) -> str:
    text = string_value(value)
    if text == "nearest_centroid_baseline":
        return "baseline"
    return text.removeprefix("exp-").replace("-", " ")


def metric_label(value: object) -> str:
    labels = {
        "accuracy": "accuracy",
        "macro_f1": "macro F1",
    }
    return labels.get(string_value(value), string_value(value).replace("_", " "))


def status_counts(candidates: list[dict[str, Any]]) -> Counter[str]:
    return Counter(string_value(candidate.get("status", "unknown")) for candidate in candidates)


def status_summary(candidates: list[dict[str, Any]]) -> str:
    counts = status_counts(candidates)
    return ", ".join(f"{status}: {count}" for status, count in sorted(counts.items()))


def model_family_labels(baseline: dict[str, Any], candidates: list[dict[str, Any]]) -> str:
    model_types = {model_type_label(baseline.get("model_type", "N/A"))}
    model_types.update(model_type_label(candidate.get("model_type", "N/A")) for candidate in candidates)
    return ", ".join(sorted(model_types))


def first_model_candidate(candidates: list[dict[str, Any]], model_type: str) -> dict[str, Any]:
    for candidate in candidates:
        if candidate.get("model_type") == model_type:
            return candidate
    return {}


def benchmark_task_ids(config: dict[str, Any]) -> str:
    return ", ".join(string_value(row.get("id", "N/A")) for row in mapping_list(config.get("benchmark_tasks")))


def artifact_role(path: str) -> str:
    if path.endswith(".png"):
        return "Generated figure"
    if "manuscript" in path:
        return "Manuscript hydration"
    if "benchmark" in path:
        return "Benchmark grading"
    if "review" in path:
        return "Review packet"
    if "security" in path or "threat_model" in path or "attestation" in path or "inventory" in path:
        return "Security evidence"
    if "ledger" in path:
        return "Run or candidate ledger"
    if "readiness" in path:
        return "Readiness validation"
    if "evidence" in path:
        return "Evidence registry"
    return "Loop artifact"


def artifact_markdown_link(path: str) -> str:
    label = Path(path).name if path not in {"", "N/A"} else "N/A"
    if path.startswith("output/"):
        target = "../" + path.removeprefix("output/")
    elif path.startswith("data/"):
        target = "../../" + path
    else:
        target = path
    return f"[{label}]({target})"


def short_scope(value: str, *, limit: int = 92) -> str:
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def per_class_count(class_balance: dict[str, Any], split: str) -> str:
    counts = [int(row.get("count", 0)) for row in mapping_list(class_balance.get("rows")) if row.get("split") == split]
    if not counts:
        return "N/A"
    unique = sorted(set(counts))
    return str(unique[0]) if len(unique) == 1 else ", ".join(str(value) for value in unique)


def escape_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")
