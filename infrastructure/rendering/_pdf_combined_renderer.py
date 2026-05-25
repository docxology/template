"""Combined manuscript rendering helpers.

Extracted from ``PDFRenderer.render_combined()`` to reduce class size.
Each function handles one discrete preprocessing or injection step.
"""

from __future__ import annotations


import os
import re
import shutil
import subprocess
import unicodedata
import yaml
from pathlib import Path
from typing import TYPE_CHECKING, Any, NamedTuple

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging import DiagnosticSeverity
from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._pdf_latex_helpers import (
    extract_preamble,
    generate_title_page_body,
    generate_title_page_preamble,
)
from infrastructure.rendering._pdf_math_delimiters import fix_math_delimiters
from infrastructure.rendering._pdf_mermaid import replace_inline_mermaid
from infrastructure.rendering._pdf_pandoc_engine import build_pandoc_render_error
from infrastructure.rendering._pdf_preflight import check_brace_balance
from infrastructure.rendering._pdf_section_titles import sanitize_texorpdfstring
from infrastructure.rendering._pdf_unicode_remap import remap_prose_unicode
from infrastructure.rendering.latex_texttt import (
    constrain_includegraphics_textheight,
    make_known_literals_breakable,
    make_long_texttt_breakable,
)
from infrastructure.validation.content.discovery import discover_markdown_files
from infrastructure.validation.content.markdown_validator import (
    validate_citations,
    validate_pandoc_pitfalls,
)

if TYPE_CHECKING:
    from infrastructure.rendering.config import RenderingConfig

logger = get_logger(__name__)

_FIG_PATH_REPLACEMENTS = [
    ("../../output/figures/", "../figures/"),
    ("../output/figures/", "../figures/"),
    ("output/figures/", "../figures/"),
]


class CombinedMarkdownResult(NamedTuple):
    """Result of preprocess_combined_markdown."""

    content: str
    mermaid_blocks_processed: int
    fig_paths_fixed: int
    manuscript_vars_substitutions: int


_PLACEHOLDER_RE = re.compile(r"\{\{([^}]+)\}\}")


def flatten_manuscript_vars(data: Any, prefix: str = "") -> dict[str, str]:
    """Flatten nested YAML mapping to dotted keys with string values (for {{key}} substitution)."""
    flat: dict[str, str] = {}
    if isinstance(data, dict):
        for k, v in data.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            if isinstance(v, dict):
                flat.update(flatten_manuscript_vars(v, key))
            elif isinstance(v, list):
                flat[key] = ", ".join(str(x) for x in v)
            elif isinstance(v, bool):
                flat[key] = str(v).lower()
            elif v is None:
                flat[key] = ""
            else:
                flat[key] = str(v)
    return flat


def substitute_manuscript_var_placeholders(content: str, flat: dict[str, str]) -> tuple[str, int]:
    """Replace ``{{name}}`` placeholders using flattened manuscript_vars.

    Handles ``{{maturity.*}}`` and ``{{verify.*}}`` summaries. Unknown keys are left unchanged.
    """
    maturity_summary = (
        f"{flat.get('maturity.real', '?')} real, "
        f"{flat.get('maturity.partial', '?')} partial, "
        f"{flat.get('maturity.aspirational', '?')} aspirational"
    )
    verify_parts = [f"{k}={flat[k]}" for k in sorted(flat) if k.startswith("verify.")]
    verify_summary = "; ".join(verify_parts) if verify_parts else "(no verify metrics in manuscript_vars)"

    n_subs = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal n_subs
        key = match.group(1).strip()
        if key == "maturity.*":
            n_subs += 1
            return maturity_summary
        if key == "verify.*":
            n_subs += 1
            return verify_summary
        if key in flat:
            n_subs += 1
            return flat[key]
        return match.group(0)

    out = _PLACEHOLDER_RE.sub(repl, content)
    return out, n_subs


def preprocess_combined_markdown(
    combined_content: str,
    manuscript_dir: Path | None = None,
) -> CombinedMarkdownResult:
    """Render Mermaid fences, normalise figure paths, and substitute variables.

    If ``manuscript_dir/manuscript_vars.yaml`` exists, ``{{dotted.key}}`` placeholders in the
    combined markdown are replaced with string values from the flattened YAML tree. Special
    keys ``{{maturity.*}}`` and ``{{verify.*}}`` expand to short summaries.

    Returns:
        CombinedMarkdownResult with processed content and counts of Mermaid renders,
        figure path fixes, and variable substitutions.
    """
    mermaid_result = replace_inline_mermaid(combined_content, manuscript_dir)
    content = mermaid_result.content
    n_mermaid = mermaid_result.diagrams_rendered
    if n_mermaid:
        logger.info(f"✓ Rendered {n_mermaid} Mermaid diagram block(s) into combined markdown")
    else:
        logger.debug("No Mermaid blocks rendered in combined markdown")

    n_fig_paths = 0
    for old_prefix, new_prefix in _FIG_PATH_REPLACEMENTS:
        count = content.count(old_prefix)
        if count:
            content = content.replace(old_prefix, new_prefix)
            n_fig_paths += count
    if n_fig_paths:
        logger.info(f"✓ Normalised {n_fig_paths} figure path(s) to ../figures/ in combined markdown")

    n_vars = 0
    if manuscript_dir is not None:
        vars_path = manuscript_dir / "manuscript_vars.yaml"
        if vars_path.is_file():
            try:
                raw = yaml.safe_load(vars_path.read_text(encoding="utf-8"))
            except (OSError, yaml.YAMLError) as e:
                logger.warning("Could not load manuscript_vars.yaml for placeholder substitution: %s", e)
            else:
                if raw is None:
                    raw = {}
                if isinstance(raw, dict):
                    flat = flatten_manuscript_vars(raw)

                    # Augment with synthetic variables if present
                    if isinstance(raw.get("topics"), dict):
                        topics_dict = raw["topics"]
                        flat["total_topics"] = str(len(topics_dict))
                        # Build synthetic topic data dynamically
                        for topic_id, topic_data in topics_dict.items():
                            if isinstance(topic_data, dict):
                                # lean_chars derived from lean_sketch
                                sketch = topic_data.get("lean_sketch", "")
                                flat[f"topics.{topic_id}.lean_chars"] = str(len(sketch))

                                # Update maturity display string and icon based on mathlib_status
                                ml_status = topic_data.get("mathlib_status", "")
                                if ml_status == "real":
                                    flat[f"topics.{topic_id}.maturity"] = "real"
                                    flat[f"topics.{topic_id}.maturity_icon"] = "✅"
                                elif ml_status == "partial":
                                    flat[f"topics.{topic_id}.maturity"] = "partial"
                                    flat[f"topics.{topic_id}.maturity_icon"] = "🔶"
                                elif ml_status == "aspirational":
                                    flat[f"topics.{topic_id}.maturity"] = "aspirational"
                                    flat[f"topics.{topic_id}.maturity_icon"] = "🔷"

                    if isinstance(raw.get("areas"), dict):
                        areas_dict = raw["areas"]
                        flat["total_areas"] = str(len(areas_dict))
                        # Alias areas.X -> areas.X.count for legacy scalar
                        # shapes only. Nested {count: N} entries are already
                        # flattened to areas.X.count by flatten_manuscript_vars;
                        # overwriting with str(dict) would emit "{'count': N}".
                        for area_name, area_value in areas_dict.items():
                            if isinstance(area_value, dict):
                                continue
                            flat[f"areas.{area_name}.count"] = str(area_value)

                    content, n_vars = substitute_manuscript_var_placeholders(content, flat)
                    if n_vars:
                        logger.info(
                            "✓ Substituted %s manuscript_vars placeholder(s) from %s",
                            n_vars,
                            vars_path.name,
                        )
                else:
                    logger.warning("manuscript_vars.yaml root must be a mapping; skipping placeholder substitution")

    return CombinedMarkdownResult(content, n_mermaid, n_fig_paths, n_vars)


def build_pandoc_tex_command(
    config: "RenderingConfig",
    combined_md: Path,
    combined_tex: Path,
    manuscript_dir: Path,
) -> list[str]:
    """Build the Pandoc CLI command for markdown→LaTeX conversion."""
    figures_dir = Path(config.figures_dir)
    cmd = [
        config.pandoc_path,
        str(combined_md),
        "-o",
        str(combined_tex),
        "--from=markdown+tex_math_dollars+raw_tex+header_attributes",
        "--to=latex",
        "--standalone",
        "--number-sections",
        "--natbib",
        "--resource-path=" + str(manuscript_dir),
        "--resource-path=" + str(figures_dir),
    ]

    # Attempt to extract geometry from config.yaml and pass to pandoc
    config_file = manuscript_dir / "config.yaml"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f)

            if yaml_data and isinstance(yaml_data, dict):
                metadata = yaml_data.get("metadata", {})
                geometry = metadata.get("geometry")
                if geometry:
                    cmd.extend(["-V", f"geometry:{geometry}"])
                    logger.debug(f"Added geometry to pandoc args: {geometry}")
        except (OSError, yaml.YAMLError) as e:
            logger.warning(f"Failed to read geometry from config.yaml: {e}")

    crossref = shutil.which("pandoc-crossref")
    if crossref:
        cmd.extend(["--filter", crossref])
        logger.info("Using pandoc-crossref at %s", crossref)
    else:
        logger.warning(
            "pandoc-crossref not on PATH; @sec:/@tbl:/@fig:/@eq: will not resolve. "
            "Install: https://github.com/lierdakil/pandoc-crossref (e.g. brew install pandoc-crossref)"
        )

    return cmd


def run_pandoc_conversion(
    cmd: list[str],
    combined_md: Path,
    source_files: list[Path],
    md_content: str,
) -> None:
    """Execute the Pandoc subprocess, raising on failure."""
    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=(8 if os.environ.get("PYTEST_CURRENT_TEST") else 600),
        )
    except subprocess.CalledProcessError as e:
        raise build_pandoc_render_error(e, combined_md, source_files, md_content, cmd) from e


def _escape_latex_def_value(value: str) -> str:
    """Escape a section title for use inside ``\\def\\@currentlabelname{...}``."""
    escaped = value.replace("\\", "\\textbackslash{}")
    return escaped.replace("{", "\\{").replace("}", "\\}")


_STARRED_HEADING_MARKERS: tuple[str, ...] = (
    "\\section*{",
    "\\subsection*{",
    "\\subsubsection*{",
)


def _next_starred_heading(tex_content: str, start: int) -> tuple[int, str] | None:
    """Return the earliest starred heading marker at or after ``start``."""
    best_at = -1
    best_marker = ""
    for marker in _STARRED_HEADING_MARKERS:
        at = tex_content.find(marker, start)
        if at >= 0 and (best_at < 0 or at < best_at):
            best_at = at
            best_marker = marker
    if best_at < 0:
        return None
    return best_at, best_marker


def fix_starred_section_nameref_labels(tex_content: str) -> tuple[str, int]:
    """Repair hyperref anchors and ``\\nameref`` titles for starred headings.

    Pandoc emits ``\\section*{Title}\\label{...}\\addcontentsline{...}`` without
    ``\\phantomsection``, so TOC links resolve to ``Doc-Start`` while page numbers
    stay correct. titlesec additionally prevents hyperref from storing section titles,
    which leaves ``\\nameref{sec:...}`` empty unless ``\\@currentlabelname`` is set.
    """
    has_titlesec = bool(re.search(r"\\usepackage(?:\[[^\]]*\])?\{titlesec\}", tex_content))
    has_hyperref = bool(re.search(r"\\usepackage(?:\[[^\]]*\])?\{hyperref\}", tex_content))
    if not has_titlesec and not has_hyperref:
        return tex_content, 0

    out: list[str] = []
    i = 0
    fixes = 0

    while True:
        found = _next_starred_heading(tex_content, i)
        if found is None:
            out.append(tex_content[i:])
            break

        start, marker = found
        out.append(tex_content[i:start])
        j = start + len(marker)
        depth = 1
        title_start = j
        while j < len(tex_content) and depth > 0:
            ch = tex_content[j]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
            j += 1

        if depth != 0:
            out.append(tex_content[start:])
            break

        title_raw = tex_content[title_start : j - 1]
        rest = tex_content[j:]
        rest_lstrip = rest.lstrip()
        if rest_lstrip.startswith("\\phantomsection"):
            out.append(tex_content[start:j])
            i = j
            continue

        label_match = re.match(r"\\label\{([^}]+)\}", rest_lstrip)
        if label_match is None:
            out.append(tex_content[start:j])
            i = j
            continue

        label = label_match.group(1)
        consumed = len(rest) - len(rest_lstrip) + label_match.end()
        heading_open = marker
        repaired = f"{heading_open}{title_raw}}}\n"
        if has_titlesec:
            title_plain = re.sub(r"\s+", " ", title_raw).strip()
            title_escaped = _escape_latex_def_value(title_plain)
            repaired += f"\\makeatletter\n\\def\\@currentlabelname{{{title_escaped}}}\n\\makeatother\n"
        repaired += f"\\phantomsection\\label{{{label}}}"
        out.append(repaired)
        fixes += 1
        i = j + consumed

    if fixes:
        logger.info(
            "✓ Repaired %d starred heading label(s) for hyperref TOC anchors and \\nameref",
            fixes,
        )
    return "".join(out), fixes


def postprocess_latex(tex_content: str) -> str:
    """Apply lmodern disabling, hidelinks patching, and math delimiter fixes."""
    # Fix lmodern conflict with xelatex
    if "\\usepackage{lmodern}" in tex_content:
        tex_content = tex_content.replace("\\usepackage{lmodern}", "% \\usepackage{lmodern}")
        logger.info("✓ Disabled lmodern package to prevent XeLaTeX font conflicts")

    # Defensive rewrite: a user preamble that re-loads hyperref with options
    # collides with Pandoc's template (which already loads hyperref via the
    # bookmark package). Convert ``\usepackage[opts]{hyperref}`` into
    # ``\PassOptionsToPackage{opts}{hyperref}`` + ``\hypersetup{opts}`` so the
    # options are honoured without triggering ``Option clash for package
    # hyperref``. Only rewrites the option-bearing form; ``\usepackage{hyperref}``
    # without options is left alone (no clash).
    hyperref_pattern = re.compile(r"\\usepackage\[(?P<opts>[^\]]*)\]\{hyperref\}")
    rewritten_count = 0

    def _rewrite_hyperref(match: "re.Match[str]") -> str:
        nonlocal rewritten_count
        rewritten_count += 1
        opts = match.group("opts").strip()
        return f"\\PassOptionsToPackage{{{opts}}}{{hyperref}}\n\\AtBeginDocument{{\\hypersetup{{{opts}}}}}"

    tex_content, _subs = hyperref_pattern.subn(_rewrite_hyperref, tex_content)
    if rewritten_count:
        logger.info(
            "✓ Rewrote %d duplicate \\usepackage[...]{hyperref} into "
            "\\PassOptionsToPackage + \\hypersetup (avoids hyperref option clash)",
            rewritten_count,
        )

    # Fix hidelinks → colorlinks=true with uniform red hyperlinks.
    if "hidelinks" in tex_content:
        tex_content = tex_content.replace(
            "hidelinks,",
            "colorlinks=true,linkcolor=red,urlcolor=red,citecolor=red,anchorcolor=red,filecolor=red,",
        )
        tex_content = tex_content.replace(
            "  hidelinks,\n",
            "  colorlinks=true,\n  linkcolor=red,\n  urlcolor=red,\n  citecolor=red,\n",
        )
        logger.info("✓ Patched hidelinks → colorlinks=true (uniform red hyperlinks)")

    # Normalise pandoc's default hypersetup colours to uniform red. Pandoc
    # emits something like:
    #   \hypersetup{
    #     colorlinks=true,linkcolor=red,urlcolor=blue,citecolor=red,anchorcolor=red,
    #     pdfcreator={LaTeX via pandoc}}
    # Force every link colour to red so cross-refs, citations, and URLs
    # share one visual treatment. Only rewrites blocks that already declare
    # at least one link-colour key so we don't perturb unrelated metadata-
    # only hypersetup blocks (e.g. ``\hypersetup{pdftitle={...}}``).
    def _find_hypersetup_blocks(s: str) -> list[tuple[int, int, str]]:
        """Return (start, end, body) for each balanced \\hypersetup{...}."""
        out: list[tuple[int, int, str]] = []
        marker = "\\hypersetup{"
        i = 0
        while True:
            idx = s.find(marker, i)
            if idx < 0:
                return out
            body_start = idx + len(marker)
            depth = 1
            j = body_start
            while j < len(s) and depth > 0:
                ch = s[j]
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                j += 1
            if depth == 0:
                out.append((idx, j, s[body_start : j - 1]))
                i = j
            else:
                return out

    blocks = _find_hypersetup_blocks(tex_content)
    color_keys = ("linkcolor", "urlcolor", "citecolor", "anchorcolor", "filecolor")
    hs_count = 0
    for start, end, body in reversed(blocks):
        if not any(re.search(rf"\b{k}\s*=", body) for k in color_keys):
            continue  # metadata-only hypersetup, skip
        new_body = body
        for key in color_keys:
            new_body = re.sub(rf"\b{key}\s*=\s*[A-Za-z][A-Za-z0-9]*", f"{key}=red", new_body)
        tex_content = tex_content[:start] + "\\hypersetup{" + new_body + "}" + tex_content[end:]
        hs_count += 1
    if hs_count:
        logger.info("✓ Normalised %d \\hypersetup block(s) to uniform red link colours", hs_count)

    # Fix broken math delimiters
    try:
        tex_content = fix_math_delimiters(tex_content)
    except (re.error, TypeError, ValueError) as e:
        logger.warning(f"Math delimiter fixing failed: {e}. Continuing with original LaTeX content.")
        logger.debug(f"Math delimiter fixing error details: {type(e).__name__}: {e}")

    # Sanitize Pandoc's auto-emitted \texorpdfstring bookmark arguments.
    # When section titles contain math, Pandoc fills the bookmark arg with
    # \textbackslash / \_ / {[} etc. that hyperref then tries to expand
    # during the pdfstring serialize, which can blow the input stack
    # ("TeX capacity exceeded, sorry [input stack size=10000]") on heavy
    # math-laden headings and abort the build mid-section.
    try:
        tex_content, _ = sanitize_texorpdfstring(tex_content)
    except (re.error, TypeError, ValueError) as e:
        logger.warning(f"texorpdfstring sanitization failed: {e}. Continuing with original LaTeX content.")

    # Remap unicode glyphs (✓, ≈, α, σ, ≪, …) that the active body/code
    # fonts cannot render. Literal verbatim blocks are preserved; Pandoc
    # Highlighting blocks receive an ASCII-safe code rewrite because their
    # macro arguments are typeset through normal text fonts.
    try:
        tex_content = remap_prose_unicode(tex_content).content
    except (re.error, TypeError, ValueError) as e:
        logger.warning(f"Prose unicode remap failed: {e}. Continuing with original LaTeX content.")

    try:
        tex_content, texttt_replacements = make_long_texttt_breakable(tex_content)
        if texttt_replacements:
            logger.info("✓ Made %d long monospace path span(s) breakable", texttt_replacements)
        tex_content, literal_replacements = make_known_literals_breakable(tex_content)
        if literal_replacements:
            logger.info("✓ Made %d recurring long label(s) breakable", literal_replacements)
    except (re.error, TypeError, ValueError) as e:
        logger.warning(f"Breakable texttt postprocessing failed: {e}. Continuing with original LaTeX content.")

    tex_content, graphics_replacements = constrain_includegraphics_textheight(tex_content, "0.50")
    if graphics_replacements:
        logger.info("✓ Constrained %d Pandoc figure height bound(s)", graphics_replacements)

    return tex_content


def inject_latex_preamble(
    tex_content: str,
    manuscript_dir: Path,
) -> str:
    """Extract preamble from preamble.md and config.yaml, inject before \\begin{document}."""
    preamble_file = manuscript_dir / "preamble.md"
    preamble_content = ""
    if preamble_file.exists():
        preamble_content = extract_preamble(preamble_file)
        if preamble_content:
            logger.info(f"✓ Extracted preamble from {preamble_file.name}")
        else:
            logger.warning("⚠️  Preamble file found but no LaTeX content extracted")
    else:
        logger.debug(f"No preamble file found at {preamble_file}")

    title_page_preamble = generate_title_page_preamble(manuscript_dir)
    title_page_body = generate_title_page_body(manuscript_dir)

    # Ensure graphicx package is always included
    graphicx_required = r"\usepackage{graphicx}"
    if preamble_content and graphicx_required not in preamble_content:
        logger.info("⚠️  graphicx package not found in preamble, adding it")
        preamble_content = graphicx_required + "\n" + preamble_content
    elif not preamble_content:
        logger.info("⚠️  No preamble found, adding graphicx package")
        preamble_content = graphicx_required

    # Ensure geometry package is present so margins are configurable in one
    # place. Default to 0.75in margins (~half of the 1.5in article default)
    # for a denser, more contemporary page that still leaves room for the
    # title/TOC. Skip injection if a manuscript-supplied or pandoc-emitted
    # geometry declaration is already present in either the user preamble
    # or the assembled TeX preamble (the portion before ``\begin{document}``).
    geometry_pkg_re = re.compile(r"\\usepackage(?:\[[^\]]*\])?\{geometry\}")
    geometry_cmd_re = re.compile(r"\\geometry\s*\{")
    tex_preamble_only = tex_content.split("\\begin{document}", 1)[0]
    has_geometry_in_user_preamble = bool(geometry_pkg_re.search(preamble_content))
    has_geometry_in_tex_preamble = bool(
        geometry_pkg_re.search(tex_preamble_only) or geometry_cmd_re.search(tex_preamble_only)
    )
    if has_geometry_in_user_preamble or has_geometry_in_tex_preamble:
        logger.debug("geometry already declared; not re-injecting")
    else:
        geometry_line = r"\usepackage[margin=0.75in]{geometry}"
        preamble_content = geometry_line + "\n" + preamble_content
        logger.info("✓ Injected geometry package (0.75in margins)")

    begin_doc_idx = tex_content.find("\\begin{document}")

    # Inject package declarations and title-page preamble before \begin{document}
    if (preamble_content or title_page_preamble) and begin_doc_idx > 0:
        combined_preamble = ""
        if title_page_preamble:
            combined_preamble += "\n".join(title_page_preamble.split("\n")) + "\n\n"
        if preamble_content:
            combined_preamble += preamble_content + "\n\n"
        tex_content = tex_content[:begin_doc_idx] + combined_preamble + tex_content[begin_doc_idx:]
        begin_doc_idx += len(combined_preamble)
        logger.debug(f"✓ Inserted preamble ({len(combined_preamble)} chars) before \\begin{{document}}")

    # Insert title page body after \begin{document}
    if not title_page_body or begin_doc_idx <= 0:
        return tex_content

    if "\\tableofcontents" in title_page_body:
        full_title_body = title_page_body
    else:
        full_title_body = title_page_body + "\n\\tableofcontents\n\\newpage"
    tex_preamble = tex_content[:begin_doc_idx]
    tex_body = tex_content[begin_doc_idx:]

    if "\\maketitle" in tex_body:
        logger.debug("✓ \\maketitle already present in LaTeX body - replacing with our full title/TOC body")
        tex_body = tex_body.replace("\\maketitle", full_title_body, 1)
    else:
        end_of_begin_doc = tex_body.find("\n") + 1
        if end_of_begin_doc > 0:
            tex_body = tex_body[:end_of_begin_doc] + "\n" + full_title_body + "\n\n" + tex_body[end_of_begin_doc:]
        logger.info(r"✓ Inserted title/opening matter after \begin{document}")

    return tex_preamble + tex_body


def discover_manuscript_bib_paths(manuscript_dir: Path) -> list[Path]:
    """Return sorted ``*.bib`` paths beside the manuscript (multi-database projects)."""
    return sorted(manuscript_dir.glob("*.bib"))


def inject_bibliography(tex_content: str, bib_exists: bool, bib_stems: str = "references") -> str:
    """Ensure bibliography starts on a new page; set ``\\bibliography{stems}``.

    ``bib_stems`` is a comma-separated list of database names without ``.bib``
    (e.g. ``references`` or ``references,references_deep``).
    """
    bib_marker = "\\bibliography{"
    if not bib_exists:
        return tex_content

    replacement = r"\bibliography{" + bib_stems + "}"
    if bib_marker in tex_content:
        tex_content = re.sub(
            r"\\bibliography\{[^}]*\}",
            lambda _m: replacement,
            tex_content,
            count=1,
        )
        idx = tex_content.find(bib_marker)
        before = tex_content[max(0, idx - 80) : idx]
        if "\\clearpage" not in before:
            tex_content = tex_content[:idx] + "\\clearpage\n\n" + tex_content[idx:]
            logger.info("✓ Inserted \\clearpage before \\bibliography{...}")
        return tex_content

    end_doc_idx = tex_content.rfind("\\end{document}")
    if end_doc_idx > 0:
        tex_content = tex_content[:end_doc_idx] + f"\n\n\\clearpage\n\n{replacement}\n" + tex_content[end_doc_idx:]
        logger.info("✓ Inserted \\clearpage and \\bibliography{...} before \\end{document}")
    else:
        logger.warning("⚠️  Could not find \\end{document} to insert bibliography")
    return tex_content


def verify_figure_references(tex_content: str, figures_dir: Path) -> None:
    """Verify that all \\includegraphics references resolve to existing files."""
    fig_pattern = r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}"
    referenced_figures = re.findall(fig_pattern, tex_content)

    if not referenced_figures:
        return

    logger.info(f"Verifying {len(referenced_figures)} figure reference(s)...")
    missing_figures: list[str] = []
    found_figures: list[str] = []

    def _figure_candidates(fig_ref: str) -> list[Path]:
        ref = fig_ref.strip()
        if ref.startswith(r"\detokenize{"):
            ref = ref.removeprefix(r"\detokenize{").rstrip("}")
        ref_path = Path(ref)
        candidates: list[Path] = []
        if ref_path.is_absolute():
            candidates.append(ref_path)
        parts = ref_path.parts
        if "figures" in parts:
            figure_index = parts.index("figures")
            candidates.append(figures_dir.joinpath(*parts[figure_index + 1 :]))
        candidates.extend([figures_dir / ref_path, figures_dir / ref_path.name])
        return [Path(unicodedata.normalize("NFC", str(candidate))) for candidate in candidates]

    for fig_ref in referenced_figures:
        display_name = fig_ref.split("/")[-1].rstrip("}")
        existing_path = next((candidate for candidate in _figure_candidates(fig_ref) if candidate.exists()), None)

        if existing_path is not None:
            found_figures.append(display_name)
            logger.debug(f"  ✓ Found: {display_name}")
        else:
            missing_figures.append(display_name)
            logger.warning(f"  ✗ Missing: {display_name}")
            if figures_dir.exists():
                similar = [
                    f.name
                    for f in figures_dir.rglob("*")
                    if f.name.lower().startswith(display_name.split(".")[0].lower())
                ]
                if similar:
                    logger.debug(f"    Similar files found: {', '.join(similar)}")

    logger.info(f"  Found: {len(found_figures)}/{len(referenced_figures)} figures")
    if missing_figures:
        logger.warning(f"  Missing {len(missing_figures)} figure(s): {', '.join(missing_figures[:5])}")
        if len(missing_figures) > 5:
            logger.warning(f"  ... and {len(missing_figures) - 5} more missing figures")


def prevalidate_markdown(combined_md: Path) -> tuple[list[str], str]:
    """Pre-validate combined markdown for common issues.

    Returns:
        Tuple of (validation_errors, md_content)
    """
    validation_errors: list[str] = []
    md_content = ""
    if combined_md.exists():
        try:
            md_content = combined_md.read_text(encoding="utf-8")
            validation_errors = check_brace_balance(md_content)
            if validation_errors:
                logger.warning(f"Pre-validation found {len(validation_errors)} potential issue(s):")
                for err in validation_errors:
                    logger.warning(f"  • {err}")
                logger.info("  (These are warnings - PDF generation will proceed)")
        except (OSError, UnicodeDecodeError) as e:  # noqa: BLE001
            logger.debug(f"Pre-validation check failed: {e}")
    return validation_errors, md_content


def prevalidate_source_markdown(
    source: Path | list[Path] | list[str],
    repo_root: Path | None = None,
    bib_file: str | Path | list[str | Path] | None = None,
) -> None:
    """Hard-gate the combined-PDF render on source-markdown integrity.

    Runs the two render-blocking checks against the actual files about to
    be combined and rendered (not the post-Pandoc ``.tex``), so file paths
    in error messages point to the editable sources:

    * :func:`validate_pandoc_pitfalls` — bare ``|word|`` in prose and
      ``\\|`` inside Markdown table cells (Pandoc converts both to
      ``\\mid`` which fails to render U+2223 in text mode).
    * :func:`validate_citations` — every ``[@key]`` resolves in the manuscript
      ``*.bib`` union (or the explicit ``bib_file`` list when supplied).

    Both classes of finding block the render under the strict gate;
    pitfall WARNINGS are promoted to blockers here because they
    materialise downstream as silent ``Missing character`` warnings +
    ``U+FFFD`` glyphs in the rendered PDF — exactly the class of failure
    this gate exists to prevent.

    Args:
        source: Either a manuscript directory (``Path``) — scanned with
            :func:`discover_markdown_files` (``scope='tree'``) — or an explicit iterable of
            markdown file paths.
        repo_root: Repository root for relative-path display in error
            messages. Defaults to a best-effort guess based on the first
            source path.
        bib_file: Explicit BibTeX path(s). ``None`` unions every ``*.bib`` next
            to the first markdown source (same default as combined-PDF render).

    Raises:
        RenderingError: When any pitfall or undefined citation is found.
            The exception message lists every blocker with its file path.
    """
    if isinstance(source, Path):
        if not source.exists():
            return
        paths: list[str] = [str(path) for path in discover_markdown_files(source, scope="tree")]
        anchor_dir = source
    else:
        paths = [str(p) for p in source]
        anchor_dir = Path(paths[0]).parent if paths else Path.cwd()

    if not paths:
        return

    if repo_root is None:
        repo_root = anchor_dir.parents[2] if len(anchor_dir.parents) >= 3 else anchor_dir

    problems = validate_pandoc_pitfalls(paths, repo_root) + validate_citations(paths, repo_root, bib_file=bib_file)
    if not problems:
        return

    # Promote everything to render-blocker under the strict gate.
    blockers = problems
    rendered = "\n".join(f"  [{p.file_path}] {p.message}" for p in blockers)
    by_severity = {
        DiagnosticSeverity.ERROR: sum(1 for p in blockers if p.severity == DiagnosticSeverity.ERROR),
        DiagnosticSeverity.WARNING: sum(1 for p in blockers if p.severity == DiagnosticSeverity.WARNING),
    }
    raise RenderingError(
        f"Pre-render validation failed with {len(blockers)} blocker(s) "
        f"({by_severity[DiagnosticSeverity.ERROR]} error / "
        f"{by_severity[DiagnosticSeverity.WARNING]} warning) before "
        f"Pandoc/xelatex runs:\n{rendered}\n"
        "Fix each occurrence in the listed source markdown file(s) and re-run."
    )
