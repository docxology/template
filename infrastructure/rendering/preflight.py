"""Manuscript rendering preflight checks."""

from __future__ import annotations

from pathlib import Path

from infrastructure.rendering.manuscript_injection import EXCLUDED_DOC_FILENAMES


def puppeteer_cache_has_chrome() -> bool:
    """Return True iff chrome-headless-shell exists in the Puppeteer cache."""
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


def project_manuscript_has_mermaid(manuscript_dir: Path) -> bool:
    """Return True iff any manuscript section embeds a mermaid fenced block."""
    if not manuscript_dir.is_dir():
        return False
    for md in manuscript_dir.glob("*.md"):
        if md.name in EXCLUDED_DOC_FILENAMES:
            continue
        if "```mermaid" in md.read_text(encoding="utf-8"):
            return True
    return False


def run_manuscript_preflight(manuscript_dir: Path) -> tuple[bool, str]:
    """Return (ok, message). ok=False means a known prerequisite gap was found."""
    if not project_manuscript_has_mermaid(manuscript_dir):
        return True, ""
    if puppeteer_cache_has_chrome():
        return True, ""
    message = "\n".join(
        [
            "PREFLIGHT WARNING — chrome-headless-shell missing from Puppeteer cache.",
            "",
            "The combined-PDF render stage uses mmdc (mermaid-cli) for inline mermaid",
            "blocks; mmdc needs a pinned chrome-headless-shell in ~/.cache/puppeteer/.",
            "",
            "From the repository root, install the pinned local tooling (reversible):",
            "  npm ci",
            '  export PATH="$PWD/node_modules/.bin:$PATH"',
            "  npx --no-install puppeteer browsers install chrome-headless-shell",
            "",
        ]
    )
    return False, message
