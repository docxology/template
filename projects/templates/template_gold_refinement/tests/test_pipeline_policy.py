from __future__ import annotations

from pathlib import Path

import yaml

from pipeline_policy import llm_review_gate_reason, llm_review_is_enabled, load_pipeline_policy


def _write_policy_config(tmp_path: Path, *, llm_enabled: bool = False) -> Path:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir(parents=True, exist_ok=True)
    (manuscript / "config.yaml").write_text(
        yaml.dump(
            {
                "steganography": {
                    "enabled": True,
                    "overlays_enabled": True,
                    "barcodes_enabled": True,
                    "metadata_enabled": True,
                    "hashing_enabled": True,
                    "encryption_enabled": False,
                    "overlay_mode": "text",
                    "overlay_text": "CONFIDENTIAL",
                    "overlay_opacity": 0.08,
                    "pdf_encryption_algorithm": "AES-256",
                    "kmyth_enabled": False,
                    "kmyth_required": False,
                    "kmyth_pcrs": [],
                    "kmyth_seal_artifacts": ["hash_manifest"],
                },
                "llm": {
                    "reviews": {
                        "enabled": llm_enabled,
                        "types": ["executive_summary", "methodology_review"],
                        "requires_ollama": True,
                        "requires_explicit_opt_in": True,
                    },
                    "translations": {"enabled": False, "languages": []},
                },
            }
        ),
        encoding="utf-8",
    )
    return tmp_path


def test_load_pipeline_policy_reads_steganography_and_llm(tmp_path):
    root = _write_policy_config(tmp_path)
    policy = load_pipeline_policy(root)

    assert policy.steganography.enabled is True
    assert policy.steganography.is_actionable is True
    assert policy.steganography.active_techniques == ("overlays", "barcodes", "metadata", "hashing")
    assert policy.steganography.overlay_text == "CONFIDENTIAL"
    assert policy.llm_reviews.enabled is False
    assert policy.llm_reviews.types == ("executive_summary", "methodology_review")
    assert policy.llm_reviews.requires_ollama is True
    assert policy.llm_reviews.requires_explicit_opt_in is True


def test_llm_review_gating_requires_ollama_and_opt_in(tmp_path):
    root = _write_policy_config(tmp_path, llm_enabled=True)
    policy = load_pipeline_policy(root)

    assert llm_review_is_enabled(policy.llm_reviews, ollama_available=False, explicit_opt_in=True) is False
    assert llm_review_gate_reason(policy.llm_reviews, ollama_available=False, explicit_opt_in=True) == "Ollama unavailable"
    assert llm_review_is_enabled(policy.llm_reviews, ollama_available=True, explicit_opt_in=False) is False
    assert "explicit opt-in required" in llm_review_gate_reason(
        policy.llm_reviews,
        ollama_available=True,
        explicit_opt_in=False,
    )
    assert llm_review_is_enabled(policy.llm_reviews, ollama_available=True, explicit_opt_in=True) is True
    assert llm_review_gate_reason(policy.llm_reviews, ollama_available=True, explicit_opt_in=True) == "ready"
