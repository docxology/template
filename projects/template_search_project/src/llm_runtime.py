"""Shared runtime helper for binding the project to a real Ollama LLM.

Both ``scripts/run_search_pipeline.py`` and ``scripts/run_deep_search.py``
need exactly the same logic to:

1. Try to import :mod:`infrastructure.llm`.
2. Try to construct an :class:`OllamaClientConfig` and an
   :class:`LLMClient` from the project's pinned LLM knobs.
3. Return a real ``(prompt: str) -> str`` callable on success, or
   ``None`` when the LLM stack is genuinely unreachable so call sites
   can skip the synthesis stage cleanly without writing placeholder
   text into the archive.

The function purposefully **does not** swallow programming errors — only
the well-defined failure modes that mean "no LLM available" (ImportError
on the optional ``infrastructure.llm`` module, or any error raised
during ``OllamaClientConfig.from_env()`` / ``LLMClient`` construction
which always indicates an environmental problem rather than a bug in
this project's code).
"""

from __future__ import annotations

from typing import Callable

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


def build_llm_callable(
    *,
    model: str,
    seed: int,
    temperature: float,
    context_window: int,
    long_max_tokens: int,
    max_input_length: int,
    review_timeout: float,
) -> Callable[[str], str] | None:
    """Return a real ``(prompt: str) -> str`` callable, or ``None``.

    Returning ``None`` is the documented signal that the LLM stack is
    genuinely unreachable — the caller is expected to skip its
    synthesis stage rather than emit a fake "(LLM unavailable)" string
    into the archive.

    Args:
        model: Ollama model name (e.g. ``"gemma3:4b"``).
        seed: Pinned seed for reproducibility.
        temperature: Pinned sampling temperature.
        context_window: Tokens of context the model accepts.
        long_max_tokens: Cap for ``query_long`` so multi-section reading
            notes are not truncated mid-section.
        max_input_length: Per-call input character cap.
        review_timeout: Per-call timeout in seconds.

    Returns:
        A callable wrapping :class:`infrastructure.llm.LLMClient` when
        the import + client construction both succeed; ``None`` when
        either step fails (with a warning logged so the operator knows
        the synthesis stage was skipped).
    """
    try:
        from infrastructure.llm import LLMClient, OllamaClientConfig
    except ImportError as exc:
        logger.warning(
            "infrastructure.llm not importable (%s); skipping LLM synthesis. "
            "Install ollama and run `ollama serve` to enable.",
            exc,
        )
        return None

    try:
        env_cfg = OllamaClientConfig.from_env()
        client = LLMClient(
            OllamaClientConfig(
                base_url=env_cfg.base_url,
                default_model=model,
                seed=seed,
                temperature=temperature,
                context_window=context_window,
                long_max_tokens=long_max_tokens,
                max_input_length=max_input_length,
                review_timeout=review_timeout,
            )
        )
    except Exception as exc:  # pragma: no cover - environment-dependent
        logger.warning(
            "Could not initialise LLMClient (%s); skipping LLM synthesis.",
            exc,
        )
        return None

    def _call(prompt: str) -> str:
        try:
            response = client.query_long(prompt)
        except AttributeError:  # pragma: no cover - older LLMClient versions
            response = client.query(prompt)
        return response if isinstance(response, str) else getattr(response, "text", str(response))

    return _call
