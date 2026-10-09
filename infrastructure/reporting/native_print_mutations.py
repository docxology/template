"""Deterministic mutations of actual native print bytes for source-owned controls."""

from __future__ import annotations

from io import BytesIO
from typing import Any, cast

from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, NameObject
from reportlab.pdfgen.canvas import Canvas


def mutate_print(content: bytes, name: str, kind: str) -> bytes:
    """Apply source-owned native mutations; baseline bytes are never altered."""
    if name == "baseline":
        return content
    if name in {"caption-pixels", "background-pixels", "png-transparency", "contact-order", "contact-caption"}:
        with Image.open(BytesIO(content)) as original:
            image = original.convert("RGBA" if name == "png-transparency" else "RGB")
        try:
            draw = ImageDraw.Draw(image)
            if name == "png-transparency":
                image.putalpha(0)
            elif name == "contact-order":
                # Swap the first two actual thumbnail cells, keeping every pixel.
                if image.width != 1408 or image.height < 460:
                    raise ValueError("contact control requires canonical source sheet geometry")
                first_tile, second_tile = image.crop((0, 0, 352, 460)), image.crop((352, 0, 704, 460))
                try:
                    image.paste(second_tile, (0, 0))
                    image.paste(first_tile, (352, 0))
                finally:
                    first_tile.close()
                    second_tile.close()
            elif name == "contact-caption":
                draw.rectangle((16, 430, 335, 456), fill="magenta")
            elif name == "caption-pixels":
                draw.rectangle((70, 86, image.width - 70, 280), fill="white")
            else:
                draw.rectangle((400, 600, 620, 810), fill="magenta")
            stream = BytesIO()
            image.save(stream, format="PNG")
            return stream.getvalue()
        finally:
            image.close()
    document = PdfReader(BytesIO(content), strict=True)
    pages = list(document.pages)
    if kind == "storybook" and name == "pdf-font":
        from reportlab.lib.utils import ImageReader

        stream = BytesIO()
        canvas = Canvas(
            stream, pagesize=(float(pages[0].mediabox.width), float(pages[0].mediabox.height)), invariant=True
        )
        for index, page in enumerate(pages):
            with Image.open(BytesIO(page.images[0].data)) as original:
                image = original.convert("RGB")
            try:
                if index == 0:
                    draw = ImageDraw.Draw(image)
                    draw.rectangle((70, 86, image.width - 70, 280), fill="white")
                    draw.text(
                        (80, 100), "Altered visible caption font", fill="black", font=ImageFont.load_default(size=80)
                    )
                canvas.drawImage(
                    ImageReader(image), 0, 0, width=float(page.mediabox.width), height=float(page.mediabox.height)
                )
                canvas.showPage()
            finally:
                image.close()
        canvas.save()
        return stream.getvalue()
    if name == "page-order":
        if len(pages) < 2:
            raise ValueError("print page-order control requires at least two actual source pages")
        pages[0], pages[1] = pages[1], pages[0]
    elif name == "omitted-page":
        if len(pages) < 2:
            raise ValueError("print omission control requires at least two actual source pages")
        pages.pop()
    first = pages[0]
    if name == "pdf-geometry":
        first.mediabox.upper_right = (float(first.mediabox.width) - 20, float(first.mediabox.height))
    elif name == "pdf-clipping":
        first.cropbox.lower_left = (100, 100)
    elif name in {"pdf-hidden", "pdf-image", "pdf-text"}:
        from reportlab.lib.utils import ImageReader

        stream = BytesIO()
        canvas = Canvas(stream, pagesize=(float(first.mediabox.width), float(first.mediabox.height)), invariant=True)
        if name == "pdf-hidden":
            canvas.setFillColorRGB(1, 1, 1)
            canvas.rect(0, 0, float(first.mediabox.width), float(first.mediabox.height) / 2, fill=1, stroke=0)
        elif name == "pdf-image":
            with Image.new("RGB", (80, 80), "magenta") as image:
                ImageDraw.Draw(image).line((0, 0, 79, 79), fill="black", width=8)
                canvas.drawImage(ImageReader(image), 60, 60, width=80, height=80)
        else:
            canvas.setFont("Courier", 18)
            canvas.drawString(55, 200, "Changed visible source measurement 999")
        canvas.showPage()
        canvas.save()
        overlay = PdfReader(BytesIO(stream.getvalue())).pages[0]
        if name != "pdf-text":
            # Empty ReportLab text setup must not turn pixel controls into font controls.
            operations = ContentStream(overlay.get_contents(), overlay.pdf)
            operations.operations = [
                (args, op) for args, op in operations.operations if op not in {b"BT", b"Tf", b"TL", b"ET"}
            ]
            overlay[NameObject("/Contents")] = operations
            cast(Any, overlay["/Resources"]).pop("/Font", None)
        first.merge_page(overlay)
    elif name == "pdf-font":
        font = next(iter(cast(Any, first["/Resources"])["/Font"].values())).get_object()
        font[NameObject("/BaseFont")] = NameObject("/Courier")
    elif name not in {"page-order", "omitted-page"}:
        raise ValueError("unknown native print mutation")
    writer = PdfWriter()
    for page in pages:
        writer.add_page(page)
    stream = BytesIO()
    writer.write(stream)
    return stream.getvalue()
