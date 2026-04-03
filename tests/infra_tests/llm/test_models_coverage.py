"""Tests for infrastructure.llm.utils.models — comprehensive coverage using pytest-httpserver."""


from pytest_httpserver import HTTPServer

from infrastructure.llm.utils.models import (
    get_available_model_info,
    get_model_names,
    select_best_model,
    select_small_fast_model,
    get_model_info,
    check_model_loaded,
    preload_model,
    DEFAULT_MODEL_PREFERENCES,
)


def _models_response(*names):
    """Build a /api/tags response with given model names."""
    return {"models": [{"name": n, "size": 1000000} for n in names]}


class TestGetAvailableModelInfo:
    def test_success(self, httpserver: HTTPServer):
        data = _models_response("llama3:latest", "mistral:7b")
        httpserver.expect_request("/api/tags").respond_with_json(data)
        result = get_available_model_info(httpserver.url_for(""), retries=0)
        assert len(result) == 2
        assert result[0]["name"] == "llama3:latest"

    def test_empty_models(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_json({"models": []})
        result = get_available_model_info(httpserver.url_for(""), retries=0)
        assert result == []

    def test_connection_error(self):
        result = get_available_model_info("http://localhost:1", retries=0, timeout=0.5)
        assert result == []

    def test_timeout(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_handler(
            lambda req: None  # never responds
        )
        result = get_available_model_info(httpserver.url_for(""), timeout=0.1, retries=0)
        assert result == []


class TestGetModelNames:
    def test_returns_names(self, httpserver: HTTPServer):
        data = _models_response("gemma:2b", "llama3:latest")
        httpserver.expect_request("/api/tags").respond_with_json(data)
        result = get_model_names(httpserver.url_for(""))
        assert "gemma:2b" in result
        assert "llama3:latest" in result

    def test_empty(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_json({"models": []})
        result = get_model_names(httpserver.url_for(""))
        assert result == []


class TestSelectBestModel:
    def test_exact_match(self, httpserver: HTTPServer):
        data = _models_response("gemma3:4b", "llama3:latest")
        httpserver.expect_request("/api/tags").respond_with_json(data)
        result = select_best_model(["gemma3:4b"], httpserver.url_for(""))
        assert result == "gemma3:4b"

    def test_partial_match(self, httpserver: HTTPServer):
        data = _models_response("llama3:latest")
        httpserver.expect_request("/api/tags").respond_with_json(data)
        result = select_best_model(["llama3"], httpserver.url_for(""))
        assert result == "llama3:latest"

    def test_fallback_to_first(self, httpserver: HTTPServer):
        data = _models_response("unknown_model:1b")
        httpserver.expect_request("/api/tags").respond_with_json(data)
        result = select_best_model(["nonexistent"], httpserver.url_for(""))
        assert result == "unknown_model:1b"

    def test_no_models(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_json({"models": []})
        result = select_best_model(["anything"], httpserver.url_for(""))
        assert result is None

    def test_default_preferences(self, httpserver: HTTPServer):
        data = _models_response("smollm2")
        httpserver.expect_request("/api/tags").respond_with_json(data)
        result = select_best_model(base_url=httpserver.url_for(""))
        assert result == "smollm2"


class TestSelectSmallFastModel:
    def test_selects_fast(self, httpserver: HTTPServer):
        data = _models_response("gemma2:2b", "llama3:latest")
        httpserver.expect_request("/api/tags").respond_with_json(data)
        result = select_small_fast_model(httpserver.url_for(""))
        assert result == "gemma2:2b"

    def test_no_models(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_json({"models": []})
        result = select_small_fast_model(httpserver.url_for(""))
        assert result is None


class TestGetModelInfo:
    def test_found(self, httpserver: HTTPServer):
        data = _models_response("llama3:latest")
        httpserver.expect_request("/api/tags").respond_with_json(data)
        result = get_model_info("llama3:latest", httpserver.url_for(""))
        assert result is not None
        assert result["name"] == "llama3:latest"

    def test_partial_match(self, httpserver: HTTPServer):
        data = _models_response("llama3:latest")
        httpserver.expect_request("/api/tags").respond_with_json(data)
        result = get_model_info("llama3", httpserver.url_for(""))
        assert result is not None

    def test_not_found(self, httpserver: HTTPServer):
        data = _models_response("llama3:latest")
        httpserver.expect_request("/api/tags").respond_with_json(data)
        result = get_model_info("nonexistent", httpserver.url_for(""))
        assert result is None


class TestCheckModelLoaded:
    def test_loaded_exact_match(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/ps").respond_with_json(
            {"processes": [{"model": "llama3:latest"}]}
        )
        is_loaded, name = check_model_loaded("llama3:latest", httpserver.url_for(""))
        assert is_loaded is True
        assert name == "llama3:latest"

    def test_loaded_partial_match(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/ps").respond_with_json(
            {"processes": [{"model": "llama3:latest"}]}
        )
        is_loaded, name = check_model_loaded("llama3", httpserver.url_for(""))
        assert is_loaded is True
        assert name == "llama3:latest"

    def test_not_loaded(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/ps").respond_with_json(
            {"processes": [{"model": "mistral:7b"}]}
        )
        is_loaded, name = check_model_loaded("llama3:latest", httpserver.url_for(""))
        assert is_loaded is False
        assert name is None

    def test_no_processes(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/ps").respond_with_json({"processes": []})
        is_loaded, name = check_model_loaded("llama3:latest", httpserver.url_for(""))
        assert is_loaded is False

    def test_error_status(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/ps").respond_with_data("error", status=500)
        is_loaded, name = check_model_loaded("llama3:latest", httpserver.url_for(""))
        assert is_loaded is False

    def test_connection_error(self):
        is_loaded, name = check_model_loaded("llama3:latest", "http://localhost:1", timeout=0.5)
        assert is_loaded is False


class TestPreloadModel:
    def test_already_loaded(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/ps").respond_with_json(
            {"processes": [{"model": "llama3:latest"}]}
        )
        success, error = preload_model("llama3:latest", httpserver.url_for(""), retries=0)
        assert success is True
        assert error is None

    def test_successful_preload(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/ps").respond_with_json({"processes": []})
        httpserver.expect_request("/api/generate", method="POST").respond_with_json(
            {"response": "ok"}
        )
        success, error = preload_model("llama3:latest", httpserver.url_for(""), retries=0)
        assert success is True

    def test_preload_failure(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/ps").respond_with_json({"processes": []})
        httpserver.expect_request("/api/generate", method="POST").respond_with_data(
            "error", status=500
        )
        success, error = preload_model(
            "llama3:latest", httpserver.url_for(""), retries=0
        )
        assert success is False
        assert error is not None

    def test_skip_loaded_check(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/generate", method="POST").respond_with_json(
            {"response": "ok"}
        )
        success, error = preload_model(
            "llama3:latest", httpserver.url_for(""), retries=0, check_loaded_first=False
        )
        assert success is True

    def test_connection_error(self):
        success, error = preload_model(
            "llama3:latest",
            "http://localhost:1",
            retries=0,
            check_loaded_first=False,
            timeout=0.5,
        )
        assert success is False


class TestDefaultPreferences:
    def test_has_entries(self):
        assert len(DEFAULT_MODEL_PREFERENCES) > 0

    def test_smollm2_first(self):
        assert DEFAULT_MODEL_PREFERENCES[0] == "smollm2"
