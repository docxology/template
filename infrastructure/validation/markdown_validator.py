"""Markdown validation utilities for ensuring document integrity.

This module provides comprehensive validation of markdown files including:
- Image reference validation
- Cross-reference validation
- Mathematical equation validation
- Link and URL validation

This is part of the infrastructure layer (generic, reusable validation).
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List, Set, Tuple

# Regex patterns for validation
IMG_PATTERN = re.compile(r"!\[[^\]]*\]\(([^\)]+)\)")
EQ_LABEL_PATTERN = re.compile(r"\\label\{([^}]+)\}")
EQ_REF_PATTERN = re.compile(r"\\eqref\{([^}]+)\}")
ANCHOR_PATTERN = re.compile(r"\{#([^}]+)\}")
INTERNAL_LINK_PATTERN = re.compile(r"\(#([^\)]+)\)")
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\((https?://[^\)]+)\)")
BARE_URL_PATTERN = re.compile(r"(?<!\]\()https?://\S+")


def find_markdown_files(markdown_dir: str | Path) -> List[str]:
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
        raise FileNotFoundError(f"Markdown directory not found: {markdown_dir}")
    
    if not markdown_dir.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {markdown_dir}")
    
    return [
        str(markdown_dir / f)
        for f in sorted(os.listdir(markdown_dir))
        if f.endswith(".md")
    ]


def collect_symbols(md_paths: List[str]) -> Tuple[Set[str], Set[str]]:
    """Collect all equation labels and section anchors from markdown files.
    
    Args:
        md_paths: List of markdown file paths to process
        
    Returns:
        Tuple of (equation_labels, section_anchors) as sets
    """
    labels: Set[str] = set()
    anchors: Set[str] = set()
    for path in md_paths:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        labels.update(EQ_LABEL_PATTERN.findall(text))
        anchors.update(ANCHOR_PATTERN.findall(text))
    return labels, anchors


def validate_images(md_paths: List[str], repo_root: str | Path) -> List[str]:
    """Validate that all referenced images exist in the filesystem.
    
    Args:
        md_paths: List of markdown file paths to validate
        repo_root: Root directory of the repository
        
    Returns:
        List of validation problem descriptions
    """
    repo_root = str(repo_root)
    problems: List[str] = []
    for path in md_paths:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        for img in IMG_PATTERN.findall(text):
            # Strip optional attributes after ) are not included by regex
            img_clean = img.split()[0]
            # Normalize relative paths (most are ../output/...)
            abs_path = os.path.normpath(os.path.join(os.path.dirname(path), img_clean))
            if not os.path.isabs(abs_path):
                abs_path = os.path.join(repo_root, abs_path)
            if not os.path.exists(abs_path):
                problems.append(f"Missing image: {img_clean} referenced from {os.path.relpath(path, repo_root)}")
    return problems


def validate_refs(md_paths: List[str], labels: Set[str], anchors: Set[str], repo_root: str | Path) -> List[str]:
    """Validate cross-references, internal links, and external URLs.
    
    Args:
        md_paths: List of markdown file paths to validate
        labels: Set of valid equation labels
        anchors: Set of valid section anchors
        repo_root: Root directory of the repository
        
    Returns:
        List of validation problem descriptions
    """
    repo_root = str(repo_root)
    problems: List[str] = []
    for path in md_paths:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        for ref in EQ_REF_PATTERN.findall(text):
            if ref not in labels:
                problems.append(f"Missing equation label for \\eqref{{{ref}}} in {os.path.relpath(path, repo_root)}")
        for link in INTERNAL_LINK_PATTERN.findall(text):
            if link not in anchors and link not in labels:
                problems.append(f"Missing anchor/label for link (#{link}) in {os.path.relpath(path, repo_root)}")
        # Flag bare URLs not inside Markdown links
        for m in BARE_URL_PATTERN.finditer(text):
            problems.append(f"Bare URL found (use informative Markdown link text): '{m.group(0)}' in {os.path.relpath(path, repo_root)}")
        # Flag non-informative link text (label equals URL)
        for m in LINK_PATTERN.finditer(text):
            label = m.group(1).strip()
            url = m.group(2).strip()
            if label == url or label.lower().startswith("http") or "/" in label:
                problems.append(
                    f"Non-informative link text for {url} in {os.path.relpath(path, repo_root)}; replace with descriptive text"
                )
    return problems


def validate_math(md_paths: List[str], repo_root: str | Path) -> List[str]:
    """Validate mathematical equation formatting and labeling.
    
    Args:
        md_paths: List of markdown file paths to validate
        repo_root: Root directory of the repository
        
    Returns:
        List of validation problem descriptions
    """
    repo_root = str(repo_root)
    problems: List[str] = []
    eq_block = re.compile(r"\\begin\{equation\}([\s\S]*?)\\end\{equation\}", re.MULTILINE)
    label_pattern = re.compile(r"\\label\{([^}]+)\}")
    seen_labels: Set[str] = set()
    for path in md_paths:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        # Disallow $$ and \[ \] display math in sources
        if "$$" in text:
            problems.append(f"Use equation environment instead of $$ in {os.path.relpath(path, repo_root)}")
        if "\\[" in text or "\\]" in text:
            problems.append(f"Use equation environment instead of \\[ \\] in {os.path.relpath(path, repo_root)}")
        # Ensure each equation block carries a label and detect duplicates
        for m in eq_block.finditer(text):
            block = m.group(1)
            labels_in_block = label_pattern.findall(block)
            if not labels_in_block:
                problems.append(f"Equation missing \\label{{...}} in {os.path.relpath(path, repo_root)}")
            else:
                for lab in labels_in_block:
                    if lab in seen_labels:
                        problems.append(f"Duplicate equation label '{{{lab}}}' found in {os.path.relpath(path, repo_root)}")
                    seen_labels.add(lab)
    return problems


def validate_markdown(markdown_dir: str | Path, repo_root: str | Path, strict: bool = False) -> Tuple[List[str], int]:
    """Validate all markdown files in a directory.
    
    This is the main validation function that runs all checks.
    
    Args:
        markdown_dir: Directory containing markdown files to validate
        repo_root: Root directory of the repository
        strict: If True, fail on any issues; if False, warn only
        
    Returns:
        Tuple of (problems list, exit_code)
        - problems: List of validation problem descriptions
        - exit_code: 0 for success, 1 for issues found (in strict mode or always)
        
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
    
    problems: List[str] = []
    problems += validate_images(md_paths, repo_root)
    problems += validate_refs(md_paths, labels, anchors, repo_root)
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
    
    raise FileNotFoundError(f"Manuscript directory not found at expected location: {manuscript_dir}")

