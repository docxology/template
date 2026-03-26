"""Inventory report generation (text, JSON, HTML).

Extracted from FileInventoryManager to keep each module focused.
These functions accept inventory entries and produce formatted reports.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.files.inventory_entry import FileInventoryEntry, format_file_size


# Standard output categories — used for report ordering
OUTPUT_CATEGORIES = (
    "pdf",
    "figures",
    "data",
    "reports",
    "simulations",
    "llm",
    "logs",
    "web",
    "slides",
    "tex",
)


def group_by_category(
    entries: list[FileInventoryEntry],
) -> dict[str, list[FileInventoryEntry]]:
    """Group entries by category.

    Args:
        entries: File inventory entries

    Returns:
        Dictionary mapping category names to lists of entries
    """
    groups: dict[str, list[FileInventoryEntry]] = {}
    for entry in entries:
        if entry.category not in groups:
            groups[entry.category] = []
        groups[entry.category].append(entry)
    return groups


def generate_text_report(
    entries: list[FileInventoryEntry], base_dir: Path | None = None
) -> str:
    """Generate text format inventory report.

    Args:
        entries: File inventory entries
        base_dir: Base directory for relative paths

    Returns:
        Text report
    """
    if not entries:
        return "No files found"

    category_groups = group_by_category(entries)

    lines: list[str] = []
    lines.append("Generated Files Inventory:")
    lines.append("")

    for category in OUTPUT_CATEGORIES:
        if category in category_groups:
            category_entries = category_groups[category]
            total_size = sum(entry.size for entry in category_entries)
            count = len(category_entries)

            category_name = category.upper() if category in ["pdf", "tex"] else category.title()
            lines.append(
                f"  {category_name} ({count} file(s), {format_file_size(total_size)}):"
            )

            shown_count = 0
            for entry in sorted(category_entries, key=lambda e: e.path):
                if shown_count >= 10:
                    remaining = len(category_entries) - 10
                    if remaining > 0:
                        lines.append(f"    ... and {remaining} more file(s)")
                    break

                rel_path = entry.path.relative_to(base_dir) if base_dir else entry.path
                lines.append(f"    - {rel_path} ({entry.size_formatted})")
                shown_count += 1

            lines.append("")

    return "\n".join(lines)


def generate_json_report(
    entries: list[FileInventoryEntry], base_dir: Path | None = None
) -> str:
    """Generate JSON format inventory report.

    Args:
        entries: File inventory entries
        base_dir: Base directory for relative paths

    Returns:
        JSON report
    """
    import json

    category_groups = group_by_category(entries)

    result = {}
    for category, category_entries in category_groups.items():
        result[category] = {
            "count": len(category_entries),
            "total_size": sum(entry.size for entry in category_entries),
            "total_size_formatted": format_file_size(
                sum(entry.size for entry in category_entries)
            ),
            "files": [
                {
                    "path": (
                        str(entry.path.relative_to(base_dir)) if base_dir else str(entry.path)
                    ),
                    "size": entry.size,
                    "size_formatted": entry.size_formatted,
                    "modified": entry.modified,
                }
                for entry in sorted(category_entries, key=lambda e: e.path)
            ],
        }

    return json.dumps(result, indent=2)


def generate_html_report(
    entries: list[FileInventoryEntry], base_dir: Path | None = None
) -> str:
    """Generate HTML format inventory report.

    Args:
        entries: File inventory entries
        base_dir: Base directory for relative paths

    Returns:
        HTML report
    """
    if not entries:
        return "<p>No files found in output directory</p>"

    category_groups = group_by_category(entries)

    html_parts: list[str] = []
    html_parts.append("<div class='file-inventory'>")
    html_parts.append("<h3>Generated Files Inventory</h3>")

    for category in OUTPUT_CATEGORIES:
        if category in category_groups:
            category_entries = category_groups[category]
            total_size = sum(entry.size for entry in category_entries)
            count = len(category_entries)

            category_name = category.upper() if category in ["pdf", "tex"] else category.title()
            html_parts.append(
                f"<h4>{category_name} ({count} file(s), {format_file_size(total_size)})</h4>"
            )
            html_parts.append("<ul>")

            for entry in sorted(category_entries, key=lambda e: e.path):
                rel_path = entry.path.relative_to(base_dir) if base_dir else entry.path
                html_parts.append(f"<li><code>{rel_path}</code> ({entry.size_formatted})</li>")

            html_parts.append("</ul>")

    html_parts.append("</div>")

    return "\n".join(html_parts)
