"""Tests for infrastructure/llm/ollama_utils.py.

Tests Ollama utility functions for model discovery and server management.
These tests run against a real Ollama installation when available.
"""

import pytest

from infrastructure.llm.utils.ollama import (
    is_ollama_running,
    get_available_models,
    get_model_names,
    select_best_model,
    select_small_fast_model,
    ensure_ollama_ready,
    get_model_info,
    check_model_loaded,
    preload_model,
    DEFAULT_MODEL_PREFERENCES,
)


class TestIsOllamaRunning:
    """Test is_ollama_running function."""

    def test_is_ollama_running_returns_bool(self):
        """Test that is_ollama_running returns a boolean."""
        result = is_ollama_running()
        assert isinstance(result, bool)

    def test_is_ollama_running_with_bad_url(self):
        """Test is_ollama_running with invalid URL returns False."""
        result = is_ollama_running(base_url="http://localhost:99999", timeout=0.5)
        assert result is False

    def test_is_ollama_running_with_default_url(self):
        """Test is_ollama_running with default URL."""
        result = is_ollama_running()
        # Just verify it returns a boolean and doesn't crash
        assert isinstance(result, bool)


@pytest.mark.requires_ollama
class TestGetAvailableModels:
    """Test get_available_models function (requires Ollama)."""

    @pytest.fixture(autouse=True)
    def check_ollama(self):
        """Skip tests if Ollama is not available."""
        if not is_ollama_running():
            pytest.skip("Ollama server not available")

    def test_get_available_models_returns_list(self):
        """Test that get_available_models returns a list."""
        models = get_available_models()
        assert isinstance(models, list)

    def test_get_available_models_has_entries(self):
        """Test that get_available_models returns models."""
        models = get_available_models()
        assert len(models) > 0, "Ollama should have at least one model installed"

    def test_get_available_models_has_name_field(self):
        """Test that model entries have 'name' field."""
        models = get_available_models()
        for model in models:
            assert "name" in model, f"Model entry missing 'name': {model}"


@pytest.mark.requires_ollama
class TestGetModelNames:
    """Test get_model_names function (requires Ollama)."""

    @pytest.fixture(autouse=True)
    def check_ollama(self):
        """Skip tests if Ollama is not available."""
        if not is_ollama_running():
            pytest.skip("Ollama server not available")

    def test_get_model_names_returns_list(self):
        """Test that get_model_names returns a list of strings."""
        names = get_model_names()
        assert isinstance(names, list)
        for name in names:
            assert isinstance(name, str)

    def test_get_model_names_has_entries(self):
        """Test that get_model_names returns model names."""
        names = get_model_names()
        assert len(names) > 0, "Ollama should have at least one model installed"
        print(f"Available models: {names}")


@pytest.mark.requires_ollama
class TestSelectBestModel:
    """Test select_best_model function (requires Ollama)."""

    @pytest.fixture(autouse=True)
    def check_ollama(self):
        """Skip tests if Ollama is not available."""
        if not is_ollama_running():
            pytest.skip("Ollama server not available")

    def test_select_best_model_returns_string(self):
        """Test that select_best_model returns a string."""
        model = select_best_model()
        assert model is not None
        assert isinstance(model, str)
        print(f"Selected model: {model}")

    def test_select_best_model_with_preferences(self):
        """Test select_best_model respects preferences."""
        available = get_model_names()
        if len(available) > 0:
            # Use first available as preference
            model = select_best_model(preferences=[available[0]])
            assert model == available[0]

    def test_select_best_model_partial_match(self):
        """Test select_best_model with partial name matching."""
        available = get_model_names()
        if len(available) > 0:
            # Get base name (without tag)
            first_model = available[0]
            base_name = first_model.split(":")[0]
            
            model = select_best_model(preferences=[base_name])
            assert model is not None
            assert base_name in model

    def test_select_best_model_fallback(self):
        """Test select_best_model falls back to first available."""
        model = select_best_model(preferences=["nonexistent_model"])
        # Should fall back to first available
        assert model is not None


@pytest.mark.requires_ollama
class TestSelectSmallFastModel:
    """Test select_small_fast_model function (requires Ollama)."""

    @pytest.fixture(autouse=True)
    def check_ollama(self):
        """Skip tests if Ollama is not available."""
        if not is_ollama_running():
            pytest.skip("Ollama server not available")

    def test_select_small_fast_model_returns_string(self):
        """Test that select_small_fast_model returns a model name."""
        model = select_small_fast_model()
        assert model is not None
        assert isinstance(model, str)
        print(f"Selected fast model: {model}")


@pytest.mark.requires_ollama
class TestEnsureOllamaReady:
    """Test ensure_ollama_ready function (requires Ollama)."""

    @pytest.fixture(autouse=True)
    def check_ollama(self):
        """Skip tests if Ollama is not available."""
        if not is_ollama_running():
            pytest.skip("Ollama server not available")

    def test_ensure_ollama_ready_returns_true(self):
        """Test ensure_ollama_ready returns True when Ollama is ready."""
        result = ensure_ollama_ready(auto_start=False)
        assert result is True

    def test_ensure_ollama_ready_no_auto_start(self):
        """Test ensure_ollama_ready with auto_start=False."""
        result = ensure_ollama_ready(auto_start=False)
        # Should still return True if already running
        assert isinstance(result, bool)


@pytest.mark.requires_ollama
class TestGetModelInfo:
    """Test get_model_info function (requires Ollama)."""

    @pytest.fixture(autouse=True)
    def check_ollama(self):
        """Skip tests if Ollama is not available."""
        if not is_ollama_running():
            pytest.skip("Ollama server not available")

    def test_get_model_info_returns_dict(self):
        """Test get_model_info returns model info dict."""
        models = get_model_names()
        if models:
            info = get_model_info(models[0])
            assert info is not None
            assert isinstance(info, dict)
            assert "name" in info

    def test_get_model_info_nonexistent(self):
        """Test get_model_info returns None for nonexistent model."""
        info = get_model_info("nonexistent_model_xyz")
        assert info is None


class TestDefaultPreferences:
    """Test DEFAULT_MODEL_PREFERENCES constant."""

    def test_default_preferences_is_list(self):
        """Test DEFAULT_MODEL_PREFERENCES is a list."""
        assert isinstance(DEFAULT_MODEL_PREFERENCES, list)

    def test_default_preferences_not_empty(self):
        """Test DEFAULT_MODEL_PREFERENCES is not empty."""
        assert len(DEFAULT_MODEL_PREFERENCES) > 0

    def test_default_preferences_are_strings(self):
        """Test all preferences are strings."""
        for pref in DEFAULT_MODEL_PREFERENCES:
            assert isinstance(pref, str)


class TestOllamaUtilsWithoutServer:
    """Tests that work without Ollama server running."""

    def test_get_available_models_no_server(self):
        """Test get_available_models with no server returns empty list."""
        models = get_available_models(base_url="http://localhost:99999", timeout=0.5)
        assert models == []

    def test_get_available_models_retries(self):
        """Test get_available_models with retry logic."""
        # Should retry on timeout
        models = get_available_models(
            base_url="http://localhost:99999",
            timeout=0.1,
            retries=1
        )
        assert models == []

    def test_get_model_names_no_server(self):
        """Test get_model_names with no server returns empty list."""
        names = get_model_names(base_url="http://localhost:99999")
        assert names == []

    def test_select_best_model_no_server(self):
        """Test select_best_model with no server returns None."""
        model = select_best_model(base_url="http://localhost:99999")
        assert model is None

    def test_ensure_ollama_ready_no_server_no_auto_start(self):
        """Test ensure_ollama_ready returns False without server and auto_start."""
        result = ensure_ollama_ready(
            base_url="http://localhost:99999",
            auto_start=False
        )
        assert result is False


class TestCheckModelLoaded:
    """Tests for check_model_loaded function."""

    def test_check_model_loaded_no_server(self):
        """Test check_model_loaded with no server returns (False, None)."""
        is_loaded, model_name = check_model_loaded(
            "test-model",
            base_url="http://localhost:99999"
        )
        assert is_loaded is False
        assert model_name is None

    def test_check_model_loaded_returns_tuple(self):
        """Test that check_model_loaded returns a tuple."""
        result = check_model_loaded("llama3-gradient")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert result[1] is None or isinstance(result[1], str)

    def test_check_model_loaded_timeout(self):
        """Test check_model_loaded with timeout."""
        is_loaded, model_name = check_model_loaded(
            "test-model",
            base_url="http://localhost:99999",
            timeout=0.1
        )
        assert is_loaded is False
        assert model_name is None

    @pytest.mark.requires_ollama
    def test_check_model_loaded_with_server(self):
        """Test check_model_loaded with running Ollama server."""
        if not is_ollama_running():
            pytest.skip("Ollama server not available")
        
        # Get first available model
        models = get_model_names()
        if not models:
            pytest.skip("No models available")
        
        model_name = models[0]
        is_loaded, loaded_name = check_model_loaded(model_name)
        
        # Result should be a valid tuple
        assert isinstance(is_loaded, bool)
        # loaded_name is either a string or None
        assert loaded_name is None or isinstance(loaded_name, str)

    @pytest.mark.requires_ollama
    def test_check_model_loaded_partial_match(self):
        """Test check_model_loaded with partial model name match."""
        if not is_ollama_running():
            pytest.skip("Ollama server not available")
        
        models = get_model_names()
        if not models:
            pytest.skip("No models available")
        
        # Get base name without tag
        first_model = models[0]
        base_name = first_model.split(":")[0]
        
        is_loaded, loaded_name = check_model_loaded(base_name)
        assert isinstance(is_loaded, bool)
        assert loaded_name is None or isinstance(loaded_name, str)


class TestPreloadModel:
    """Tests for preload_model function."""

    def test_preload_model_no_server(self):
        """Test preload_model with no server returns (False, error)."""
        success, error = preload_model(
            "test-model",
            base_url="http://localhost:99999",
            timeout=1.0
        )
        assert success is False
        assert error is not None
        assert isinstance(error, str)

    def test_preload_model_returns_tuple(self):
        """Test that preload_model returns a tuple."""
        result = preload_model("nonexistent-model", timeout=1.0)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert result[1] is None or isinstance(result[1], str)

    def test_preload_model_check_loaded_first(self):
        """Test preload_model with check_loaded_first=True."""
        # With non-existent server, should return False quickly
        success, error = preload_model(
            "test-model",
            base_url="http://localhost:99999",
            timeout=1.0,
            check_loaded_first=True
        )
        assert success is False
        assert error is not None

    @pytest.mark.requires_ollama
    def test_preload_model_with_server(self):
        """Test preload_model with running Ollama server."""
        if not is_ollama_running():
            pytest.skip("Ollama server not available")
        
        # Get first available model
        models = get_model_names()
        if not models:
            pytest.skip("No models available")
        
        model_name = models[0]
        success, error = preload_model(model_name, timeout=60.0)
        
        # Should either succeed or fail gracefully
        assert isinstance(success, bool)
        assert error is None or isinstance(error, str)

    @pytest.mark.requires_ollama
    def test_preload_model_already_loaded(self):
        """Test preload_model when model is already loaded."""
        if not is_ollama_running():
            pytest.skip("Ollama server not available")
        
        models = get_model_names()
        if not models:
            pytest.skip("No models available")
        
        model_name = models[0]
        
        # Preload once
        success1, error1 = preload_model(model_name, timeout=60.0)
        if not success1:
            pytest.skip(f"Could not preload model {model_name}: {error1}")
        
        # Preload again - should detect it's already loaded
        success2, error2 = preload_model(model_name, check_loaded_first=True, timeout=60.0)
        assert success2 is True
        assert error2 is None

