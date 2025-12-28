"""Pytest configuration for infrastructure layer tests."""
import os
import pytest

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

@pytest.fixture(scope="session")
def ensure_ollama_for_tests():
    """Ensure Ollama is running and functional for tests.

    This fixture:
    - Checks if Ollama is running
    - Attempts to start Ollama automatically if not running
    - Verifies Ollama is responding and has models
    - FAILS loudly if Ollama can't be started or isn't working

    This fixture runs once per test session and ensures all tests
    marked with @pytest.mark.requires_ollama have a working Ollama instance.
    """
    from infrastructure.llm.utils.ollama import (
        is_ollama_running,
        ensure_ollama_ready,
        get_model_names,
    )
    from infrastructure.core.logging_utils import get_logger

    logger = get_logger(__name__)

    # Check if Ollama is already running
    if is_ollama_running():
        logger.info("✓ Ollama server is already running")
    else:
        logger.warning("⚠️  Ollama server is not running - attempting to start...")
        if not ensure_ollama_ready(auto_start=True):
            pytest.fail(
                "\n" + "="*80 + "\n"
                "❌ CRITICAL: Ollama server cannot be started for tests!\n"
                "="*80 + "\n"
                "Tests require a working Ollama installation.\n\n"
                "Troubleshooting:\n"
                "  1. Install Ollama: https://ollama.ai\n"
                "  2. Start Ollama manually: ollama serve\n"
                "  3. Verify installation: ollama --version\n"
                "  4. Check if port 11434 is available: lsof -i :11434\n"
                "  5. Install at least one model: ollama pull llama3-gradient\n\n"
                "To skip Ollama tests: pytest -m 'not requires_ollama'\n"
                "="*80
            )

    # Verify Ollama has models available
    models = get_model_names()
    if not models:
        pytest.fail(
            "\n" + "="*80 + "\n"
            "❌ CRITICAL: Ollama server is running but has no models!\n"
            "="*80 + "\n"
            "Tests require at least one Ollama model to be installed.\n\n"
            "Install a model:\n"
            "  ollama pull llama3-gradient    # Recommended (4.7GB, 256K context)\n"
            "  ollama pull llama3.1:latest     # Alternative (4.7GB, 128K context)\n"
            "  ollama pull gemma2:2b          # Small/fast option (2B params)\n\n"
            "Verify models: ollama list\n"
            "="*80
        )

    logger.info(f"✓ Ollama ready for tests with {len(models)} model(s): {', '.join(models[:3])}")
    return True
