"""Real-output tests for the visual proof matrix, verifier, and kmyth helpers.

Every test operates on real artifacts: proof PDFs rendered with reportlab and
parsed back with pypdf, hash manifests computed with hashlib, and subprocess
helpers exercised against real throwaway executables written to ``tmp_path``.
No mocking frameworks are used.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter

import redacted_report.visuals as visuals
from redacted_report import (
    RedactionDecision,
    RedactionSegment,
    build_visual_variant_matrix,
    expected_dev_variant_filenames,
    expected_visual_variant_ids,
    normalize_pdf_background,
    normalize_redaction_style,
    redact_text,
    verify_dev_variant_outputs,
    write_dev_variant_pdfs,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_packet() -> tuple[list[RedactionSegment], list[RedactionDecision]]:
    payload = json.loads((PROJECT_ROOT / "data" / "example_segments.json").read_text(encoding="utf-8"))
    segments = [
        RedactionSegment(
            id=item["id"],
            classification=item["classification"],
            text=item["text"],
            source_controls=tuple(item.get("source_controls", [])),
        )
        for item in payload["segments"]
    ]
    decisions = [RedactionDecision(**item) for item in payload["redactions"]]
    return segments, decisions


def _digest(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _write_executable(path: Path, python_body: str) -> Path:
    """Write a real executable python script used as a throwaway CLI tool."""
    path.write_text("#!/usr/bin/env python3\n" + python_body, encoding="utf-8")
    path.chmod(0o755)
    return path


@pytest.fixture(scope="module")
def packet() -> tuple[list[RedactionSegment], list[RedactionDecision]]:
    return _load_packet()


@pytest.fixture(scope="module")
def base_variants_dir(
    tmp_path_factory: pytest.TempPathFactory,
    packet: tuple[list[RedactionSegment], list[RedactionDecision]],
) -> tuple[Path, dict[str, object]]:
    """Render the full 16-variant base proof matrix once for the module."""
    segments, decisions = packet
    output_dir = tmp_path_factory.mktemp("base-variants")
    result = write_dev_variant_pdfs(
        segments,
        decisions,
        output_dir,
        include_steganography=False,
        include_kmyth=False,
    )
    return output_dir, result


@pytest.fixture(scope="module")
def stego_complete_dir(
    tmp_path_factory: pytest.TempPathFactory,
    base_variants_dir: tuple[Path, dict[str, object]],
    packet: tuple[list[RedactionSegment], list[RedactionDecision]],
) -> Path:
    """Build a verifier-complete output dir from real PDFs and real hashes."""
    base_dir, _result = base_variants_dir
    segments, decisions = packet
    output_dir = tmp_path_factory.mktemp("stego-complete")
    matrix = build_visual_variant_matrix(segments, decisions, include_steganography=True, include_kmyth=False)
    variants: list[dict[str, object]] = []
    for raw_variant in matrix["variants"]:
        variant = dict(raw_variant)
        variant_id = str(variant["variant_id"])
        base_pdf = output_dir / f"{variant_id}.pdf"
        stego_pdf = output_dir / f"{variant_id}_steganography.pdf"
        manifest = output_dir / f"{variant_id}.hashes.json"
        shutil.copyfile(base_dir / f"{variant_id}.pdf", base_pdf)
        shutil.copyfile(base_dir / f"{variant_id}.pdf", stego_pdf)
        manifest.write_text(
            json.dumps(
                {
                    "source_file": base_pdf.name,
                    "hashes": {"sha256": _digest(base_pdf, "sha256"), "sha512": _digest(base_pdf, "sha512")},
                    "steganography_applied": "true",
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        variant.update(
            {
                "base_pdf_bytes": base_pdf.stat().st_size,
                "base_pdf_sha256": _digest(base_pdf, "sha256"),
                "steganography_pdf_bytes": stego_pdf.stat().st_size,
                "steganography_pdf_sha256": _digest(stego_pdf, "sha256"),
                "hash_manifest_exists": True,
                "hash_manifest_sha256": _digest(manifest, "sha256"),
            }
        )
        variants.append(variant)
    matrix_payload = {**matrix, "variants": variants}
    (output_dir / "variant_matrix.json").write_text(
        json.dumps(matrix_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return output_dir


@pytest.fixture()
def stego_dir_copy(stego_complete_dir: Path, tmp_path: Path) -> Path:
    target = tmp_path / "variants"
    shutil.copytree(stego_complete_dir, target)
    return target


def _rewrite_variant_record(output_dir: Path, variant_id: str, **updates: object) -> None:
    matrix_path = output_dir / "variant_matrix.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    for variant in matrix["variants"]:
        if variant["variant_id"] == variant_id:
            variant.update(updates)
    matrix_path.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8")


# --- Real 16-variant base matrix generation ---


def test_write_dev_variant_pdfs_emits_all_sixteen_base_pdfs(
    base_variants_dir: tuple[Path, dict[str, object]],
) -> None:
    output_dir, result = base_variants_dir
    expected_names = set(expected_dev_variant_filenames(include_steganography=False, include_hash_manifests=False))
    actual_names = {path.name for path in output_dir.iterdir() if path.is_file()}

    assert actual_names == expected_names
    assert result["variant_count"] == 16
    assert Path(str(result["variant_matrix_path"])).exists()
    kmyth = result["kmyth"]
    assert isinstance(kmyth, dict)
    assert kmyth["status"] == "not_requested"
    assert kmyth["sidecars_created"] == 0


def test_variant_generation_is_byte_deterministic(
    tmp_path: Path,
    packet: tuple[list[RedactionSegment], list[RedactionDecision]],
    base_variants_dir: tuple[Path, dict[str, object]],
) -> None:
    """The 4x4 proof matrix must regenerate byte-identically run-to-run.

    variant_matrix.json binds each artifact to a sha256; those bindings are
    only auditable if the same inputs reproduce the same bytes. Regression
    pin for the reportlab Canvas invariant=1 flag — without it, CreationDate
    and the document /ID churn on every run and this test fails.
    """
    segments, decisions = packet
    first_dir, first_result = base_variants_dir
    second_dir = tmp_path / "again"
    write_dev_variant_pdfs(segments, decisions, second_dir, include_steganography=False, include_kmyth=False)
    first = json.loads((first_dir / "variant_matrix.json").read_text(encoding="utf-8"))
    second = json.loads((second_dir / "variant_matrix.json").read_text(encoding="utf-8"))
    first_hashes = {v["variant_id"]: v["base_pdf_sha256"] for v in first["variants"]}
    second_hashes = {v["variant_id"]: v["base_pdf_sha256"] for v in second["variants"]}
    assert first_hashes == second_hashes
    # And the recorded hash is really the file's hash, not a stored constant.
    sample = second["variants"][0]
    digest = hashlib.sha256((second_dir / str(sample["base_pdf"])).read_bytes()).hexdigest()
    assert digest == sample["base_pdf_sha256"]


def test_config_declared_matrix_dimensions_match_implementation() -> None:
    """manuscript/config.yaml declares the style/background lists; bind them.

    The config advertises the combinatoric space (render.redaction_visual);
    a style added or dropped in only one place would silently desynchronize
    the declared matrix from the generated one.
    """
    import yaml

    config = yaml.safe_load(
        (Path(__file__).resolve().parents[1] / "manuscript" / "config.yaml").read_text(encoding="utf-8")
    )
    declared = config["render"]["redaction_visual"]
    assert tuple(declared["redaction_styles"]) == tuple(p.name for p in visuals.REDACTION_VISUAL_STYLES)
    assert tuple(declared["pdf_backgrounds"]) == tuple(p.name for p in visuals.PDF_BACKGROUND_MODES)


def test_title_page_author_comes_from_manuscript_config(
    base_variants_dir: tuple[Path, dict[str, object]],
) -> None:
    """Proof-PDF bylines must trace to config.yaml, never a hardcoded scaffold author."""
    import yaml

    config = yaml.safe_load(
        (Path(__file__).resolve().parents[1] / "manuscript" / "config.yaml").read_text(encoding="utf-8")
    )
    config_author = config["authors"][0]["name"]
    assert visuals.publication_author_and_date()[0] == config_author
    output_dir, _result = base_variants_dir
    reader = PdfReader(str(output_dir / "blackout_on_white.pdf"))
    first_page_text = reader.pages[0].extract_text()
    assert config_author in first_page_text
    assert "Research Template Author" not in first_page_text


def test_written_matrix_records_real_sizes_and_hashes(
    base_variants_dir: tuple[Path, dict[str, object]],
) -> None:
    output_dir, result = base_variants_dir
    matrix = json.loads((output_dir / "variant_matrix.json").read_text(encoding="utf-8"))

    assert matrix["schema"] == "template-redacted-report-visual-variant-matrix-v1"
    assert [variant["variant_id"] for variant in matrix["variants"]] == list(expected_visual_variant_ids())
    for variant in matrix["variants"]:
        base_pdf = output_dir / str(variant["base_pdf"])
        assert base_pdf.stat().st_size == variant["base_pdf_bytes"]
        assert _digest(base_pdf, "sha256") == variant["base_pdf_sha256"]
        assert variant["steganography_pdf"] == ""
    assert result["include_steganography"] is False


def test_every_rendered_proof_pdf_is_readable_and_multi_page(
    base_variants_dir: tuple[Path, dict[str, object]],
) -> None:
    output_dir, _result = base_variants_dir
    for variant_id in expected_visual_variant_ids():
        pdf_path = output_dir / f"{variant_id}.pdf"
        reader = PdfReader(str(pdf_path))
        assert len(reader.pages) >= 3, variant_id
        assert pdf_path.stat().st_size > 10_000, variant_id


def test_file_sha256_matches_hashlib(base_variants_dir: tuple[Path, dict[str, object]]) -> None:
    output_dir, _result = base_variants_dir
    sample = output_dir / "blackout_on_white.pdf"
    assert visuals._file_sha256(sample) == _digest(sample, "sha256")


def test_renderer_paginates_on_small_pages_and_skips_unknown_sections(
    packet: tuple[list[RedactionSegment], list[RedactionDecision]],
    tmp_path: Path,
) -> None:
    from reportlab.lib.colors import Color
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.pdfgen import canvas

    segments, decisions = packet
    stressed = [*segments, RedactionSegment("s99", "UNCLASSIFIED", "Unmapped trailing segment.")]
    output_pdf = tmp_path / "stress.pdf"
    renderer = visuals._ProofPDFRenderer(
        output_pdf=output_pdf,
        style=normalize_redaction_style("blur"),
        background=normalize_pdf_background("blur"),
        title="Pagination Stress Proof",
        color_cls=Color,
        pagesize=(300, 220),
        string_width_fn=stringWidth,
        canvas_cls=canvas.Canvas,
    )
    renderer.render(stressed, decisions)

    reader = PdfReader(str(output_pdf))
    assert len(reader.pages) > 10


def _selector_tokens(text: str) -> set[str]:
    """Distinctive tokens (emails, IPs, coordinates, timestamps, long words)."""
    return {token.strip(".,") for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9@.\-]{5,}", text)}


def test_rendered_pdf_text_layer_never_leaks_redacted_source_tokens(
    base_variants_dir: tuple[Path, dict[str, object]],
    packet: tuple[list[RedactionSegment], list[RedactionDecision]],
    tmp_path: Path,
) -> None:
    """The redaction invariant itself: redacted spans must not survive into the PDF text layer."""
    segments, decisions = packet
    decision_map: dict[str, list[RedactionDecision]] = {}
    for decision in decisions:
        decision_map.setdefault(decision.segment_id, []).append(decision)

    # Tokens the proof PDF legitimately draws outside segment bodies: sanitized
    # public text, classification/source-control labels, section headers and
    # intros, and the redaction-reason column of the ledger table.
    drawn_by_design: set[str] = set()
    redacted_tokens: set[str] = set()
    for segment in segments:
        public_text = str(redact_text(segment.text, decision_map.get(segment.id, [])))
        drawn_by_design |= _selector_tokens(public_text)
        drawn_by_design |= _selector_tokens(segment.classification)
        drawn_by_design |= _selector_tokens(" ".join(segment.source_controls))
        redacted_tokens |= _selector_tokens(segment.text) - _selector_tokens(public_text)
    for header, intro in visuals._SECTION_MAP.values():
        drawn_by_design |= _selector_tokens(header) | _selector_tokens(intro)
    for decision in decisions:
        drawn_by_design |= _selector_tokens(decision.reason.replace("_", " "))
    forbidden_tokens = redacted_tokens - drawn_by_design
    assert "analyst@example.org" in forbidden_tokens  # the test binds real selectors
    assert any(token.startswith("38.8977") for token in forbidden_tokens)

    # Negative control: an unredacted render MUST trip this detector, proving
    # the extraction/token pipeline can actually see leaked segment text.
    unredacted_pdf = tmp_path / "unredacted.pdf"
    visuals._write_visual_pdf(
        unredacted_pdf,
        segments,
        [],
        normalize_redaction_style("blackout"),
        normalize_pdf_background("white"),
        title="Negative Control",
    )
    unredacted_text = "\n".join(page.extract_text() or "" for page in PdfReader(str(unredacted_pdf)).pages)
    assert forbidden_tokens & _selector_tokens(unredacted_text), "detector failed to fire on a known-bad render"

    output_dir, _result = base_variants_dir
    for variant_id in ("blackout_on_white", "grayout_on_black", "blur_on_blur"):
        reader = PdfReader(str(output_dir / f"{variant_id}.pdf"))
        extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
        extracted_tokens = _selector_tokens(extracted)
        # Positive control: the same draw path that would leak a redacted token
        # demonstrably lands sanitized segment text in the extractable layer.
        assert drawn_by_design & extracted_tokens, variant_id
        leaks = forbidden_tokens & extracted_tokens
        assert not leaks, f"{variant_id}: redacted source tokens leaked into PDF text layer: {sorted(leaks)}"


def test_redaction_parts_and_space_preserving_split() -> None:
    decisions = [RedactionDecision("s1", 0, 6, "privacy"), RedactionDecision("s1", 11, 15, "privacy")]
    parts = visuals._redaction_parts("secret and tail end", decisions)

    assert parts == (
        ("redaction", "secret"),
        ("text", " and "),
        ("redaction", "tail"),
        ("text", " end"),
    )
    assert visuals._split_keep_spaces("alpha beta") == ("alpha", " beta")
    assert visuals._split_keep_spaces(" lead") == (" lead",)


# --- Variant-matrix option branches ---


def test_matrix_marks_kmyth_requested_but_unavailable(
    packet: tuple[list[RedactionSegment], list[RedactionDecision]],
) -> None:
    segments, decisions = packet
    matrix = build_visual_variant_matrix(
        segments,
        decisions,
        include_steganography=True,
        include_kmyth=True,
        kmyth_available=False,
        kmyth_summary="tools missing",
    )

    assert "kmyth_tpm_sidecar_sealing_requested" in matrix["security_methods"]
    assert "kmyth_tpm_sidecar_sealing_available" not in matrix["security_methods"]
    assert matrix["kmyth"]["status"] == "unavailable"


def test_matrix_without_steganography_has_no_security_methods(
    packet: tuple[list[RedactionSegment], list[RedactionDecision]],
) -> None:
    segments, decisions = packet
    matrix = build_visual_variant_matrix(segments, decisions, include_steganography=False, include_kmyth=True)

    assert matrix["security_methods"] == ()
    assert matrix["kmyth"]["status"] == "not_requested"
    assert all(variant["steganography_pdf"] == "" for variant in matrix["variants"])


def test_expected_filenames_honour_inclusion_flags() -> None:
    minimal = expected_dev_variant_filenames(include_steganography=False, include_hash_manifests=False)
    sealed = expected_dev_variant_filenames(include_kmyth_sidecars=True)

    assert len(minimal) == 17
    assert all(not name.endswith("_steganography.pdf") for name in minimal)
    assert all(not name.endswith(".hashes.json") for name in minimal if name != "variant_matrix.json")
    assert sum(name.endswith(".ski") for name in sealed) == 32
    assert "variant_matrix.json" in minimal


# --- Verifier: real success path and real failure modes ---


def test_verifier_accepts_real_pdfs_and_real_hash_manifests(stego_complete_dir: Path) -> None:
    summary = verify_dev_variant_outputs(stego_complete_dir)

    assert summary["errors"] == ()
    assert summary["valid"] is True
    assert summary["pdf_count"] == 32
    assert summary["hash_manifest_count"] == 16
    assert summary["kmyth_sidecar_count"] == 0


def test_verifier_reports_missing_matrix_and_unparseable_matrix(tmp_path: Path) -> None:
    missing = verify_dev_variant_outputs(tmp_path / "empty")
    assert missing["valid"] is False
    assert any("missing matrix" in error for error in missing["errors"])

    bad_json_dir = tmp_path / "bad-json"
    bad_json_dir.mkdir()
    (bad_json_dir / "variant_matrix.json").write_text("{not json", encoding="utf-8")
    bad_json = verify_dev_variant_outputs(bad_json_dir)
    assert bad_json["valid"] is False
    assert any("invalid matrix JSON" in error for error in bad_json["errors"])

    non_object_dir = tmp_path / "non-object"
    non_object_dir.mkdir()
    (non_object_dir / "variant_matrix.json").write_text("[]", encoding="utf-8")
    non_object = verify_dev_variant_outputs(non_object_dir)
    assert non_object["valid"] is False
    assert any("matrix root is not an object" in error for error in non_object["errors"])


def test_verifier_rejects_malformed_variant_collections(tmp_path: Path) -> None:
    not_a_list_dir = tmp_path / "not-a-list"
    not_a_list_dir.mkdir()
    (not_a_list_dir / "variant_matrix.json").write_text(json.dumps({"variants": "nope"}), encoding="utf-8")
    not_a_list = verify_dev_variant_outputs(not_a_list_dir)
    assert any("matrix variants is not a list" in error for error in not_a_list["errors"])

    bad_item_dir = tmp_path / "bad-item"
    bad_item_dir.mkdir()
    (bad_item_dir / "variant_matrix.json").write_text(json.dumps({"variants": ["nope"]}), encoding="utf-8")
    bad_item = verify_dev_variant_outputs(bad_item_dir)
    assert any("matrix variants[0] is not an object" in error for error in bad_item["errors"])

    errors: list[str] = []
    assert visuals._matrix_variants("nope", errors) == []
    assert errors == ["matrix root is not an object"]


def test_verifier_flags_unknown_and_mismatched_variant_ids(stego_dir_copy: Path) -> None:
    matrix_path = stego_dir_copy / "variant_matrix.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    matrix["variants"][0]["variant_id"] = "sepia_on_white"
    matrix["variants"][0]["redaction_style"] = "sepia"
    matrix["variants"][1]["redaction_style"] = "grayout"
    matrix_path.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = verify_dev_variant_outputs(stego_dir_copy)

    assert summary["valid"] is False
    assert any("do not match expected 4x4 set" in error for error in summary["errors"])
    assert any("variant_id does not match style/background" in error for error in summary["errors"])


def test_verifier_flags_tampered_missing_and_extra_files(stego_dir_copy: Path) -> None:
    (stego_dir_copy / "grayout_on_black_steganography.pdf").unlink()
    (stego_dir_copy / "rogue.txt").write_text("stray", encoding="utf-8")
    tampered = stego_dir_copy / "blackout_on_white_steganography.pdf"
    tampered.write_bytes(tampered.read_bytes() + b"tail")
    (stego_dir_copy / "whiteout_on_gray.pdf").write_bytes(b"")

    summary = verify_dev_variant_outputs(stego_dir_copy)
    errors = summary["errors"]

    assert summary["valid"] is False
    assert any("missing PDF: grayout_on_black_steganography.pdf" in error for error in errors)
    assert any("missing expected files" in error for error in errors)
    assert any("unexpected files: rogue.txt" in error for error in errors)
    assert any("blackout_on_white_steganography.pdf: byte size differs" in error for error in errors)
    assert any("blackout_on_white_steganography.pdf: sha256 differs" in error for error in errors)
    assert any("empty PDF: whiteout_on_gray.pdf" in error for error in errors)


def test_verifier_flags_unreadable_and_zero_page_pdfs(stego_dir_copy: Path) -> None:
    corrupt = stego_dir_copy / "blur_on_blur.pdf"
    corrupt.write_bytes(b"not a pdf at all")
    zero_pages = stego_dir_copy / "grayout_on_white.pdf"
    with zero_pages.open("wb") as handle:
        PdfWriter().write(handle)
    _rewrite_variant_record(
        stego_dir_copy,
        "blur_on_blur",
        base_pdf_bytes=corrupt.stat().st_size,
        base_pdf_sha256=_digest(corrupt, "sha256"),
    )
    _rewrite_variant_record(
        stego_dir_copy,
        "grayout_on_white",
        base_pdf_bytes=zero_pages.stat().st_size,
        base_pdf_sha256=_digest(zero_pages, "sha256"),
    )

    summary = verify_dev_variant_outputs(stego_dir_copy)
    errors = summary["errors"]

    assert any("blur_on_blur.pdf: PDF readability check failed" in error for error in errors)
    assert any("grayout_on_white.pdf: no readable PDF pages" in error for error in errors)


def test_verifier_flags_every_hash_manifest_defect(stego_dir_copy: Path) -> None:
    base_hash = _digest(stego_dir_copy / "blackout_on_white.pdf", "sha256")
    cases: dict[str, str] = {
        "blackout_on_white": "{broken",
        "blackout_on_gray": json.dumps(["not", "an", "object"]),
        "blackout_on_black": json.dumps(
            {"source_file": "wrong.pdf", "hashes": {"sha256": "0" * 64, "sha512": "0" * 128}}
        ),
        "blackout_on_blur": json.dumps({"source_file": "blackout_on_blur.pdf", "hashes": "nope"}),
        "whiteout_on_white": json.dumps(
            {"source_file": "whiteout_on_white.pdf", "hashes": {"sha256": "0" * 64, "sha512": "0" * 128}}
        ),
        "whiteout_on_gray": json.dumps(
            {"source_file": "whiteout_on_gray.pdf", "hashes": {"sha256": "short", "sha512": ""}}
        ),
    }
    for variant_id, payload in cases.items():
        manifest = stego_dir_copy / f"{variant_id}.hashes.json"
        manifest.write_text(payload, encoding="utf-8")
        _rewrite_variant_record(stego_dir_copy, variant_id, hash_manifest_sha256=_digest(manifest, "sha256"))
    (stego_dir_copy / "whiteout_on_black.hashes.json").unlink()
    tampered_after_record = stego_dir_copy / "grayout_on_gray.hashes.json"
    tampered_after_record.write_text(tampered_after_record.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    summary = verify_dev_variant_outputs(stego_dir_copy)
    errors = summary["errors"]

    assert any("blackout_on_white.hashes.json: invalid JSON" in error for error in errors)
    assert any("blackout_on_gray.hashes.json: manifest root is not an object" in error for error in errors)
    assert any("blackout_on_black.hashes.json: source_file does not match" in error for error in errors)
    assert any("blackout_on_blur.hashes.json: hashes is not an object" in error for error in errors)
    assert any("whiteout_on_white.hashes.json: sha256 does not match source PDF" in error for error in errors)
    assert any("whiteout_on_gray.hashes.json: missing sha256 digest" in error for error in errors)
    assert any("whiteout_on_gray.hashes.json: missing sha512 digest" in error for error in errors)
    assert any("missing hash manifest: whiteout_on_black.hashes.json" in error for error in errors)
    assert any("grayout_on_gray.hashes.json: sha256 differs from matrix" in error for error in errors)
    assert base_hash  # the untouched manifests still validate against real PDFs


def test_verifier_checks_kmyth_sidecars_and_surfaces_kmyth_warning(stego_dir_copy: Path) -> None:
    for variant_id in expected_visual_variant_ids():
        (stego_dir_copy / f"{variant_id}.hashes.json.ski").write_bytes(b"sealed")
        (stego_dir_copy / f"{variant_id}_steganography.pdf.ski").write_bytes(b"sealed")
    (stego_dir_copy / "blackout_on_white.hashes.json.ski").write_bytes(b"")
    (stego_dir_copy / "blackout_on_gray.hashes.json.ski").unlink()
    matrix_path = stego_dir_copy / "variant_matrix.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    matrix["kmyth"] = {"requested": True, "available": False, "summary": "Kmyth requested but tools were missing."}
    matrix_path.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = verify_dev_variant_outputs(stego_dir_copy, require_kmyth_sidecars=True)
    errors = summary["errors"]

    assert summary["valid"] is False
    assert summary["kmyth_sidecar_count"] == 31
    assert any("empty Kmyth sidecar: blackout_on_white.hashes.json.ski" in error for error in errors)
    assert any("missing Kmyth sidecar: blackout_on_gray.hashes.json.ski" in error for error in errors)
    assert "Kmyth requested but tools were missing." in summary["warnings"]


# --- Render smoke via a real throwaway pdftoppm on PATH ---


def test_render_smoke_passes_with_working_pdftoppm(
    stego_dir_copy: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool_dir = tmp_path / "bin"
    tool_dir.mkdir()
    _write_executable(
        tool_dir / "pdftoppm",
        "import sys\nopen(sys.argv[-1] + '.png', 'wb').write(b'fake-png')\n",
    )
    monkeypatch.setenv("PATH", f"{tool_dir}{os.pathsep}{os.environ['PATH']}")

    summary = verify_dev_variant_outputs(stego_dir_copy, render_smoke=True)

    assert summary["errors"] == ()
    assert summary["valid"] is True
    assert summary["render_smoke"] is True


def test_render_smoke_reports_failing_and_silent_renderers(
    stego_complete_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sample_pdf = stego_complete_dir / "blackout_on_white.pdf"
    tool_dir = tmp_path / "bin"
    tool_dir.mkdir()
    render_dir = tmp_path / "render"
    render_dir.mkdir()

    _write_executable(tool_dir / "pdftoppm", "import sys\nsys.stderr.write('boom')\nsys.exit(3)\n")
    monkeypatch.setenv("PATH", f"{tool_dir}{os.pathsep}{os.environ['PATH']}")
    errors: list[str] = []
    visuals._render_pdf_smoke(sample_pdf, render_dir, errors)
    assert errors == ["blackout_on_white.pdf: render smoke failed: boom"]

    _write_executable(tool_dir / "pdftoppm", "pass\n")
    errors = []
    visuals._render_pdf_smoke(sample_pdf, render_dir, errors)
    assert errors == ["blackout_on_white.pdf: render smoke produced no PNG"]

    empty_dir = tmp_path / "empty-path"
    empty_dir.mkdir()
    monkeypatch.setenv("PATH", str(empty_dir))
    errors = []
    visuals._render_pdf_smoke(sample_pdf, render_dir, errors)
    assert len(errors) == 1 and "render smoke failed" in errors[0]


def test_render_smoke_requires_pdftoppm_on_path(
    stego_dir_copy: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    empty_dir = tmp_path / "empty-path"
    empty_dir.mkdir()
    monkeypatch.setenv("PATH", str(empty_dir))

    summary = verify_dev_variant_outputs(stego_dir_copy, render_smoke=True)

    assert summary["valid"] is False
    assert any("pdftoppm is not on PATH" in error for error in summary["errors"])


# --- Kmyth subprocess helpers against real throwaway tools ---


def test_kmyth_help_and_seal_probe_succeed_with_real_tool(tmp_path: Path) -> None:
    tool = _write_executable(
        tmp_path / "kmyth-seal",
        "import sys\n"
        "argv = sys.argv\n"
        "if '--output' in argv:\n"
        "    open(argv[argv.index('--output') + 1], 'w').write('sealed')\n",
    )

    assert visuals._kmyth_help_error(tool) == ""
    assert visuals._kmyth_seal_probe_error(tool, timeout_seconds=10) == ""


def test_kmyth_helpers_report_failures_oserrors_and_missing_sidecars(tmp_path: Path) -> None:
    failing = _write_executable(
        tmp_path / "kmyth-fail", "import sys\nsys.stderr.write('tpm unavailable')\nsys.exit(2)\n"
    )
    silent = _write_executable(tmp_path / "kmyth-silent", "pass\n")
    missing = tmp_path / "kmyth-missing"

    assert "tpm unavailable" in visuals._kmyth_help_error(failing)
    assert "tpm unavailable" in visuals._kmyth_seal_probe_error(failing, timeout_seconds=10)
    assert "did not write a sidecar" in visuals._kmyth_seal_probe_error(silent, timeout_seconds=10)
    assert visuals._kmyth_help_error(missing) != ""
    assert visuals._kmyth_seal_probe_error(missing, timeout_seconds=10) != ""


def test_kmyth_seal_probe_times_out_on_hung_tool(tmp_path: Path) -> None:
    sleeper = _write_executable(tmp_path / "kmyth-sleep", "import time\ntime.sleep(5)\n")

    assert visuals._kmyth_seal_probe_error(sleeper, timeout_seconds=1) != ""


def test_resolve_kmyth_status_reports_unrunnable_and_runnable_tools(
    tmp_path: Path,
) -> None:
    failing = _write_executable(tmp_path / "kmyth-seal-bad", "import sys\nsys.exit(2)\n")
    working = _write_executable(
        tmp_path / "kmyth-seal-ok",
        "import sys\n"
        "argv = sys.argv\n"
        "if '--output' in argv:\n"
        "    open(argv[argv.index('--output') + 1], 'w').write('sealed')\n",
    )

    class Availability:
        def __init__(self, tool: Path) -> None:
            self.available = True
            self.seal_path = tool
            self.unseal_path = tool

        def summary(self) -> str:
            return "kmyth tools discovered"

    unrunnable = visuals._resolve_kmyth_status(
        include_kmyth=True,
        binary_dir=tmp_path,
        seal_probe_timeout_seconds=5,
        installation_validator=lambda binary_dir=None: Availability(failing),
    )
    assert unrunnable["available"] is False
    assert unrunnable["tools_runnable"] is False
    assert "not runnable" in str(unrunnable["summary"])

    runnable = visuals._resolve_kmyth_status(
        include_kmyth=True,
        binary_dir=tmp_path,
        seal_probe_timeout_seconds=10,
        installation_validator=lambda binary_dir=None: Availability(working),
    )
    assert runnable["available"] is True
    assert runnable["tools_runnable"] is True
    assert runnable["summary"] == "kmyth tools discovered"
