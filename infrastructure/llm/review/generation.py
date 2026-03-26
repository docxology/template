"""Core review generation logic: streaming, retry, and text extraction.

Contains the low-level generation machinery used by the convenience wrappers
in generator.py. Separated to keep each module under 300 LOC.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from infrastructure.llm.templates.base import ResearchTemplate
from pathlib import Path

from infrastructure.core.logging.utils import (
    get_logger,
    log_substep,
    log_success,
)
from infrastructure.core.logging.progress import StreamingProgress

from infrastructure.llm.core.client import LLMClient
from infrastructure.llm.core.config import GenerationOptions, OllamaClientConfig

from infrastructure.llm.utils.heartbeat import StreamHeartbeatMonitor
from infrastructure.llm.validation.repetition import (
    detect_repetition,
    deduplicate_sections,
)
from infrastructure.llm.templates.manuscript import (
    ManuscriptTranslationAbstract,
    TRANSLATION_LANGUAGES,
)

from infrastructure.llm.review.metrics import ReviewMetrics, ManuscriptInputMetrics, estimate_tokens
from infrastructure.llm.review.quality import validate_review_quality, _is_small_model, ReviewType
# Cross-subsystem import: llm/review depends on validation/pdf_validator for text extraction.
# This is an intentional seam — PDF text extraction lives in validation because it is also
# used by the output validator. If this becomes a problem, move extract_text_from_pdf to
# infrastructure/core/pdf_utils.py so both subsystems can import without circular deps.
from infrastructure.validation.content.pdf_validator import extract_text_from_pdf
from infrastructure.core.exceptions import PDFValidationError

from infrastructure.llm.core._prompt_availability import PROMPT_SYSTEM_AVAILABLE

if PROMPT_SYSTEM_AVAILABLE:
    from infrastructure.llm.prompts.composer import PromptComposer

logger = get_logger(__name__)


def extract_manuscript_text(
    pdf_path: Path | str,
    max_input_length: int | None = None,
) -> tuple[str | None, ManuscriptInputMetrics]:
    """Extract text from a manuscript PDF for LLM review.

    Args:
        pdf_path: Path to the PDF file.
        max_input_length: Maximum characters to return; 0 or None means unlimited.
            Pass ``client.config.max_input_length`` to avoid a redundant env re-read.

    Returns:
        (text, metrics) where text is None if the PDF file does not exist.

    Raises:
        PDFValidationError: If the file exists but cannot be read or is invalid.
    """
    log_substep(f"Extracting text from manuscript: {Path(pdf_path).name}")
    metrics = ManuscriptInputMetrics()

    if isinstance(pdf_path, str):
        pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        logger.error(f"Manuscript PDF not found: {pdf_path}")
        return None, metrics

    try:
        text = extract_text_from_pdf(pdf_path)
        metrics.total_chars = len(text)
        metrics.total_words = len(text.split())
        metrics.total_tokens_est = estimate_tokens(text)
        logger.info(
            f"  Extracted: {metrics.total_chars:,} chars ({metrics.total_words:,} words, ~{metrics.total_tokens_est:,} tokens)"  # noqa: E501
        )
        max_length = max_input_length if max_input_length is not None else OllamaClientConfig.from_env().max_input_length

        if max_length > 0 and len(text) > max_length:
            metrics.truncated = True
            metrics.truncated_chars = max_length
            logger.warning(
                f"  Truncating from {metrics.total_chars:,} to {max_length:,} characters"
            )
            text = text[:max_length] + "\\n\\n[... truncated for LLM context limit ...]"
        else:
            metrics.truncated = False
            metrics.truncated_chars = metrics.total_chars
            logger.info("  Sending full manuscript to LLM (no truncation)")

        return text, metrics
    except PDFValidationError:
        raise
    except OSError as e:
        raise PDFValidationError(f"Failed to read PDF file {pdf_path}: {e}") from e


def _build_retry_prompt(prompt: str, had_off_topic: bool) -> str:
    """Build a modified prompt for a retry, prepending an off-topic warning if needed."""
    if not had_off_topic:
        return prompt
    prefix = "IMPORTANT: You must review the ACTUAL manuscript text provided below.\\n\\n"
    if PROMPT_SYSTEM_AVAILABLE:
        try:
            composer = PromptComposer()
            return composer.add_retry_prompt(prompt, retry_type="off_topic")
        except (ImportError, AttributeError, OSError, KeyError) as e:
            logger.debug(f"PromptComposer retry prompt failed, using plain prefix: {e}")
    return prefix + prompt


def _stream_with_heartbeat(
    client: LLMClient,
    prompt: str,
    options: GenerationOptions,
    review_name: str,
    estimated_total_tokens: int,
    config: OllamaClientConfig,
) -> str:
    """Stream a query with heartbeat monitoring and progress display.

    Falls back to a blocking query if streaming fails.
    """
    try:
        progress = StreamingProgress(
            total=estimated_total_tokens,
            message=f"Generating {review_name}",
            update_interval=0.5,
        )
        heartbeat_monitor = StreamHeartbeatMonitor(
            operation_name=review_name,
            timeout_seconds=config.review_timeout,
            heartbeat_interval=config.heartbeat_interval,
            stall_threshold=config.stall_threshold,
            early_warning_threshold=config.early_warning_threshold,
            logger=logger,
        )
        heartbeat_monitor.set_estimated_total(estimated_total_tokens)
        heartbeat_monitor.start_monitoring()

        response_chunks: list[str] = []
        tokens_generated = 0
        start_gen_time = time.time()
        try:
            for chunk in client.stream_query(prompt, options=options):
                response_chunks.append(chunk)
                tokens_generated += len(chunk.split())
                progress.set(tokens_generated)
                heartbeat_monitor.update_token_received()
        finally:
            heartbeat_monitor.stop_monitoring()

        total_time = time.time() - start_gen_time
        final_tokens_per_sec = tokens_generated / total_time if total_time > 0 else 0
        progress.finish(
            f"    Generated {tokens_generated:,} tokens in {total_time:.1f}s"
            f" ({final_tokens_per_sec:.1f} tokens/sec)"
        )
        return "".join(response_chunks)
    except Exception as e:  # noqa: BLE001 — intentional: fallback to blocking query on any stream failure
        logger.warning(
            f"Streaming query failed, falling back to blocking query: {type(e).__name__}: {e}"
        )
        try:
            return client.query(prompt, options=options)
        except Exception as block_err:
            raise block_err from e


def _deduplicate_response(response: str, best_response: str) -> str:
    """Deduplicate a review response if heavily repetitive; fall back to best_response."""
    has_rep, _, unique_ratio = detect_repetition(response, similarity_threshold=0.8)
    if not (has_rep and unique_ratio < 0.3):
        return response
    original_length = len(response)
    deduped = deduplicate_sections(
        response,
        max_repetitions=2,
        mode="conservative",
        similarity_threshold=0.9,
        min_content_preservation=0.8,
    )
    if len(deduped) / original_length < 0.7:
        return best_response
    return deduped


def generate_review_with_metrics(
    client: LLMClient,
    text: str,
    review_type: ReviewType,
    review_name: str,
    template_class: type[ResearchTemplate],
    model_name: str = "",
    temperature: float = 0.3,
    max_tokens: int | None = None,
    max_retries: int = 1,
) -> tuple[str | None, ReviewMetrics]:
    """Generate a review using a specified template and record execution metrics."""
    log_substep(f"Generating {review_name}...")

    if max_tokens is None:
        max_tokens = client.config.long_max_tokens

    metrics = ReviewMetrics(
        input_chars=len(text),
        input_words=len(text.split()),
        input_tokens_est=estimate_tokens(text),
    )

    client.reset()
    template = template_class()
    prompt = template.render(text=text, max_tokens=max_tokens)
    adjusted_temp = temperature + 0.1 if _is_small_model(model_name) else temperature
    options = GenerationOptions(temperature=adjusted_temp, max_tokens=max_tokens)

    start_time = time.time()
    best_response = ""
    had_off_topic = False
    config = client.config

    for attempt in range(max_retries + 1):
        response = ""  # reset each attempt; overwritten on success
        try:
            current_prompt = prompt
            if attempt > 0:
                client.reset()
                adjusted_temp = min(temperature + 0.15 * attempt, 0.8)
                options = GenerationOptions(temperature=adjusted_temp, max_tokens=max_tokens)
                current_prompt = _build_retry_prompt(prompt, had_off_topic)

            response = _stream_with_heartbeat(
                client, current_prompt, options, review_name, max_tokens, config
            )

            is_valid, issues, details = validate_review_quality(
                response, review_type, model_name=model_name
            )
            had_off_topic = any("off-topic" in issue.lower() for issue in issues)

            if len(response.split()) > len(best_response.split()):
                best_response = response

            if is_valid:
                break
            elif attempt == max_retries:
                response = best_response or response
                if not response:
                    metrics.generation_time_seconds = time.time() - start_time
                    return None, metrics
                logger.warning(
                    f"All {max_retries + 1} attempts failed validation for {review_name}; "
                    f"using longest response ({len(response.split())} words) despite quality issues: "
                    f"{', '.join(issues[:3])}"
                )

        except Exception as e:  # noqa: BLE001 — intentional: retry loop must continue on any LLM client failure
            if attempt < max_retries:
                logger.debug(f"Attempt {attempt + 1} failed for {review_name}: {e}")
            else:
                metrics.generation_time_seconds = time.time() - start_time
                logger.error(f"Error generating {review_name}: {e}")
                return None, metrics

    response = _deduplicate_response(response, best_response)

    metrics.generation_time_seconds = time.time() - start_time
    metrics.output_chars = len(response)
    metrics.output_words = len(response.split())
    metrics.output_tokens_est = estimate_tokens(response)
    metrics.preview = (
        response[:150].replace("\\n", " ") + "..." if len(response) > 150 else response
    )

    log_success(f"{review_name} generated", logger)
    return response, metrics


def generate_translation(
    client: LLMClient, text: str, language_code: str = "", model_name: str = ""
) -> tuple[str | None, ReviewMetrics]:
    """Generate a translated abstract for the manuscript.

    Returns (str, metrics) on success or (None, metrics) on failure.
    Unlike the review functions, translation errors are non-fatal: callers
    must check for None and skip the translation rather than treating it as
    a pipeline failure.
    """
    target_language = TRANSLATION_LANGUAGES.get(language_code, language_code)
    log_substep(f"Generating translation ({target_language})...")

    metrics = ReviewMetrics(
        input_chars=len(text), input_words=len(text.split()), input_tokens_est=estimate_tokens(text)
    )
    client.reset()
    _cfg = client.config  # Use the caller-provided client config, not a fresh from_env() read
    max_tokens = _cfg.long_max_tokens
    timeout = _cfg.review_timeout
    logger.info(f"    Timeout: {timeout:.0f}s per translation ({target_language})")
    if timeout < 60:
        logger.warning(f"    ⚠️  Low timeout ({timeout:.0f}s) - may cause failures for slow models")
        logger.info(
            "    Consider: export LLM_REVIEW_TIMEOUT=300 (5 minutes) for better reliability"
        )
    template = ManuscriptTranslationAbstract()
    prompt = template.render(text=text, target_language=target_language, max_tokens=max_tokens)
    temperature = 0.4 if _is_small_model(model_name) else 0.3
    options = GenerationOptions(temperature=temperature, max_tokens=max_tokens)

    start_time = time.time()
    try:
        response = _stream_with_heartbeat(
            client, prompt, options, f"translation ({target_language})", max_tokens, _cfg
        )
    except Exception as e:  # noqa: BLE001 — intentional: translation errors are non-fatal
        metrics.generation_time_seconds = time.time() - start_time
        logger.warning(f"Translation to {target_language} failed: {e}")
        return None, metrics

    metrics.generation_time_seconds = time.time() - start_time
    metrics.output_chars = len(response)
    metrics.output_words = len(response.split())
    metrics.output_tokens_est = estimate_tokens(response)
    metrics.preview = (
        response[:150].replace("\\n", " ") + "..." if len(response) > 150 else response
    )

    log_success(f"translation ({target_language}) generated", logger)
    return response, metrics
