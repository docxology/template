from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_detailed_security_policy_has_no_placeholder_intake() -> None:
    policy = (REPO_ROOT / "docs" / "development" / "security.md").read_text(encoding="utf-8")
    forbidden = [
        "[INSERT SECURITY EMAIL]",
        "[Name]",
        "[Email]",
        "[Names]",
        "[Emails]",
        "[Your Name]",
        "[Vulnerability Description]",
        "3.2.x",
    ]

    for marker in forbidden:
        assert marker not in policy


def test_github_security_policy_and_detail_share_private_reporting_route() -> None:
    github_policy = (REPO_ROOT / ".github" / "SECURITY.md").read_text(encoding="utf-8")
    detailed_policy = (REPO_ROOT / "docs" / "development" / "security.md").read_text(encoding="utf-8")
    advisory_url = "https://github.com/docxology/template/security/advisories/new"

    assert advisory_url in github_policy
    assert advisory_url in detailed_policy
    assert "public issue" in github_policy
    assert "public GitHub issues" in detailed_policy
