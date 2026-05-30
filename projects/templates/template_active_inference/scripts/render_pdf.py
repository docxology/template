#!/usr/bin/env python3
"""Self-contained PDF renderer for the standalone repository.

This is the standalone build path: it composes, hydrates, and renders the
manuscript to PDF using only this project's own code plus the external `pandoc`
and `xelatex` command-line tools — **no monorepo `infrastructure` import**. A
checkout of this repository alone can produce its PDF with::

    uv run python scripts/render_pdf.py

Typography is read from this project's own sources: page margins from
``manuscript/config.yaml`` (``metadata.geometry``), the dense body font from
``manuscript/preamble.md`` (the ``fontsize`` package), and red hyperlinks via
pandoc's ``colorlinks`` variables. The richer monorepo pipeline
(``scripts/03_render_pdf.py`` in the template repo) adds transmission bookends,
QR strips, and LaTeX post-processing; this renderer is the portable subset.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from manuscript.render_helpers import extract_preamble, geometry_string  # noqa: E402


def main() -> int:
    for tool in ("pandoc", "xelatex"):
        if shutil.which(tool) is None:
            print(f"error: `{tool}` not found on PATH (required for standalone render)", file=sys.stderr)
            return 2

    from manuscript.hydrate import write_resolved_manuscript
    from manuscript.sheaf import compose_all_sections
    from manuscript.variables import generate_variables

    manuscript_dir = PROJECT_ROOT / "manuscript"
    out_pdf_dir = PROJECT_ROOT / "output" / "pdf"
    out_pdf_dir.mkdir(parents=True, exist_ok=True)

    # 1. compose flat sections from sheaf fragments, 2. hydrate {{tokens}}.
    compose_all_sections(PROJECT_ROOT, manuscript_dir=manuscript_dir)
    variables = generate_variables(PROJECT_ROOT, require_analysis_outputs=False)
    resolved_dir = write_resolved_manuscript(PROJECT_ROOT, variables)

    # 3. concatenate composed+hydrated sections in lexical (manifest) order.
    sections = sorted(p for p in resolved_dir.glob("[0-9][0-9]_*.md"))
    if not sections:
        sections = sorted(p for p in manuscript_dir.glob("[0-9][0-9]_*.md"))
    combined_md = out_pdf_dir / "_standalone_combined.md"
    combined_md.write_text("\n\n".join(p.read_text(encoding="utf-8") for p in sections), encoding="utf-8")

    # 4. preamble (font) + geometry (margins), both from project-owned sources.
    header_tex = out_pdf_dir / "_standalone_preamble.tex"
    header_tex.write_text(extract_preamble(manuscript_dir / "preamble.md") + "\n", encoding="utf-8")

    config = yaml.safe_load((manuscript_dir / "config.yaml").read_text(encoding="utf-8")) or {}
    title = str((config.get("paper") or {}).get("title") or "Manuscript")

    pdf_out = out_pdf_dir / "template_active_inference_standalone.pdf"
    cmd = [
        "pandoc",
        str(combined_md),
        "-o",
        str(pdf_out),
        "--from=markdown+tex_math_dollars+raw_tex",
        "--pdf-engine=xelatex",
        "--standalone",
        "--number-sections",
        "-H",
        str(header_tex),
        "-V",
        f"geometry:{geometry_string(manuscript_dir / 'config.yaml')}",
        # Red hyperlinks — self-contained, no LaTeX post-processing needed.
        "-V",
        "colorlinks=true",
        "-V",
        "linkcolor=red",
        "-V",
        "urlcolor=red",
        "-V",
        "citecolor=red",
        "-M",
        f"title={title}",
        f"--resource-path={manuscript_dir}",
    ]
    crossref = shutil.which("pandoc-crossref")
    if crossref:
        cmd += ["--filter", crossref]
    bib = manuscript_dir / "references.bib"
    if bib.is_file():
        cmd += ["--citeproc", "--bibliography", str(bib)]

    print("rendering (standalone):", " ".join(cmd))
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print("error: pandoc render failed", file=sys.stderr)
        return result.returncode
    print(f"✓ standalone PDF: {pdf_out} ({pdf_out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
