"""Real raster data/order/geometry contracts for slide-specific figure panels."""

from __future__ import annotations
from pathlib import Path
from typing import Any
from math import ceil
import hashlib
import json
import matplotlib.pyplot as plt
from helpers import REPO_ROOT
from template_template.core.introspection import (
    discover_infrastructure_modules,
    discover_projects,
    load_pipeline_stages_from_yaml,
)
from template_template.figures.figure_architecture_overview import (
    _architecture_panel_figure,
    generate_architecture_presentation_panels,
)
from template_template.figures.figure_module_inventory import (
    _module_inventory_panel_figure,
    _module_inventory_figure,
    generate_module_inventory,
    generate_module_inventory_presentation_panels,
)
from template_template.figures.figure_pipeline_stages import (
    generate_pipeline_presentation_panels,
    generate_pipeline_stages,
    _pipeline_overview_figure,
)
from template_template.figures.figure_comparative_panels import generate_comparative_presentation_panels
from template_template.figures.figure_comparative_matrix import (
    comparative_feature_matrix_data,
    _comparative_feature_matrix_figure,
    generate_comparative_feature_matrix,
)
from template_template.figures.viz_palette import doc_badge, presentation_renderer


def _read_measured_panels(manifest_path: Path) -> list[dict[str, Any]]:
    manifest = json.loads(manifest_path.read_text())
    assert set(manifest) == {"schema_version", "panels"}
    assert manifest["schema_version"] == "1.0"
    evidence = []
    for panel in manifest["panels"]:
        assert set(panel) == {"src", "alt", "sha256", "minimum_label_px"}
        path = manifest_path.parent / Path(panel["src"]).name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == panel["sha256"]
        measured = json.loads(path.with_suffix(".labels.json").read_text())
        assert measured["png_sha256"] == panel["sha256"]
        raster = plt.imread(path)
        assert raster.shape[:2] == (measured["height_px"], measured["width_px"])
        minima = []
        for text in measured["text_measurements"]:
            x0, y0, x1, y1 = text["bbox_px"]
            assert 0 <= x0 < x1 <= measured["width_px"]
            assert 0 <= y0 < y1 <= measured["height_px"]
            assert 0 < text["minimum_label_px"] <= min(y1 - y0 + 0.00001, text["font_pixels"])
            minima.append(text["minimum_label_px"])
        assert min(minima) == panel["minimum_label_px"] == measured["minimum_label_px"]
        evidence.append(measured)
    return evidence


def test_architecture_slide_panels_preserve_complete_roster_and_measured_cards(tmp_path: Path) -> None:
    modules = discover_infrastructure_modules(REPO_ROOT)
    projects = discover_projects(REPO_ROOT)
    actual_labels = []
    actual_details = []
    for layer, items in (("Infrastructure", modules), ("Projects", projects)):
        for offset in range(0, len(items), 4):
            fig, ax = _architecture_panel_figure(
                items[offset : offset + 4], layer=layer, panel_number=offset // 4 + 1, panel_count=ceil(len(items) / 4)
            )
            try:
                fig.canvas.draw()
                renderer = presentation_renderer(fig)
                cards = [patch for patch in ax.patches if patch.get_gid() == "architecture-card"]
                labels = [text for text in ax.texts if text.get_gid() == "architecture-card-label"]
                details = [text for text in ax.texts if text.get_gid() == "architecture-card-detail"]
                assert len(cards) == len(labels) == len(details) == len(items[offset : offset + 4])
                for card, label, detail in zip(cards, labels, details, strict=True):
                    extent = card.get_window_extent(renderer)
                    for text in (label, detail):
                        box = text.get_window_extent(renderer)
                        assert extent.contains(box.x0, box.y0) and extent.contains(box.x1, box.y1)
                    assert not label.get_window_extent(renderer).overlaps(detail.get_window_extent(renderer))
                actual_labels.extend("".join(text.get_text().split()) for text in labels)
                actual_details.extend(text.get_text() for text in details)
            finally:
                plt.close(fig)
    assert actual_labels == [module.name.replace("_", "") for module in modules] + [
        project.name.removeprefix("template_").replace("_", "") for project in projects
    ]
    assert actual_details == [f"{module.python_file_count} py\n[{doc_badge(module)}]" for module in modules] + [
        f"{project.chapter_count} chapters\n{project.test_file_count} test files" for project in projects
    ]
    manifest = generate_architecture_presentation_panels(modules, projects, tmp_path, "test-version")
    evidence = _read_measured_panels(manifest)
    assert len(evidence) == ceil(len(modules) / 4) + ceil(len(projects) / 4)


def test_inventory_slide_panels_preserve_sorted_counts_badges_and_measured_labels(tmp_path: Path) -> None:
    modules = discover_infrastructure_modules(REPO_ROOT)
    ordered = sorted(modules, key=lambda module: module.python_file_count, reverse=True)
    for offset in range(0, len(ordered), 6):
        selected = ordered[offset : offset + 6]
        fig, ax = _module_inventory_panel_figure(
            selected, maximum=max(module.python_file_count for module in ordered), first=offset + 1, total=len(ordered)
        )
        try:
            fig.canvas.draw()
            renderer = presentation_renderer(fig)
            names = [text for text in ax.texts if text.get_text() in {module.name for module in selected}]
            bars = list(ax.patches)
            assert len(names) == len(bars) == len(selected)
            for name, bar in zip(names, bars, strict=True):
                assert name.get_window_extent(renderer).x1 < bar.get_window_extent(renderer).x0
        finally:
            plt.close(fig)
    fig, ax = _module_inventory_figure(modules)
    try:
        fig.canvas.draw()
        renderer = presentation_renderer(fig)
        annotations = [text for text in ax.texts if text.get_gid() == "module-count-badge"]
        assert [text.get_text() for text in annotations] == [
            f"{module.python_file_count} [{doc_badge(module)}]" for module in ordered
        ]
        for text, bar in zip(annotations, ax.patches, strict=True):
            box = text.get_window_extent(renderer)
            assert box.x0 > bar.get_window_extent(renderer).x1
            assert fig.bbox.contains(box.x0, box.y0) and fig.bbox.contains(box.x1, box.y1)
        legend = fig.texts[0].get_window_extent(renderer)
        assert fig.bbox.contains(legend.x0, legend.y0) and fig.bbox.contains(legend.x1, legend.y1)
        assert all(
            not legend.overlaps(text.get_window_extent(renderer)) for text in annotations + list(ax.get_yticklabels())
        )
        assert all(
            not first.get_window_extent(renderer).overlaps(second.get_window_extent(renderer))
            for index, first in enumerate(annotations)
            for second in annotations[index + 1 :]
        )
    finally:
        plt.close(fig)
    combined = generate_module_inventory(modules, tmp_path)
    assert (
        json.loads(combined.with_suffix(".labels.json").read_text())["png_sha256"]
        == hashlib.sha256(combined.read_bytes()).hexdigest()
    )
    manifest = generate_module_inventory_presentation_panels(modules, tmp_path)
    evidence = _read_measured_panels(manifest)
    assert len(evidence) == ceil(len(modules) / 6)
    actual = []
    for panel in evidence:
        texts = [row["text"] for row in panel["text_measurements"]]
        body = texts[1:-3]
        assert len(body) % 3 == 0
        actual.extend(zip(body[::3], body[1::3], body[2::3], strict=True))
    assert actual == [(module.name, str(module.python_file_count), f"[{doc_badge(module)}]") for module in ordered]


def test_pipeline_panels_preserve_complete_declarations(tmp_path: Path) -> None:
    stages = load_pipeline_stages_from_yaml(REPO_ROOT)
    fig = _pipeline_overview_figure(stages)
    try:
        fig.canvas.draw()
        renderer = presentation_renderer(fig)
        labels = []
        tags = []
        boxes = []
        assert len(fig.axes) == ceil(len(stages) / 5)
        for ax in fig.axes:
            physical = ax.get_window_extent(renderer)
            assert abs(physical.width / float(fig.dpi) - 9.0) < 0.000001
            assert abs(physical.height / float(fig.dpi) - 6.6) < 0.000001
            labels.extend(
                "".join(text.get_text().split()) for text in ax.texts if text.get_gid() == "pipeline-stage-name"
            )
            tags.extend(
                "".join(text.get_text().split()) for text in ax.texts if text.get_gid() == "pipeline-stage-tags"
            )
            for text in ax.texts:
                box = text.get_window_extent(renderer)
                assert fig.bbox.contains(box.x0, box.y0) and fig.bbox.contains(box.x1, box.y1)
                boxes.append(box)
        assert labels == ["".join(stage.name.split()) for stage in stages]
        assert tags == ["".join(stage.tags) or "(none)" for stage in stages]
        assert all(not box.overlaps(other) for index, box in enumerate(boxes) for other in boxes[index + 1 :])
    finally:
        plt.close(fig)
    overview = generate_pipeline_stages(stages, tmp_path)
    overview_measurements = json.loads(overview.with_suffix(".labels.json").read_text())
    assert overview_measurements["png_sha256"] == hashlib.sha256(overview.read_bytes()).hexdigest()
    assert plt.imread(overview).shape[:2] == (overview_measurements["height_px"], overview_measurements["width_px"])
    manifest = generate_pipeline_presentation_panels(stages, tmp_path)
    measured = _read_measured_panels(manifest)
    actual_names = []
    actual_tags = []
    for panel in measured:
        texts = [item["text"] for item in panel["text_measurements"]][1:]
        assert len(texts) % 3 == 0
        actual_names.extend("".join(name.split()) for name in texts[1::3])
        actual_tags.extend("".join(tags.split()) for tags in texts[2::3])
    assert actual_names == ["".join(stage.name.split()) for stage in stages]
    assert actual_tags == ["".join(("".join(stage.tags) or "(none)").split()) for stage in stages]


def test_matrix_panels_preserve_every_tool_capability_and_cell(tmp_path: Path) -> None:
    data, tools, capabilities = comparative_feature_matrix_data()
    fig, ax, colorbar = _comparative_feature_matrix_figure()
    try:
        fig.canvas.draw()
        renderer = presentation_renderer(fig)
        groups = [text for text in ax.texts if text.get_text() in {"Core Pipeline", "Quality & Security", "Ecosystem"}]
        assert [text.get_text() for text in groups] == ["Core Pipeline", "Quality & Security", "Ecosystem"]
        forbidden = [colorbar.ax.get_window_extent(renderer)] + [
            text.get_window_extent(renderer) for text in colorbar.ax.get_yticklabels()
        ]
        for text in groups:
            box = text.get_window_extent(renderer)
            assert fig.bbox.contains(box.x0, box.y0) and fig.bbox.contains(box.x1, box.y1)
            assert all(not box.overlaps(other) for other in forbidden)
        footer = fig.texts[0].get_window_extent(renderer)
        assert fig.bbox.contains(footer.x0, footer.y0) and fig.bbox.contains(footer.x1, footer.y1)
    finally:
        plt.close(fig)
    assert generate_comparative_feature_matrix(tmp_path).stat().st_size > 1000
    manifest = generate_comparative_presentation_panels(tmp_path)
    panels = _read_measured_panels(manifest)
    key = [row["text"] for row in panels[0]["text_measurements"]][1:-1]
    assert ["".join(text.split()) for text in key] == [
        "".join((chr(65 + index) + tool).split()) for index, tool in enumerate(tools)
    ]
    actual_names = []
    actual_cells = []
    for panel in panels[1:]:
        texts = [row["text"] for row in panel["text_measurements"]]
        assert texts[1:11] == list("ABCDEFGHIJ")
        body = texts[11:-1]
        assert len(body) % 11 == 0
        actual_names.extend("".join(body[index].split()) for index in range(0, len(body), 11))
        actual_cells.extend(body[index + 1 : index + 11] for index in range(0, len(body), 11))
    assert actual_names == ["".join(capability.split()) for capability in capabilities]
    assert actual_cells == [["✓" if value == 1 else "◐" if value == 0.5 else "—" for value in row] for row in data]
