"""PDF Preflight Validation module."""

from __future__ import annotations

import re


def check_brace_balance(md_content: str) -> list[str]:
    """Check markdown content for unbalanced braces.

    Performs three checks:
    1. Balanced braces in section header attributes {#id}
    2. Balanced braces in header lines
    3. Character-by-character brace balance outside code blocks and LaTeX commands

    Args:
        md_content: Raw markdown string to validate

    Returns:
        List of warning message strings (empty if no issues found)
    """
    warnings: list[str] = []

    # Check balanced braces in section header attributes
    header_attr_pattern = r"\{#([a-zA-Z0-9_:.-]+)"
    for attr in re.findall(header_attr_pattern, md_content):
        if attr.count("{") != attr.count("}"):
            warnings.append(f"Unbalanced braces in section header attribute: {{#{attr}}}")

    # Check balanced braces in full header lines
    for header_line in re.findall(r"^#+\s+.*\{#.*$", md_content, re.MULTILINE):
        if header_line.count("{") != header_line.count("}"):
            warnings.append(f"Unbalanced braces in header line: {header_line[:80]}")

    # Character-by-character brace balance outside code blocks and LaTeX commands
    # Strip fenced and inline code blocks first to avoid false positives
    content = re.sub(r"```.*?```", "", md_content, flags=re.DOTALL)
    content = re.sub(r"`[^`]+`", "", content)

    brace_count = 0
    i = 0
    while i < len(content):
        char = content[i]
        if char == "\\" and i < len(content) - 1 and content[i + 1].isalpha():
            # Skip LaTeX command including optional [...] and required {...} arguments
            j = i + 2
            while j < len(content) and content[j].isalpha():
                j += 1
            if j < len(content) and content[j] == "[":
                depth = 1
                j += 1
                while j < len(content) and depth > 0:
                    if content[j] == "[":
                        depth += 1
                    elif content[j] == "]":
                        depth -= 1
                    j += 1
            if j < len(content) and content[j] == "{":
                depth = 1
                j += 1
                while j < len(content) and depth > 0:
                    if content[j] == "{":
                        depth += 1
                    elif content[j] == "}":
                        depth -= 1
                    j += 1
            i = j
            continue
        elif char == "{":
            brace_count += 1
        elif char == "}":
            brace_count -= 1
        i += 1

    if brace_count != 0:
        warnings.append(
            f"Potential unbalanced braces in markdown: "
            f"difference={brace_count} (positive=more {{, negative=more }})"
        )

    return warnings
