"""Tests for docs/prompts skill metadata contracts (no mocks)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from infrastructure.skills.contracts import (
    check_skill_contracts,
    validate_skill_contract_file,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


VALID_SKILL = """---
name: template-academic-paper
description: Template-native paper drafting workflow.
metadata:
  version: "1.0.0"
  last_updated: "2026-05-25"
  status: active
  data_access_level: redacted
  task_type: open-ended
  modes:
    - plan
    - full
  related_skills:
    - template-manuscript-creation
---

# Academic paper
"""


def test_validate_skill_contract_file_accepts_complete_metadata(tmp_path: Path) -> None:
    skill = tmp_path / "docs/prompts/academic-paper/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(VALID_SKILL, encoding="utf-8")

    assert validate_skill_contract_file(skill) == []


def test_validate_skill_contract_file_rejects_missing_metadata(tmp_path: Path) -> None:
    skill = tmp_path / "docs/prompts/academic-paper/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        "---\nname: bad\ndescription: Missing contract\n---\n# Bad\n",
        encoding="utf-8",
    )

    issues = validate_skill_contract_file(skill)

    assert any("metadata.version" in issue for issue in issues)
    assert any("metadata.data_access_level" in issue for issue in issues)
    assert any("metadata.modes" in issue for issue in issues)


def test_check_skill_contracts_scans_docs_prompts(tmp_path: Path) -> None:
    valid = tmp_path / "docs/prompts/academic-paper/SKILL.md"
    valid.parent.mkdir(parents=True)
    valid.write_text(VALID_SKILL, encoding="utf-8")
    invalid = tmp_path / "docs/prompts/bad/SKILL.md"
    invalid.parent.mkdir(parents=True)
    invalid.write_text("---\nname: bad\ndescription: Bad\n---\n", encoding="utf-8")

    issues = check_skill_contracts(tmp_path)

    assert any("docs/prompts/bad/SKILL.md" in issue for issue in issues)
    assert not any("docs/prompts/academic-paper/SKILL.md" in issue for issue in issues)


def test_template_prompt_contracts_are_valid() -> None:
    assert check_skill_contracts(_repo_root()) == []


def test_check_contracts_cli() -> None:
    root = _repo_root()
    proc = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-m",
            "infrastructure.skills",
            "check-contracts",
            "--repo-root",
            str(root),
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "skill contracts ok" in (proc.stdout + proc.stderr).lower()
