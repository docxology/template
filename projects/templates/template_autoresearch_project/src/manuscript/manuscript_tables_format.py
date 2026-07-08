"""Table-specific formatting helpers for manuscript table builders."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from .manuscript_tokens_format import escape_table_cell


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[str]], caption: str) -> str:
    """Process markdown table."""
    safe_rows = rows or tuple(("N/A",) * len(headers) for _ in range(1))
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in safe_rows:
        lines.append("| " + " | ".join(escape_table_cell(cell) for cell in row) + " |")
    lines.extend(("", f": {caption}"))
    return "\n".join(lines)


def pdf_small_table(headers: Sequence[str], rows: Sequence[Sequence[str]], caption: str) -> str:
    """Process pdf small table."""
    return "\n".join(("\\begingroup\\footnotesize", markdown_table(headers, rows, caption), "\\endgroup"))


def artifact_link_label(path: str) -> str:
    """Process artifact link label."""
    if path in {"", "N/A"}:
        return "N/A"
    stem = Path(path).stem
    for prefix in ("autoresearch_", "ml_", "mnist_"):
        stem = stem.removeprefix(prefix)
    labels = {
        "integrity_attestation": "integrity attestation",
        "security_profile": "security profile",
        "supply_chain_inventory": "supply inventory",
        "threat_model": "threat model",
        "candidate_intervals": "candidate intervals",
        "classification_diagnostics": "class diagnostics",
        "statistical_summary": "statistical summary",
        "probability_diagnostics": "probability diagnostics",
    }
    return labels.get(stem, stem.replace("_", " "))


def artifact_markdown_link(path: str) -> str:
    """Process artifact markdown link."""
    label = artifact_link_label(path)
    if path.startswith("output/"):
        target = "../" + path.removeprefix("output/")
    elif path.startswith("data/"):
        target = "../../" + path
    else:
        target = path
    return f"[{label}]({target})"
