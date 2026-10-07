"""Source-bound raster storybook checks; producer summaries are never evidence.

Reference scenes use the admitted source renderer. Independent PDF decoding,
placement and contact-sheet reconstruction verify its transported artifacts.
Font/library custody must be admitted by the calling native receipt reader.
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
import math
import re
import textwrap
import time
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, cast

import yaml
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader
from pypdf.generic import ContentStream

LIMIT = 64 * 1024 * 1024


class _SourceLoader(yaml.SafeLoader):
    pass


def _unique_mapping(loader: yaml.SafeLoader, node: yaml.MappingNode) -> dict[Any, Any]:
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if key in result:
            raise ValueError("duplicate source YAML field")
        result[key] = loader.construct_object(value_node)
    return result


_SourceLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


def read_source_yaml(path: Path) -> Any:
    if path.stat().st_size > LIMIT:
        raise ValueError("source YAML exceeds artifact bound")
    loader = _SourceLoader(path.read_bytes())
    try:
        return loader.get_single_data()
    finally:
        loader.dispose()


def source_package(project: Path, name: str) -> Any:
    """Import only the current candidate's confined source package."""
    source = project.resolve() / "src" / name
    label = "_native_print_" + hashlib.sha256((str(source) + source_identity(project)).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(
        label, source / "__init__.py", submodule_search_locations=[str(source)]
    )
    if spec is None or spec.loader is None:
        raise ValueError("missing source package")
    module = importlib.util.module_from_spec(spec)
    sys.modules[label] = module
    spec.loader.exec_module(module)
    return importlib.import_module(label + ".rendering" if name == "storybook" else label + ".engine")


def source_identity(project: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted((*project.glob("src/**/*.py"), *project.glob("content/**/*.yaml"))):
        if path.is_symlink() or not path.resolve().is_relative_to(project.resolve()):
            raise ValueError("source resource escapes current candidate")
        digest.update(path.relative_to(project).as_posix().encode() + b"\0" + path.read_bytes())
    return digest.hexdigest()


def pixels(data: bytes) -> tuple[tuple[int, int], bytes]:
    if len(data) > LIMIT:
        raise ValueError("image exceeds native artifact bound")
    with Image.open(BytesIO(data)) as image:
        if (
            image.format != "PNG"
            or image.mode != "RGB"
            or set(image.info) & {"transparency", "icc_profile", "gamma", "srgb", "chromaticity", "exif"}
        ):
            raise ValueError("unsupported native PNG decode/color/transparency")
        if image.width * image.height > 10_000_000:
            raise ValueError("image exceeds decoded pixel bound")
        return image.size, image.convert("RGB").tobytes()


@dataclass(frozen=True)
class StorybookReference:
    source_sha256: str
    dimensions: tuple[int, int]
    filenames: tuple[str, ...]
    pages: tuple[bytes, ...]
    contact_sheet: bytes


def _caption_bounds(spec: Any, page: Any, rendering: Any) -> None:
    """Independently bound every source title/body line before raster admission."""
    layout = importlib.import_module(rendering.__package__ + ".text_layout")
    draw = ImageDraw.Draw(Image.new("RGB", (spec.page_width, spec.page_height)))
    width, height = spec.page_width, spec.page_height

    def lines(text: str, count: int) -> list[str]:
        return [
            line for paragraph in text.splitlines() for line in (textwrap.wrap(paragraph, count) if paragraph else [""])
        ]

    def check(text: str, x: int, y: int, size: int, bold: bool = False) -> None:
        if not text:
            return
        font = layout.load_font(size, bold=bold)
        box = draw.textbbox((x, y), text, font=font)
        if box[0] < 0 or box[1] < 0 or box[2] > width or box[3] > height:
            raise ValueError("storybook source caption clips outside its page")

    if page.slug == "cover":
        y = 86
        for text in lines(page.title, 18):
            font = layout.load_font(108, bold=True)
            x = (width - int(draw.textbbox((0, 0), text, font=font)[2])) // 2
            check(text, x, y, 108, True)
            y += 122
        info = [line for line in page.text.splitlines() if line.strip()]
        y = height - 344 + 38
        if info:
            font = layout.load_font(32, bold=True)
            for text in layout.pixel_wrapped_lines(draw, info[0], font, width - 386):
                check(text, 270, y, 32, True)
                box = draw.textbbox((0, 0), text, font=font)
                y += box[3] - box[1] + 10
        y += 16
        for index, text in enumerate(info[1:]):
            label = text if index == 0 else "|  " + text
            check(label, 270, y, 24 if text == "template_storybook" else 27, text == "template_storybook")
            y += 41
    elif page.slug == "publication_information":
        check(page.title, 112, 198, 58, True)
        y = 296
        for text in lines(page.text, 57):
            if not text:
                y += 28
                continue
            size = 32 if y < 690 else 26
            check(text, 112, y, size)
            y += 43 if size == 32 else 36
    else:
        titles, body = lines(page.title, 24), lines(page.text, 40)
        box_height = 68 * len(titles) + 48 * len(body) + 72
        y = 92 if page.caption_position == "top" else height - box_height - 88
        for text in titles:
            check(text, 86, y, 58, True)
            y += 68
        y += 12
        for text in body:
            check(text, 86, y, 37)
            y += 48


def build_storybook_reference(project: Path, directory: Path, *, deadline: float) -> StorybookReference:
    """Reconstruct ordered source images privately, never from output manifests."""
    if not math.isfinite(deadline) or time.monotonic() >= deadline:
        raise TimeoutError("storybook source reconstruction deadline")
    before = source_identity(project)
    raw = read_source_yaml(project / "content/story.yaml")
    if not isinstance(raw, dict) or set(raw) != {"storybook", "characters", "pages"}:
        raise ValueError("unsupported storybook source shape")
    if set(raw["storybook"]) != {"title", "subtitle", "trim_size", "output_pdf", "page_width", "page_height"}:
        raise ValueError("unsupported storybook settings")
    page_keys = {"number", "slug", "title", "scene", "text", "overlay_box", "palette"}
    for page in raw["pages"]:
        if not isinstance(page, dict) or not page_keys <= set(page) or set(page) - page_keys - {"caption_position"}:
            raise ValueError("unsupported storybook page fields")
    if {character.get("id") for character in raw["characters"] if isinstance(character, dict)} != {
        "tessa",
        "ciro",
        "cube_family",
        "tetra_family",
    }:
        raise ValueError("unsupported storybook scene cast")
    for character in raw["characters"]:
        if set(character) != {"id", "name", "shape", "family_shape", "fill", "accent", "role"}:
            raise ValueError("unsupported storybook character fields")
    rendering = source_package(project, "storybook")
    spec = rendering.load_storybook(project)
    if spec.trim_size != "portrait" or (spec.page_width, spec.page_height) != (1275, 1650):
        raise ValueError("unsupported storybook caption/scene geometry")
    if spec.output_pdf.is_absolute() or ".." in spec.output_pdf.parts:
        raise ValueError("storybook output resource escapes source project")
    if any(re.fullmatch(r"[a-z0-9_]+", page.slug) is None for page in spec.pages):
        raise ValueError("unsupported storybook page slug")
    if not 1 <= len(spec.pages) <= 32 or spec.page_width * spec.page_height > 10_000_000:
        raise ValueError("unsupported storybook size")
    directory.mkdir(parents=True, exist_ok=True)
    images = []
    for index, page in enumerate(spec.pages):
        if time.monotonic() >= deadline:
            raise TimeoutError("storybook source reconstruction deadline")
        _caption_bounds(spec, page, rendering)
        path = directory / f"source-{index}.png"
        rendering.render_page_image(spec, page, path)
        images.append(path.read_bytes())
    # Assemble independently; never call the producer contact-sheet builder.
    thumbs = []
    for data in images:
        image = Image.open(BytesIO(data)).convert("RGB")
        image.thumbnail((320, 460), Image.Resampling.LANCZOS)
        thumbs.append(image)
    cell_height = max(image.height for image in thumbs) + 58
    sheet = Image.new("RGB", (4 * 352, ((len(thumbs) + 3) // 4) * cell_height), "white")
    draw = ImageDraw.Draw(sheet)
    for index, (image, page) in enumerate(zip(thumbs, spec.pages, strict=True)):
        x = (index % 4) * 352 + (352 - image.width) // 2
        y = (index // 4) * cell_height + 8
        sheet.paste(image, (x, y))
        draw.text(
            (x, y + image.height + 8),
            f"{index + 1:02d} · {Path(page.filename).stem}",
            font=ImageFont.load_default(),
            fill=(24, 28, 42),
        )
    stream = BytesIO()
    sheet.save(stream, format="PNG")
    if source_identity(project) != before:
        raise ValueError("source changed during storybook reconstruction")
    return StorybookReference(
        before,
        (spec.page_width, spec.page_height),
        tuple(page.filename for page in spec.pages),
        tuple(images),
        stream.getvalue(),
    )


def inspect_storybook_artifact(
    data: bytes, reference: StorybookReference, *, kind: str, page_number: int | None = None
) -> dict[str, object]:
    """Reject altered pixels, page geometry/order, overlay operators or clipping."""
    if len(data) > LIMIT:
        raise ValueError("storybook artifact exceeds bound")
    if kind == "page":
        if type(page_number) is not int or not 0 <= page_number < len(reference.pages):
            raise ValueError("unknown storybook page")
        if pixels(data) != pixels(reference.pages[page_number]):
            raise ValueError("storybook page differs from source pixels")
    elif kind == "contact-sheet":
        if pixels(data) != pixels(reference.contact_sheet):
            raise ValueError("storybook contact sheet differs from ordered source pages")
    elif kind == "pdf":
        document = PdfReader(BytesIO(data), strict=True)
        if document.is_encrypted or len(document.pages) != len(reference.pages):
            raise ValueError("storybook print page count/encryption")
        catalog = cast(Any, document.trailer["/Root"])
        if catalog.get("/OpenAction") or catalog.get("/AA"):
            raise ValueError("unsupported storybook active PDF content")
        width, height = reference.dimensions
        for index, page in enumerate(document.pages):
            if (
                tuple(float(value) for value in page.mediabox) != (0, 0, width, height)
                or tuple(page.cropbox) != tuple(page.mediabox)
                or page.rotation
                or page.get("/Annots")
            ):
                raise ValueError("storybook print geometry/annotation")
            operations = ContentStream(page.get_contents(), document).operations
            # The source canvas emits this exact full-page image program.
            expected_ops = [b"cm", b"BT", b"Tf", b"TL", b"ET", b"q", b"cm", b"Do", b"Q"]
            if [op for _, op in operations] != expected_ops:
                raise ValueError("unsupported storybook PDF drawing/hidden overlay")
            if [float(item) for item in operations[0][0]] != [1, 0, 0, 1, 0, 0]:
                raise ValueError("storybook transformed page image")
            objects = cast(Any, page["/Resources"])["/XObject"]
            if len(objects) != 1 or str(operations[7][0][0]) not in objects:
                raise ValueError("unsupported storybook image resource")
            image_object = next(iter(objects.values())).get_object()
            if (
                set(image_object)
                != {"/BitsPerComponent", "/ColorSpace", "/Filter", "/Height", "/Subtype", "/Type", "/Width"}
                or image_object["/ColorSpace"] != "/DeviceRGB"
                or image_object["/BitsPerComponent"] != 8
                or image_object["/Width"] != width
                or image_object["/Height"] != height
                or list(image_object["/Filter"]) != ["/ASCII85Decode", "/FlateDecode"]
            ):
                raise ValueError("unsupported storybook image decode/transparency")
            if [float(item) for item in operations[6][0]] != [width, 0, 0, height, 0, 0]:
                raise ValueError("storybook image placement/clipping")
            if len(page.images) != 1 or pixels(page.images[0].data) != pixels(reference.pages[index]):
                raise ValueError("storybook embedded image differs from ordered source")
    else:
        raise ValueError("unsupported storybook artifact kind")
    return {
        "schema_version": "template-storybook-native-v1",
        "kind": kind,
        "source_sha256": reference.source_sha256,
        "artifact_sha256": hashlib.sha256(data).hexdigest(),
        "pages": len(reference.pages),
    }
