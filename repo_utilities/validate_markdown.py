#!/usr/bin/env python3
"""Markdown validation utilities for ensuring document integrity.

This module provides comprehensive validation of markdown files including:
- Image reference validation
- Cross-reference validation
- Mathematical equation validation
- Link and URL validation
"""
from __future__ import annotations

import os
import re
import sys
from typing import Dict, List, Set, Tuple


def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def find_markdown_files(markdown_dir: str) -> List[str]:
    """Find all markdown files in the specified directory.
    
    Args:
        markdown_dir: Directory to search for markdown files
        
    Returns:
        List of full paths to markdown files, sorted by filename
    """
    return [
        os.path.join(markdown_dir, f)
        for f in sorted(os.listdir(markdown_dir))
        if f.endswith(".md")
    ]


IMG_PATTERN = re.compile(r"!\[[^\]]*\]\(([^\)]+)\)")
EQ_LABEL_PATTERN = re.compile(r"\\label\{([^}]+)\}")
EQ_REF_PATTERN = re.compile(r"\\eqref\{([^}]+)\}")
ANCHOR_PATTERN = re.compile(r"\{#([^}]+)\}")
INTERNAL_LINK_PATTERN = re.compile(r"\(#([^\)]+)\)")
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\((https?://[^\)]+)\)")
BARE_URL_PATTERN = re.compile(r"(?<!\]\()https?://\S+")


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


def validate_images(md_paths: List[str], repo_root: str) -> List[str]:
    """Validate that all referenced images exist in the filesystem.
    
    Args:
        md_paths: List of markdown file paths to validate
        repo_root: Root directory of the repository
        
    Returns:
        List of validation problem descriptions
    """
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


def validate_refs(md_paths: List[str], labels: Set[str], anchors: Set[str], repo_root: str) -> List[str]:
    """Validate cross-references, internal links, and external URLs.
    
    Args:
        md_paths: List of markdown file paths to validate
        labels: Set of valid equation labels
        anchors: Set of valid section anchors
        repo_root: Root directory of the repository
        
    Returns:
        List of validation problem descriptions
    """
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


def validate_math(md_paths: List[str], repo_root: str) -> List[str]:
    """Validate mathematical equation formatting and labeling.
    
    Args:
        md_paths: List of markdown file paths to validate
        repo_root: Root directory of the repository
        
    Returns:
        List of validation problem descriptions
    """
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


def main() -> int:
    """Main function to run markdown validation.

    Returns:
        0 on success, 1 on failure or validation issues
    """
    repo_root = _repo_root()

    # Try multiple possible locations for manuscript files
    possible_manuscript_dirs = [
        os.path.join(repo_root, "manuscript"),  # Standard location
        os.path.join(os.getcwd(), "manuscript"),  # Current working directory (for tests)
        "manuscript"  # Relative to current directory
    ]

    manuscript_dir = None
    for potential_dir in possible_manuscript_dirs:
        if os.path.isdir(potential_dir):
            manuscript_dir = potential_dir
            break

    if manuscript_dir is None:
        print(f"Manuscript directory not found. Tried: {possible_manuscript_dirs}")
        return 1

    md_paths = find_markdown_files(manuscript_dir)
    labels, anchors = collect_symbols(md_paths)

    problems: List[str] = []
    problems += validate_images(md_paths, repo_root)
    problems += validate_refs(md_paths, labels, anchors, repo_root)
    problems += validate_math(md_paths, repo_root)

    strict = "--strict" in sys.argv
    if problems:
        header = "Markdown validation issues (non-strict)" if not strict else "Validation issues found"
        print(header + ":")
        for p in problems:
            print(" -", p)
        return 1 if strict else 0
    else:
        print("Markdown validation passed: all images and references resolved.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
