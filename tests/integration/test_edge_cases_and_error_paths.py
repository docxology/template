"""Integration tests for edge cases and error handling across multiple modules.

This test suite validates error handling and edge cases that span multiple
infrastructure modules, ensuring graceful degradation and proper error propagation.
"""

import pytest
from pathlib import Path

from infrastructure.build import build_verifier
from infrastructure.validation import integrity
from infrastructure.build import quality_checker


class TestEdgeCasesAndErrorPaths:
    """Test edge cases and error handling paths across modules."""

    def test_empty_input_handling(self):
        """Test that modules handle empty inputs gracefully."""
        # build_verifier
        assert build_verifier.verify_dependency_consistency([])['files_checked'] == 0
        
        # integrity
        assert len(integrity.verify_file_integrity([])) == 0
        
        # quality_checker
        assert quality_checker.count_syllables("") == 0

    def test_invalid_path_handling(self, tmp_path):
        """Test handling of invalid paths."""
        invalid = tmp_path / "nonexistent" / "path" / "file.txt"
        
        # These should not crash
        assert integrity.calculate_file_hash(invalid) is None

    def test_malformed_data_handling(self, tmp_path):
        """Test handling of malformed data files."""
        bad_json = tmp_path / "bad.json"
        bad_json.write_text("{invalid json}")
        
        # Should handle gracefully
        consistency = integrity.verify_data_consistency([bad_json])
        assert consistency['data_integrity'] == False


