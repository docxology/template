"""Bind source-owned figure registry alternatives into tagged-PDF LaTeX."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._figure_alt_registry import (
    FigureAltRecord,
    FigureAltRegistry,
    rendered_figure_filename,
    require_record_alt,
)
from infrastructure.rendering._pdf_title_page_latex import _latex_graphic_alt_text

_INCLUDE_GRAPHICS = r"\includegraphics"
_FIGURE_BEGIN = re.compile(r"\\begin\{(figure\*?)\}")
_FIGURE_LABEL = re.compile(r"\\label\s*\{(fig:[^{}]+)\}")


@dataclass(frozen=True)
class _FigureContext:
    """One enclosing LaTeX figure and its optional exact registry label."""

    start: int
    end: int
    label: str | None


def apply_pdf_figure_alts(
    tex_content: str,
    registry_path: Path,
    *,
    tagged_pdf: bool,
) -> str:
    """Replace Pandoc caption-derived body-image alt with exact registry text.

    Untagged PDF output is intentionally unchanged: an ``alt`` option in
    ordinary graphicx output is not evidence of a tagged or PDF/UA document.
    """
    if not tagged_pdf:
        return tex_content
    registry = FigureAltRegistry.load_optional(registry_path)

    figure_contexts = _figure_contexts(tex_content)
    replacements: list[tuple[int, int, str]] = []
    cursor = 0
    while True:
        command_start = tex_content.find(_INCLUDE_GRAPHICS, cursor)
        if command_start < 0:
            break
        after_command = command_start + len(_INCLUDE_GRAPHICS)
        option_start = _skip_space(tex_content, after_command)
        option_end: int | None = None
        if option_start < len(tex_content) and tex_content[option_start] == "[":
            option_end = _balanced_square_end(tex_content, option_start)
            path_start = _skip_space(tex_content, option_end)
        else:
            path_start = option_start
        if path_start >= len(tex_content) or tex_content[path_start] != "{":
            cursor = after_command
            continue
        path_end = _balanced_brace_end(tex_content, path_start)
        raw_path = _unwrap_path(tex_content[path_start + 1 : path_end - 1])
        filename = rendered_figure_filename(raw_path)
        option_body = tex_content[option_start + 1 : option_end - 1] if option_end is not None else ""
        figure = _enclosing_figure(figure_contexts, command_start)
        record = _exact_registry_record(
            registry,
            label=figure.label if figure is not None else None,
            filename=filename,
            inside_figure=figure is not None,
        )
        if record is not None:
            alt_text = require_record_alt(record, rendered_target=str(registry.path))
            serialized = _latex_graphic_alt_text(alt_text)
            if option_end is None:
                replacements.append((path_start, path_start, f"[alt={{{serialized}}}]"))
            else:
                option_body = tex_content[option_start + 1 : option_end - 1]
                updated_options = _replace_or_append_alt(option_body, serialized)
                replacements.append((option_start + 1, option_end - 1, updated_options))
        elif figure is None and registry.by_filename(filename):
            if not _has_nonblank_authored_alt(option_body):
                # Pandoc omits or blanks the alt option for an explicitly
                # decorative reuse. Keep that authored semantic without
                # consuming the canonical labelled figure's registry record.
                if option_end is None:
                    replacements.append((path_start, path_start, "[alt={}]"))
                else:
                    replacements.append((option_start + 1, option_end - 1, _replace_or_append_alt(option_body, "")))
        elif not _has_nonblank_authored_alt(option_body):
            raise RenderingError(
                "Tagged-PDF graphic is missing nonblank authored alt text",
                context={
                    "figure": (figure.label or "unlabelled") if figure is not None else "outside-figure",
                    "path": raw_path,
                    "registry": str(registry.path),
                },
            )
        cursor = path_end

    for start, end, replacement in reversed(replacements):
        tex_content = tex_content[:start] + replacement + tex_content[end:]
    return tex_content


def _figure_contexts(content: str) -> tuple[_FigureContext, ...]:
    """Locate non-nested figure environments and their exact fig:* labels."""

    contexts: list[_FigureContext] = []
    cursor = 0
    while match := _FIGURE_BEGIN.search(content, cursor):
        environment = match.group(1)
        end_token = rf"\end{{{environment}}}"
        end_start = content.find(end_token, match.end())
        if end_start < 0:
            raise RenderingError("Unterminated LaTeX figure environment while binding figure alt text")
        nested = _FIGURE_BEGIN.search(content, match.end(), end_start)
        if nested is not None:
            raise RenderingError("Nested LaTeX figure environments are ambiguous for figure alt text")
        end = end_start + len(end_token)
        labels = _FIGURE_LABEL.findall(content, match.end(), end_start)
        if len(set(labels)) > 1:
            raise RenderingError(
                "LaTeX figure has multiple fig:* labels while binding figure alt text",
                context={"labels": sorted(set(labels))},
            )
        contexts.append(_FigureContext(start=match.start(), end=end, label=labels[0] if labels else None))
        cursor = end
    return tuple(contexts)


def _enclosing_figure(contexts: tuple[_FigureContext, ...], offset: int) -> _FigureContext | None:
    return next((context for context in contexts if context.start <= offset < context.end), None)


def _exact_registry_record(
    registry: FigureAltRegistry,
    *,
    label: str | None,
    filename: str | None,
    inside_figure: bool,
) -> FigureAltRecord | None:
    """Return only a registry record whose label and image path both match."""

    path_records = registry.by_filename(filename)
    if len(path_records) > 1:
        raise RenderingError(
            f"Tagged-PDF figure path maps to multiple registry records: {filename}",
            context={"path": filename, "registry": str(registry.path)},
        )
    if label is None:
        if inside_figure and path_records:
            raise RenderingError(
                "Tagged-PDF figure label/path mismatch: registry path appears in an unlabelled figure",
                context={"path": filename, "registry": str(registry.path)},
            )
        return None

    label_record = registry.by_label(label)
    if label_record is None:
        if path_records:
            raise RenderingError(
                f"Tagged-PDF figure label/path mismatch: {label} is not the registry owner of {filename}",
                context={"figure": label, "path": filename, "registry": str(registry.path)},
            )
        return None
    if filename != label_record.filename:
        raise RenderingError(
            f"Tagged-PDF figure label/path mismatch: {label} does not render {label_record.filename}",
            context={"figure": label, "path": filename, "registry": str(registry.path)},
        )
    return label_record


def _has_nonblank_authored_alt(options: str) -> bool:
    match = _top_level_alt_assignment(options)
    if match is None:
        return False
    start, end = match
    assignment = options[start:end]
    _separator, _equals, raw_value = assignment.partition("=")
    value = raw_value.strip()
    if value.startswith("{") and value.endswith("}"):
        value = value[1:-1]
    return bool(value.strip())


def _skip_space(content: str, start: int) -> int:
    while start < len(content) and content[start].isspace():
        start += 1
    return start


def _balanced_square_end(content: str, start: int) -> int:
    square_depth = 1
    brace_depth = 0
    cursor = start + 1
    while cursor < len(content):
        char = content[cursor]
        if char == "{":
            brace_depth += 1
        elif char == "}" and brace_depth:
            brace_depth -= 1
        elif brace_depth == 0 and char == "[":
            square_depth += 1
        elif brace_depth == 0 and char == "]":
            square_depth -= 1
            if square_depth == 0:
                return cursor + 1
        cursor += 1
    raise RenderingError("Unterminated includegraphics option list while binding figure alt text")


def _balanced_brace_end(content: str, start: int) -> int:
    depth = 1
    cursor = start + 1
    while cursor < len(content):
        char = content[cursor]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return cursor + 1
        cursor += 1
    raise RenderingError("Unterminated includegraphics path while binding figure alt text")


def _unwrap_path(raw_path: str) -> str:
    path = raw_path.strip()
    marker = r"\detokenize{"
    if path.startswith(marker) and path.endswith("}"):
        path = path[len(marker) : -1]
    return path.replace(r"\_", "_")


def _replace_or_append_alt(options: str, serialized_alt: str) -> str:
    match = _top_level_alt_assignment(options)
    replacement = f"alt={{{serialized_alt}}}"
    if match is None:
        stripped = options.rstrip()
        separator = "," if stripped else ""
        return stripped + separator + replacement + options[len(stripped) :]
    start, end = match
    return options[:start] + replacement + options[end:]


def _top_level_alt_assignment(options: str) -> tuple[int, int] | None:
    brace_depth = 0
    cursor = 0
    while cursor < len(options):
        char = options[cursor]
        if char == "{":
            brace_depth += 1
            cursor += 1
            continue
        if char == "}" and brace_depth:
            brace_depth -= 1
            cursor += 1
            continue
        if brace_depth == 0:
            match = re.match(r"alt\s*=\s*", options[cursor:], flags=re.IGNORECASE)
            if match is not None and (cursor == 0 or options[cursor - 1] in {",", " "}):
                value_start = cursor + match.end()
                if value_start < len(options) and options[value_start] == "{":
                    value_end = _balanced_brace_end(options, value_start)
                else:
                    comma = options.find(",", value_start)
                    value_end = len(options) if comma < 0 else comma
                return cursor, value_end
        cursor += 1
    return None
