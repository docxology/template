"""Real-filesystem tests for cross-runtime Agent Skills parity."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.skills.runtime_sync import (
    compute_skill_tree_digest,
    install_runtime_skills,
    runtime_status,
    validate_vendored_source,
)


def _template_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _write_skill(source: Path, name: str, description: str = "A test skill") -> None:
    skill = source / name
    (skill / "references").mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n",
        encoding="utf-8",
    )
    (skill / "references" / "note.md").write_text("reference\n", encoding="utf-8")


def _fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    source = repo / ".agents" / "skills"
    _write_skill(source, "alpha")
    _write_skill(source, "beta")
    digest, file_count = compute_skill_tree_digest(source)
    lock = {
        "schema_version": 1,
        "source_url": "https://example.invalid/context-skills",
        "revision": "a" * 40,
        "plugin_version": "1.0.0",
        "license": "MIT",
        "skill_count": 2,
        "file_count": file_count,
        "vendored_tree_sha256": digest,
    }
    (repo / ".agents" / "context-engineering.lock.json").write_text(
        json.dumps(lock),
        encoding="utf-8",
    )
    return repo


def test_real_vendored_context_engineering_tree_matches_lock() -> None:
    status = validate_vendored_source(_template_repo_root())
    assert status["ok"], status["issues"]
    assert status["skill_count"] == 17
    assert status["file_count"] == 57
    assert "context-fundamentals" in status["skill_names"]
    assert "self-improvement-loops" in status["skill_names"]


def test_install_links_all_runtimes_and_is_idempotent(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    home = tmp_path / "home"

    first = install_runtime_skills(repo, home)
    status = runtime_status(repo, home)
    second = install_runtime_skills(repo, home)

    assert status["ok"]
    assert status["hermes_trust"]["ok"]
    assert Path(first["receipt_path"]).is_file()
    assert Path(first["state_path"]).is_file()
    assert Path(second["receipt_path"]).is_file()
    assert first["receipt_path"] != second["receipt_path"]
    assert all(action["action"] == "linked" for action in first["actions"])
    assert all(action["action"] == "unchanged" for action in second["actions"])
    for runtime_root in (home / ".agents/skills", home / ".claude/skills", home / ".hermes/skills"):
        for name in ("alpha", "beta"):
            assert (runtime_root / name).is_symlink()
            assert (runtime_root / name / "references" / "note.md").read_text(encoding="utf-8") == "reference\n"


def test_install_backs_up_existing_runtime_skill(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    home = tmp_path / "home"
    existing = home / ".claude/skills/alpha"
    existing.mkdir(parents=True)
    (existing / "local.txt").write_text("keep me\n", encoding="utf-8")
    hermes_config = home / ".hermes/config.yaml"
    hermes_config.parent.mkdir(parents=True)
    hermes_config.write_text("skills:\n  external_dirs:\n    - /existing/skills\n", encoding="utf-8")

    result = install_runtime_skills(repo, home)

    alpha_action = next(row for row in result["actions"] if row["runtime"] == "claude" and row["skill"] == "alpha")
    backup = Path(alpha_action["backup"])
    assert (backup / "local.txt").read_text(encoding="utf-8") == "keep me\n"
    assert existing.is_symlink()
    config_backup = home / ".local/state/template-agent-skills/backups"
    assert list(config_backup.glob("*/hermes-config/hermes-config.yaml"))
    assert "/existing/skills" in hermes_config.read_text(encoding="utf-8")


def test_status_detects_wrong_runtime_target(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    home = tmp_path / "home"
    install_runtime_skills(repo, home)
    wrong = tmp_path / "wrong"
    wrong.mkdir()
    link = home / ".hermes/skills/alpha"
    link.unlink()
    link.symlink_to(wrong, target_is_directory=True)

    status = runtime_status(repo, home)

    assert status["ok"] is False
    assert status["runtimes"]["hermes"]["ok"] is False
    assert status["runtimes"]["codex"]["ok"] is True


def test_vendored_digest_drift_fails_closed(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    (repo / ".agents/skills/alpha/SKILL.md").write_text("changed\n", encoding="utf-8")

    status = validate_vendored_source(repo)

    assert status["ok"] is False
    assert any("digest" in issue for issue in status["issues"])


def test_vendored_source_rejects_symlink(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    target = repo / "outside.txt"
    target.write_text("outside\n", encoding="utf-8")
    (repo / ".agents/skills/alpha/references/link.md").symlink_to(target)

    with pytest.raises(ValueError, match="symlink"):
        validate_vendored_source(repo)
