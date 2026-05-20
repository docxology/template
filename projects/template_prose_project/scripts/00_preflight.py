#!/usr/bin/env python3
"""Pre-flight check: warn before the pipeline if a known rendering prerequisite is missing.

The combined-PDF stage (`scripts/03_render_pdf.py`) shells out to `mmdc`
(mermaid-cli) for every inline `mermaid` block in the manuscript. `mmdc`
in turn needs a **pinned** `chrome-headless-shell` in the Puppeteer cache
(`~/.cache/puppeteer/`). CI provisions this automatically; a fresh local
clone does not. Without it, the PDF Rendering stage fails while per-section
slide PDFs still succeed — that asymmetric tell is the documented signature
of the missing dependency.

This script emits a single, actionable diagnostic before any other stage
runs. It does NOT install anything (install is one-time and out of scope).
Exit code 0 means "preflight clean"; exit code 1 means "preflight surfaced
a known prerequisite gap — see message".

Usage::

    uv run python projects/template_prose_project/scripts/00_preflight.py
"""

from __future__ import annotations

import sys
from pathlib import Path


def _puppeteer_cache_has_chrome() -> bool:
    """Return True iff a `chrome-headless-shell/` directory exists in the Puppeteer cache."""
    cache_root = Path.home() / ".cache" / "puppeteer"
    if not cache_root.is_dir():
        return False
    for shell_dir in cache_root.glob("chrome-headless-shell*"):
        if shell_dir.is_dir():
            return True
    nested = cache_root / "chrome-headless-shell"
    if nested.is_dir() and any(nested.iterdir()):
        return True
    return False


def _project_manuscript_has_mermaid() -> bool:
    """Return True iff any manuscript section embeds a ```mermaid``` block."""
    here = Path(__file__).resolve().parent
    manuscript_dir = here.parent / "manuscript"
    if not manuscript_dir.is_dir():
        return False
    for md in manuscript_dir.glob("*.md"):
        if "```mermaid" in md.read_text(encoding="utf-8"):
            return True
    return False


def main() -> int:
    if not _project_manuscript_has_mermaid():
        return 0
    if _puppeteer_cache_has_chrome():
        return 0
    sys.stderr.write(
        "\n".join(
            [
                "PREFLIGHT WARNING — chrome-headless-shell missing from Puppeteer cache.",
                "",
                "The combined-PDF render stage uses mmdc (mermaid-cli) for inline mermaid",
                "blocks; mmdc needs a pinned chrome-headless-shell in ~/.cache/puppeteer/.",
                "Without it the 'PDF Rendering' stage will fail while per-section slide",
                "PDFs succeed — that asymmetry is the diagnostic tell.",
                "",
                "One-time install (reversible):",
                "  npx --yes puppeteer browsers install chrome-headless-shell",
                "",
                "Full detail: projects/template_prose_project/docs/troubleshooting.md",
                "             (#pdf-rendering-stage-fails-mmdc-could-not-find-chrome)",
                "",
            ]
        )
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
