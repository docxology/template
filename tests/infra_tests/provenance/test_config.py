"""Real-behavior tests for infrastructure.provenance.config — load_provenance_config and ProvenanceConfig."""

from __future__ import annotations


import pytest

from infrastructure.provenance.config import ProvenanceConfig, load_provenance_config


class TestProvenanceConfigDefaults:
    """Tests for default ProvenanceConfig values."""

    def test_defaults(self):
        """Default config has expected values."""
        c = ProvenanceConfig()
        assert c.enabled is True
        assert c.output_dir == "output/provenance"
        assert c.filename == "dag.json"
        assert c.auto_hash_artifacts is False
        assert c.source_path == ""

    def test_dag_path(self, tmp_path):
        """dag_path() joins project dir, output_dir, and filename."""
        c = ProvenanceConfig(output_dir="custom", filename="graph.json")
        assert c.dag_path(tmp_path) == tmp_path / "custom" / "graph.json"

    def test_dag_path_default(self, tmp_path):
        """dag_path() with defaults produces output/provenance/dag.json."""
        c = ProvenanceConfig()
        assert c.dag_path(tmp_path) == tmp_path / "output" / "provenance" / "dag.json"

    def test_to_dict(self):
        """to_dict() returns all config fields."""
        c = ProvenanceConfig(enabled=False, output_dir="out", filename="g.json", auto_hash_artifacts=True)
        d = c.to_dict()
        assert d == {
            "enabled": False,
            "output_dir": "out",
            "filename": "g.json",
            "auto_hash_artifacts": True,
        }

    def test_to_dict_round_trip(self):
        """to_dict() values match the config that produced them."""
        c = ProvenanceConfig(enabled=True, auto_hash_artifacts=True)
        d = c.to_dict()
        assert d["enabled"] is True
        assert d["auto_hash_artifacts"] is True


class TestLoadProvenanceConfig:
    """Tests for load_provenance_config()."""

    def test_missing_file_returns_defaults(self, tmp_path):
        """Missing provenance.yaml returns defaults with empty source_path."""
        c = load_provenance_config(tmp_path)
        assert c.enabled is True
        assert c.output_dir == "output/provenance"
        assert c.filename == "dag.json"
        assert c.auto_hash_artifacts is False
        assert c.source_path == ""

    def test_load_yaml(self, tmp_path):
        """Loading a valid YAML config populates all fields."""
        content = "enabled: false\noutput_dir: custom\nfilename: graph.json\nauto_hash_artifacts: true\n"
        (tmp_path / "provenance.yaml").write_text(content, encoding="utf-8")
        c = load_provenance_config(tmp_path)
        assert c.enabled is False
        assert c.output_dir == "custom"
        assert c.filename == "graph.json"
        assert c.auto_hash_artifacts is True
        assert c.source_path == str(tmp_path / "provenance.yaml")

    def test_load_partial_config(self, tmp_path):
        """Loading a partial config uses defaults for missing keys."""
        (tmp_path / "provenance.yaml").write_text("enabled: false\n", encoding="utf-8")
        c = load_provenance_config(tmp_path)
        assert c.enabled is False
        assert c.output_dir == "output/provenance"  # default
        assert c.filename == "dag.json"  # default

    def test_unknown_key_raises(self, tmp_path):
        """Unknown config key raises ValueError."""
        (tmp_path / "provenance.yaml").write_text("foo: bar\n", encoding="utf-8")
        with pytest.raises(ValueError, match="unknown provenance key"):
            load_provenance_config(tmp_path)

    def test_non_bool_enabled_raises(self, tmp_path):
        """Non-boolean enabled value raises ValueError."""
        (tmp_path / "provenance.yaml").write_text('enabled: "yes"\n', encoding="utf-8")
        with pytest.raises(ValueError, match="must be a boolean"):
            load_provenance_config(tmp_path)

    def test_non_bool_auto_hash_raises(self, tmp_path):
        """Non-boolean auto_hash_artifacts value raises ValueError."""
        (tmp_path / "provenance.yaml").write_text('auto_hash_artifacts: "true"\n', encoding="utf-8")
        with pytest.raises(ValueError, match="must be a boolean"):
            load_provenance_config(tmp_path)

    def test_non_mapping_raises(self, tmp_path):
        """Non-mapping YAML content raises ValueError."""
        (tmp_path / "provenance.yaml").write_text("- item1\n- item2\n", encoding="utf-8")
        with pytest.raises(ValueError, match="must be a mapping"):
            load_provenance_config(tmp_path)

    def test_empty_file_returns_defaults(self, tmp_path):
        """Empty provenance.yaml returns defaults with source_path set."""
        (tmp_path / "provenance.yaml").write_text("", encoding="utf-8")
        c = load_provenance_config(tmp_path)
        assert c.enabled is True
        assert c.source_path == str(tmp_path / "provenance.yaml")

    def test_json_fallback(self, tmp_path, monkeypatch):
        """When PyYAML is unavailable, falls back to JSON parsing."""
        (tmp_path / "provenance.yaml").write_text(
            '{"enabled": false, "output_dir": "json_out", "filename": "j.json", "auto_hash_artifacts": true}',
            encoding="utf-8",
        )
        # Simulate yaml being unavailable
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "yaml":
                raise ImportError("yaml not available")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)
        c = load_provenance_config(tmp_path)
        assert c.enabled is False
        assert c.output_dir == "json_out"
        assert c.filename == "j.json"
        assert c.auto_hash_artifacts is True
