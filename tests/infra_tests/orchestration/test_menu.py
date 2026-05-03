"""Tests for infrastructure.orchestration.menu."""

from __future__ import annotations

import pytest

from infrastructure.orchestration.menu import (
    MENU_OPTIONS,
    STAGE_NAMES,
    menu_keys,
    parse_choice_sequence,
    render_menu,
)


def test_render_menu_is_deterministic() -> None:
    """The same inputs must yield byte-identical output."""
    a = render_menu("template_code_project")
    b = render_menu("template_code_project")
    assert a == b


def test_render_menu_includes_project_name() -> None:
    rendered = render_menu("my_special_project_xyz")
    assert "my_special_project_xyz" in rendered


def test_render_menu_lists_all_keys() -> None:
    rendered = render_menu("template_code_project")
    for key, label, _ in MENU_OPTIONS:
        # Each key appears at least once with its label.
        assert f"  {key}  {label}" in rendered, f"missing key={key} label={label}"


def test_render_menu_no_ansi_codes() -> None:
    """The Python menu must not embed ANSI escape codes; tests assert literal output."""
    rendered = render_menu("template_code_project")
    assert "\x1b[" not in rendered


def test_stage_names_align_with_pipeline() -> None:
    # 9 named stages (numbered [1/9]..[9/9])
    assert len(STAGE_NAMES) == 9
    assert STAGE_NAMES[0] == "Setup Environment"
    assert STAGE_NAMES[-1] == "Copy Outputs"


def test_menu_keys_unique() -> None:
    keys = [k for k, _, _ in MENU_OPTIONS]
    assert len(keys) == len(set(keys)), "MENU_OPTIONS keys must be unique"
    assert "q" in menu_keys()


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("234", ["2", "3", "4"]),
        ("3,4,5", ["3", "4", "5"]),
        ("3 4 5", ["3", "4", "5"]),
        ("a", ["a"]),
        ("", []),
        ("   ", []),
    ],
)
def test_parse_choice_sequence(raw: str, expected: list[str]) -> None:
    assert parse_choice_sequence(raw) == expected


def test_parse_choice_sequence_rejects_invalid_key() -> None:
    with pytest.raises(ValueError, match="invalid menu key"):
        parse_choice_sequence("z")


def test_parse_choice_sequence_rejects_invalid_in_csv() -> None:
    with pytest.raises(ValueError, match="invalid menu key"):
        parse_choice_sequence("2,zz,4")


def test_parse_choice_sequence_rejects_digit_with_invalid_concat() -> None:
    """The 'concatenated digits' branch only applies to digits 0-9."""
    # 'a3' is not pure digits, so it routes to single-token validation
    with pytest.raises(ValueError, match="invalid menu key"):
        parse_choice_sequence("a3")


def test_parse_choice_sequence_none() -> None:
    assert parse_choice_sequence(None) == []  # type: ignore[arg-type]


def test_parse_choice_sequence_skips_empty_tokens() -> None:
    """Empty tokens between commas are silently skipped."""
    assert parse_choice_sequence("3,,4") == ["3", "4"]
    assert parse_choice_sequence(",3,") == ["3"]
