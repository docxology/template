"""Tests for infrastructure/llm/utils/models.py.

Covers: get_available_model_info, get_model_names, select_best_model,
small_fast_preference_matches, get_model_info, check_model_loaded,
preload_model.

No mocks used -- uses pytest-httpserver for HTTP testing.
"""

from __future__ import annotations


from pytest_httpserver import HTTPServer

from infrastructure.llm.utils.models import (
    get_available_model_info,
    get_model_names,
    select_best_model,
    small_fast_preference_matches,
    get_model_info,
    check_model_loaded,
    preload_model,
)


SAMPLE_MODELS = [
    {"name": "smollm2", "size": 135000000},
    {"name": "gemma3:4b", "size": 4000000000},
    {"name": "llama3.1:latest", "size": 8000000000},
]


class TestGetAvailableModelInfo:
    """Test get_available_model_info."""

    def test_successful_response(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_json(
            {"models": SAMPLE_MODELS}
        )
        models = get_available_model_info(
            base_url=httpserver.url_for(""), timeout=5.0, retries=0
        )
        assert len(models) == 3
        assert models[0]["name"] == "smollm2"

    def test_empty_model_list(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_json({"models": []})
        models = get_available_model_info(
            base_url=httpserver.url_for(""), timeout=5.0, retries=0
        )
        assert models == []

    def test_connection_error(self):
        models = get_available_model_info(
            base_url="http://localhost:1", timeout=0.5, retries=0
        )
        assert models == []

    def test_retry_on_timeout(self):
        # Very short timeout to force timeout
        models = get_available_model_info(
            base_url="http://192.0.2.1:11434", timeout=0.1, retries=1
        )
        assert models == []


class TestGetModelNames:
    """Test get_model_names."""

    def test_returns_names(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_json(
            {"models": SAMPLE_MODELS}
        )
        names = get_model_names(base_url=httpserver.url_for(""))
        assert "smollm2" in names
        assert "gemma3:4b" in names

    def test_empty_when_no_server(self):
        names = get_model_names(base_url="http://localhost:1")
        assert names == []


class TestSelectBestModel:
    """Test select_best_model."""

    def test_selects_preferred(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_json(
            {"models": SAMPLE_MODELS}
        )
        model = select_best_model(
            preferences=["gemma3:4b", "smollm2"],
            base_url=httpserver.url_for(""),
        )
        assert model == "gemma3:4b"

    def test_partial_match(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_json(
            {"models": [{"name": "llama3.1:latest"}]}
        )
        model = select_best_model(
            preferences=["llama3"],
            base_url=httpserver.url_for(""),
        )
        assert model == "llama3.1:latest"

    def test_fallback_to_first(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_json(
            {"models": [{"name": "custom-model:latest"}]}
        )
        model = select_best_model(
            preferences=["nonexistent-model"],
            base_url=httpserver.url_for(""),
        )
        assert model == "custom-model:latest"

    def test_no_models_available(self):
        model = select_best_model(base_url="http://localhost:1")
        assert model is None

    def test_uses_default_preferences(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_json(
            {"models": SAMPLE_MODELS}
        )
        model = select_best_model(base_url=httpserver.url_for(""))
        assert model is not None


class TestSmallFastPreferenceMatches:
    """Test small_fast_preference_matches."""

    def test_exact_match(self):
        assert small_fast_preference_matches(["smollm2", "other"]) is True

    def test_partial_match(self):
        assert small_fast_preference_matches(["gemma2:2b-instruct"]) is True

    def test_no_match(self):
        assert small_fast_preference_matches(["custom-model:latest"]) is False

    def test_empty_list(self):
        assert small_fast_preference_matches([]) is False


class TestGetModelInfo:
    """Test get_model_info."""

    def test_found(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_json(
            {"models": SAMPLE_MODELS}
        )
        info = get_model_info("smollm2", base_url=httpserver.url_for(""))
        assert info is not None
        assert info["name"] == "smollm2"

    def test_partial_match(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_json(
            {"models": SAMPLE_MODELS}
        )
        info = get_model_info("gemma3", base_url=httpserver.url_for(""))
        assert info is not None

    def test_not_found(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_json(
            {"models": SAMPLE_MODELS}
        )
        info = get_model_info("nonexistent", base_url=httpserver.url_for(""))
        assert info is None


class TestCheckModelLoaded:
    """Test check_model_loaded."""

    def test_exact_match_loaded(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/ps").respond_with_json(
            {"processes": [{"model": "smollm2"}]}
        )
        is_loaded, name = check_model_loaded(
            "smollm2", base_url=httpserver.url_for("")
        )
        assert is_loaded is True
        assert name == "smollm2"

    def test_partial_match_loaded(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/ps").respond_with_json(
            {"processes": [{"model": "llama3:latest"}]}
        )
        is_loaded, name = check_model_loaded(
            "llama3", base_url=httpserver.url_for("")
        )
        assert is_loaded is True
        assert name == "llama3:latest"

    def test_not_loaded(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/ps").respond_with_json(
            {"processes": [{"model": "other-model"}]}
        )
        is_loaded, name = check_model_loaded(
            "smollm2", base_url=httpserver.url_for("")
        )
        assert is_loaded is False
        assert name is None

    def test_no_processes(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/ps").respond_with_json(
            {"processes": []}
        )
        is_loaded, name = check_model_loaded(
            "smollm2", base_url=httpserver.url_for("")
        )
        assert is_loaded is False

    def test_server_error(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/ps").respond_with_data(
            "error", status=500
        )
        is_loaded, name = check_model_loaded(
            "smollm2", base_url=httpserver.url_for("")
        )
        assert is_loaded is False

    def test_connection_error(self):
        is_loaded, name = check_model_loaded(
            "smollm2", base_url="http://localhost:1", timeout=0.5
        )
        assert is_loaded is False


class TestPreloadModel:
    """Test preload_model."""

    def test_successful_preload(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/ps").respond_with_json(
            {"processes": []}
        )
        httpserver.expect_request("/api/generate").respond_with_json(
            {"response": "ok", "done": True}
        )
        success, error = preload_model(
            "smollm2", base_url=httpserver.url_for(""), retries=0
        )
        assert success is True
        assert error is None

    def test_already_loaded(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/ps").respond_with_json(
            {"processes": [{"model": "smollm2"}]}
        )
        success, error = preload_model(
            "smollm2", base_url=httpserver.url_for(""), retries=0
        )
        assert success is True

    def test_skip_loaded_check(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/generate").respond_with_json(
            {"response": "ok", "done": True}
        )
        success, error = preload_model(
            "smollm2",
            base_url=httpserver.url_for(""),
            check_loaded_first=False,
            retries=0,
        )
        assert success is True

    def test_connection_error(self):
        success, error = preload_model(
            "smollm2", base_url="http://localhost:1", timeout=0.5, retries=0
        )
        assert success is False
        assert error is not None

    def test_http_error(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/ps").respond_with_json({"processes": []})
        httpserver.expect_request("/api/generate").respond_with_data(
            "model not found", status=404
        )
        success, error = preload_model(
            "smollm2", base_url=httpserver.url_for(""), retries=0
        )
        assert success is False
