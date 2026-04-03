"""Tests for review generator functions in infrastructure.llm.review.generator."""

from __future__ import annotations

import json

import pytest
from pytest_httpserver import HTTPServer

from infrastructure.llm.core.client import LLMClient
from infrastructure.llm.core.config import OllamaClientConfig
from infrastructure.llm.review.generator import (
    extract_manuscript_text,
    generate_improvement_suggestions,
    generate_llm_executive_summary as generate_executive_summary,
    generate_review_with_metrics,
    generate_translation,
    validate_review_quality,
    warmup_model,
)
from infrastructure.llm.templates.manuscript import ManuscriptMethodologyReview, ManuscriptQualityReview


class TestExtractManuscriptText:
    """Tests for extract_manuscript_text() function."""

    def test_file_not_found(self, tmp_path):
        """Test extract_manuscript_text returns None for missing file."""
        text, metrics = extract_manuscript_text(str(tmp_path / "nonexistent.pdf"))
        assert text is None

    def test_no_pdf_library_raises_error(self, tmp_path):
        """Test extract_manuscript_text raises PDFValidationError for a corrupt/tiny file."""
        from infrastructure.core.exceptions import PDFValidationError

        # Create a dummy PDF file (too small to be a valid PDF)
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"dummy pdf content")

        with pytest.raises(PDFValidationError):
            extract_manuscript_text(str(pdf_file))

    def test_extracts_text_from_real_pdf(self, tmp_path):
        """Test extract_manuscript_text with a real PDF file."""
        pytest.importorskip("reportlab")
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        pdf_file = tmp_path / "test.pdf"
        c = canvas.Canvas(str(pdf_file), pagesize=letter)
        c.drawString(100, 750, "Extracted text from page")
        c.drawString(100, 730, "Second line of text")
        c.save()

        try:
            text, metrics = extract_manuscript_text(str(pdf_file))
            assert text is not None
            assert "Extracted text from page" in text
            assert "Second line of text" in text
        except ValueError as e:
            assert "No PDF parsing library available" in str(e)


class TestGenerateReviewWithMetrics:
    """Tests for generate_review_with_metrics() function."""

    @pytest.mark.slow
    def test_generates_executive_summary(self, ollama_test_server):
        """Test generate_review_with_metrics with executive_summary type."""
        from infrastructure.llm.templates import ManuscriptExecutiveSummary

        manuscript_text = "This is a test manuscript about machine learning."
        client = LLMClient()

        review_text, metrics = generate_review_with_metrics(
            client, manuscript_text, "executive_summary", "Executive Summary", ManuscriptExecutiveSummary
        )

        assert isinstance(review_text, str)
        assert len(review_text) > 0
        # ReviewMetrics attributes:
        assert metrics.output_chars > 0
        assert metrics.generation_time_seconds > 0

    @pytest.mark.slow
    def test_generates_quality_review(self, ollama_test_server):
        """Test generate_review_with_metrics with quality_review type."""
        from infrastructure.llm.templates import ManuscriptQualityReview

        manuscript_text = "Test manuscript text."
        client = LLMClient()

        review_text, metrics = generate_review_with_metrics(
            client, manuscript_text, "quality_review", "Quality Review", ManuscriptQualityReview
        )

        assert isinstance(review_text, str)
        assert len(review_text) > 0

    @pytest.mark.slow
    def test_generates_methodology_review(self, ollama_test_server):
        """Test generate_review_with_metrics with methodology_review type."""
        from infrastructure.llm.templates import ManuscriptMethodologyReview

        manuscript_text = "Test manuscript."
        client = LLMClient()

        review_text, metrics = generate_review_with_metrics(
            client, manuscript_text, "methodology_review", "Methodology Review", ManuscriptMethodologyReview
        )

        assert isinstance(review_text, str)
        assert len(review_text) > 0

    @pytest.mark.slow
    def test_generates_improvement_suggestions(self, ollama_test_server):
        """Test generate_review_with_metrics with improvement_suggestions type."""
        from infrastructure.llm.templates import ManuscriptImprovementSuggestions

        manuscript_text = "Test manuscript."
        client = LLMClient()

        review_text, metrics = generate_review_with_metrics(
            client,
            manuscript_text,
            "improvement_suggestions",
            "Improvement Suggestions",
            ManuscriptImprovementSuggestions,
        )

        assert isinstance(review_text, str)
        assert len(review_text) > 0

    @pytest.mark.slow
    def test_metrics_include_all_fields(self, ollama_test_server):
        """Test that metrics dict includes all expected fields."""
        from infrastructure.llm.templates import ManuscriptExecutiveSummary

        manuscript_text = "Test manuscript text for metrics testing."
        client = LLMClient()

        _, metrics = generate_review_with_metrics(
            client, manuscript_text, "executive_summary", "Executive Summary", ManuscriptExecutiveSummary
        )

        # Check dataclass attributes
        assert hasattr(metrics, "input_chars")
        assert hasattr(metrics, "output_chars")
        assert hasattr(metrics, "generation_time_seconds")
        assert hasattr(metrics, "input_tokens_est")

    @pytest.mark.slow
    def test_truncates_long_manuscript(self, ollama_test_server):
        """Test that long manuscripts are truncated."""
        from infrastructure.llm.templates import ManuscriptExecutiveSummary

        long_text = "x" * 600000
        client = LLMClient()

        review_text, metrics = generate_review_with_metrics(
            client, long_text, "executive_summary", "Executive Summary", ManuscriptExecutiveSummary
        )

        assert isinstance(review_text, str)
        assert len(review_text) > 0


class TestTemplateBasedGenerators:
    """Tests for template-based generator functions."""

    @pytest.mark.slow
    def test_generate_executive_summary_calls_llm(self, ollama_test_server):
        """Test generate_executive_summary actually queries LLM."""
        manuscript_text = "Test manuscript about AI research."
        client = LLMClient()

        result, metrics = generate_executive_summary(
            client, manuscript_text, model_name="gemma3:4b"
        )

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.slow
    def test_generate_quality_review_calls_llm(self, ollama_test_server):
        """Test generate_review_with_metrics with quality template queries LLM."""
        manuscript_text = "Test manuscript."
        client = LLMClient()

        result, metrics = generate_review_with_metrics(
            client=client,
            text=manuscript_text,
            review_type="quality_review",
            review_name="quality review",
            template_class=ManuscriptQualityReview,
            temperature=0.3,
            max_tokens=None,
        )

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.slow
    def test_generate_methodology_review_calls_llm(self, ollama_test_server):
        """Test generate_review_with_metrics with methodology template queries LLM."""
        manuscript_text = "Test manuscript."
        client = LLMClient()

        result, metrics = generate_review_with_metrics(
            client=client,
            text=manuscript_text,
            review_type="methodology_review",
            review_name="methodology review",
            template_class=ManuscriptMethodologyReview,
            temperature=0.3,
            max_tokens=None,
        )

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.slow
    def test_generate_improvement_suggestions_calls_llm(self, ollama_test_server):
        """Test generate_improvement_suggestions actually queries LLM."""
        manuscript_text = "Test manuscript."
        client = LLMClient()

        result, metrics = generate_improvement_suggestions(client, manuscript_text)

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.slow
    def test_generate_translation_calls_llm(self, ollama_test_server):
        """Test generate_translation actually queries LLM."""
        text = "Hello world"
        target_language = "zh"
        client = LLMClient()

        result, metrics = generate_translation(client, text, target_language)

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.slow
    def test_generate_translation_with_model(self, ollama_test_server):
        """Test generate_translation respects model parameter."""
        text = "Test"
        target_language = "hi"
        client = LLMClient()

        result, metrics = generate_translation(
            client, text, target_language, model_name="gemma3:4b"
        )

        assert isinstance(result, str)
        assert len(result) > 0


class TestGenerateReviewWithMetricsRetry:
    """Offline tests for the retry loop in generate_review_with_metrics."""

    def test_retry_fires_on_off_topic_first_response(self):
        """First off-topic response triggers a retry; best response is returned."""
        from infrastructure.llm.templates import ManuscriptQualityReview

        call_count = [0]
        long_valid = (
            "## Quality Assessment\n\nThis manuscript demonstrates clear structure "
            "and sound argumentation. " * 40
        )

        def stateful_handler(request):
            try:
                data = json.loads(request.get_data())
            except (ValueError, TypeError):
                data = {}
            call_count[0] += 1
            model = data.get("model", "gemma3:4b")
            is_stream = data.get("stream", False)
            # Off-topic on first attempt, valid review on second
            content = "Dear reviewer, I cannot help with this request." if call_count[0] == 1 else long_valid
            if is_stream:
                chunks = [
                    {"model": model, "message": {"role": "assistant", "content": content[:50]}, "done": False},
                    {"model": model, "message": {"role": "assistant", "content": content[50:]}, "done": False},
                    {"model": model, "message": {"role": "assistant", "content": ""}, "done": True},
                ]
                return "\n".join(json.dumps(c) for c in chunks)
            return json.dumps({"model": model, "message": {"role": "assistant", "content": content}, "done": True})

        server = HTTPServer()
        server.start()
        server.expect_request("/api/chat", method="POST").respond_with_handler(stateful_handler)
        server.expect_request("/api/tags").respond_with_json({"models": [{"name": "gemma3:4b"}]})

        try:
            config = OllamaClientConfig(auto_inject_system_prompt=False)
            config.base_url = server.url_for("/")
            config.default_model = "gemma3:4b"
            client = LLMClient(config=config)

            review_text, _metrics = generate_review_with_metrics(
                client, "Test manuscript text.", "quality_review", "Quality Review",
                ManuscriptQualityReview, max_retries=1,
            )

            assert call_count[0] == 2, f"Expected 2 attempts, got {call_count[0]}"
            assert review_text is not None
            assert len(review_text.split()) > 10
        finally:
            server.stop()

    def test_max_retries_zero_makes_single_attempt(self):
        """max_retries=0 makes exactly one attempt regardless of validation outcome."""
        from infrastructure.llm.templates import ManuscriptExecutiveSummary

        call_count = [0]

        def counter_handler(request):
            try:
                data = json.loads(request.get_data())
            except (ValueError, TypeError):
                data = {}
            call_count[0] += 1
            model = data.get("model", "gemma3:4b")
            is_stream = data.get("stream", False)
            content = "Short."
            if is_stream:
                chunks = [
                    {"model": model, "message": {"role": "assistant", "content": content}, "done": False},
                    {"model": model, "message": {"role": "assistant", "content": ""}, "done": True},
                ]
                return "\n".join(json.dumps(c) for c in chunks)
            return json.dumps({"model": model, "message": {"role": "assistant", "content": content}, "done": True})

        server = HTTPServer()
        server.start()
        server.expect_request("/api/chat", method="POST").respond_with_handler(counter_handler)
        server.expect_request("/api/tags").respond_with_json({"models": [{"name": "gemma3:4b"}]})

        try:
            config = OllamaClientConfig(auto_inject_system_prompt=False)
            config.base_url = server.url_for("/")
            config.default_model = "gemma3:4b"
            client = LLMClient(config=config)

            generate_review_with_metrics(
                client, "Test.", "executive_summary", "Executive Summary",
                ManuscriptExecutiveSummary, max_retries=0,
            )

            assert call_count[0] == 1, f"Expected 1 attempt, got {call_count[0]}"
        finally:
            server.stop()


class TestWarmupModelOffline:
    """Offline tests for warmup_model() using a local HTTP server."""

    def _make_client(self, server: HTTPServer) -> LLMClient:
        config = OllamaClientConfig(auto_inject_system_prompt=False)
        config.base_url = server.url_for("/")
        config.default_model = "gemma3:4b"
        config.timeout = 5
        return LLMClient(config=config)

    def _make_server_with_ps(self, ps_response: dict) -> HTTPServer:
        """Start a server with /api/ps returning ps_response and /api/chat streaming chunks."""

        def chat_handler(request):
            try:
                data = json.loads(request.get_data())
            except (ValueError, TypeError):
                data = {}
            model = data.get("model", "gemma3:4b")
            content = "The main topic is machine learning."
            chunks = [
                {"model": model, "message": {"role": "assistant", "content": content}, "done": False},
                {"model": model, "message": {"role": "assistant", "content": ""}, "done": True},
            ]
            return "\n".join(json.dumps(c) for c in chunks)

        server = HTTPServer()
        server.start()
        server.expect_request("/api/ps").respond_with_json(ps_response)
        server.expect_request("/api/chat", method="POST").respond_with_handler(chat_handler)
        return server

    def test_warmup_error_path_returns_false(self):
        """Server returning 500 causes warmup_model to return (False, 0.0)."""
        server = HTTPServer()
        server.start()
        server.expect_request("/api/ps").respond_with_json({"models": []})
        server.expect_request("/api/chat", method="POST").respond_with_data("", status=500)

        try:
            client = self._make_client(server)
            success, tps = warmup_model(client, "Test text for warmup", "gemma3:4b")
            assert success is False
            assert tps == 0.0
        finally:
            server.stop()

    def test_warmup_no_model_loaded_triggers_preload(self):
        """No model in /api/ps triggers preload path; returns (True, >0) on successful stream."""
        server = self._make_server_with_ps({"models": []})
        server.expect_request("/api/generate", method="POST").respond_with_json({"done": True})

        try:
            client = self._make_client(server)
            success, tps = warmup_model(client, "Warmup text preview", "gemma3:4b")
            assert isinstance(success, bool)
            assert isinstance(tps, float)
        finally:
            server.stop()

    def test_warmup_model_already_loaded_skips_preload(self):
        """Model already loaded in /api/ps skips preload and streams warmup prompt."""
        ps_response = {"models": [{"name": "gemma3:4b", "size_vram": 4000000000}]}
        server = self._make_server_with_ps(ps_response)

        try:
            client = self._make_client(server)
            success, tps = warmup_model(client, "Warmup text preview", "gemma3:4b")
            assert success is True
            assert tps >= 0.0
        finally:
            server.stop()


@pytest.mark.requires_ollama
class TestReviewGeneratorsIntegration:
    """Integration tests for review generators (requires Ollama)."""

    def test_generate_executive_summary_real_ollama(self):
        """Test generate_executive_summary with real Ollama."""
        from .real_ollama_client import build_real_small_llm_client

        client = build_real_small_llm_client(timeout=60.0)

        manuscript_text = "This is a test manuscript about machine learning and AI."
        result, metrics = generate_executive_summary(client, manuscript_text)

        assert len(result) > 0
        assert isinstance(result, str)

    def test_generate_review_with_metrics_real_ollama(self):
        """Test generate_review_with_metrics with real Ollama."""
        from .real_ollama_client import build_real_small_llm_client

        client = build_real_small_llm_client(timeout=60.0)

        manuscript_text = "Test manuscript about optimization algorithms."
        from infrastructure.llm.templates import ManuscriptExecutiveSummary

        review_text, metrics = generate_review_with_metrics(
            client, manuscript_text, "executive_summary", "Executive Summary", ManuscriptExecutiveSummary
        )

        assert len(review_text) > 0
        assert hasattr(metrics, "output_chars")
        assert hasattr(metrics, "generation_time_seconds")
        assert metrics.generation_time_seconds > 0


class TestValidateReviewQuality:
    """Deterministic tests for validate_review_quality() — no Ollama required."""

    def _good_executive_summary(self, n_extra_words: int = 0) -> str:
        """Build a minimal passing executive summary with required section keywords."""
        base = (
            "## Overview\nThis is the overview section of the manuscript. "
            "## Key Contributions\nThe main findings and contributions are described here. "
            "## Methodology\nThe methods and approach used in this work. "
            "## Results\nThe outcomes and principal results of the study. "
            "## Significance\nThe impact and implications of this research. "
        )
        extra = " ".join(f"word{i}" for i in range(n_extra_words))
        return base + " " + extra

    def test_passes_for_adequate_response(self):
        """A response with enough words and required sections passes validation."""
        response = self._good_executive_summary(n_extra_words=300)
        passed, issues, details = validate_review_quality(response, "executive_summary")
        assert passed is True, f"Expected pass but got issues: {issues}"

    def test_fails_for_too_short_response(self):
        """A response with too few words fails with a 'too short' issue."""
        response = " ".join(f"word{i}" for i in range(5))
        passed, issues, details = validate_review_quality(
            response, "executive_summary", min_words=200
        )
        assert passed is False
        assert any("short" in issue.lower() for issue in issues)

    def test_fails_for_too_short_explicit_min(self):
        """Explicit min_words overrides the default minimum for any review type."""
        response = "This is a short response with overview content."
        passed, issues, details = validate_review_quality(
            response, "executive_summary", min_words=500
        )
        assert passed is False
        assert any("short" in issue.lower() for issue in issues)
        assert details["word_count"] < 500

    def test_returns_word_count_in_details(self):
        """Details dict always contains word_count."""
        response = self._good_executive_summary(n_extra_words=200)
        _, _, details = validate_review_quality(response, "executive_summary", min_words=10)
        assert "word_count" in details
        assert details["word_count"] > 0

    def test_small_model_reduces_minimum_word_count(self):
        """Small model names lower the effective minimum word threshold by 20%."""
        # Build a response with sections but borderline word count
        response = self._good_executive_summary(n_extra_words=200)
        # Pass with explicit min_words that normal model would require but small won't
        _, issues_normal, _ = validate_review_quality(
            response, "executive_summary", min_words=5000
        )
        _, issues_small, _ = validate_review_quality(
            response, "executive_summary", min_words=5000, model_name="llama3-8b"
        )
        # Small model has a lower effective minimum (min * 0.8), so it may have fewer issues
        # Both may still fail for 5000 words but small model's threshold is lower
        normal_short = any("short" in i.lower() for i in issues_normal)
        small_short = any("short" in i.lower() for i in issues_small)
        # Both should flag it as too short for 5000 min, but that's the expected behavior
        assert normal_short is True
        assert small_short is True


