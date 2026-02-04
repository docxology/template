"""Edge case tests for integrity module.

This test suite validates edge cases including hash mismatches, missing
cross-references, permission checks, and validation for missing categories.
"""

from pathlib import Path

import pytest

from infrastructure.validation import integrity


class TestIntegrityEdgeCases:
    """Edge case tests for integrity module."""

    def test_verify_file_integrity_with_mismatched_hash(self, tmp_path):
        """Test integrity verification with hash mismatch."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Original content")

        # Calculate hash for original
        original_hash = integrity.calculate_file_hash(test_file)

        # Modify file
        test_file.write_text("Modified content")

        # Verify with old hash should fail
        expected_hashes = {str(test_file): original_hash}
        integrity_status = integrity.verify_file_integrity([test_file], expected_hashes)

        assert integrity_status[str(test_file)] == False

    def test_verify_cross_references_missing_figure_labels(self, tmp_path):
        """Test cross-reference verification with missing figure labels."""
        md_file = tmp_path / "test.md"
        md_file.write_text(
            r"""
        # Test {#sec:test}
        
        See Figure \ref{fig:missing}.
        """
        )

        integrity_status = integrity.verify_cross_references([md_file])

        assert integrity_status["figures"] == False

    def test_check_file_permissions_nonexistent(self, tmp_path):
        """Test permission check for nonexistent path."""
        nonexistent = tmp_path / "nonexistent"

        permissions = integrity.check_file_permissions(nonexistent)

        assert permissions["readable"] == False
        # Nonexistent paths may be writable (parent directory permission)
        assert len(permissions["issues"]) > 0

    def test_validate_build_artifacts_missing_category(self, tmp_path):
        """Test artifact validation with completely missing category."""
        expected_files = {
            "pdf": ["test.pdf"],
            "figures": ["test.png"],
            "nonexistent_category": ["file.dat"],
        }

        validation = integrity.validate_build_artifacts(tmp_path, expected_files)

        assert validation["validation_passed"] == False
        assert len(validation["missing_files"]) > 0
