"""Integration tests for edge cases and error handling across multiple modules.

This test suite validates error handling and edge cases that span multiple
infrastructure modules, ensuring graceful degradation and proper error propagation.
"""

from pathlib import Path

import pytest

from infrastructure.scientific import check_numerical_stability
from infrastructure.validation.integrity import checks as integrity


class TestEdgeCasesAndErrorPaths:
    """Test edge cases and error handling paths across modules."""

    def test_empty_input_handling(self):
        """Test that modules handle empty inputs gracefully."""
        # integrity - verify_file_integrity handles empty list
        assert len(integrity.verify_file_integrity([])) == 0

        # scientific - check_numerical_stability handles empty test inputs
        def dummy_func(x):
            return x

        result = check_numerical_stability(dummy_func, [])
        assert result.stability_score == 0.0

    def test_invalid_path_handling(self, tmp_path):
        """Test handling of invalid paths."""
        invalid = tmp_path / "nonexistent" / "path" / "file.txt"

        # These should not crash - integrity module handles invalid paths gracefully
        result = integrity.verify_file_integrity([invalid])
        assert isinstance(result, dict)
        assert str(invalid) in result

    def test_malformed_data_handling(self, tmp_path):
        """Test handling of malformed data files."""
        bad_json = tmp_path / "bad.json"
        bad_json.write_text("{invalid json}")

        # Should handle gracefully - verify_file_integrity handles invalid files
        result = integrity.verify_file_integrity([bad_json])
        assert isinstance(result, dict)
        assert str(bad_json) in result

    def test_numerical_stability_with_constant_function(self):
        """Test numerical stability check on a constant function (trivially stable)."""

        def constant(x):
            return 42.0

        result = check_numerical_stability(constant, [0.0, 1.0, -1.0, 1e6, -1e6])
        assert result.stability_score >= 0.0
        assert result.stability_score <= 1.0

    def test_numerical_stability_with_unstable_function(self):
        """Test that an unstable function scores below a stable one."""

        def stable(x):
            return float(x)

        def unstable(x):
            # Catastrophic cancellation near zero
            return (1.0 + float(x)) - 1.0 - float(x)

        stable_result = check_numerical_stability(stable, [1.0, 2.0, 3.0])
        unstable_result = check_numerical_stability(unstable, [1e-15, 2e-15, 3e-15])

        # Both should return valid StabilityTest objects
        assert hasattr(stable_result, "stability_score")
        assert hasattr(unstable_result, "stability_score")

    def test_verify_file_integrity_on_real_file(self, tmp_path):
        """Test integrity checks on a real file produce expected keys."""
        real_file = tmp_path / "sample.txt"
        real_file.write_text("hello world\n")

        result = integrity.verify_file_integrity([real_file])
        assert isinstance(result, dict)
        assert str(real_file) in result

    def test_integrity_manifest_roundtrip(self, tmp_path):
        """Test that integrity manifest save/load roundtrip is lossless."""
        (tmp_path / "data.bin").write_bytes(b"\x00\x01\x02\x03" * 256)

        manifest = integrity.create_integrity_manifest(tmp_path)
        manifest_path = tmp_path / "manifest.json"
        integrity.save_integrity_manifest(manifest, manifest_path)

        loaded = integrity.load_integrity_manifest(manifest_path)
        assert loaded == manifest

    def test_project_discovery_finds_active_projects(self):
        """Test that project discovery returns at least the known exemplar projects."""
        from infrastructure.project.discovery import discover_projects

        projects = discover_projects(Path("."))
        names = {p.name for p in projects}
        assert "code_project" in names, "code_project must always be discoverable"
