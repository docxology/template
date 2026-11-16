"""Reconstruct exact shared hydration bytes and every lexical token occurrence.

This is a deterministic transformation predicate. Variables are inputs, never
independently admitted research results. Original stage and domain custody are
separate requirements even when these bytes match.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from enum import Enum

from infrastructure.core.files.portability import _MACHINE_HOME_RE, sanitize_machine_local_text
from infrastructure.rendering.manuscript_injection import (
    _HTML_OUTPUT_ATTR_RE,
    _MARKDOWN_OUTPUT_TARGET_RE,
    _TOKEN_RE,
)


class SharedHydrationWriter(Enum):
    """Actual Source writer routes, selected before examining consumed bytes."""

    RESOLVED_TREE = "write_resolved_manuscript_tree"
    HYDRATED_UPPERCASE_TREE = "hydrate_manuscript_tree-uppercase-rebased"
    HYDRATED_WORD_TREE = "hydrate_manuscript_tree-word-tokens"


@dataclass(frozen=True)
class HydrationOccurrence:
    """One exact source occurrence, retaining repeated equal tokens separately."""

    ordinal: int
    key: str
    source_start_byte: int
    source_end_byte: int
    output_start_byte: int
    output_end_byte: int
    replacement_sha256: str
    resolved: bool


@dataclass(frozen=True)
class HydrationReconstruction:
    """Held bytes and the independently computed complete occurrence mapping."""

    source: bytes
    output: bytes
    occurrences: tuple[HydrationOccurrence, ...]
    writer: SharedHydrationWriter

    def data(self) -> dict[str, object]:
        return {
            "writer": self.writer.value,
            "source_sha256": hashlib.sha256(self.source).hexdigest(),
            "source_bytes": len(self.source),
            "output_sha256": hashlib.sha256(self.output).hexdigest(),
            "output_bytes": len(self.output),
            "occurrences": [asdict(row) for row in self.occurrences],
        }


def _rewrite_spans(
    text: str, spans: list[tuple[int, int]], edits: list[tuple[int, int, str]]
) -> tuple[str, list[tuple[int, int]]]:
    """Map complete edits, including a home prefix crossing a token boundary.

    A nonempty occurrence owns its complete resulting interval. If one edit
    consumes several occurrences their intervals can overlap; native ordinal
    annotation must still refuse overlapping ownership. Empty replacements
    remain empty and cannot acquire authored bytes by normalization.
    """
    positions = sorted({point for span in spans for point in span})
    bounds: dict[int, tuple[int, int]] = {}
    point = cursor = delta = 0
    parts: list[str] = []
    for first, last, replacement in edits:
        if not cursor <= first < last <= len(text):
            raise ValueError("hydration rewrite overlaps or escapes its complete input")
        while point < len(positions) and positions[point] <= first:
            position = positions[point]
            bounds[position] = (position + delta, position + delta)
            point += 1
        while point < len(positions) and positions[point] < last:
            bounds[positions[point]] = (first + delta, first + delta + len(replacement))
            point += 1
        parts.extend((text[cursor:first], replacement))
        cursor = last
        delta += len(replacement) - (last - first)
    while point < len(positions):
        position = positions[point]
        bounds[position] = (position + delta, position + delta)
        point += 1
    parts.append(text[cursor:])
    return "".join(parts), [
        (bounds[first][0], bounds[last][1] if first != last else bounds[first][0]) for first, last in spans
    ]


def reconstruct_shared_hydration(
    source: bytes, variables: Mapping[str, str], *, writer: SharedHydrationWriter
) -> HydrationReconstruction:
    """Rebuild one explicit actual writer, never choose a rule by output equality.

    Legacy read_text converts authored newlines and rebases destination links.
    Ownership-aware hydration decodes raw bytes and normalizes home prefixes
    after the Source-selected substitution callback (and its optional rebasing).
    Authored bytes, hashes and raw occurrence positions always remain original.
    """
    if not isinstance(source, bytes) or len(source) > 64 * 1024 * 1024:
        raise ValueError("hydration requires a bounded exact UTF-8 source body")
    if not isinstance(writer, SharedHydrationWriter):
        raise ValueError("hydration requires its actual Source-selected writer route")
    if any(not isinstance(key, str) or not isinstance(value, str) for key, value in variables.items()):
        raise ValueError("shared hydration variables must retain exact string keys and values")
    raw_text = source.decode("utf-8")
    text = (
        raw_text.replace("\r\n", "\n").replace("\r", "\n")
        if writer is SharedHydrationWriter.RESOLVED_TREE else raw_text
    )
    # The literature callbacks use their genuine word-token grammar; the old
    # shared writer and AutoResearch callback use the uppercase Source grammar.
    pattern = re.compile(r"\{\{(\w+)\}\}") if writer is SharedHydrationWriter.HYDRATED_WORD_TREE else _TOKEN_RE
    raw_matches, matches = tuple(pattern.finditer(raw_text)), tuple(pattern.finditer(text))
    if len(raw_matches) != len(matches) or len(matches) > 10000:
        raise ValueError("hydration newline normalization changed lexical token membership")
    parts: list[str] = []
    spans: list[tuple[int, int]] = []
    identities: list[tuple[int, str, int, int, bool]] = []
    cursor = raw_cursor = raw_bytes = output_chars = output_bytes = 0
    for ordinal, (raw_match, match) in enumerate(zip(raw_matches, matches, strict=True), 1):
        prefix = text[cursor : match.start()]
        key = match.group(1)
        replacement = variables.get(key, match.group(0))
        start = raw_bytes + len(raw_text[raw_cursor : raw_match.start()].encode())
        end = start + len(raw_match.group(0).encode())
        parts.extend((prefix, replacement))
        output_chars += len(prefix)
        spans.append((output_chars, output_chars + len(replacement)))
        identities.append((ordinal, key, start, end, key in variables))
        output_chars += len(replacement)
        output_bytes += len(prefix.encode()) + len(replacement.encode())
        if output_bytes > 64 * 1024 * 1024:
            raise ValueError("hydrated manuscript exceeds its complete byte ceiling")
        cursor, raw_cursor, raw_bytes = match.end(), raw_match.end(), end
    parts.append(text[cursor:])
    text = "".join(parts)
    if len(text.encode()) > 64 * 1024 * 1024:
        raise ValueError("hydrated manuscript exceeds its complete byte ceiling")
    if writer is not SharedHydrationWriter.HYDRATED_WORD_TREE:
        for link_pattern in (_MARKDOWN_OUTPUT_TARGET_RE, _HTML_OUTPUT_ATTR_RE):
            text, spans = _rewrite_spans(
                text, spans,
                [(match.end("open") + 3, match.start("rest"), "") for match in link_pattern.finditer(text)],
            )
    if writer is not SharedHydrationWriter.RESOLVED_TREE:
        text, spans = _rewrite_spans(
            text, spans,
            [(match.start(), match.end(), sanitize_machine_local_text(match.group()))
             for match in _MACHINE_HOME_RE.finditer(text)],
        )
    output = text.encode()
    if len(output) > 64 * 1024 * 1024:
        raise ValueError("hydrated manuscript exceeds its complete byte ceiling")
    offsets: dict[int, int] = {}
    cursor = byte_count = 0
    for position in sorted({point for span in spans for point in span}):
        byte_count += len(text[cursor:position].encode())
        offsets[position] = byte_count
        cursor = position
    rows = tuple(
        HydrationOccurrence(
            ordinal, key, first, last, offsets[start], offsets[end],
            hashlib.sha256(output[offsets[start]:offsets[end]]).hexdigest(), resolved,
        )
        for (ordinal, key, first, last, resolved), (start, end) in zip(identities, spans, strict=True)
    )
    return HydrationReconstruction(source, output, rows, writer)


def require_shared_hydration(
    source: bytes, variables: Mapping[str, str], consumed: bytes, *, writer: SharedHydrationWriter
) -> HydrationReconstruction:
    """Refuse changed/omitted/reordered bytes and every unresolved real token."""
    result = reconstruct_shared_hydration(source, variables, writer=writer)
    if any(not row.resolved for row in result.occurrences):
        raise ValueError("native consumed shared hydration retains an unresolved source token")
    if result.output != consumed:
        raise ValueError("native consumed manuscript differs from exact shared source hydration")
    return result


def combine_held_manuscripts(bodies: tuple[bytes, ...], *, separator: str) -> bytes:
    """Reconstruct the writer's ordered rstrip/newline/join/BOM composition.

    The caller chooses the separator from the actual Source algorithm, never
    from a receipt's arbitrary string. Empty sections remain ordered members.
    """
    if not bodies or any(not isinstance(body, bytes) for body in bodies) or sum(map(len, bodies)) > 64 * 1024 * 1024:
        raise ValueError("composition requires the complete nonempty held input roster")
    parts = []
    for index, body in enumerate(bodies):
        text = body.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
        parts.append(text.rstrip() + "\n")
        if index < len(bodies) - 1 and separator:
            parts.append(separator)
    combined = "\n\n".join(parts).lstrip("\n\r").removeprefix("\ufeff")
    if not combined.strip():
        raise ValueError("complete composed manuscript is empty")
    return combined.encode()
