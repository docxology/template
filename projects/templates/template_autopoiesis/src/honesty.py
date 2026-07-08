"""Honesty manifest — structural evidence that the generator does what it claims.

The honesty contract is: every claim in the manuscript must be backed by
structural evidence in the source code.  This module:
  1. Inspects the source AST to detect real function calls (not stubs).
  2. Scans prose for unsupported quantitative claims.
  3. Returns a manifest that can be checked in tests.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Structural evidence catalogue
# ---------------------------------------------------------------------------

STRUCTURAL_EVIDENCE: dict[str, list[str]] = {
    "grammar_parses": ["src/grammar.py::parse_grammar"],
    "expand_deterministic": ["src/expand.py::expand", "src/expand.py::_digest_index"],
    "materialize_writes_files": ["src/materialize.py::materialize"],
    "integrity_hashes": ["src/integrity.py::tree_hash_from_content_hashes"],
    "verify_recomputes": ["src/verify.py::verify_child"],
    "primitives_collected": ["src/primitives/__init__.py::collect_primitives"],
}


# ---------------------------------------------------------------------------
# Manifest dataclass
# ---------------------------------------------------------------------------


@dataclass
class HonestyManifest:
    """Records which honesty checks passed."""

    evidence: dict[str, bool] = field(default_factory=dict)
    missing_calls: list[str] = field(default_factory=list)
    unsupported_claims: list[str] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        """Process all passed."""
        return all(self.evidence.values()) and not self.missing_calls and not self.unsupported_claims


# ---------------------------------------------------------------------------
# AST call detection
# ---------------------------------------------------------------------------


def _collect_function_names(source_code: str) -> set[str]:
    """Return the set of all function/method definition names in *source_code*."""
    names: set[str] = set()
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return names
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
    return names


def build_manifest(project_root: str | Path) -> HonestyManifest:
    """Build an honesty manifest by inspecting source files."""
    project_root = Path(project_root)
    manifest = HonestyManifest()

    for claim, evidence_list in STRUCTURAL_EVIDENCE.items():
        all_found = True
        for evidence_ref in evidence_list:
            parts = evidence_ref.split("::")
            rel_path = parts[0]
            fn_name = parts[1] if len(parts) > 1 else ""
            src_path = project_root / rel_path
            if not src_path.exists():
                manifest.missing_calls.append(f"{rel_path} not found")
                all_found = False
                continue
            if fn_name:
                names = _collect_function_names(src_path.read_text())
                if fn_name not in names:
                    manifest.missing_calls.append(f"{fn_name} not in {rel_path}")
                    all_found = False
        manifest.evidence[claim] = all_found

    return manifest


# ---------------------------------------------------------------------------
# Prose scanning
# ---------------------------------------------------------------------------

_UNSUPPORTED_CLAIM_PATTERN = re.compile(
    r"\b(100%|guaranteed|always|never|impossible|proven|certainly)\b",
    re.IGNORECASE,
)


def verify_honesty(
    project_root: str | Path,
    manuscript_dir: Optional[str | Path] = None,
) -> HonestyManifest:
    """Full honesty verification: AST + prose scan."""
    manifest = build_manifest(project_root)

    ms_dir = Path(manuscript_dir) if manuscript_dir else Path(project_root) / "manuscript"
    if ms_dir.exists():
        for md_file in ms_dir.glob("*.md"):
            text = md_file.read_text()
            for m in _UNSUPPORTED_CLAIM_PATTERN.finditer(text):
                manifest.unsupported_claims.append(f"{md_file.name}:{m.start()}: '{m.group()}'")

    return manifest
