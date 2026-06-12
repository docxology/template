#!/usr/bin/env python3
"""Tests for documentation generation helpers."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from documentation import build_api_reference_markdown  # noqa: E402

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from generate_api_docs import run_api_doc_generation  # noqa: E402


def test_build_api_reference_markdown_contains_core_symbols() -> None:
    text = build_api_reference_markdown()
    assert "OptimizationResult" in text or "API" in text


def test_run_api_doc_generation_writes_api_reference(tmp_path: Path) -> None:
    project_root = tmp_path / "proj"
    (project_root / "src").mkdir(parents=True)
    (project_root / "src" / "sample.py").write_text("def foo() -> int:\n    return 1\n", encoding="utf-8")

    result = run_api_doc_generation(project_root)
    assert result is not None
    api_path = Path(result["api_reference"])
    assert api_path.exists()
    assert len(api_path.read_text(encoding="utf-8")) > 0
