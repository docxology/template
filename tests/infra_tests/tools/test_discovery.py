"""Tests for infrastructure.tools discovery and validation.

All tests use real tmp_path directories — no mocks.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.tools import discover_tools, validate_tool_structure
from infrastructure.tools.public_scope import PUBLIC_TOOL_NAMES, public_tool_infos, public_tool_names


def test_public_tool_names_is_tuple() -> None:
    assert isinstance(PUBLIC_TOOL_NAMES, tuple)


def test_public_tool_names_non_empty() -> None:
    assert len(PUBLIC_TOOL_NAMES) > 0, "Should have at least one public tool"


def test_public_tool_names_contains_strings() -> None:
    for name in PUBLIC_TOOL_NAMES:
        assert isinstance(name, str)
        assert name


def test_discover_tools_against_real_repo() -> None:
    """Discover tools in the real repo — must find template_code_executor."""
    tools = discover_tools(Path("."))
    names = [t.name for t in tools]
    assert "template_code_executor" in names
    assert "template_validator" in names
    assert "template_skill" in names


def test_public_tool_infos_contains_exemplars() -> None:
    infos = public_tool_infos(Path("."))
    names = [i.qualified_name for i in infos]
    for expected in PUBLIC_TOOL_NAMES:
        assert expected in names, f"Expected {expected} in public tools, got {names}"


def test_validate_tool_structure_valid(tmp_path: Path) -> None:
    """A valid tool has tools.yaml + scripts/."""
    tool_dir = tmp_path / "test_tool"
    (tool_dir / "scripts").mkdir(parents=True)
    (tool_dir / "tools.yaml").write_text(
        "type: code_executor\ndescription: Test\ntags: [test]\nentrypoints: [scripts/run.sh]\n",
        encoding="utf-8",
    )
    (tool_dir / "scripts" / "run.sh").write_text("#!/bin/bash\necho ok\n")
    valid, msg = validate_tool_structure(tool_dir)
    assert valid, msg


def test_validate_tool_structure_no_yaml(tmp_path: Path) -> None:
    tool_dir = tmp_path / "no_yaml"
    (tool_dir / "scripts").mkdir(parents=True)
    valid, _ = validate_tool_structure(tool_dir)
    assert not valid


def test_validate_tool_structure_no_scripts(tmp_path: Path) -> None:
    tool_dir = tmp_path / "no_scripts"
    tool_dir.mkdir()
    (tool_dir / "tools.yaml").write_text("type: validator\n")
    valid, _ = validate_tool_structure(tool_dir)
    assert not valid


def test_public_tool_names_matches_infos() -> None:
    names = public_tool_names(Path("."))
    infos = public_tool_infos(Path("."))
    assert len(names) == len(infos)
    for info in infos:
        assert info.qualified_name in names