"""Source-bound local figure variants for the accessible presentation writer.

Canonical manuscript figures remain untouched. Explicit manifests enumerate
complete presentation panels in reading order and bind their native label
measurements to the exact raster bytes. Measurements are declarations from the
figure producer; this boundary verifies integrity and final scale, not meaning.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility_contracts import density_error
from infrastructure.rendering._slides_accessibility_figures import _image_nodes
from infrastructure.rendering._slides_accessibility_limits import MAX_ACCESSIBLE_PANDOC_AST_NODES
from infrastructure.rendering._slides_accessibility_image_io import (
    MAX_INTRINSIC_IMAGE_BYTES,
    _resolve_local_image,
    inspect_intrinsic_image_geometry,
    read_confined_slide_resource,
)

MANIFEST_ATTRIBUTE = "data-slide-manifest"
MAX_VARIANT_MANIFEST_BYTES = 1024 * 1024
MAX_PRESENTATION_PANELS = 64


def _error(message: str, source: str) -> RenderingError:
    return density_error("slides.schema.presentation-variant", message, source=source, heading="Presentation variant")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate manifest key")
        result[key] = value
    return result


def _attributes(image: dict[str, Any], source: str) -> dict[str, str]:
    try:
        pairs = image["c"][0][2]
        result: dict[str, str] = {}
        for key, value in pairs:
            if not isinstance(key, str) or not isinstance(value, str) or key in result:
                raise ValueError("duplicate or malformed image attribute")
            result[key] = value
        return result
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise _error("presentation image attributes must be unique string pairs", source) from exc


def _panels(
    target: str,
    *,
    source: str,
    roots: tuple[Path, ...],
    figure_root: Path | None,
) -> list[dict[str, Any]]:
    payload = read_confined_slide_resource(
        target,
        source=source,
        authorized_roots=roots,
        figure_root=figure_root,
        maximum_bytes=MAX_VARIANT_MANIFEST_BYTES,
    )
    try:
        manifest = json.loads(payload, object_pairs_hook=_unique_object)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise _error("presentation manifest is not bounded, unique-key JSON", source) from exc
    if not isinstance(manifest, dict) or set(manifest) != {"schema_version", "panels"}:
        raise _error("presentation manifest requires exactly schema_version and panels", source)
    panels = manifest["panels"]
    if (
        manifest["schema_version"] != "1.0"
        or not isinstance(panels, list)
        or not 1 <= len(panels) <= MAX_PRESENTATION_PANELS
    ):
        raise _error("presentation manifest version or panel count is invalid", source)
    seen: set[str] = set()
    for panel in panels:
        if not isinstance(panel, dict) or set(panel) != {"src", "alt", "sha256", "minimum_label_px"}:
            raise _error("each presentation panel requires src, alt, sha256, and minimum_label_px", source)
        if any(not isinstance(panel[key], str) or not panel[key].strip() for key in ("src", "alt", "sha256")):
            raise _error("presentation panel strings must be nonempty", source)
        if panel["src"] in seen:
            raise _error("presentation panels must have distinct source paths", source)
        seen.add(panel["src"])
        minimum = panel["minimum_label_px"]
        if (
            isinstance(minimum, bool)
            or not isinstance(minimum, (int, float))
            or not math.isfinite(minimum)
            or minimum <= 0
        ):
            raise _error("minimum_label_px must be finite and positive", source)
        raster = read_confined_slide_resource(
            panel["src"],
            source=source,
            authorized_roots=roots,
            figure_root=figure_root,
            maximum_bytes=MAX_INTRINSIC_IMAGE_BYTES,
        )
        if hashlib.sha256(raster).hexdigest() != panel["sha256"]:
            raise _error("presentation panel bytes do not match the producer digest", source)
        geometry = inspect_intrinsic_image_geometry(
            panel["src"],
            source=source,
            heading="Presentation variant",
            authorized_roots=roots,
            figure_root=figure_root,
        )
        if geometry is None:
            raise _error("presentation panels must be inspectable local rasters", source)
    return panels


def expand_presentation_variants(
    document: dict[str, Any],
    *,
    source: str,
    roots: tuple[Path, ...],
    figure_root: Path | None,
) -> dict[str, Any]:
    """Replace an explicitly annotated top-level figure with complete panels.

    Paths use the same resource-root aliases as canonical images; they are not
    relative to the manifest file. Each emitted figure retains its canonical
    caption and a unique derivative label. All other input remains unchanged.
    """
    for image in _image_nodes(document.get("meta", {})):
        if MANIFEST_ATTRIBUTE in _attributes(image, source):
            raise _error("presentation manifests cannot appear in headings or metadata", source)
    updated = copy.deepcopy(document)
    blocks: list[dict[str, Any]] = []
    consumed: set[int] = set()
    expanded_nodes = 0
    identifiers = {block["c"][0][0] for block in updated["blocks"] if block.get("t") == "Figure"}
    for block_index, block in enumerate(updated["blocks"], start=1):
        images = _image_nodes(block)
        annotated = [image for image in images if MANIFEST_ATTRIBUTE in _attributes(image, source)]
        if not annotated:
            blocks.append(block)
            continue
        if block.get("t") != "Figure" or len(images) != 1 or len(annotated) != 1:
            raise _error("presentation manifests require a top-level figure with one image", source)
        image = annotated[0]
        attributes = _attributes(image, source)
        consumed.add(id(image))
        panels = _panels(attributes[MANIFEST_ATTRIBUTE], source=source, roots=roots, figure_root=figure_root)
        for index, panel in enumerate(panels, start=1):
            variant = copy.deepcopy(block)
            base = variant["c"][0][0] or f"presentation-figure-{block_index}"
            identifier = f"{base}-slide-panel-{index}"
            while identifier in identifiers:
                identifier += "-variant"
            identifiers.add(identifier)
            variant["c"][0][0] = identifier
            selected = _image_nodes(variant)[0]
            selected["c"][2][0] = panel["src"]
            selected["c"][1] = [{"t": "Str", "c": panel["alt"]}]
            selected["c"][0][2] = [
                [key, value]
                for key, value in attributes.items()
                if key not in {MANIFEST_ATTRIBUTE, "width", "height"} and not key.startswith("data-slide-label-")
            ] + [
                ["data-slide-label-minimum-px", str(panel["minimum_label_px"])],
                ["data-slide-label-source-sha256", panel["sha256"]],
            ]
            stack: list[object] = [variant]
            while stack:
                value = stack.pop()
                expanded_nodes += 1
                if expanded_nodes > MAX_ACCESSIBLE_PANDOC_AST_NODES:
                    raise _error("presentation expansion exceeds the AST node limit", source)
                if isinstance(value, dict):
                    stack.extend(value.values())
                elif isinstance(value, list):
                    stack.extend(value)
            blocks.append(variant)
    for image in _image_nodes(updated):
        attributes = _attributes(image, source)
        if MANIFEST_ATTRIBUTE in attributes and id(image) not in consumed:
            raise _error("presentation manifests cannot appear in headings or metadata", source)
        if any(key.startswith("data-slide-label-") for key in attributes):
            raise _error("label measurements must enter through a source-bound presentation manifest", source)
    updated["blocks"] = blocks
    return updated


def relocate_presentation_panels(
    document: dict[str, Any],
    *,
    output_dir: Path,
    source: str,
    roots: tuple[Path, ...],
    figure_root: Path | None,
) -> None:
    """Resolve selected panels once for both writers' output-relative paths.

    Pandoc resource roots resolve input bytes but do not relocate linked HTML
    assets. This runs only after manifest validation and composition; authored
    measurement attributes cannot reach this boundary.
    """
    for image in _image_nodes(document):
        if "data-slide-label-source-sha256" not in _attributes(image, source):
            continue
        resolved = _resolve_local_image(
            image["c"][2][0],
            source=source,
            heading="Presentation variant",
            authorized_roots=roots,
            figure_root=figure_root,
        )
        if resolved is None:
            raise _error("selected panel no longer resolves to a confined local file", source)
        image["c"][2][0] = Path(os.path.relpath(resolved.path, output_dir)).as_posix()


def reject_small_embedded_labels(pdf: Path, composed_source: Path, *, minimum_pt: float) -> None:
    """Require declared raster labels to meet the floor at actual PDF scale.

    Image dimensions identify candidate occurrences. Where distinct panels have
    the same dimensions, apply the smallest declared native label to every
    occurrence conservatively. Require at least the declared occurrence count;
    a missing rendered image cannot silently satisfy the contract.
    """
    from infrastructure.rendering._slides_accessibility_limits import read_bounded_pandoc_json

    document = json.loads(read_bounded_pandoc_json(composed_source, source=str(composed_source)))
    expected: dict[tuple[int, int], list[float]] = {}
    for image in _image_nodes(document):
        attributes = _attributes(image, str(composed_source))
        if "data-slide-label-minimum-px" not in attributes:
            continue
        try:
            size = (
                int(attributes["data-slide-figure-intrinsic-width"]),
                int(attributes["data-slide-figure-intrinsic-height"]),
            )
            expected.setdefault(size, []).append(float(attributes["data-slide-label-minimum-px"]))
        except (ValueError, KeyError) as exc:
            raise _error("composed panel is missing measured raster geometry", str(composed_source)) from exc
    if not expected:
        return
    import pdfplumber

    observed = dict.fromkeys(expected, 0)
    findings: list[dict[str, object]] = []
    with pdfplumber.open(pdf) as rendered:
        for page_number, page in enumerate(rendered.pages, start=1):
            for embedded in page.images:
                size = tuple(embedded["srcsize"])
                if size not in expected:
                    continue
                observed[size] += 1
                scale = min(float(embedded["width"]) / size[0], float(embedded["height"]) / size[1])
                effective = min(expected[size]) * scale
                if not math.isfinite(effective) or effective < minimum_pt:
                    findings.append({"page": page_number, "effective_label_pt": effective, "required_pt": minimum_pt})
    for size, labels in expected.items():
        if observed[size] < len(labels):
            findings.append({"missing_panel_dimensions": size, "expected": len(labels), "observed": observed[size]})
    if findings:
        pdf.unlink(missing_ok=True)
        raise density_error(
            "slides.density.figure-label-scale",
            "presentation labels fail the final embedded-size contract",
            source=str(composed_source),
            heading="Rendered figures",
            findings=findings,
        )


__all__ = ["expand_presentation_variants", "reject_small_embedded_labels"]
