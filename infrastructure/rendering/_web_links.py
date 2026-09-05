"""Resolve public repository links and validate deployed publication anchors."""

from __future__ import annotations

import html
import re
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

import yaml

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._web_io import write_if_changed

_ANCHOR_HREF_RE = re.compile(
    r"(?P<prefix><a\b[^>]*?(?<!\S)href\s*=\s*)(?P<quote>[\"'])(?P<href>.*?)(?P=quote)",
    flags=re.IGNORECASE | re.DOTALL,
)

_PASSTHROUGH_HREF_SCHEMES = frozenset({"http", "https", "mailto", "tel"})

_PUBLIC_POOL_ROOTS = frozenset({"projects", "fonds", "rules", "tools"})


def repository_root_for(path: Path) -> Path:
    """Return the enclosing public repository root for a web render.

    A source or output path outside this checkout is deliberately rejected. In
    particular, private sidecar projects must never cause their authored links
    to be rewritten against the public repository.
    """

    candidates: list[Path] = []
    resolved = path.resolve(strict=False)
    directory = resolved if resolved.is_dir() else resolved.parent
    for candidate in (directory, *directory.parents):
        if candidate not in candidates:
            candidates.append(candidate)
    for candidate in candidates:
        citation = candidate / "CITATION.cff"
        if (
            resolved.is_relative_to(candidate)
            and citation.is_file()
            and not citation.is_symlink()
            and (candidate / "infrastructure").is_dir()
            and (candidate / "projects" / "templates").is_dir()
        ):
            return candidate.resolve(strict=True)
    raise RenderingError(
        f"Could not locate public repository root for web source: {path}",
        context={"source": str(path)},
    )


def _repository_code_url(repository_root: Path) -> str:
    """Read and validate the canonical repository URL from ``CITATION.cff``."""

    citation = repository_root / "CITATION.cff"
    if citation.is_symlink() or not citation.is_file():
        raise RenderingError(f"Repository citation metadata is missing or unsafe: {citation}")
    try:
        payload = yaml.safe_load(citation.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise RenderingError(f"Could not read repository citation metadata: {citation}") from exc
    repository_code = payload.get("repository-code") if isinstance(payload, dict) else None
    if not isinstance(repository_code, str):
        raise RenderingError(f"CITATION.cff is missing repository-code: {citation}")
    parsed = urlsplit(repository_code)
    if (
        parsed.scheme != "https"
        or parsed.netloc.lower() != "github.com"
        or len([part for part in parsed.path.split("/") if part]) != 2
        or parsed.query
        or parsed.fragment
    ):
        raise RenderingError(f"CITATION.cff repository-code is not a canonical GitHub HTTPS URL: {repository_code}")
    return repository_code.rstrip("/")


def _url_suffix(query: str, fragment: str) -> str:
    return (f"?{query}" if query else "") + (f"#{fragment}" if fragment else "")


def _reject_non_public_pool_target(relative_path: Path) -> None:
    parts = relative_path.parts
    if parts and parts[0] in _PUBLIC_POOL_ROOTS and (len(parts) < 2 or parts[1] != "templates"):
        raise RenderingError(f"Web link targets non-public repository content: {relative_path.as_posix()}")


def _resolve_repository_href_target(
    href_path: str,
    *,
    html_file: Path,
    repository_root: Path,
    source_files: tuple[Path, ...] = (),
) -> tuple[Path, bool]:
    """Resolve one local href from Pandoc or a renderer postprocessor."""

    decoded = unquote(href_path)
    if "\x00" in decoded or "\\" in decoded:
        raise RenderingError(f"Web link contains an unsafe local path: {href_path}")
    lexical = Path(decoded)
    if lexical.is_absolute():
        raise RenderingError(f"Web link contains an unsupported absolute filesystem path: {href_path}")

    # Pandoc preserves authored paths in the HTML. Prefer the output-page
    # interpretation for renderer-owned assets, then the source directory for
    # authored manuscript links, and finally a checkout-relative path used by
    # generated links.
    page_candidate = html_file.parent / lexical
    candidate_paths: list[Path] = [page_candidate]
    candidate_paths.extend(source.parent / lexical for source in source_files)
    candidate_paths.append(repository_root / lexical)

    page_target: Path | None = None
    source_targets: list[Path] = []
    root_target: Path | None = None
    for index, candidate in enumerate(candidate_paths):
        try:
            if not candidate.exists():
                continue
            target = candidate.resolve(strict=True)
        except OSError:
            continue
        if index == 0:
            page_target = target
        elif index < len(candidate_paths) - 1:
            if target not in source_targets:
                source_targets.append(target)
        else:
            root_target = target

    if page_target is not None:
        target = page_target
    elif len(source_targets) > 1:
        raise RenderingError(
            f"Web link resolves to multiple manuscript targets: {href_path}",
            context={"page": str(html_file), "targets": [str(path) for path in source_targets]},
        )
    elif source_targets:
        target = source_targets[0]
    elif root_target is not None:
        target = root_target
    else:
        raise RenderingError(
            f"Web link target does not exist: {href_path}",
            context={"page": str(html_file)},
        )

    web_root = html_file.parent.resolve(strict=True)
    if page_target is not None:
        try:
            page_target.relative_to(web_root)
        except ValueError:
            pass
        else:
            return page_target, page_target.is_dir()

    root = repository_root.resolve(strict=True)
    try:
        relative = target.relative_to(root)
    except ValueError as exc:
        raise RenderingError(
            f"Web link escapes the public repository: {href_path}",
            context={"page": str(html_file), "target": str(target)},
        ) from exc
    _reject_non_public_pool_target(relative)
    return target, target.is_dir()


def _quoted_relative_path(path: Path) -> str:
    """Quote a repository or web-relative path for an HTML URL."""

    return quote(path.as_posix(), safe="/-._~")


def _web_relative_target(html_file: Path, target: Path) -> str | None:
    """Return a deployed-web-relative target when ``target`` is local HTML."""

    try:
        relative = target.relative_to(html_file.parent.resolve(strict=True))
    except ValueError:
        return None
    return _quoted_relative_path(relative)


def _renderer_figure_asset_target(html_file: Path, href_path: str) -> Path | None:
    """Resolve a safe deployed link into the sibling ``output/figures`` tree."""

    decoded = unquote(href_path)
    if "\x00" in decoded or "\\" in decoded:
        return None
    lexical = Path(decoded)
    if lexical.is_absolute():
        return None
    try:
        target = (html_file.parent / lexical).resolve(strict=True)
        figures_root = (html_file.parent.parent / "figures").resolve(strict=True)
        target.relative_to(figures_root)
    except (OSError, ValueError):
        return None
    if target.is_symlink() or not target.is_file():
        return None
    return target


def rewrite_repository_links(
    html_file: Path,
    *,
    repository_root: Path,
    rendered_sources: Mapping[Path, str],
) -> None:
    """Rewrite local anchors into deployed pages or canonical repository URLs.

    Pandoc preserves authored relative paths in the HTML. Links to renderer-
    owned pages stay inside ``output/web``; links to manuscript source files
    are mapped to their rendered page when available; every other public
    repository target becomes a deterministic GitHub ``main`` URL. Unsafe or
    nonexistent targets fail instead of surviving as broken deployed links.
    """

    root = repository_root.resolve(strict=True)
    repository_code = _repository_code_url(root)
    source_files = tuple(source.resolve(strict=True) for source in rendered_sources)
    mapped_sources = {
        source.resolve(strict=True): Path(output_name) for source, output_name in rendered_sources.items()
    }
    for output_name in mapped_sources.values():
        if output_name.is_absolute() or ".." in output_name.parts:
            raise RenderingError(f"Rendered web page name is unsafe: {output_name}")
    content = html_file.read_text(encoding="utf-8")

    def _rewrite(match: re.Match[str]) -> str:
        raw_href = html.unescape(match.group("href"))
        parsed = urlsplit(raw_href)
        scheme = parsed.scheme.lower()
        if scheme in _PASSTHROUGH_HREF_SCHEMES:
            return match.group(0)
        if scheme or parsed.netloc:
            raise RenderingError(f"Web link uses an unsupported URI scheme: {raw_href}")
        if not parsed.path or parsed.path.startswith("/"):
            return match.group(0)
        if _renderer_figure_asset_target(html_file, parsed.path) is not None:
            return match.group(0)

        target, is_directory = _resolve_repository_href_target(
            parsed.path,
            html_file=html_file,
            repository_root=root,
            source_files=source_files,
        )
        suffix = _url_suffix(parsed.query, parsed.fragment)
        local_web_target = _web_relative_target(html_file, target)
        mapped = mapped_sources.get(target)
        if local_web_target is not None:
            replacement = local_web_target
        elif mapped is not None:
            replacement = _quoted_relative_path(mapped)
        else:
            relative = target.relative_to(root)
            encoded = _quoted_relative_path(relative)
            if not encoded:
                replacement = repository_code + ("/" if parsed.path.endswith("/") else "")
            else:
                route = "tree" if is_directory else "blob"
                replacement = f"{repository_code}/{route}/main/{encoded}"
                if is_directory and parsed.path.endswith("/"):
                    replacement += "/"
        escaped = html.escape(replacement + suffix, quote=True)
        return f"{match.group('prefix')}{match.group('quote')}{escaped}{match.group('quote')}"

    write_if_changed(html_file, _ANCHOR_HREF_RE.sub(_rewrite, content))


def deployed_web_link_issues(web_dir: Path) -> tuple[str, ...]:
    """Return fail-closed issues for renderer-owned deployed HTML anchors."""

    try:
        root = web_dir.resolve(strict=True)
    except OSError as exc:
        return (f"web output directory is unreadable: {web_dir}: {exc}",)
    pages = [root / "index.html", *sorted(root.glob("*__*.html"))]
    issues: list[str] = []
    for page in pages:
        if not page.is_file() or page.is_symlink():
            issues.append(f"renderer-owned web page is missing or unsafe: {page}")
            continue
        try:
            content = page.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            issues.append(f"renderer-owned web page is unreadable: {page}: {exc}")
            continue
        for match in _ANCHOR_HREF_RE.finditer(content):
            raw_href = html.unescape(match.group("href"))
            parsed = urlsplit(raw_href)
            scheme = parsed.scheme.lower()
            if scheme in _PASSTHROUGH_HREF_SCHEMES:
                continue
            if scheme or parsed.netloc:
                issues.append(f"{page.name}: unsupported href scheme: {raw_href}")
                continue
            if not parsed.path:
                continue
            if parsed.path.startswith("/"):
                continue
            decoded = unquote(parsed.path)
            if "\x00" in decoded or "\\" in decoded:
                issues.append(f"{page.name}: unsafe local href: {raw_href}")
                continue
            candidate = page.parent / decoded
            try:
                resolved = candidate.resolve(strict=True)
                resolved.relative_to(root)
            except (OSError, ValueError):
                if _renderer_figure_asset_target(page, parsed.path) is None:
                    issues.append(f"{page.name}: local href leaves output/web or is missing: {raw_href}")
    return tuple(issues)
