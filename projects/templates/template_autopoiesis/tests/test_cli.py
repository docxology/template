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
