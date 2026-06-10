"""Documentation contract checks for reproducibility-facing references."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from gates.documentation_contract import (
    check_documentation_contract,
    check_historical_test_evidence,
    check_hydrated_output_links,
    check_markdown_links,
    check_project_local_commands,
    check_readme_agents_pairs,
)


def test_rendering_reproducibility_reference_is_signposted(project_root: Path) -> None:
    issues = check_documentation_contract(project_root)
    assert issues == []


def test_documentation_contract_cli(project_root: Path) -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_documentation_contract.py", "--check"],
        cwd=project_root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "documentation_contract: ok" in result.stdout


def test_documentation_contract_rejects_missing_markdown_link(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("[missing](docs/missing.md)\n", encoding="utf-8")

    issues = check_markdown_links(tmp_path)

    assert [issue.code for issue in issues] == ["markdown-link-missing"]


def test_documentation_contract_rejects_missing_reference_style_link(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("[docs]: docs/missing.md\n", encoding="utf-8")

    issues = check_markdown_links(tmp_path)

    assert [issue.code for issue in issues] == ["markdown-link-missing"]

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Docs\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("[docs]: <docs/index.md>\n", encoding="utf-8")
    assert check_markdown_links(tmp_path) == []


def test_documentation_contract_rejects_undefined_reference_style_usage(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("[docs][missing]\n", encoding="utf-8")

    issues = check_markdown_links(tmp_path)

    assert [(issue.code, issue.target) for issue in issues] == [
        ("markdown-reference-missing", "[docs][missing]")
    ]

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Docs\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("[docs][]\n\n[docs]: docs/index.md\n", encoding="utf-8")
    assert check_markdown_links(tmp_path) == []


def test_documentation_contract_rejects_missing_markdown_anchor(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# Existing Heading\n\n[bad](#missing-anchor)\n", encoding="utf-8")

    issues = check_markdown_links(tmp_path)

    assert [issue.code for issue in issues] == ["markdown-anchor-missing"]

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("## Target Section {#custom-target}\n", encoding="utf-8")
    readme.write_text(
        "# Existing Heading\n\n[good](#existing-heading)\n[custom](docs/index.md#custom-target)\n",
        encoding="utf-8",
    )
    assert check_markdown_links(tmp_path) == []


def test_documentation_contract_rejects_hydrated_output_path_shape(tmp_path: Path) -> None:
    manuscript = tmp_path / "output" / "manuscript"
    figures = tmp_path / "output" / "figures"
    manuscript.mkdir(parents=True)
    figures.mkdir(parents=True)
    (figures / "ok.png").write_bytes(b"png")
    path = manuscript / "00_abstract.md"
    path.write_text("![bad](../output/figures/ok.png)\n", encoding="utf-8")

    issues = check_hydrated_output_links(tmp_path)

    assert [issue.code for issue in issues] == ["hydrated-output-link"]

    path.write_text("![good](../figures/ok.png)\n", encoding="utf-8")
    assert check_hydrated_output_links(tmp_path) == []
    assert check_markdown_links(tmp_path) == []


def test_documentation_contract_requires_readme_agents_pairs(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "README.md").write_text("# Docs\n", encoding="utf-8")

    issues = check_readme_agents_pairs(tmp_path)

    assert [issue.code for issue in issues] == ["readme-agents-pair"]

    (docs / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
    assert check_readme_agents_pairs(tmp_path) == []


def test_documentation_contract_rejects_stale_root_shaped_project_commands(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "Run `uv run --directory projects/templates/template_active_inference pytest tests -q`.\n",
        encoding="utf-8",
    )

    issues = check_project_local_commands(tmp_path)

    assert [issue.code for issue in issues] == ["root-directory-uv-run"]


def test_documentation_contract_requires_labeled_historical_counts(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "Old baseline: 153-test / 92.03%.\n\n"
        "Previous baseline: 364 tests / 90.70%.\n\n"
        "In this audit, `uv run pytest tests/ --cov=src --cov-fail-under=90` passed 1 tests with\n"
        "90.00% coverage.\n",
        encoding="utf-8",
    )
    issues = check_historical_test_evidence(tmp_path)
    assert [issue.code for issue in issues] == ["historical-evidence-unlabeled", "historical-evidence-unlabeled"]

    (tmp_path / "README.md").write_text(
        "The 153-test / 92.03% baseline is historical and stale; do not reuse it.\n\n"
        "The 364 tests / 90.70% baseline is historical and stale; do not reuse it.\n\n"
        "In this audit, `uv run pytest tests/ --cov=src --cov-fail-under=90` passed 1 tests with\n"
        "90.00% coverage.\n",
        encoding="utf-8",
    )
    assert check_historical_test_evidence(tmp_path) == []
