"""Combined ``pytest -m`` expressions for subprocess suite runners.

``pyproject.toml`` ``addopts`` defaults apply only when pytest is started without
overriding ``-m``. Orchestrators that invoke ``python -m pytest …`` with an
explicit ``-m`` must pass the full expression (including ``not bench`` when
benchmarks are opt-in).
"""

from __future__ import annotations


def build_pytest_marker_expression(
    *,
    skip_requires_ollama: bool,
    skip_slow: bool,
    skip_bench: bool,
) -> str | None:
    """Return a single ``and``-combined marker expression, or ``None`` if unrestricted.

    Args:
        skip_requires_ollama: When True, append ``not requires_ollama``.
        skip_slow: When True, append ``not slow``.
        skip_bench: When True, append ``not bench``.
    """
    parts: list[str] = []
    if skip_requires_ollama:
        parts.append("not requires_ollama")
    if skip_slow:
        parts.append("not slow")
    if skip_bench:
        parts.append("not bench")
    if not parts:
        return None
    return " and ".join(parts)


__all__ = ["build_pytest_marker_expression"]
