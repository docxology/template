"""Comprehensive tests for infrastructure/publishing/api.py.

Tests publishing API functionality comprehensively.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from infrastructure.publishing import api
from infrastructure.publishing.api import ZenodoConfig, ZenodoClient


class TestPublishingApiImport:
    """Test module import."""
    
    def test_module_imports(self):
        """Test that module imports correctly."""
        assert api is not None
    
    def test_module_attributes(self):
        """Test module has expected attributes."""
        module_attrs = [a for a in dir(api) if not a.startswith('_')]
        assert len(module_attrs) > 0


class TestZenodoConfig:
    """Test ZenodoConfig dataclass."""
    
    def test_sandbox_url(self):
        """Test sandbox URL."""
        config = ZenodoConfig(access_token="test", sandbox=True)
        assert "sandbox" in config.base_url
    
    def test_production_url(self):
        """Test production URL."""
        config = ZenodoConfig(access_token="test", sandbox=False)
        assert "sandbox" not in config.base_url
    
    def test_access_token(self):
        """Test access token is stored."""
        config = ZenodoConfig(access_token="my_token")
        assert config.access_token == "my_token"


class TestZenodoClient:
    """Test ZenodoClient class."""
    
    def test_init(self):
        """Test client initialization."""
        config = ZenodoConfig(access_token="test")
        client = ZenodoClient(config)
        
        assert client.config == config
        assert "Bearer test" in client.headers["Authorization"]
    
    def test_create_deposition_success(self):
        """Test successful deposition creation."""
        config = ZenodoConfig(access_token="test")
        client = ZenodoClient(config)
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {'id': 12345}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            
            result = client.create_deposition({'title': 'Test'})
            
            assert result == '12345'
    
    def test_create_deposition_failure(self):
        """Test deposition creation failure."""
        from infrastructure.core.exceptions import PublishingError
        import requests
        
        config = ZenodoConfig(access_token="test")
        client = ZenodoClient(config)
        
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.RequestException("Network error")
            
            with pytest.raises(PublishingError):
                client.create_deposition({'title': 'Test'})
    
    def test_upload_file_success(self, tmp_path):
        """Test successful file upload."""
        config = ZenodoConfig(access_token="test")
        client = ZenodoClient(config)
        
        # Create test file
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF content")
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            
            # Should not raise
            client.upload_file("123", str(test_file))
    
    def test_upload_file_not_found(self, tmp_path):
        """Test upload with missing file."""
        from infrastructure.core.exceptions import UploadError
        
        config = ZenodoConfig(access_token="test")
        client = ZenodoClient(config)
        
        with pytest.raises(UploadError):
            client.upload_file("123", str(tmp_path / "missing.pdf"))
    
    def test_publish_success(self):
        """Test successful publication."""
        config = ZenodoConfig(access_token="test")
        client = ZenodoClient(config)
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {'doi': '10.5281/zenodo.12345'}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            
            result = client.publish("123")
            
            assert result == '10.5281/zenodo.12345'
    
    def test_publish_failure(self):
        """Test publication failure."""
        from infrastructure.core.exceptions import PublishingError
        import requests
        
        config = ZenodoConfig(access_token="test")
        client = ZenodoClient(config)
        
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.RequestException("Publish failed")
            
            with pytest.raises(PublishingError):
                client.publish("123")


class TestPublishingApiIntegration:
    """Integration tests for publishing API."""
    
    def test_module_structure(self):
        """Test module has expected structure."""
        # Should have ZenodoClient
        assert hasattr(api, 'ZenodoClient')
        assert hasattr(api, 'ZenodoConfig')
    
    def test_full_workflow(self, tmp_path):
        """Test complete publishing workflow."""
        config = ZenodoConfig(access_token="test")
        client = ZenodoClient(config)
        
        # Create test file
        test_file = tmp_path / "paper.pdf"
        test_file.write_bytes(b"%PDF content")
        
        with patch('requests.post') as mock_post:
            # Create mock responses for each call
            create_response = MagicMock()
            create_response.json.return_value = {'id': 123}
            create_response.raise_for_status = MagicMock()
            
            upload_response = MagicMock()
            upload_response.raise_for_status = MagicMock()
            
            publish_response = MagicMock()
            publish_response.json.return_value = {'doi': '10.5281/zenodo.123'}
            publish_response.raise_for_status = MagicMock()
            
            mock_post.side_effect = [create_response, upload_response, publish_response]
            
            dep_id = client.create_deposition({'title': 'Test'})
            client.upload_file(dep_id, str(test_file))
            doi = client.publish(dep_id)
            
            assert dep_id == '123'
            assert '10.5281' in doi

