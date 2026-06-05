"""Tests for public documentation RedTeam audit helpers."""

from __future__ import annotations

from pathlib import Path

from infrastructure.validation.docs.public_audit import (
    build_public_documentation_audit,
    collect_public_markdown,
    collect_symbol_documentation,
    find_gate_claims_without_negative_controls,
    find_volatile_fact_claims,
    format_audit_markdown,
)


def _write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_public_markdown_inventory_uses_shared_exclusions(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "# Root\n")
    _write(tmp_path / "docs/README.md", "# Docs\n")
    _write(tmp_path / "projects/templates/template_code_project/README.md", "# Project\n")
    _write(
        tmp_path / "projects/templates/template_code_project/.venv/lib/site-packages/pkg/README.md",
        "# Ignored\n",
    )

    records = collect_public_markdown(tmp_path)
    paths = {record.path for record in records}

    assert "README.md" in paths
    assert "docs/README.md" in paths
    assert "projects/templates/template_code_project/README.md" in paths
    assert not any(".venv" in path for path in paths)


def test_volatile_fact_audit_flags_roster_without_generated_link(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs/guide.md",
        "Current active projects: template_alpha, template_beta, template_gamma.\n",
    )

    findings = find_volatile_fact_claims(tmp_path)

    assert [finding.category for finding in findings] == ["volatile-fact"]
    assert findings[0].line == 1


def test_volatile_fact_audit_accepts_generated_source_link(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs/guide.md",
        (
            "Current active projects: template_alpha, template_beta, template_gamma; "
            "see docs/_generated/active_projects.md.\n"
        ),
    )

    assert find_volatile_fact_claims(tmp_path) == []


def test_gate_claim_audit_flags_claim_without_negative_control(tmp_path: Path) -> None:
    _write(tmp_path / "docs/rules.md", "The schema validator enforces every record.\n")

    findings = find_gate_claims_without_negative_controls(tmp_path)

    assert [finding.category for finding in findings] == ["gate-negative-control"]
    assert findings[0].severity == "advisory"


def test_gate_claim_audit_accepts_nearby_negative_control(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs/rules.md",
        (
            "The schema validator enforces every record.\n"
            "Negative control: a known-wrong fixture is expected to fail.\n"
        ),
    )

    assert find_gate_claims_without_negative_controls(tmp_path) == []


def test_symbol_documentation_audit_scans_every_def_and_class(tmp_path: Path) -> None:
    _write(tmp_path / "infrastructure/pkg/__init__.py", "")
    _write(
        tmp_path / "infrastructure/pkg/module.py",
        (
            "class PublicThing:\n"
            "    def method(self):\n"
            "        return 1\n"
            "\n"
            "def public_function():\n"
            "    return 2\n"
        ),
    )

    records = collect_symbol_documentation(tmp_path)
    names = {record.qualname for record in records}

    assert names == {"PublicThing", "PublicThing.method", "public_function"}
    assert all(not record.has_docstring for record in records)


def test_public_documentation_audit_markdown_is_source_backed(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "# Root\n")
    _write(tmp_path / "docs/guide.md", "The gate validates all docs.\n")

    audit = build_public_documentation_audit(tmp_path)
    report = format_audit_markdown(audit)

    assert "# Public Documentation RedTeam Audit" in report
    assert "docs/guide.md:1" in report
    assert "Markdown files:" in report
