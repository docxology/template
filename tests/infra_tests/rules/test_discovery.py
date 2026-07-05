"""Tests for infrastructure.rules discovery and validation.

All tests use real tmp_path directories — no mocks.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.rules import discover_rules, validate_rule_structure
from infrastructure.rules.public_scope import PUBLIC_RULE_NAMES, public_rule_infos, public_rule_names


def test_public_rule_names_is_tuple() -> None:
    assert isinstance(PUBLIC_RULE_NAMES, tuple)


def test_public_rule_names_non_empty() -> None:
    assert len(PUBLIC_RULE_NAMES) > 0


def test_public_rule_names_contains_strings() -> None:
    for name in PUBLIC_RULE_NAMES:
        assert isinstance(name, str)
        assert name


def test_discover_rules_against_real_repo() -> None:
    """Discover rules in the real repo."""
    rules = discover_rules(Path("."))
    names = [r.name for r in rules]
    assert "template_project_rules" in names
    assert "template_manuscript_rules" in names


def test_public_rule_infos_contains_exemplars() -> None:
    infos = public_rule_infos(Path("."))
    names = [i.qualified_name for i in infos]
    for expected in PUBLIC_RULE_NAMES:
        assert expected in names, f"Expected {expected} in public rules, got {names}"


def test_validate_rule_structure_both(tmp_path: Path) -> None:
    """Valid rule has rules.yaml + at least one of soft/ or strong/."""
    rule_dir = tmp_path / "full_rule"
    (rule_dir / "soft").mkdir(parents=True)
    (rule_dir / "strong").mkdir()
    (rule_dir / "rules.yaml").write_text(
        "type: project\ndescription: Test\n", encoding="utf-8",
    )
    valid, msg = validate_rule_structure(rule_dir)
    assert valid, msg


def test_validate_rule_structure_soft_only(tmp_path: Path) -> None:
    rule_dir = tmp_path / "soft_only"
    (rule_dir / "soft").mkdir(parents=True)
    (rule_dir / "rules.yaml").write_text("type: manuscript\ndescription: Soft only\n")
    valid, msg = validate_rule_structure(rule_dir)
    assert valid, msg


def test_validate_rule_structure_strong_only(tmp_path: Path) -> None:
    rule_dir = tmp_path / "strong_only"
    (rule_dir / "strong").mkdir(parents=True)
    (rule_dir / "rules.yaml").write_text("type: code\ndescription: Strong only\n")
    valid, msg = validate_rule_structure(rule_dir)
    assert valid, msg


def test_validate_rule_structure_no_yaml(tmp_path: Path) -> None:
    rule_dir = tmp_path / "no_yaml"
    (rule_dir / "soft").mkdir(parents=True)
    valid, _ = validate_rule_structure(rule_dir)
    assert not valid


def test_validate_rule_structure_no_soft_no_strong(tmp_path: Path) -> None:
    rule_dir = tmp_path / "no_content"
    rule_dir.mkdir()
    (rule_dir / "rules.yaml").write_text("type: project\n")
    valid, _ = validate_rule_structure(rule_dir)
    assert not valid


def test_exemplar_rules_have_both_kinds() -> None:
    """Real exemplar rules should have both soft and strong dirs."""
    for name in PUBLIC_RULE_NAMES:
        head = name.split("/")[-1]
        rule_dir = Path("rules/templates") / head
        if not rule_dir.exists():
            continue
        valid, msg = validate_rule_structure(rule_dir)
        assert valid, f"{name}: {msg}"