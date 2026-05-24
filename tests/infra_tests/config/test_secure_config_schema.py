"""Tests for repository secure_config.yaml schema expectations."""

from __future__ import annotations

from pathlib import Path

import yaml

from infrastructure.orchestration.secure_run import _load_repo_secure_config


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_secure_config_yaml_loads_steganography_block() -> None:
    config_path = _repo_root() / "infrastructure" / "config" / "secure_config.yaml"
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    stego = data.get("steganography")
    assert isinstance(stego, dict)
    assert stego.get("enabled") is True
    assert stego.get("overlay_mode") in {"text", "qr", "none"}
    assert isinstance(stego.get("hash_algorithms"), list)
    assert "sha256" in stego["hash_algorithms"]


def test_load_repo_secure_config_returns_mapping() -> None:
    loaded = _load_repo_secure_config(_repo_root())
    assert isinstance(loaded, dict)
    assert loaded.get("enabled") is True
    assert "overlay_mode" in loaded
