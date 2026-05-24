#!/usr/bin/env python3
"""Tests for infrastructure.core.cache_gate."""

from __future__ import annotations

import os
from pathlib import Path

from infrastructure.core.cache_gate import run_cache_gate


def test_run_cache_gate_fails_without_hermes_home() -> None:
    prior = os.environ.pop("HERMES_HOME", None)
    try:
        assert run_cache_gate() == 1
    finally:
        if prior is not None:
            os.environ["HERMES_HOME"] = prior


def test_run_cache_gate_fails_when_home_missing(tmp_path: Path) -> None:
    missing = tmp_path / "no_hermes"
    prior_home = os.environ.get("HERMES_HOME")
    prior_cache = os.environ.get("HERMES_CACHE_PATH")
    os.environ["HERMES_HOME"] = str(missing)
    try:
        assert run_cache_gate() == 1
    finally:
        if prior_home is None:
            os.environ.pop("HERMES_HOME", None)
        else:
            os.environ["HERMES_HOME"] = prior_home
        if prior_cache is None:
            os.environ.pop("HERMES_CACHE_PATH", None)
        else:
            os.environ["HERMES_CACHE_PATH"] = prior_cache


def test_run_cache_gate_populates_fresh_cache(tmp_path: Path) -> None:
    hermes_home = tmp_path / "hermes"
    plugins = hermes_home / "plugins"
    plugins.mkdir(parents=True)
    (plugins / "manifest.json").write_text("{}\n")
    cache_path = tmp_path / "cache"

    prior = {
        key: os.environ.get(key)
        for key in ("HERMES_HOME", "HERMES_CACHE_PATH", "CACHE_TTL_SECONDS")
    }
    os.environ["HERMES_HOME"] = str(hermes_home)
    os.environ["HERMES_CACHE_PATH"] = str(cache_path)
    os.environ["CACHE_TTL_SECONDS"] = "3600"
    try:
        assert run_cache_gate() == 0
        assert (cache_path / "cache_metadata.json").is_file()
        assert (cache_path / ".cache_valid").is_file()
    finally:
        for key, value in prior.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
