"""Honesty manifest — structural evidence that the generator does what it claims.

The honesty contract is: every claim in the manuscript must be backed by
structural evidence in the source code.  This module:
  1. Inspects the source AST to detect real function calls (not stubs).
  2. Scans prose for unsupported quantitative claims.
  3. Returns a manifest that can be checked in tests.
"""

from __future__ import annotations

import ast
import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Structural evidence catalogue
# ---------------------------------------------------------------------------

STRUCTURAL_EVIDENCE: dict[str, list[str]] = {
    "grammar_parses": ["src/template_autopoiesis/core/grammar.py::parse_grammar"],
    "expand_deterministic": [
        "src/template_autopoiesis/core/expand.py::expand",
        "src/template_autopoiesis/core/expand.py::_digest_index",
    ],
    "materialize_writes_files": ["src/template_autopoiesis/gates/materialize.py::materialize"],
    "integrity_hashes": ["src/template_autopoiesis/gates/integrity.py::tree_hash_from_content_hashes"],
    "verify_recomputes": ["src/template_autopoiesis/gates/verify.py::verify_child"],
    "primitives_collected": ["src/template_autopoiesis/primitives/__init__.py::collect_primitives"],
}

# Required calls are inspected inside the named function body, not elsewhere
# in the file. This is structural custody; actual child execution has its own
# receipt and independently scored exported results.
_REQUIRED_CALLS = {
    "parse_grammar": {"Grammar", "GrammarSlot"},
    "expand": {"_digest_index", "Spec"},
    "_digest_index": {"sha256"},
    "materialize": {"_build_tree", "write_text", "tree_hash_from_content_hashes"},
    "tree_hash_from_content_hashes": {"sha256_text", "sorted"},
    "verify_child": {"read_text", "tree_hash_from_content_hashes"},
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
    source_sha256: dict[str, str] = field(default_factory=dict)

    @property
    def all_passed(self) -> bool:
        """Process all passed."""
        return (
            bool(self.evidence)
            and all(self.evidence.values())
            and not self.missing_calls
            and not self.unsupported_claims
        )


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
            if (
                not src_path.is_file()
                or src_path.is_symlink()
                or not src_path.resolve().is_relative_to(project_root.resolve())
                or any(
                    parent.is_symlink()
                    for parent in src_path.parents
                    if parent != project_root and parent.is_relative_to(project_root)
                )
            ):
                manifest.missing_calls.append(f"{rel_path} not found")
                all_found = False
                continue
            if fn_name:
                source = src_path.read_bytes()
                manifest.source_sha256[rel_path] = hashlib.sha256(source).hexdigest()
                try:
                    tree = ast.parse(source)
                except SyntaxError:
                    manifest.missing_calls.append(f"invalid syntax in {rel_path}")
                    all_found = False
                    continue
                functions = [
                    node
                    for node in tree.body
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == fn_name
                ]
                if len(functions) != 1:
                    manifest.missing_calls.append(f"{fn_name} must have one top-level definition in {rel_path}")
                    all_found = False
                    continue
                body = functions[0]
                calls = {
                    call.func.id if isinstance(call.func, ast.Name) else call.func.attr
                    for call in ast.walk(body)
                    if isinstance(call, ast.Call) and isinstance(call.func, (ast.Name, ast.Attribute))
                }
                missing = _REQUIRED_CALLS.get(fn_name, set()) - calls
                returns = [node for node in ast.walk(body) if isinstance(node, ast.Return)]
                if missing or not returns and fn_name == "collect_primitives":
                    manifest.missing_calls.append(f"{fn_name} lacks required structural operations: {sorted(missing)}")
                    all_found = False
                if fn_name == "collect_primitives" and not any(
                    isinstance(node.value, ast.Dict) and len(node.value.keys) >= 1 for node in returns
                ):
                    manifest.missing_calls.append("collect_primitives must return a nonempty registry")
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
