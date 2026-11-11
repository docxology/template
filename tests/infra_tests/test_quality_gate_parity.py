"""Enforce the configured public-archive size-policy boundary."""

from __future__ import annotations

import re
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_large_file_hook_allows_only_named_public_arxiv_archives() -> None:
    config = yaml.safe_load((REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    hook = next(hook for repo in config["repos"] for hook in repo["hooks"] if hook["id"] == "check-added-large-files")
    excluded = re.compile(str(hook["exclude"]), re.VERBOSE)

    assert excluded.search("projects/templates/template_active_inference/output/arxiv_submission_20260814.tar.gz")
    assert not excluded.search("projects/templates/template_active_inference/output/arbitrary.tar.gz")
    assert not excluded.search("projects/working/private/output/arxiv_submission_20260814.tar.gz")
