"""Actual subprocess oracle for bounded source-native print controls."""

from __future__ import annotations

import argparse
import json
import time
from io import BytesIO
from pathlib import Path
from typing import Any, cast

from PIL import Image, ImageDraw
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas

from infrastructure.reporting.native_newspaper_source import build_newspaper_reference, inspect_newspaper_artifact
from infrastructure.reporting.native_storybook_source import (
    build_storybook_reference,
    inspect_storybook_artifact,
    source_package,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=("storybook", "newspaper"))
    parser.add_argument(
        "mode",
        choices=(
            "baseline",
            "altered",
            "omitted",
            "reordered",
            "hidden",
            "clipped",
            "geometry",
            "font",
            "image",
            "contact-order",
            "transparency",
            "font-resource",
            "png-transparency",
        ),
    )
    parser.add_argument("project", type=Path)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + 120
    if args.kind == "storybook":
        storybook_reference = build_storybook_reference(args.project, args.directory / "reference", deadline=deadline)
        rendering = source_package(args.project, "storybook")
        producer = args.directory / "producer"
        producer.mkdir()
        import shutil

        shutil.copytree(args.project / "content", producer / "content")
        result = rendering.build_storybook_pdf(producer)
        original = result.output_path.read_bytes()
    else:
        newspaper_reference = build_newspaper_reference(args.project, args.directory / "reference", deadline=deadline)
        engine = source_package(args.project, "newspaper")
        config = engine.load_newspaper_config(args.project / "content")
        edition = engine.load_edition(args.project / "content")
        path = args.directory / "producer.pdf"
        engine.render_edition(edition, config, project_root=args.directory / "reference", output_path=path)
        original = path.read_bytes()
    candidate = original
    kind = "pdf"
    if args.mode == "png-transparency":
        if args.kind != "storybook":
            raise ValueError("unsupported control selection")
        image = Image.open(result.image_paths[0]).convert("RGBA")
        image.putalpha(0)
        stream = BytesIO()
        image.save(stream, format="PNG")
        candidate = stream.getvalue()
        kind = "page"
    elif args.mode == "contact-order":
        if args.kind != "storybook":
            raise ValueError("unsupported control selection")
        paths = list(result.image_paths)
        paths.reverse()
        rendering.build_contact_sheet(paths, args.directory / "reordered-sheet.png")
        candidate = (args.directory / "reordered-sheet.png").read_bytes()
        kind = "contact-sheet"
    elif args.kind == "storybook" and args.mode in {"altered", "hidden", "font", "image"}:
        # Mutate the actual embedded raster while preserving the source PDF
        # image-only drawing program, proving decoded pixel readback matters.
        from PIL import ImageFont
        from reportlab.lib.utils import ImageReader

        stream = BytesIO()
        canvas = Canvas(stream, pagesize=storybook_reference.dimensions, invariant=True)
        for index, path in enumerate(result.image_paths):
            image = Image.open(path).convert("RGB")
            if index == 0:
                draw = ImageDraw.Draw(image)
                if args.mode == "hidden":
                    draw.rectangle((0, 0, image.width, image.height), fill="white")
                elif args.mode == "font":
                    draw.rectangle((70, 85, image.width - 70, 330), fill="white")
                    draw.text(
                        (80, 100),
                        "The Shape Between",
                        fill="black",
                        font=ImageFont.load_default(size=100),
                    )
                else:
                    draw.rectangle((400, 500, 650, 750), fill="magenta" if args.mode == "image" else "black")
            width, height = storybook_reference.dimensions
            canvas.drawImage(ImageReader(image), 0, 0, width=width, height=height, preserveAspectRatio=False)
            canvas.showPage()
        canvas.save()
        candidate = stream.getvalue()
    elif args.mode != "baseline":
        reader = PdfReader(BytesIO(original))
        writer = PdfWriter()
        pages = list(reader.pages)
        if args.mode == "omitted":
            pages.pop()
        if args.mode == "reordered":
            pages.reverse()
        for index, page in enumerate(pages):
            if index == 0 and args.mode == "font-resource":
                from pypdf.generic import NameObject

                font = next(iter(cast(Any, page["/Resources"])["/Font"].values())).get_object()
                font[NameObject("/BaseFont")] = NameObject("/Courier")
            if index == 0 and args.mode == "transparency":
                from pypdf.generic import DecodedStreamObject, NameObject, NumberObject

                image = next(iter(cast(Any, page["/Resources"])["/XObject"].values())).get_object()
                mask = DecodedStreamObject()
                mask.set_data(bytes(int(image["/Width"]) * int(image["/Height"])))
                mask.update(
                    {
                        NameObject("/Type"): NameObject("/XObject"),
                        NameObject("/Subtype"): NameObject("/Image"),
                        NameObject("/ColorSpace"): NameObject("/DeviceGray"),
                        NameObject("/BitsPerComponent"): NumberObject(8),
                        NameObject("/Width"): image["/Width"],
                        NameObject("/Height"): image["/Height"],
                    }
                )
                image[NameObject("/SMask")] = mask
            if index == 0:
                if args.mode == "geometry":
                    page.mediabox.upper_right = (float(page.mediabox.width) - 20, float(page.mediabox.height))
                elif args.mode == "clipped":
                    page.cropbox.lower_left = (100, 100)
                elif args.mode in {"hidden", "image", "font", "altered"}:
                    stream = BytesIO()
                    canvas = Canvas(stream, pagesize=tuple(float(x) for x in page.mediabox.upper_right))
                    if args.mode == "hidden":
                        canvas.setFillColorRGB(1, 1, 1)
                        canvas.rect(0, 0, float(page.mediabox.width), float(page.mediabox.height), fill=1, stroke=0)
                    elif args.mode == "image":
                        image = Image.new("RGB", (80, 80), "magenta")
                        ImageDraw.Draw(image).line((0, 0, 79, 79), fill="black", width=8)
                        from reportlab.lib.utils import ImageReader

                        canvas.drawImage(ImageReader(image), 60, 60, 80, 80)
                    else:
                        canvas.setFont("Courier" if args.mode == "font" else "Helvetica", 18)
                        canvas.drawString(55, 200, "Changed visible source measurement 999")
                    canvas.save()
                    page.merge_page(PdfReader(BytesIO(stream.getvalue())).pages[0])
            writer.add_page(page)
        stream = BytesIO()
        writer.write(stream)
        candidate = stream.getvalue()
    (args.directory / "candidate.bin").write_bytes(candidate)
    try:
        if args.kind == "storybook":
            observation = inspect_storybook_artifact(
                candidate, storybook_reference, kind=kind, page_number=0 if kind == "page" else None
            )
            if args.mode == "baseline":
                observation["page_pngs"] = [
                    inspect_storybook_artifact(path.read_bytes(), storybook_reference, kind="page", page_number=index)
                    for index, path in enumerate(result.image_paths)
                ]
                observation["contact_sheet"] = inspect_storybook_artifact(
                    result.contact_sheet_path.read_bytes(), storybook_reference, kind="contact-sheet"
                )
        else:
            observation = inspect_newspaper_artifact(
                candidate,
                newspaper_reference,
                args.directory / "readback",
                pdftoppm=__import__("shutil").which("pdftoppm") or "pdftoppm",
                deadline=deadline,
            )
    except ValueError as error:
        (args.directory / "observation.json").write_text(json.dumps({"refused": str(error)}))
        print(error)
        return 1
    (args.directory / "observation.json").write_text(json.dumps(observation))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
