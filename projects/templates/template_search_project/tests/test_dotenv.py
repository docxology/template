"""Tests for src.dotenv — real files, no third-party dotenv."""

from __future__ import annotations

import os
from pathlib import Path

from src.dotenv import load_dotenv, parse_dotenv


def test_parse_dotenv_basic_and_comments():
    text = """
    # comment
    FOO=bar
    EMPTY=

    BAZ="quoted value"
    """
    d = parse_dotenv(text)
    assert d["FOO"] == "bar"
    assert d["EMPTY"] == ""
    assert d["BAZ"] == "quoted value"


def test_parse_dotenv_skips_malformed_lines():
    d = parse_dotenv("not_a_keyval\nOK=1\n")
    assert d == {"OK": "1"}


def test_load_dotenv_writes_env(tmp_path: Path, monkeypatch):
    p = tmp_path / ".env"
    p.write_text("MY_TEST_KEY_FROM_DOTENV=hello\n", encoding="utf-8")
    monkeypatch.delenv("MY_TEST_KEY_FROM_DOTENV", raising=False)
    applied = load_dotenv(p)
    assert applied["MY_TEST_KEY_FROM_DOTENV"] == "hello"
    assert os.environ["MY_TEST_KEY_FROM_DOTENV"] == "hello"


def test_load_dotenv_respects_existing_env(tmp_path: Path, monkeypatch):
    p = tmp_path / ".env"
    p.write_text("PRESERVE=from_file\n", encoding="utf-8")
    monkeypatch.setenv("PRESERVE", "from_shell")
    applied = load_dotenv(p)
    assert "PRESERVE" not in applied
    assert os.environ["PRESERVE"] == "from_shell"


def test_load_dotenv_override(tmp_path: Path, monkeypatch):
    p = tmp_path / ".env"
    p.write_text("OVERRIDE_ME=x\n", encoding="utf-8")
    monkeypatch.setenv("OVERRIDE_ME", "old")
    applied = load_dotenv(p, override=True)
    assert applied["OVERRIDE_ME"] == "x"
    assert os.environ["OVERRIDE_ME"] == "x"


def test_load_dotenv_missing_file_returns_empty(tmp_path: Path):
    assert load_dotenv(tmp_path / "nope.env") == {}
