"""Comprehensive tests for HTML parsing functionality in literature module.

Tests the _extract_pdf_urls_from_html function and related HTML parsing capabilities.
"""

import pytest
from infrastructure.literature.pdf import extract_pdf_urls_from_html, PDFHandler
from infrastructure.literature.core import LiteratureConfig


class TestExtractPDFUrlsFromHTML:
    """Test the _extract_pdf_urls_from_html function."""

    def test_extract_pdf_urls_basic_href(self):
        """Test basic PDF URL extraction from <a> tags."""
        html = b"""
        <html>
        <body>
            <a href="https://example.com/paper.pdf">Download PDF</a>
            <a href="https://example.com/paper2.pdf">Another PDF</a>
            <a href="https://example.com/other.txt">Not a PDF</a>
        </body>
        </html>
        """

        urls = extract_pdf_urls_from_html(html, "https://example.com")
        expected = [
            "https://example.com/paper.pdf",
            "https://example.com/paper2.pdf"
        ]

        assert urls == expected

    def test_extract_pdf_urls_case_insensitive(self):
        """Test case-insensitive PDF extension detection."""
        html = b"""
        <html>
        <body>
            <a href="https://example.com/paper.PDF">Uppercase PDF</a>
            <a href="https://example.com/paper.Pdf">Mixed case PDF</a>
        </body>
        </html>
        """

        urls = extract_pdf_urls_from_html(html, "https://example.com")
        expected = [
            "https://example.com/paper.PDF",
            "https://example.com/paper.Pdf"
        ]

        # Sort both lists for consistent comparison since order might vary
        assert sorted(urls) == sorted(expected)

    def test_extract_pdf_urls_meta_tags(self):
        """Test PDF URL extraction from meta tags."""
        html = b"""
        <html>
        <head>
            <meta name="citation_pdf_url" content="https://example.com/meta.pdf">
            <meta property="og:url" content="https://example.com/paper.pdf">
        </head>
        </html>
        """

        urls = extract_pdf_urls_from_html(html, "https://example.com")
        assert "https://example.com/meta.pdf" in urls
        assert "https://example.com/paper.pdf" in urls

    def test_extract_pdf_urls_javascript_variables(self):
        """Test PDF URL extraction from JavaScript variables."""
        html = b"""
        <html>
        <script>
            var pdfUrl = "https://example.com/js_var.pdf";
            const downloadUrl = 'https://example.com/const.pdf';
            let pdf = "https://example.com/let.pdf";
        </script>
        </html>
        """

        urls = extract_pdf_urls_from_html(html, "https://example.com")
        expected = [
            "https://example.com/js_var.pdf",
            "https://example.com/const.pdf",
            "https://example.com/let.pdf"
        ]

        for url in expected:
            assert url in urls

    def test_extract_pdf_urls_publisher_patterns(self):
        """Test publisher-specific PDF URL patterns."""
        # Elsevier/ScienceDirect pattern
        html_elsevier = b"""
        <html>
        <script>
            var pii = "S1234567890123456";
        </script>
        </html>
        """

        urls = extract_pdf_urls_from_html(html_elsevier, "https://www.sciencedirect.com")
        assert "https://www.sciencedirect.com/science/article/pii/S1234567890123456/pdfft?isDTMRedir=true&download=true" in urls

        # Springer pattern
        html_springer = b"""
        <html>
        <body>
            <a href="/chapter/pdf/10.1007/978-3-030-12345-6_1">Chapter PDF</a>
        </body>
        </html>
        """

        urls = extract_pdf_urls_from_html(html_springer, "https://link.springer.com")
        # The HTML contains /chapter/pdf/, which gets resolved to the full URL
        assert "https://link.springer.com/chapter/pdf/10.1007/978-3-030-12345-6_1" in urls

        # IEEE pattern
        html_ieee = b"""
        <html>
        <script>
            var arnumber = "1234567";
        </script>
        </html>
        """

        urls = extract_pdf_urls_from_html(html_ieee, "https://ieeexplore.ieee.org")
        assert "https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?arnumber=1234567" in urls

    def test_extract_pdf_urls_relative_urls(self):
        """Test resolution of relative URLs."""
        html = b"""
        <html>
        <body>
            <a href="/downloads/paper.pdf">Relative PDF</a>
            <a href="paper2.pdf">Simple relative PDF</a>
            <a href="../shared/doc.pdf">Parent relative PDF</a>
        </body>
        </html>
        """

        base_url = "https://example.com/path/page.html"
        urls = extract_pdf_urls_from_html(html, base_url)

        expected = [
            "https://example.com/downloads/paper.pdf",
            "https://example.com/path/paper2.pdf",
            "https://example.com/shared/doc.pdf"
        ]

        for url in expected:
            assert url in urls

    def test_extract_pdf_urls_filter_invalid(self):
        """Test filtering of invalid or non-PDF URLs."""
        html = b"""
        <html>
        <body>
            <a href="https://example.com/paper.pdf">Valid PDF</a>
            <a href="https://example.com/paper.txt">Text file</a>
            <a href="javascript:void(0)">JavaScript link</a>
            <a href="mailto:test@example.com">Email link</a>
            <a href="#section">Anchor link</a>
        </body>
        </html>
        """

        urls = extract_pdf_urls_from_html(html, "https://example.com")
        assert "https://example.com/paper.pdf" in urls
        assert len(urls) == 1  # Only the PDF should be included

    def test_extract_pdf_urls_empty_html(self):
        """Test handling of empty or invalid HTML."""
        urls = extract_pdf_urls_from_html(b"", "https://example.com")
        assert urls == []

        urls = extract_pdf_urls_from_html(b"<html></html>", "https://example.com")
        assert urls == []

    def test_extract_pdf_urls_malformed_html(self):
        """Test handling of malformed HTML."""
        malformed_html = b"""
        <html>
        <body>
            <a href="https://example.com/paper.pdf">PDF link
            <a href="https://example.com/broken.pdf">Broken link
        </body>
        """

        urls = extract_pdf_urls_from_html(malformed_html, "https://example.com")
        assert "https://example.com/paper.pdf" in urls
        assert "https://example.com/broken.pdf" in urls

    def test_extract_pdf_urls_multiple_occurrences(self):
        """Test handling of multiple occurrences of the same URL."""
        html = b"""
        <html>
        <body>
            <a href="https://example.com/paper.pdf">First link</a>
            <a href="https://example.com/paper.pdf">Second link</a>
            <a href="https://example.com/other.pdf">Different link</a>
        </body>
        </html>
        """

        urls = extract_pdf_urls_from_html(html, "https://example.com")
        assert urls.count("https://example.com/paper.pdf") == 1  # Deduplicated
        assert "https://example.com/other.pdf" in urls
        assert len(urls) == 2

    def test_extract_pdf_urls_complex_html(self):
        """Test extraction from complex real-world HTML structure."""
        complex_html = b"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="citation_pdf_url" content="https://example.com/citation.pdf">
            <title>Paper Title</title>
        </head>
        <body>
            <div class="article-header">
                <a href="/content/pdf/paper.pdf" class="pdf-link">Download PDF</a>
                <a href="/content/pdf/supplement.pdf" class="supplement-link">Supplementary Materials</a>
            </div>
            <script type="application/json">
            {
                "pdfUrl": "https://example.com/script.pdf",
                "doi": "10.1234/example.12345"
            }
            </script>
            <div style="display:none">
                <a href="hidden.pdf">Hidden PDF</a>
            </div>
        </body>
        </html>
        """

        urls = extract_pdf_urls_from_html(complex_html, "https://example.com")

        expected_urls = [
            "https://example.com/citation.pdf",
            "https://example.com/content/pdf/paper.pdf",
            "https://example.com/content/pdf/supplement.pdf",
            "https://example.com/script.pdf",
            "https://example.com/hidden.pdf"
        ]

        for url in expected_urls:
            assert url in urls


class TestPDFHandlerHTMLIntegration:
    """Test PDFHandler integration with HTML parsing."""

    def test_parse_html_for_pdf_method(self, tmp_path):
        """Test the parse_html_for_pdf method on PDFHandler."""
        config = LiteratureConfig(download_dir=str(tmp_path / "downloads"))
        handler = PDFHandler(config)

        html = b"""
        <html>
        <body>
            <a href="https://example.com/paper.pdf">Download PDF</a>
            <a href="https://example.com/other.txt">Not PDF</a>
        </body>
        </html>
        """

        urls = handler.parse_html_for_pdf(html, "https://example.com")
        assert urls == ["https://example.com/paper.pdf"]

    def test_html_parsing_with_real_world_examples(self):
        """Test HTML parsing with real-world publisher page examples."""
        # IEEE Xplore-like page
        ieee_html = b"""
        <html>
        <head>
            <script>
                var arnumber = "9876543";
                var doi = "10.1109/EXAMPLE.2023.1234567";
            </script>
        </head>
        <body>
            <a href="/stampPDF/getPDF.jsp?arnumber=9876543" class="pdf-link">PDF</a>
        </body>
        </html>
        """

        urls = extract_pdf_urls_from_html(ieee_html, "https://ieeexplore.ieee.org")
        expected = [
            "https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?arnumber=9876543",  # From pattern
            "/stampPDF/getPDF.jsp?arnumber=9876543"  # From href
        ]

        for url in expected:
            if url.startswith("/"):
                assert f"https://ieeexplore.ieee.org{url}" in urls
            else:
                assert url in urls

    def test_html_parsing_edge_cases(self):
        """Test edge cases in HTML parsing."""
        # HTML with encoding issues
        bad_encoding_html = b"""
        <html>
        <body>
            <a href="https://example.com/paper.pdf">\xff\xfeInvalid encoding</a>
        </body>
        </html>
        """

        urls = extract_pdf_urls_from_html(bad_encoding_html, "https://example.com")
        assert "https://example.com/paper.pdf" in urls

        # Moderately large HTML content (should still work)
        large_html = b'<html><body><a href="https://example.com/large.pdf">PDF</a></body></html>' * 20
        urls = extract_pdf_urls_from_html(large_html, "https://example.com")
        assert "https://example.com/large.pdf" in urls

    def test_html_parsing_url_validation(self):
        """Test that extracted URLs are properly validated."""
        html = b"""
        <html>
        <body>
            <a href="https://valid.example.com/paper.pdf">Valid PDF</a>
            <a href="ftp://ftp.example.com/paper.pdf">FTP URL (invalid)</a>
            <a href="file:///local/path/paper.pdf">File URL (invalid)</a>
            <a href="//relative.example.com/paper.pdf">Protocol-relative (valid)</a>
        </body>
        </html>
        """

        urls = extract_pdf_urls_from_html(html, "https://example.com")

        assert "https://valid.example.com/paper.pdf" in urls
        assert "https://relative.example.com/paper.pdf" in urls

        # Should not include FTP or file URLs
        assert not any(url.startswith(("ftp://", "file://")) for url in urls)


class TestHTMLParsingIntegration:
    """Test HTML parsing integration with the broader system."""

    def test_html_parsing_does_not_break_existing_functionality(self, tmp_path):
        """Ensure HTML parsing doesn't break existing PDFHandler functionality."""
        config = LiteratureConfig(download_dir=str(tmp_path / "downloads"))
        handler = PDFHandler(config)

        # Test that the handler can still be created and basic methods work
        assert handler.config == config
        assert handler.parse_html_for_pdf(b"<html></html>", "https://example.com") == []

    def test_html_parsing_performance(self):
        """Test that HTML parsing is reasonably performant."""
        import time

        # Create a moderately complex HTML page
        html_parts = []
        for i in range(100):
            html_parts.append(f'<a href="https://example.com/paper{i}.pdf">PDF {i}</a>')
        html = f"<html><body>{''.join(html_parts)}</body></html>".encode()

        start_time = time.time()
        urls = extract_pdf_urls_from_html(html, "https://example.com")
        end_time = time.time()

        # Should extract all 100 URLs
        assert len(urls) == 100

        # Should complete in reasonable time (< 1 second)
        duration = end_time - start_time
        assert duration < 1.0, f"HTML parsing took {duration:.2f}s, expected < 1.0s"
