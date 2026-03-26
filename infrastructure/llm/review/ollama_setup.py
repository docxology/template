"""Ollama server management and LLM client setup for manuscript review.

Handles server readiness checks, model selection, warmup, and client
construction with review-specific configuration.
"""

from __future__ import annotations

import os
import shutil
import time

from infrastructure.core.logging.utils import (
    get_logger,
    log_substep,
    log_success,
)
from infrastructure.core.logging.progress import (
    log_with_spinner,
    Spinner,
)

from infrastructure.llm.core.client import LLMClient
from infrastructure.llm.core.config import OllamaClientConfig

from infrastructure.llm.utils.ollama import (
    is_ollama_running,
    ensure_ollama_ready,
    select_best_model,
    get_available_model_info,
    check_model_loaded,
    preload_model,
)

from infrastructure.llm.core._prompt_availability import PROMPT_SYSTEM_AVAILABLE

if PROMPT_SYSTEM_AVAILABLE:
    from infrastructure.llm.core._prompt_availability import get_default_loader

logger = get_logger(__name__)

_DEFAULT_REVIEW_SYSTEM_PROMPT = (
    "You are an expert academic manuscript reviewer with extensive experience in peer review"
    " for top-tier journals. Provide thorough, constructive, and professional reviews.\n\n"
    "Guidelines:\n"
    "- Base your assessment solely on the manuscript text provided\n"
    "- Cite sections, passages, or elements when making observations\n"
    "- Balance strengths with areas for improvement\n"
    "- Use markdown formatting and complete all requested sections with substantive content"
)


def get_manuscript_review_system_prompt() -> str:
    """Get the system prompt for manuscript review."""
    if PROMPT_SYSTEM_AVAILABLE:
        try:
            loader = get_default_loader()
            return loader.get_system_prompt("manuscript_review")
        except (ImportError, AttributeError, OSError, FileNotFoundError, KeyError) as e:  # noqa: BLE001 — fall back to built-in default prompt
            logger.warning(f"Could not load system prompt from prompt system, using built-in default: {e}")

    return _DEFAULT_REVIEW_SYSTEM_PROMPT


def create_review_client(model_name: str) -> LLMClient:
    """Build an LLMClient configured for manuscript review: review timeout, system prompt injected.

    Side effect: reads LLM_LONG_MAX_TOKENS env var and logs the token limit source at DEBUG.
    """
    base = OllamaClientConfig.from_env()
    config = base.with_overrides(
        default_model=model_name,
        timeout=base.review_timeout,
        system_prompt=get_manuscript_review_system_prompt(),
        auto_inject_system_prompt=True,
    )

    source = (
        f"environment variable LLM_LONG_MAX_TOKENS={config.long_max_tokens}"
        if os.environ.get("LLM_LONG_MAX_TOKENS")
        else f"config default long_max_tokens={config.long_max_tokens}"
    )
    logger.debug(f"Review max_tokens configuration: {source}")
    return LLMClient(config)

def select_and_start_ollama_model() -> tuple[bool, str | None]:
    """Ensure Ollama is running and select the best available model.

    Verifies the Ollama binary is installed, starts the server if it is not
    already running (up to 3 attempts with exponential backoff), then queries
    the available model list and selects the best candidate for manuscript review.

    Returns:
        (True, model_name) on success, (False, None) if Ollama is unavailable
        or no suitable model is found.
    """
    log_substep("Checking Ollama availability...")
    auto_start = os.environ.get("OLLAMA_AUTO_START", "true").lower() == "true"

    if not shutil.which("ollama"):
        logger.error("❌ Ollama command not found. Install Ollama: https://ollama.ai")
        return False, None

    max_retries = 3
    for attempt in range(max_retries):
        if attempt > 0:
            wait_time = min(2**attempt, 10)
            time.sleep(wait_time)

        if not is_ollama_running():
            if auto_start:
                logger.info("    Ollama not running, attempting to start automatically...")
                if ensure_ollama_ready(auto_start=True):
                    log_success("Ollama server started and ready", logger)
                    break  # auto-start succeeded — server is ready
                else:
                    if attempt == max_retries - 1:
                        logger.warning(
                            "❌ Failed to start Ollama server automatically after retries"
                        )
                        return False, None
            else:
                logger.warning("❌ Ollama server is not running")
                return False, None
        else:
            log_success("Ollama server is running", logger)
            break  # server already running — no start needed

    available_models = get_available_model_info()
    if not available_models:
        logger.warning("❌ No Ollama models available")
        return False, None

    model_names = [m.get("name", "unknown") for m in available_models]
    logger.debug(f"    Found {len(model_names)} model(s): {', '.join(model_names[:5])}")
    model = select_best_model()
    if not model:
        logger.warning("❌ Could not select a suitable model")
        return False, None

    return True, model


def warmup_model(client: LLMClient, text_preview: str, model_name: str) -> tuple[bool, float]:
    """Pre-load the model into GPU memory and generate a quick test response."""
    log_substep("Warming up model...")
    warmup_timeout = client.config.review_timeout
    logger.info(f"    Timeout: {warmup_timeout:.0f}s for warmup")

    logger.debug("    Checking loaded models via Ollama API...")
    base_url = (client.config.base_url or "http://localhost:11434").rstrip("/")
    model_preloaded, loaded_model = check_model_loaded(model_name, base_url=base_url)

    need_preload = False
    if model_preloaded:
        logger.info(f"    ✓ Model {model_name} is already loaded in GPU memory")
    elif loaded_model:
        logger.info(f"    ⚠️ Different model loaded: {loaded_model}")
        need_preload = True
    else:
        logger.info("    ⏳ No model currently loaded in GPU memory")
        need_preload = True

    if need_preload:
        logger.info(f"    ⏳ Loading {model_name} into GPU memory...")
        preload_start = time.time()
        with log_with_spinner(
            f"Loading {model_name} into GPU memory...", logger, final_message=None
        ):
            preload_timeout = min(15.0, float(warmup_timeout)) if warmup_timeout else 15.0
            preload_success, preload_error = preload_model(
                model_name,
                base_url=base_url,
                timeout=preload_timeout,
                retries=0,
            )

        preload_elapsed = time.time() - preload_start
        if preload_success:
            logger.info(f"    ✓ Model loaded successfully in {preload_elapsed:.1f}s")
        else:
            error_msg = f": {preload_error}" if preload_error else ""
            logger.warning(f"    ⚠️ Preload returned error{error_msg}, continuing anyway...")

    prompt = (
        f"In exactly one sentence, what is the main topic of this text?\\n\\n{text_preview[:500]}"
    )

    start_time = time.time()
    response_chunks = []
    first_token_time = None

    spinner = Spinner("Waiting for first token...", delay=0.1)
    spinner.start()

    try:
        for chunk in client.stream_short(prompt):
            if first_token_time is None:
                first_token_time = time.time()
                time_to_first = first_token_time - start_time
                spinner.stop()
                logger.info(f"    ✓ First token in {time_to_first:.1f}s - generating response...")
            response_chunks.append(chunk)

        elapsed = time.time() - start_time
        response = "".join(response_chunks)

        if first_token_time is not None:
            # first_token_time is when the first token arrived; generation_time excludes TTFT
            generation_time = elapsed - (first_token_time - start_time)
            output_tokens = int(len(response.split()) * 1.3)
            tokens_per_sec = output_tokens / generation_time if generation_time > 0 else 0
        else:
            # No tokens received — streaming produced no output
            tokens_per_sec = 0

        log_success(f"Warmup complete ({elapsed:.1f}s)", logger)
        response_preview = response[:80].replace("\\n", " ")
        if len(response) > 80:
            response_preview += "..."
        logger.info(f"    Response: {response_preview}")
        logger.info(f"    Performance: ~{tokens_per_sec:.1f} tokens/sec")

        return True, tokens_per_sec

    except Exception as e:  # noqa: BLE001 — intentional: warmup errors are non-fatal; caller falls back to first actual request
        spinner.stop()
        elapsed = time.time() - start_time
        logger.error(f"Model warmup failed after {elapsed:.1f}s: {e}")
        return False, 0.0
