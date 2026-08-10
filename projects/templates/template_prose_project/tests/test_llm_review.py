"""Offline and fail-closed tests for optional LLM review evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.config import LLMReviewConfig, ProjectConfig, load_project_config
from src.llm_review import (
    LLM_TRANSCRIPT_SCHEMA_VERSION,
    build_llm_review_receipt,
)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _transcript() -> dict[str, object]:
    return {
        "schema_version": LLM_TRANSCRIPT_SCHEMA_VERSION,
        "provider": "local_transcript",
        "model": "fixture-model",
        "prompt_digest": _digest("prompt"),
        "response_digest": _digest("response"),
        "reviewer": "fixture-reviewer",
        "reviewed_paths": ["manuscript/00_abstract.md"],
        "status": "completed",
    }


def test_disabled_review_is_explicit_and_offline(tmp_path: Path) -> None:
    receipt = build_llm_review_receipt(LLMReviewConfig(), project_root=tmp_path)
    assert receipt == {
        "schema_version": "template-prose/llm-review/1",
        "status": "skipped",
        "reason": "disabled_by_config",
    }


def test_enabled_review_verifies_local_transcript(tmp_path: Path) -> None:
    transcript = tmp_path / "output" / "llm_review.json"
    transcript.parent.mkdir()
    transcript.write_text(json.dumps(_transcript()), encoding="utf-8")
    config = LLMReviewConfig(
        enabled=True,
        provider="local_transcript",
        model="fixture-model",
    )
    receipt = build_llm_review_receipt(config, project_root=tmp_path)
    assert receipt["status"] == "verified"
    assert receipt["execution"] == "transcript_only"
    assert len(str(receipt["transcript_digest"])) == 64


def test_enabled_review_missing_transcript_fails_closed(tmp_path: Path) -> None:
    config = LLMReviewConfig(enabled=True, provider="local_transcript", model="fixture-model")
    with pytest.raises(ValueError, match="requires transcript"):
        build_llm_review_receipt(config, project_root=tmp_path)


def test_transcript_provider_drift_fails_closed(tmp_path: Path) -> None:
    payload = _transcript()
    payload["provider"] = "other-provider"
    transcript = tmp_path / "output" / "llm_review.json"
    transcript.parent.mkdir()
    transcript.write_text(json.dumps(payload), encoding="utf-8")
    config = LLMReviewConfig(enabled=True, provider="local_transcript", model="fixture-model")
    with pytest.raises(ValueError, match="provider/model"):
        build_llm_review_receipt(config, project_root=tmp_path)


def test_config_accepts_disabled_review_and_rejects_unknown_nested_key(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "paper: {title: Demo}\nllm:\n  review:\n    enabled: false\n",
        encoding="utf-8",
    )
    assert load_project_config(config_path).llm.enabled is False
    config_path.write_text(
        "paper: {title: Demo}\nllm:\n  review:\n    unknown: true\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="llm.review"):
        load_project_config(config_path)


def test_enabled_review_rejects_network_provider_without_model() -> None:
    with pytest.raises(ValueError, match="non-empty model"):
        LLMReviewConfig(enabled=True, provider="ollama")


def test_project_config_has_offline_llm_default() -> None:
    assert ProjectConfig(title="x").llm.enabled is False
