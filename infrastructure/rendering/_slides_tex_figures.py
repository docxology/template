"""Figure path normalization for Beamer LaTeX emitted by Pandoc."""

from __future__ import annotations

import re
from pathlib import Path


def fix_slides_figure_paths(tex_content: str, output_dir: Path, figures_dir: Path) -> str:
    """Fix figure paths in LaTeX content for proper compilation.

    Converts paths like ../output/figures/file.png to relative paths
    that work from the LaTeX compilation directory (output/slides).

    Handles multiple path formats and preserves optional parameters.

    Args:
        tex_content: LaTeX content to process
        output_dir: Directory where LaTeX compilation happens (output/slides)
        figures_dir: Directory containing figures (output/figures)

    Returns:
        LaTeX content with corrected figure paths
    """

    def extract_filename(path_str: str) -> str:
        """Extract filename from various path formats."""
        # Handle various path formats
        path_variations = [
            "../output/figures/",
            "output/figures/",
            "../figures/",
            "./figures/",
        ]

        for prefix in path_variations:
            if prefix in path_str:
                return path_str.split(prefix)[-1]

        # If no prefix matched, extract filename from path
        if "/" in path_str or "\\" in path_str:
            return re.split(r"[/\\]", path_str)[-1]
        else:
            # No separators — path_str is already a bare filename
            return path_str

    def matching_delimiter(start: int, opener: str, closer: str) -> int | None:
        """Return the index just after a balanced delimiter group.

        Pandoc commonly emits ``\\includegraphics[alt={... [ ...]}]{...}``.
        A regex like ``\\[([^\\]]*)\\]`` stops at the first bracket inside
        the alt text and therefore misses the real path argument.  This
        scanner tracks braces while looking for the closing option
        bracket, which is enough for Pandoc's generated Beamer LaTeX.
        """
        depth = 0
        brace_depth = 0
        escaped = False
        for idx in range(start, len(tex_content)):
            ch = tex_content[idx]
            if escaped:
                escaped = False
                continue
            if ch == "\\":
                escaped = True
                continue
            if ch == "{":
                brace_depth += 1
                continue
            if ch == "}":
                brace_depth = max(0, brace_depth - 1)
                continue
            if ch == opener and brace_depth == 0:
                depth += 1
                continue
            if ch == closer and brace_depth == 0:
                depth -= 1
                if depth == 0:
                    return idx + 1
        return None

    def matching_brace(start: int) -> int | None:
        """Find the index of the matching closing brace."""
        depth = 0
        escaped = False
        for idx in range(start, len(tex_content)):
            ch = tex_content[idx]
            if escaped:
                escaped = False
                continue
            if ch == "\\":
                escaped = True
                continue
            if ch == "{":
                depth += 1
                continue
            if ch == "}":
                depth -= 1
                if depth == 0:
                    return idx + 1
        return None

    pieces: list[str] = []
    cursor = 0
    command = r"\includegraphics"
    while True:
        start = tex_content.find(command, cursor)
        if start == -1:
            pieces.append(tex_content[cursor:])
            break

        pieces.append(tex_content[cursor:start])
        pos = start + len(command)
        while pos < len(tex_content) and tex_content[pos].isspace():
            pos += 1

        if pos < len(tex_content) and tex_content[pos] == "[":
            opt_end = matching_delimiter(pos, "[", "]")
            if opt_end is None:
                pieces.append(tex_content[start:])
                cursor = len(tex_content)
                break
            pos = opt_end
            while pos < len(tex_content) and tex_content[pos].isspace():
                pos += 1

        if pos >= len(tex_content) or tex_content[pos] != "{":
            pieces.append(tex_content[start:pos])
            cursor = pos
            continue

        arg_end = matching_brace(pos)
        if arg_end is None:
            pieces.append(tex_content[start:])
            cursor = len(tex_content)
            break

        old_path = tex_content[pos + 1 : arg_end - 1]
        if old_path.startswith("../figures/"):
            pieces.append(tex_content[start:arg_end])
        else:
            filename = extract_filename(old_path)
            new_path = f"../figures/{filename}"
            pieces.append(tex_content[start : pos + 1])
            pieces.append(new_path)
            pieces.append("}")
        cursor = arg_end

    return "".join(pieces)
