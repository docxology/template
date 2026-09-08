"""Backwards-compat shim: the module moved to ``infrastructure.publishing.metadata.metadata_export_cli``.

Historical import paths keep resolving; new code imports the new path
directly."""

from infrastructure.publishing.metadata.metadata_export_cli import (
    main,
)

__all__ = [
    "main",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
