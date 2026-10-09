"""Portable independent replay of actual PDF source witness predicates.

The enclosing reader authenticates retained source/parser, hydrated asset,
SDK/native process and every raster execution's custody. Origin paths remain
labels. This leaf recomputes source and native predicates from admitted bytes.
"""

from __future__ import annotations

import hashlib
import math
import time
from collections.abc import Callable
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_format_pdf_semantic_plan import compile_pdf_semantic_plan
from infrastructure.reporting.native_format_pdf_source_witness import inspect_pdf_source_witness


def replay_pdf_source_witness(
    original: dict[str, Any],
    *,
    artifact_id: str,
    sources: tuple[tuple[str, bytes], ...],
    ast_bytes: bytes,
    pdf: dict[str, Any],
    rasters: tuple[dict[str, Any], ...],
    assets: dict[str, dict[str, Any]],
    read_artifact: Callable[[dict[str, Any]], bytes],
    deadline: float,
    citation_reference: dict[str, Any] | None = None,
    mathematical_inputs: dict[str, Any] | None = None,
    full_source_reference: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Rebuild every source literal/grid/image predicate without origin access.

    Replayed pass is this leaf's scoped semantic result. It grants no release
    acceptance unless the enclosing reader also proves full source/layout,
    original controls and every explicitly retained unsupported obligation.
    """
    if type(deadline) not in {float, int} or not math.isfinite(deadline) or time.monotonic() >= deadline:
        raise TimeoutError("independent PDF source witness replay has no finite budget")
    if not 0 < len(rasters) <= 500:
        raise ValueError("independent PDF source witness requires bounded every-page rasters")
    seen = set()
    total = 0

    def admitted(binding: dict[str, Any]) -> bytes:
        nonlocal total
        if time.monotonic() >= deadline:
            raise TimeoutError("independent PDF source witness replay exhausted its finite budget")
        if (
            set(binding) != {"path", "sha256"}
            or not isinstance(binding["path"], str)
            or not binding["path"]
            or binding["path"] in seen
        ):
            raise ValueError("independent PDF source witness artifact closure is ambiguous")
        seen.add(binding["path"])
        content = read_artifact(binding)
        total += len(content)
        if len(content) > 64 * 1024 * 1024 or total > 256 * 1024 * 1024:
            raise ValueError("independent PDF source witness exceeds its admitted byte budget")
        if hashlib.sha256(content).hexdigest() != binding["sha256"]:
            raise ValueError("original PDF source witness artifact differs from retained binding")
        return content

    plan = compile_pdf_semantic_plan(artifact_id, sources, ast_bytes, citation_reference=citation_reference)
    native_pdf = admitted(pdf)
    native_rasters = tuple(admitted(binding) for binding in rasters)
    # Multiple source occurrences may legitimately consume one identical
    # original asset. Authenticate each unique path once without merging the
    # occurrence ledger or allowing a path to claim inconsistent bytes.
    image_bytes: dict[str, bytes] = {}
    image_digests: dict[str, str] = {}
    source_images = {}
    for identity, binding in assets.items():
        if set(binding) != {"path", "sha256"}:
            raise ValueError("independent PDF figure asset fieldset differs")
        path = binding["path"]
        if path in image_bytes:
            if image_digests[path] != binding["sha256"]:
                raise ValueError("source figure shared asset identity is inconsistent")
            content = image_bytes[path]
        else:
            content = admitted(binding)
            image_bytes[path], image_digests[path] = content, binding["sha256"]
        source_images[identity] = (path, content)
    mathematics = None
    if mathematical_inputs is not None:
        if set(mathematical_inputs) != {"source_tex", "instrumented_pdf", "interpreted_pdf", "interpreted_rasters"}:
            raise ValueError("portable mathematical reference closure differs")
        mathematics = {
            "ast_bytes": ast_bytes,
            "source_tex": admitted(mathematical_inputs["source_tex"]),
            "instrumented_pdf": admitted(mathematical_inputs["instrumented_pdf"]),
            "interpreted_pdf": admitted(mathematical_inputs["interpreted_pdf"]),
            "interpreted_rasters": tuple(admitted(binding) for binding in mathematical_inputs["interpreted_rasters"]),
        }
    whole_source = None
    if full_source_reference is not None:
        if set(full_source_reference) != {"pdf", "rasters", "source_plan_digest"}:
            raise ValueError("portable whole-source PDF reference closure differs")
        whole_source = {
            "pdf": admitted(full_source_reference["pdf"]),
            "rasters": tuple(admitted(binding) for binding in full_source_reference["rasters"]),
            "source_plan_digest": full_source_reference["source_plan_digest"],
        }
    current: dict[str, Any] = inspect_pdf_source_witness(
        native_pdf,
        native_rasters,
        plan,
        assets=source_images,
        deadline=deadline,
        citation_reference=citation_reference,
        mathematical_inputs=mathematics,
        full_source_reference=whole_source,
    )
    if canonical_digest(current) != canonical_digest(original):
        raise ValueError("original PDF semantic witness differs from independent source/native replay")
    return current
