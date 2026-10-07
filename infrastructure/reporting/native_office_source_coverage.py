"""Independent scientific occurrence accounting; inventory alone never admits layout.

Every occurrence needs a native witness even when an independently rebuilt
same-format reference happens to equal the candidate. Unsupported raw content
and writer canonicalizations remain visible obligations.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

KINDS = frozenset({"Math", "Table", "Cite", "Image", "RawBlock", "RawInline"})
MAX_AST_BYTES = 32 * 1024 * 1024
MAX_AST_NODES = 1_000_000


@dataclass(frozen=True)
class OfficeSourceOccurrence:
    ordinal: int
    kind: str
    location: tuple[str | int, ...]
    content_sha256: str
    content_json: str


def scientific_source_occurrences(ast: bytes) -> tuple[OfficeSourceOccurrence, ...]:
    """Account for all source occurrences, including nested tables and captions.

    Exact JSON content is retained: no mathematical, citation, table, or raw
    syntax normalization can silently excuse a writer dropping information.
    """
    if len(ast) > MAX_AST_BYTES:
        raise ValueError("Office scientific AST exceeds finite byte budget")
    document = json.loads(ast)
    if not isinstance(document, dict) or not isinstance(document.get("blocks"), list):
        raise ValueError("Office scientific AST has no document blocks")
    if not document.get("pandoc-api-version"):
        raise ValueError("Office scientific AST has no parser version")
    pending: list[tuple[Any, tuple[str | int, ...]]] = [(document["blocks"], ("blocks",))]
    result: list[OfficeSourceOccurrence] = []
    visited = 0
    while pending:
        value, location = pending.pop()
        visited += 1
        if visited > MAX_AST_NODES:
            raise ValueError("Office scientific AST exceeds finite node budget")
        if isinstance(value, dict):
            kind = value.get("t")
            if kind in KINDS:
                if "c" not in value:
                    raise ValueError("Office scientific occurrence has no content")
                canonical = json.dumps(value["c"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                result.append(
                    OfficeSourceOccurrence(
                        len(result), kind, location, hashlib.sha256(canonical.encode()).hexdigest(), canonical
                    )
                )
            pending.extend((child, (*location, key)) for key, child in reversed(list(value.items())))
        elif isinstance(value, list):
            pending.extend((value[index], (*location, index)) for index in reversed(range(len(value))))
    return tuple(result)


def office_coverage_obligations(ast: bytes) -> dict[str, Any]:
    """Emit unresolved source requirements, never a producer-supplied pass bit."""
    occurrences = scientific_source_occurrences(ast)
    return {
        "schema_version": "template-native-office-source-coverage-v1",
        "source_ast_sha256": hashlib.sha256(ast).hexdigest(),
        "counts": {kind: sum(row.kind == kind for row in occurrences) for kind in sorted(KINDS)},
        "occurrences": [
            {
                "ordinal": row.ordinal,
                "kind": row.kind,
                "location": list(row.location),
                "content_sha256": row.content_sha256,
                "content_json": row.content_json,
                "required_native_witness": True,
            }
            for row in occurrences
        ],
        "blockers": [
            f"{row.kind} occurrence {row.ordinal} requires independent native content/layout proof"
            for row in occurrences
        ],
    }
