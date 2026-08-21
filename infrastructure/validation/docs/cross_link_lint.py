"""Markdown cross-link linter.

Sweeps Markdown files for relative `[text](path)` and `[text](path#anchor)` links and
returns links that don't resolve on disk. Skips fenced code blocks AND inline-code
spans (single + double backticks) so URLs inside backticks aren't flagged.

Public API:
    - :class:`BrokenLink`
    - :func:`find_broken_links`
"""

import os
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

from infrastructure.core.logging.utils import get_logger
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.validation.docs._io import read_markdown
from infrastructure.validation.docs.accuracy import heading_slug
from infrastructure.validation.docs.consistency._shared import blank_content
from infrastructure.validation.docs.scan_scope import DEFAULT_EXCLUDE_PARTS, iter_markdown_files

logger = get_logger(__name__)

# Project dirs that are tracked in this PUBLIC repo. Everything else under
# projects/ — including the non-rendered typed subfolders
# (working/ongoing/archive/) holding confidential / rotating WIP — is
# intentionally absent
# from a clean checkout (enforced by .gitignore + scripts/audit/check_tracked_all.py).
# Docs may legitimately reference those as "optional / restore-when-needed", so a
# link into one of those areas is "absent by design", NOT a broken link.
_TRACKED_PROJECT_DIRS = frozenset(PUBLIC_PROJECT_NAMES)
_TRACKED_PROJECT_LEAF_DIRS = frozenset(name.split("/")[-1] for name in PUBLIC_PROJECT_NAMES)

#: Typed subfolders whose contents are deliberately absent from a clean checkout.
_ABSENT_TYPED_SUBDIRS: frozenset[str] = frozenset({"working", "ongoing", "archive"})
#: All typed subfolders that sit between ``projects/`` and a project dir.
_TYPED_PROJECT_SUBDIRS: frozenset[str] = frozenset({"active", "working", "ongoing", "archive", "templates"})


def _qualified_project_segments(parts: tuple[str, ...]) -> tuple[str, int] | None:
    """Return ``(qualified_name, name_end_index)`` for a path under ``projects/``.

    Collapses an optional typed-subfolder prefix into the qualified name, so
    ``projects/templates/template_code_project/output`` yields
    (``"templates/template_code_project"``, index-just-past-the-name).
    """
    if "projects" not in parts:
        return None
    i = parts.index("projects")
    if i + 1 >= len(parts):
        return None
    first = parts[i + 1]
    if first in _TYPED_PROJECT_SUBDIRS:
        if i + 2 >= len(parts):
            return None
        return f"{first}/{parts[i + 2]}", i + 3
    return first, i + 2


def _is_intentionally_absent_project(md_file: Path, decoded: str) -> bool:
    """True when *decoded* points into a deliberately-untracked project area."""
    parts = Path(os.path.normpath(str(md_file.parent / decoded))).parts
    if "projects" not in parts:
        return False
    i = parts.index("projects")
    if i + 1 < len(parts) and parts[i + 1] in _ABSENT_TYPED_SUBDIRS:
        return True
    resolved = _qualified_project_segments(parts)
    if resolved is not None:
        qualified, _ = resolved
        leaf = qualified.split("/")[-1]
        if qualified not in _TRACKED_PROJECT_DIRS and not leaf.endswith(".md"):
            if leaf in _TRACKED_PROJECT_LEAF_DIRS:
                return False
            return True
    return False


def _is_generated_project_output(md_file: Path, decoded: str) -> bool:
    """True when *decoded* points under a public project's generated output."""
    parts = Path(os.path.normpath(str(md_file.parent / decoded))).parts
    resolved = _qualified_project_segments(parts)
    if resolved is None:
        return False
    qualified, name_end = resolved
    return qualified in _TRACKED_PROJECT_DIRS and name_end < len(parts) and parts[name_end] == "output"


_DEFAULT_EXCLUDE_PARTS = DEFAULT_EXCLUDE_PARTS

# Default file globs to skip even within scanned roots.
_DEFAULT_EXCLUDE_GLOBS: tuple[str, ...] = (
    "**/CHANGELOG*.md",
    "**/_generated/**",
    "**/_skill-eval/**",
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
    text = _FENCE_RE.sub(blank_content, text)
    text = _DOUBLE_BACKTICK_RE.sub(blank_content, text)
    text = _SINGLE_BACKTICK_RE.sub(blank_content, text)
    return text


#: Fragment prefixes that are a domain DSL rather than a GitHub heading anchor.
#: ``template_textbook`` renders ``[**term**](#gl:slug)`` glossary references through
#: its own resolver, so those fragments must not be measured against heading slugs.
_NON_ANCHOR_FRAGMENT_PREFIXES: tuple[str, ...] = ("gl:",)

_ATX_HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$", re.MULTILINE)
_EXPLICIT_ID_RE = re.compile(r"""<a\s+(?:id|name)\s*=\s*["']([^"']+)["']""", re.IGNORECASE)
_CURLY_ID_RE = re.compile(r"\{#([A-Za-z0-9_:.-]+)\}")


def _blank_fences(text: str) -> str:
    """Blank fenced code blocks while PRESERVING inline-code spans.

    Headings legitimately contain inline code (``## `uv` command not found``) and
    GitHub slugs the code's *text content*, so the inline-span blanking used for
    link discovery would mis-slug those headings.
    """
    return _FENCE_RE.sub(blank_content, text)


def collect_anchors(md_file: Path) -> frozenset[str]:
    """Return every in-page anchor *md_file* defines.

    Covers ATX heading slugs (with GitHub's ``-1``/``-2`` duplicate suffixes),
    explicit ``<a id="...">``/``<a name="...">`` targets, and ``{#custom-id}``
    heading attributes.
    """
    raw = read_markdown(md_file)
    if raw is None:
        return frozenset()
    anchors: set[str] = set(_EXPLICIT_ID_RE.findall(raw))
    seen: dict[str, int] = {}
    for match in _ATX_HEADING_RE.finditer(_blank_fences(raw)):
        heading = match.group(2)
        custom = _CURLY_ID_RE.search(heading)
        if custom:
            anchors.add(custom.group(1))
            heading = _CURLY_ID_RE.sub("", heading)
        slug = heading_slug(heading)
        if not slug:
            continue
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        anchors.add(slug if count == 0 else f"{slug}-{count}")
    return frozenset(anchors)


def _is_external(target: str) -> bool:
    """True if *target* is an external URL or otherwise not a filesystem reference.

    Pure-anchor targets (``#section``) stay "external" here because callers such as
    :func:`_file_link_target` use this predicate to decide what is a *file* edge;
    treating a same-file anchor as a file edge would add self-loops to the link
    graph. Same-file anchors are validated separately in :func:`find_broken_links`.
    """
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


def _fragment_failure(
    target_file: Path,
    fragment: str,
    anchors_for: "Callable[[Path], frozenset[str]]",
) -> str:
    """Return a failure reason if *fragment* does not resolve in *target_file*.

    Returns an empty string when the fragment resolves or is out of scope. Only
    Markdown targets are checked — a fragment on a ``.py`` or image link is a
    line-reference or viewer hint, not a heading anchor.
    """
    if not fragment:
        return ""
    decoded = unquote(fragment)
    if decoded.startswith(_NON_ANCHOR_FRAGMENT_PREFIXES):
        return ""
    if target_file.is_dir() or target_file.suffix.lower() != ".md":
        return ""
    if decoded in anchors_for(target_file):
        return ""
    return f"anchor '#{decoded}' not found in {target_file.name}"


def find_broken_links(
    roots: Iterable[Path],
    exclude_globs: Iterable[str] = _DEFAULT_EXCLUDE_GLOBS,
) -> list[BrokenLink]:
    """Return all broken relative Markdown links under *roots*.

    Skips fenced code blocks and inline-code spans (single + double backticks),
    skips external URLs (http/https/mailto/etc.), and skips pure-anchor links.
    """
    broken: list[BrokenLink] = []
    anchor_cache: dict[Path, frozenset[str]] = {}

    def _anchors(path: Path) -> frozenset[str]:
        if path not in anchor_cache:
            anchor_cache[path] = collect_anchors(path)
        return anchor_cache[path]

    for md in _iter_markdown_files(roots, exclude_globs):
        raw = read_markdown(md)
        if raw is None:
            continue
        scrubbed = _strip_code(raw)
        raw_lines = raw.splitlines()
        for match in _LINK_RE.finditer(scrubbed):
            target = match.group("url")
            if _is_external(target):
                # A pure `#fragment` still has to resolve within THIS file.
                if target.startswith("#"):
                    line = scrubbed[: match.start()].count("\n") + 1
                    reason = _fragment_failure(md, target[1:], _anchors)
                    if reason and not (0 < line <= len(raw_lines) and _NOQA_RE.search(raw_lines[line - 1])):
                        broken.append(
                            BrokenLink(
                                file=md,
                                line=line,
                                text=raw[match.start("text") : match.end("text")],
                                target=target,
                                reason=reason,
                            )
                        )
                continue
            resolved, reason = _resolve_target(md, target)
            if resolved is None:
                line = scrubbed[: match.start()].count("\n") + 1
                # Allow inline `<!-- noqa: docs-lint -->` on the source line.
                if 0 < line <= len(raw_lines) and _NOQA_RE.search(raw_lines[line - 1]):
                    continue
                # A link into a deliberately-untracked project area (the
                # non-rendered typed subfolders projects/working|ongoing|archive/, or any
                # non-exemplar projects/ name) is absent
                # BY DESIGN in a public/confidential checkout — not a broken link.
                _base = unquote(target.split("#", 1)[0].split("?", 1)[0])
                if _base and _is_intentionally_absent_project(md, _base):
                    continue
                # Project-local output is generated by pipeline stages and is
                # deliberately ignored in clean public checkouts.
                if _base and _is_generated_project_output(md, _base):
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
                continue
            # File resolved — now the `#fragment`, if any, must resolve inside it.
            if "#" in target and resolved is not None:
                fragment = target.split("#", 1)[1]
                frag_reason = _fragment_failure(resolved, fragment, _anchors)
                if not frag_reason:
                    continue
                line = scrubbed[: match.start()].count("\n") + 1
                if 0 < line <= len(raw_lines) and _NOQA_RE.search(raw_lines[line - 1]):
                    continue
                broken.append(
                    BrokenLink(
                        file=md,
                        line=line,
                        text=raw[match.start("text") : match.end("text")],
                        target=target,
                        reason=frag_reason,
                    )
                )
    return broken


@dataclass(frozen=True)
class LinkCycle:
    """A cycle in the relative Markdown file-link graph."""

    files: tuple[str, ...]


def _file_link_target(md_file: Path, target: str) -> str | None:
    """Return repo-relative path for an internal file link, or None if not a file edge."""
    if _is_external(target):
        return None
    base = unquote(target.split("#", 1)[0].split("?", 1)[0])
    if not base:
        return None
    resolved, _ = _resolve_target(md_file, target)
    if resolved is None:
        return None
    return str(resolved)


def _collect_file_edges(roots: Iterable[Path], exclude_globs: Iterable[str]) -> dict[str, set[str]]:
    """Build adjacency list of repo-relative markdown paths."""
    graph: dict[str, set[str]] = {}
    for md in _iter_markdown_files(roots, exclude_globs):
        raw = read_markdown(md)
        if raw is None:
            continue
        source = str(md.resolve())
        graph.setdefault(source, set())
        scrubbed = _strip_code(raw)
        for match in _LINK_RE.finditer(scrubbed):
            target_path = _file_link_target(md, match.group("url"))
            if target_path is None:
                continue
            graph.setdefault(source, set()).add(target_path)
            graph.setdefault(target_path, set())
    return graph


def detect_markdown_link_cycles(
    roots: Iterable[Path],
    exclude_globs: Iterable[str] = _DEFAULT_EXCLUDE_GLOBS,
) -> list[LinkCycle]:
    """Detect directed cycles in relative Markdown file-to-file links under *roots*."""
    graph = _collect_file_edges(roots, exclude_globs)
    visited: set[str] = set()
    stack: set[str] = set()
    cycles: list[LinkCycle] = []

    def dfs(node: str, path: list[str]) -> None:
        """Run a depth-first search over the link graph."""
        if node in stack:
            start = path.index(node)
            cycle = tuple(path[start:] + [node])
            cycles.append(LinkCycle(files=cycle))
            return
        if node in visited:
            return
        visited.add(node)
        stack.add(node)
        path.append(node)
        for neighbor in graph.get(node, ()):
            dfs(neighbor, path)
        path.pop()
        stack.remove(node)

    for node in graph:
        dfs(node, [])

    # Deduplicate cycles that are rotations of the same loop.
    unique: list[LinkCycle] = []
    seen: set[tuple[str, ...]] = set()
    for cycle in cycles:
        body = cycle.files[:-1]
        if not body:
            continue
        rotations = tuple(tuple(body[i:] + body[:i]) for i in range(len(body)))
        key = min(rotations)
        if key not in seen:
            seen.add(key)
            unique.append(LinkCycle(files=cycle.files))
    return unique


__all__ = ["BrokenLink", "LinkCycle", "detect_markdown_link_cycles", "find_broken_links"]
