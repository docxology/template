"""Package entry point: ``python -m infrastructure.rendering``.

Delegates to the rendering CLI's :func:`main`.
"""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
