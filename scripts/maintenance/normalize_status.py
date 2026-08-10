#!/usr/bin/env python3
"""Migrate the human-readable status ledger to the typed evidence schema."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RECEIPT = "docs/_generated/status_evidence.json"


def _identity(subsystem: str) -> tuple[str, str, str]:
    """Return a stable ID, executable command, and verification mode."""
    lower = subsystem.casefold()
    if "pipeline orchestration" in lower:
        return (
            "STATUS-PIPELINE-1",
            "`./run.sh --pipeline --project template_code_project --core-only --skip-infra`",
            "manual",
        )
    if "test runner" in lower:
        return (
            "STATUS-TEST-RUNNER-1",
            "`uv run python scripts/pipeline/stage_01_test.py --infra-only --profile release`",
            "automated",
        )
    if "pdf rendering" in lower:
        return (
            "STATUS-PDF-RENDER-1",
            "`uv run python scripts/pipeline/stage_03_render.py --project templates/template_code_project`",
            "manual",
        )
    if "output validation" in lower:
        return (
            "STATUS-OUTPUT-VALIDATION-1",
            "`uv run python scripts/pipeline/stage_04_validate.py --project templates/template_code_project`",
            "automated",
        )
    if "llm stages" in lower:
        return "STATUS-LLM-1", "`uv run pytest tests/infra_tests/llm -m requires_ollama -q`", "optional-tool"
    if "steganography" in lower:
        return (
            "STATUS-STEGANOGRAPHY-1",
            "`STEGANOGRAPHY_DETERMINISTIC=1 ./secure_run.sh --steganography-only --project template_code_project`",
            "manual",
        )
    if "publishing" in lower:
        return (
            "STATUS-PUBLISHING-1",
            "`uv run python scripts/runner/archive_publication.py --project templates/template_code_project --providers software_heritage`",
            "external",
        )
    if "confidentiality" in lower:
        return "STATUS-CONFIDENTIALITY-1", "`uv run python scripts/audit/check_tracked_all.py`", "automated"
    if "multi-project discovery" in lower:
        return "STATUS-DISCOVERY-1", "`uv run python scripts/docgen/active_projects.py --check`", "automated"
    if "secure-run" in lower:
        return (
            "STATUS-SECURE-RUN-1",
            "`STEGANOGRAPHY_DETERMINISTIC=1 ./secure_run.sh --steganography-only --project template_code_project`",
            "manual",
        )
    if "ci matrix" in lower:
        return (
            "STATUS-CI-MATRIX-1",
            "`uv run python scripts/audit/check_public_template_contract.py --strict`",
            "external",
        )
    if "documentation index" in lower:
        return "STATUS-DOCUMENTATION-1", "`uv run python scripts/docgen/counts.py --check`", "automated"
    if "root release" in lower:
        return "STATUS-ROOT-RELEASE-1", "`uv run python scripts/docgen/publication_records.py --check`", "manual"
    if "skills manifest" in lower:
        return "STATUS-SKILLS-1", "`uv run python -m infrastructure.skills check`", "automated"
    if "regression tests" in lower:
        return "STATUS-REGRESSION-1", "`uv run pytest tests/regression/ -q --no-cov --timeout=120`", "external"
    if "autoresearch exemplar" in lower:
        return (
            "STATUS-AUTORESEARCH-1",
            "`uv run pytest projects/templates/template_autoresearch_project/tests -q --no-cov --timeout=120`",
            "automated",
        )
    raise ValueError(f"no stable status mapping for {subsystem!r}")


def normalize_status(path: Path) -> str:
    """Return a normalized ledger with stable IDs and receipt metadata."""
    lines = path.read_text(encoding="utf-8").splitlines()
    header_index = next(i for i, line in enumerate(lines) if line.startswith("| Subsystem |"))
    end_index = next(i for i in range(header_index + 2, len(lines)) if lines[i].startswith("## Health legend"))
    rows: list[str] = []
    for line in lines[header_index + 2 : end_index]:
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 5 or cells[0].casefold() == "subsystem":
            continue
        subsystem, verified_on, verified_by, scope, health = cells
        identifier, command, mode = _identity(subsystem)
        rows.append(
            "| "
            + " | ".join((identifier, subsystem, verified_on, verified_by, scope, command, RECEIPT, mode, health))
            + " |"
        )
    replacement = [
        "| ID | Subsystem | Last verified | Verified by | Verification scope | Command | Receipt | Mode | Health |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        *rows,
    ]
    return "\n".join([*lines[:header_index], *replacement, *lines[end_index:]]) + "\n"


def main() -> int:
    """Normalize ``STATUS.md`` in place."""
    path = REPO_ROOT / "STATUS.md"
    normalized = normalize_status(path)
    path.write_text(normalized, encoding="utf-8")
    print(f"normalized {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
