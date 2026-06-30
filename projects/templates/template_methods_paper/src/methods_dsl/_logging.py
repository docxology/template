"""The one sanctioned infrastructure import in this project's domain ``src/``.

Every other module in ``methods_dsl`` is standalone (no ``infrastructure``
import), so the package could be forked out of the monorepo unchanged. This
adapter is the deliberate exception: it reaches into the repository's unified
logging system (``infrastructure.core.logging.utils.get_logger``) so the DSL's
gate and compiler output uses the same structured log format as every other
project in the template. The exception is declared explicitly in
``manuscript/layer_contract.yaml`` (``allow_infrastructure_imports``), the
mechanism ``infrastructure/project/drift/checks_boundary.py`` reads to
distinguish a sanctioned integration point from a layer-boundary leak.
"""

from __future__ import annotations

import logging

try:
    from infrastructure.core.logging.utils import get_logger as _infra_get_logger
except ImportError:  # pragma: no cover - standalone fork without infrastructure/ on the path

    def get_logger(name: str) -> logging.Logger:
        return logging.getLogger(name)

else:

    def get_logger(name: str) -> logging.Logger:
        return _infra_get_logger(name)
