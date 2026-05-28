"""Tests for manuscript.sheaf.cli helpers."""

from __future__ import annotations

from pathlib import Path

from manuscript.sheaf.cli import build_parser, run_compose_cli


def test_build_parser_has_expected_flags() -> None:
    parser = build_parser()
    args = parser.parse_args(["--validate-only", "--strict", "--list-tracks"])
    assert args.validate_only
    assert args.strict
    assert args.list_tracks


def test_run_compose_cli_list_tracks(project_root: Path, capsys) -> None:
    code = run_compose_cli(["--list-tracks"], project_root=project_root)
    out = capsys.readouterr().out
    assert code == 0
    assert "prose" in out
    assert "order=" in out


def test_run_compose_cli_validate_only_strict(project_root: Path) -> None:
    code = run_compose_cli(["--validate-only", "--strict"], project_root=project_root)
    assert code == 0


def test_run_compose_cli_compose_section(project_root: Path, tmp_path: Path) -> None:
    code = run_compose_cli(
        ["--section", "methods_sheaf", "--coverage-json", str(tmp_path / "cov.json")],
        project_root=project_root,
    )
    assert code == 0
    assert (tmp_path / "cov.json").is_file()
