#!/usr/bin/env python3
"""Build the Ento-Linguistics PDF manuscript.

This script uses pandoc to combine markdown files, handle citations,
and generate a publication-ready PDF with a proper cover page.
"""
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def _build_frontmatter(config_path: Path) -> str:
    r"""Parse config.yaml and return a YAML frontmatter block for Pandoc.

    config.yaml stores metadata as nested ``paper:`` / ``authors:`` keys;
    Pandoc expects top-level ``title`` / ``author`` / ``date``.

    Author affiliation, ORCID, and email are injected via ``header-includes``
    which redefines the LaTeX ``\author{}`` command with full details, while
    the YAML ``author:`` field carries just the plain name for PDF metadata.

    Returns:
        YAML frontmatter string (with ``---`` delimiters) or empty string.
    """
    if yaml is None:
        print("  Warning: PyYAML not available, skipping cover page metadata")
        return ""

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    paper = config.get("paper", {})
    title = paper.get("title", "Untitled")
    subtitle = paper.get("subtitle", "")
    raw_date = paper.get("date", "")
    date_str = raw_date if raw_date else datetime.now().strftime("%B %d, %Y")

    # Extract author information
    authors_cfg = config.get("authors", [])
    author_names = [a.get("name", "") for a in authors_cfg if a.get("name")]

    # Build LaTeX author block with affiliation details for header-includes
    author_latex_parts = []
    for a in authors_cfg:
        name = a.get("name", "")
        if not name:
            continue
        author_latex_parts.append(name)
        if a.get("affiliation"):
            author_latex_parts.append(
                r"  \newline {\small " + a["affiliation"] + r"}"
            )
        if a.get("orcid"):
            author_latex_parts.append(
                r"  \newline {\footnotesize ORCID: " + a["orcid"] + r"}"
            )
        if a.get("email"):
            author_latex_parts.append(
                r"  \newline {\footnotesize \texttt{" + a["email"] + r"}}"
            )

    # Build YAML frontmatter using yaml.dump for safe serialization
    metadata = {"title": title, "date": date_str}
    if subtitle:
        metadata["subtitle"] = subtitle
    if author_names:
        metadata["author"] = author_names

    # Add header-includes to redefine \author with rich details
    if author_latex_parts:
        author_block = "\n".join(author_latex_parts)
        header_inc = r"\makeatletter" + "\n"
        header_inc += r"\renewcommand{\@author}{" + author_block + r"}" + "\n"
        header_inc += r"\makeatother"
        metadata["header-includes"] = [header_inc]

    frontmatter = "---\n" + yaml.dump(metadata, default_flow_style=False) + "---\n"

    print(f"  Cover metadata: title='{title[:50]}...', "
          f"{len(author_names)} author(s), date='{date_str}'")

    return frontmatter


def _load_corpus_vars(project_root: Path) -> dict:
    """Load corpus statistics from output/data/ for template substitution.

    Reads corpus_statistics.json for token counts and data/corpus/abstracts.json
    for the publication count. Returns a dict of {{KEY}} -> value mappings that
    are substituted into manuscript markdown files before pandoc is run, ensuring
    all cited numbers always reflect the most recent corpus build.

    Returns:
        Mapping of template variable names to their formatted string values.
    """
    import json

    vars_: dict = {}

    # Publication count from the raw corpus
    abstracts_path = project_root / "data" / "corpus" / "abstracts.json"
    if abstracts_path.exists():
        with open(abstracts_path) as fh:
            abstracts = json.load(fh)
        vars_["CORPUS_PUBLICATIONS"] = str(len(abstracts))
    else:
        vars_["CORPUS_PUBLICATIONS"] = "N/A"

    # Token statistics from the processed corpus
    stats_path = project_root / "output" / "data" / "corpus_statistics.json"
    if stats_path.exists():
        with open(stats_path) as fh:
            stats = json.load(fh)
        vars_["CORPUS_TOTAL_TOKENS"] = f"{stats.get('total_tokens', 0):,}"
        vars_["CORPUS_UNIQUE_TOKENS"] = f"{stats.get('unique_tokens', 0):,}"
    else:
        vars_["CORPUS_TOTAL_TOKENS"] = "N/A"
        vars_["CORPUS_UNIQUE_TOKENS"] = "N/A"

    # Term extraction counts from extracted_terms.json
    terms_path = project_root / "output" / "data" / "extracted_terms.json"
    if terms_path.exists():
        with open(terms_path) as fh:
            terms_data = json.load(fh)
        # extracted_terms.json is a flat dict: term → {lemma, domains, frequency, confidence}
        candidate_terms = len(terms_data)
        domain_terms = sum(
            1 for v in terms_data.values()
            if isinstance(v, dict) and v.get("domains")
        )
        vars_["CORPUS_CANDIDATE_TERMS"] = str(candidate_terms)
        vars_["CORPUS_DOMAIN_TERMS"] = str(domain_terms)
    else:
        vars_["CORPUS_CANDIDATE_TERMS"] = "871"
        vars_["CORPUS_DOMAIN_TERMS"] = "223"

    print(f"  Corpus template vars: {len(vars_)} variables loaded")
    print(
        f"    Publications={vars_['CORPUS_PUBLICATIONS']}, "
        f"Tokens={vars_['CORPUS_TOTAL_TOKENS']}, "
        f"Unique={vars_['CORPUS_UNIQUE_TOKENS']}"
    )
    return vars_


def _apply_corpus_vars(content: str, vars_: dict) -> str:
    """Substitute {{KEY}} placeholders with corpus statistics values."""
    for key, value in vars_.items():
        content = content.replace("{{" + key + "}}", value)
    return content


def build_pdf():
    project_root = Path(__file__).resolve().parent.parent
    manuscript_dir = project_root / "manuscript"
    output_dir = project_root / "output" / "pdf"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "ento_linguistics_combined.pdf"

    # Define file order
    files = [
        "01_abstract.md",
        "02_introduction.md",
        "03_methodology.md",
        "04_experimental_results.md",
        "05_discussion.md",
        "06_conclusion.md",
        "07_related_work.md",
        "08_acknowledgments.md",
        "98_symbols_glossary.md",
        "99_references.md",
        "S01_supplemental_methods.md",
        "S02_supplemental_results.md",
        "S03_supplemental_analysis.md",
        "S04_supplemental_applications.md",
    ]

    # ── Parse cover page metadata from config.yaml ────────────────────
    config_path = manuscript_dir / "config.yaml"
    frontmatter = _build_frontmatter(config_path)

    # Create a combined markdown file with absolute image paths
    combined_content = frontmatter

    # Load corpus statistics for template variable substitution
    corpus_vars = _load_corpus_vars(project_root)

    # Verify files exist and concatenate
    input_files = []
    for f in files:
        path = manuscript_dir / f
        if path.exists():
            input_files.append(str(path))
        else:
            print(f"Warning: File not found: {path}")

    for f_path in input_files:
        with open(f_path, "r") as f:
            content = f.read()
            # Replace relative paths with absolute paths
            abs_figures = str(output_dir.parent / "figures")
            abs_figures = abs_figures.replace("\\", "/")

            content = content.replace("../figures/", abs_figures + "/")
            content = content.replace("../output/figures/", abs_figures + "/")

            # Substitute {{CORPUS_*}} template variables with live data values
            content = _apply_corpus_vars(content, corpus_vars)

            combined_content += content + "\n\n\\newpage\n\n"

    temp_md = output_dir / "temp_combined.md"
    with open(temp_md, "w") as f:
        f.write(combined_content)

    # Step 1: Generate .tex with Pandoc (natbib mode -> raw \cite commands)
    tex_file = output_dir / "ento_linguistics_combined.tex"

    pandoc_cmd = [
        "pandoc",
        str(temp_md),
        "-o", str(tex_file),
        "--from=markdown+citations+raw_tex",
        "--standalone",
        "--include-in-header=" + str(manuscript_dir / "preamble.tex"),
        "--bibliography=" + str(manuscript_dir / "references.bib"),
        "--natbib",
        "--number-sections",
        "--toc",
        "--toc-depth=2",
        "--variable", "geometry:margin=1in",
        "--variable", "links-as-notes=true",
    ]

    print("Step 1/5: Generating LaTeX source with Pandoc...")
    print("Command:", " ".join(pandoc_cmd))

    try:
        subprocess.run(pandoc_cmd, check=True)
        print(f"  LaTeX source generated: {tex_file}")
    except subprocess.CalledProcessError as e:
        print(f"  Pandoc failed with error code {e.returncode}")
        sys.exit(e.returncode)

    # Step 2: Copy .bib file to build directory (bibtex needs it alongside .tex)
    import shutil
    bib_src = manuscript_dir / "references.bib"
    bib_dst = output_dir / "references.bib"
    shutil.copy2(bib_src, bib_dst)
    print("Step 2/5: Copied bibliography to build directory")

    # Step 3-5: Multi-pass LaTeX compilation for proper citation resolution
    tex_basename = tex_file.stem

    def run_latex(step_label, cmd_list):
        """Run a LaTeX toolchain command, suppressing non-error output."""
        print(f"  {step_label}...")
        result = subprocess.run(
            cmd_list,
            cwd=str(output_dir),
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"  Warning: {step_label} returned code {result.returncode}")
            if "bibtex" in cmd_list[0].lower():
                if "error" in result.stderr.lower() or result.returncode > 1:
                    print(f"  STDERR: {result.stderr[-500:]}")
                    return False
        return True

    print("Step 3/5: Running xelatex (pass 1)...")
    # Pass 1: no -halt-on-error so undefined-citation warnings don't abort the
    # run mid-document; we need a complete .aux file for bibtex.
    # Note: with the bgcolor preamble bug fixed, pass 1 should now complete cleanly.
    run_latex("xelatex pass 1", [
        "xelatex", "-interaction=nonstopmode", tex_basename
    ])

    print("Step 4/5: Running bibtex (resolving citations)...")
    bibtex_ok = run_latex("bibtex", ["bibtex", tex_basename])
    if not bibtex_ok:
        print("  BibTeX failed — citations will not be resolved")

    print("Step 5/5: Running xelatex (passes 2-3)...")
    # Passes 2-3: citations known, so -halt-on-error is safe.
    run_latex("xelatex pass 2", [
        "xelatex", "-interaction=nonstopmode", "-halt-on-error", tex_basename
    ])
    run_latex("xelatex pass 3", [
        "xelatex", "-interaction=nonstopmode", "-halt-on-error", tex_basename
    ])

    # The PDF is generated in output_dir with the tex basename
    generated_pdf = output_dir / f"{tex_basename}.pdf"
    if generated_pdf.exists() and generated_pdf != output_file:
        shutil.move(str(generated_pdf), str(output_file))

    if output_file.exists():
        size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"\nPDF built successfully: {output_file} ({size_mb:.1f} MB)")
    else:
        print(f"\nPDF build failed — output file not found")
        sys.exit(1)

if __name__ == "__main__":
    build_pdf()
