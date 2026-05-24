"""Tests for infrastructure/reporting/page_grid.py.

Covers: create_page_grid and _save_image_as_pdf with real PIL Images.

No mocks used — all tests use real PIL Image objects and real file I/O.
"""

from __future__ import annotations


import pytest

from infrastructure.core.exceptions import ValidationError


class TestCreatePageGrid:
    """Test create_page_grid with real PIL images."""

    def _make_images(self, count: int, size: tuple[int, int] = (200, 300)):
        """Create real PIL Images."""
        from PIL import Image
        return [Image.new("RGB", size, color=(i * 30 % 256, 100, 200)) for i in range(count)]

    def test_basic_grid(self):
        """Should create a grid image from multiple page images."""
        from infrastructure.reporting.page_grid import create_page_grid
        images = self._make_images(4)
        result = create_page_grid(images, cols=2)
        assert result.width > 0
        assert result.height > 0

    def test_single_image(self):
        """Should handle single image grid."""
        from infrastructure.reporting.page_grid import create_page_grid
        images = self._make_images(1)
        result = create_page_grid(images, cols=1)
        assert result.width > 0

    def test_many_images(self):
        """Should handle many images in grid."""
        from infrastructure.reporting.page_grid import create_page_grid
        images = self._make_images(12)
        result = create_page_grid(images, cols=4)
        assert result.width > 0

    def test_empty_images_raises(self):
        """Should raise ValidationError for empty image list."""
        from infrastructure.reporting.page_grid import create_page_grid
        with pytest.raises(ValidationError):
            create_page_grid([])

    def test_landscape_images(self):
        """Should handle landscape-oriented images."""
        from infrastructure.reporting.page_grid import create_page_grid
        images = self._make_images(2, size=(400, 200))
        result = create_page_grid(images, cols=2)
        assert result.width > 0

    def test_custom_padding(self):
        """Should respect custom padding."""
        from infrastructure.reporting.page_grid import create_page_grid
        images = self._make_images(2)
        result = create_page_grid(images, cols=2, padding=20)
        assert result.width > 0

    def test_custom_thumb_size(self):
        """Should respect custom thumbnail size."""
        from infrastructure.reporting.page_grid import create_page_grid
        images = self._make_images(2)
        result = create_page_grid(images, cols=2, max_thumb_size=(300, 400))
        assert result.width > 0


class TestSaveImageAsPdf:
    """Test _save_image_as_pdf with real images and files."""

    def test_save_pdf(self, tmp_path):
        """Should save a PIL Image as PDF."""
        from PIL import Image
        from infrastructure.reporting.page_grid import _save_image_as_pdf

        img = Image.new("RGB", (800, 600), color="white")
        pdf_path = tmp_path / "test_grid.pdf"
        _save_image_as_pdf(img, pdf_path, "Test Grid")
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0

    def test_save_large_image(self, tmp_path):
        """Should handle large images."""
        from PIL import Image
        from infrastructure.reporting.page_grid import _save_image_as_pdf

        img = Image.new("RGB", (3000, 4000), color="lightblue")
        pdf_path = tmp_path / "large_grid.pdf"
        _save_image_as_pdf(img, pdf_path, "Large Grid")
        assert pdf_path.exists()
