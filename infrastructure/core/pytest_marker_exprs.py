"""Combined ``pytest -m`` expressions for subprocess suite runners.

``pyproject.toml`` ``addopts`` defaults apply only when pytest is started without
overriding ``-m``. Orchestrators that invoke ``python -m pytest …`` with an
explicit ``-m`` must pass the full expression, including all repository marker
aliases used for opt-in benchmark and performance suites.
"""


def build_pytest_marker_expression(
    *,
    skip_requires_ollama: bool,
    skip_slow: bool,
    skip_bench: bool,
    skip_requires_docker: bool = True,
    skip_long_running: bool = True,
    skip_private_project: bool = True,
    skip_external_fixture: bool = True,
) -> str | None:
    """Return a single ``and``-combined marker expression, or ``None`` if unrestricted.

    Args:
        skip_requires_ollama: When True, append ``not requires_ollama``.
        skip_requires_docker: When True, append ``not requires_docker``.
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


__all__ = ["build_pytest_marker_expression"]
