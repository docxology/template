"""Real-execution coverage for the visual proof renderer and output verifier.

Every test here uses real files (``tmp_path``), real reportlab/pypdf objects, and
real ``hashlib`` digests. The only indirection is pytest's ``monkeypatch`` fixture
(explicitly permitted by the repository no-mock policy) and real system binaries
(``/usr/bin/true``, ``/usr/bin/false``, and deliberately nonexistent paths) used to
drive the kmyth subprocess branches without any mocking framework.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path
from types import ModuleType

import pytest
from pypdf import PdfReader

import redacted_report.visuals as visuals
from redacted_report import (
    RedactionDecision,
    RedactionSegment,
    audit_release_packet,
    paragraph_audit_table,
    segment_hash_manifest,
)
from redacted_report.visuals import (
    normalize_pdf_background,
    normalize_redaction_style,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_fixture() -> tuple[list[RedactionSegment], list[RedactionDecision]]:
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


def _digest(path: Path, algorithm: str = "sha256") -> str:
    hasher = hashlib.new(algorithm)
    hasher.update(path.read_bytes())
    return hasher.hexdigest()


# --------------------------------------------------------------------------- #
# _ProofPDFRenderer: render every style x background against the real fixture. #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("style_name", ["blackout", "whiteout", "grayout", "blur"])
@pytest.mark.parametrize("background_name", ["white", "gray", "black", "blur"])
def test_write_visual_pdf_renders_readable_multipage_pdf(
    tmp_path: Path,
    style_name: str,
    background_name: str,
) -> None:
    segments, decisions = _load_fixture()
    style = normalize_redaction_style(style_name)
    background = normalize_pdf_background(background_name)
    output_pdf = tmp_path / f"{style_name}_on_{background_name}.pdf"

    visuals._write_visual_pdf(output_pdf, segments, decisions, style, background, title="Coverage Proof")

    assert output_pdf.exists()
    assert output_pdf.stat().st_size > 0
    reader = PdfReader(str(output_pdf))
    # Title page + content pages spanning every figure/table/diagram insert.
    assert len(reader.pages) >= 2


def test_write_dev_variant_matrix_drives_full_renderer_and_pdf_page_count(tmp_path: Path) -> None:
    segments, decisions = _load_fixture()

    result = visuals.write_dev_variant_pdfs(
        segments,
        decisions,
        tmp_path,
        include_steganography=False,
        include_kmyth=False,
    )

    assert "variant_matrix_path" in result
    pdfs = sorted(tmp_path.glob("*.pdf"))
    assert len(pdfs) == 16
    # Real pypdf parse of a produced PDF exercises _pdf_page_count end to end.
    assert visuals._pdf_page_count(pdfs[0]) >= 1
    assert (tmp_path / "variant_matrix.json").exists()


# --------------------------------------------------------------------------- #
# _verify_pdf_file: real files for every finding branch.                       #
# --------------------------------------------------------------------------- #


def test_verify_pdf_file_accepts_real_pdf_and_flags_each_defect(tmp_path: Path) -> None:
    segments, decisions = _load_fixture()
    good_pdf = tmp_path / "good.pdf"
    visuals._write_visual_pdf(
        good_pdf,
        segments,
        decisions,
        normalize_redaction_style("blackout"),
        normalize_pdf_background("white"),
        title="Verify",
    )
    good_sha = _digest(good_pdf)
    good_bytes = good_pdf.stat().st_size

    errors: list[str] = []
    visuals._verify_pdf_file(good_pdf, good_sha, good_bytes, errors)
    assert errors == []

    missing_errors: list[str] = []
    visuals._verify_pdf_file(tmp_path / "absent.pdf", None, None, missing_errors)
    assert any("missing PDF" in message for message in missing_errors)

    empty_pdf = tmp_path / "empty.pdf"
    empty_pdf.write_bytes(b"")
    empty_errors: list[str] = []
    visuals._verify_pdf_file(empty_pdf, None, None, empty_errors)
    assert any("empty PDF" in message for message in empty_errors)

    size_errors: list[str] = []
    visuals._verify_pdf_file(good_pdf, good_sha, good_bytes + 1, size_errors)
    assert any("byte size differs" in message for message in size_errors)

    sha_errors: list[str] = []
    visuals._verify_pdf_file(good_pdf, "0" * 64, good_bytes, sha_errors)
    assert any("sha256 differs" in message for message in sha_errors)

    unreadable = tmp_path / "unreadable.pdf"
    unreadable.write_bytes(b"this is not a valid pdf payload at all")
    unreadable_errors: list[str] = []
    visuals._verify_pdf_file(unreadable, None, None, unreadable_errors)
    assert any("PDF readability check failed" in message for message in unreadable_errors)


def test_verify_pdf_file_reports_zero_readable_pages(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pdf = tmp_path / "pages.pdf"
    pdf.write_bytes(b"%PDF-1.4 real bytes present\n")
    monkeypatch.setattr(visuals, "_pdf_page_count", lambda _path: 0)
    errors: list[str] = []

    visuals._verify_pdf_file(pdf, None, None, errors)

    assert any("no readable PDF pages" in message for message in errors)


# --------------------------------------------------------------------------- #
# _verify_hash_manifest: real JSON files + real digests for each branch.       #
# --------------------------------------------------------------------------- #


def _write_manifest(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_verify_hash_manifest_accepts_matching_manifest(tmp_path: Path) -> None:
    source_pdf = tmp_path / "source.pdf"
    source_pdf.write_bytes(b"%PDF-1.4 source proof\n")
    manifest = tmp_path / "source.hashes.json"
    _write_manifest(
        manifest,
        {
            "source_file": source_pdf.name,
            "hashes": {"sha256": _digest(source_pdf, "sha256"), "sha512": _digest(source_pdf, "sha512")},
        },
    )
    errors: list[str] = []

    visuals._verify_hash_manifest(manifest, source_pdf.name, _digest(manifest), source_pdf, errors)

    assert errors == []


def test_verify_hash_manifest_flags_each_defect(tmp_path: Path) -> None:
    source_pdf = tmp_path / "source.pdf"
    source_pdf.write_bytes(b"%PDF-1.4 source proof\n")

    missing_errors: list[str] = []
    visuals._verify_hash_manifest(tmp_path / "gone.json", source_pdf.name, None, source_pdf, missing_errors)
    assert any("missing hash manifest" in message for message in missing_errors)

    manifest = tmp_path / "source.hashes.json"
    _write_manifest(
        manifest,
        {
            "source_file": source_pdf.name,
            "hashes": {"sha256": _digest(source_pdf, "sha256"), "sha512": _digest(source_pdf, "sha512")},
        },
    )
    sha_errors: list[str] = []
    visuals._verify_hash_manifest(manifest, source_pdf.name, "0" * 64, source_pdf, sha_errors)
    assert any("sha256 differs from matrix" in message for message in sha_errors)

    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{not valid json", encoding="utf-8")
    bad_json_errors: list[str] = []
    visuals._verify_hash_manifest(bad_json, source_pdf.name, None, source_pdf, bad_json_errors)
    assert any("invalid JSON" in message for message in bad_json_errors)

    non_object = tmp_path / "list.json"
    _write_manifest(non_object, ["not", "an", "object"])
    non_object_errors: list[str] = []
    visuals._verify_hash_manifest(non_object, source_pdf.name, None, source_pdf, non_object_errors)
    assert any("manifest root is not an object" in message for message in non_object_errors)

    wrong_source = tmp_path / "wrong_source.json"
    _write_manifest(
        wrong_source,
        {
            "source_file": "someone_else.pdf",
            "hashes": {"sha256": _digest(source_pdf, "sha256"), "sha512": _digest(source_pdf, "sha512")},
        },
    )
    wrong_source_errors: list[str] = []
    visuals._verify_hash_manifest(wrong_source, source_pdf.name, None, source_pdf, wrong_source_errors)
    assert any("source_file does not match" in message for message in wrong_source_errors)

    hashes_not_object = tmp_path / "hashes_not_object.json"
    _write_manifest(hashes_not_object, {"source_file": source_pdf.name, "hashes": "nope"})
    hashes_not_object_errors: list[str] = []
    visuals._verify_hash_manifest(hashes_not_object, source_pdf.name, None, source_pdf, hashes_not_object_errors)
    assert any("hashes is not an object" in message for message in hashes_not_object_errors)

    wrong_source_digest = tmp_path / "wrong_digest.json"
    _write_manifest(
        wrong_source_digest,
        {
            "source_file": source_pdf.name,
            "hashes": {"sha256": "a" * 64, "sha512": _digest(source_pdf, "sha512")},
        },
    )
    wrong_digest_errors: list[str] = []
    visuals._verify_hash_manifest(wrong_source_digest, source_pdf.name, None, source_pdf, wrong_digest_errors)
    assert any("does not match source PDF" in message for message in wrong_digest_errors)

    short_digests = tmp_path / "short.json"
    _write_manifest(short_digests, {"source_file": source_pdf.name, "hashes": {"sha256": "abc", "sha512": "def"}})
    short_errors: list[str] = []
    visuals._verify_hash_manifest(short_digests, source_pdf.name, None, source_pdf, short_errors)
    assert any("missing sha256 digest" in message for message in short_errors)
    assert any("missing sha512 digest" in message for message in short_errors)


# --------------------------------------------------------------------------- #
# _verify_kmyth_sidecar, _matrix_variants, _expect.                            #
# --------------------------------------------------------------------------- #


def test_verify_kmyth_sidecar_branches(tmp_path: Path) -> None:
    present = tmp_path / "present.ski"
    present.write_bytes(b"sealed bytes")
    present_errors: list[str] = []
    visuals._verify_kmyth_sidecar(present, present_errors)
    assert present_errors == []

    missing_errors: list[str] = []
    visuals._verify_kmyth_sidecar(tmp_path / "absent.ski", missing_errors)
    assert any("missing Kmyth sidecar" in message for message in missing_errors)

    empty = tmp_path / "empty.ski"
    empty.write_bytes(b"")
    empty_errors: list[str] = []
    visuals._verify_kmyth_sidecar(empty, empty_errors)
    assert any("empty Kmyth sidecar" in message for message in empty_errors)


def test_matrix_variants_reports_shape_defects() -> None:
    non_dict_errors: list[str] = []
    assert visuals._matrix_variants(["not", "a", "dict"], non_dict_errors) == []
    assert any("root is not an object" in message for message in non_dict_errors)

    non_list_errors: list[str] = []
    assert visuals._matrix_variants({"variants": {"bad": "shape"}}, non_list_errors) == []
    assert any("variants is not a list" in message for message in non_list_errors)

    element_errors: list[str] = []
    result = visuals._matrix_variants({"variants": [{"variant_id": "ok"}, "not-a-dict"]}, element_errors)
    assert len(result) == 1
    assert any("variants[1] is not an object" in message for message in element_errors)


def test_expect_appends_only_on_failure() -> None:
    errors: list[str] = []
    visuals._expect(True, errors, "should not appear")
    assert errors == []
    visuals._expect(False, errors, "must appear")
    assert errors == ["must appear"]


# --------------------------------------------------------------------------- #
# verify_dev_variant_outputs: whole-matrix verifier branches.                  #
# --------------------------------------------------------------------------- #


def _build_valid_variant_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Materialize a passing 16-variant proof directory using real files/digests."""
    segments, decisions = _load_fixture()
    matrix = visuals.build_visual_variant_matrix(
        segments,
        decisions,
        include_steganography=True,
        include_kmyth=False,
    )
    variants: list[dict[str, object]] = []
    for raw_variant in matrix["variants"]:
        variant = dict(raw_variant)
        variant_id = str(variant["variant_id"])
        base_pdf = tmp_path / str(variant["base_pdf"])
        secure_pdf = tmp_path / str(variant["steganography_pdf"])
        manifest = tmp_path / str(variant["hash_manifest"])
        base_pdf.write_bytes(f"base {variant_id}\n".encode("utf-8"))
        secure_pdf.write_bytes(f"secure {variant_id}\n".encode("utf-8"))
        _write_manifest(
            manifest,
            {
                "source_file": base_pdf.name,
                "hashes": {"sha256": _digest(base_pdf, "sha256"), "sha512": _digest(base_pdf, "sha512")},
            },
        )
        variant.update(
            {
                "base_pdf_bytes": base_pdf.stat().st_size,
                "base_pdf_sha256": _digest(base_pdf),
                "steganography_pdf_bytes": secure_pdf.stat().st_size,
                "steganography_pdf_sha256": _digest(secure_pdf),
                "hash_manifest_sha256": _digest(manifest),
            }
        )
        variants.append(variant)
    matrix = {**matrix, "variants": variants}
    (tmp_path / "variant_matrix.json").write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    monkeypatch.setattr(visuals, "_pdf_page_count", lambda _path: 1)
    return tmp_path


def test_verify_dev_variant_outputs_valid_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _build_valid_variant_dir(tmp_path, monkeypatch)

    summary = visuals.verify_dev_variant_outputs(tmp_path)

    assert summary["valid"] is True
    assert summary["pdf_count"] == 32
    assert summary["hash_manifest_count"] == 16
    assert summary["errors"] == ()


def test_verify_dev_variant_outputs_missing_matrix(tmp_path: Path) -> None:
    summary = visuals.verify_dev_variant_outputs(tmp_path)

    assert summary["valid"] is False
    assert any("missing matrix" in message for message in summary["errors"])


def test_verify_dev_variant_outputs_invalid_matrix_json(tmp_path: Path) -> None:
    (tmp_path / "variant_matrix.json").write_text("{broken json", encoding="utf-8")

    summary = visuals.verify_dev_variant_outputs(tmp_path)

    assert summary["valid"] is False
    assert any("invalid matrix JSON" in message for message in summary["errors"])


def test_verify_dev_variant_outputs_matrix_root_not_object(tmp_path: Path) -> None:
    (tmp_path / "variant_matrix.json").write_text("[1, 2, 3]", encoding="utf-8")

    summary = visuals.verify_dev_variant_outputs(tmp_path)

    assert summary["valid"] is False
    assert any("matrix root is not an object" in message for message in summary["errors"])


def test_verify_dev_variant_outputs_bad_schema_and_counts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _build_valid_variant_dir(tmp_path, monkeypatch)
    matrix_path = tmp_path / "variant_matrix.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    matrix["schema"] = "wrong-schema"
    matrix["variant_count"] = 4
    matrix_path.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = visuals.verify_dev_variant_outputs(tmp_path)

    assert summary["valid"] is False
    assert any("bad matrix schema" in message for message in summary["errors"])
    assert any("variant_count is not 16" in message for message in summary["errors"])


def test_verify_dev_variant_outputs_reports_unexpected_and_missing_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _build_valid_variant_dir(tmp_path, monkeypatch)
    (tmp_path / "stray.pdf").write_bytes(b"unexpected\n")
    next(tmp_path.glob("*_steganography.pdf")).unlink()

    summary = visuals.verify_dev_variant_outputs(tmp_path)

    assert summary["valid"] is False
    assert any("unexpected files" in message for message in summary["errors"])
    assert any("missing expected files" in message for message in summary["errors"])


def test_verify_dev_variant_outputs_emits_kmyth_warning(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _build_valid_variant_dir(tmp_path, monkeypatch)
    matrix_path = tmp_path / "variant_matrix.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    matrix["kmyth"] = {"requested": True, "available": False, "summary": "Kmyth requested but unavailable in CI."}
    matrix_path.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = visuals.verify_dev_variant_outputs(tmp_path)

    assert summary["valid"] is True
    assert any("unavailable" in message for message in summary["warnings"])


def test_verify_dev_variant_outputs_requires_kmyth_sidecars(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _build_valid_variant_dir(tmp_path, monkeypatch)

    summary = visuals.verify_dev_variant_outputs(tmp_path, require_kmyth_sidecars=True)

    assert summary["valid"] is False
    assert any("missing Kmyth sidecar" in message for message in summary["errors"])
    assert any("missing expected files" in message for message in summary["errors"])


def test_verify_dev_variant_outputs_render_smoke_without_tool(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _build_valid_variant_dir(tmp_path, monkeypatch)
    monkeypatch.setattr(visuals.shutil, "which", lambda _name: None)

    summary = visuals.verify_dev_variant_outputs(tmp_path, render_smoke=True)

    assert summary["valid"] is False
    assert any("pdftoppm is not on PATH" in message for message in summary["errors"])


# --------------------------------------------------------------------------- #
# _render_pdf_smoke: real pdftoppm when present, real absent-tool branch.      #
# --------------------------------------------------------------------------- #


def test_render_pdf_smoke_against_real_pdf(tmp_path: Path) -> None:
    segments, decisions = _load_fixture()
    pdf = tmp_path / "smoke.pdf"
    visuals._write_visual_pdf(
        pdf,
        segments,
        decisions,
        normalize_redaction_style("grayout"),
        normalize_pdf_background("gray"),
        title="Smoke",
    )
    render_dir = tmp_path / "render"
    render_dir.mkdir()
    errors: list[str] = []

    visuals._render_pdf_smoke(pdf, render_dir, errors)

    if shutil.which("pdftoppm"):
        # A real renderer must turn the real PDF into a non-empty PNG.
        assert errors == []
        assert (render_dir / f"{pdf.stem}.png").stat().st_size > 0
    else:
        # No renderer on PATH: the real subprocess call raises and is recorded.
        assert any("render smoke failed" in message for message in errors)


def test_render_pdf_smoke_reports_missing_source_pdf(tmp_path: Path) -> None:
    render_dir = tmp_path / "render"
    render_dir.mkdir()
    errors: list[str] = []

    visuals._render_pdf_smoke(tmp_path / "does_not_exist.pdf", render_dir, errors)

    # Whether pdftoppm is present (nonzero exit) or absent (OSError), it fails loudly.
    assert any("render smoke failed" in message for message in errors)


# --------------------------------------------------------------------------- #
# kmyth subprocess helpers via real system binaries (no mocks).               #
# --------------------------------------------------------------------------- #


def test_kmyth_help_error_with_nonexistent_binary() -> None:
    result = visuals._kmyth_help_error(Path("/nonexistent/kmyth-seal-should-not-exist"))

    assert "kmyth-seal-should-not-exist" in result


@pytest.mark.skipif(not Path("/usr/bin/false").exists(), reason="requires /usr/bin/false")
def test_kmyth_help_error_with_failing_binary() -> None:
    result = visuals._kmyth_help_error(Path("/usr/bin/false"))

    assert result != ""
    assert "false" in result


@pytest.mark.skipif(not Path("/usr/bin/true").exists(), reason="requires /usr/bin/true")
def test_kmyth_help_error_with_succeeding_binary() -> None:
    assert visuals._kmyth_help_error(Path("/usr/bin/true")) == ""


def test_kmyth_seal_probe_error_with_nonexistent_binary() -> None:
    result = visuals._kmyth_seal_probe_error(Path("/nonexistent/kmyth-seal-should-not-exist"), timeout_seconds=5)

    assert result != ""


@pytest.mark.skipif(not Path("/usr/bin/false").exists(), reason="requires /usr/bin/false")
def test_kmyth_seal_probe_error_with_failing_binary() -> None:
    result = visuals._kmyth_seal_probe_error(Path("/usr/bin/false"), timeout_seconds=5)

    assert result != ""


@pytest.mark.skipif(not Path("/usr/bin/true").exists(), reason="requires /usr/bin/true")
def test_kmyth_seal_probe_error_when_tool_writes_no_sidecar() -> None:
    # /usr/bin/true ignores args, exits 0, and never writes the requested --output.
    result = visuals._kmyth_seal_probe_error(Path("/usr/bin/true"), timeout_seconds=5)

    assert "did not write a sidecar" in result


def test_resolve_kmyth_status_reports_tools_found_but_not_runnable(monkeypatch: pytest.MonkeyPatch) -> None:
    class Availability:
        available = True
        seal_path = Path("/usr/bin/true")
        unseal_path = Path("/usr/bin/true")

        def summary(self) -> str:
            return "kmyth present"

    infrastructure_module = ModuleType("infrastructure")
    steganography_module = ModuleType("infrastructure.steganography")
    setattr(infrastructure_module, "steganography", steganography_module)
    setattr(steganography_module, "validate_kmyth_installation", lambda binary_dir=None: Availability())
    monkeypatch.setitem(sys.modules, "infrastructure", infrastructure_module)
    monkeypatch.setitem(sys.modules, "infrastructure.steganography", steganography_module)
    monkeypatch.setattr(visuals, "_kmyth_help_error", lambda tool_path: f"{tool_path.name}: broken")

    status = visuals._resolve_kmyth_status(include_kmyth=True, binary_dir="bin", seal_probe_timeout_seconds=1)

    assert status["available"] is False
    assert status["tools_runnable"] is False
    assert "not runnable" in str(status["summary"])


# --------------------------------------------------------------------------- #
# redaction.py residual gaps: ValueError branches and duplicate segment ids.   #
# --------------------------------------------------------------------------- #


def test_paragraph_audit_table_survives_invalid_decision_bounds() -> None:
    segment = RedactionSegment("s1", "UNCLASSIFIED", "public text")
    decisions = [RedactionDecision("s1", 1, 999, "privacy")]

    rows = paragraph_audit_table([segment], decisions)

    # The ValueError branch keeps the un-redacted text length and still audits residual markers.
    assert rows[0]["redacted_length"] == len(segment.text)
    assert rows[0]["residual_markers"] == ()


def test_segment_hash_manifest_survives_invalid_decision_bounds() -> None:
    segment = RedactionSegment("s1", "UNCLASSIFIED", "public text")
    decisions = [RedactionDecision("s1", 1, 999, "privacy")]

    manifest = segment_hash_manifest([segment], decisions)

    empty_public = hashlib.sha256(b"").hexdigest()
    assert manifest[0]["public_sha256"] == empty_public
    assert len(manifest[0]["source_sha256"]) == 64


def test_audit_release_packet_flags_duplicate_segment_ids() -> None:
    segments = [
        RedactionSegment("dup", "UNCLASSIFIED", "first copy"),
        RedactionSegment("dup", "UNCLASSIFIED", "second copy"),
    ]

    audit = audit_release_packet(segments, [], release_authority="review-board")

    assert "duplicate_segment_id" in {finding.code for finding in audit.findings}
