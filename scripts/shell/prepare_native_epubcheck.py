#!/usr/bin/env python3
"""Delegate pinned EPUBCheck preparation to the SDK implementation."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from infrastructure.reporting.native_epub_preparation import (  # noqa: E402
    MAX_EXPANDED as MAX_EXPANDED,
    PREFIX as PREFIX,
    SHA256 as SHA256,
    SIZE as SIZE,
    URL as URL,
    _HTTPSOnlyRedirect as _HTTPSOnlyRedirect,
    _download_response as _download_response,
    extract_bundle as extract_bundle,
    main as main,
    prepare as prepare,
)


if __name__ == "__main__":
    main()
