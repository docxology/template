"""Declarative literature search engine enablement.

Only ``dispatch_ordered`` is currently wired into ``search_runner.py``'s
production dispatch path. ``EngineSpec``, ``ENGINE_SPECS``, and
``engine_enabled`` are a correct, fully-tested, but not-yet-adopted
alternative to the per-engine boolean gates ``search_runner.py`` still
implements inline for each of the nine engines. Do not assume
``engine_enabled`` governs current runtime behavior — verify against
``search_runner.py`` directly.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EngineSpec:
    """Data container for EngineSpec."""

    name: str
    skip_flag: str
    config_key: str

    def enabled(self, args: argparse.Namespace, engines: dict[str, Any], *, fast_api: bool, injected: bool) -> bool:
        """Process enabled."""
        if getattr(args, self.skip_flag, False):
            return False
        if not engines.get(self.config_key, True):
            return False
        if fast_api and not injected:
            return False
        return True


ENGINE_SPECS: tuple[EngineSpec, ...] = (
    EngineSpec("arxiv", "skip_arxiv", "arxiv"),
    EngineSpec("semantic_scholar", "skip_s2", "semantic_scholar"),
    EngineSpec("openalex", "skip_openalex", "openalex"),
    EngineSpec("crossref", "skip_crossref", "crossref"),
    EngineSpec("pubmed", "skip_pubmed", "pubmed"),
    EngineSpec("sovietrxiv", "skip_sovietrxiv", "sovietrxiv"),
    EngineSpec("chinarxiv", "skip_chinarxiv", "chinarxiv"),
    EngineSpec("europepmc", "skip_europepmc", "europepmc"),
    EngineSpec("biorxiv", "skip_biorxiv", "biorxiv"),
)


def engine_enabled(
    spec: EngineSpec,
    args: argparse.Namespace,
    engines: dict[str, Any],
    *,
    fast_api: bool,
    url_injected: bool,
) -> bool:
    """Return whether *spec* should run for this invocation.

    arXiv, Semantic Scholar, and OpenAlex always construct their search
    function regardless of URL injection (their own clients handle the
    hermetic-test case internally), so they skip the fast_api/injected
    check that the other six engines apply. All nine still honor the
    per-engine skip flag and the `engines` config-toggle map.
    """
    if spec.name in {"arxiv", "semantic_scholar", "openalex"}:
        if getattr(args, spec.skip_flag, False):
            return False
        return engines.get(spec.config_key, True)
    return spec.enabled(args, engines, fast_api=fast_api, injected=url_injected)


def dispatch_ordered(
    route_order: list[str],
    runners: dict[str, Callable[[], None]],
) -> None:
    """Invoke runners in router order."""
    for key in route_order:
        runner = runners.get(key)
        if runner is not None:
            runner()
