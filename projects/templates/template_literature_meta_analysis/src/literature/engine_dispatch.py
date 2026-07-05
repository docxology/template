"""Declarative literature search engine enablement."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EngineSpec:
    name: str
    skip_flag: str
    config_key: str

    def enabled(self, args: argparse.Namespace, engines: dict[str, Any], *, fast_api: bool, injected: bool) -> bool:
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
)


def engine_enabled(
    spec: EngineSpec,
    args: argparse.Namespace,
    engines: dict[str, Any],
    *,
    fast_api: bool,
    url_injected: bool,
) -> bool:
    """Return whether *spec* should run for this invocation."""
    if spec.name in {"arxiv", "semantic_scholar", "openalex"}:
        return not getattr(args, spec.skip_flag, False)
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
