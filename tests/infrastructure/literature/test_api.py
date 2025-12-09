import pytest
import requests
from infrastructure.literature.sources import ArxivSource, SemanticScholarSource, SearchResult
from infrastructure.core.exceptions import LiteratureSearchError, APIRateLimitError


class TestArxivSource:
    def test_xml_parsing_logic(self, mock_config):
        """Test Arxiv XML response parsing logic without network calls."""
        source = ArxivSource(mock_config)

        # Test XML parsing directly by calling the internal method
        xml_response = """
        <feed xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <id>http://arxiv.org/abs/2101.00001</id>
                <title>Test Paper</title>
                <summary>Abstract</summary>
                <published>2021-01-01T00:00:00Z</published>
                <author><name>Author One</name></author>
                <link title="pdf" href="http://arxiv.org/pdf/2101.00001" />
            </entry>
        </feed>
        """

        # Test the XML parsing logic directly
        results = source._parse_response(xml_response)

        assert len(results) == 1
        assert results[0].title == "Test Paper"
        assert results[0].year == 2021
        assert results[0].pdf_url == "http://arxiv.org/pdf/2101.00001"
        assert results[0].source == "arxiv"

    def test_search_error_handling(self, mock_config):
        """Test error handling in search method."""
        source = ArxivSource(mock_config)

        # Test with invalid XML
        invalid_xml = "<invalid>xml</invalid>"
        results = source._parse_response(invalid_xml)
        assert results == []  # Should handle gracefully

    @pytest.mark.integration
    def test_search_network_call(self, mock_config):
        """Integration test for actual Arxiv API call."""
        source = ArxivSource(mock_config)
        # This would make real network calls - skip in normal testing
        results = source.search("machine learning", limit=1)
        # Just check that it returns a list (may be empty if rate limited)
        assert isinstance(results, list)

class TestSemanticScholarSource:
    def test_json_parsing_logic(self, mock_config):
        """Test Semantic Scholar JSON response parsing logic without network calls."""
        source = SemanticScholarSource(mock_config)

        # Test JSON parsing directly
        json_data = {
            "data": [{
                "title": "Test Paper",
                "authors": [{"name": "Author One"}],
                "year": 2021,
                "abstract": "Abstract",
                "url": "http://url",
                "externalIds": {"DOI": "10.1234/5678"},
                "isOpenAccess": True,
                "openAccessPdf": {"url": "http://pdf"}
            }]
        }

        results = source._parse_response(json_data)

        assert len(results) == 1
        assert results[0].title == "Test Paper"
        assert results[0].doi == "10.1234/5678"
        assert results[0].pdf_url == "http://pdf"
        assert results[0].source == "semanticscholar"

    def test_json_parsing_empty_response(self, mock_config):
        """Test parsing empty Semantic Scholar response."""
        source = SemanticScholarSource(mock_config)

        json_data = {"data": []}
        results = source._parse_response(json_data)
        assert results == []

