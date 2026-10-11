"""Real source-only unnumbered section labels under an explicit archive policy."""

from __future__ import annotations

import hashlib
import time

import pytest

from infrastructure.reporting.native_format_pdf_source_labels import (
    reconstruct_source_reference_labels,
    replay_source_reference_label_bytes,
)
from tests.infra_tests.reporting.test_native_pdf_source_witness import tex_pdf


@pytest.fixture(scope="module")
def source_section_aux(tmp_path_factory: pytest.TempPathFactory) -> tuple[bytes, bytes]:
    path = tmp_path_factory.mktemp("unnumbered-original-section") / "original.tex"
    tex = (
        r"\documentclass[10pt]{article}\begin{document}"
        "\n"
        r"\section*{Original Section}\label{sec:original}"
        "\n"
        r"\begin{equation}x^2\label{eq:original}\end{equation}"
        "\n"
        r"\end{document}"
        "\n"
    )
    tex_pdf(path, tex)
    return path.read_bytes(), path.with_suffix(".aux").read_bytes()


def test_genuine_unnumbered_source_section_requires_explicit_policy(source_section_aux: tuple[bytes, bytes]) -> None:
    source, aux = source_section_aux
    with pytest.raises(ValueError, match="unresolved literal label number"):
        reconstruct_source_reference_labels(source, aux)
    original = reconstruct_source_reference_labels(source, aux, allowed_unnumbered_labels=("sec:original",))
    assert original["label_numbers"] == {"eq:original": "1"}
    assert original["unnumbered_labels"] == [{"label": "sec:original", "page": "1"}]
    with pytest.raises(ValueError, match="independently numbered witness"):
        reconstruct_source_reference_labels(
            source, aux, allowed_unnumbered_labels=("sec:original",), requested_labels=("sec:original",)
        )


@pytest.mark.parametrize("allowlist", [("sec:invented",), ("sec:original", "sec:original")])
def test_archive_unnumbered_allowlist_cannot_invent_or_duplicate_source_labels(
    source_section_aux: tuple[bytes, bytes], allowlist: tuple[str, ...]
) -> None:
    with pytest.raises(ValueError, match="exact declared literals"):
        reconstruct_source_reference_labels(*source_section_aux, allowed_unnumbered_labels=allowlist)


def test_portable_unnumbered_source_policy_recomputes_original_declared_rows(
    source_section_aux: tuple[bytes, bytes],
) -> None:
    source, aux = source_section_aux
    original = reconstruct_source_reference_labels(source, aux, allowed_unnumbered_labels=("sec:original",))
    payloads = {"source.tex": source, "projection.tex": source, "original-source-only.aux": aux}
    bindings = {
        path: {"path": path, "sha256": hashlib.sha256(content).hexdigest()} for path, content in payloads.items()
    }

    def retained(binding: dict[str, str]) -> bytes:
        return payloads[binding["path"]]

    result = replay_source_reference_label_bytes(
        original,
        source_tex_binding=bindings["source.tex"],
        projection_tex_binding=bindings["projection.tex"],
        original_aux_binding=bindings["original-source-only.aux"],
        read_artifact=retained,
        deadline=time.monotonic() + 10,
    )
    assert result == original
