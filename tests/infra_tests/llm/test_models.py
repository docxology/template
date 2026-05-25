"""Tests for infrastructure.llm.utils.models."""

from __future__ import annotations

import pytest
from pytest_httpserver import HTTPServer

from infrastructure.llm.utils.models import (
    DEFAULT_MODEL_PREFERENCES,
    check_model_loaded,
    get_available_model_info,
    get_model_info,
    get_model_names,
    preload_model,
    select_best_model,
    select_small_fast_model,
    small_fast_preference_matches,
)

SAMPLE_MODELS = [
    {"name": "smollm2", "size": 135000000},
    {"name": "gemma3:4b", "size": 4000000000},
    {"name": "llama3.1:latest", "size": 8000000000},
]


def _models_response(*names: str) -> dict:
    """Build a /api/tags response with given model names."""
    return {"models": [{"name": n, "size": 1000000} for n in names]}


class TestGetAvailableModelInfo:
    def test_successful_response(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_json({"models": SAMPLE_MODELS})
        models = get_available_model_info(base_url=httpserver.url_for(""), timeout=5.0, retries=0)
        assert len(models) == 3
        assert models[0]["name"] == "smollm2"

    def test_empty_model_list(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_json({"models": []})
        models = get_available_model_info(base_url=httpserver.url_for(""), timeout=5.0, retries=0)
        assert models == []

    @pytest.mark.parametrize(
        ("base_url", "timeout", "retries"),
        [
            ("http://localhost:1", 0.5, 0),
            ("http://192.0.2.1:11434", 0.1, 1),
        ],
    )
    def test_connection_or_timeout_returns_empty(self, base_url, timeout, retries):
        assert get_available_model_info(base_url=base_url, timeout=timeout, retries=retries) == []


class TestGetModelNames:
    def test_returns_names(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_json({"models": SAMPLE_MODELS})
        names = get_model_names(base_url=httpserver.url_for(""))
        assert "smollm2" in names
        assert "gemma3:4b" in names

    def test_empty_when_no_server(self):
        assert get_model_names(base_url="http://localhost:1") == []


class TestSelectBestModel:
    @pytest.mark.parametrize(
        ("preferences", "models_payload", "expected"),
        [
            (["gemma3:4b", "smollm2"], SAMPLE_MODELS, "gemma3:4b"),
            (["llama3"], [{"name": "llama3.1:latest"}], "llama3.1:latest"),
            (["nonexistent-model"], [{"name": "custom-model:latest"}], "custom-model:latest"),
        ],
    )
    def test_selection_strategies(self, httpserver: HTTPServer, preferences, models_payload, expected):
        httpserver.expect_request("/api/tags").respond_with_json({"models": models_payload})
        model = select_best_model(preferences=preferences, base_url=httpserver.url_for(""))
        assert model == expected

    def test_no_models_available(self):
        assert select_best_model(base_url="http://localhost:1") is None

    def test_uses_default_preferences(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/tags").respond_with_json({"models": SAMPLE_MODELS})
        assert select_best_model(base_url=httpserver.url_for("")) is not None


class TestSmallFastPreferenceMatches:
    @pytest.mark.parametrize(
        ("preferences", "expected"),
        [
            (["smollm2", "other"], True),
            (["gemma2:2b-instruct"], True),
            (["custom-model:latest"], False),
            ([], False),
        ],
    )
    def test_preference_matching(self, preferences, expected):
        assert small_fast_preference_matches(preferences) is expected


class TestGetModelInfo:
    @pytest.mark.parametrize(
        ("query", "expected_name"),
        [
            ("smollm2", "smollm2"),
            ("gemma3", "gemma3:4b"),
            ("nonexistent", None),
        ],
    )
    def test_model_lookup(self, httpserver: HTTPServer, query, expected_name):
        httpserver.expect_request("/api/tags").respond_with_json({"models": SAMPLE_MODELS})
        info = get_model_info(query, base_url=httpserver.url_for(""))
        if expected_name is None:
            assert info is None
        else:
            assert info is not None
            assert expected_name in info["name"]


class TestCheckModelLoaded:
    @pytest.mark.parametrize(
        ("processes", "query", "expected_loaded", "expected_name"),
        [
            ([{"model": "smollm2"}], "smollm2", True, "smollm2"),
            ([{"model": "llama3:latest"}], "llama3", True, "llama3:latest"),
            ([{"model": "other-model"}], "smollm2", False, None),
            ([], "smollm2", False, None),
        ],
    )
    def test_loaded_state(self, httpserver: HTTPServer, processes, query, expected_loaded, expected_name):
        httpserver.expect_request("/api/ps").respond_with_json({"processes": processes})
        is_loaded, name = check_model_loaded(query, base_url=httpserver.url_for(""))
        assert is_loaded is expected_loaded
        assert name == expected_name

    def test_server_error(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/ps").respond_with_data("error", status=500)
        is_loaded, name = check_model_loaded("smollm2", base_url=httpserver.url_for(""))
        assert is_loaded is False
        assert name is None

    def test_connection_error(self):
        is_loaded, name = check_model_loaded("smollm2", base_url="http://localhost:1", timeout=0.5)
        assert is_loaded is False
        assert name is None


class TestPreloadModel:
    def test_successful_preload(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/ps").respond_with_json({"processes": []})
        httpserver.expect_request("/api/generate").respond_with_json({"response": "ok", "done": True})
        success, error = preload_model("smollm2", base_url=httpserver.url_for(""), retries=0)
        assert success is True
        assert error is None

    def test_already_loaded(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/ps").respond_with_json({"processes": [{"model": "smollm2"}]})
        success, error = preload_model("smollm2", base_url=httpserver.url_for(""), retries=0)
        assert success is True
        assert error is None

    def test_skip_loaded_check(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/generate").respond_with_json({"response": "ok", "done": True})
        success, error = preload_model(
            "smollm2",
            base_url=httpserver.url_for(""),
            check_loaded_first=False,
            retries=0,
        )
        assert success is True
        assert error is None

    def test_connection_error(self):
        success, error = preload_model("smollm2", base_url="http://localhost:1", timeout=0.5, retries=0)
        assert success is False
        assert error is not None

    def test_http_error(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/ps").respond_with_json({"processes": []})
        httpserver.expect_request("/api/generate").respond_with_data("model not found", status=404)
        success, error = preload_model("smollm2", base_url=httpserver.url_for(""), retries=0)
        assert success is False


class TestGetAvailableModelInfoFromModels:
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


class TestGetModelNamesFromModels:
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


class TestSelectBestModelFromModels:
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


class TestGetModelInfoFromModels:
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


class TestCheckModelLoadedFromModels:
    def test_loaded_exact_match(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/ps").respond_with_json({"processes": [{"model": "llama3:latest"}]})
        is_loaded, name = check_model_loaded("llama3:latest", httpserver.url_for(""))
        assert is_loaded is True
        assert name == "llama3:latest"

    def test_loaded_partial_match(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/ps").respond_with_json({"processes": [{"model": "llama3:latest"}]})
        is_loaded, name = check_model_loaded("llama3", httpserver.url_for(""))
        assert is_loaded is True
        assert name == "llama3:latest"

    def test_not_loaded(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/ps").respond_with_json({"processes": [{"model": "mistral:7b"}]})
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


class TestPreloadModelFromModels:
    def test_already_loaded(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/ps").respond_with_json({"processes": [{"model": "llama3:latest"}]})
        success, error = preload_model("llama3:latest", httpserver.url_for(""), retries=0)
        assert success is True
        assert error is None

    def test_successful_preload(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/ps").respond_with_json({"processes": []})
        httpserver.expect_request("/api/generate", method="POST").respond_with_json({"response": "ok"})
        success, error = preload_model("llama3:latest", httpserver.url_for(""), retries=0)
        assert success is True

    def test_preload_failure(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/ps").respond_with_json({"processes": []})
        httpserver.expect_request("/api/generate", method="POST").respond_with_data("error", status=500)
        success, error = preload_model("llama3:latest", httpserver.url_for(""), retries=0)
        assert success is False
        assert error is not None

    def test_skip_loaded_check(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/generate", method="POST").respond_with_json({"response": "ok"})
        success, error = preload_model("llama3:latest", httpserver.url_for(""), retries=0, check_loaded_first=False)
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
