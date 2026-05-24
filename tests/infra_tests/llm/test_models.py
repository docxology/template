"""Tests for infrastructure.llm.utils.models."""

from __future__ import annotations

import pytest
from pytest_httpserver import HTTPServer

from infrastructure.llm.utils.models import (
    check_model_loaded,
    get_available_model_info,
    get_model_info,
    get_model_names,
    preload_model,
    select_best_model,
    small_fast_preference_matches,
)

SAMPLE_MODELS = [
    {"name": "smollm2", "size": 135000000},
    {"name": "gemma3:4b", "size": 4000000000},
    {"name": "llama3.1:latest", "size": 8000000000},
]


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
    def test_selection_strategies(
        self, httpserver: HTTPServer, preferences, models_payload, expected
    ):
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
    def test_loaded_state(
        self, httpserver: HTTPServer, processes, query, expected_loaded, expected_name
    ):
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
        httpserver.expect_request("/api/ps").respond_with_json(
            {"processes": [{"model": "smollm2"}]}
        )
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
        success, error = preload_model(
            "smollm2", base_url="http://localhost:1", timeout=0.5, retries=0
        )
        assert success is False
        assert error is not None

    def test_http_error(self, httpserver: HTTPServer):
        httpserver.expect_request("/api/ps").respond_with_json({"processes": []})
        httpserver.expect_request("/api/generate").respond_with_data("model not found", status=404)
        success, error = preload_model("smollm2", base_url=httpserver.url_for(""), retries=0)
        assert success is False
