"""Page grid layout and PDF export for manuscript overviews.

Arranges page images in a grid layout and exports as PDF.

Part of the infrastructure reporting layer (Layer 1) - reusable across projects.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import TYPE_CHECKING

from infrastructure.core.exceptions import ValidationError
from infrastructure.core.logging.utils import get_logger

if TYPE_CHECKING:
    import PIL.Image

logger = get_logger(__name__)


def create_page_grid(
    images: list["PIL.Image.Image"],
    cols: int = 4,
    padding: int = 10,
    max_thumb_size: tuple[int, int] = (600, 800),
) -> "PIL.Image.Image":
    """Arrange page images in a grid layout.

    Args:
        images: List of PIL Images (one per page)
        cols: Number of columns in grid (default: 4)
        padding: Padding between thumbnails in pixels (default: 10)
        max_thumb_size: Maximum size for each thumbnail (width, height) (default: 600x800)

    Returns:
        Single PIL Image containing the grid layout
    """
    if not images:
        raise ValidationError("No images provided for grid creation")

    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as e:
        raise ImportError("PIL required for image processing") from e

    # Calculate grid dimensions
    num_images = len(images)
    rows = math.ceil(num_images / cols)

    # Resize images to fit grid cells
    thumb_width, thumb_height = max_thumb_size
    resized_images = []

    for img in images:
        # Maintain aspect ratio
        img_ratio = img.width / img.height
        if img.width > img.height:
            # Landscape or square
            new_width = min(img.width, thumb_width)
            new_height = int(new_width / img_ratio)
            if new_height > thumb_height:
                new_height = thumb_height
                new_width = int(new_height * img_ratio)
        else:
            # Portrait
            new_height = min(img.height, thumb_height)
            new_width = int(new_height * img_ratio)
            if new_width > thumb_width:
                new_width = thumb_width
                new_height = int(new_width / img_ratio)

        # Resize image
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        resized_images.append(resized)

    # Calculate grid dimensions
    grid_width = cols * (thumb_width + padding) + padding
    grid_height = rows * (thumb_height + padding) + padding

    # Create grid image
    grid_img = Image.new("RGB", (grid_width, grid_height), color="white")
    draw = ImageDraw.Draw(grid_img)

    # Try to load font for page numbers
    try:
        font = ImageFont.truetype("Helvetica", 10)
    except OSError as e:
        logger.debug(f"Could not load Helvetica font: {e}")
        font = ImageFont.load_default()

    # Place images in grid
    for i, img in enumerate(resized_images):
        row = i // cols
        col = i % cols

        x = col * (thumb_width + padding) + padding
        y = row * (thumb_height + padding) + padding

        # Center image in cell if smaller than max size
        cell_center_x = x + thumb_width // 2
        cell_center_y = y + thumb_height // 2
        img_x = cell_center_x - img.width // 2
        img_y = cell_center_y - img.height // 2

        # Paste image
        grid_img.paste(img, (img_x, img_y))

        # Add page number label
        label = f"Page {i + 1}"
        draw.text((img_x + 5, img_y + 5), label, fill="black", font=font)

    # Add title
    title = f"Manuscript Overview - {num_images} Pages"
    try:
        title_font = ImageFont.truetype("Helvetica-Bold", 16)
    except OSError as e:
        logger.debug(f"Could not load Helvetica-Bold font: {e}")
        title_font = ImageFont.load_default()

    draw.text((padding, padding // 2), title, fill="black", font=title_font)

    return grid_img


def _save_image_as_pdf(image: "PIL.Image.Image", pdf_path: Path, title: str) -> None:
    """Save a PIL Image as a PDF file using reportlab."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.utils import ImageReader
        from reportlab.pdfgen import canvas
    except ImportError as e:
        raise ImportError("reportlab required for PDF output") from e

    # Create PDF with the image
    c = canvas.Canvas(str(pdf_path), pagesize=letter)

    # Calculate scaling to fit page
    page_width, page_height = letter
    img_width, img_height = image.size

    # Scale to fit page with margins
    margin = 50
    available_width = page_width - 2 * margin
    available_height = page_height - 2 * margin

    scale_x = available_width / img_width
    scale_y = available_height / img_height
    scale = min(scale_x, scale_y)

    new_width = img_width * scale
    new_height = img_height * scale

    # Center on page
    x = (page_width - new_width) / 2
    y = (page_height - new_height) / 2

    # Convert PIL image to reportlab ImageReader
    img_reader = ImageReader(image)

    # Draw image
    c.drawImage(img_reader, x, y, width=new_width, height=new_height)

    # Add title
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(page_width / 2, page_height - 30, title)

    c.save()
