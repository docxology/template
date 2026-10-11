"""Actual fixed Source registry declarations, never JSON-selected callbacks."""

from pathlib import Path

import pytest

from infrastructure.reporting.native_code_figure_registry import SOURCE, declared_code_figure_registry


def _actual_source() -> bytes:
    return (Path(__file__).absolute().parents[3] / SOURCE).read_bytes()


def test_full_real_source_declaration_preserves_every_label_caption_generator_and_alt() -> None:
    raw = _actual_source()
    expected = declared_code_figure_registry(raw)
    assert len(expected) == 6
    assert list(expected) == [
        "fig:convergence",
        "fig:step_sensitivity",
        "fig:convergence_rate",
        "fig:complexity",
        "fig:stability",
        "fig:benchmark",
    ]
    for ordinal, (label, row) in enumerate(expected.items()):
        assert row["figure_id"] == f"figure_{ordinal:03d}"
        assert row["label"] == label and row["generated_by"] == "optimization_analysis.py"
        assert row["caption"] and row["metadata"]["alt_text"]


def test_source_dynamic_declaration_cannot_be_selected_by_a_serialized_registry() -> None:
    raw = _actual_source()
    changed = raw.replace(b"figures = [", b"figures = list([").replace(
        b"        ]\n        for filename, caption, label, alt_text in figures:",
        b"        ])\n        for filename, caption, label, alt_text in figures:",
    )
    # An exact literal Source role is required; malformed or dynamic Source is
    # refused rather than delegated to an arbitrary callable or alleged list.
    with pytest.raises(ValueError, match="literal declaration"):
        declared_code_figure_registry(changed)


def test_omitted_or_reordered_registry_source_loop_is_refused() -> None:
    raw = _actual_source()
    for changed in (
        raw.replace(b" in figures:", b" in figures[:1]:"),
        raw.replace(
            b"filename, caption, label, alt_text in figures:", b"label, caption, filename, alt_text in figures:"
        ),
        raw.replace(b"fm.counter = 0", b"fm.counter = 7"),
    ):
        with pytest.raises(ValueError, match="every declared figure|reset its complete"):
            declared_code_figure_registry(changed)
