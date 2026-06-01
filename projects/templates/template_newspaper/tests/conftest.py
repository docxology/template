"""Shared fixtures for the newspaper test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from newspaper.config import NewspaperConfig, load_newspaper_config
from newspaper.content import Edition, load_edition

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = PROJECT_ROOT / "content"


@pytest.fixture
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture
def content_dir() -> Path:
    return CONTENT_DIR


@pytest.fixture
def edition() -> Edition:
    return load_edition(CONTENT_DIR)


@pytest.fixture
def config() -> NewspaperConfig:
    return load_newspaper_config(CONTENT_DIR)
