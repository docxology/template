"""Tests for the project-local figure-registry publisher (standalone-safe)."""

from __future__ import annotations

from pathlib import Path

import pytest

from data_descriptor.registry import (
    FigureRegistryError,
    build_generated_figure_registry,
    publish_generated_figures,
    write_generated_figure_registry,
)
from data_descriptor.figures import DESCRIPTOR_FIGURE_SPECS, FIGURE_REGISTRY_SCHEMA


class TestRegistryBuild:
    """Registry building is fail-closed and byte-deterministic."""

    def test_full_spec_set_builds_registry(self, tmp_path: Path) -> None:
        generated = [tmp_path / spec.filename for spec in DESCRIPTOR_FIGURE_SPECS]
        for path in generated:
            path.write_bytes(b"\x89PNG\r\n\x1a\n")

        payload = build_generated_figure_registry(
            DESCRIPTOR_FIGURE_SPECS,
            generated,
            schema_version=FIGURE_REGISTRY_SCHEMA,
        )

        assert payload["schema_version"] == FIGURE_REGISTRY_SCHEMA
        assert {record["label"] for record in payload["figures"]} == {
            "fig:schema_overview",
            "fig:file_inventory",
            "fig:provenance_flow",
            "fig:quality_gate",
            "fig:checksum_verification",
        }
        assert all(record["metadata"]["alt_text"].strip() for record in payload["figures"])

    def test_missing_generated_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FigureRegistryError, match="missing generated figure file"):
            build_generated_figure_registry(
                DESCRIPTOR_FIGURE_SPECS,
                [],
                schema_version=FIGURE_REGISTRY_SCHEMA,
            )

    def test_empty_schema_version_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FigureRegistryError, match="schema_version"):
            build_generated_figure_registry(
                DESCRIPTOR_FIGURE_SPECS,
                [],
                schema_version="   ",
            )

    def test_empty_spec_set_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FigureRegistryError, match="at least one figure"):
            build_generated_figure_registry((), [], schema_version=FIGURE_REGISTRY_SCHEMA)

    def test_duplicate_labels_raise(self, tmp_path: Path) -> None:
        spec_a = DESCRIPTOR_FIGURE_SPECS[0]
        spec_b = DESCRIPTOR_FIGURE_SPECS[1]
        swapped = (
            type(spec_a)(
                label=spec_a.label,
                filename=spec_b.filename,
                caption=spec_a.caption,
                generated_by=spec_a.generated_by,
                alt_text=spec_a.alt_text,
            ),
            spec_a,
        )
        with pytest.raises(FigureRegistryError, match="duplicate figure label"):
            build_generated_figure_registry(swapped, [], schema_version=FIGURE_REGISTRY_SCHEMA)

    def test_non_fig_label_raises(self, tmp_path: Path) -> None:
        spec = DESCRIPTOR_FIGURE_SPECS[0]
        # The real spec labels all start with "fig:"; simulate a bad one.
        bad = type(spec)(
            label="schema_overview",
            filename=spec.filename,
            caption=spec.caption,
            generated_by=spec.generated_by,
            alt_text=spec.alt_text,
        )
        with pytest.raises(FigureRegistryError, match="must start with 'fig:'"):
            build_generated_figure_registry((bad,), [], schema_version=FIGURE_REGISTRY_SCHEMA)

    def test_non_basename_filename_raises(self, tmp_path: Path) -> None:
        spec = DESCRIPTOR_FIGURE_SPECS[0]
        bad = type(spec)(
            label=spec.label,
            filename="subdir/out.png",
            caption=spec.caption,
            generated_by=spec.generated_by,
            alt_text=spec.alt_text,
        )
        with pytest.raises(FigureRegistryError, match="must be a basename"):
            build_generated_figure_registry((bad,), [], schema_version=FIGURE_REGISTRY_SCHEMA)

    def test_empty_caption_raises(self, tmp_path: Path) -> None:
        spec = DESCRIPTOR_FIGURE_SPECS[0]
        bad = type(spec)(
            label=spec.label,
            filename=spec.filename,
            caption="   ",
            generated_by=spec.generated_by,
            alt_text=spec.alt_text,
        )
        with pytest.raises(FigureRegistryError, match="caption must not be empty"):
            build_generated_figure_registry((bad,), [], schema_version=FIGURE_REGISTRY_SCHEMA)

    def test_empty_generated_by_raises(self, tmp_path: Path) -> None:
        spec = DESCRIPTOR_FIGURE_SPECS[0]
        bad = type(spec)(
            label=spec.label,
            filename=spec.filename,
            caption=spec.caption,
            generated_by="",
            alt_text=spec.alt_text,
        )
        with pytest.raises(FigureRegistryError, match="generated_by must not be empty"):
            build_generated_figure_registry((bad,), [], schema_version=FIGURE_REGISTRY_SCHEMA)

    def test_empty_alt_text_raises(self, tmp_path: Path) -> None:
        spec = DESCRIPTOR_FIGURE_SPECS[0]
        bad = type(spec)(
            label=spec.label,
            filename=spec.filename,
            caption=spec.caption,
            generated_by=spec.generated_by,
            alt_text="   ",
        )
        with pytest.raises(FigureRegistryError, match="alt_text must not be empty"):
            build_generated_figure_registry((bad,), [], schema_version=FIGURE_REGISTRY_SCHEMA)

    def test_duplicate_generated_filename_raises(self, tmp_path: Path) -> None:
        generated = [tmp_path / spec.filename for spec in DESCRIPTOR_FIGURE_SPECS[:2]]
        for path in generated:
            path.write_bytes(b"\x89PNG\r\n\x1a\n")
        with pytest.raises(FigureRegistryError, match="duplicate generated figure filename"):
            build_generated_figure_registry(
                DESCRIPTOR_FIGURE_SPECS[:2],
                [generated[0], generated[0]],
                schema_version=FIGURE_REGISTRY_SCHEMA,
            )

    def test_declared_file_absent_on_disk_raises(self, tmp_path: Path) -> None:
        # A path whose name matches the spec but was never actually created.
        phantom = tmp_path / DESCRIPTOR_FIGURE_SPECS[0].filename
        with pytest.raises(FigureRegistryError, match="do not exist"):
            build_generated_figure_registry(
                DESCRIPTOR_FIGURE_SPECS[:1],
                [phantom],
                schema_version=FIGURE_REGISTRY_SCHEMA,
            )


class TestRegistryPublish:
    """Publishing mirrors files and writes the registry atomically."""

    def test_publish_writes_mirrored_pngs_and_registry(self, tmp_path: Path) -> None:
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        generated: list[Path] = []
        for spec in DESCRIPTOR_FIGURE_SPECS:
            path = source_dir / spec.filename
            path.write_bytes(b"\x89PNG\r\n\x1a\n")
            generated.append(path)
        output_dir = tmp_path / "output" / "figures"

        written = publish_generated_figures(
            output_dir,
            DESCRIPTOR_FIGURE_SPECS,
            generated,
            schema_version=FIGURE_REGISTRY_SCHEMA,
        )

        assert len(written) == len(DESCRIPTOR_FIGURE_SPECS) + 1
        registry_path = output_dir / "figure_registry.json"
        assert registry_path in written
        assert all(path.is_file() for path in written)
        payload = build_generated_figure_registry(
            DESCRIPTOR_FIGURE_SPECS,
            written[:-1],
            schema_version=FIGURE_REGISTRY_SCHEMA,
        )
        assert {record["label"] for record in payload["figures"]} == {
            "fig:schema_overview",
            "fig:file_inventory",
            "fig:provenance_flow",
            "fig:quality_gate",
            "fig:checksum_verification",
        }

    def test_incomplete_set_cannot_publish(self, tmp_path: Path) -> None:
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        generated = [source_dir / spec.filename for spec in DESCRIPTOR_FIGURE_SPECS[:-1]]
        for path in generated:
            path.write_bytes(b"\x89PNG\r\n\x1a\n")
        output_dir = tmp_path / "output" / "figures"

        with pytest.raises(FigureRegistryError, match="missing generated figure file"):
            publish_generated_figures(
                output_dir,
                DESCRIPTOR_FIGURE_SPECS,
                generated,
                schema_version=FIGURE_REGISTRY_SCHEMA,
            )

        assert not output_dir.exists()

    def test_write_is_deterministic(self, tmp_path: Path) -> None:
        generated = [tmp_path / spec.filename for spec in DESCRIPTOR_FIGURE_SPECS]
        for path in generated:
            path.write_bytes(b"\x89PNG\r\n\x1a\n")

        first = tmp_path / "first.json"
        second = tmp_path / "second.json"
        write_generated_figure_registry(
            first,
            DESCRIPTOR_FIGURE_SPECS,
            generated,
            schema_version=FIGURE_REGISTRY_SCHEMA,
        )
        write_generated_figure_registry(
            second,
            DESCRIPTOR_FIGURE_SPECS,
            generated,
            schema_version=FIGURE_REGISTRY_SCHEMA,
        )

        assert first.read_bytes() == second.read_bytes()
