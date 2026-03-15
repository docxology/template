"""Review generation utilities for manuscript review operations.

Error contract design:
- Text extraction helpers (extract_manuscript_text) return (None, metrics) on failure
  so the pipeline can report a graceful skip rather than aborting on missing files.
- LLM response validation (llm/validation/core.py) raises ValidationError immediately —
  an invalid response from the LLM is a programmer error or model failure that cannot
  be meaningfully recovered from in-line.
- These are intentionally different contracts for different failure domains.
"""

from __future__ import annotations

import os
import re
import subprocess
import time
from typing import Any, Callable, Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from infrastructure.llm.templates.base import ResearchTemplate
from pathlib import Path

from infrastructure.core.logging_utils import (
    get_logger,
    log_substep,
    log_success,
)
from infrastructure.core.logging_progress import (
    log_with_spinner,
    StreamingProgress,
    Spinner,
)

from infrastructure.llm.core.client import LLMClient
from infrastructure.llm.core.config import GenerationOptions, OllamaClientConfig

from infrastructure.llm.utils.ollama import (
    is_ollama_running,
    ensure_ollama_ready,
    select_best_model,
    get_available_models,
    check_model_loaded,
    preload_model,
)
from infrastructure.llm.utils.heartbeat import StreamHeartbeatMonitor
from infrastructure.llm.templates.manuscript import (
    ManuscriptExecutiveSummary,
    ManuscriptImprovementSuggestions,
    ManuscriptTranslationAbstract,
    REVIEW_MIN_WORDS,
    TRANSLATION_LANGUAGES,
)
from infrastructure.llm.validation.repetition import (
    detect_repetition,
    deduplicate_sections,
)
from infrastructure.llm.validation.format import (
    is_off_topic,
    check_format_compliance,
)

from infrastructure.llm.review.metrics import ReviewMetrics, ManuscriptInputMetrics, estimate_tokens
# Cross-subsystem import: llm/review depends on validation/pdf_validator for text extraction.
# This is an intentional seam — PDF text extraction lives in validation because it is also
# used by the output validator. If this becomes a problem, move extract_text_from_pdf to
# infrastructure/core/pdf_utils.py so both subsystems can import without circular deps.
from infrastructure.validation.pdf_validator import extract_text_from_pdf
from infrastructure.core.exceptions import PDFValidationError

logger = get_logger(__name__)

from infrastructure.llm.core._prompt_availability import PROMPT_SYSTEM_AVAILABLE

if PROMPT_SYSTEM_AVAILABLE:
    from infrastructure.llm.prompts.composer import PromptComposer

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

_SMALL_MODEL_SUFFIXES = frozenset(["3b", "4b", "7b", "8b"])


def _is_small_model(model_name: str) -> bool:
    """Return True if model_name indicates a small parameter-count model."""
    lower = model_name.lower()
    return any(s in lower for s in _SMALL_MODEL_SUFFIXES)


ReviewType = Literal[
    "executive_summary",
    "quality_review",
    "methodology_review",
    "improvement_suggestions",
    "translation",
]


def validate_review_quality(
    response: str,
    review_type: ReviewType,
    min_words: int | None = None,
    model_name: str = "",
) -> tuple[bool, list[str], dict[str, Any]]:
    """Validate the quality and formatting of an LLM review response."""
    issues = []
    details: dict[str, Any] = {
        "sections_found": [],
        "scores_found": [],
        "format_compliance": {},
        "repetition": {},
    }
    response_lower = response.lower()

    if is_off_topic(response):
        issues.append("Response appears off-topic or confused")
        return False, issues, details

    has_repetition, duplicates, unique_ratio = detect_repetition(response)
    details["repetition"] = {
        "has_repetition": has_repetition,
        "unique_ratio": unique_ratio,
        "duplicates_found": len(duplicates),
    }

    if unique_ratio < 0.5:
        issues.append(f"Excessive repetition detected: {unique_ratio:.0%} unique content")
        return False, issues, details
    elif has_repetition:
        details["repetition_warning"] = (
            f"Some repeated content detected ({len(duplicates)} duplicates)"
        )
        logger.debug(f"Repetition warning: {unique_ratio:.0%} unique content")

    is_format_compliant, format_issues, format_details = check_format_compliance(response)
    details["format_compliance"] = format_details

    if not is_format_compliant:
        details["format_warnings"] = format_issues

    default_min = REVIEW_MIN_WORDS.get(review_type, 200)
    if _is_small_model(model_name):
        default_min = int(default_min * 0.8)
    min_word_count = min_words or default_min

    word_count = len(response.split())
    details["word_count"] = word_count
    details["min_required"] = min_word_count

    tolerance = max(1, int(min_word_count * 0.05))
    effective_min = min_word_count - tolerance

    if word_count < effective_min:
        issues.append(
            f"Too short: {word_count} words (minimum: {min_word_count}, effective: {effective_min} with tolerance)"  # noqa: E501
        )

    validator = _REVIEW_TYPE_VALIDATORS.get(review_type)
    if validator:
        validator(response_lower, details, issues)

    is_valid = len(issues) == 0
    return is_valid, issues, details


def _validate_executive_summary_section(
    response_lower: str, details: dict[str, Any], issues: list[str]
) -> None:
    header_variations = [
        (["overview", "summary", "introduction", "abstract"], "overview"),
        (
            ["key contributions", "contributions", "main findings", "key findings", "highlights"],
            "contributions",
        ),
        (["methodology", "methods", "approach", "method", "techniques"], "methodology"),
        (["results", "findings", "principal results", "outcomes", "key results"], "results"),
        (["significance", "impact", "implications", "importance", "takeaway"], "significance"),
    ]
    found_sections = [
        name
        for variations, name in header_variations
        if any(v in response_lower for v in variations)
    ]
    details["sections_found"] = found_sections
    details["sections_required"] = 1
    if not found_sections:
        issues.append("Missing expected structure (found: none of 5 expected sections)")


def _validate_quality_review_section(
    response_lower: str, details: dict[str, Any], issues: list[str]
) -> None:
    score_patterns = [
        (r"\*\*score:\s*(\d)/5\*\*", "**Score: X/5**"),
        (r"score:\s*(\d)/5", "Score: X/5"),
        (r"\*\*(\d)/5\*\*", "**X/5**"),
        (r"score\s*:\s*(\d)", "Score: X"),
        (r"rating\s*:\s*(\d)", "Rating: X"),
        (r"\[(\d)/5\]", "[X/5]"),
        (r"(\d)\s*out\s*of\s*5", "X out of 5"),
        (r"(\d)/5", "X/5"),
    ]
    scores_found = [
        (m, name) for pattern, name in score_patterns for m in re.findall(pattern, response_lower)
    ]
    details["scores_found"] = scores_found
    has_assessment = any(
        kw in response_lower
        for kw in ("clarity", "structure", "readability", "technical accuracy", "overall quality")
    )
    details["has_assessment"] = has_assessment
    if not scores_found and not has_assessment:
        issues.append("Missing scoring or quality assessment")


def _validate_methodology_review_section(
    response_lower: str, details: dict[str, Any], issues: list[str]
) -> None:
    methodology_sections = [
        (["strengths", "strong points", "advantages", "positives", "pros"], "strengths"),
        (
            ["weaknesses", "limitations", "concerns", "issues", "weak points", "cons", "gaps"],
            "weaknesses",
        ),
        (["suggestions", "recommendations", "improvements", "future work"], "recommendations"),
    ]
    found_sections = [
        name
        for variations, name in methodology_sections
        if any(v in response_lower for v in variations)
    ]
    details["sections_found"] = found_sections
    has_methodology_content = any(
        kw in response_lower
        for kw in ("research design", "methodology", "approach", "methods", "experimental")
    )
    details["has_methodology_content"] = has_methodology_content
    if not found_sections and not has_methodology_content:
        issues.append(f"Missing expected sections (found: {found_sections or 'none'})")


def _validate_improvement_suggestions_section(
    response_lower: str, details: dict[str, Any], issues: list[str]
) -> None:
    priority_variations = [
        (["high priority", "critical", "urgent", "must fix", "immediate", "major"], "high"),
        (["medium priority", "moderate", "should address", "important", "significant"], "medium"),
        (["low priority", "minor", "nice to have", "optional", "consider", "cosmetic"], "low"),
    ]
    found_priorities = [
        name
        for variations, name in priority_variations
        if any(v in response_lower for v in variations)
    ]
    details["priorities_found"] = found_priorities
    has_recommendations = any(
        kw in response_lower for kw in ("recommendation", "suggest", "improve", "fix", "address")
    )
    details["has_recommendations"] = has_recommendations
    if not found_priorities and not has_recommendations:
        issues.append("Missing priority sections or recommendations")


def _validate_translation_section(
    response_lower: str, details: dict[str, Any], issues: list[str]
) -> None:
    has_english = (
        "english abstract" in response_lower
        or "## english" in response_lower
        or ("abstract" in response_lower and "english" in response_lower)
    )
    details["has_english_section"] = has_english
    has_translation = any(
        kw in response_lower
        for kw in ("translation", "chinese", "hindi", "russian", "中文", "हिंदी", "русский")
    )
    details["has_translation_section"] = has_translation
    if not has_english:
        issues.append("Missing English abstract section")
    if not has_translation:
        issues.append("Missing translation section")


# Module-level dispatch table — built once after all validators are defined.
_ValidatorFn = Callable[[str, dict[str, Any], list[str]], None]
_REVIEW_TYPE_VALIDATORS: dict[str, _ValidatorFn] = {
    "executive_summary": _validate_executive_summary_section,
    "quality_review": _validate_quality_review_section,
    "methodology_review": _validate_methodology_review_section,
    "improvement_suggestions": _validate_improvement_suggestions_section,
    "translation": _validate_translation_section,
}


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

    try:
        result = subprocess.run(["which", "ollama"], capture_output=True, timeout=2.0)
        if result.returncode != 0:
            logger.error("❌ Ollama command not found. Install Ollama: https://ollama.ai")
            return False, None
    except (subprocess.SubprocessError, FileNotFoundError):  # noqa: BLE001 — failure propagated as (False, None) return value
        logger.error("❌ Unable to check if Ollama is installed")
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

    available_models = get_available_models()
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
    model_preloaded, loaded_model = check_model_loaded(model_name)

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
            preload_success, preload_error = preload_model(model_name)

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

    original_length = len(response)
    has_rep, _, unique_ratio = detect_repetition(response, similarity_threshold=0.8)
    if has_rep and unique_ratio < 0.3:
        response = deduplicate_sections(
            response,
            max_repetitions=2,
            mode="conservative",
            similarity_threshold=0.9,
            min_content_preservation=0.8,
        )
        reduction_ratio = len(response) / original_length
        if reduction_ratio < 0.7:
            response = best_response

    metrics.generation_time_seconds = time.time() - start_time
    metrics.output_chars = len(response)
    metrics.output_words = len(response.split())
    metrics.output_tokens_est = estimate_tokens(response)
    metrics.preview = (
        response[:150].replace("\\n", " ") + "..." if len(response) > 150 else response
    )

    log_success(f"{review_name} generated", logger)
    return response, metrics


def generate_llm_executive_summary(
    client: LLMClient, text: str, model_name: str = ""
) -> tuple[str | None, ReviewMetrics]:
    """Named public API entry point for executive summary reviews.

    Binds review_type='executive_summary' and ManuscriptExecutiveSummary template.
    Callers use the named function rather than the generic generate_review_with_metrics
    to avoid having to know the template class and review_type string.
    """
    return generate_review_with_metrics(
        client=client,
        text=text,
        review_type="executive_summary",
        review_name="executive summary",
        template_class=ManuscriptExecutiveSummary,
        model_name=model_name,
        temperature=0.3,
        max_tokens=None,
    )


def generate_improvement_suggestions(
    client: LLMClient, text: str, model_name: str = ""
) -> tuple[str | None, ReviewMetrics]:
    """Named public API entry point for improvement suggestions (ManuscriptImprovementSuggestions template).

    Uses temperature=0.4 (vs 0.3 for other reviews) because generative ideation
    benefits from higher diversity — the task is proposing novel directions, not
    accurate analysis.
    """
    return generate_review_with_metrics(
        client=client,
        text=text,
        review_type="improvement_suggestions",
        review_name="improvement suggestions",
        template_class=ManuscriptImprovementSuggestions,
        model_name=model_name,
        temperature=0.4,
        max_tokens=None,
    )


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
