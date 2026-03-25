"""Markdown validation utilities for ensuring document integrity.

This module provides comprehensive validation of markdown files including:
- Image reference validation
- Cross-reference validation
- Mathematical equation validation
- Link and URL validation

This is part of the infrastructure layer (generic, reusable validation).
"""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.core.exceptions import FileNotFoundError, NotADirectoryError

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

# Regex patterns for validation
IMG_PATTERN = re.compile(r"!\[[^\]]*\]\(([^\)]+)\)")
EQ_LABEL_PATTERN = re.compile(r"\\label\{([^}]+)\}")
EQ_REF_PATTERN = re.compile(r"\\eqref\{([^}]+)\}")
ANCHOR_PATTERN = re.compile(r"\{#([^}]+)\}")
INTERNAL_LINK_PATTERN = re.compile(r"\(#([^\)]+)\)")
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\((https?://[^\)]+)\)")
BARE_URL_PATTERN = re.compile(r"(?<!\]\()https?://\S+")


def find_markdown_files(markdown_dir: str | Path) -> list[str]:
    """Find all markdown files in the specified directory.

    Args:
        markdown_dir: Directory to search for markdown files

    Returns:
        List of full paths to markdown files, sorted by filename

    Raises:
        FileNotFoundError: If markdown_dir doesn't exist
    """
    markdown_dir = Path(markdown_dir)
    if not markdown_dir.exists():
        raise FileNotFoundError(
            f"Markdown directory not found: {markdown_dir}",
            context={"directory": str(markdown_dir)},
        )

    if not markdown_dir.is_dir():
        raise NotADirectoryError(
            f"Path is not a directory: {markdown_dir}",
            context={"path": str(markdown_dir)},
        )

    return [str(p) for p in sorted(markdown_dir.glob("*.md"))]


def collect_symbols(md_paths: list[str]) -> tuple[set[str], set[str]]:
    """Collect all equation labels and section anchors from markdown files.

    Args:
        md_paths: List of markdown file paths to process

    Returns:
        Tuple of (equation_labels, section_anchors) as sets
    """
    labels: set[str] = set()
    anchors: set[str] = set()
    for path in md_paths:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        labels.update(EQ_LABEL_PATTERN.findall(text))
        anchors.update(ANCHOR_PATTERN.findall(text))
    return labels, anchors


def validate_images(
    md_paths: list[str],
    repo_root: str | Path,
    extra_search_dirs: list[str | Path] | None = None,
) -> list[str]:
    """Validate that all referenced images exist in the filesystem.

    When a relative image path fails to resolve from the markdown file's
    directory, this function also checks ``extra_search_dirs`` and
    auto-discovered project-level figure directories (``output/figures/``
    and ``figures/`` relative to the manuscript's project root).

    Args:
        md_paths: List of markdown file paths to validate
        repo_root: Root directory of the repository
        extra_search_dirs: Additional directories to search for images

    Returns:
        List of validation problem descriptions
    """
    repo_root_path = Path(repo_root)
    problems: list[str] = []

    # Build search directories from the markdown directory's project context.
    # Manuscript dirs follow the pattern: projects/<name>/manuscript/
    # So the project root is two levels up from the manuscript dir.
    search_dirs: list[Path] = []
    if extra_search_dirs:
        search_dirs.extend(Path(d) for d in extra_search_dirs)

    if md_paths:
        md_dir = Path(md_paths[0]).parent
        # Auto-discover sibling output/figures/ and figures/ dirs
        project_root = md_dir.parent  # parent of manuscript/
        for candidate in [
            project_root / "output" / "figures",
            project_root / "figures",
        ]:
            if candidate.is_dir() and candidate not in search_dirs:
                search_dirs.append(candidate)

    for path in md_paths:
        path_obj = Path(path)
        text = path_obj.read_text(encoding="utf-8")
        for img in IMG_PATTERN.findall(text):
            # Strip optional attributes after ) are not included by regex
            img_clean = img.split()[0]
            # Normalize relative paths (most are ../output/...  or figures/)
            abs_path = (path_obj.parent / img_clean).resolve()
            if abs_path.exists():
                continue

            # Try each search directory as a fallback
            img_basename = Path(img_clean).name
            found = False
            for search_dir in search_dirs:
                if (search_dir / img_basename).exists():
                    found = True
                    break
            if not found:
                try:
                    display_path = Path(path).relative_to(repo_root_path)
                except ValueError:
                    display_path = path  # type: ignore[assignment]
                problems.append(
                    f"Missing image: {img_clean} referenced from {display_path}"
                )
    return problems


def validate_refs(
    md_paths: list[str], repo_root: str | Path, labels: set[str], anchors: set[str]
) -> list[str]:
    """Validate cross-references, internal links, and external URLs.

    Args:
        md_paths: List of markdown file paths to validate
        repo_root: Root directory of the repository
        labels: Set of valid equation labels
        anchors: Set of valid section anchors

    Returns:
        List of validation problem descriptions
    """
    repo_root_path = Path(repo_root)
    problems: list[str] = []
    for path in md_paths:
        text = Path(path).read_text(encoding="utf-8")
        try:
            rel: str | Path = Path(path).relative_to(repo_root_path)
        except ValueError:
            rel = path
        for ref in EQ_REF_PATTERN.findall(text):
            if ref not in labels:
                problems.append(
                    f"Missing equation label for \\eqref{{{ref}}} in {rel}"  # noqa: E501
                )
        for link in INTERNAL_LINK_PATTERN.findall(text):
            if link not in anchors and link not in labels:
                problems.append(
                    f"Missing anchor/label for link (#{link}) in {rel}"
                )
        # Flag bare URLs not inside Markdown links.
        # Strip fenced code blocks first to avoid false positives on Turtle/SPARQL/RDF URIs
        # that are syntactically required inside code blocks (e.g. @prefix np: <http://...>)
        text_no_code = re.sub(r"```[^`]*```", "", text, flags=re.DOTALL)
        text_no_code = re.sub(r"`[^`]+`", "", text_no_code)  # also strip inline code
        for m in BARE_URL_PATTERN.finditer(text_no_code):
            problems.append(
                f"Bare URL found (use informative Markdown link text): '{m.group(0)}' in {rel}"  # noqa: E501
            )
        # Flag non-informative link text (label equals URL)
        for m in LINK_PATTERN.finditer(text):
            label = m.group(1).strip()
            url = m.group(2).strip()
            if label == url or label.lower().startswith("http") or "/" in label:
                problems.append(
                    f"Non-informative link text for {url} in {rel}; replace with descriptive text"  # noqa: E501
                )
    return problems


def validate_math(md_paths: list[str], repo_root: str | Path) -> list[str]:
    """Validate mathematical equation formatting and labeling.

    Args:
        md_paths: List of markdown file paths to validate
        repo_root: Root directory of the repository

    Returns:
        List of validation problem descriptions
    """
    repo_root_path = Path(repo_root)
    problems: list[str] = []
    eq_block = re.compile(r"\\begin\{equation\}([\s\S]*?)\\end\{equation\}", re.MULTILINE)
    label_pattern = re.compile(r"\\label\{([^}]+)\}")
    seen_labels: set[str] = set()
    for path in md_paths:
        text = Path(path).read_text(encoding="utf-8")
        try:
            rel: str | Path = Path(path).relative_to(repo_root_path)
        except ValueError:
            rel = path
        # Disallow $$ and \[ \] display math in sources
        if "$$" in text:
            problems.append(f"Use equation environment instead of $$ in {rel}")
        if "\\[" in text or "\\]" in text:
            problems.append(f"Use equation environment instead of \\[ \\] in {rel}")
        # Ensure each equation block carries a label and detect duplicates
        for m in eq_block.finditer(text):
            block = m.group(1)
            labels_in_block = label_pattern.findall(block)
            if not labels_in_block:
                problems.append(f"Equation missing \\label{{...}} in {rel}")
            else:
                for lab in labels_in_block:
                    if lab in seen_labels:
                        problems.append(
                            f"Duplicate equation label '{{{lab}}}' found in {rel}"
                        )
                    seen_labels.add(lab)
    return problems


def validate_markdown(
    markdown_dir: str | Path, repo_root: str | Path, strict: bool = False
) -> tuple[list[str], int]:
    """Validate all markdown files in a directory.

    This is the main validation function that runs all checks.

    Args:
        markdown_dir: Directory containing markdown files to validate
        repo_root: Root directory of the repository
        strict: If True, fail on any issues; if False, warn only

    Returns:
        Tuple of (problems list, exit_code)
        - problems: List of validation problem descriptions
        - exit_code: 0 for success or when strict=False; 1 only when strict=True and issues found

    Raises:
        FileNotFoundError: If markdown_dir doesn't exist
    """
    markdown_dir = Path(markdown_dir)
    repo_root = Path(repo_root)

    if not markdown_dir.exists():
        raise FileNotFoundError(f"Markdown directory not found: {markdown_dir}")

    md_paths = find_markdown_files(markdown_dir)
    if not md_paths:
        return ([], 0)

    labels, anchors = collect_symbols(md_paths)

    problems: list[str] = []
    problems += validate_images(md_paths, repo_root)
    problems += validate_refs(md_paths, repo_root, labels, anchors)
    problems += validate_math(md_paths, repo_root)

    if problems:
        exit_code = 1 if strict else 0
        return (problems, exit_code)
    else:
        return ([], 0)


def find_manuscript_directory(repo_root: str | Path, project_name: str = "project") -> Path:
    """Find the manuscript directory at the standard location.

    Args:
        repo_root: Root directory of the repository
        project_name: Name of the project (default: "project")

    Returns:
        Path to the manuscript directory at projects/{project_name}/manuscript/

    Raises:
        FileNotFoundError: If manuscript directory cannot be found at projects/{project_name}/manuscript/
    """
    repo_root = Path(repo_root)

    manuscript_dir = repo_root / "projects" / project_name / "manuscript"

    if manuscript_dir.exists() and manuscript_dir.is_dir():
        return manuscript_dir

    raise FileNotFoundError(
        f"Manuscript directory not found at expected location: {manuscript_dir}"
    )
