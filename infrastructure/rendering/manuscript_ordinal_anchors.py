"""Exact ordinal anchors in held bytes and a complete annotated Pandoc AST.

These pure transforms supply DATA, never parser, scientific or native authority.
Only known anchor nodes/bytes are removed. Every remaining AST field is compared
with the enclosing caller's genuinely admitted unannotated parser result.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

MAX_BYTES = 4 * 1024 * 1024
MAX_OCCURRENCES = 10000
MAX_NODES = 100000


@dataclass(frozen=True)
class OrdinalAnchor:
    """One actual input occurrence, distinct even when payloads are identical."""

    input_index: int
    ordinal: int
    key: str
    first: int
    last: int
    payload_sha256: str
    start: str
    end: str
    carrier_first: int
    carrier_last: int
    prefix: bytes
    suffix: bytes
    boundary_kind: str
    start_input: str
    end_input: str


@dataclass(frozen=True)
class _Markers:
    tokens: tuple[str, ...]


@dataclass(frozen=True)
class _Site:
    token: str
    path: tuple[str | int, ...]
    offset: int
    kind: str


def _pipe_table_carrier(body: bytes, first: int, last: int) -> tuple[int, int] | None:
    """Frame only a complete unnested pipe table, without changing its rows.

    This is a finite carrier placement check, not a Markdown interpretation.
    Actual parser equivalence must still prove exactly one containing Table.
    Unsupported framing cannot acquire a table or scalar endpoint.
    """
    lines = body.splitlines(keepends=True)
    starts, cursor = [], 0
    for line in lines:
        starts.append(cursor)
        cursor += len(line)
    touched = [
        index for index, (start, line) in enumerate(zip(starts, lines)) if start < last and start + len(line) > first
    ]
    if not touched or not any(lines[index].startswith(b"|") for index in touched):
        return None
    low, high = touched[0], touched[-1]
    if not all(lines[index].startswith(b"|") for index in touched):
        raise ValueError("ordinal occurrence crosses an unsupported pipe-table boundary")
    while low > 0 and lines[low - 1].startswith(b"|"):
        low -= 1
    while high + 1 < len(lines) and lines[high + 1].startswith(b"|"):
        high += 1
    rows = [line.rstrip(b"\r\n").rstrip(b" \t") for line in lines[low : high + 1]]
    if (
        len(rows) < 3
        or len(rows) > 1000
        or any(not row.endswith(b"|") for row in rows)
        or re.fullmatch(rb"\|(?:[ \t]*:?-+:?[ \t]*\|)+", rows[1]) is None
        or len({row.count(b"|") for row in rows}) != 1
    ):
        raise ValueError("ordinal carrier requires complete fixed pipe-table framing")
    # Source's one-line attached caption remains inside the containing role.
    caption = high + 1
    while caption < len(lines) and not lines[caption].strip():
        caption += 1
    if caption < len(lines) and lines[caption].startswith(b": "):
        high = caption
    end = starts[high] + len(lines[high].rstrip(b"\r\n"))
    if not starts[low] <= first < last <= end:
        raise ValueError("ordinal table carrier no longer contains the actual selected payload")
    return starts[low], end


def annotate_manuscript_ordinals(
    bodies: tuple[bytes, ...], occurrences: tuple[tuple[int, int, str, int, int, str], ...]
) -> tuple[tuple[bytes, ...], tuple[OrdinalAnchor, ...]]:
    """Insert anchors only at exact held hydration byte boundaries.

    Each occurrence is (input index, authored ordinal, key, start, end, SHA).
    No occurrence is selected by searching for a payload or matching a number.
    """
    if (
        not bodies
        or any(not isinstance(body, bytes) for body in bodies)
        or sum(map(len, bodies)) > MAX_BYTES
        or len(occurrences) > MAX_OCCURRENCES
    ):
        raise ValueError("ordinal annotation requires the complete bounded held manuscript")
    for body in bodies:
        body.decode("utf-8")
    identity = hashlib.sha256()
    for body in bodies:
        identity.update(len(body).to_bytes(8, "big"))
        identity.update(body)
    identity.update(json.dumps(occurrences, separators=(",", ":")).encode())
    prefix = "<!--template-ordinal-" + identity.hexdigest()[:32] + "-"
    if any(prefix.encode() in body for body in bodies):
        raise ValueError("actual Source already contains the selected ordinal anchor namespace")
    anchors: list[OrdinalAnchor] = []
    identities: set[tuple[int, int, str]] = set()
    edits: dict[int, list[tuple[int, str]]] = {}
    intervals: dict[int, list[tuple[int, int]]] = {}
    for position, (index, ordinal, key, first, last, digest) in enumerate(occurrences, 1):
        if (
            type(index) is not int
            or not 0 <= index < len(bodies)
            or type(ordinal) is not int
            or ordinal < 1
            or not isinstance(key, str)
            or not key
            or type(first) is not int
            or type(last) is not int
            or not 0 <= first < last <= len(bodies[index])
            or hashlib.sha256(bodies[index][first:last]).hexdigest() != digest
            or (index, ordinal, key) in identities
        ):
            raise ValueError("ordinal annotation changed a genuine nonempty hydration occurrence")
        bodies[index][:first].decode("utf-8")
        bodies[index][:last].decode("utf-8")
        identities.add((index, ordinal, key))
        start, end = prefix + str(position) + "-start-->", prefix + str(position) + "-end-->"
        table = _pipe_table_carrier(bodies[index], first, last)
        carrier_first, carrier_last = table if table is not None else (first, last)
        start_input, end_input = (start + "\n", "\n" + end) if table is not None else (start, end)
        anchors.append(
            OrdinalAnchor(
                index,
                ordinal,
                key,
                first,
                last,
                digest,
                start,
                end,
                carrier_first,
                carrier_last,
                bodies[index][carrier_first:first],
                bodies[index][last:carrier_last],
                "containing-table" if table is not None else "exact-occurrence",
                start_input,
                end_input,
            )
        )
        edits.setdefault(index, []).extend(((carrier_first, start_input), (carrier_last, end_input)))
        intervals.setdefault(index, []).append((first, last))
    for rows in intervals.values():
        ordered = sorted(rows)
        if any(left[1] > right[0] for left, right in zip(ordered, ordered[1:])):
            raise ValueError("actual hydration occurrences overlap")
    result = []
    for index, body in enumerate(bodies):
        marker_rows = sorted(edits.get(index, ()), key=lambda row: (row[0], "-start-->" in row[1]))
        parts: list[bytes] = []
        cursor = 0
        for offset, marker in marker_rows:
            parts.extend((body[cursor:offset], marker.encode()))
            cursor = offset
        parts.append(body[cursor:])
        result.append(b"".join(parts))
    if sum(map(len, result)) > 2 * MAX_BYTES:
        raise ValueError("annotated manuscript exceeds its finite byte ceiling")
    return tuple(result), tuple(anchors)


def require_unannotated_parser_bytes(
    annotated: bytes, actual: bytes, anchors: tuple[OrdinalAnchor, ...]
) -> tuple[tuple[int, int], ...]:
    """Require full byte equivalence after deleting only exact unique anchors."""
    text = annotated.decode("utf-8")
    tokens = [token for anchor in anchors for token in (anchor.start_input, anchor.end_input)]
    if any(text.count(token) != 1 for token in tokens):
        raise ValueError("Source combine/preprocess omitted or duplicated an actual ordinal anchor")
    boundaries: dict[str, int] = {}
    parts = []
    cursor = 0
    output = 0
    for first, last, token in sorted((text.index(token), text.index(token) + len(token), token) for token in tokens):
        prefix = text[cursor:first].encode()
        parts.append(prefix)
        output += len(prefix)
        boundaries[token] = output
        cursor = last
    parts.append(text[cursor:].encode())
    if b"".join(parts) != actual:
        raise ValueError("ordinal annotation changed the complete actual parser input")
    pairs = []
    for anchor in anchors:
        carrier_first, carrier_last = boundaries[anchor.start_input], boundaries[anchor.end_input]
        first, last = carrier_first + len(anchor.prefix), carrier_last - len(anchor.suffix)
        if (
            not carrier_first <= first < last <= carrier_last
            or actual[carrier_first:first] != anchor.prefix
            or actual[last:carrier_last] != anchor.suffix
            or hashlib.sha256(actual[first:last]).hexdigest() != anchor.payload_sha256
        ):
            raise ValueError("Source preprocessing changed the held payload or its exact table-carrier framing")
        pairs.append((first, last))
    if any(first >= last for first, last in pairs):
        raise ValueError("Source transform removed or inverted the selected visible occurrence")
    return tuple(pairs)


def _document(body: bytes) -> dict[str, Any]:
    if not body or len(body) > 2 * MAX_BYTES:
        raise ValueError("ordinal parser AST exceeds its finite byte ceiling")

    def fields(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in rows:
            if key in result:
                raise ValueError("ordinal parser AST repeats a field")
            result[key] = value
        return result

    result = json.loads(body, object_pairs_hook=fields)
    if (
        not isinstance(result, dict)
        or set(result) != {"pandoc-api-version", "meta", "blocks"}
        or not isinstance(result["blocks"], list)
        or not isinstance(result["meta"], dict)
        or not isinstance(result["pandoc-api-version"], list)
        or not result["pandoc-api-version"]
        or any(type(value) is not int or value < 0 for value in result["pandoc-api-version"])
    ):
        raise ValueError("ordinal replay requires the complete actual Pandoc AST envelope")
    return result


def require_complete_ordinal_ast_equivalence(
    annotated: bytes, actual: bytes, anchors: tuple[OrdinalAnchor, ...]
) -> tuple[dict[str, Any], ...]:
    """Desugar fixed anchors, compare every field, retain exact AST boundaries.

    Literal anchors inside Math/Code stay tied to those whole Source nodes.
    Changed attributes, metadata, parser transforms and unknown fields refuse.
    Native roles are qualified separately by their existing complete witnesses.
    """
    tokens = {token for anchor in anchors for token in (anchor.start, anchor.end)}
    sites: list[_Site] = []
    visited = 0

    def literal(text: str) -> tuple[str, list[tuple[str, int]]]:
        present = [(text.index(token), token) for token in tokens if token in text]
        if any(text.count(token) != 1 for _, token in present):
            raise ValueError("annotated AST repeated an ordinal anchor")
        result = []
        offsets = []
        cursor = 0
        length = 0
        for position, token in sorted(present):
            result.append(text[cursor:position])
            length += position - cursor
            offsets.append((token, length))
            cursor = position + len(token)
        result.append(text[cursor:])
        return "".join(result), offsets

    def walk(value: Any, path: tuple[str | int, ...]) -> Any:
        nonlocal visited
        visited += 1
        if visited > MAX_NODES or len(path) > 100:
            raise ValueError("ordinal AST exceeds its finite node/depth ceiling")
        if isinstance(value, dict):
            tag = value.get("t")
            content = value.get("c")
            field: tuple[str | int, ...] | None = None
            text: str
            if tag == "Str" and isinstance(content, str):
                field = ("c",)
                text = content
            elif tag in {"Math", "Code", "CodeBlock", "RawInline", "RawBlock"} and (
                isinstance(content, list) and len(content) == 2 and isinstance(content[1], str)
            ):
                field = ("c", 1)
                text = content[1]
                paired_content = content
            if field is not None:
                clean, positions = literal(text)
                marker_only = not clean
                if tag == "RawBlock" and positions and clean and not clean.replace("\n", ""):
                    ordered = [token for token, _ in positions]
                    framed = {
                        token
                        for anchor in anchors
                        if anchor.boundary_kind == "containing-table"
                        for token in (anchor.start, anchor.end)
                    }
                    marker_only = set(ordered) <= framed and paired_content[1] in {
                        "\n".join(ordered),
                        "\n".join(ordered) + "\n",
                    }
                if tag in {"RawInline", "RawBlock"} and paired_content[0] == "html" and positions and marker_only:
                    if set(value) != {"t", "c"}:
                        raise ValueError("ordinal anchor node changed an unmodeled actual AST field")
                    return _Markers(tuple(token for token, _ in positions))
                clone = dict(value)
                if field == ("c",):
                    clone["c"] = clean
                else:
                    clone["c"] = [paired_content[0], clean]
                sites.extend(_Site(token, (*path, *field), offset, "literal-codepoint") for token, offset in positions)
                # No arbitrary field containing an anchor may be normalized.
                return {key: walk(child, (*path, key)) for key, child in clone.items()}
            return {key: walk(child, (*path, key)) for key, child in value.items()}
        if isinstance(value, list):
            result: list[Any] = []
            pending: list[str] = []
            for child in value:
                before = len(sites)
                row = walk(child, (*path, len(result)))
                if isinstance(row, _Markers):
                    pending.extend(row.tokens)
                    continue
                previous = result[-1] if result else None
                left = isinstance(previous, dict) and previous.get("t") == "Str" and set(previous) == {"t", "c"}
                right = isinstance(row, dict) and row.get("t") == "Str" and set(row) == {"t", "c"}
                if pending and isinstance(previous, dict) and left and right:
                    length = len(previous["c"])
                    target = (*path, len(result) - 1, "c")
                    sites.extend(_Site(token, target, length, "literal-codepoint") for token in pending)
                    for index in range(before, len(sites) - len(pending)):
                        site = sites[index]
                        if site.path != (*path, len(result), "c"):
                            raise ValueError("ordinal Str bridge changed an unexpected nested field")
                        sites[index] = _Site(site.token, target, site.offset + length, site.kind)
                    previous["c"] += row["c"]
                else:
                    if pending:
                        if left and isinstance(previous, dict):
                            target, offset, kind = (
                                (*path, len(result) - 1, "c"),
                                len(previous["c"]),
                                "literal-codepoint",
                            )
                        elif right:
                            target, offset, kind = (*path, len(result), "c"), 0, "literal-codepoint"
                        else:
                            target, offset, kind = path, len(result), "ordered-list-boundary"
                        sites.extend(_Site(token, target, offset, kind) for token in pending)
                    result.append(row)
                pending.clear()
            if pending:
                last = result[-1] if result else None
                if isinstance(last, dict) and last.get("t") == "Str" and set(last) == {"t", "c"}:
                    target, offset, kind = (*path, len(result) - 1, "c"), len(last["c"]), "literal-codepoint"
                else:
                    target, offset, kind = path, len(result), "ordered-list-boundary"
                sites.extend(_Site(token, target, offset, kind) for token in pending)
            return result
        return value

    original = _document(actual)
    rebuilt = walk(_document(annotated), ())
    if json.dumps(rebuilt, sort_keys=True, separators=(",", ":"), allow_nan=False) != json.dumps(
        original, sort_keys=True, separators=(",", ":"), allow_nan=False
    ):
        raise ValueError("ordinal replay changed the complete original AST fields/order/tokens")
    by_token: dict[str, list[_Site]] = {}
    for site in sites:
        by_token.setdefault(site.token, []).append(site)
    if set(by_token) != tokens:
        raise ValueError("complete annotated AST omitted or repeated an actual ordinal anchor")

    # Pandoc's modern Figure stores the same caption once visibly and once as
    # its single Image alternative. Both complete roles remain in the AST.
    caption_aliases: list[tuple[tuple[str | int, ...], tuple[str | int, ...]]] = []

    def aliases(value: Any, path: tuple[str | int, ...]) -> None:
        if isinstance(value, dict):
            if value.get("t") == "Figure":
                content = value.get("c")
                if isinstance(content, list) and len(content) == 3:
                    caption, blocks = content[1], content[2]
                    if (
                        isinstance(caption, list)
                        and len(caption) == 2
                        and caption[0] is None
                        and isinstance(caption[1], list)
                        and len(caption[1]) == 1
                        and isinstance(blocks, list)
                        and len(blocks) == 1
                        and isinstance(caption[1][0], dict)
                        and caption[1][0].get("t") in {"Plain", "Para"}
                        and set(caption[1][0]) == {"t", "c"}
                        and isinstance(blocks[0], dict)
                        and blocks[0].get("t") in {"Plain", "Para"}
                        and set(blocks[0]) == {"t", "c"}
                        and isinstance(blocks[0]["c"], list)
                        and len(blocks[0]["c"]) == 1
                    ):
                        image = blocks[0]["c"][0]
                        if (
                            isinstance(image, dict)
                            and set(image) == {"t", "c"}
                            and image["t"] == "Image"
                            and isinstance(image["c"], list)
                            and len(image["c"]) == 3
                            and json.dumps(caption[1][0]["c"], sort_keys=True, allow_nan=False)
                            == json.dumps(image["c"][1], sort_keys=True, allow_nan=False)
                        ):
                            caption_aliases.append(((*path, "c", 1, 1, 0, "c"), (*path, "c", 2, 0, "c", 0, "c", 1)))
            for key, child in value.items():
                aliases(child, (*path, key))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                aliases(child, (*path, index))

    aliases(original, ())

    def selected_sites(token: str) -> tuple[_Site, tuple[_Site, ...]]:
        rows = by_token[token]
        for visible, alternative in caption_aliases:
            primary = [row for row in rows if row.path[: len(visible)] == visible]
            copied = [row for row in rows if row.path[: len(alternative)] == alternative]
            if primary or copied:
                if (
                    len(rows) != 2
                    or len(primary) != 1
                    or len(copied) != 1
                    or primary[0].path[len(visible) :] != copied[0].path[len(alternative) :]
                    or primary[0].offset != copied[0].offset
                    or primary[0].kind != copied[0].kind
                ):
                    raise ValueError("ordinal caption must retain both exact complete Figure/Image alias sites")
                return primary[0], (copied[0],)
        if len(rows) != 1:
            raise ValueError("complete annotated AST repeated a nonalias ordinal anchor")
        return rows[0], ()

    def data(site: _Site, kind: str | None = None) -> dict[str, Any]:
        return {"ast_path": list(site.path), "offset": site.offset, "kind": kind or site.kind}

    result = []
    for anchor in anchors:
        start, start_aliases = selected_sites(anchor.start)
        end, end_aliases = selected_sites(anchor.end)
        container = None
        kind = None
        if anchor.boundary_kind == "containing-table":
            if (
                start.path != end.path
                or start.kind != "ordered-list-boundary"
                or end.kind != "ordered-list-boundary"
                or end.offset != start.offset + 1
                or start_aliases
                or end_aliases
            ):
                raise ValueError("ordinal table carriers must enclose exactly one complete actual Table")
            parent: Any = original
            for component in start.path:
                parent = parent[component]
            if not isinstance(parent, list) or parent[start.offset].get("t") != "Table":
                raise ValueError("ordinal table carrier did not retain its genuine complete Table role")
            container = [*start.path, start.offset]
            kind = "containing-table-boundary"
        row = {
            "input_index": anchor.input_index,
            "ordinal": anchor.ordinal,
            "key": anchor.key,
            "payload_sha256": anchor.payload_sha256,
            "boundary_kind": anchor.boundary_kind,
            "input_payload_byte_range": [anchor.first, anchor.last],
            "input_carrier_byte_range": [anchor.carrier_first, anchor.carrier_last],
            "container_ast_path": container,
            "start": data(start, kind),
            "end": data(end, kind),
        }
        if start_aliases or end_aliases:
            row["caption_aliases"] = {
                "start": [data(site) for site in start_aliases],
                "end": [data(site) for site in end_aliases],
            }
        result.append(row)
    return tuple(result)
