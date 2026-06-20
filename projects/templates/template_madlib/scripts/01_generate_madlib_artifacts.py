#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parents[2]
for candidate in (PROJECT_ROOT, PROJECT_ROOT / "src", REPO_ROOT):
    text = str(candidate)
    if text not in sys.path:
        sys.path.insert(0, text)

from infrastructure.core.logging.utils import get_logger, log_success
from src.analysis import generate_artifacts

logger = get_logger(__name__)


def main() -> int:
    artifacts = generate_artifacts(PROJECT_ROOT)
    for name, path in sorted(artifacts.items()):
        logger.info("%s: %s", name, path)
    log_success("Madlib artifacts generated", logger)
    print(str(artifacts["token_inventory"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
