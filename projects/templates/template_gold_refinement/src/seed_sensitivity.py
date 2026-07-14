"""Deterministic seed-sensitivity study for the token-composition engine.

The study treats seeds as technical replicates of one executable pipeline.  It
describes how much the selected token plan changes across a declared seed
sample; it does not treat seeds as people, independent manuscripts, or
evidence of external writing quality.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from statistics import NormalDist
from collections.abc import Iterable, Mapping
from typing import Any

try:
    from .composition import generate_token_plan
    from .config import GoldRefinementConfig
except ImportError:  # pragma: no cover - flat-layout fallback
    from composition import generate_token_plan  # type: ignore[no-redef]
    from config import GoldRefinementConfig  # type: ignore[no-redef]


DEFAULT_SAMPLE_SIZE = 1024
DEFAULT_SEED_START = 0
DEFAULT_AGREEMENT_THRESHOLD = 0.25
DEFAULT_CONFIDENCE_LEVEL = 0.95
DEFAULT_PRECISION_TARGET = 0.05
DEFAULT_SAMPLE_SIZE_LADDER = (16, 32, 64, 128, 256, 512, 1024)
DEFAULT_BOOTSTRAP_REPLICATES = 2000
DEFAULT_SEED_SAMPLING_SCHEME = "contiguous_integer_seeds"
DEFAULT_PRECISION_ASSUMPTION = (
    "Conditional on exchangeable random-seed draws; the declared contiguous seed range is a sensitivity surface, "
    "not an empirical population."
)


@dataclass(frozen=True)
class SeedReplicate:
    """Compact per-seed record retained for audit and plotting."""

    seed: int
    token_agreement: float
    unique_token_values: int
    plan_digest: str


@dataclass(frozen=True)
class SeedSensitivityReport:
    """Descriptive seed-variation summary with explicit precision metadata."""

    schema: str
    sample_size: int
    seed_start: int
    seed_end: int
    canonical_seed: int
    token_count: int
    unique_plan_count: int
    canonical_matches: int
    mean_agreement: float
    sd_agreement: float
    agreement_interval: tuple[float, float]
    agreement_min: float
    agreement_max: float
    agreement_threshold: float
    high_agreement_count: int
    high_agreement_rate: float
    high_agreement_interval: tuple[float, float]
    inventory_total: int
    inventory_observed: int
    inventory_coverage: float
    mean_unique_token_values: float
    confidence_level: float
    precision_target: float
    hoeffding_radius: float
    meets_precision_target: bool
    minimum_sample_size_for_precision_target: int
    seed_sampling_scheme: str
    precision_assumption: str
    agreement_interval_method: str
    threshold_interval_method: str
    precision_method: str
    bootstrap_replicates: int
    bootstrap_seed: int
    bootstrap_mean_interval: tuple[float, float]
    sample_size_ladder: tuple[dict[str, float | int], ...]
    records: tuple[SeedReplicate, ...]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the report into a stable JSON-compatible payload."""
        payload = asdict(self)
        payload["agreement_interval"] = list(self.agreement_interval)
        payload["high_agreement_interval"] = list(self.high_agreement_interval)
        payload["bootstrap_mean_interval"] = list(self.bootstrap_mean_interval)
        payload["records"] = [asdict(record) for record in self.records]
        return payload


def _normal_interval(mean: float, sd: float, sample_size: int, z: float) -> tuple[float, float]:
    if sample_size < 1:
        return (0.0, 0.0)
    margin = z * sd / math.sqrt(sample_size)
    return (max(0.0, mean - margin), min(1.0, mean + margin))


def _wilson_interval(successes: int, sample_size: int, z: float) -> tuple[float, float]:
    """Return a score interval for a bounded thresholded rate."""
    if sample_size < 1:
        return (0.0, 0.0)
    p = successes / sample_size
    denominator = 1.0 + z * z / sample_size
    centre = (p + z * z / (2.0 * sample_size)) / denominator
    spread = z * math.sqrt(p * (1.0 - p) / sample_size + z * z / (4.0 * sample_size**2)) / denominator
    return (max(0.0, centre - spread), min(1.0, centre + spread))


def _hoeffding_radius(sample_size: int, confidence_level: float) -> float:
    alpha = 1.0 - confidence_level
    return math.sqrt(math.log(2.0 / alpha) / (2.0 * sample_size))


def _minimum_sample_size_for_target(confidence_level: float, precision_target: float) -> int:
    """Return the smallest integer n satisfying the declared Hoeffding target."""
    alpha = 1.0 - confidence_level
    return math.ceil(math.log(2.0 / alpha) / (2.0 * precision_target**2))


def _quantile(sorted_values: list[float], probability: float) -> float:
    """Compute a deterministic linearly interpolated empirical quantile."""
    if not sorted_values:
        return 0.0
    position = (len(sorted_values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    weight = position - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


def _bootstrap_mean_interval(
    values: list[float],
    confidence_level: float,
    replicates: int,
    seed: int,
) -> tuple[float, float]:
    """Return a deterministic percentile bootstrap interval for the seed-range mean."""
    rng = random.Random(seed ^ 0x9E3779B9)
    sample_size = len(values)
    means = [
        sum(values[rng.randrange(sample_size)] for _ in range(sample_size)) / sample_size for _ in range(replicates)
    ]
    means.sort()
    alpha = 1.0 - confidence_level
    return (_quantile(means, alpha / 2.0), _quantile(means, 1.0 - alpha / 2.0))


def _config_value(config: GoldRefinementConfig, key: str, default: Any) -> Any:
    value = config.seed_sensitivity.get(key, default)
    return default if value is None else value


def _validate_settings(
    sample_size: int,
    confidence_level: float,
    threshold: float,
    precision_target: float,
    bootstrap_replicates: int,
) -> None:
    if sample_size < 1:
        raise ValueError("seed sensitivity sample_size must be >= 1")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("seed sensitivity confidence_level must be in (0, 1)")
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("seed sensitivity agreement_threshold must be in [0, 1]")
    if not 0.0 < precision_target <= 1.0:
        raise ValueError("seed sensitivity precision_target must be in (0, 1]")
    if bootstrap_replicates < 1:
        raise ValueError("seed sensitivity bootstrap_replicates must be >= 1")


def _ladder(sample_size: int, configured: Iterable[Any]) -> tuple[int, ...]:
    values = {int(value) for value in configured if int(value) > 0 and int(value) <= sample_size}
    values.add(sample_size)
    return tuple(sorted(values))


def run_seed_sensitivity(config: GoldRefinementConfig) -> SeedSensitivityReport:
    """Evaluate token-plan agreement across the configured seed sample."""
    sample_size = int(_config_value(config, "sample_size", DEFAULT_SAMPLE_SIZE))
    seed_start = int(_config_value(config, "seed_start", DEFAULT_SEED_START))
    threshold = float(_config_value(config, "agreement_threshold", DEFAULT_AGREEMENT_THRESHOLD))
    confidence_level = float(_config_value(config, "confidence_level", DEFAULT_CONFIDENCE_LEVEL))
    precision_target = float(_config_value(config, "precision_target", DEFAULT_PRECISION_TARGET))
    bootstrap_replicates = int(_config_value(config, "bootstrap_replicates", DEFAULT_BOOTSTRAP_REPLICATES))
    seed_sampling_scheme = str(_config_value(config, "seed_sampling_scheme", DEFAULT_SEED_SAMPLING_SCHEME))
    precision_assumption = str(_config_value(config, "precision_assumption", DEFAULT_PRECISION_ASSUMPTION))
    _validate_settings(sample_size, confidence_level, threshold, precision_target, bootstrap_replicates)

    z = NormalDist().inv_cdf(0.5 + confidence_level / 2.0)
    canonical_plan = generate_token_plan(config)
    canonical_values = tuple(choice.value for choice in canonical_plan.choices)
    token_count = len(canonical_values)
    if token_count == 0:
        raise ValueError("seed sensitivity requires at least one configured token choice")

    used_categories = {slot.category for slot in config.slots}
    inventory_total = sum(len(config.lexicon.get(category, ())) for category in used_categories)
    observed: set[tuple[str, str]] = set()
    records: list[SeedReplicate] = []
    agreement_values: list[float] = []
    unique_digests: set[str] = set()
    ladder = _ladder(sample_size, _config_value(config, "sample_size_ladder", DEFAULT_SAMPLE_SIZE_LADDER))
    ladder_rows: dict[int, dict[str, float | int]] = {}

    for offset in range(sample_size):
        seed = seed_start + offset
        plan = generate_token_plan(replace(config, seed=seed))
        values = tuple(choice.value for choice in plan.choices)
        agreement = sum(a == b for a, b in zip(values, canonical_values, strict=True)) / token_count
        digest = hashlib.sha256("\x1f".join(values).encode("utf-8")).hexdigest()
        records.append(SeedReplicate(seed, agreement, len(set(values)), digest))
        agreement_values.append(agreement)
        unique_digests.add(digest)
        observed.update((choice.category, choice.value) for choice in plan.choices)

        current_size = offset + 1
        if current_size in ladder:
            current_values = agreement_values[:current_size]
            current_mean = sum(current_values) / current_size
            current_sd = (
                math.sqrt(sum((value - current_mean) ** 2 for value in current_values) / (current_size - 1))
                if current_size > 1
                else 0.0
            )
            ladder_rows[current_size] = {
                "sample_size": current_size,
                "mean_agreement": current_mean,
                "precision_radius": _hoeffding_radius(current_size, confidence_level),
                "inventory_coverage": len(observed) / inventory_total if inventory_total else 0.0,
                "sd_agreement": current_sd,
            }

    mean_agreement = sum(agreement_values) / sample_size
    sd_agreement = (
        math.sqrt(sum((value - mean_agreement) ** 2 for value in agreement_values) / (sample_size - 1))
        if sample_size > 1
        else 0.0
    )
    high_count = sum(value >= threshold for value in agreement_values)
    canonical_digest = hashlib.sha256("\x1f".join(canonical_values).encode("utf-8")).hexdigest()
    bootstrap_mean_interval = _bootstrap_mean_interval(
        agreement_values,
        confidence_level,
        bootstrap_replicates,
        config.seed,
    )
    canonical_matches = sum(record.plan_digest == canonical_digest for record in records)

    return SeedSensitivityReport(
        schema="template-gold-refinement-seed-sensitivity-v1",
        sample_size=sample_size,
        seed_start=seed_start,
        seed_end=seed_start + sample_size - 1,
        canonical_seed=config.seed,
        token_count=token_count,
        unique_plan_count=len(unique_digests),
        canonical_matches=canonical_matches,
        mean_agreement=mean_agreement,
        sd_agreement=sd_agreement,
        agreement_interval=_normal_interval(mean_agreement, sd_agreement, sample_size, z),
        agreement_min=min(agreement_values),
        agreement_max=max(agreement_values),
        agreement_threshold=threshold,
        high_agreement_count=high_count,
        high_agreement_rate=high_count / sample_size,
        high_agreement_interval=_wilson_interval(high_count, sample_size, z),
        inventory_total=inventory_total,
        inventory_observed=len(observed),
        inventory_coverage=len(observed) / inventory_total if inventory_total else 0.0,
        mean_unique_token_values=sum(record.unique_token_values for record in records) / sample_size,
        confidence_level=confidence_level,
        precision_target=precision_target,
        hoeffding_radius=_hoeffding_radius(sample_size, confidence_level),
        meets_precision_target=_hoeffding_radius(sample_size, confidence_level) <= precision_target,
        minimum_sample_size_for_precision_target=_minimum_sample_size_for_target(confidence_level, precision_target),
        seed_sampling_scheme=seed_sampling_scheme,
        precision_assumption=precision_assumption,
        agreement_interval_method="Normal approximation; descriptive conditional summary",
        threshold_interval_method="Wilson score interval; conditional binomial summary",
        precision_method="Hoeffding bound; conditional bounded-metric guarantee",
        bootstrap_replicates=bootstrap_replicates,
        bootstrap_seed=config.seed,
        bootstrap_mean_interval=bootstrap_mean_interval,
        sample_size_ladder=tuple(ladder_rows[size] for size in ladder),
        records=tuple(records),
    )


def validate_seed_sensitivity_payload(
    config: GoldRefinementConfig,
    payload: Mapping[str, Any] | SeedSensitivityReport,
) -> tuple[str, ...]:
    """Validate a generated report against a deterministic recomputation.

    This closes the gap between a correct generator and a later manuscript
    hydration step that might otherwise trust a stale or edited JSON report.
    """
    actual = payload.to_dict() if isinstance(payload, SeedSensitivityReport) else dict(payload)
    try:
        expected = run_seed_sensitivity(config).to_dict()
        expected = json.loads(json.dumps(expected, sort_keys=True))
        actual = json.loads(json.dumps(actual, sort_keys=True))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        return (f"seed sensitivity report cannot be normalized: {exc}",)

    mismatches = sorted(key for key in set(expected) | set(actual) if expected.get(key) != actual.get(key))
    if not mismatches:
        return ()
    return ("seed sensitivity report differs from deterministic recomputation in: " + ", ".join(mismatches),)


def write_seed_sensitivity_report(report: SeedSensitivityReport, output_path: Path) -> Path:
    """Write a seed-sensitivity report to a generated JSON path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return output_path


__all__ = [
    "DEFAULT_BOOTSTRAP_REPLICATES",
    "DEFAULT_SAMPLE_SIZE",
    "SeedReplicate",
    "SeedSensitivityReport",
    "run_seed_sensitivity",
    "validate_seed_sensitivity_payload",
    "write_seed_sensitivity_report",
]
