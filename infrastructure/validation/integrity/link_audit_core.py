"""Core link audit loop for repository markdown files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Set, cast

from infrastructure.core.logging.utils import get_logger
from infrastructure.validation.docs.accuracy import extract_headings
from infrastructure.validation.content.discovery import discover_markdown_files
from infrastructure.validation.integrity.check_links import generate_comprehensive_report
from infrastructure.validation.integrity.link_extract import (
    LinkCheckResult,
    check_file_reference,
    extract_links,
    validate_directory_structures,
    validate_file_paths_in_code,
    validate_placeholder_consistency,
    validate_python_imports,
)
from infrastructure.validation.integrity.link_policies import (
    DEFAULT_ANCHOR_POLICY,
    DEFAULT_FILE_REF_POLICY,
)

logger = get_logger(__name__)


@dataclass(frozen=True)
class LinkIssue:
    """Structured link audit finding."""

    category: str
    file: str
    line: int
    target: str
    text: str
    issue: str
    type: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "line": self.line,
            "target": self.target,
            "text": self.text,
            "issue": self.issue,
            "type": self.type,
        }


def run_link_audit(repo_root: Path) -> int:
    """Run the comprehensive link and reference audit for ``repo_root``."""
    md_files = discover_markdown_files(repo_root, scope="link_audit")

    logger.info(f"Found {len(md_files)} markdown files")
    logger.info("Running comprehensive filepath and reference audit")

    all_headings: dict[str, Set[str]] = {}
    issues: dict[str, list[Any]] = {
        "broken_anchor_links": [],
        "broken_file_refs": [],
        "code_block_paths": [],
        "directory_structures": [],
        "python_imports": [],
        "placeholder_consistency": [],
    }

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
            all_headings[str(md_file.relative_to(repo_root))] = extract_headings(content)
        except (OSError, UnicodeDecodeError) as exc:
            logger.error(f"Error reading {md_file}: {exc}")

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
            internal_links, _external_links, file_refs = extract_links(content, md_file)
            file_key = str(md_file.relative_to(repo_root))

            for link in internal_links:
                target = link["target"].lstrip("#")
                if DEFAULT_ANCHOR_POLICY.should_skip(file_key, target):
                    continue
                if file_key in all_headings and target not in all_headings[file_key]:
                    issues["broken_anchor_links"].append(
                        LinkIssue(
                            category="broken_anchor_links",
                            file=file_key,
                            line=link["line"],
                            target=link["target"],
                            text=link["text"],
                            issue="Anchor not found",
                            type="broken_anchor",
                        ).as_dict()
                    )

            for ref in file_refs:
                target = ref["target"]
                if "#" in target:
                    target = target.split("#", 1)[0]
                if not target or DEFAULT_FILE_REF_POLICY.should_skip(target):
                    continue
                exists, msg = check_file_reference(target, md_file, repo_root)
                if not exists:
                    issues["broken_file_refs"].append(
                        LinkIssue(
                            category="broken_file_refs",
                            file=str(md_file.relative_to(repo_root)),
                            line=ref["line"],
                            target=ref["target"],
                            text=ref["text"],
                            issue=msg,
                            type="broken_file_ref",
                        ).as_dict()
                    )

            issues["code_block_paths"].extend(validate_file_paths_in_code(content, md_file, repo_root))
            issues["directory_structures"].extend(validate_directory_structures(content, md_file, repo_root))
            issues["python_imports"].extend(validate_python_imports(content, md_file, repo_root))
            issues["placeholder_consistency"].extend(validate_placeholder_consistency(content, md_file, repo_root))

        except (OSError, UnicodeDecodeError) as exc:
            logger.error(f"Error processing {md_file}: {exc}")

    return generate_comprehensive_report(cast(dict[str, list[LinkCheckResult]], issues), len(md_files))
