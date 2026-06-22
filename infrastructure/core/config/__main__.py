"""Package entry point so ``python -m infrastructure.core.config`` works.

Delegates to :func:`infrastructure.core.config.cli.main`, propagating its
integer exit code via ``SystemExit``.
"""

from __future__ import annotations

from infrastructure.core.config.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
