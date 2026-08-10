"""Notebook-to-source binding receipt for the EDA exemplar.

The receipt is intentionally explicit: a notebook cell edit or a source edit
invalidates the checked-in receipt until the author re-runs the local refresh
command. This prevents a notebook from becoming an unreviewed second copy of
the analysis.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "template-eda-notebook-binding-v1"


def _digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def notebook_code_digest(path: Path) -> str:
    """Hash code-cell sources in notebook order, ignoring execution metadata."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    cells = payload.get("cells")
    if not isinstance(cells, list):
        raise ValueError("notebook cells must be a list")
    code_sources = ["".join(cell.get("source", [])) for cell in cells if cell.get("cell_type") == "code"]
    return _digest_bytes(json.dumps(code_sources, separators=(",", ":")).encode("utf-8"))


def source_digest(project_root: Path, paths: list[str]) -> str:
    """Hash the declared source files and their relative names."""
    canonical: list[dict[str, str]] = []
    root = Path(project_root).resolve()
    for relative in sorted(paths):
        path = (root / relative).resolve()
        path.relative_to(root)
        if not path.is_file():
            raise FileNotFoundError(path)
        canonical.append({"path": relative, "sha256": _digest_bytes(path.read_bytes())})
    return _digest_bytes(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def validate_binding(receipt: dict[str, Any], project_root: Path) -> tuple[str, ...]:
    """Validate the checked-in binding receipt against current files."""
    issues: list[str] = []
    if receipt.get("schema_version") != SCHEMA_VERSION:
        issues.append("unsupported notebook binding schema version")
    notebook = receipt.get("notebook")
    sources = receipt.get("sources")
    if not isinstance(notebook, dict) or not isinstance(sources, list):
        return ("notebook binding requires notebook and sources",)
    notebook_path = (Path(project_root) / str(notebook.get("path", ""))).resolve()
    try:
        notebook_path.relative_to(Path(project_root).resolve())
    except ValueError:
        issues.append("notebook path escapes project root")
    else:
        if not notebook_path.is_file():
            issues.append("bound notebook is missing")
        else:
            try:
                actual_notebook_digest = notebook_code_digest(notebook_path)
            except (OSError, ValueError, TypeError) as exc:
                issues.append(f"notebook cannot be parsed: {exc}")
            else:
                if actual_notebook_digest != notebook.get("code_digest"):
                    issues.append("notebook code-cell digest drift")
    source_paths = [str(row.get("path", "")) for row in sources if isinstance(row, dict)]
    if len(source_paths) != len(sources) or not all(source_paths):
        issues.append("source bindings require non-empty path rows")
    try:
        actual_source_digest = source_digest(Path(project_root), source_paths)
    except (OSError, ValueError) as exc:
        issues.append(f"source binding cannot be resolved: {exc}")
    else:
        if actual_source_digest != receipt.get("source_digest"):
            issues.append("source digest drift")
    return tuple(issues)


def build_binding_receipt(project_root: Path, notebook_path: str, source_paths: list[str]) -> dict[str, Any]:
    """Build a refreshable deterministic receipt for a notebook/source pair."""
    root = Path(project_root)
    return {
        "schema_version": SCHEMA_VERSION,
        "notebook": {"path": notebook_path, "code_digest": notebook_code_digest(root / notebook_path)},
        "sources": [{"path": path} for path in sorted(source_paths)],
        "source_digest": source_digest(root, source_paths),
        "refresh_command": "uv run python scripts/refresh_notebook_binding.py",
    }


__all__ = ["SCHEMA_VERSION", "build_binding_receipt", "notebook_code_digest", "source_digest", "validate_binding"]
