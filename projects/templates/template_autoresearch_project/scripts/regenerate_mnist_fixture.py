#!/usr/bin/env python3
"""Regenerate the checked-in offline MNIST fixture.

This is an explicit maintenance utility. It is not called by the default
AutoResearch pipeline, tests, rendering, or validation.
"""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.mnist_fixture import regenerate_mnist_fixture  # noqa: E402


def main() -> None:
    """Regenerate `data/mnist_small.npz` and provenance."""
    fixture_path, provenance_path = regenerate_mnist_fixture(PROJECT_ROOT)
    print(fixture_path)
    print(provenance_path)


if __name__ == "__main__":
    main()
