"""Genuine source-only XeTeX AUX plus strict data/replay negative controls."""

from __future__ import annotations

import copy
import hashlib
import time
from pathlib import Path

import pytest

from infrastructure.reporting.native_format_pdf_source_labels import (
    original_source_labels,
    reconstruct_source_reference_labels,
    replay_source_reference_label_bytes,
)
from tests.infra_tests.reporting.test_native_pdf_source_witness import tex_pdf

SOURCE_TEX = (
    r"\documentclass[10pt]{article}"
    "\n"
    r"\begin{document}\section{Original Section}\label{sec:original}"
    "\n"
    r"\begin{equation}x^2\label{eq:original}\end{equation}"
    "\n"
    r"\end{document}"
    "\n"
)


@pytest.fixture(scope="module")
def original_source_aux(tmp_path_factory: pytest.TempPathFactory) -> tuple[bytes, bytes]:
    directory = tmp_path_factory.mktemp("source-only-labels")
    path = directory / "original.tex"
    tex_pdf(path, SOURCE_TEX)
    return path.read_bytes(), path.with_suffix(".aux").read_bytes()


def test_genuine_source_only_section_and_equation_label_numbers(original_source_aux: tuple[bytes, bytes]) -> None:
    source, aux = original_source_aux
    actual = reconstruct_source_reference_labels(source, aux)
    assert actual["label_numbers"] == {"eq:original": "1", "sec:original": "1"}
    assert {row["label"] for row in actual["declared_labels"]} == {"eq:original", "sec:original"}
    assert actual["source_aux_sha256"] == hashlib.sha256(aux).hexdigest()


@pytest.mark.parametrize(
    "control,reason",
    [
        ("missing", "omits"),
        ("duplicate", "repeats"),
        ("invented", "undeclared"),
        ("dynamic-number", "unresolved"),
        ("residual-command", "residual"),
        ("unbalanced", "unterminated"),
    ],
)
def test_actual_source_aux_mutations_are_rejected(
    original_source_aux: tuple[bytes, bytes], control: str, reason: str
) -> None:
    source, aux = original_source_aux
    original = next(line for line in aux.splitlines(keepends=True) if line.startswith(rb"\newlabel{sec:original}"))
    body = original.rstrip(b"\r\n")
    newline = original[len(body) :]
    assert body.endswith(b"}")
    changed = {
        "missing": aux.replace(original, b""),
        "duplicate": aux + original,
        "invented": aux + original.replace(b"sec:original", b"sec:invented"),
        "dynamic-number": aux.replace(original, original.replace(b"{{1}", rb"{{\dynamic}")),
        "residual-command": aux.replace(original, original.rstrip() + rb"\input{outside}" + b"\n"),
        "unbalanced": aux.replace(original, body[:-1] + newline),
    }[control]
    assert changed != aux, "negative control must alter the retained genuine AUX bytes"
    with pytest.raises(ValueError, match=reason):
        reconstruct_source_reference_labels(source, changed)


def test_literal_source_label_policy_excludes_comments_and_verbatim() -> None:
    source = (
        b"% \\label{comment}\n"
        rb"\verb|\label{literal}|" + b"\n"
        rb"\begin{verbatim}\label{literal-two}\end{verbatim}" + b"\n"
        rb"\section{Source}\label{sec:actual}" + b"\n"
    )
    assert [row["label"] for row in original_source_labels(source)] == ["sec:actual"]
    with pytest.raises(ValueError, match="dynamic"):
        original_source_labels(rb"\label{\dynamic}")
    with pytest.raises(ValueError, match="repeats"):
        original_source_labels(rb"\label{a}\label{a}")


def _bindings(payloads: dict[str, bytes]) -> dict[str, dict[str, str]]:
    return {path: {"path": path, "sha256": hashlib.sha256(content).hexdigest()} for path, content in payloads.items()}


def test_portable_source_label_map_is_recomputed_without_origin_access(
    original_source_aux: tuple[bytes, bytes],
) -> None:
    source, aux = original_source_aux
    original = reconstruct_source_reference_labels(source, aux, requested_labels=("sec:original",))
    payloads = {"source.tex": source, "projection.tex": source, "source-only.aux": aux}
    bindings = _bindings(payloads)

    def retained(binding: dict[str, str]) -> bytes:
        return payloads[binding["path"]]

    arguments = {
        "source_tex_binding": bindings["source.tex"],
        "projection_tex_binding": bindings["projection.tex"],
        "original_aux_binding": bindings["source-only.aux"],
        "read_artifact": retained,
        "deadline": time.monotonic() + 10,
    }
    assert replay_source_reference_label_bytes(original, **arguments) == original
    changed = copy.deepcopy(original)
    changed["label_numbers"]["sec:original"] = "9"
    with pytest.raises(ValueError, match="portable source-only interpretation"):
        replay_source_reference_label_bytes(changed, **arguments)
    payloads["projection.tex"] = source + b"% changed projection\n"
    arguments["projection_tex_binding"] = _bindings(payloads)["projection.tex"]
    with pytest.raises(ValueError, match="differs from original source projection"):
        replay_source_reference_label_bytes(original, **arguments)


def test_real_changed_counter_aux_cannot_replace_original_source_only_map(
    tmp_path: Path, original_source_aux: tuple[bytes, bytes]
) -> None:
    source, aux = original_source_aux
    original = reconstruct_source_reference_labels(source, aux)
    path = tmp_path / "changed-candidate.tex"
    changed_tex = SOURCE_TEX.replace(r"\begin{document}", r"\begin{document}\setcounter{section}{8}")
    tex_pdf(path, changed_tex)
    changed_aux = path.with_suffix(".aux").read_bytes()
    assert reconstruct_source_reference_labels(path.read_bytes(), changed_aux)["label_numbers"]["sec:original"] == "9"
    payloads = {"source.tex": source, "projection.tex": source, "candidate.aux": changed_aux}
    bindings = _bindings(payloads)

    def retained(binding: dict[str, str]) -> bytes:
        return payloads[binding["path"]]

    with pytest.raises(ValueError, match="portable source-only interpretation"):
        replay_source_reference_label_bytes(
            original,
            source_tex_binding=bindings["source.tex"],
            projection_tex_binding=bindings["projection.tex"],
            original_aux_binding=bindings["candidate.aux"],
            read_artifact=retained,
            deadline=time.monotonic() + 10,
        )
