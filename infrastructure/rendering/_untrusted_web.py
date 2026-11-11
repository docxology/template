"""Admit and render prepared documents for the untrusted HTML profile."""

from __future__ import annotations

import html
import json
import os
import selectors
import stat
import subprocess
import time
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory, TemporaryFile
from typing import Any
from urllib.parse import unquote, urlsplit

import yaml

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.files.secure_write import HeldDirectory, atomic_write_text_confined, hold_confined_directory
from infrastructure.core.project_paths import BARE_PROJECT_LOCATIONS, NON_RENDERED_SUBDIRS, validate_project_name
from infrastructure.rendering._web_source_context import source_context_tokens, split_canonical_html
from infrastructure.rendering.config import RenderingConfig, _unresolved_config_tokens
from infrastructure.rendering.manuscript_discovery import EXCLUDE_NAMES
from infrastructure.rendering.native_render_custody import native_render_custody

_MAX_INPUT_BYTES = 1024 * 1024
_MAX_INPUT_FILES = 64
_MAX_MANUSCRIPT_BYTES = 8 * 1024 * 1024
_MAX_AST_BYTES = 16 * 1024 * 1024
_MAX_HTML_BYTES = 16 * 1024 * 1024
_MAX_AST_DEPTH = 96
_MALFORMED_AST = "Untrusted Markdown parser returned a malformed or over-deep document"
_MARKDOWN = "markdown+raw_html+raw_tex+raw_attribute+tex_math_dollars+header_attributes"
_SAFE_METADATA = frozenset({"title", "subtitle", "author", "date", "lang"})


@dataclass(frozen=True)
class PreparedWeb:
    """Original names and the exact confined bytes the untrusted writer may consume."""

    config: dict[str, Any] | None
    sources: tuple[tuple[Path, bytes], ...]
    bibliographies: tuple[tuple[str, bytes], ...]


def _directory_identity(root: Path) -> tuple[int, int]:
    info = root.lstat()
    if not stat.S_ISDIR(info.st_mode):
        raise RenderingError("Untrusted manuscript root must be a real directory")
    return info.st_dev, info.st_ino


@contextmanager
def hold_untrusted_project(repo_root: Path, project_name: str) -> Iterator[tuple[Path, HeldDirectory]]:
    """Select a project slot with the usual precedence and refuse every path alias."""
    root = repo_root.absolute()
    identity = _directory_identity(root)
    name = validate_project_name(project_name)
    qualified = name.split("/", 1)[0] in (NON_RENDERED_SUBDIRS | {"active", "templates"})
    locations = ("",) if qualified else BARE_PROJECT_LOCATIONS

    with ExitStack() as stack:
        flat = None
        for location in locations:
            slot = Path("projects") / location / name
            try:
                directory = stack.enter_context(hold_confined_directory(root, slot, expected_root_identity=identity))
            except FileNotFoundError:
                continue
            binding = (root / slot, directory)
            if (
                qualified
                or location == "working"
                or {"src", "tests", "scripts", "manuscript"}.intersection(os.listdir(directory.descriptor))
            ):
                yield binding
                return
            if not location:
                flat = binding
        if flat is not None:
            yield flat
            return
        raise RenderingError("Untrusted Stage 3 requires a real project slot")


def _read_file(directory_fd: int, name: str, *, budget: int) -> bytes:
    """Read one small single-link file from a held manuscript directory."""
    if not hasattr(os, "O_NOFOLLOW"):
        raise RenderingError("Untrusted input requires no-follow filesystem support")
    descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
    with os.fdopen(descriptor, "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > _MAX_INPUT_BYTES:
            raise RenderingError("Untrusted input must be a bounded regular single-link file")
        if before.st_size > budget:
            raise RenderingError("Untrusted manuscript exceeds its aggregate input byte budget")
        body = stream.read(min(_MAX_INPUT_BYTES, budget) + 1)
        after = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        held = os.fstat(stream.fileno())
        if (
            len(body) != before.st_size
            or (after.st_dev, after.st_ino) != (before.st_dev, before.st_ino)
            or (held.st_size, held.st_mtime_ns, held.st_ctime_ns, held.st_nlink)
            != (before.st_size, before.st_mtime_ns, before.st_ctime_ns, 1)
        ):
            raise RenderingError("Untrusted input changed during the confined read")
        return body


def _prepared_web(
    root: Path,
    relative: Path,
    sources: tuple[Path, ...] | None,
    *,
    bibliographies: bool,
    expected_root_identity: tuple[int, int] | None = None,
) -> PreparedWeb | None:
    identity = expected_root_identity if expected_root_identity is not None else _directory_identity(root)
    with ExitStack() as stack:
        try:
            directory = stack.enter_context(hold_confined_directory(root, relative, expected_root_identity=identity))
        except FileNotFoundError:
            if sources is None:
                return None
            raise
        names = set(os.listdir(directory.descriptor))
        manuscript = root / relative
        if sources is None:
            sources = tuple(
                manuscript / name for name in sorted(names) if name.endswith(".md") and name not in EXCLUDE_NAMES
            )
            if not sources:
                return None
            if any(source.stem[:1].isdigit() and not source.stem.startswith(("98_", "99_")) for source in sources):
                sources = tuple(source for source in sources if source.name != "complete.md")

        if (
            not sources
            or len(sources) != len(set(sources))
            or any(source.parent != manuscript or source.suffix != ".md" for source in sources)
        ):
            raise RenderingError("Untrusted HTML requires distinct top-level Markdown inputs")

        bib_names = sorted(name for name in names if bibliographies and name.endswith(".bib"))
        if len(sources) + len(bib_names) > _MAX_INPUT_FILES:
            raise RenderingError("Untrusted manuscript input count exceeds its limit")

        remaining_bytes = _MAX_MANUSCRIPT_BYTES

        def read(name: str) -> bytes:
            nonlocal remaining_bytes
            body = _read_file(directory.descriptor, name, budget=remaining_bytes)
            remaining_bytes -= len(body)
            return body

        config = None
        if "config.yaml" in names:
            config_text = read("config.yaml").decode()
            if _unresolved_config_tokens(config_text):
                raise RenderingError("Untrusted manuscript configuration contains unresolved hydration tokens")
            config = yaml.safe_load(config_text)
            if config is not None and not isinstance(config, dict):
                raise RenderingError("Untrusted manuscript configuration must be a mapping")

        held = PreparedWeb(
            config,
            tuple((source, read(source.name)) for source in sources),
            tuple((name, read(name)) for name in bib_names),
        )
        if not directory.matches_path():
            raise RenderingError("Untrusted manuscript directory moved during admission")
        return held


def prepare_project_web(project_root: Path, *, expected_root_identity: tuple[int, int]) -> PreparedWeb:
    """Select the first prepared manuscript inside the held project root."""
    for location in (Path("output/manuscript"), Path("manuscript"), Path("docs/manuscript")):
        prepared = _prepared_web(
            project_root, location, None, bibliographies=True, expected_root_identity=expected_root_identity
        )
        if prepared is not None:
            return prepared
    raise RenderingError("Untrusted Stage 3 requires prepared Markdown inputs")


def prepare_web_sources(manuscript_dir: Path, sources: tuple[Path, ...], *, bibliographies: bool) -> PreparedWeb:
    """Admit explicitly nominated sources without following their path aliases."""
    try:
        result = _prepared_web(
            manuscript_dir.absolute(), Path(), tuple(path.absolute() for path in sources), bibliographies=bibliographies
        )
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise RenderingError("Could not admit untrusted manuscript inputs") from exc
    if result is None:
        raise RenderingError("Untrusted HTML requires prepared Markdown inputs")
    return result


def _check_link(target: str) -> None:
    normalized = unquote(html.unescape(target))
    if normalized != normalized.strip() or any(ord(char) < 32 or char == "\\" for char in normalized):
        raise RenderingError("Untrusted HTML link contains an unsafe character")
    try:
        parsed = urlsplit(normalized)
    except ValueError as exc:
        raise RenderingError("Untrusted HTML link is malformed") from exc
    if parsed.scheme in {"https", "http"} and parsed.hostname and parsed.username is None:
        return
    if parsed.scheme in {"mailto", "tel"} and parsed.path and not parsed.netloc:
        return
    if parsed.scheme or parsed.netloc or parsed.path.startswith("/") or ".." in Path(parsed.path).parts:
        raise RenderingError("Untrusted HTML link uses an unsafe destination")


def _check_document(value: object, depth: int = 0) -> None:
    """Admit Pandoc nodes before the HTML writer or citeproc can consume them."""
    if depth > _MAX_AST_DEPTH:
        raise RenderingError(_MALFORMED_AST)
    if isinstance(value, dict):
        tag = value.get("t")
        if tag in ("RawBlock", "RawInline", "Image"):
            raise RenderingError("Untrusted HTML refuses raw markup and image inputs")
        if tag == "Link":
            _check_link(value["c"][-1][0])
        for item in value.values():
            _check_document(item, depth + 1)
    elif isinstance(value, list):
        if len(value) == 3 and isinstance(value[0], str) and isinstance(value[1], list) and isinstance(value[2], list):
            if value[2]:
                raise RenderingError("Untrusted HTML refuses authored attribute values")
        for item in value:
            _check_document(item, depth + 1)


class _ScriptlessHTML(HTMLParser):
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"base", "embed", "form", "iframe", "link", "object", "script", "svg", "template"}:
            raise RenderingError("Untrusted HTML writer produced an unsupported element")
        for name, value in attrs:
            if name.startswith("on") or name in {"action", "formaction", "http-equiv", "src", "srcdoc", "srcset"}:
                raise RenderingError("Untrusted HTML writer produced an active attribute")
            if name == "href":
                if tag != "a" or value is None:
                    raise RenderingError("Untrusted HTML writer produced an unsupported link")
                _check_link(value)


def _remaining(deadline: float) -> float:
    seconds = deadline - time.monotonic()
    if seconds <= 0:
        raise RenderingError("Untrusted HTML rendering exceeded its time budget")
    return seconds


def _read_pandoc_output(descriptor: int, *, deadline: float, output_limit: int) -> bytes:
    """Consume a finite stdout prefix, allowing the caller to kill an over-limit producer."""
    body = bytearray()
    with selectors.DefaultSelector() as selector:
        selector.register(descriptor, selectors.EVENT_READ)
        while selector.select(_remaining(deadline)):
            chunk = os.read(descriptor, min(65536, output_limit + 1 - len(body)))
            if not chunk:
                return bytes(body)
            body.extend(chunk)
            if len(body) > output_limit:
                raise RenderingError("Untrusted Pandoc output exceeds its byte budget")
    raise RenderingError("Untrusted HTML rendering exceeded its time budget")


def _pandoc(
    config: RenderingConfig, arguments: list[str], data: bytes, cwd: Path, *, deadline: float, output_limit: int
) -> bytes:
    # Feed a finite regular file rather than blocking on a simultaneous stdin pipe.
    with TemporaryFile(dir=cwd) as source:
        source.write(data)
        source.seek(0)
        try:
            _remaining(deadline)
            with subprocess.Popen(  # noqa: S603 - caller tool selection and SDK-owned argument vector
                [config.pandoc_path, "--sandbox", *arguments],
                stdin=source,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                cwd=cwd,
                env=config.security().environment(),
            ) as process:
                try:
                    if process.stdout is None:
                        raise RenderingError("Untrusted Pandoc stdout is unavailable")
                    body = _read_pandoc_output(process.stdout.fileno(), deadline=deadline, output_limit=output_limit)
                    if process.wait(timeout=_remaining(deadline)):
                        raise RenderingError("Pandoc could not render the admitted untrusted document")
                    return body
                finally:
                    if process.poll() is None:
                        process.kill()
        except subprocess.TimeoutExpired as exc:
            raise RenderingError("Untrusted HTML rendering exceeded its time budget") from exc
        except (OSError, subprocess.SubprocessError) as exc:
            raise RenderingError("Pandoc could not render the admitted untrusted document") from exc


def _document(body: bytes) -> dict[str, Any]:
    try:
        parsed = json.loads(body)
        if (
            not isinstance(parsed, dict)
            or not isinstance(parsed.get("blocks"), list)
            or not isinstance(parsed.get("meta"), dict)
        ):
            raise RenderingError(_MALFORMED_AST)
        if set(parsed["meta"]) - _SAFE_METADATA:
            raise RenderingError("Untrusted Markdown contains unsupported document metadata")
        _check_document(parsed)
    except (ValueError, KeyError, IndexError, TypeError, RecursionError) as exc:
        raise RenderingError(_MALFORMED_AST) from exc
    return parsed


def render_prepared_web(
    config: RenderingConfig,
    prepared: PreparedWeb,
    outputs: tuple[Path | None, ...],
    *,
    index: Path | None = None,
    project_anchor: tuple[Path, tuple[int, int]] | None = None,
) -> Path:
    """Render an admitted roster privately, then publish only scriptless HTML."""
    profile = config.security()
    if native_render_custody("Untrusted HTML cannot use a native render origin") is not None:
        raise RenderingError("Untrusted HTML cannot use native render launchers")
    root = profile.temp_root
    if root is None or not root.is_dir() or root.is_symlink():
        raise RenderingError("Untrusted HTML requires an existing real temporary root")
    root = root.absolute()
    root_identity = _directory_identity(root)
    output_dir = Path(config.web_dir).absolute()
    if len(outputs) != len(prepared.sources) or (index is None and (len(outputs) != 1 or outputs[0] is None)):
        raise RenderingError("Untrusted HTML output roster differs from its sources")
    planned = tuple(path for path in (index, *outputs) if path is not None)
    if not output_dir.is_relative_to(root) or any(path.absolute().parent != output_dir for path in planned):
        raise RenderingError("Untrusted HTML outputs must share one confined directory")
    if len({path.name.casefold() for path in planned}) != len(planned):
        raise RenderingError("Untrusted HTML output names collide")

    deadline = time.monotonic() + min(profile.timeout_seconds, 60)
    with (
        hold_confined_directory(root, Path(), expected_root_identity=root_identity) as temporary_root,
        TemporaryDirectory(prefix=".untrusted-web-", dir=root) as scratch,
    ):
        profile.validate_output_tree(output_dir, allow_missing_root=True)
        directory = Path(scratch)
        bodies = tuple(body for _, body in prepared.sources)
        documents = []
        remaining_ast_bytes = _MAX_AST_BYTES
        for body in bodies:
            parsed = _pandoc(
                config,
                [f"--from={_MARKDOWN}", "--to=json"],
                body,
                directory,
                deadline=deadline,
                output_limit=remaining_ast_bytes,
            )
            remaining_ast_bytes -= len(parsed)
            documents.append(_document(parsed))
        document = documents[0]
        if index is not None:
            blocks = []
            for section, (start, end) in zip(documents, source_context_tokens(bodies), strict=True):
                blocks.append({"t": "RawBlock", "c": ["html", f"<!--{start}-->"]})
                blocks.extend(section["blocks"])
                blocks.append({"t": "RawBlock", "c": ["html", f"<!--{end}-->"]})
            document = {**document, "blocks": blocks}

        options = ["--from=json", "--to=html5", "--standalone", "--mathml", "--metadata=pagetitle:Manuscript"]
        if index is not None and prepared.bibliographies:
            options.append("--citeproc")
            for number, (_, body) in enumerate(prepared.bibliographies):
                bibliography = directory / f"bibliography-{number}.bib"
                bibliography.write_bytes(body)
                options.append(f"--bibliography={bibliography}")

        rendered = _pandoc(
            config, options, json.dumps(document).encode(), directory, deadline=deadline, output_limit=_MAX_HTML_BYTES
        ).decode()
        pages = list(zip(outputs, (rendered,), strict=True)) if index is None else []
        if index is not None:
            combined, split = split_canonical_html(rendered, bodies, byte_limit=_MAX_HTML_BYTES)
            pages = [(index, combined), *zip(outputs, split, strict=True)]
        destinations = {path: body for path, body in pages if path is not None}
        for page in destinations.values():
            parser = _ScriptlessHTML()
            parser.feed(page)
            parser.close()

        if not temporary_root.matches_path():
            raise RenderingError("Untrusted HTML temporary root changed before publication")
        profile.validate_output_tree(output_dir, allow_missing_root=True)
        write_root, write_identity = project_anchor if project_anchor is not None else (root, root_identity)
        for path, page_html in destinations.items():
            profile.validate_output(path)
            try:
                mode = stat.S_IMODE(path.lstat().st_mode)
            except FileNotFoundError:
                mode = 0o644
            atomic_write_text_confined(write_root, path, page_html, mode=mode, expected_root_identity=write_identity)

    return next(iter(destinations))
