import pytest
import requests
from unittest.mock import MagicMock
from infrastructure.literature.api import ArxivSource, SemanticScholarSource, SearchResult
from infrastructure.core.exceptions import LiteratureSearchError, APIRateLimitError

class TestArxivSource:
    def test_search_success(self, mock_config, mock_requests_get):
        # Mock XML response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
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
        mock_requests_get.return_value = mock_response

        source = ArxivSource(mock_config)
        results = source.search("query")

        assert len(results) == 1
        assert results[0].title == "Test Paper"
        assert results[0].year == 2021
        assert results[0].pdf_url == "http://arxiv.org/pdf/2101.00001"

    def test_search_failure(self, mock_config, mock_requests_get):
        mock_requests_get.side_effect = requests.exceptions.RequestException("Error")
        source = ArxivSource(mock_config)

        with pytest.raises(LiteratureSearchError):
            source.search("query")

class TestSemanticScholarSource:
    def test_search_success(self, mock_config, mock_requests_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
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
        mock_requests_get.return_value = mock_response

        source = SemanticScholarSource(mock_config)
        results = source.search("query")

        assert len(results) == 1
        assert results[0].doi == "10.1234/5678"

    def test_rate_limit(self, mock_config, mock_requests_get):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_requests_get.return_value = mock_response

        source = SemanticScholarSource(mock_config)
        with pytest.raises(APIRateLimitError):
            source.search("query")

