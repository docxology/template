#!/usr/bin/env python3
"""Tests for infrastructure.core.pipeline.dag.stage_label."""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.pipeline import stage_label


def _write_pipeline_yaml(repo_root: Path, stage_names: list[str]) -> None:
    """Write a minimal pipeline.yaml at the infrastructure default location."""
    pipeline_dir = repo_root / "infrastructure" / "core" / "pipeline"
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    stages = "\n".join(
        f"  - name: {name}\n    method: noop_{i}" for i, name in enumerate(stage_names)
    )
    (pipeline_dir / "pipeline.yaml").write_text(f"stages:\n{stages}\n", encoding="utf-8")


def test_stage_label_numbered_when_found(tmp_path: Path) -> None:
    """A stage present in the YAML is labelled with its 1-based index/total."""
    _write_pipeline_yaml(tmp_path, ["Setup", "Test"])

    label = stage_label("Test", repo_root=tmp_path)

    assert label == "Stage 2/2: Test"


def test_stage_label_fallback_when_stage_missing(tmp_path: Path) -> None:
    """A stage absent from the YAML falls back to the non-numeric label."""
    _write_pipeline_yaml(tmp_path, ["Setup", "Test"])

    label = stage_label("Nonexistent", repo_root=tmp_path)

    assert label == "Nonexistent stage"


def test_stage_label_fallback_when_repo_root_none() -> None:
    """With no repo_root, the lookup is skipped and the fallback is returned."""
    assert stage_label("LLM Scientific Review", repo_root=None) == "LLM Scientific Review stage"
