"""Tests for CLI commands."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from src.cli import build_parser, main


PROJECT_ROOT = Path(__file__).parent.parent


def test_build_parser_returns_parser():
    parser = build_parser()
    assert parser is not None


def test_parser_has_enumerate_command():
    parser = build_parser()
    args = parser.parse_args(["enumerate"])
    assert args.command == "enumerate"


def test_parser_has_expand_command():
    parser = build_parser()
    args = parser.parse_args(["expand"])
    assert args.command == "expand"


def test_parser_has_sample_command():
    parser = build_parser()
    args = parser.parse_args(["sample"])
    assert args.command == "sample"


def test_parser_has_materialize_command():
    parser = build_parser()
    args = parser.parse_args(["materialize"])
    assert args.command == "materialize"


def test_parser_has_verify_command():
    parser = build_parser()
    args = parser.parse_args(["verify", "output/example"])
    assert args.command == "verify"


def test_parser_has_honesty_command():
    parser = build_parser()
    args = parser.parse_args(["honesty"])
    assert args.command == "honesty"


def test_parser_expand_seed():
    parser = build_parser()
    args = parser.parse_args(["expand", "--seed", "999"])
    assert args.seed == "999"


def test_parser_sample_count():
    parser = build_parser()
    args = parser.parse_args(["sample", "--count", "3"])
    assert args.count == "3"


def test_main_no_command_exits(capsys):
    with pytest.raises(SystemExit):
        main([])


def test_main_expand_runs(capsys):
    main(["--project-root", str(PROJECT_ROOT), "expand"])
    out = capsys.readouterr().out
    assert "seed" in out


def test_main_enumerate_runs(capsys):
    main(["--project-root", str(PROJECT_ROOT), "enumerate"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert len(data) > 0


def test_main_sample_runs(capsys):
    main(["--project-root", str(PROJECT_ROOT), "sample", "--count", "3"])
    out = capsys.readouterr().out
    lines = [l for l in out.strip().split("\n") if l]
    assert len(lines) == 3


def test_main_honesty_exits_zero(capsys):
    try:
        main(["--project-root", str(PROJECT_ROOT), "honesty"])
    except SystemExit as e:
        assert e.code == 0


# ---------------------------------------------------------------------------
# cmd_materialize end-to-end — lines 50-65
# ---------------------------------------------------------------------------


def test_main_materialize_runs(tmp_path, capsys):
    """cmd_materialize should print 'Materialized:' and 'Tree hash:' lines."""
    main([
        "--project-root", str(PROJECT_ROOT),
        "materialize",
        "--out-root", str(tmp_path),
    ])
    out = capsys.readouterr().out
    assert "Materialized:" in out
    assert "Tree hash:" in out


def test_main_materialize_creates_child_dir(tmp_path, capsys):
    """cmd_materialize should create a non-empty child directory."""
    main([
        "--project-root", str(PROJECT_ROOT),
        "materialize",
        "--out-root", str(tmp_path),
    ])
    # At least one child subdirectory must have been created
    children = list(tmp_path.iterdir())
    assert len(children) >= 1


def test_main_materialize_with_clean_flag(tmp_path, capsys):
    """cmd_materialize --clean should succeed and produce output."""
    # First run to create a child
    main([
        "--project-root", str(PROJECT_ROOT),
        "materialize",
        "--out-root", str(tmp_path),
    ])
    capsys.readouterr()  # clear buffer
    # Second run with --clean to overwrite
    main([
        "--project-root", str(PROJECT_ROOT),
        "materialize",
        "--out-root", str(tmp_path),
        "--clean",
    ])
    out = capsys.readouterr().out
    assert "Materialized:" in out
    assert "Tree hash:" in out


def test_parser_has_clean_flag_on_materialize():
    """materialize subcommand should accept --clean flag."""
    parser = build_parser()
    args = parser.parse_args(["materialize", "--clean"])
    assert args.clean is True


def test_parser_clean_default_is_false():
    """materialize subcommand --clean should default to False."""
    parser = build_parser()
    args = parser.parse_args(["materialize"])
    assert args.clean is False


# ---------------------------------------------------------------------------
# cmd_verify end-to-end — lines 69-75
# ---------------------------------------------------------------------------


def test_main_verify_runs(tmp_path, capsys):
    """cmd_verify on a valid child should print PASS/FAIL lines."""
    # First materialize a child
    main([
        "--project-root", str(PROJECT_ROOT),
        "materialize",
        "--out-root", str(tmp_path),
    ])
    out = capsys.readouterr().out
    # Extract the child path from the 'Materialized: <path>' line
    child_path = None
    for line in out.splitlines():
        if line.startswith("Materialized:"):
            child_path = line.split("Materialized:", 1)[1].strip()
            break
    assert child_path is not None, f"Could not find 'Materialized:' in output: {out!r}"

    # Now verify the materialized child
    try:
        main([
            "--project-root", str(PROJECT_ROOT),
            "verify",
            child_path,
        ])
    except SystemExit:
        pass  # verify exits 0 on pass or 1 on fail; either is fine here

    out2 = capsys.readouterr().out
    # Should have at least one [PASS] or [FAIL] line
    assert "[PASS]" in out2 or "[FAIL]" in out2


def test_main_verify_passes_on_clean_child(tmp_path, capsys):
    """cmd_verify should exit 0 on a clean freshly materialized child."""
    main([
        "--project-root", str(PROJECT_ROOT),
        "materialize",
        "--out-root", str(tmp_path),
    ])
    out = capsys.readouterr().out
    child_path = None
    for line in out.splitlines():
        if line.startswith("Materialized:"):
            child_path = line.split("Materialized:", 1)[1].strip()
            break
    assert child_path is not None

    exit_code = 0
    try:
        main([
            "--project-root", str(PROJECT_ROOT),
            "verify",
            child_path,
        ])
    except SystemExit as exc:
        exit_code = exc.code

    assert exit_code == 0, f"Expected exit 0, got {exit_code}"
