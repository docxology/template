"""Combined ``pytest -m`` expressions for subprocess suite runners.

``pyproject.toml`` ``addopts`` defaults apply only when pytest is started without
overriding ``-m``. Orchestrators that invoke ``python -m pytest …`` with an
explicit ``-m`` must pass the full expression, including all repository marker
aliases used for opt-in benchmark and performance suites.
"""


def build_pytest_marker_expression(
    *,
    skip_requires_ollama: bool = True,
    skip_slow: bool = True,
    skip_bench: bool = True,
    skip_requires_docker: bool = True,
    skip_network: bool = True,
    skip_long_running: bool = True,
    skip_private_project: bool = True,
    skip_external_fixture: bool = True,
) -> str | None:
    """Return a single ``and``-combined marker expression, or ``None`` if unrestricted.

    The keyword defaults are the repository's default pytest selection, so they
    are the single authority for ``pyproject.toml`` ``addopts``.

    Args:
        skip_requires_ollama: When True, append ``not requires_ollama``.
        skip_requires_docker: When True, append ``not requires_docker``.
        skip_network: When True, append ``not network``.
        skip_slow: When True, append ``not slow``.
        skip_bench: When True, exclude ``bench``, ``benchmark``, and
            ``performance`` marker aliases.
        skip_long_running: When True, append ``not long_running``.
        skip_private_project: When True, append ``not private_project``.
        skip_external_fixture: When True, append ``not external_fixture``.
    """
    parts: list[str] = []
    if skip_requires_ollama:
        parts.append("not requires_ollama")
    if skip_requires_docker:
        parts.append("not requires_docker")
    if skip_network:
        parts.append("not network")
    if skip_slow:
        parts.append("not slow")
    if skip_bench:
        parts.extend(("not bench", "not benchmark", "not performance"))
    if skip_long_running:
        parts.append("not long_running")
    if skip_private_project:
        parts.append("not private_project")
    if skip_external_fixture:
        parts.append("not external_fixture")
    if not parts:
        return None
    return " and ".join(parts)


def repository_marker_expression() -> str:
    """Return the marker expression ``pyproject.toml`` ``addopts`` must carry."""
    expression = build_pytest_marker_expression()
    if expression is None:  # pragma: no cover - the defaults always exclude opt-in markers
        raise ValueError("repository marker defaults must exclude opt-in markers")
    return expression


__all__ = ["build_pytest_marker_expression", "repository_marker_expression"]
