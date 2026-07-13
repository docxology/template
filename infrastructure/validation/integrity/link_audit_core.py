"""Core link audit loop for repository markdown files."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Set, cast

from infrastructure.core.logging.utils import get_logger
from infrastructure.validation.content.discovery import _LINK_AUDIT_EXCLUDE_PARTS
from infrastructure.validation.docs.accuracy import extract_headings
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


def _gitignored_top_level_dirs(root: Path) -> set[str]:
    """Return basenames of top-level directories under *root* ignored by git.

    The expensive trees (``.git``, ``.venv``, ``node_modules``, ``output`` …)
    are already in the static exclude set; this single batched ``git
    check-ignore`` catches any *additional* top-level directories the user has
    gitignored so the walk skips them too. Best-effort: returns an empty set
    when *root* is not a git repository or ``git`` is unavailable, falling back
    to the static exclude-part pruning. Invoked once per audit run — never per
    directory level — so it never dominates the walk.
    """
    try:
        top_dirs = [p for p in root.iterdir() if p.is_dir()]
    except OSError:
        return set()
    if not top_dirs:
        return set()
    rels = [p.name for p in top_dirs]
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "check-ignore", "--stdin"],
            input="\n".join(rels),
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, ValueError):
        return set()
    # Exit code 0 => some matched; 1 => none matched; 128 => not a git repo.
    if proc.returncode not in (0, 1):
        return set()
    return {Path(line.strip()).name for line in proc.stdout.splitlines() if line.strip()}


def discover_link_audit_files(repo_root: Path) -> list[Path]:
    """Discover link-audit markdown files via a pruning ``os.walk``.

    Equivalent to ``discover_markdown_files(repo_root, scope="link_audit")`` but
    prunes excluded (and gitignored) directories *before* descending, so the
    walk never enters ``.git``/``.venv``/``node_modules``/``output``/
    ``__pycache__`` and the rest of the link-audit exclusion set. The previous
    ``rglob`` path still materialised every path under those huge trees before
    discarding them; pruning in place avoids that entirely. Returns the same
    shape: a sorted list of resolved absolute ``*.md`` paths.
    """
    root = Path(repo_root).resolve()
    skip = set(_LINK_AUDIT_EXCLUDE_PARTS) | _gitignored_top_level_dirs(root)
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune excluded/gitignored directories in place BEFORE descending.
        dirnames[:] = [d for d in dirnames if d not in skip]
        base = Path(dirpath)
        for name in filenames:
            if name.lower().endswith(".md"):
                out.append(base / name)
    return sorted(out)


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
        """Process as dict."""
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
    md_files = discover_link_audit_files(repo_root)

    logger.info(f"Found {len(md_files)} markdown files")
    logger.info("Running comprehensive filepath and reference audit")

    # ``discover_link_audit_files`` returns resolved absolute paths; resolve the
    # repo root once so ``relative_to`` keys are stable without re-resolving.
    repo_root_resolved = repo_root.resolve()

    all_headings: dict[str, Set[str]] = {}
    issues: dict[str, list[Any]] = {
        "broken_anchor_links": [],
        "broken_file_refs": [],
        "code_block_paths": [],
        "directory_structures": [],
        "python_imports": [],
        "placeholder_consistency": [],
    }

    # Read each file exactly once; the previous implementation walked the full
    # file set twice (headings pass + links pass), doubling the I/O.
    contents: dict[Path, str] = {}
    file_keys: dict[Path, str] = {}
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            logger.error(f"Error reading {md_file}: {exc}")
            continue
        contents[md_file] = content
        file_key = str(md_file.relative_to(repo_root_resolved))
        file_keys[md_file] = file_key
        all_headings[file_key] = extract_headings(content)

    for md_file in md_files:
        cached_content = contents.get(md_file)
        if cached_content is None:
            continue
        try:
            internal_links, _external_links, file_refs = extract_links(cached_content, md_file)
            file_key = file_keys[md_file]

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
                exists, msg = check_file_reference(target, md_file, repo_root_resolved)
                if not exists:
                    issues["broken_file_refs"].append(
                        LinkIssue(
                            category="broken_file_refs",
                            file=file_key,
                            line=ref["line"],
                            target=ref["target"],
                            text=ref["text"],
                            issue=msg,
                            type="broken_file_ref",
                        ).as_dict()
                    )

            issues["code_block_paths"].extend(validate_file_paths_in_code(content, md_file, repo_root_resolved))
            issues["directory_structures"].extend(validate_directory_structures(content, md_file, repo_root_resolved))
            issues["python_imports"].extend(validate_python_imports(content, md_file, repo_root_resolved))
            issues["placeholder_consistency"].extend(
                validate_placeholder_consistency(content, md_file, repo_root_resolved)
            )

        except (OSError, UnicodeDecodeError) as exc:
            logger.error(f"Error processing {md_file}: {exc}")

    return generate_comprehensive_report(cast(dict[str, list[LinkCheckResult]], issues), len(md_files))
