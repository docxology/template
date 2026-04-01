"""Combined manuscript rendering helpers.

Extracted from ``PDFRenderer.render_combined()`` to reduce class size.
Each function handles one discrete preprocessing or injection step.
"""

from __future__ import annotations

import os
import re
import subprocess
import unicodedata
import yaml
from pathlib import Path
from typing import TYPE_CHECKING, Any, NamedTuple

from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._pdf_latex_helpers import (
    extract_preamble,
    generate_title_page_body,
    generate_title_page_preamble,
)
from infrastructure.rendering._pdf_math_delimiters import fix_math_delimiters
from infrastructure.rendering._pdf_pandoc_engine import build_pandoc_render_error
from infrastructure.rendering._pdf_preflight import check_brace_balance

if TYPE_CHECKING:
    from infrastructure.rendering.config import RenderingConfig

logger = get_logger(__name__)

_MERMAID_RE = re.compile(r"```\s*mermaid\s*\n.*?```", re.DOTALL | re.IGNORECASE)

_FIG_PATH_REPLACEMENTS = [
    ("../../output/figures/", "../figures/"),
    ("../output/figures/", "../figures/"),
    ("output/figures/", "../figures/"),
]


class CombinedMarkdownResult(NamedTuple):
    """Result of preprocess_combined_markdown."""

    content: str
    mermaid_blocks_removed: int
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


def substitute_manuscript_var_placeholders(
    content: str, flat: dict[str, str]
) -> tuple[str, int]:
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
    """Strip Mermaid fences, normalise figure paths, optional ``manuscript_vars.yaml`` substitution.

    If ``manuscript_dir/manuscript_vars.yaml`` exists, ``{{dotted.key}}`` placeholders in the
    combined markdown are replaced with string values from the flattened YAML tree. Special
    keys ``{{maturity.*}}`` and ``{{verify.*}}`` expand to short summaries.

    Returns:
        CombinedMarkdownResult with processed content and counts of removals/fixes/substitutions.
    """
    content, n_mermaid = _MERMAID_RE.subn("", combined_content)
    if n_mermaid:
        logger.info(f"✓ Removed {n_mermaid} Mermaid diagram block(s) from combined markdown")
    else:
        logger.debug("No Mermaid blocks found in combined markdown")

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
                    content, n_vars = substitute_manuscript_var_placeholders(content, flat)
                    if n_vars:
                        logger.info(
                            "✓ Substituted %s manuscript_vars placeholder(s) from %s",
                            n_vars,
                            vars_path.name,
                        )
                else:
                    logger.warning(
                        "manuscript_vars.yaml root must be a mapping; skipping placeholder substitution"
                    )

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


def postprocess_latex(tex_content: str) -> str:
    """Apply lmodern disabling, hidelinks patching, and math delimiter fixes."""
    # Fix lmodern conflict with xelatex
    if "\\usepackage{lmodern}" in tex_content:
        tex_content = tex_content.replace("\\usepackage{lmodern}", "% \\usepackage{lmodern}")
        logger.info("✓ Disabled lmodern package to prevent XeLaTeX font conflicts")

    # Fix hidelinks → colorlinks
    if "hidelinks" in tex_content:
        tex_content = tex_content.replace(
            "hidelinks,",
            "colorlinks=true,linkcolor=red,urlcolor=red,citecolor=red,anchorcolor=red,",
        )
        tex_content = tex_content.replace(
            "  hidelinks,\n",
            "  colorlinks=true,\n  linkcolor=red,\n  urlcolor=red,\n  citecolor=red,\n",
        )
        logger.info("✓ Patched hidelinks → colorlinks=true with red link colours")

    # Fix broken math delimiters
    try:
        tex_content = fix_math_delimiters(tex_content)
    except (re.error, TypeError, ValueError) as e:
        logger.warning(f"Math delimiter fixing failed: {e}. Continuing with original LaTeX content.")
        logger.debug(f"Math delimiter fixing error details: {type(e).__name__}: {e}")

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

    begin_doc_idx = tex_content.find("\\begin{document}")

    # Inject package declarations and title-page preamble before \begin{document}
    if (preamble_content or title_page_preamble) and begin_doc_idx > 0:
        combined_preamble = ""
        if title_page_preamble:
            combined_preamble += "\n".join(title_page_preamble.split("\n")) + "\n\n"
        if preamble_content:
            combined_preamble += preamble_content + "\n\n"
        tex_content = (
            tex_content[:begin_doc_idx] + combined_preamble + tex_content[begin_doc_idx:]
        )
        begin_doc_idx += len(combined_preamble)
        logger.debug(
            f"✓ Inserted preamble ({len(combined_preamble)} chars) before \\begin{{document}}"
        )

    # Insert title page body after \begin{document}
    if not title_page_body or begin_doc_idx <= 0:
        return tex_content

    full_title_body = title_page_body + "\n\\tableofcontents\n\\newpage"
    tex_preamble = tex_content[:begin_doc_idx]
    tex_body = tex_content[begin_doc_idx:]

    if "\\maketitle" in tex_body:
        logger.debug(
            "✓ \\maketitle already present in LaTeX body - replacing with our full title/TOC body"
        )
        tex_body = tex_body.replace("\\maketitle", full_title_body, 1)
    else:
        end_of_begin_doc = tex_body.find("\n") + 1
        if end_of_begin_doc > 0:
            tex_body = (
                tex_body[:end_of_begin_doc]
                + "\n"
                + full_title_body
                + "\n\n"
                + tex_body[end_of_begin_doc:]
            )
        logger.info(
            r"✓ Inserted title page (\maketitle), TOC, and newpage after \begin{document}"
        )

    return tex_preamble + tex_body


def inject_bibliography(tex_content: str, bib_exists: bool) -> str:
    """Ensure bibliography starts on a new page; insert \\bibliography if missing."""
    bib_marker = "\\bibliography{"
    if bib_exists and bib_marker in tex_content:
        idx = tex_content.find(bib_marker)
        before = tex_content[max(0, idx - 80) : idx]
        if "\\clearpage" not in before:
            tex_content = tex_content[:idx] + "\\clearpage\n\n" + tex_content[idx:]
            logger.info("✓ Inserted \\clearpage before \\bibliography{...}")
        return tex_content
    if bib_exists and bib_marker not in tex_content:
        end_doc_idx = tex_content.rfind("\\end{document}")
        if end_doc_idx > 0:
            tex_content = (
                tex_content[:end_doc_idx]
                + "\n\n\\clearpage\n\n\\bibliography{references}\n"
                + tex_content[end_doc_idx:]
            )
            logger.info(
                "✓ Inserted \\clearpage and \\bibliography{references} before \\end{document}"
            )
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

    for fig_ref in referenced_figures:
        filename = fig_ref.split("/")[-1]
        fig_path = figures_dir / filename
        fig_normalized = figures_dir / unicodedata.normalize("NFC", filename)

        if fig_path.exists():
            found_figures.append(filename)
            logger.debug(f"  ✓ Found: {filename}")
        elif fig_normalized.exists():
            found_figures.append(filename)
            logger.debug(f"  ✓ Found (normalized): {filename}")
        else:
            missing_figures.append(filename)
            logger.warning(f"  ✗ Missing: {filename}")
            if figures_dir.exists():
                similar = [
                    f.name
                    for f in figures_dir.iterdir()
                    if f.name.lower().startswith(filename.split(".")[0].lower())
                ]
                if similar:
                    logger.debug(f"    Similar files found: {', '.join(similar)}")

    logger.info(f"  Found: {len(found_figures)}/{len(referenced_figures)} figures")
    if missing_figures:
        logger.warning(
            f"  Missing {len(missing_figures)} figure(s): {', '.join(missing_figures[:5])}"
        )
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
                logger.warning(
                    f"Pre-validation found {len(validation_errors)} potential issue(s):"
                )
                for err in validation_errors:
                    logger.warning(f"  • {err}")
                logger.info("  (These are warnings - PDF generation will proceed)")
        except (OSError, UnicodeDecodeError) as e:  # noqa: BLE001
            logger.debug(f"Pre-validation check failed: {e}")
    return validation_errors, md_content
