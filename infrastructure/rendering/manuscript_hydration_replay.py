"""Reconstruct exact shared hydration bytes and every lexical token occurrence.

This is a deterministic transformation predicate. Variables are inputs, never
independently admitted research results. Original stage and domain custody are
separate requirements even when these bytes match.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import asdict, dataclass

from infrastructure.rendering.manuscript_injection import _TOKEN_RE


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

    def data(self) -> dict[str, object]:
        return {
            "source_sha256": hashlib.sha256(self.source).hexdigest(),
            "source_bytes": len(self.source),
            "output_sha256": hashlib.sha256(self.output).hexdigest(),
            "output_bytes": len(self.output),
            "occurrences": [asdict(row) for row in self.occurrences],
        }


def reconstruct_shared_hydration(source: bytes, variables: Mapping[str, str]) -> HydrationReconstruction:
    """Apply the actual writer token rule with Python text-reader newline semantics.

    No paths, selected occurrence list, status or original execution object are
    accepted. The full input is scanned in order. Values remain exact strings;
    a missing variable remains literal and is explicitly marked unresolved.
    """
    if not isinstance(source, bytes) or len(source) > 64 * 1024 * 1024:
        raise ValueError("hydration requires a bounded exact UTF-8 source body")
    if any(not isinstance(key, str) or not isinstance(value, str) for key, value in variables.items()):
        raise ValueError("shared hydration variables must retain exact string keys and values")
    text = source.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    # Raw offsets refer to the admitted bytes, before read_text's universal
    # newline conversion. This separate regex uses the same literal Source
    # token grammar; occurrences cannot be merged by equal key/value/body.
    raw_text = source.decode("utf-8")
    raw_matches = tuple(_TOKEN_RE.finditer(raw_text))
    matches = tuple(_TOKEN_RE.finditer(text))
    if len(raw_matches) != len(matches) or len(matches) > 10000:
        raise ValueError("hydration newline normalization changed lexical token membership")
    parts: list[str] = []
    rows = []
    cursor = 0
    raw_cursor = 0
    raw_bytes = 0
    output_bytes = 0
    for ordinal, (raw_match, match) in enumerate(zip(raw_matches, matches, strict=True), 1):
        prefix = text[cursor : match.start()]
        parts.append(prefix)
        output_bytes += len(prefix.encode())
        key = match.group(1)
        replacement = variables.get(key, match.group(0))
        start = raw_bytes + len(raw_text[raw_cursor : raw_match.start()].encode())
        end = start + len(raw_match.group(0).encode())
        replacement_bytes = replacement.encode()
        rows.append(
            HydrationOccurrence(
                ordinal,
                key,
                start,
                end,
                output_bytes,
                output_bytes + len(replacement_bytes),
                hashlib.sha256(replacement_bytes).hexdigest(),
                key in variables,
            )
        )
        parts.append(replacement)
        output_bytes += len(replacement_bytes)
        cursor = match.end()
        raw_cursor, raw_bytes = raw_match.end(), end
        if output_bytes > 64 * 1024 * 1024:
            raise ValueError("hydrated manuscript exceeds its complete byte ceiling")
    parts.append(text[cursor:])
    output = "".join(parts).encode()
    if len(output) > 64 * 1024 * 1024:
        raise ValueError("hydrated manuscript exceeds its complete byte ceiling")
    return HydrationReconstruction(source, output, tuple(rows))


def require_shared_hydration(source: bytes, variables: Mapping[str, str], consumed: bytes) -> HydrationReconstruction:
    """Refuse changed/omitted/reordered bytes and every unresolved real token."""
    result = reconstruct_shared_hydration(source, variables)
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
