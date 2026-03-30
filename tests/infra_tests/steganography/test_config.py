"""Tests for SteganographyConfig dataclass."""

from __future__ import annotations


class TestSteganographyConfig:
    def test_default_config_disabled(self):
        from infrastructure.steganography.config import SteganographyConfig

        config = SteganographyConfig()
        assert config.enabled is False
        assert config.overlays_enabled is True
        assert config.barcodes_enabled is True
        assert config.metadata_enabled is True
        assert config.hashing_enabled is True
        assert config.encryption_enabled is False

    def test_all_enabled(self):
        from infrastructure.steganography.config import SteganographyConfig

        config = SteganographyConfig.all_enabled()
        assert config.enabled is True
        assert config.overlays_enabled is True
        assert config.encryption_enabled is True

    def test_from_dict_basic(self):
        from infrastructure.steganography.config import SteganographyConfig

        config = SteganographyConfig.from_dict({"enabled": True, "overlays": False, "barcodes": True})
        assert config.enabled is True
        assert config.overlays_enabled is False
        assert config.barcodes_enabled is True

    def test_from_dict_empty(self):
        from infrastructure.steganography.config import SteganographyConfig

        assert SteganographyConfig.from_dict({}).enabled is False

    def test_from_dict_none(self):
        from infrastructure.steganography.config import SteganographyConfig

        assert SteganographyConfig.from_dict(None).enabled is False

    def test_from_dict_unknown_keys_ignored(self):
        from infrastructure.steganography.config import SteganographyConfig

        config = SteganographyConfig.from_dict({"enabled": True, "unknown_key": "value"})
        assert config.enabled is True

    def test_from_dict_canonical_names(self):
        from infrastructure.steganography.config import SteganographyConfig

        config = SteganographyConfig.from_dict({"enabled": True, "overlays_enabled": False, "encryption_enabled": True})
        assert config.overlays_enabled is False
        assert config.encryption_enabled is True

    def test_default_hash_algorithms(self):
        from infrastructure.steganography.config import SteganographyConfig

        config = SteganographyConfig()
        assert "sha256" in config.hash_algorithms
        assert "sha512" in config.hash_algorithms

    def test_overlay_defaults(self):
        from infrastructure.steganography.config import SteganographyConfig

        config = SteganographyConfig()
        assert config.overlay_text == "CONFIDENTIAL"
        assert 0.0 < config.overlay_opacity < 1.0
        assert config.output_suffix == "_steganography"
