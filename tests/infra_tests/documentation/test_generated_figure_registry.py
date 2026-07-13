"""Tests for fail-closed generated-figure registry persistence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from infrastructure.documentation.generated_figure_registry import (
    FigureRegistryError,
    build_generated_figure_registry,
    publish_generated_figures,
    write_generated_figure_registry,
)
from infrastructure.validation.content.figure_validator import validate_figure_registry


@dataclass(frozen=True)
class Spec:
    label: str
    filename: str
    caption: str
    generated_by: str


SPECS = (
    Spec("fig:alpha", "alpha.png", "Alpha result.", "analysis.plot_alpha"),
    Spec("fig:beta", "beta.png", "Beta result.", "analysis.plot_beta"),
)


def _write_png_stub(path: Path) -> Path:
    path.write_bytes(b"\x89PNG\r\n\x1a\nregistry-test")
    return path


def test_writer_emits_deterministic_validator_compatible_registry(tmp_path: Path) -> None:
    figures = tmp_path / "figures"
    figures.mkdir()
    alpha = _write_png_stub(figures / "alpha.png")
    beta = _write_png_stub(figures / "beta.png")
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "01_results.md").write_text(
        "![Alpha](../figures/alpha.png){#fig:alpha}\n![Beta](../figures/beta.png){#fig:beta}\n",
        encoding="utf-8",
    )

    registry = write_generated_figure_registry(
        figures / "figure_registry.json",
        reversed(SPECS),
        [beta, alpha],
        schema_version="test-registry-v1",
    )
    first_bytes = registry.read_bytes()
    write_generated_figure_registry(
        registry,
        iter(SPECS),
        [alpha, beta],
        schema_version="test-registry-v1",
    )

    assert registry.read_bytes() == first_bytes
    payload = json.loads(registry.read_text(encoding="utf-8"))
    assert [record["label"] for record in payload["figures"]] == ["fig:alpha", "fig:beta"]
    assert all(record["generated_by"].startswith("analysis.") for record in payload["figures"])
    ok, issues = validate_figure_registry(registry, manuscript)
    assert ok, issues


def test_missing_declared_figure_fails_without_writing_registry(tmp_path: Path) -> None:
    alpha = _write_png_stub(tmp_path / "alpha.png")
    registry = tmp_path / "figure_registry.json"

    with pytest.raises(FigureRegistryError, match=r"missing generated figure file\(s\): beta\.png"):
        write_generated_figure_registry(
            registry,
            SPECS,
            [alpha],
            schema_version="test-registry-v1",
        )

    assert not registry.exists()


def test_publisher_validates_before_mirroring_and_includes_unregistered_extra(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    alpha = _write_png_stub(source / "alpha.png")
    beta = _write_png_stub(source / "beta.png")
    cover = _write_png_stub(source / "cover.png")
    destination = tmp_path / "published"

    written = publish_generated_figures(
        destination,
        iter(SPECS),
        [alpha, beta, cover],
        schema_version="test-registry-v1",
    )

    assert {path.name for path in written} == {
        "alpha.png",
        "beta.png",
        "cover.png",
        "figure_registry.json",
    }
    payload = json.loads((destination / "figure_registry.json").read_text(encoding="utf-8"))
    assert {record["filename"] for record in payload["figures"]} == {"alpha.png", "beta.png"}

    incomplete_destination = tmp_path / "incomplete"
    with pytest.raises(FigureRegistryError, match="missing generated figure file"):
        publish_generated_figures(
            incomplete_destination,
            SPECS,
            [alpha],
            schema_version="test-registry-v1",
        )
    assert not incomplete_destination.exists()


def test_deleted_generated_file_is_rejected(tmp_path: Path) -> None:
    alpha = _write_png_stub(tmp_path / "alpha.png")
    beta = _write_png_stub(tmp_path / "beta.png")
    beta.unlink()

    with pytest.raises(FigureRegistryError, match=r"generated figure path\(s\) do not exist: beta\.png"):
        build_generated_figure_registry(
            SPECS,
            [alpha, beta],
            schema_version="test-registry-v1",
        )


@pytest.mark.parametrize(
    ("specs", "message"),
    [
        ((Spec("alpha", "alpha.png", "caption", "generator"),), "must start with 'fig:'"),
        ((Spec("fig:alpha", "nested/alpha.png", "caption", "generator"),), "must be a basename"),
        ((Spec("fig:alpha", "alpha.png", "", "generator"),), "caption must not be empty"),
        ((Spec("fig:alpha", "alpha.png", "caption", ""),), "generated_by must not be empty"),
    ],
)
def test_invalid_spec_metadata_is_rejected(tmp_path: Path, specs: tuple[Spec, ...], message: str) -> None:
    alpha = _write_png_stub(tmp_path / "alpha.png")
    with pytest.raises(FigureRegistryError, match=message):
        build_generated_figure_registry(specs, [alpha], schema_version="test-registry-v1")


def test_duplicate_labels_and_filenames_are_rejected(tmp_path: Path) -> None:
    alpha = _write_png_stub(tmp_path / "alpha.png")
    duplicate_label = (
        SPECS[0],
        Spec("fig:alpha", "beta.png", "Beta result.", "analysis.plot_beta"),
    )
    duplicate_filename = (
        SPECS[0],
        Spec("fig:beta", "alpha.png", "Beta result.", "analysis.plot_beta"),
    )

    with pytest.raises(FigureRegistryError, match="duplicate figure label"):
        build_generated_figure_registry(duplicate_label, [alpha], schema_version="test-registry-v1")
    with pytest.raises(FigureRegistryError, match="duplicate figure filename"):
        build_generated_figure_registry(duplicate_filename, [alpha], schema_version="test-registry-v1")


def test_empty_schema_and_specs_are_rejected(tmp_path: Path) -> None:
    alpha = _write_png_stub(tmp_path / "alpha.png")
    with pytest.raises(FigureRegistryError, match="schema_version must not be empty"):
        build_generated_figure_registry(SPECS, [alpha], schema_version=" ")
    with pytest.raises(FigureRegistryError, match="must declare at least one figure"):
        build_generated_figure_registry((), [alpha], schema_version="test-registry-v1")
