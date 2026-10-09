"""Genuine frozen producer deletion and independent source replay controls."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time
import uuid

import pytest

from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
from infrastructure.reporting.native_format_acceptance_contracts import native_environment
from infrastructure.reporting.native_format_pdf_source import PDFSourceInputs
from infrastructure.reporting.native_format_scientific_math import observe_scientific_math_reference
from infrastructure.reporting.native_scientific_reference_replay import replay_scientific_math_reference
from infrastructure.reporting.native_scientific_reference_reproduction import reproduce_scientific_reference

ROOT = Path(__file__).resolve().parents[3]
pytestmark = pytest.mark.timeout(300)


@pytest.fixture(scope="module")
def original_reference(tmp_path_factory: pytest.TempPathFactory):
    if shutil.disk_usage(ROOT).free < 2 * 1024**3 + 150 * 1024**2:
        pytest.fail("genuine scientific reference control requires reserved 2 GiB headroom")
    base = ROOT / "output/readiness" / ("scientific-replay-" + uuid.uuid4().hex)
    directory = base / "original"
    directory.mkdir(parents=True)
    tools = base / "tools"
    tools.mkdir()
    for name in ("xelatex", "xdvipdfmx", "kpsewhich"):
        executable = shutil.which(name)
        if executable is None:
            pytest.fail(f"actual prepared {name} prerequisite missing")
        shutil.copy2(Path(executable).resolve(), tools / name)
    source = b"Complex $\\sum_{i=1}^{n}\\frac{x_i^2}{1+\\exp(-\\lambda x_i)}$ expression.\n\n$$\\int_0^1 x^2\\,dx=\\frac{1}{3}$$\n"
    markdown = directory / "input.md"
    markdown.write_bytes(source)
    inputs = PDFSourceInputs(
        source, (("fixture.md", source),), ("fixture.yaml", b"metadata:\n  fontsize: 10pt\n"), None, (), (), ()
    )
    environment = native_environment(ROOT, Path(sys.executable), directory)
    run_id = base.name
    for variable in ("TEXMFROOT", "TEXMFDIST", "TEXMFCNF"):
        tool = native_tool_record(
            ROOT,
            directory,
            str(Path(shutil.which("kpsewhich")).resolve()),
            [f"--var-value={variable}"],
            env=environment,
            deadline=time.monotonic() + 30,
            run_id=run_id,
            purpose=f"original-installed-{variable.lower()}",
        )
        process = json.loads((ROOT / tool["artifact"]["path"]).read_bytes())
        assert process["original_exit_code"] == process["exit_code"] == 0
        value = process["stdout"].strip()
        assert value, f"actual installed TeX configuration missing {variable}"
        if variable != "TEXMFCNF":
            assert Path(value).is_absolute() and Path(value).resolve(strict=True).is_dir()
        environment[variable] = value
    environment["PATH"] = str(tools) + ":" + environment["PATH"]
    ast_tool = native_tool_record(
        ROOT,
        directory,
        "pandoc",
        [str(markdown), "--from=markdown+tex_math_dollars", "--to=json"],
        env=environment,
        deadline=time.monotonic() + 120,
        run_id=run_id,
        purpose="original-source-ast",
    )
    ast_process = json.loads((ROOT / ast_tool["artifact"]["path"]).read_bytes())
    assert ast_process["original_exit_code"] == ast_process["exit_code"] == 0
    ast = ast_process["stdout"].encode()
    raw = observe_scientific_math_reference(
        ROOT, directory, ast, inputs, env=environment, deadline=time.monotonic() + 180, run_id=run_id
    )
    raster_tool = native_tool_record(
        ROOT,
        directory,
        "pdftoppm",
        ["-png", "-r", "150", str(ROOT / raw["pdf"]["path"]), str(directory / "page")],
        env=environment,
        deadline=time.monotonic() + 120,
        run_id=run_id,
        purpose="scientific-reference-raster",
    )
    raster = {
        "tool_artifact": raster_tool["artifact"],
        "rasters": [
            {"path": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in sorted(directory.glob("page-*.png"))
        ],
    }
    (directory / "original-observation.json").write_text(json.dumps(raw, indent=2))
    (directory / "original-raster.json").write_text(json.dumps(raster, indent=2))
    reader_root = tmp_path_factory.mktemp("different-base-reader")
    copied = reader_root / directory.relative_to(ROOT)
    shutil.copytree(directory, copied)
    original_files = {str(path): path.stat().st_size for path in copied.rglob("*") if path.is_file()}
    assert sum(original_files.values()) < 10 * 1024**2
    compiler_paths = [Path(row["path"]) for row in raw["runtime_before"].values()]
    shutil.rmtree(base)
    assert not directory.exists() and all(not path.exists() for path in compiler_paths)
    assert reader_root != ROOT
    yield {
        "root": reader_root,
        "raw": raw,
        "ast": ast,
        "inputs": inputs,
        "raster": raster,
        "run_id": run_id,
        "environment": environment,
        "original_directory": directory,
        "files": original_files,
    }


def component(fixture, raw=None):
    root = fixture["root"]
    return replay_scientific_math_reference(
        raw or fixture["raw"],
        fixture["ast"],
        fixture["inputs"],
        read_artifact=lambda binding: (root / binding["path"]).read_bytes(),
        producer_path=lambda path: str(ROOT) if path == "." else str(ROOT / path),
        run_id=fixture["run_id"],
        deadline=time.monotonic() + 30,
    )


def test_deleted_original_compiler_and_producer_replay_at_different_base(original_reference):
    observed = component(original_reference)
    assert len(observed["reference_glyphs"]) == 2
    assert observed["blockers"]
    assert not original_reference["original_directory"].exists()


def test_fresh_reader_source_compilation_reconstructs_glyph_vectors_and_ink(original_reference):
    root = original_reference["root"]
    directory = root / "output/readiness/fresh-reader-reference"
    environment = native_environment(root, Path(sys.executable), directory)
    result = reproduce_scientific_reference(
        root,
        directory,
        original_reference["raw"],
        original_reference["ast"],
        original_reference["inputs"],
        original_reference["raster"],
        read_artifact=lambda binding: (root / binding["path"]).read_bytes(),
        producer_path=lambda path: str(ROOT) if path == "." else str(ROOT / path),
        original_run_id=original_reference["run_id"],
        env=environment,
        timeout=180,
    )
    assert result["status"] == "blocked"
    assert len(result["original_observation"]["reference_glyphs"]) == 2
    assert result["reader_reference"]["runtime_before"] == result["reader_reference"]["runtime_after"]


@pytest.mark.parametrize("kind", ["source", "command", "font", "outcome", "implementation"])
def test_rehashed_original_artifact_tamper_refused(original_reference, kind):
    raw = copy.deepcopy(original_reference["raw"])
    if kind == "source":
        binding = raw["source"]
    elif kind in {"command", "outcome"}:
        binding = raw["tool_artifacts"][7]["artifact"]
    elif kind == "font":
        binding = next(
            row["artifact"] for row in raw["dependencies_before"] if Path(row["resolved_path"]).suffix == ".otf"
        )
    elif kind == "implementation":
        binding = raw["implementation"][0]["artifact"]
    else:
        binding = raw["backend_inputs"]["final"]
    path = original_reference["root"] / binding["path"]
    original = path.read_bytes()
    if kind in {"command", "outcome"}:
        process = json.loads(original)
        if kind == "command":
            process["command"].append("--source-unowned")
        else:
            process["original_exit_code"] = 1
        changed = json.dumps(process).encode()
    elif kind == "xdv":
        changed = b""
    else:
        changed = original + b"changed"
    try:
        path.write_bytes(changed)
        binding["sha256"] = hashlib.sha256(changed).hexdigest()
        with pytest.raises(ValueError):
            component(original_reference, raw)
    finally:
        path.write_bytes(original)


@pytest.mark.parametrize("kind", ["xdv", "vector", "pixels"])
def test_rehashed_native_substitution_refused_by_actual_source_recompilation(original_reference, kind):
    from io import BytesIO

    raw = copy.deepcopy(original_reference["raw"])
    raster = copy.deepcopy(original_reference["raster"])
    binding = (
        raw["backend_inputs"]["final"] if kind == "xdv" else raw["pdf"] if kind == "vector" else raster["rasters"][0]
    )
    path = original_reference["root"] / binding["path"]
    original = path.read_bytes()
    if kind == "xdv":
        changed = original[:-1] + bytes([original[-1] ^ 1])
    elif kind == "vector":
        from pypdf import PdfReader, PdfWriter
        from reportlab.pdfgen.canvas import Canvas

        reader = PdfReader(BytesIO(original))
        overlay = BytesIO()
        page = reader.pages[0]
        canvas = Canvas(overlay, pagesize=(float(page.mediabox.width), float(page.mediabox.height)))
        canvas.setFillColorRGB(1, 1, 1)
        canvas.rect(0, 0, float(page.mediabox.width), float(page.mediabox.height), fill=1, stroke=0)
        canvas.save()
        page.merge_page(PdfReader(BytesIO(overlay.getvalue())).pages[0])
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        output = BytesIO()
        writer.write(output)
        changed = output.getvalue()
    else:
        from PIL import Image

        with Image.open(BytesIO(original)) as image:
            output = BytesIO()
            Image.new("RGB", image.size, "white").save(output, format="PNG")
            changed = output.getvalue()
    try:
        path.write_bytes(changed)
        binding["sha256"] = hashlib.sha256(changed).hexdigest()
        root = original_reference["root"]
        directory = root / "output/readiness" / ("fresh-reader-negative-" + kind)
        environment = native_environment(root, Path(sys.executable), directory)
        with pytest.raises(ValueError):
            reproduce_scientific_reference(
                root,
                directory,
                raw,
                original_reference["ast"],
                original_reference["inputs"],
                raster,
                read_artifact=lambda b: (root / b["path"]).read_bytes(),
                producer_path=lambda p: str(ROOT) if p == "." else str(ROOT / p),
                original_run_id=original_reference["run_id"],
                env=environment,
                timeout=180,
            )
    finally:
        path.write_bytes(original)


@pytest.mark.parametrize("tag", ["Cite", "RawInline", "RawBlock", "Table"])
def test_unsupported_original_source_nodes_remain_visible_blockers(tag):
    from infrastructure.reporting.native_scientific_reference_replay import unsupported_source_blockers

    ast = json.dumps({"blocks": [{"t": tag, "c": []}]}).encode()
    assert unsupported_source_blockers(ast) == [
        f"blocks/0: source {tag} requires independent full-source/citation/table replay"
    ]


def test_only_valid_nonrendering_xdv_clock_comment_is_projected():
    from infrastructure.reporting.native_scientific_reference_reproduction import canonical_xdv

    original = bytes([247, 7]) + bytes(12) + bytes([29]) + b" XeTeX output 2026.10.06:1751" + b"original instructions"
    changed_clock = original[:15] + b" XeTeX output 2026.10.07:0800" + original[44:]
    assert canonical_xdv(original) == canonical_xdv(changed_clock)
    with pytest.raises(ValueError):
        canonical_xdv(original[:15] + b" XeTeX output 2026.99.06:1751" + original[44:])
    assert canonical_xdv(original) != canonical_xdv(original[:-1] + b"changed")


def _actual_png(width, height):
    import struct
    import zlib

    def chunk(name, data):
        return struct.pack(">I", len(data)) + name + data + struct.pack(">I", zlib.crc32(name + data))

    compressor = zlib.compressobj()
    rows = []
    # Real one-bit grayscale scanlines; very small compressed bytes, no giant
    # image/array allocation. The IHDR still describes actual oversized pixels.
    scanline = bytes((width + 7) // 8 + 1)
    for _ in range(height):
        rows.append(compressor.compress(scanline))
    rows.append(compressor.flush())
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 1, 0, 0, 0, 0))
        + chunk(b"IDAT", b"".join(rows))
        + chunk(b"IEND", b"")
    )


def _actual_binding(root, path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(65536):
            digest.update(chunk)
    return {"path": path.relative_to(root).as_posix(), "sha256": digest.hexdigest()}


def _bounded_actual_authentication(root):
    from infrastructure.core.files.secure_write import read_bytes_confined

    return lambda binding: read_bytes_confined(root, root / binding["path"], max_bytes=1024 * 1024)


def test_real_compressed_oversized_png_refused_before_decode(tmp_path):
    from infrastructure.reporting.native_scientific_reference_reproduction import admit_original_rasters

    image = _actual_png(10000, 6001)
    assert len(image) < 16000
    path = tmp_path / "output/readiness/page-1.png"
    path.parent.mkdir(parents=True)
    path.write_bytes(image)
    with pytest.raises(ValueError, match="pixel dimensions"):
        admit_original_rasters(
            tmp_path,
            [_actual_binding(tmp_path, path)],
            read_artifact=_bounded_actual_authentication(tmp_path),
            deadline=time.monotonic() + 30,
        )


def test_real_sparse_encoded_file_cap_refused_without_allocation(tmp_path):
    from infrastructure.reporting.native_scientific_reference_reproduction import admit_original_rasters

    path = tmp_path / "output/readiness/page-1.png"
    path.parent.mkdir(parents=True)
    path.write_bytes(_actual_png(8, 8))
    with path.open("r+b") as stream:
        stream.truncate(64 * 1024 * 1024 + 1)
    with pytest.raises(ValueError, match="regular-file size"):
        admit_original_rasters(
            tmp_path,
            [_actual_binding(tmp_path, path)],
            read_artifact=_bounded_actual_authentication(tmp_path),
            deadline=time.monotonic() + 30,
        )


def test_real_sparse_aggregate_raster_cap_refused_before_authentication(tmp_path):
    from infrastructure.reporting.native_scientific_reference_reproduction import admit_original_rasters

    directory = tmp_path / "output/readiness"
    directory.mkdir(parents=True)
    bindings = []
    for index in range(1, 6):
        path = directory / f"page-{index}.png"
        path.write_bytes(_actual_png(8, 8))
        if index < 5:
            with path.open("r+b") as stream:
                stream.truncate(64 * 1024 * 1024)
        bindings.append(_actual_binding(tmp_path, path))
    with pytest.raises(ValueError, match="encoded closure exceeds 256 MiB"):
        admit_original_rasters(
            tmp_path, bindings, read_artifact=_bounded_actual_authentication(tmp_path), deadline=time.monotonic() + 30
        )


@pytest.mark.parametrize("kind", ["duplicate", "unordered", "count", "fieldset", "callback"])
def test_original_raster_exact_admission_and_authentication(tmp_path, kind):
    from infrastructure.reporting.native_scientific_reference_reproduction import admit_original_rasters

    directory = tmp_path / "output/readiness"
    directory.mkdir(parents=True)
    bindings = []
    for index in (1, 2):
        path = directory / f"page-{index}.png"
        path.write_bytes(_actual_png(8, 8))
        bindings.append(_actual_binding(tmp_path, path))
    authentication = _bounded_actual_authentication(tmp_path)
    accepted = admit_original_rasters(tmp_path, bindings, read_artifact=authentication, deadline=time.monotonic() + 30)
    assert [row["dimensions"] for row in accepted] == [(8, 8), (8, 8)]
    if kind == "duplicate":
        bindings.append(bindings[0])
        bindings.sort(key=lambda row: row["path"])
    elif kind == "unordered":
        bindings.reverse()
    elif kind == "count":
        bindings *= 251
    elif kind == "fieldset":
        bindings[0]["extra"] = "unadmitted"
    else:
        wrong = directory / "different.png"
        wrong.write_bytes(_actual_png(16, 8))

        # A real alternate filesystem reader fails original binding authentication.
        def different_reader(binding):
            return wrong.read_bytes()

        authentication = different_reader
    with pytest.raises(ValueError):
        admit_original_rasters(tmp_path, bindings, read_artifact=authentication, deadline=time.monotonic() + 30)


def test_original_tool_json_duplicate_fields_refused():
    from infrastructure.reporting.native_scientific_reference_replay import strict_json_object

    with pytest.raises(ValueError, match="repeats a field"):
        strict_json_object(b'{"exit_code": 1, "exit_code": 0}')


@pytest.mark.parametrize("diagnostic", [False, 0, None, []])
def test_original_raster_diagnostic_requires_exact_empty_string(original_reference, diagnostic):
    root = original_reference["root"]
    raster = copy.deepcopy(original_reference["raster"])
    binding = raster["tool_artifact"]
    path = root / binding["path"]
    original = path.read_bytes()
    process = json.loads(original)
    process["diagnostic"] = diagnostic
    changed = json.dumps(process).encode()
    try:
        path.write_bytes(changed)
        binding["sha256"] = hashlib.sha256(changed).hexdigest()
        directory = root / "output/readiness" / ("diagnostic-negative-" + uuid.uuid4().hex)
        with pytest.raises(ValueError, match="command/outcome/custody differs"):
            reproduce_scientific_reference(
                root,
                directory,
                original_reference["raw"],
                original_reference["ast"],
                original_reference["inputs"],
                raster,
                read_artifact=lambda b: (root / b["path"]).read_bytes(),
                producer_path=lambda p: str(ROOT) if p == "." else str(ROOT / p),
                original_run_id=original_reference["run_id"],
                env=native_environment(root, Path(sys.executable), directory),
                timeout=30,
            )
        assert not directory.exists()
    finally:
        path.write_bytes(original)
