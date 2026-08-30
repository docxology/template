"""Figure path normalization for Beamer LaTeX emitted by Pandoc."""

from __future__ import annotations

import re
from pathlib import Path


_EMPTY_PROJECTED_CAPTION_RE = re.compile(r"\\caption\{\}")
_PROJECTED_FLOAT_RE = re.compile(
    r"(?P<open>\\begin\{(?P<environment>figure\*?|table\*?|longtable)\})(?P<body>.*?)(?P<close>\\end\{(?P=environment)\})",
    flags=re.DOTALL,
)
_VERBATIM_ENVIRONMENT_RE = re.compile(
    r"\\begin\{(?P<environment>verbatim\*?|Verbatim|lstlisting|minted)\}.*?"
    r"\\end\{(?P=environment)\}",
    flags=re.DOTALL,
)
_INLINE_VERB_RE = re.compile(r"\\verb\*?(?P<delimiter>[^\w\s]).*?(?P=delimiter)", flags=re.DOTALL)
_ENVIRONMENT_TOKEN_RE = re.compile(r"\\(?P<action>begin|end)\{(?P<environment>[^{}]+)\}")
_DIRECT_HREF_IMAGE_PREFIX_RE = re.compile(
    r"\\href\s*\{(?:\\.|[^{}])*\}\s*\{\s*$",
    flags=re.DOTALL,
)


def _split_top_level_options(options: str) -> list[str]:
    """Split a LaTeX option list without treating braced commas as separators."""

    items: list[str] = []
    start = 0
    brace_depth = 0
    bracket_depth = 0
    escaped = False
    for index, character in enumerate(options):
        if escaped:
            escaped = False
            continue
        if character == "\\":
            escaped = True
            continue
        if character == "{":
            brace_depth += 1
            continue
        if character == "}":
            brace_depth = max(0, brace_depth - 1)
            continue
        if character == "[":
            bracket_depth += 1
            continue
        if character == "]":
            bracket_depth = max(0, bracket_depth - 1)
            continue
        if character == "," and brace_depth == 0 and bracket_depth == 0:
            items.append(options[start:index])
            start = index + 1
    items.append(options[start:])
    return items


def _commented_at(text: str, position: int) -> bool:
    """Return whether ``position`` follows an unescaped percent on its line."""

    line_start = text.rfind("\n", 0, position) + 1
    for index in range(line_start, position):
        if text[index] != "%":
            continue
        backslashes = 0
        cursor = index - 1
        while cursor >= line_start and text[cursor] == "\\":
            backslashes += 1
            cursor -= 1
        if backslashes % 2 == 0:
            return True
    return False


def _environment_depth_at(text: str, position: int) -> int:
    """Return direct-environment depth before one TeX position."""

    depth = 0
    for token in _ENVIRONMENT_TOKEN_RE.finditer(text, 0, position):
        if _commented_at(text, token.start()):
            continue
        if token.group("action") == "begin":
            depth += 1
        else:
            depth = max(0, depth - 1)
    return depth


def _brace_depth_at(text: str, position: int) -> int:
    """Return unescaped TeX brace depth before one direct-body position."""

    depth = 0
    escaped = False
    for index, character in enumerate(text[:position]):
        if character == "\n":
            escaped = False
            continue
        if _commented_at(text, index):
            continue
        if escaped:
            escaped = False
            continue
        if character == "\\":
            escaped = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth = max(0, depth - 1)
    return depth


def _inside_direct_href_image(text: str, position: int) -> bool:
    """Return whether an image is the direct body of a top-level href.

    Pandoc wraps linked thumbnails as ``\\href{target}{\\includegraphics}``.
    That one supported wrapper introduces brace depth but no peer content;
    arbitrary nested macros and caption bodies remain outside this exception.
    """

    match = _DIRECT_HREF_IMAGE_PREFIX_RE.search(text[:position])
    return bool(
        match is not None
        and not _commented_at(text, match.start())
        and _environment_depth_at(text, match.start()) == 0
        and _brace_depth_at(text, match.start()) == 0
    )


def _remove_projected_empty_captions(tex_content: str) -> tuple[str, int]:
    """Replace direct empty captions with zero-glue counter advancement.

    A generated empty caption consumes projection space, but deleting it
    outright also deletes the ``\\refstepcounter`` side effect that binds a
    following label.  Preserve standalone/local-reference numbering without
    restoring caption glue.
    """

    removed = 0

    def _normalize_float(match: re.Match[str]) -> str:
        nonlocal removed
        body = match.group("body")
        environment = match.group("environment")
        counter = "figure" if environment.startswith("figure") else "table"
        # ``longtable`` advances ``\LTcaptype`` at environment start; a
        # second manual step would skip a table number. Ordinary figure/table
        # floats advance only through their caption and therefore need the
        # zero-glue replacement.
        counter_step = "" if environment == "longtable" else rf"\refstepcounter{{{counter}}}"
        protected = [
            *(item.span() for item in _VERBATIM_ENVIRONMENT_RE.finditer(body)),
            *(item.span() for item in _INLINE_VERB_RE.finditer(body)),
        ]
        pieces: list[str] = []
        cursor = 0
        for caption in _EMPTY_PROJECTED_CAPTION_RE.finditer(body):
            in_verbatim = any(start <= caption.start() < end for start, end in protected)
            if (
                in_verbatim
                or _commented_at(body, caption.start())
                or _environment_depth_at(body, caption.start())
                or _brace_depth_at(body, caption.start())
            ):
                continue
            pieces.append(body[cursor : caption.start()])
            pieces.append(counter_step)
            cursor = caption.end()
            removed += 1
        if not pieces:
            normalized_body = body
        else:
            pieces.append(body[cursor:])
            normalized_body = "".join(pieces)
        return match.group("open") + normalized_body + match.group("close")

    return _PROJECTED_FLOAT_RE.sub(_normalize_float, tex_content), removed


def _normalize_direct_projection_graphics(
    tex_content: str,
    *,
    owned_projection_only: bool = False,
) -> tuple[str, int]:
    """Normalize bounded generated graphics while preserving authored TeX.

    The normal float-body pass remains direct-scope only.  A second narrow
    pass may reach bare or linked image paragraphs, but only when their exact
    bounded-width-by-70%-height options identify a composer-owned projection
    envelope.
    """

    pieces: list[str] = []
    cursor = 0
    graphics = 0
    command = r"\includegraphics"
    protected = [
        *(item.span() for item in _VERBATIM_ENVIRONMENT_RE.finditer(tex_content)),
        *(item.span() for item in _INLINE_VERB_RE.finditer(tex_content)),
    ]
    while True:
        start = tex_content.find(command, cursor)
        if start == -1:
            pieces.append(tex_content[cursor:])
            break
        pieces.append(tex_content[cursor:start])
        option_start = start + len(command)
        while option_start < len(tex_content) and tex_content[option_start].isspace():
            option_start += 1
        if (
            _commented_at(tex_content, start)
            or any(protected_start <= start < protected_end for protected_start, protected_end in protected)
            or (
                not owned_projection_only
                and (
                    _environment_depth_at(tex_content, start)
                    or (_brace_depth_at(tex_content, start) and not _inside_direct_href_image(tex_content, start))
                )
            )
            or option_start >= len(tex_content)
            or tex_content[option_start] != "["
        ):
            pieces.append(tex_content[start:option_start])
            cursor = option_start
            continue

        depth = 0
        brace_depth = 0
        escaped = False
        option_end: int | None = None
        for index in range(option_start, len(tex_content)):
            character = tex_content[index]
            if escaped:
                escaped = False
                continue
            if character == "\\":
                escaped = True
                continue
            if character == "{":
                brace_depth += 1
                continue
            if character == "}":
                brace_depth = max(0, brace_depth - 1)
                continue
            if character == "[" and brace_depth == 0:
                depth += 1
                continue
            if character == "]" and brace_depth == 0:
                depth -= 1
                if depth == 0:
                    option_end = index
                    break
        if option_end is None:
            pieces.append(tex_content[start:])
            cursor = len(tex_content)
            break

        options = tex_content[option_start + 1 : option_end]
        option_items = _split_top_level_options(options)
        named_options = [(item.partition("=")[0].strip().casefold(), item) for item in option_items if item.strip()]
        option_names = {name for name, _item in named_options}
        option_values = {
            name: item.partition("=")[2].replace(" ", "").casefold() for name, item in named_options if "=" in item
        }
        width_match = re.fullmatch(
            r"(?P<factor>(?:0?\.\d+|1(?:\.0+)?))\\linewidth",
            option_values.get("width", ""),
        )
        height_match = re.fullmatch(
            r"(?P<factor>(?:0?\.\d+|1(?:\.0+)?))\\textheight",
            option_values.get("height", ""),
        )
        composer_owned_bounds = bool(
            width_match is not None
            and height_match is not None
            and 0 < float(width_match.group("factor")) <= 0.98
            and 0 < float(height_match.group("factor")) <= 1.0
        )
        if "width" in option_names and "height" in option_names:
            if owned_projection_only and not composer_owned_bounds:
                pieces.append(tex_content[start : option_end + 1])
                cursor = option_end + 1
                continue
            aspect_items = [item for name, item in named_options if name == "keepaspectratio"]
            effective_aspect = len(aspect_items) == 1 and aspect_items[0].strip().casefold() == "keepaspectratio"
            if not effective_aspect:
                retained = [item for name, item in named_options if name != "keepaspectratio"]
                options = ",".join(["keepaspectratio", *retained])
                graphics += 1
        pieces.append(tex_content[start : option_start + 1])
        pieces.append(options)
        pieces.append("]")
        cursor = option_end + 1

    return "".join(pieces), graphics


def normalize_accessible_projection_latex(tex_content: str) -> tuple[str, int, int]:
    """Preserve projected image proportions and remove empty-caption glue.

    The accessible composer deliberately leaves projected figure captions
    empty because the complete caption, long description, and exact values
    live in the linked canonical HTML reader. Pandoc nevertheless serializes
    that empty AST caption as ``\\caption{}``, which consumes vertical space.
    It also omits ``keepaspectratio`` when both source-owned width and height
    bounds are present. Normalize only these generated figure details; archive
    slides never call this helper.

    Returns the updated TeX, number of graphics normalized, and number of empty
    projected figure or table caption commands removed.
    """

    graphics = 0
    captions = 0

    def _normalize_float(match: re.Match[str]) -> str:
        nonlocal captions, graphics
        body = match.group("body")
        if match.group("environment") in {"figure", "figure*"}:
            body, normalized_graphics = _normalize_direct_projection_graphics(body)
            graphics += normalized_graphics
        float_text = match.group("open") + body + match.group("close")
        float_text, removed_captions = _remove_projected_empty_captions(float_text)
        captions += removed_captions
        return float_text

    updated = _PROJECTED_FLOAT_RE.sub(_normalize_float, tex_content)
    # Pandoc emits image-only paragraphs as bare ``\\includegraphics`` (or
    # inside a direct ``\\href`` wrapper), without a figure environment. The
    # exact composer-owned bounds make this pass narrow enough to reach those
    # images without rewriting arbitrary nested authored graphics.
    updated, normalized_bare_graphics = _normalize_direct_projection_graphics(
        updated,
        owned_projection_only=True,
    )
    graphics += normalized_bare_graphics
    return updated, graphics, captions


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
