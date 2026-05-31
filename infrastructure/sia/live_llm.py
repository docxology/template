"""Optional Ollama-backed meta/feedback for live SIA runs."""

from __future__ import annotations


from infrastructure.core.logging.utils import get_logger
from infrastructure.llm.core.client import LLMClient
from infrastructure.llm.core.config import OllamaClientConfig
from infrastructure.core.exceptions import LLMConnectionError

logger = get_logger(__name__)


def generate_improvement_markdown(
    *,
    generation: int,
    metric_name: str,
    metric_value: float,
    llm_model: str,
) -> str | None:
    """Ask an LLM for improvement text; return None when unavailable."""
    if not llm_model:
        return None
    prompt = (
        f"Generation {generation - 1} achieved {metric_name}={metric_value:.4f} "
        "on mini_classify. Write a short markdown improvement note (3-5 lines) "
        "suggesting threshold tuning on feature_0."
    )
    config = OllamaClientConfig(auto_inject_system_prompt=False)
    if llm_model:
        config.default_model = llm_model
    client = LLMClient(config)
    try:
        response = client.query(prompt)
    except LLMConnectionError as exc:
        logger.warning("LLM feedback unavailable: %s", exc)
        return None
    text = response.strip()
    if not text:
        return None
    if not text.startswith("#"):
        text = f"# Improvement gen {generation}\n\n{text}"
    return text


__all__ = ["generate_improvement_markdown"]
