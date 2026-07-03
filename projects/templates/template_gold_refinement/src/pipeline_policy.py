from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import yaml

try:
    from .coercion import coerce_bool
except ImportError:
    from coercion import coerce_bool  # type: ignore[no-redef]


def _load_project_config(project_root: Path) -> dict[str, Any]:
    config_path = project_root / "manuscript" / "config.yaml"
    if not config_path.exists():
        return {}
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data if isinstance(data, dict) else {}


def _as_bool(value: Any, default: bool = False, *, field_name: str) -> bool:
    return coerce_bool(value, default=default, field_name=field_name)


def _as_str_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return tuple(part.strip() for part in value.split(",") if part.strip())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return ()


def _as_int_tuple(value: Any) -> tuple[int, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return tuple(int(part.strip()) for part in value.split(",") if part.strip())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(int(item) for item in value if str(item).strip())
    return ()


def _as_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    return float(value)


@dataclass(frozen=True)
class SteganographyProfile:
    enabled: bool = False
    overlays_enabled: bool = False
    barcodes_enabled: bool = False
    metadata_enabled: bool = False
    hashing_enabled: bool = False
    encryption_enabled: bool = False
    overlay_mode: str = "text"
    overlay_text: str = ""
    overlay_opacity: float = 0.08
    pdf_password: str = ""
    pdf_encryption_algorithm: str = "AES-256"
    kmyth_enabled: bool = False
    kmyth_required: bool = False
    kmyth_binary_dir: str = ""
    kmyth_source_dir: str = ""
    kmyth_pcrs: tuple[int, ...] = ()
    kmyth_cipher: str = ""
    kmyth_seal_artifacts: tuple[str, ...] = ()
    kmyth_output_suffix: str = ""
    kmyth_overwrite: bool = False
    kmyth_timeout_seconds: int = 0

    @property
    def active_techniques(self) -> tuple[str, ...]:
        return tuple(
            name
            for name, enabled in (
                ("overlays", self.overlays_enabled),
                ("barcodes", self.barcodes_enabled),
                ("metadata", self.metadata_enabled),
                ("hashing", self.hashing_enabled),
                ("encryption", self.encryption_enabled),
                ("kmyth", self.kmyth_enabled),
            )
            if enabled
        )

    @property
    def is_actionable(self) -> bool:
        return self.enabled and bool(self.active_techniques)

    def summary(self) -> str:
        if not self.enabled:
            return "disabled"
        techniques = ", ".join(self.active_techniques) if self.active_techniques else "none"
        return f"enabled ({techniques})"


@dataclass(frozen=True)
class LLMReviewPolicy:
    enabled: bool = False
    types: tuple[str, ...] = ()
    requires_ollama: bool = True
    requires_explicit_opt_in: bool = True

    @property
    def is_configured(self) -> bool:
        return self.enabled and bool(self.types)

    def gate_reasons(self, *, ollama_available: bool, explicit_opt_in: bool) -> tuple[str, ...]:
        reasons: list[str] = []
        if not self.enabled:
            reasons.append("LLM reviews disabled in config")
        if not self.types:
            reasons.append("no review types configured")
        if self.requires_ollama and not ollama_available:
            reasons.append("Ollama unavailable")
        if self.requires_explicit_opt_in and not explicit_opt_in:
            reasons.append("explicit opt-in required")
        return tuple(reasons)

    def can_run(self, *, ollama_available: bool, explicit_opt_in: bool) -> bool:
        return not self.gate_reasons(ollama_available=ollama_available, explicit_opt_in=explicit_opt_in)

    def summary(self) -> str:
        if not self.enabled:
            return "disabled"
        review_types = ", ".join(self.types) if self.types else "none"
        return f"enabled ({review_types})"


@dataclass(frozen=True)
class PipelinePolicy:
    steganography: SteganographyProfile
    llm_reviews: LLMReviewPolicy


def load_steganography_profile(project_root: Path | None = None) -> SteganographyProfile:
    root = project_root or Path(__file__).resolve().parent.parent
    config = _load_project_config(root)
    raw = config.get("steganography", {})
    if not isinstance(raw, dict):
        raw = {}
    return SteganographyProfile(
        enabled=_as_bool(raw.get("enabled"), False, field_name="steganography.enabled"),
        overlays_enabled=_as_bool(
            raw.get("overlays_enabled", raw.get("overlays")),
            False,
            field_name="steganography.overlays_enabled",
        ),
        barcodes_enabled=_as_bool(
            raw.get("barcodes_enabled", raw.get("barcodes")),
            False,
            field_name="steganography.barcodes_enabled",
        ),
        metadata_enabled=_as_bool(
            raw.get("metadata_enabled", raw.get("metadata")),
            False,
            field_name="steganography.metadata_enabled",
        ),
        hashing_enabled=_as_bool(
            raw.get("hashing_enabled", raw.get("hashing")),
            False,
            field_name="steganography.hashing_enabled",
        ),
        encryption_enabled=_as_bool(
            raw.get("encryption_enabled", raw.get("encryption")),
            False,
            field_name="steganography.encryption_enabled",
        ),
        overlay_mode=str(raw.get("overlay_mode", "text")),
        overlay_text=str(raw.get("overlay_text", "")),
        overlay_opacity=_as_float(raw.get("overlay_opacity"), 0.08),
        pdf_password=str(raw.get("pdf_password", "")),
        pdf_encryption_algorithm=str(raw.get("pdf_encryption_algorithm", "AES-256")),
        kmyth_enabled=_as_bool(raw.get("kmyth_enabled"), False, field_name="steganography.kmyth_enabled"),
        kmyth_required=_as_bool(raw.get("kmyth_required"), False, field_name="steganography.kmyth_required"),
        kmyth_binary_dir=str(raw.get("kmyth_binary_dir", "")),
        kmyth_source_dir=str(raw.get("kmyth_source_dir", "")),
        kmyth_pcrs=_as_int_tuple(raw.get("kmyth_pcrs")),
        kmyth_cipher=str(raw.get("kmyth_cipher", "")),
        kmyth_seal_artifacts=_as_str_tuple(raw.get("kmyth_seal_artifacts")),
        kmyth_output_suffix=str(raw.get("kmyth_output_suffix", "")),
        kmyth_overwrite=_as_bool(raw.get("kmyth_overwrite"), False, field_name="steganography.kmyth_overwrite"),
        kmyth_timeout_seconds=int(raw.get("kmyth_timeout_seconds", 0) or 0),
    )


def load_llm_review_policy(project_root: Path | None = None) -> LLMReviewPolicy:
    root = project_root or Path(__file__).resolve().parent.parent
    config = _load_project_config(root)
    raw = config.get("llm", {})
    if not isinstance(raw, dict):
        raw = {}
    reviews = raw.get("reviews", {})
    if not isinstance(reviews, dict):
        reviews = {}
    return LLMReviewPolicy(
        enabled=_as_bool(reviews.get("enabled"), False, field_name="llm.reviews.enabled"),
        types=_as_str_tuple(reviews.get("types")),
        requires_ollama=_as_bool(
            reviews.get("requires_ollama"),
            True,
            field_name="llm.reviews.requires_ollama",
        ),
        requires_explicit_opt_in=_as_bool(
            reviews.get("requires_explicit_opt_in"),
            True,
            field_name="llm.reviews.requires_explicit_opt_in",
        ),
    )


def load_pipeline_policy(project_root: Path | None = None) -> PipelinePolicy:
    return PipelinePolicy(
        steganography=load_steganography_profile(project_root),
        llm_reviews=load_llm_review_policy(project_root),
    )


def llm_review_gate_reason(
    policy: LLMReviewPolicy,
    *,
    ollama_available: bool,
    explicit_opt_in: bool,
) -> str:
    reasons = policy.gate_reasons(ollama_available=ollama_available, explicit_opt_in=explicit_opt_in)
    return "ready" if not reasons else "; ".join(reasons)


def llm_review_is_enabled(
    policy: LLMReviewPolicy,
    *,
    ollama_available: bool,
    explicit_opt_in: bool,
) -> bool:
    return policy.can_run(ollama_available=ollama_available, explicit_opt_in=explicit_opt_in)


__all__ = [
    "LLMReviewPolicy",
    "PipelinePolicy",
    "SteganographyProfile",
    "llm_review_gate_reason",
    "llm_review_is_enabled",
    "load_llm_review_policy",
    "load_pipeline_policy",
    "load_steganography_profile",
]
