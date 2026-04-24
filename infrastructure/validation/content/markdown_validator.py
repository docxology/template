"""Markdown validation utilities for ensuring document integrity.

This module provides comprehensive validation of markdown files including:
- Image reference validation
- Cross-reference validation
- Mathematical equation validation
- Link and URL validation

This is part of the infrastructure layer (generic, reusable validation).
"""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.core.exceptions import FileNotFoundError, NotADirectoryError
from infrastructure.core.logging import DiagnosticEvent, DiagnosticSeverity
from infrastructure.core.logging.utils import get_logger
from infrastructure.validation.content.diagnostic_codes import (
    BibtexCode,
    MarkdownCode,
)

logger = get_logger(__name__)

# Regex patterns for validation
IMG_PATTERN = re.compile(r"!\[[^\]]*\]\(([^\)]+)\)")
EQ_LABEL_PATTERN = re.compile(r"\\label\{([^}]+)\}")
EQ_REF_PATTERN = re.compile(r"\\eqref\{([^}]+)\}")
ANCHOR_PATTERN = re.compile(r"\{#([^}]+)\}")
INTERNAL_LINK_PATTERN = re.compile(r"\(#([^\)]+)\)")
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\((https?://[^\)]+)\)")
BARE_URL_PATTERN = re.compile(r"(?<!\]\()https?://\S+")


def _text_without_fenced_code(text: str) -> str:
    """Remove triple-backtick and tilde-fenced code blocks.

    Used for reference and internal-link checks so LaTeX inside a fenced
    ``latex`` block (e.g. ``p(#1)`` in ``\\newcommand``) is not misparsed
    as Markdown ``(#...)`` internal links.
    """
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"~~~[\s\S]*?~~~", "", text)
    return text

# Pandoc converts bare ``|word|`` in prose contexts and escaped ``\|`` inside
# table cells to the math macro ``\mid``. When the surrounding text is
# rendered in text mode (e.g. table cell, prose, accessibility alt-text),
# ``\mid`` falls back to the text font (lmroman) which lacks U+2223 and emits
# ``Missing character`` warnings followed by ``U+FFFD`` glyphs in the PDF.
# These two patterns flag the markdown sources that trigger the conversion
# so authors can wrap them in math mode (``$|word|$`` or ``$\mid$``).
PANDOC_BARE_PIPE_PATTERN = re.compile(r"(?<![\\$`])\|(\w+)\|(?![$`])")
PANDOC_TABLE_ESCAPED_PIPE_PATTERN = re.compile(r"\\\|")
CITE_KEY_PATTERN = re.compile(r"(?<![A-Za-z0-9_])@([A-Za-z][\w:.\-]*)")
# Tolerate both ``,`` and ``}`` as the key terminator: BibTeX permits a
# field-less entry such as ``@misc{key}`` where there is no comma after the
# key. The original ``,``-only regex silently dropped these.
BIBTEX_KEY_PATTERN = re.compile(r"^@\w+\{\s*([^,\s}]+)\s*[,}]", re.MULTILINE)

# Files that live alongside manuscript content but are never rendered into the
# final PDF (project documentation / preamble metadata). Skipped by the
# render-time pitfall and citation checks to avoid false positives.
NON_RENDERED_MANUSCRIPT_FILES: frozenset[str] = frozenset(
    {"AGENTS.md", "README.md", "preamble.md"}
)


def find_markdown_files(markdown_dir: str | Path) -> list[str]:
    """Find all markdown files in the specified directory.

    Args:
        markdown_dir: Directory to search for markdown files

    Returns:
        List of full paths to markdown files, sorted by filename

    Raises:
        FileNotFoundError: If markdown_dir doesn't exist
    """
    markdown_dir = Path(markdown_dir)
    if not markdown_dir.exists():
        raise FileNotFoundError(
            f"Markdown directory not found: {markdown_dir}",
            context={"directory": str(markdown_dir)},
        )

    if not markdown_dir.is_dir():
        raise NotADirectoryError(
            f"Path is not a directory: {markdown_dir}",
            context={"path": str(markdown_dir)},
        )

    return [str(p) for p in sorted(markdown_dir.glob("*.md"))]


def collect_symbols(md_paths: list[str]) -> tuple[set[str], set[str]]:
    """Collect all equation labels and section anchors from markdown files.

    Args:
        md_paths: List of markdown file paths to process

    Returns:
        Tuple of (equation_labels, section_anchors) as sets
    """
    labels: set[str] = set()
    anchors: set[str] = set()
    for path in md_paths:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        labels.update(EQ_LABEL_PATTERN.findall(text))
        anchors.update(ANCHOR_PATTERN.findall(text))
    return labels, anchors


def validate_images(
    md_paths: list[str],
    repo_root: str | Path,
    extra_search_dirs: list[str | Path] | None = None,
) -> list[DiagnosticEvent]:
    """Validate that all referenced images exist in the filesystem.

    When a relative image path fails to resolve from the markdown file's
    directory, this function also checks ``extra_search_dirs`` and
    auto-discovered project-level figure directories (``output/figures/``
    and ``figures/`` relative to the manuscript's project root).

    Args:
        md_paths: List of markdown file paths to validate
        repo_root: Root directory of the repository
        extra_search_dirs: Additional directories to search for images

    Returns:
        List of DiagnosticEvents for missing images.
    """
    repo_root_path = Path(repo_root)
    problems: list[DiagnosticEvent] = []

    # Build search directories from the markdown directory's project context.
    # Manuscript dirs follow the pattern: projects/<name>/manuscript/
    # So the project root is two levels up from the manuscript dir.
    search_dirs: list[Path] = []
    if extra_search_dirs:
        search_dirs.extend(Path(d) for d in extra_search_dirs)

    if md_paths:
        md_dir = Path(md_paths[0]).parent
        # Auto-discover sibling output/figures/ and figures/ dirs
        project_root = md_dir.parent  # parent of manuscript/
        for candidate in [
            project_root / "output" / "figures",
            project_root / "figures",
        ]:
            if candidate.is_dir() and candidate not in search_dirs:
                search_dirs.append(candidate)

    for path in md_paths:
        path_obj = Path(path)
        text = path_obj.read_text(encoding="utf-8")
        for img in IMG_PATTERN.findall(text):
            # Strip optional attributes after ) are not included by regex
            img_clean = img.split()[0]
            # Normalize relative paths (most are ../output/...  or figures/)
            abs_path = (path_obj.parent / img_clean).resolve()
            if abs_path.exists():
                continue

            # Try each search directory as a fallback
            img_basename = Path(img_clean).name
            found = False
            for search_dir in search_dirs:
                if (search_dir / img_basename).exists():
                    found = True
                    break
            if not found:
                display_path: Path
                try:
                    display_path = Path(path).relative_to(repo_root_path)
                except ValueError:
                    display_path = path_obj
                problems.append(
                    DiagnosticEvent(
                        severity=DiagnosticSeverity.ERROR,
                        category="MARKDOWN_IMAGE",
                        message=f"Missing referenced image: '{img_clean}'",
                        code=MarkdownCode.IMG_MISSING,
                        file_path=str(display_path),
                        fix_suggestion="Ensure the image file exists in the specified relative path or figures directory."
                    )
                )
    return problems


def validate_refs(
    md_paths: list[str], repo_root: str | Path, labels: set[str], anchors: set[str]
) -> list[DiagnosticEvent]:
    """Validate cross-references, internal links, and external URLs.

    Args:
        md_paths: List of markdown file paths to validate
        repo_root: Root directory of the repository
        labels: Set of valid equation labels
        anchors: Set of valid section anchors

    Returns:
        List of DiagnosticEvents for reference issues.
    """
    repo_root_path = Path(repo_root)
    problems: list[DiagnosticEvent] = []
    for path in md_paths:
        text = Path(path).read_text(encoding="utf-8")
        try:
            rel: str | Path = Path(path).relative_to(repo_root_path)
        except ValueError:
            rel = path
            
        rel_str = str(rel)
        text_wo_fences = _text_without_fenced_code(text)
        for ref in EQ_REF_PATTERN.findall(text_wo_fences):
            if ref not in labels:
                problems.append(
                    DiagnosticEvent(
                        severity=DiagnosticSeverity.ERROR,
                        category="MARKDOWN_REF",
                        message=f"Missing equation label for \\eqref{{{ref}}}",
                        code=MarkdownCode.REF_EQUATION_MISSING,
                        file_path=rel_str,
                        fix_suggestion=f"Verify that '\\label{{{ref}}}' exists in an equation block."
                    )
                )
        for link in INTERNAL_LINK_PATTERN.findall(text_wo_fences):
            if link not in anchors and link not in labels:
                problems.append(
                    DiagnosticEvent(
                        severity=DiagnosticSeverity.ERROR,
                        category="MARKDOWN_LINK",
                        message=f"Missing anchor/label for internal link (#{link})",
                        code=MarkdownCode.LINK_ANCHOR_MISSING,
                        file_path=rel_str,
                        fix_suggestion=f"Provide a heading anchor '{{#{link}}}' or equation label."
                    )
                )
        # Flag bare URLs not inside Markdown links.
        text_no_code = re.sub(r"```[^`]*```", "", text, flags=re.DOTALL)
        text_no_code = re.sub(r"`[^`]+`", "", text_no_code)  # also strip inline code
        for m in BARE_URL_PATTERN.finditer(text_no_code):
            problems.append(
                DiagnosticEvent(
                    severity=DiagnosticSeverity.WARNING,
                    category="MARKDOWN_LINK",
                    message=f"Bare URL found: '{m.group(0)}'",
                    code=MarkdownCode.LINK_BARE_URL,
                    file_path=rel_str,
                    fix_suggestion="Wrap the URL in a Markdown link with informative text: [link text](url)"
                )
            )
        # Flag non-informative link text
        for m in LINK_PATTERN.finditer(text):
            label = m.group(1).strip()
            url = m.group(2).strip()
            if label == url or label.lower().startswith("http") or "/" in label:
                problems.append(
                    DiagnosticEvent(
                        severity=DiagnosticSeverity.WARNING,
                        category="MARKDOWN_LINK",
                        message=f"Non-informative link text for {url}",
                        code=MarkdownCode.LINK_BAD_TEXT,
                        file_path=rel_str,
                        fix_suggestion=f"Replace '{label}' with descriptive text about the link destination."
                    )
                )
    return problems


def validate_math(md_paths: list[str], repo_root: str | Path) -> list[DiagnosticEvent]:
    """Validate mathematical equation formatting and labeling.

    Args:
        md_paths: List of markdown file paths to validate
        repo_root: Root directory of the repository

    Returns:
        List of DiagnosticEvents for math formatting issues.
    """
    repo_root_path = Path(repo_root)
    problems: list[DiagnosticEvent] = []
    eq_block = re.compile(r"\\begin\{equation\}([\s\S]*?)\\end\{equation\}", re.MULTILINE)
    label_pattern = re.compile(r"\\label\{([^}]+)\}")
    seen_labels: set[str] = set()
    for path in md_paths:
        text = Path(path).read_text(encoding="utf-8")
        try:
            rel: str | Path = Path(path).relative_to(repo_root_path)
        except ValueError:
            rel = path
            
        rel_str = str(rel)
            
        # Disallow $$ and \[ \] display math in sources
        if "$$" in text:
            problems.append(
                DiagnosticEvent(
                    severity=DiagnosticSeverity.WARNING,
                    category="MARKDOWN_MATH",
                    message="Use equation environment instead of $$",
                    code=MarkdownCode.MATH_DOLLAR_DISPLAY,
                    file_path=rel_str,
                    fix_suggestion="Replace $$...$$ with \\begin{equation}...\\end{equation}"
                )
            )
        if "\\[" in text or "\\]" in text:
            problems.append(
                DiagnosticEvent(
                    severity=DiagnosticSeverity.WARNING,
                    category="MARKDOWN_MATH",
                    message="Use equation environment instead of \\[ \\]",
                    code=MarkdownCode.MATH_BRACKET_DISPLAY,
                    file_path=rel_str,
                    fix_suggestion="Replace \\[...\\] with \\begin{equation}...\\end{equation}"
                )
            )
        # Ensure each equation block carries a label and detect duplicates
        for m in eq_block.finditer(text):
            block = m.group(1)
            labels_in_block = label_pattern.findall(block)
            if not labels_in_block:
                problems.append(
                    DiagnosticEvent(
                        severity=DiagnosticSeverity.WARNING,
                        category="MARKDOWN_MATH",
                        message="Equation missing \\label{...}",
                        code=MarkdownCode.MATH_LABEL_MISSING,
                        file_path=rel_str,
                        fix_suggestion="Add a \\label{eq_name} inside the \\begin{equation} block."
                    )
                )
            else:
                for lab in labels_in_block:
                    if lab in seen_labels:
                        problems.append(
                            DiagnosticEvent(
                                severity=DiagnosticSeverity.ERROR,
                                category="MARKDOWN_MATH",
                                message=f"Duplicate equation label '{{{lab}}}' found",
                                code=MarkdownCode.MATH_LABEL_DUPLICATE,
                                file_path=rel_str,
                                fix_suggestion="Rename one of the labels to be unique."
                            )
                        )
                    seen_labels.add(lab)
    return problems


def _strip_code_and_math(text: str) -> str:
    """Remove fenced code, inline code, display math, and inline math regions.

    Strips, in order:
      1. Triple-backtick fenced blocks (```...```).
      2. Tilde-fenced blocks (~~~...~~~).
      3. Inline code (`...`).
      4. Indented code blocks (4+ leading spaces, contiguous lines).
      5. LaTeX environments commonly used for display math.
      6. Display math \\[ \\] and \\( \\).
      7. Inline ``$...$`` math.

    Used by Pandoc-pitfall and citation checks so that patterns inside
    code blocks or math contexts are not flagged.
    """
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"~~~[\s\S]*?~~~", "", text)
    text = re.sub(r"`[^`\n]+`", "", text)
    # Indented code blocks: contiguous run of lines each starting with 4+ spaces
    # or a tab, preceded by a blank line (or start of file). Markdown's loose
    # rule is "indent of 4+ spaces or a tab"; we collapse such runs to nothing.
    text = re.sub(
        r"(?:\A|\n)(?:[ ]{4,}|\t)[^\n]*(?:\n(?:[ ]{4,}|\t)[^\n]*)*",
        "\n",
        text,
    )
    text = re.sub(r"\\begin\{(equation\*?|align\*?|gather\*?|multline\*?)\}[\s\S]*?\\end\{\1\}", "", text)
    text = re.sub(r"\\\([\s\S]*?\\\)", "", text)
    text = re.sub(r"\\\[[\s\S]*?\\\]", "", text)
    text = re.sub(r"(?<!\$)\$(?!\$)([^$\n]+?)(?<!\$)\$(?!\$)", "", text)
    return text


def validate_pandoc_pitfalls(
    md_paths: list[str], repo_root: str | Path
) -> list[DiagnosticEvent]:
    """Flag markdown patterns Pandoc converts to LaTeX ``\\mid`` in text mode.

    Pandoc transforms two prose patterns into the math macro ``\\mid``:

    * Bare ``|word|`` outside math/code (e.g. figure captions, alt-text).
    * Escaped ``\\|`` inside table cells (the only way to put a literal
      pipe in a Markdown table).

    When the rendered context is text mode, ``\\mid`` resolves through the
    text font (lmroman) which lacks U+2223 and produces visible
    ``Missing character`` warnings plus ``U+FFFD`` glyphs in the PDF.
    Wrapping the offending span in inline math (``$|word|$`` or
    ``$\\mid$``) routes the macro through the math font where it renders
    correctly.

    Args:
        md_paths: Markdown source files to scan.
        repo_root: Repository root for relative-path display.

    Returns:
        DiagnosticEvents (severity WARNING) for each occurrence.
    """
    repo_root_path = Path(repo_root)
    problems: list[DiagnosticEvent] = []

    for path in md_paths:
        path_obj = Path(path)
        if path_obj.name in NON_RENDERED_MANUSCRIPT_FILES:
            continue
        text = path_obj.read_text(encoding="utf-8")
        try:
            rel: str | Path = path_obj.relative_to(repo_root_path)
        except ValueError:
            rel = path_obj
        rel_str = str(rel)

        prose = _strip_code_and_math(text)
        for m in PANDOC_BARE_PIPE_PATTERN.finditer(prose):
            problems.append(
                DiagnosticEvent(
                    severity=DiagnosticSeverity.WARNING,
                    category="MARKDOWN_PANDOC_MID",
                    message=(
                        f"Bare pipe pattern '|{m.group(1)}|' in prose will be "
                        f"converted by Pandoc to '\\mid {m.group(1)}\\mid{{}}', "
                        "which fails to render U+2223 in text mode."
                    ),
                    code=MarkdownCode.PANDOC_BARE_PIPE,
                    file_path=rel_str,
                    fix_suggestion=(
                        f"Wrap the span in inline math (e.g. '$|{m.group(1)}|$' "
                        f"or '${{|}}{m.group(1)}{{|}}$') so the macro renders "
                        "through the math font."
                    ),
                )
            )

        for line_no, line in enumerate(text.splitlines(), 1):
            stripped = line.lstrip()
            if not stripped.startswith("|"):
                continue
            # Strip inline math regions (where ``\|`` is the norm operator,
            # not a Pandoc-converted pipe) before scanning.
            line_no_math = re.sub(r"(?<!\$)\$(?!\$)([^$\n]+?)(?<!\$)\$(?!\$)", "", line)
            line_no_math = re.sub(r"`[^`]+`", "", line_no_math)
            if not PANDOC_TABLE_ESCAPED_PIPE_PATTERN.search(line_no_math):
                continue
            problems.append(
                DiagnosticEvent(
                    severity=DiagnosticSeverity.WARNING,
                    category="MARKDOWN_PANDOC_MID",
                    message=(
                        f"Escaped pipe '\\|' in table cell (line {line_no}) "
                        "is rendered by Pandoc as '\\mid', which fails to "
                        "render U+2223 in text mode."
                    ),
                    code=MarkdownCode.PANDOC_TABLE_ESCAPED_PIPE,
                    file_path=rel_str,
                    fix_suggestion=(
                        "Replace the cell content with inline math, e.g. "
                        "'$P(\\text{A} \\mid \\text{B})$'."
                    ),
                )
            )
    return problems


def validate_citations(
    md_paths: list[str], repo_root: str | Path, bib_file: str | Path | None = None
) -> list[DiagnosticEvent]:
    """Verify every ``[@key]`` citation resolves in the project's BibTeX file.

    Scans markdown for Pandoc-style citation tokens (``@key`` outside code
    or math contexts) and reports any keys not present in the supplied
    ``references.bib``. Mirrors the natbib *Citation `key' undefined*
    warning that would otherwise surface only after a full LaTeX render.

    Args:
        md_paths: Markdown source files to scan.
        repo_root: Repository root for relative-path display.
        bib_file: Path to ``references.bib``. When ``None``, look for
            ``references.bib`` next to the first markdown file.

    Returns:
        DiagnosticEvents (severity ERROR) for each unresolved citation key.
    """
    repo_root_path = Path(repo_root)
    problems: list[DiagnosticEvent] = []
    if not md_paths:
        return problems

    if bib_file is None:
        bib_candidate = Path(md_paths[0]).parent / "references.bib"
        bib_path = bib_candidate if bib_candidate.exists() else None
    else:
        bib_path = Path(bib_file)
        if not bib_path.exists():
            bib_path = None

    if bib_path is None:
        return problems

    try:
        bib_text = bib_path.read_text(encoding="utf-8", errors="ignore")
    except OSError as e:
        logger.warning(f"Failed to read BibTeX file {bib_path}: {e}")
        return problems

    known_keys = {k.strip() for k in BIBTEX_KEY_PATTERN.findall(bib_text)}

    for path in md_paths:
        path_obj = Path(path)
        if path_obj.name in NON_RENDERED_MANUSCRIPT_FILES:
            continue
        text = path_obj.read_text(encoding="utf-8")
        try:
            rel: str | Path = path_obj.relative_to(repo_root_path)
        except ValueError:
            rel = path_obj
        rel_str = str(rel)

        prose = _strip_code_and_math(text)
        seen_in_file: set[str] = set()
        for m in CITE_KEY_PATTERN.finditer(prose):
            key = m.group(1)
            if key in known_keys or key in seen_in_file:
                continue
            seen_in_file.add(key)
            problems.append(
                DiagnosticEvent(
                    severity=DiagnosticSeverity.ERROR,
                    category="MARKDOWN_CITATION",
                    message=f"Undefined citation key '@{key}' (not in {bib_path.name})",
                    code=BibtexCode.UNDEFINED_KEY,
                    file_path=rel_str,
                    fix_suggestion=(
                        f"Add an entry '@type{{{key}, ...}}' to {bib_path.name} or "
                        "correct the citation key in the markdown."
                    ),
                )
            )
    return problems


def validate_markdown(
    markdown_dir: str | Path, repo_root: str | Path, strict: bool = False
) -> tuple[list[DiagnosticEvent], int]:
    """Validate all markdown files in a directory.

    This is the main validation function that runs all checks.

    Args:
        markdown_dir: Directory containing markdown files to validate
        repo_root: Root directory of the repository
        strict: If True, fail on any issues; if False, warn only

    Returns:
        Tuple of (problems list, exit_code)
        - problems: List of DiagnosticEvents
        - exit_code: 0 for success or when strict=False; 1 only when strict=True and issues found

    Raises:
        FileNotFoundError: If markdown_dir doesn't exist
    """
    markdown_dir = Path(markdown_dir)
    repo_root = Path(repo_root)

    if not markdown_dir.exists():
        raise FileNotFoundError(f"Markdown directory not found: {markdown_dir}")

    md_paths = find_markdown_files(markdown_dir)
    if not md_paths:
        return ([], 0)

    labels, anchors = collect_symbols(md_paths)

    problems: list[DiagnosticEvent] = []
    problems += validate_images(md_paths, repo_root)
    problems += validate_refs(md_paths, repo_root, labels, anchors)
    problems += validate_math(md_paths, repo_root)
    problems += validate_pandoc_pitfalls(md_paths, repo_root)
    problems += validate_citations(md_paths, repo_root)

    if problems:
        # Currently treating WARNING severity as failing if strict is True.
        # But if we want only ERROR to fail, we can filter.
        has_errors = any(p.severity == DiagnosticSeverity.ERROR for p in problems)
        exit_code = 1 if (strict and has_errors) else 0
        return (problems, exit_code)
    else:
        return ([], 0)


def find_manuscript_directory(repo_root: str | Path, project_name: str = "project") -> Path:
    """Find the manuscript directory at the standard location.

    Args:
        repo_root: Root directory of the repository
        project_name: Name of the project (default: "project")

    Returns:
        Path to the manuscript directory at projects/{project_name}/manuscript/

    Raises:
        FileNotFoundError: If manuscript directory cannot be found at projects/{project_name}/manuscript/
    """
    repo_root = Path(repo_root)

    manuscript_dir = repo_root / "projects" / project_name / "manuscript"

    if manuscript_dir.exists() and manuscript_dir.is_dir():
        return manuscript_dir

    raise FileNotFoundError(
        f"Manuscript directory not found at expected location: {manuscript_dir}"
    )
