#!/usr/bin/env python3
"""Regenerate the checked-in offline MNIST fixture.

This is an explicit maintenance utility. It is not called by the default
AutoResearch pipeline, tests, rendering, or validation.
"""

from __future__ import annotations

from pathlib import Path

from _bootstrap import ensure_project_paths

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ensure_project_paths(PROJECT_ROOT)

from src.ml.mnist_fixture import regenerate_mnist_fixture  # noqa: E402


def main() -> None:
    """Regenerate `data/mnist_small.npz` and provenance."""
    fixture_path, provenance_path = regenerate_mnist_fixture(PROJECT_ROOT)
    print(fixture_path)
    print(provenance_path)


if __name__ == "__main__":
    main()
