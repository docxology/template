"""Independent decoded source assets and actual native PDF image witnesses."""

from __future__ import annotations

import hashlib
import time
from collections import Counter
from io import BytesIO
from typing import Any

from infrastructure.reporting.native_office_content_witness import (
    MAX_PACKAGE_BYTES,
    MAX_PIXELS,
    _archive,
    _image_identity,
)
from infrastructure.reporting.native_pdf_stream_bounds import preflight_pdf_streams


def inspect_office_native_images(pdf: bytes, figures: tuple[bytes, ...], *, deadline: float) -> dict[str, Any]:
    """Decode every native PDF image only after finite stream/pixel admission.

    The independent complete-page comparison supplies placement/geometry.
    This additional source check refuses common reference/candidate asset loss.
    Exact vector assets still require a dedicated source vector interpretation.
    """
    from PIL import Image
    from pypdf import PdfReader

    preflight_pdf_streams(pdf, deadline=deadline, max_bytes=MAX_PACKAGE_BYTES, max_objects=2_000_000)
    reader = PdfReader(BytesIO(pdf), strict=True)
    expected: Counter[str] = Counter()
    blockers = []
    for ordinal, data in enumerate(figures):
        identity = _image_identity(data)
        if identity["kind"] != "decoded-raster":
            blockers.append(f"source figure {ordinal} requires native vector interpretation")
            continue
        with Image.open(BytesIO(data)) as image:
            image.load()
            expected[hashlib.sha256(image.convert("RGB").tobytes()).hexdigest()] += 1
    observed: Counter[str] = Counter()
    observations = []
    total_pixels = 0

    def resolved(value: Any) -> Any:
        return value.get_object() if hasattr(value, "get_object") else value

    for page_number, page in enumerate(reader.pages, 1):
        if time.monotonic() >= deadline:
            raise TimeoutError("Office native source image decoding exhausted original deadline")
        # Admit raw XObject image dimensions before invoking pypdf's actual
        # Pillow adapter. Form recursion is bounded and cycle-safe.
        pending = [page.get("/Resources", {})]
        visited = set()
        while pending:
            resources = resolved(pending.pop())
            objects = resolved(resources.get("/XObject", {}))
            for reference in objects.values():
                resource_identity = (getattr(reference, "idnum", None), getattr(reference, "generation", None))
                if resource_identity[0] is not None and resource_identity in visited:
                    continue
                visited.add(resource_identity)
                if len(visited) > 20_000:
                    raise ValueError("Office native image resource graph exceeds finite node budget")
                stream = resolved(reference)
                if stream.get("/Subtype") == "/Form":
                    pending.append(stream.get("/Resources", {}))
                elif stream.get("/Subtype") == "/Image":
                    width, height = stream.get("/Width"), stream.get("/Height")
                    if (
                        not isinstance(width, int)
                        or not isinstance(height, int)
                        or isinstance(width, bool)
                        or isinstance(height, bool)
                        or min(width, height) < 1
                        or width * height > MAX_PIXELS
                    ):
                        raise ValueError("Office native image exceeds finite pixel geometry")
                    total_pixels += width * height
                    if total_pixels * 4 > MAX_PACKAGE_BYTES:
                        raise ValueError("Office native decoded images exceed finite byte budget")
        for native_image in page.images:
            actual = native_image.image
            if actual is None:
                raise ValueError("Office native PDF image has no actual decoded pixels")
            digest = hashlib.sha256(actual.convert("RGB").tobytes()).hexdigest()
            observed[digest] += 1
            observations.append(
                {"page": page_number, "name": native_image.name, "size": list(actual.size), "rgb_sha256": digest}
            )
    missing = expected - observed
    return {
        "schema_version": "template-native-office-source-image-ink-v1",
        "pdf_sha256": hashlib.sha256(pdf).hexdigest(),
        "status": "failed" if missing else "blocked" if blockers else "observed",
        "findings": [
            {"code": "office.source.native_image", "rgb_sha256": digest, "missing_occurrences": count}
            for digest, count in sorted(missing.items())
        ],
        "blockers": blockers,
        "source_counts": dict(sorted(expected.items())),
        "native_images": observations,
    }


def inspect_office_cover(package: bytes, source: bytes, alternative: str) -> dict[str, Any]:
    """Identify the declared EPUB cover image through its actual OPF manifest."""
    from defusedxml.ElementTree import fromstring
    from posixpath import normpath, join, dirname

    members = _archive(package)
    container = fromstring(members["META-INF/container.xml"])
    namespace = "{urn:oasis:names:tc:opendocument:xmlns:container}"
    package_path = container.find(f"{namespace}rootfiles/{namespace}rootfile").get("full-path")
    opf = fromstring(members[package_path])
    namespace = "{http://www.idpf.org/2007/opf}"
    covers = [
        node
        for node in opf.findall(f"{namespace}manifest/{namespace}item")
        if "cover-image" in node.get("properties", "").split()
    ]
    if len(covers) != 1:
        raise ValueError("Office EPUB cover has no unique declared manifest image")
    image_path = normpath(join(dirname(package_path), covers[0].get("href")))
    if image_path not in members:
        raise ValueError("Office EPUB declared cover is missing")
    source_identity = _image_identity(source)
    native_identity = _image_identity(members[image_path])
    findings = []
    if source_identity != native_identity:
        findings.append({"code": "office.source.cover_content"})
    alternatives = []
    for name, data in members.items():
        if name.endswith(".xhtml"):
            for node in fromstring(data).iter():
                if node.tag.endswith("}img") and normpath(join(dirname(name), node.get("src", ""))) == image_path:
                    alternatives.append(node.get("alt", ""))
    if not alternatives or any(value != alternative for value in alternatives):
        findings.append({"code": "office.source.cover_alternative"})
    return {
        "schema_version": "template-native-office-cover-survival-v1",
        "status": "failed" if findings else "observed",
        "findings": findings,
        "blockers": [],
        "member": image_path,
        "image": source_identity,
        "alternative": alternative,
    }
