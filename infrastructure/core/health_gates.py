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
        ("mypy", [sys.executable, "scripts/gates/mypy_ratchet.py", *public_targets]),
        ("ruff", [sys.executable, "-m", "ruff", "check", *lint_targets]),
        ("ruff-format", [sys.executable, "-m", "ruff", "format", "--check", *lint_targets]),
        (
            "bandit",
            [
                sys.executable,
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
        ("no-mocks", [sys.executable, "scripts/audit/verify_no_mocks.py"]),
        (
            "semantic-standins",
            [
                sys.executable,
                "scripts/audit/verify_no_mocks.py",
                "--inventory",
                "--max-dependency-replacements",
                "0",
            ],
        ),
        ("all-exports", [sys.executable, "-m", "infrastructure.skills", "check-all-exports"]),
        ("skills-manifest", [sys.executable, "-m", "infrastructure.skills", "check"]),
        (
            "operations-manifest",
            [sys.executable, "-m", "infrastructure.skills", "operations-check"],
        ),
        ("skill-reachability", [sys.executable, "scripts/gates/skill_reachability_check.py"]),
        ("confidentiality", [sys.executable, "scripts/audit/check_tracked_all.py"]),
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
            [sys.executable, "scripts/audit/check_tracked_generated_artifacts.py"],
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
                    " print('\\n'.join(violations));"
                    " sys.exit(1 if violations else 0)"
                ),
            ],
        ),
        ("template-drift", [sys.executable, "scripts/audit/check_template_drift.py", "--strict"]),
        ("docs-lint", [sys.executable, "scripts/audit/lint_docs.py", "--quiet"]),
        ("stage-table", [sys.executable, "scripts/docgen/stage_table.py"]),
        ("api-reference", [sys.executable, "scripts/docgen/api_reference.py", "--check"]),
        ("counts", [sys.executable, "scripts/docgen/counts.py", "--check"]),
        ("exemplar-roster", [sys.executable, "scripts/docgen/exemplar_roster.py", "--check"]),
        ("publication-records", [sys.executable, "scripts/docgen/publication_records.py", "--check"]),
        ("status-freshness", [sys.executable, "scripts/gates/status_freshness.py"]),
        (
            "methods-plan",
            [
                sys.executable,
                "scripts/gates/methods_plan_check.py",
                "--all-public",
                "--artifact-mode",
                "source",
            ],
        ),
        ("public-capabilities", [sys.executable, "scripts/gates/public_capabilities.py"]),
        ("architecture-overview", arch_overview_argv),
        ("module-line-count", [sys.executable, "scripts/gates/module_line_count_check.py"]),
        (
            "ci-module-durations",
            [sys.executable, "scripts/gates/ci_module_durations_check.py"],
        ),
    ]


__all__ = ["build_gate_specs"]
