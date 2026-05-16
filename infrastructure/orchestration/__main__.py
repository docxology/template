"""Module entry point for ``python -m infrastructure.orchestration``."""

import sys

from infrastructure.orchestration.cli import main

if __name__ == "__main__":
    sys.exit(main())
