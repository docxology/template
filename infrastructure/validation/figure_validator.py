"""Figure validation module - Validate figure registry against manuscript references.

This module provides utilities for validating that figure references in
manuscript files match the figure registry. Part of the infrastructure 
layer (Layer 1) - reusable across all projects.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Tuple, List

from infrastructure.core.logging_utils import get_logger, log_success, log_substep

logger = get_logger(__name__)


def validate_figure_registry(
    registry_path: Path,
    manuscript_dir: Path
) -> Tuple[bool, List[str]]:
    """Validate figure registry against manuscript references.
    
    Checks that all figure references in manuscript markdown files are
    registered in the figure registry. Skips documentation files (AGENTS.md,
    README.md) when scanning for references.
    
    Args:
        registry_path: Path to figure registry JSON file
        manuscript_dir: Path to manuscript directory containing markdown files
        
    Returns:
        Tuple of (success, list of issues found):
        - success: True if all references are registered, False otherwise
        - issues: List of issue descriptions (empty if success is True)
    """
    log_substep("Validating figure registry...", logger)
    
    issues: List[str] = []
    
    # Load registry
    registered_figures = set()
    if registry_path.exists():
        try:
            with open(registry_path) as f:
                registry = json.load(f)
                registered_figures = set(registry.keys())
                log_success(f"Figure registry loaded: {len(registered_figures)} figure(s)", logger)
        except Exception as e:
            issues.append(f"Failed to load figure registry: {e}")
            return False, issues
    else:
        logger.warning("Figure registry not found")
        return True, []  # Not an error if registry doesn't exist
    
    # Find figure references in markdown (only in numbered section files, not AGENTS.md/README.md)
    referenced_figures = set()
    figure_ref_pattern = re.compile(r'\\(?:ref|label)\{(fig:[^}]+)\}')
    
    if manuscript_dir.exists():
        for md_file in manuscript_dir.glob("*.md"):
            # Skip documentation files (AGENTS.md, README.md)
            if md_file.name in ["AGENTS.md", "README.md"]:
                continue
            
            try:
                content = md_file.read_text()
                refs = figure_ref_pattern.findall(content)
                referenced_figures.update(refs)
            except Exception as e:
                logger.warning(f"Could not read {md_file.name}: {e}")
    
    # Find unregistered references
    unregistered = referenced_figures - registered_figures
    if unregistered:
        for ref in sorted(unregistered):
            issues.append(f"Unregistered figure reference: {ref}")
    
    # Summary
    if issues:
        logger.warning(f"  Found {len(issues)} figure issue(s)")
        for issue in issues:
            logger.warning(f"    • {issue}")
    else:
        log_success(f"All {len(referenced_figures)} figure references verified", logger)
    
    return len(issues) == 0, issues













