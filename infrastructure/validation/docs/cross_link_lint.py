"""Markdown cross-link linter.

Sweeps Markdown files for relative `[text](path)` and `[text](path#anchor)` links and
returns links that don't resolve on disk. Skips fenced code blocks AND inline-code
spans (single + double backticks) so URLs inside backticks aren't flagged.

Public API:
    - :class:`BrokenLink`
    - :func:`find_broken_links`
"""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

from infrastructure.core.logging.utils import get_logger
from infrastructure.validation.docs.scan_scope import DEFAULT_EXCLUDE_PARTS, iter_markdown_files

logger = get_logger(__name__)


_DEFAULT_EXCLUDE_PARTS = DEFAULT_EXCLUDE_PARTS

# Default file globs to skip even within scanned roots.
_DEFAULT_EXCLUDE_GLOBS: tuple[str, ...] = (
    "**/CHANGELOG*.md",
    "**/_generated/**",
)

# Match a fenced code block (``` or ~~~), capturing the entire block (incl fences).
# Allow leading whitespace so indented fences (e.g. inside list items) are matched.
_FENCE_RE = re.compile(
    r"^[ \t]*(?P<fence>`{3,}|~{3,}).*?\n.*?\n[ \t]*(?P=fence)",
    re.MULTILINE | re.DOTALL,
)

# Match double-backtick spans first (so single-backtick stripper doesn't mangle them).
_DOUBLE_BACKTICK_RE = re.compile(r"``[^`\n]+?``")
# Match single-backtick spans (no embedded backticks, no newlines).
_SINGLE_BACKTICK_RE = re.compile(r"`[^`\n]+?`")

# Match `[text](url)` — text can have nested brackets minimally; url is balanced parens-free.
_LINK_RE = re.compile(r"\[(?P<text>[^\]\n]*)\]\((?P<url>[^)\n\s]+)(?:\s+\"[^\"]*\")?\)")

# Inline escape hatch — append `<!-- noqa: docs-lint -->` (optionally with a
# free-form explanatory comment that may itself contain hyphens) to a Markdown
# line to suppress broken-link warnings on that line.
_NOQA_RE = re.compile(r"<!--\s*noqa:\s*docs-lint", re.IGNORECASE)


@dataclass(frozen=True)
class BrokenLink:
    """A relative link in Markdown that does not resolve on disk."""

    file: Path
    line: int
    text: str
    target: str  # raw target string from the markdown source (may include #anchor)
    reason: str  # short human-readable reason

    def format(self) -> str:
        """Return a single-line summary."""
        return f"{self.file}:{self.line}: broken link [{self.text}]({self.target}) — {self.reason}"


def _iter_markdown_files(roots: Iterable[Path], exclude_globs: Iterable[str]) -> list[Path]:
    """Walk *roots*, return Markdown files, honour exclude globs and dirs."""
    return iter_markdown_files(
        roots,
        exclude_parts=_DEFAULT_EXCLUDE_PARTS,
        exclude_globs=exclude_globs,
    )


def _strip_code(text: str) -> str:
    """Replace fenced and inline code spans with same-length whitespace.

    Whitespace replacement (rather than deletion) keeps line/column offsets correct
    so reported line numbers map to the source file faithfully.
    """

    def _blank(match: re.Match[str]) -> str:
        s = match.group(0)
        # Preserve newlines so line counts stay correct.
        return "".join("\n" if ch == "\n" else " " for ch in s)

    text = _FENCE_RE.sub(_blank, text)
    text = _DOUBLE_BACKTICK_RE.sub(_blank, text)
    text = _SINGLE_BACKTICK_RE.sub(_blank, text)
    return text


def _is_external(target: str) -> bool:
    """True if *target* is an external URL or otherwise not a filesystem reference."""
    if not target:
        return True
    if target.startswith("#"):
        return True
    parts = urlsplit(target)
    if parts.scheme in {"http", "https", "ftp", "mailto", "tel", "data", "file"}:
        return True
    # Schemes like `git@github.com:foo/bar.git` are not handled here — treat as external.
    if ":" in target.split("/")[0] and not target.startswith("./") and not target.startswith("../"):
        # e.g. "github:foo" — bail out.
        return True
    return False


def _resolve_target(md_file: Path, target: str) -> tuple[Path | None, str]:
    """Resolve a relative link target. Return (resolved-path, reason-if-broken)."""
    # Strip anchor + query
    base = target.split("#", 1)[0].split("?", 1)[0]
    if not base:
        # Pure anchor — handled by `_is_external` upstream.
        return md_file, ""
    decoded = unquote(base)
    if decoded.startswith("/"):
        # Absolute-from-root style is ambiguous on disk — treat as unresolvable
        return None, "absolute path (treated as unresolvable in repo context)"
    candidate = (md_file.parent / decoded).resolve()
    if candidate.exists():
        return candidate, ""
    # Try normalising trailing slash.
    if decoded.endswith("/"):
        idx = (md_file.parent / decoded.rstrip("/")).resolve()
        if idx.exists():
            return idx, ""
    return None, "target does not exist on disk"


def find_broken_links(
    roots: Iterable[Path],
    exclude_globs: Iterable[str] = _DEFAULT_EXCLUDE_GLOBS,
) -> list[BrokenLink]:
    """Return all broken relative Markdown links under *roots*.

    Skips fenced code blocks and inline-code spans (single + double backticks),
    skips external URLs (http/https/mailto/etc.), and skips pure-anchor links.
    """
    broken: list[BrokenLink] = []
    for md in _iter_markdown_files(roots, exclude_globs):
        try:
            raw = md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            logger.debug("skipping %s: %s", md, e)
            continue
        scrubbed = _strip_code(raw)
        raw_lines = raw.splitlines()
        for match in _LINK_RE.finditer(scrubbed):
            target = match.group("url")
            if _is_external(target):
                continue
            resolved, reason = _resolve_target(md, target)
            if resolved is None:
                line = scrubbed[: match.start()].count("\n") + 1
                # Allow inline `<!-- noqa: docs-lint -->` on the source line.
                if 0 < line <= len(raw_lines) and _NOQA_RE.search(raw_lines[line - 1]):
                    continue
                # Pull the original (non-scrubbed) text from the same span.
                original_text = raw[match.start("text") : match.end("text")]
                broken.append(
                    BrokenLink(
                        file=md,
                        line=line,
                        text=original_text,
                        target=target,
                        reason=reason,
                    )
                )
    return broken


__all__ = ["BrokenLink", "find_broken_links"]
