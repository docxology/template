"""Tests for infrastructure.core.files.pdf_locator.

No mocks used — all tests operate on real files under ``tmp_path``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.core.files.pdf_locator import (
    find_combined_pdf,
    find_last_output_segment_index,
)

PROJECT_NAME = "demo_project"
PDF_BYTES = b"%PDF-1.4\n% not a real PDF, but non-empty and recognizable\n"


def _make_pdf(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(PDF_BYTES)
    return path


class TestFindLastOutputSegmentIndex:
    def test_returns_none_when_no_output_segment(self) -> None:
        assert find_last_output_segment_index(("foo", "bar", "baz")) is None

    def test_returns_single_occurrence_index(self) -> None:
        parts = ("Users", "me", "proj", "output", "demo")
        assert find_last_output_segment_index(parts) == 3

    def test_returns_last_occurrence_for_nested_output_dirs(self) -> None:
        # A parent dir named 'output' must not corrupt the derivation.
        parts = ("Users", "me", "output", "proj", "output", "demo")
        assert find_last_output_segment_index(parts) == 4

    def test_handles_trailing_output_segment(self) -> None:
        parts = ("proj", "output")
        assert find_last_output_segment_index(parts) == 1


class TestFindCombinedPdfPostCopyLayout:
    """Search order #1: output_dir/{project}_combined.pdf (root of copied outputs)."""

    def test_finds_pdf_at_root_of_output_dir(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output" / PROJECT_NAME
        output_dir.mkdir(parents=True)
        pdf = _make_pdf(output_dir / f"{PROJECT_NAME}_combined.pdf")

        result = find_combined_pdf(output_dir, PROJECT_NAME)

        assert result is not None
        found_path, size_mb = result
        assert found_path == pdf
        assert size_mb > 0.0

    def test_ignores_empty_root_pdf_and_falls_through(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output" / PROJECT_NAME
        output_dir.mkdir(parents=True)
        # Empty file — must not count as "found".
        (output_dir / f"{PROJECT_NAME}_combined.pdf").write_bytes(b"")
        pdf_in_dir = _make_pdf(output_dir / "pdf" / f"{PROJECT_NAME}_combined.pdf")

        result = find_combined_pdf(output_dir, PROJECT_NAME)

        assert result is not None
        found_path, _size = result
        assert found_path == pdf_in_dir


class TestFindCombinedPdfGenerationLayout:
    """Search order #2: output_dir/pdf/{project}_combined.pdf (original render location)."""

    def test_finds_pdf_in_pdf_subdir(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output" / PROJECT_NAME
        output_dir.mkdir(parents=True)
        pdf = _make_pdf(output_dir / "pdf" / f"{PROJECT_NAME}_combined.pdf")

        result = find_combined_pdf(output_dir, PROJECT_NAME)

        assert result is not None
        found_path, _ = result
        assert found_path == pdf


class TestFindCombinedPdfSourceLayout:
    """Search order #3: projects/{project}/output/pdf/ (pre-copy validation)."""

    def test_finds_pdf_in_source_project_layout(self, tmp_path: Path) -> None:
        # Simulate the template repo layout: <repo>/projects/{name}/output/pdf/
        repo_root = tmp_path
        source_output = repo_root / "projects" / PROJECT_NAME / "output"
        source_output.mkdir(parents=True)
        source_pdf = _make_pdf(
            source_output / "pdf" / f"{PROJECT_NAME}_combined.pdf"
        )

        # Stage 4 may be validating the *copied* output dir before Stage 5 has run.
        copied_output = repo_root / "output" / PROJECT_NAME
        copied_output.mkdir(parents=True)

        result = find_combined_pdf(copied_output, PROJECT_NAME)

        assert result is not None
        found_path, _ = result
        assert found_path == source_pdf

    def test_returns_none_when_pdf_missing_from_all_locations(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output" / PROJECT_NAME
        output_dir.mkdir(parents=True)

        result = find_combined_pdf(output_dir, PROJECT_NAME)

        assert result is None


class TestFindCombinedPdfRobustnessAgainstNestedOutputDirs:
    """Regression test for the session-10 rindex bug.

    A parent directory named ``output`` must not corrupt the derivation of the
    source project path. Use the LAST ``output`` segment, not the first.
    """

    def test_parent_output_dir_does_not_corrupt_source_lookup(self, tmp_path: Path) -> None:
        # Simulate an unfortunate layout where a parent dir is also named 'output'.
        repo_root = tmp_path / "output" / "workspace"
        repo_root.mkdir(parents=True)

        source_output = repo_root / "projects" / PROJECT_NAME / "output"
        source_output.mkdir(parents=True)
        source_pdf = _make_pdf(
            source_output / "pdf" / f"{PROJECT_NAME}_combined.pdf"
        )

        copied_output = repo_root / "output" / PROJECT_NAME
        copied_output.mkdir(parents=True)

        result = find_combined_pdf(copied_output, PROJECT_NAME)

        assert result is not None, (
            "Helper must use the LAST 'output' segment so nested parent dirs "
            "don't corrupt the repo-root derivation."
        )
        found_path, _ = result
        assert found_path == source_pdf


class TestFindCombinedPdfFallbackWhenNoOutputSegment:
    """If *output_dir* doesn't contain any 'output' segment, fall back to
    ``output_dir.parent.parent / projects / {name} / output / pdf``."""

    def test_fallback_source_layout(self, tmp_path: Path) -> None:
        # output_dir has no 'output' segment in its parts.
        fake_root = tmp_path / "work" / "area"
        fake_root.mkdir(parents=True)

        # The fallback computes output_dir.parent.parent / projects / {name} / ...
        # So project source must live under tmp_path / projects / {name} / output / pdf
        source_pdf_dir = tmp_path / "projects" / PROJECT_NAME / "output" / "pdf"
        source_pdf = _make_pdf(source_pdf_dir / f"{PROJECT_NAME}_combined.pdf")

        result = find_combined_pdf(fake_root, PROJECT_NAME)

        assert result is not None
        found_path, _ = result
        assert found_path == source_pdf


class TestFindCombinedPdfMatchesLegacyName:
    """The helper must preserve the ``_find_combined_pdf`` legacy import name via
    re-export in the validator module, so downstream code that reached in via
    ``from infrastructure.validation.output.validator import _find_combined_pdf``
    continues to work."""

    def test_validator_reexport_still_importable(self) -> None:
        from infrastructure.validation.output.validator import (  # noqa: WPS433 - test-only deep import
            _find_combined_pdf,
        )

        # Should be the same callable (or a rebinding) as the canonical helper.
        assert callable(_find_combined_pdf)

    def test_pdf_locator_is_canonical_source(self) -> None:
        from infrastructure.core.files import find_combined_pdf as reexported

        assert reexported is find_combined_pdf


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
