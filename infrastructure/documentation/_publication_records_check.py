"""Check and write generated publication-record documentation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Mapping

from infrastructure.documentation._publication_records_external import refresh_external_records
from infrastructure.documentation._publication_records_load import load_publication_records
from infrastructure.documentation._publication_records_render import (
    render_github_readme_publication_block,
    render_publication_records_doc,
    replace_github_readme_publication_block,
)
from infrastructure.documentation._publication_records_types import (
    README_BLOCK_BEGIN,
    README_BLOCK_END,
)
from infrastructure.documentation.publication_standalone import (
    extract_standalone_publication_block,
    render_standalone_publication_block,
    replace_standalone_publication_block,
)


def _markdown_table_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        if not line.startswith("| "):
            continue
        columns = [column.strip() for column in line.strip().strip("|").split("|")]
        if not columns or all(set(column) <= {"-", " "} for column in columns):
            continue
        rows.append(columns)
    return rows


def _project_label_from_cell(cell: str) -> str:
    match = re.search(r"`([^`]+)`", cell)
    return match.group(1) if match else cell.strip()


def _publication_matrix_source_rows(text: str) -> dict[str, tuple[str, str, str, str, str, str]]:
    rows: dict[str, tuple[str, str, str, str, str, str]] = {}
    for columns in _markdown_table_rows(text):
        if len(columns) < 10:
            continue
        project_name = _project_label_from_cell(columns[0])
        if not project_name.startswith("templates/"):
            continue
        rows[project_name] = (columns[1], columns[2], columns[3], columns[5], columns[6], columns[7])
    return rows


def _local_source_path_rows(text: str) -> dict[str, tuple[str, str, str, str, str]]:
    rows: dict[str, tuple[str, str, str, str, str]] = {}
    for columns in _markdown_table_rows(text):
        if len(columns) != 6:
            continue
        project_name = _project_label_from_cell(columns[0])
        if not project_name.startswith("templates/") or "manuscript/config.yaml" not in columns[2]:
            continue
        rows[project_name] = (columns[1], columns[2], columns[3], columns[4], columns[5])
    return rows


def _github_readme_source_rows(text: str) -> dict[str, tuple[str, str, str, str, str, str]]:
    rows: dict[str, tuple[str, str, str, str, str, str]] = {}
    match = re.search(
        re.escape(README_BLOCK_BEGIN) + r"(?P<block>.*?)" + re.escape(README_BLOCK_END),
        text,
        flags=re.DOTALL,
    )
    if not match:
        return rows
    for columns in _markdown_table_rows(match.group("block")):
        if len(columns) < 8:
            continue
        project_name = _project_label_from_cell(columns[0])
        if not project_name.startswith("templates/"):
            continue
        rows[project_name] = (columns[1], columns[2], columns[3], columns[5], columns[6], columns[7])
    return rows


def _row_map_differences(
    label: str,
    current: Mapping[str, tuple[str, ...]],
    expected: Mapping[str, tuple[str, ...]],
) -> list[str]:
    differences: list[str] = []
    if current == expected:
        return differences
    missing = sorted(set(expected) - set(current))
    extra = sorted(set(current) - set(expected))
    changed = sorted(name for name in set(current) & set(expected) if current[name] != expected[name])
    details = []
    if missing:
        details.append(f"missing={missing}")
    if extra:
        details.append(f"extra={extra}")
    if changed:
        details.append(f"changed={changed}")
    differences.append(f"{label} drifted: {' '.join(details)}")
    return differences


def check_publication_records_doc(
    repo_root: Path,
    *,
    refresh_external: bool = False,
    update_github_readme: bool = True,
) -> list[str]:
    """Check publication records doc."""
    repo_root = Path(repo_root).resolve()
    records = load_publication_records(repo_root)
    if refresh_external:
        refresh_external_records(records)

    expected_doc = render_publication_records_doc(repo_root, records, refreshed_external=refresh_external)
    doc_path = repo_root / "docs" / "_generated" / "publication_records.md"
    if not doc_path.is_file():
        return [f"missing {doc_path.relative_to(repo_root)}"]

    differences: list[str] = []
    current_doc = doc_path.read_text(encoding="utf-8")
    differences.extend(
        _row_map_differences(
            "publication_records.md source-owned matrix columns",
            _publication_matrix_source_rows(current_doc),
            _publication_matrix_source_rows(expected_doc),
        )
    )
    differences.extend(
        _row_map_differences(
            "publication_records.md local source paths",
            _local_source_path_rows(current_doc),
            _local_source_path_rows(expected_doc),
        )
    )

    if update_github_readme:
        readme_path = repo_root / ".github" / "README.md"
        if not readme_path.is_file():
            differences.append(f"missing {readme_path.relative_to(repo_root)}")
        else:
            expected_readme = replace_github_readme_publication_block(
                readme_path.read_text(encoding="utf-8"),
                render_github_readme_publication_block(records),
            )
            differences.extend(
                _row_map_differences(
                    ".github/README.md publication block source-owned columns",
                    _github_readme_source_rows(readme_path.read_text(encoding="utf-8")),
                    _github_readme_source_rows(expected_readme),
                )
            )
    stale_standalone = [
        record.project_name
        for record in records
        if not record.standalone_path.is_file()
        or extract_standalone_publication_block(record.standalone_path.read_text(encoding="utf-8"))
        != render_standalone_publication_block(record)
    ]
    if stale_standalone:
        differences.append(f"standalone publication identity blocks drifted: {stale_standalone}")
    return differences


def write_publication_records_doc(
    repo_root: Path,
    *,
    refresh_external: bool = False,
    update_github_readme: bool = True,
) -> tuple[Path, Path | None]:
    """Write generated publication docs and optionally sync ``.github/README.md``."""
    repo_root = Path(repo_root).resolve()
    records = load_publication_records(repo_root)
    if refresh_external:
        refresh_external_records(records)

    out_dir = repo_root / "docs" / "_generated"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "publication_records.md"
    out_path.write_text(
        render_publication_records_doc(repo_root, records, refreshed_external=refresh_external),
        encoding="utf-8",
    )

    readme_path: Path | None = None
    if update_github_readme:
        readme_path = repo_root / ".github" / "README.md"
        block = render_github_readme_publication_block(records)
        readme_path.write_text(
            replace_github_readme_publication_block(readme_path.read_text(encoding="utf-8"), block),
            encoding="utf-8",
        )

    for record in records:
        if not record.standalone_path.is_file():
            continue
        current = record.standalone_path.read_text(encoding="utf-8")
        record.standalone_path.write_text(
            replace_standalone_publication_block(current, render_standalone_publication_block(record)),
            encoding="utf-8",
        )

    return out_path, readme_path
