"""Comprehensive tests for infrastructure/publishing/publish_cli.py.

Tests the wrapper CLI script for publishing releases.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from infrastructure.publishing import publish_cli


class TestPublishCliMain:
    """Test suite for publish_cli main function."""
    
    def test_main_basic_publish(self, tmp_path, capsys):
        """Test basic publish execution."""
        # Create mock PDF
        pdf_dir = tmp_path / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "test.pdf").write_bytes(b"%PDF")
        
        mock_url = "https://github.com/owner/repo/releases/tag/v1.0"
        
        with patch('sys.argv', [
            'publish_cli.py',
            '--token', 'test_token',
            '--repo', 'owner/repo',
            '--tag', 'v1.0',
            '--name', 'Release 1.0'
        ]):
            with patch.object(publish_cli, 'publishing') as mock_publishing:
                mock_publishing.create_github_release.return_value = mock_url
                with patch.object(Path, 'glob', return_value=[pdf_dir / "test.pdf"]):
                    with patch('infrastructure.publishing.publish_cli.Path') as mock_path:
                        mock_path.return_value.glob.return_value = [pdf_dir / "test.pdf"]
                        publish_cli.main()
        
        captured = capsys.readouterr()
        assert "Creating release" in captured.out
    
    def test_main_missing_required_args(self, capsys):
        """Test with missing required arguments."""
        with patch('sys.argv', ['publish_cli.py']):
            with pytest.raises(SystemExit):
                publish_cli.main()


class TestPublishCliModule:
    """Test module structure."""
    
    def test_has_main_function(self):
        """Test that module has main function."""
        assert hasattr(publish_cli, 'main')
        assert callable(publish_cli.main)
    
    def test_imports_publishing(self):
        """Test that publishing module is imported."""
        assert hasattr(publish_cli, 'publishing')

