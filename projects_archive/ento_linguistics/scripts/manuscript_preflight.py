#!/usr/bin/env python3
"""Preflight checks for manuscript assets.

Validates that referenced figures exist, glossary markers are present,
and references boilerplate is intact before PDF rendering.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Tuple

# Ensure infrastructure/ and src/ are on path BEFORE imports
repo_root = Path(__file__).resolve().parents[2]
src_path = Path(__file__).resolve().parent / "src"
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.utils.validation import (validate_markdown, validate_pdf_rendering,
                                  verify_output_integrity)

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

# Try to import build module (may not exist)
try:
    from infrastructure.build.quality_checker import analyze_document_quality

    _BUILD_MODULE_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    _BUILD_MODULE_AVAILABLE = False

    def analyze_document_quality(path):
        return {
            "status": "skipped",
            "reason": "infrastructure.build module not available",
        }


FIGURE_PATTERN = re.compile(r"\\includegraphics[^{}]*\{([^}]+)\}")
GLOSSARY_BEGIN = "<!-- BEGIN: AUTO-API-GLOSSARY -->"
GLOSSARY_END = "<!-- END: AUTO-API-GLOSSARY -->"


@dataclass
class CheckResult:
    missing_figures: List[str]
    missing_glossary_markers: bool
    missing_references_block: bool

    def is_clean(self) -> bool:
        return (
            not self.missing_figures
            and not self.missing_glossary_markers
            and not self.missing_references_block
        )


def _find_markdown_files(manuscript_dir: Path) -> List[Path]:
    return sorted(f for f in manuscript_dir.glob("*.md") if f.is_file())


def _collect_figure_paths(markdown_files: List[Path]) -> List[Tuple[Path, str]]:
    found: List[Tuple[Path, str]] = []
    for md_file in markdown_files:
        for line in md_file.read_text(encoding="utf-8").splitlines():
            match = FIGURE_PATTERN.search(line)
            if match:
                found.append((md_file, match.group(1)))
    return found


def run_checks(manuscript_dir: Path) -> CheckResult:
    markdown_files = _find_markdown_files(manuscript_dir)

    figure_refs = _collect_figure_paths(markdown_files)
    missing_figs: List[str] = []
    for md_file, ref in figure_refs:
        ref_path = (md_file.parent / ref).resolve()
        if not ref_path.exists():
            missing_figs.append(f"{md_file.name}: {ref}")

    glossary_path = manuscript_dir / "98_symbols_glossary.md"
    glossary_text = (
        glossary_path.read_text(encoding="utf-8") if glossary_path.exists() else ""
    )
    missing_glossary = not (
        GLOSSARY_BEGIN in glossary_text and GLOSSARY_END in glossary_text
    )

    references_path = manuscript_dir / "99_references.md"
    references_text = (
        references_path.read_text(encoding="utf-8") if references_path.exists() else ""
    )
    missing_references_block = "\\bibliography{references}" not in references_text

    return CheckResult(
        missing_figures=missing_figs,
        missing_glossary_markers=missing_glossary,
        missing_references_block=missing_references_block,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run manuscript preflight checks.")
    parser.add_argument(
        "--manuscript-dir",
        type=Path,
        default=Path(__file__).parent.parent / "manuscript",
        help="Path to manuscript directory (default: project/manuscript)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status on any issue.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON output for CI consumption.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    result = run_checks(args.manuscript_dir)
    validation_messages: List[str] = []

    # Run additional validation passes
    try:
        problems, _ = validate_markdown(str(args.manuscript_dir), ".")
        if problems:
            validation_messages.append(f"Markdown validation issues: {len(problems)}")
    except Exception as exc:
        validation_messages.append(f"Markdown validation skipped: {exc}")

    try:
        # If combined PDF exists, validate rendering quality
        combined_pdf = Path("output/pdf/project_combined.pdf")
        if combined_pdf.exists():
            pdf_report = validate_pdf_rendering(combined_pdf)
            if pdf_report.get("issues", {}).get("total_issues", 0) > 0:
                validation_messages.append("PDF validation found issues")
    except Exception as exc:
        validation_messages.append(f"PDF validation skipped: {exc}")

    try:
        verify_output_integrity(Path("output"))
    except Exception as exc:
        validation_messages.append(f"Output integrity check warning: {exc}")

    try:
        quality = analyze_document_quality(args.manuscript_dir)
        if quality:
            validation_messages.append("Quality metrics computed")
    except Exception as exc:
        validation_messages.append(f"Quality check skipped: {exc}")

    if args.json:
        payload = asdict(result)
        payload["validation_messages"] = validation_messages
        print(
            json.dumps(payload, indent=2)
        )  # Keep JSON output as-is for machine consumption
    else:
        logger.info(f"Manuscript dir: {args.manuscript_dir}")
        if result.missing_figures:
            logger.error("❌ Missing figures:")
            for entry in result.missing_figures:
                logger.error(f"  - {entry}")
        else:
            logger.info("✅ All referenced figures exist")

        if result.missing_glossary_markers:
            logger.error("❌ Glossary markers missing in 98_symbols_glossary.md")
        else:
            logger.info("✅ Glossary markers present")

        if result.missing_references_block:
            logger.error("❌ References block missing in 99_references.md")
        else:
            logger.info("✅ References block present")
        for msg in validation_messages:
            logger.info(f"ℹ️  {msg}")

    if args.strict and not result.is_clean():
        sys.exit(1)


if __name__ == "__main__":
    main()
