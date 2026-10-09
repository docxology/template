"""Conditional source-declared figure kernel without candidate-derived pixels."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_format_html_admitted_source import AdmittedHTMLSource
from infrastructure.reporting.native_format_html_integer_resampling import inspect_integer_resampling
from infrastructure.reporting.native_format_html_source_metadata import remaining_seconds
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader


def inspect_admitted_resampling(
    admitted: AdmittedHTMLSource,
    dom: dict[str, Any],
    pixels: bytes,
    artifact: ArtifactSnapshot,
    reader: SnapshotReader,
    *,
    deadline: float,
) -> dict[str, Any]:
    """Only explicit original width/height/pixelated/solid-background is modeled.

    All other occurrences remain in the ledger with their exact source ID and
    blocker. Source background and geometry never come from observed pixels.
    Existing decoder/alpha/figure and whole Source blockers remain independent.
    """
    remaining_seconds(deadline)
    rows: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    blockers: list[str] = []
    used: set[int] = set()
    for source in admitted.fidelity["image_alt"]["images"]:
        remaining_seconds(deadline)
        identity = source["source_id"]
        index = next(
            (i for i, row in enumerate(dom["images"]) if i not in used and row["src"] == source["native_target"]), None
        )
        if index is None:
            findings.append({"code": "html.figure.resampling-source", "source_id": identity})
            continue
        used.add(index)
        attr = source["attributes"]
        declarations: dict[str, str] = {}
        reasons = []
        for key, value in attr[2]:
            if key in declarations:
                reasons.append("duplicate original figure attribute")
            declarations[key] = value
        style: dict[str, str] = {}
        for clause in declarations.get("style", "").split(";"):
            if not clause.strip():
                continue
            if clause.count(":") != 1:
                reasons.append("unknown original figure CSS syntax")
                continue
            key, value = (part.strip() for part in clause.split(":", 1))
            if key in style:
                reasons.append("duplicate original figure CSS declaration")
            style[key] = value
        if set(style) - {"image-rendering", "background-color", "width", "height"}:
            reasons.append("original figure CSS needs a separate presentation model")
        dimensions = [style.get(name, declarations.get(name, "")) for name in ("width", "height")]
        if any(not re.fullmatch(r"[1-9][0-9]{0,4}(?:px)?", value) for value in dimensions):
            reasons.append("source-declared integral figure width/height is unavailable")
        if style.get("image-rendering") != "pixelated" or style.get("background-color") not in {
            "white",
            "#fff",
            "#ffffff",
            "rgb(255, 255, 255)",
        }:
            reasons.append("original pixelated kernel and opaque solid background are not both explicit")
        parsed = urlsplit(source["native_target"] or "")
        if parsed.scheme or parsed.netloc or parsed.path.startswith("/") or parsed.query or parsed.fragment:
            reasons.append("external or rewritten figure source needs a separate original asset model")
        if reasons:
            blockers.extend(identity + ": " + reason for reason in reasons)
            rows.append({"source_id": identity, "image_index": index, "kernel": None, "blockers": reasons})
            continue
        native = dom["images"][index]
        expected_size = [int(value.removesuffix("px")) for value in dimensions]
        if native["box"][2:] != expected_size:
            findings.append({"code": "html.figure.resampling-source-geometry", "source_id": identity})
        path = Path(os.path.normpath(str(artifact.path.parent / unquote(parsed.path))))
        relative = path.relative_to(reader.root).as_posix()
        actual = reader.read(relative)
        original = admitted.reference.read(relative)
        if actual.content != original:
            raise ValueError("figure kernel source differs from factory-admitted immutable original bytes")
        kernel = inspect_integer_resampling(original, identity, native, pixels, (255, 255, 255, 255), deadline=deadline)
        findings.extend(kernel["findings"])
        blockers.extend(kernel["blockers"])
        rows.append(
            {
                "source_id": identity,
                "image_index": index,
                "source": {"path": relative, "sha256": actual.sha256},
                "kernel": kernel,
            }
        )
    result = {
        "figures": rows,
        "findings": findings,
        "blockers": blockers,
        "status": "fail" if findings else "blocked" if blockers else "pass",
    }
    result = {**result, "digest": canonical_digest(result)}
    remaining_seconds(deadline)
    return result
