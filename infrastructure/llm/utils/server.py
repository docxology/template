"""Ollama server management: status checks, startup, and readiness.

Provides utilities for:
- Checking Ollama server status
- Starting Ollama server if needed
- Ensuring Ollama is ready with models available

Note:
    This is an implementation module. Prefer importing from
    ``infrastructure.llm.utils.ollama``, which re-exports everything here
    alongside model-discovery utilities under a stable, consolidated API.
"""

from __future__ import annotations

import shutil
import subprocess
import time

try:
    import requests
    from requests.exceptions import ConnectionError as RequestsConnectionError
    from requests.exceptions import RequestException, Timeout
    _requests_available = True
except ImportError:
    requests = None  # type: ignore[assignment]
    RequestsConnectionError = OSError  # type: ignore[assignment,misc]
    RequestException = OSError  # type: ignore[assignment]
    Timeout = OSError  # type: ignore[assignment]
    _requests_available = False

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


def is_ollama_running(base_url: str = "http://localhost:11434", timeout: float = 2.0) -> bool:
    """Check if Ollama server is running and responding."""
    if not _requests_available:
        logger.debug("requests not installed; cannot check Ollama server status")
        return False
    try:
        logger.debug(f"Checking Ollama server at {base_url}...")
        response = requests.get(f"{base_url}/api/tags", timeout=timeout)
        if response.status_code == 200:
            logger.debug(f"Ollama server responding at {base_url}")
            return True
        logger.warning(f"Ollama server returned status {response.status_code} at {base_url}")
        return False
    except Timeout:
        logger.debug(f"Ollama server timeout at {base_url} (timeout={timeout}s)")
        return False
    except RequestsConnectionError as e:
        logger.debug(f"Ollama server connection failed at {base_url}: {e}")
        return False
    except RequestException as e:
        logger.debug(f"Ollama server request failed at {base_url}: {e}")
        return False


def start_ollama_server(wait_seconds: float = 3.0, max_retries: int = 2) -> bool:
    """Attempt to start the Ollama server with detailed logging.

    Args:
        wait_seconds: How long to wait for server to start
        max_retries: Number of retry attempts on failure

    Returns:
        True if server started successfully, False otherwise
    """
    logger.info("Attempting to start Ollama server...")

    for attempt in range(max_retries + 1):
        try:
            # Log attempt number
            if attempt > 0:
                logger.info(f"Retry {attempt}/{max_retries}...")

            ollama_bin = shutil.which("ollama")
            if not ollama_bin:
                logger.error("Ollama command not found. Install Ollama: https://ollama.ai")
                return False

            # Start server: list argv only, no shell interpolation.
            process = subprocess.Popen(
                [ollama_bin, "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            logger.debug(f"Started Ollama process (PID: {process.pid})")

            # Wait and verify
            time.sleep(wait_seconds)
            if is_ollama_running():
                logger.info("✓ Ollama server started successfully")
                return True
            else:
                logger.warning(
                    f"Ollama process started but server not responding after {wait_seconds}s"
                )

        except FileNotFoundError:
            logger.error("Ollama command not found. Install Ollama: https://ollama.ai")
            return False
        except PermissionError as e:
            logger.error(f"Permission denied starting Ollama: {e}")
            return False
        except subprocess.SubprocessError as e:
            logger.warning(f"Failed to start Ollama (attempt {attempt + 1}): {e}")
            if attempt < max_retries:
                wait_time = (attempt + 1) * 1.0
                logger.debug(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)

    logger.error("Failed to start Ollama server after all retries")
    return False


def ensure_ollama_ready(base_url: str = "http://localhost:11434", auto_start: bool = True) -> bool:
    """Ensure Ollama server is running and has models available."""
    # Import here to avoid circular dependency
    from infrastructure.llm.utils.models import get_model_names

    # Check if running
    if not is_ollama_running(base_url):
        if auto_start:
            logger.info("Ollama server not running, attempting to start...")
            if start_ollama_server():
                logger.info("Ollama server started successfully")
            else:
                logger.warning("Failed to start Ollama server automatically")
                logger.info("Possible reasons:")
                logger.info("  - Ollama not installed (install from https://ollama.ai)")
                logger.info("  - Permission denied (check file permissions)")
                logger.info("  - Port 11434 already in use")
                return False
        else:
            logger.debug("Ollama not running and auto_start=False")
            return False

    # Check for available models with progress logging
    logger.debug("Checking for available models...")
    models = get_model_names(base_url)
    if not models:
        logger.warning("No Ollama models available")
        logger.info("Install a model with: ollama pull llama3-gradient")
        logger.info("Recommended models:")
        logger.info("  - llama3-gradient:latest (4.7GB, 256K context)")
        logger.info("  - llama3.1:latest (4.7GB, 128K context)")
        return False

    logger.info(f"Ollama ready with {len(models)} model(s)")
    if len(models) <= 5:
        logger.info(f"  Models: {', '.join(models)}")
    else:
        logger.info(f"  Models: {', '.join(models[:5])} ... and {len(models) - 5} more")
    return True
