"""Ollama model discovery, selection, readiness and preload contracts.

Real-daemon cases assert daemon state and model-selection outcomes, not generated
prose quality or response length. Deterministic HTTP tests cover transport paths.
"""

from pathlib import Path

import pytest

from infrastructure.llm.utils.ollama import (
    DEFAULT_MODEL_PREFERENCES,
    check_model_loaded,
    ensure_ollama_ready,
    get_available_model_info,
    get_model_info,
    get_model_names,
    is_ollama_running,
    preload_model,
    pull_ollama_model,
    select_best_model,
    select_small_fast_model,
)


@pytest.mark.requires_ollama
class TestIsOllamaRunning:
    """Test is_ollama_running function."""

    def test_is_ollama_running_with_bad_url(self):
        """Test is_ollama_running with invalid URL returns False."""
        result = is_ollama_running(base_url="http://localhost:99999", timeout=0.5)
        assert result is False


@pytest.mark.requires_ollama
class TestSelectBestModel:
    """Test select_best_model function (requires Ollama)."""

    @pytest.fixture(autouse=True)
    def check_ollama(self, ensure_ollama_for_tests):
        """Ensure Ollama is running and functional for tests."""
        # Fixture dependency ensures Ollama is ready
        # If Ollama can't be started, ensure_ollama_for_tests will fail loudly
        pass

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


@pytest.mark.requires_ollama
class TestEnsureOllamaReady:
    """Test ensure_ollama_ready function (requires Ollama)."""

    @pytest.fixture(autouse=True)
    def check_ollama(self, ensure_ollama_for_tests):
        """Ensure Ollama is running and functional for tests."""
        # Fixture dependency ensures Ollama is ready
        # If Ollama can't be started, ensure_ollama_for_tests will fail loudly
        pass

    def test_ensure_ollama_ready_returns_true(self):
        """Test ensure_ollama_ready returns True when Ollama is ready."""
        result = ensure_ollama_ready(auto_start=False)
        assert result is True


@pytest.mark.requires_ollama
class TestGetModelInfo:
    """Test get_model_info function (requires Ollama)."""

    @pytest.fixture(autouse=True)
    def check_ollama(self, ensure_ollama_for_tests):
        """Ensure Ollama is running and functional for tests."""
        # Fixture dependency ensures Ollama is ready
        # If Ollama can't be started, ensure_ollama_for_tests will fail loudly
        pass

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
        models = get_available_model_info(base_url="http://localhost:99999", timeout=0.5)
        assert models == []

    def test_get_available_models_retries(self):
        """Test get_available_models with retry logic."""
        # Should retry on timeout
        models = get_available_model_info(base_url="http://localhost:99999", timeout=0.1, retries=1)
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
        result = ensure_ollama_ready(base_url="http://localhost:99999", auto_start=False)
        assert result is False


class TestCheckModelLoaded:
    """Tests for check_model_loaded function."""

    def test_check_model_loaded_no_server(self):
        """Test check_model_loaded with no server returns (False, None)."""
        is_loaded, model_name = check_model_loaded("test-model", base_url="http://localhost:99999")
        assert is_loaded is False
        assert model_name is None

    def test_check_model_loaded_timeout(self):
        """Test check_model_loaded with timeout."""
        is_loaded, model_name = check_model_loaded("test-model", base_url="http://localhost:99999", timeout=0.1)
        assert is_loaded is False
        assert model_name is None


class TestPreloadModel:
    """Tests for preload_model function."""

    def test_preload_model_no_server(self):
        """Test preload_model with no server returns (False, error)."""
        success, error = preload_model("test-model", base_url="http://localhost:99999", timeout=1.0)
        assert success is False
        assert error is not None
        assert isinstance(error, str)

    def test_preload_model_check_loaded_first(self):
        """Test preload_model with check_loaded_first=True."""
        # With non-existent server, should return False quickly
        success, error = preload_model(
            "test-model",
            base_url="http://localhost:99999",
            timeout=1.0,
            check_loaded_first=True,
        )
        assert success is False
        assert error is not None

    @pytest.mark.requires_ollama
    def test_preload_model_already_loaded(self):
        """Test preload_model when model is already loaded."""
        assert is_ollama_running(), "requires_ollama fixture should ensure Ollama is running"

        model_name = select_small_fast_model()
        if model_name is None:
            models = get_model_names()
            assert models, "requires_ollama fixture should ensure at least one model is installed"
            model_name = models[0]

        # Preload once
        success1, error1 = preload_model(model_name, timeout=30.0, retries=1)
        assert success1, f"Could not preload model {model_name}: {error1}"

        # Preload again - should detect it's already loaded
        success2, error2 = preload_model(
            model_name,
            check_loaded_first=True,
            timeout=30.0,
            retries=1,
        )
        assert success2 is True
        assert error2 is None


class TestSmallFastPreferenceMatches:
    """Unit tests for small_fast_preference_matches (no daemon)."""

    def test_matches_smollm2(self):
        from infrastructure.llm.utils.models import small_fast_preference_matches

        assert small_fast_preference_matches(["smollm2"]) is True
        assert small_fast_preference_matches(["registry/smollm2:latest"]) is True

    def test_matches_gemma_prefix(self):
        from infrastructure.llm.utils.models import small_fast_preference_matches

        assert small_fast_preference_matches(["gemma2:2b"]) is True

    def test_no_match_only_large(self):
        from infrastructure.llm.utils.models import small_fast_preference_matches

        assert small_fast_preference_matches(["llama3:70b"]) is False
        assert small_fast_preference_matches([]) is False


def _ollama_stub(tmp_path: Path, sh_body: str) -> Path:
    """Write a POSIX ``ollama`` stub script and return its path."""
    exe = tmp_path / "ollama"
    exe.write_text("#!/bin/sh\nset -e\n" + sh_body)
    exe.chmod(0o755)
    return exe


class TestPullOllamaModel:
    """``pull_ollama_model`` with real stub scripts and injectable ``which`` (no import patching)."""

    def test_pull_returns_false_when_ollama_missing(self):
        ok, err = pull_ollama_model("smollm2", timeout=1.0, which=lambda _cmd: None)
        assert ok is False
        assert err is not None
        assert "PATH" in err

    def test_pull_success_on_zero_exit(self, tmp_path):
        stub = _ollama_stub(tmp_path, 'test "$1" = pull && test "$2" = smollm2\nexit 0\n')
        ok, err = pull_ollama_model(
            "smollm2",
            timeout=5.0,
            which=lambda cmd: str(stub) if cmd == "ollama" else None,
        )
        assert ok is True
        assert err is None

    def test_pull_failure_on_nonzero_exit(self, tmp_path):
        stub = _ollama_stub(tmp_path, "echo network error >&2\nexit 1\n")
        ok, err = pull_ollama_model(
            "smollm2",
            timeout=5.0,
            which=lambda cmd: str(stub) if cmd == "ollama" else None,
        )
        assert ok is False
        assert err is not None
        assert "network error" in err

    def test_pull_timeout(self, tmp_path):
        stub = _ollama_stub(tmp_path, "sleep 30\nexit 0\n")
        ok, err = pull_ollama_model(
            "smollm2",
            timeout=0.3,
            which=lambda cmd: str(stub) if cmd == "ollama" else None,
        )
        assert ok is False
        assert err is not None
        assert "timed out" in err.lower()
