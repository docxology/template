"""Bind fully understood standalone source natbib commands to genuine labels.

Residual markup, nonvisible commands, macro/state changes and unsupported raw
forms retain their raw obligations. Original bibliography/engine/SDK/custody
admission belongs to the enclosing reader; candidate display text is no oracle.
"""

from __future__ import annotations

import hashlib
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_format_content_contracts import text_tokens
from infrastructure.reporting.native_pdf_citations import CITATION_POLICY, CITATION_SCHEMA, raw_citations


def independent_raw_natbib_labels(ast_bytes: bytes, reference: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Reparse each original raw node and bind its whole exact command closure.

    Only whitespace-separated visible supported natbib commands are understood.
    A citation-looking fragment inside arbitrary raw TeX never clears that node.
    """
    from infrastructure.reporting.native_format_pdf_semantic_plan import strict_ast

    ast = strict_ast(ast_bytes)
    if (
        reference.get("schema_version") != CITATION_SCHEMA
        or reference.get("policy_digest") != canonical_digest(CITATION_POLICY)
        or reference["inputs"]["ast_sha256"] != hashlib.sha256(ast_bytes).hexdigest()
    ):
        raise ValueError("original raw natbib labels differ from the admitted source AST/policy")
    retained: dict[str, list[dict[str, Any]]] = {}
    seen_ids = set()
    for row in reference["occurrences"]:
        if row["id"] in seen_ids:
            raise ValueError("original natbib occurrence identities are ambiguous")
        seen_ids.add(row["id"])
        if row["source"]["kind"] == "raw-natbib":
            retained.setdefault(row["source"]["path"], []).append(row)
    result: dict[str, dict[str, Any]] = {}
    pending: list[tuple[Any, str]] = [(ast["blocks"], "blocks")]
    nodes = 0
    while pending:
        value, path = pending.pop()
        nodes += 1
        if nodes > 100_000:
            raise ValueError("original raw natbib node census exceeds its finite budget")
        if isinstance(value, list):
            pending.extend((child, f"{path}/{index}") for index, child in reversed(list(enumerate(value))))
        elif isinstance(value, dict):
            if value.get("t") in {"Code", "CodeBlock", "Cite"}:
                continue
            if value.get("t") in {"RawInline", "RawBlock"}:
                form, source = value["c"]
                if form not in {"tex", "latex"}:
                    continue
                try:
                    commands, residual = raw_citations(source)
                except ValueError:
                    continue  # The exact unsupported raw source still survives in the plan.
                if not commands or residual.strip() or any(row["command"] == "nocite" for row in commands):
                    continue
                labels = retained.get(path, [])
                if len(labels) != len(commands):
                    raise ValueError("original raw natbib reference omits or invents a source command")
                for command, label in zip(commands, labels, strict=True):
                    if (
                        label["source"]["original"] != command
                        or tuple(label["keys"]) != tuple(command["keys"])
                        or not isinstance(label["native_text"], str)
                        or not text_tokens(label["native_text"])
                    ):
                        raise ValueError("original raw natbib label differs from its exact parsed source command")
                result[path] = {
                    "source_node": value,
                    "raw_commands": commands,
                    "reference_ids": [row["id"] for row in labels],
                    "native_text": " ".join(row["native_text"] for row in labels),
                }
                continue
            pending.extend((child, f"{path}/{key}") for key, child in value.items() if key != "t")
    return result
