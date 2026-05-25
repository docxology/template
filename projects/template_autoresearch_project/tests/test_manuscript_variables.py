"""Tests for manuscript variable hydration."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from src.loop import run_autoresearch_loop
from src.manuscript_variables import compute_variables, compute_variables_from_payload


def test_manuscript_variables_cover_all_source_tokens(project_root: Path, repo_root: Path) -> None:
    run_autoresearch_loop(project_root, repo_root)
    variables = compute_variables(project_root)
    tokens = set()
    for path in (project_root / "manuscript").glob("[0-9][0-9]_*.md"):
        tokens.update(re.findall(r"\{\{([A-Z0-9_]+)\}\}", path.read_text(encoding="utf-8")))

    assert tokens
    assert tokens <= set(variables)
    assert variables["READINESS_STATUS"] == "passed"


def test_variable_script_writes_resolved_manuscript(project_root: Path) -> None:
    script = project_root / "scripts" / "z_generate_manuscript_variables.py"
    result = subprocess.run([sys.executable, str(script)], cwd=project_root, text=True, capture_output=True)

    assert result.returncode == 0, result.stderr
    resolved = project_root / "output" / "manuscript" / "00_abstract.md"
    assert resolved.exists()
    assert "{{" not in resolved.read_text(encoding="utf-8")


def test_compute_variables_handles_malformed_payload_sections() -> None:
    variables = compute_variables_from_payload(
        {
            "config": [],
            "metrics": [],
            "stage_results": [{"name": "plan"}],
            "claims": [{"identifier": "rq1"}],
        }
    )

    assert variables["AUTORESEARCH_TOPIC"] == "Deterministic AutoResearch"
    assert variables["LOOP_STAGE_COUNT"] == "1"
    assert variables["SUPPORTED_CLAIM_COUNT"] == "1"
    assert variables["READINESS_STATUS"] == "requires review"
