"""Module entry point for ``python -m infrastructure.methods``."""

from infrastructure.methods.cli import main


if __name__ == "__main__":  # pragma: no cover - exercised by subprocess tests
    raise SystemExit(main())
