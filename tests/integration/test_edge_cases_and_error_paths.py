"""Integration tests for edge cases and error handling across multiple modules.

This test suite validates error handling and edge cases that span multiple
infrastructure modules, ensuring graceful degradation and proper error propagation.
"""

import pytest
from pathlib import Path

from infrastructure.validation import integrity
from infrastructure.scientific import check_numerical_stability


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
        # Note: calculate_file_hash may not exist, so we test verify_file_integrity instead
        result = integrity.verify_file_integrity([invalid])
        # Should return a list (may be empty or contain error info)
        assert isinstance(result, list)

    def test_malformed_data_handling(self, tmp_path):
        """Test handling of malformed data files."""
        bad_json = tmp_path / "bad.json"
        bad_json.write_text("{invalid json}")
        
        # Should handle gracefully - verify_file_integrity handles invalid files
        result = integrity.verify_file_integrity([bad_json])
        # Result should be a list, may be empty or contain error info
        assert isinstance(result, list)
















