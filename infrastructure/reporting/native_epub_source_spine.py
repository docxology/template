"""Ordered EPUB reference parity subordinate to independent source survival."""

from __future__ import annotations

import hashlib
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_epub_observer import epub_spine_rows, inspect_epub_spine
from infrastructure.reporting.native_format_content_contracts import (
    MAX_BLOCKS,
    MAX_TOKENS,
    ContentBlock,
    NativeContentContract,
)

SCHEMA = "template-native-epub-source-reference-spine-v1"


def inspect_source_reference_epub_spine(
    reference_epub: bytes,
    candidate_epub: bytes,
    reference_source_survival: dict[str, Any],
) -> dict[str, Any]:
    """Compare the actual spine with an independently source-rendered reference.

    The enclosing observer admits the source-only writer and independently
    checks that reference against original source. This narrower receipt cannot
    grant source survival, native layout or complete format acceptance itself.
    Its ordered contracts include every actual reference spine entry; unknown
    and nontext source projections retain their original blockers.
    """
    reference_sha = hashlib.sha256(reference_epub).hexdigest()
    findings = reference_source_survival.get("findings")
    blockers = reference_source_survival.get("blockers")
    if (
        reference_source_survival.get("schema_version") != "template-native-office-source-survival-v1"
        or reference_source_survival.get("package_sha256") != reference_sha
        or any(
            not isinstance(reference_source_survival.get(name), str)
            or len(reference_source_survival[name]) != 64
            or any(character not in "0123456789abcdef" for character in reference_source_survival[name])
            for name in ("source_ast_sha256", "filtered_ast_sha256", "native_ast_sha256")
        )
        or not isinstance(findings, list)
        or any(not isinstance(row, dict) or not isinstance(row.get("code"), str) or not row["code"] for row in findings)
        or not isinstance(blockers, list)
        or any(not isinstance(reason, str) or not reason for reason in blockers)
        or reference_source_survival.get("status") != ("failed" if findings else "blocked" if blockers else "observed")
    ):
        raise ValueError("EPUB reference spine requires its exact independent source-survival witness")
    rows = epub_spine_rows(reference_epub)
    if not rows or len(rows) > MAX_BLOCKS or sum(len(row["tokens"]) for row in rows) > MAX_TOKENS:
        raise ValueError("EPUB reference spine exceeds its nonempty source-contract budget")
    chapters = tuple(
        NativeContentContract(
            f"epub:source-reference-spine:{ordinal}",
            ((f"source-reference-spine/{ordinal}/{row['member']}", row["sha256"]),),
            (ContentBlock(f"spine:{ordinal}", "reference-spine-body", 1, tuple(row["tokens"])),),
            (),
        )
        for ordinal, row in enumerate(rows)
    )
    reference = inspect_epub_spine(reference_epub, chapters)
    candidate = inspect_epub_spine(candidate_epub, chapters)
    combined_findings = [*findings, *reference["findings"], *candidate["findings"]]
    combined_blockers = [*blockers, *reference["blockers"], *candidate["blockers"]]
    return {
        "schema_version": SCHEMA,
        "reference_epub_sha256": reference_sha,
        "reference_source_survival_digest": canonical_digest(reference_source_survival),
        "chapter_contracts": [chapter.to_dict() for chapter in chapters],
        "reference": reference,
        "candidate": candidate,
        "status": "fail" if combined_findings else "blocked" if combined_blockers else "pass",
        "findings": combined_findings,
        "blockers": combined_blockers,
        "assurance": (
            "ordered source-reference spine parity; original source survival, native lay"
            "out and controls remain mandatory"
        ),
    }


def replay_source_reference_epub_spine(
    reference_epub: bytes,
    candidate_epub: bytes,
    reference_source_survival: dict[str, Any],
    raw: object,
) -> dict[str, Any]:
    """Reparse current admitted bytes and refuse changed original observations."""
    observed = inspect_source_reference_epub_spine(reference_epub, candidate_epub, reference_source_survival)
    if raw != observed:
        raise ValueError("independent source-reference EPUB spine replay differs")
    return observed
