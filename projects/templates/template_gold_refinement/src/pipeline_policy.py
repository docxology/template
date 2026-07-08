from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

try:
    from .parsing import (
        as_bool as _as_bool,
        as_float as _as_float,
        as_int_tuple as _as_int_tuple,
        as_str_tuple as _as_str_tuple,
        load_manuscript_config as _load_project_config,
    )
except ImportError:
    from parsing import (  # type: ignore[no-redef]
        as_bool as _as_bool,
        as_float as _as_float,
        as_int_tuple as _as_int_tuple,
        as_str_tuple as _as_str_tuple,
        load_manuscript_config as _load_project_config,
    )


@dataclass(frozen=True)
class SteganographyProfile:
    """Data container for SteganographyProfile."""

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
        """Process active techniques."""
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
        """Check whether actionable."""
        return self.enabled and bool(self.active_techniques)

    def summary(self) -> str:
        """Return a summary dict of counts and status."""
        if not self.enabled:
            return "disabled"
        techniques = ", ".join(self.active_techniques) if self.active_techniques else "none"
        return f"enabled ({techniques})"


@dataclass(frozen=True)
class LLMReviewPolicy:
    """Data container for LLMReviewPolicy."""

    enabled: bool = False
    types: tuple[str, ...] = ()
    requires_ollama: bool = True
    requires_explicit_opt_in: bool = True

    @property
    def is_configured(self) -> bool:
        """Check whether configured."""
        return self.enabled and bool(self.types)

    def gate_reasons(self, *, ollama_available: bool, explicit_opt_in: bool) -> tuple[str, ...]:
        """Process gate reasons."""
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
        """Process can run."""
        return not self.gate_reasons(ollama_available=ollama_available, explicit_opt_in=explicit_opt_in)

    def summary(self) -> str:
        """Return a summary dict of counts and status."""
        if not self.enabled:
            return "disabled"
        review_types = ", ".join(self.types) if self.types else "none"
        return f"enabled ({review_types})"


@dataclass(frozen=True)
class PipelinePolicy:
    """Data container for PipelinePolicy."""

    steganography: SteganographyProfile
    llm_reviews: LLMReviewPolicy


def load_steganography_profile(project_root: Path | None = None) -> SteganographyProfile:
    """Load steganography profile from a file."""
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
    """Load llm review policy from a file."""
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
    """Load pipeline policy from a file."""
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
    """Process llm review gate reason."""
    reasons = policy.gate_reasons(ollama_available=ollama_available, explicit_opt_in=explicit_opt_in)
    return "ready" if not reasons else "; ".join(reasons)


def llm_review_is_enabled(
    policy: LLMReviewPolicy,
    *,
    ollama_available: bool,
    explicit_opt_in: bool,
) -> bool:
    """Process llm review is enabled."""
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
