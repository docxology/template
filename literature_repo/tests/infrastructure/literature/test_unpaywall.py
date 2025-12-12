"""Tests for Unpaywall integration.

Tests the UnpaywallSource class and UnpaywallResult dataclass.
Pure logic tests - no network access required.
"""
import pytest
from unittest.mock import patch, MagicMock

from infrastructure.literature.core import LiteratureConfig
from infrastructure.literature.sources import UnpaywallSource, UnpaywallResult


class TestUnpaywallResult:
    """Tests for UnpaywallResult dataclass."""

    def test_result_creation(self):
        """Test basic UnpaywallResult creation."""
        result = UnpaywallResult(
            doi="10.1038/nature12373",
            is_oa=True,
            pdf_url="https://example.com/paper.pdf"
        )
        
        assert result.doi == "10.1038/nature12373"
        assert result.is_oa is True
        assert result.pdf_url == "https://example.com/paper.pdf"

    def test_result_with_all_fields(self):
        """Test UnpaywallResult with all fields."""
        result = UnpaywallResult(
            doi="10.1038/nature12373",
            is_oa=True,
            pdf_url="https://example.com/paper.pdf",
            oa_status="gold",
            host_type="publisher",
            version="publishedVersion",
            license="cc-by"
        )
        
        assert result.oa_status == "gold"
        assert result.host_type == "publisher"
        assert result.version == "publishedVersion"
        assert result.license == "cc-by"

    def test_result_closed_access(self):
        """Test UnpaywallResult for closed access paper."""
        result = UnpaywallResult(
            doi="10.1016/j.example.2024.12345",
            is_oa=False,
            oa_status="closed"
        )
        
        assert result.is_oa is False
        assert result.pdf_url is None
        assert result.oa_status == "closed"


class TestUnpaywallSource:
    """Tests for UnpaywallSource class."""

    def test_init_with_email(self):
        """Test UnpaywallSource initialization with email."""
        config = LiteratureConfig(
            use_unpaywall=True,
            unpaywall_email="test@example.com"
        )
        source = UnpaywallSource(config)
        
        assert source.config.unpaywall_email == "test@example.com"

    def test_init_without_email_warns(self):
        """Test UnpaywallSource warns when email not configured."""
        config = LiteratureConfig(
            use_unpaywall=True,
            unpaywall_email=""
        )
        
        # Creating the source should work without error
        source = UnpaywallSource(config)
        
        # The source should still be created, just with warning logged
        assert source is not None
        assert source.config.unpaywall_email == ""

    def test_lookup_without_email_returns_none(self):
        """Test lookup returns None when email not configured."""
        config = LiteratureConfig(unpaywall_email="")
        source = UnpaywallSource(config)
        
        result = source.lookup("10.1038/nature12373")
        
        assert result is None

    def test_get_pdf_url_without_email_returns_none(self):
        """Test get_pdf_url returns None when email not configured."""
        config = LiteratureConfig(unpaywall_email="")
        source = UnpaywallSource(config)
        
        url = source.get_pdf_url("10.1038/nature12373")
        
        assert url is None

    def test_doi_cleaning_url_prefix(self):
        """Test DOI cleaning removes URL prefix."""
        config = LiteratureConfig(unpaywall_email="test@example.com")
        source = UnpaywallSource(config)
        
        # Mock the request to verify cleaned DOI
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            
            source.lookup("https://doi.org/10.1038/nature12373")
            
            # Check the URL called
            call_url = mock_get.call_args[0][0]
            assert "10.1038/nature12373" in call_url
            assert "https://doi.org" not in call_url

    def test_doi_cleaning_http_prefix(self):
        """Test DOI cleaning removes http prefix."""
        config = LiteratureConfig(unpaywall_email="test@example.com")
        source = UnpaywallSource(config)
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            
            source.lookup("http://doi.org/10.1038/nature12373")
            
            call_url = mock_get.call_args[0][0]
            assert "10.1038/nature12373" in call_url

    def test_doi_cleaning_doi_prefix(self):
        """Test DOI cleaning removes doi: prefix."""
        config = LiteratureConfig(unpaywall_email="test@example.com")
        source = UnpaywallSource(config)
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            
            source.lookup("doi:10.1038/nature12373")
            
            call_url = mock_get.call_args[0][0]
            assert "10.1038/nature12373" in call_url

    def test_parse_response_open_access(self):
        """Test parsing open access response."""
        config = LiteratureConfig(unpaywall_email="test@example.com")
        source = UnpaywallSource(config)
        
        data = {
            "doi": "10.1038/nature12373",
            "is_oa": True,
            "oa_status": "gold",
            "best_oa_location": {
                "url_for_pdf": "https://example.com/paper.pdf",
                "host_type": "publisher",
                "version": "publishedVersion",
                "license": "cc-by"
            }
        }
        
        result = source._parse_response(data)
        
        assert result.doi == "10.1038/nature12373"
        assert result.is_oa is True
        assert result.pdf_url == "https://example.com/paper.pdf"
        assert result.oa_status == "gold"
        assert result.host_type == "publisher"

    def test_parse_response_closed_access(self):
        """Test parsing closed access response."""
        config = LiteratureConfig(unpaywall_email="test@example.com")
        source = UnpaywallSource(config)
        
        data = {
            "doi": "10.1016/j.example.2024.12345",
            "is_oa": False,
            "oa_status": "closed",
            "best_oa_location": None
        }
        
        result = source._parse_response(data)
        
        assert result.is_oa is False
        assert result.pdf_url is None
        assert result.oa_status == "closed"

    def test_parse_response_fallback_to_oa_locations(self):
        """Test parsing falls back to oa_locations when best_oa_location has no PDF."""
        config = LiteratureConfig(unpaywall_email="test@example.com")
        source = UnpaywallSource(config)
        
        data = {
            "doi": "10.1038/nature12373",
            "is_oa": True,
            "oa_status": "green",
            "best_oa_location": {
                "url_for_pdf": None,
                "host_type": "publisher"
            },
            "oa_locations": [
                {
                    "url_for_pdf": "https://repository.example.com/paper.pdf",
                    "host_type": "repository",
                    "version": "acceptedVersion"
                }
            ]
        }
        
        result = source._parse_response(data)
        
        assert result.pdf_url == "https://repository.example.com/paper.pdf"
        assert result.host_type == "repository"

    def test_lookup_handles_404(self):
        """Test lookup handles 404 (DOI not found)."""
        config = LiteratureConfig(unpaywall_email="test@example.com")
        source = UnpaywallSource(config)
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            
            result = source.lookup("10.0000/nonexistent")
            
            assert result is None

    def test_lookup_handles_request_exception(self):
        """Test lookup handles request exceptions gracefully."""
        import requests
        
        config = LiteratureConfig(unpaywall_email="test@example.com")
        source = UnpaywallSource(config)
        
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
            
            result = source.lookup("10.1038/nature12373")
            
            assert result is None


class TestUnpaywallIntegration:
    """Integration tests for Unpaywall with PDFHandler."""

    def test_config_enables_unpaywall(self):
        """Test config properly enables Unpaywall."""
        config = LiteratureConfig(
            use_unpaywall=True,
            unpaywall_email="test@example.com"
        )
        
        assert config.use_unpaywall is True
        assert config.unpaywall_email == "test@example.com"

    def test_pdf_handler_creates_unpaywall_source_when_enabled(self):
        """Test PDFHandler creates UnpaywallSource when enabled."""
        from infrastructure.literature.pdf import PDFHandler
        
        config = LiteratureConfig(
            use_unpaywall=True,
            unpaywall_email="test@example.com"
        )
        handler = PDFHandler(config)
        
        assert handler._fallbacks._unpaywall is not None
        assert isinstance(handler._fallbacks._unpaywall, UnpaywallSource)

    def test_pdf_handler_no_unpaywall_when_disabled(self):
        """Test PDFHandler doesn't create UnpaywallSource when disabled."""
        from infrastructure.literature.pdf import PDFHandler
        
        config = LiteratureConfig(
            use_unpaywall=False,
            unpaywall_email=""
        )
        handler = PDFHandler(config)
        
        assert handler._fallbacks._unpaywall is None

    def test_pdf_handler_no_unpaywall_without_email(self):
        """Test PDFHandler doesn't create UnpaywallSource without email."""
        from infrastructure.literature.pdf import PDFHandler
        
        config = LiteratureConfig(
            use_unpaywall=True,
            unpaywall_email=""  # Missing email
        )
        handler = PDFHandler(config)
        
        assert handler._fallbacks._unpaywall is None


class TestUnpaywallHealthMethods:
    """Tests for UnpaywallSource health check methods."""

    def test_get_health_status_returns_proper_format(self):
        """Test get_health_status() returns proper format."""
        config = LiteratureConfig(unpaywall_email="test@example.com")
        source = UnpaywallSource(config)
        
        status = source.get_health_status()
        
        assert isinstance(status, dict)
        assert "healthy" in status
        assert "consecutive_failures" in status
        assert "last_request_time" in status
        assert "source_name" in status
        assert status["source_name"] == "UnpaywallSource"
        assert isinstance(status["healthy"], bool)
        assert isinstance(status["consecutive_failures"], int)
        assert isinstance(status["last_request_time"], float)

    def test_get_health_status_initial_state(self):
        """Test get_health_status() initial state is healthy."""
        config = LiteratureConfig(unpaywall_email="test@example.com")
        source = UnpaywallSource(config)
        
        status = source.get_health_status()
        
        assert status["healthy"] is True
        assert status["consecutive_failures"] == 0

    def test_is_healthy_property_initial(self):
        """Test is_healthy property is True initially."""
        config = LiteratureConfig(unpaywall_email="test@example.com")
        source = UnpaywallSource(config)
        
        assert source.is_healthy is True

    def test_is_healthy_after_failures(self):
        """Test is_healthy becomes False after multiple failures."""
        config = LiteratureConfig(unpaywall_email="test@example.com")
        source = UnpaywallSource(config)
        
        # Simulate failures
        source._consecutive_failures = 2
        assert source.is_healthy is True  # Still healthy (< 3)
        
        source._consecutive_failures = 3
        assert source.is_healthy is False  # Now unhealthy (>= 3)

    def test_check_health_success(self):
        """Test check_health() returns True on successful lookup."""
        config = LiteratureConfig(unpaywall_email="test@example.com")
        source = UnpaywallSource(config)
        
        # Mock successful response (even 404 means API is responding)
        with patch.object(source, 'lookup') as mock_lookup:
            mock_lookup.return_value = None  # 404 response
            result = source.check_health()
            
            assert result is True
            assert source._consecutive_failures == 0

    def test_check_health_with_result(self):
        """Test check_health() returns True when lookup returns result."""
        config = LiteratureConfig(unpaywall_email="test@example.com")
        source = UnpaywallSource(config)
        
        # Mock successful response with result
        mock_result = UnpaywallResult(
            doi="10.1038/nature12373",
            is_oa=True,
            pdf_url="https://example.com/paper.pdf"
        )
        
        with patch.object(source, 'lookup') as mock_lookup:
            mock_lookup.return_value = mock_result
            result = source.check_health()
            
            assert result is True
            assert source._consecutive_failures == 0

    def test_check_health_failure(self):
        """Test check_health() returns False on exception."""
        config = LiteratureConfig(unpaywall_email="test@example.com")
        source = UnpaywallSource(config)
        
        # Mock exception
        with patch.object(source, 'lookup') as mock_lookup:
            mock_lookup.side_effect = Exception("Network error")
            result = source.check_health()
            
            assert result is False
            assert source._consecutive_failures == 1

    def test_consecutive_failures_tracking(self):
        """Test consecutive failures are tracked correctly."""
        config = LiteratureConfig(unpaywall_email="test@example.com")
        source = UnpaywallSource(config)
        
        assert source._consecutive_failures == 0
        
        # Simulate a failed lookup
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            source.lookup("10.1038/nature12373")
            
            assert source._consecutive_failures > 0

    def test_consecutive_failures_reset_on_success(self):
        """Test consecutive failures reset on successful lookup."""
        config = LiteratureConfig(unpaywall_email="test@example.com")
        source = UnpaywallSource(config)
        
        # Set failures
        source._consecutive_failures = 2
        
        # Mock successful lookup
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "doi": "10.1038/nature12373",
                "is_oa": True
            }
            mock_get.return_value = mock_response
            
            source.lookup("10.1038/nature12373")
            
            assert source._consecutive_failures == 0

    def test_health_status_integration_with_literature_search(self):
        """Test health status integration with LiteratureSearch."""
        from infrastructure.literature.core import LiteratureSearch
        
        config = LiteratureConfig(
            use_unpaywall=True,
            unpaywall_email="test@example.com"
        )
        search = LiteratureSearch(config)
        
        # Should not raise AttributeError
        health_status = search.get_source_health_status()
        
        assert "unpaywall" in health_status
        assert isinstance(health_status["unpaywall"], dict)
        assert "healthy" in health_status["unpaywall"]

    def test_health_status_without_email(self):
        """Test health status when email not configured."""
        config = LiteratureConfig(unpaywall_email="")
        source = UnpaywallSource(config)
        
        status = source.get_health_status()
        
        # Should still return valid status format
        assert isinstance(status, dict)
        assert "healthy" in status
        # Health check will fail without email, but status should still be returned
        assert status["consecutive_failures"] == 0  # Initial state

