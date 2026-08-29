"""Declarative static-health gate argv contracts.

``build_gate_specs`` is the single list of ``(name, argv)`` pairs. The CLI in
``health.py`` runs those subprocesses; this module only declares them.
"""

from __future__ import annotations

import sys
from pathlib import Path

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES, public_ci_lint_paths, public_ci_source_paths


def _public_source_targets(repo_root: Path) -> list[str]:
    """Return public CI source paths for type checks."""
    return [path.as_posix() for path in public_ci_source_paths(repo_root)]


def _public_lint_targets(repo_root: Path) -> list[str]:
    """Return the full public lint surface without private/generated trees."""
    return [path.as_posix() for path in public_ci_lint_paths(repo_root)]


def build_gate_specs(repo_root: Path) -> list[tuple[str, list[str]]]:
    """Return the canonical ``(name, argv)`` list for every gate.

    The list is parameterised on ``repo_root`` so callers can run static health
    checks against any checkout (the live tree, a temp clone, or CI workspace).
    """
    arch_overview_argv = [
        sys.executable,
        "-c",
        (
            "import sys; from pathlib import Path;"
            " from infrastructure.documentation.architecture_overview import architecture_overview_is_current;"
            f" sys.exit(0 if architecture_overview_is_current(Path({str(repo_root)!r})) else 1)"
        ),
    ]

    public_targets = _public_source_targets(repo_root)
    lint_targets = _public_lint_targets(repo_root)
    public_project_targets = [f"projects/{name}/" for name in PUBLIC_PROJECT_NAMES]

    return [
        ("mypy", ["uv", "run", "python", "scripts/gates/mypy_ratchet.py", *public_targets]),
        ("ruff", ["uv", "run", "ruff", "check", *lint_targets]),
        ("ruff-format", ["uv", "run", "ruff", "format", "--check", *lint_targets]),
        (
            "bandit",
            [
                "uv",
                "run",
                "python",
                "-m",
                "bandit",
                "-r",
                "-ll",
                "-c",
                "bandit.yaml",
                "infrastructure/",
                "scripts/",
                *public_project_targets,
            ],
        ),
        ("no-mocks", ["uv", "run", "python", "scripts/audit/verify_no_mocks.py"]),
        (
            "semantic-standins",
            [
                "uv",
                "run",
                "python",
                "scripts/audit/verify_no_mocks.py",
                "--inventory",
                "--max-dependency-replacements",
                "0",
            ],
        ),
        ("all-exports", ["uv", "run", "python", "-m", "infrastructure.skills", "check-all-exports"]),
        ("skills-manifest", ["uv", "run", "python", "-m", "infrastructure.skills", "check"]),
        (
            "operations-manifest",
            ["uv", "run", "python", "-m", "infrastructure.skills", "operations-check"],
        ),
        ("skill-reachability", ["uv", "run", "python", "scripts/gates/skill_reachability_check.py"]),
        ("confidentiality", ["uv", "run", "python", "scripts/audit/check_tracked_all.py"]),
        (
            "codeowners",
            [
                sys.executable,
                "-c",
                (
                    "import sys; from pathlib import Path;"
                    " from infrastructure.project.codeowners import codeowners_is_current;"
                    f" sys.exit(0 if codeowners_is_current(Path({str(repo_root)!r})) else 1)"
                ),
            ],
        ),
        (
            "generated-artifacts",
            ["uv", "run", "python", "scripts/audit/check_tracked_generated_artifacts.py"],
        ),
        (
            "xml-parser-policy",
            [
                sys.executable,
                "-c",
                (
                    "import sys; from pathlib import Path;"
                    " from infrastructure.validation.xml_parser_policy import validate_xml_parser_policy;"
                    " violations = validate_xml_parser_policy("
                    f"Path({str(repo_root)!r}) / 'infrastructure', Path({str(repo_root)!r}));"
                    " sys.exit(1 if violations else 0)"
                ),
            ],
        ),
        ("template-drift", ["uv", "run", "python", "scripts/audit/check_template_drift.py", "--strict"]),
        ("docs-lint", ["uv", "run", "python", "scripts/audit/lint_docs.py", "--quiet"]),
        ("stage-table", ["uv", "run", "python", "scripts/docgen/stage_table.py"]),
        ("api-reference", ["uv", "run", "python", "scripts/docgen/api_reference.py", "--check"]),
        ("counts", ["uv", "run", "python", "scripts/docgen/counts.py", "--check"]),
        ("exemplar-roster", ["uv", "run", "python", "scripts/docgen/exemplar_roster.py", "--check"]),
        ("publication-records", ["uv", "run", "python", "scripts/docgen/publication_records.py", "--check"]),
        ("status-freshness", ["uv", "run", "python", "scripts/gates/status_freshness.py"]),
        (
            "methods-plan",
            [
                "uv",
                "run",
                "python",
                "scripts/gates/methods_plan_check.py",
                "--all-public",
                "--artifact-mode",
                "source",
            ],
        ),
        ("public-capabilities", ["uv", "run", "python", "scripts/gates/public_capabilities.py"]),
        ("architecture-overview", arch_overview_argv),
        ("module-line-count", ["uv", "run", "python", "scripts/gates/module_line_count_check.py"]),
    ]


__all__ = ["build_gate_specs"]
