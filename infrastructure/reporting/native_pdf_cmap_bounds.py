"""Bound actual CMap range expansion before native font-map construction."""

from __future__ import annotations

from typing import Any

from pdfminer.psparser import PSKeyword


def cmap_range_cost(tokens: list[Any], limit: int) -> tuple[int, int]:
    """Admit exact declared short ranges; inheritance remains unsupported.

    Return native mapping entries and output bytes, including implied values.
    Malformed sections cannot hide expansion behind native parser recovery.
    """
    mappings = text = 0
    index = 0
    while index < len(tokens):
        token = tokens[index]
        index += 1
        if not isinstance(token, PSKeyword):
            continue
        if token.name == b"usecmap":
            raise ValueError("native PDF inherited CMaps require bounded support")
        if token.name in {b"endbfrange", b"endcidrange"}:
            raise ValueError("native PDF CMap range expansion has an unmatched original terminator")
        if token.name not in {b"beginbfrange", b"begincidrange"}:
            continue
        closing = b"endbfrange" if token.name == b"beginbfrange" else b"endcidrange"
        rows = tokens[index - 2] if index >= 2 else None
        if type(rows) is not int or not 0 <= rows <= limit:
            raise ValueError("native PDF CMap range expansion has no finite declared rows")
        for _ in range(rows):
            if index + 2 >= len(tokens):
                raise ValueError("native PDF CMap range expansion has incomplete rows")
            first, last, destination = tokens[index : index + 3]
            index += 3
            if not isinstance(first, bytes) or not isinstance(last, bytes) or not 1 <= len(first) == len(last) <= 4:
                raise ValueError("native PDF CMap range expansion has unbounded source strings")
            start, end = int.from_bytes(first, "big"), int.from_bytes(last, "big")
            count = end - start + 1
            if not 1 <= count <= 65536 or mappings + count > limit:
                raise ValueError("native PDF CMap range expansion exceeds finite mapping budget")
            if closing == b"endcidrange":
                if type(destination) is not int or not 0 <= destination <= 65535 - count + 1:
                    raise ValueError("native PDF CMap CID range expansion is malformed or unbounded")
                output = count * len(first)
            elif isinstance(destination, bytes):
                if not 1 <= len(destination) <= 32:
                    raise ValueError("native PDF CMap range expansion has unbounded destination strings")
                if int.from_bytes(destination[-4:], "big") + count - 1 > 2**32 - 1:
                    raise ValueError("native PDF CMap range expansion overflows its native destination")
                output = count * len(destination)
            elif isinstance(destination, PSKeyword) and destination.name == b"[":
                output = 0
                for _ in range(count):
                    if (
                        index >= len(tokens)
                        or not isinstance(tokens[index], bytes)
                        or not 1 <= len(tokens[index]) <= 32
                    ):
                        raise ValueError("native PDF CMap range expansion has incomplete explicit destinations")
                    output += len(tokens[index])
                    index += 1
                if index >= len(tokens) or not isinstance(tokens[index], PSKeyword) or tokens[index].name != b"]":
                    raise ValueError("native PDF CMap range expansion has extra explicit destinations")
                index += 1
            else:
                raise ValueError("native PDF CMap range expansion destination is unsupported")
            mappings += count
            text += output
            if text > limit:
                raise ValueError("native PDF CMap range expansion exceeds finite output budget")
        if index >= len(tokens) or not isinstance(tokens[index], PSKeyword) or tokens[index].name != closing:
            raise ValueError("native PDF CMap range expansion rows differ from the original declaration")
        index += 1
    return mappings, text
