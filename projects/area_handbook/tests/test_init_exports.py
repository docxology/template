"""Public package exports."""

from __future__ import annotations

import src as area_pkg


def test_all_exports_importable() -> None:
    for name in area_pkg.__all__:
        assert hasattr(area_pkg, name)
