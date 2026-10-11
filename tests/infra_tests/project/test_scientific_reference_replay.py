"""Genuine frozen producer deletion and independent source replay controls.

The fixture compiles a real source-only XeTeX reference, deletes its copied
compiler and producer directory, and relocates the retained bytes to another
base. Ordinary infra CI constructs no NativeSourceContext, NativeOriginalLaunch
or live producer owner, so the replay/reproduction entry points must refuse
before consuming any custody-gated native byte; reachable DATA predicates are
exercised against the genuine retained records. Positive replay remains an
installed native acceptance obligation.
"""

from __future__ import annotations

import copy
from dataclasses import asdict
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
from infrastructure.reporting.native_format_scientific_math import (
    observe_scientific_math_reference,
    reference_math_glyphs,
    scientific_math_from_ast,
)
from infrastructure.reporting.native_projection_contracts import ProjectionSourceUnsupported
from infrastructure.reporting.native_scientific_reference_replay import (
    replay_scientific_math_reference,
    strict_json_object,
)
from infrastructure.reporting.native_scientific_reference_reproduction import (
    reproduce_scientific_reference,
    validate_original_raster_process,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

ROOT = Path(__file__).resolve().parents[3]
CUSTODY = "externally admitted source and original launch custody"
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
    # Finite closure incl. the distribution's preloaded format: xelatex.fmt is
    # ~5.4 MB in TeX Live 2026 and ~9.1 MB in Ubuntu's TeX Live 2023.
    assert sum(original_files.values()) < 32 * 1024**2
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


def _producer_path(path):
    return str(ROOT) if path == "." else str(ROOT / path)


def _recording_reader(root, reads):
    """Plain relocated-base reader that records which retained bindings were consumed."""

    def read(binding):
        reads.append(binding["path"])
        return (root / binding["path"]).read_bytes()

    return read


def _custody_gated_paths(raw):
    """Retained native bytes the replay may consume only after original launch custody."""
    paths = {raw[name]["path"] for name in ("source", "pdf", "discovery_fls", "final_fls")}
    paths |= {binding["path"] for role in ("backend_inputs", "compiler_logs") for binding in raw[role].values()}
    paths |= {row["artifact"]["path"] for row in (*raw["tool_artifacts"], *raw["dependencies_before"])}
    return paths


def component(fixture, raw=None, *, reader=None, reads=None):
    root = fixture["root"]
    return replay_scientific_math_reference(
        raw or fixture["raw"],
        fixture["ast"],
        fixture["inputs"],
        read_artifact=_recording_reader(root, [] if reads is None else reads),
        producer_path=_producer_path,
        run_id=fixture["run_id"],
        deadline=time.monotonic() + 30,
        native_reader=SnapshotReader(root) if reader is None else reader,
    )


def reproduce(fixture, directory, raw, raster, reader, reads):
    root = fixture["root"]
    return reproduce_scientific_reference(
        root,
        directory,
        raw,
        fixture["ast"],
        fixture["inputs"],
        raster,
        read_artifact=_recording_reader(root, reads),
        producer_path=_producer_path,
        original_run_id=fixture["run_id"],
        env=native_environment(root, Path(sys.executable), directory),
        original_reader=reader,
        deadline=time.monotonic() + 180,
    )


def _data_only_readers(fixture):
    # Neither a plain reader nor serialized original observation DATA is custody.
    root = fixture["root"]
    return (SnapshotReader(root), SnapshotReader(root, native_operation=copy.deepcopy(fixture["raw"])))


def test_deleted_original_compiler_and_producer_replay_requires_launch_custody(original_reference):
    raw, root = original_reference["raw"], original_reference["root"]
    directory = original_reference["original_directory"]
    assert not directory.exists()
    # Paranoid Kpathsea policy is retained exactly as replay requires it.
    assert raw["environment"] == {
        **{name: str(directory / name.lower()) for name in ("TEXMFHOME", "TEXMFCONFIG", "TEXMFVAR")},
        "TEXMFOUTPUT": str(directory),
        "openin_any": "p",
        "openout_any": "p",
    }
    # Exact process order the replay authenticates once custody is admitted.
    assert [json.loads((root / row["artifact"]["path"]).read_bytes())["purpose"] for row in raw["tool_artifacts"]] == [
        "reference-xelatex-version",
        "reference-xdvipdfmx-version",
        "reference-kpsewhich-version",
        "reference-texmfdist",
        "reference-texmfroot",
        "reference-texmf-trees",
        "reference-discovery-compiler",
        "reference-discovery-backend",
        "reference-final-compiler",
        "reference-final-backend",
    ]
    nodes = scientific_math_from_ast(original_reference["ast"])
    assert raw["nodes"] == [asdict(node) for node in nodes]
    pdf = (root / raw["pdf"]["path"]).read_bytes()
    assert hashlib.sha256(pdf).hexdigest() == raw["pdf"]["sha256"]
    # Retained bytes alone reconstruct both glyph rows at the different base.
    assert len(reference_math_glyphs(pdf, nodes)) == 2
    for reader in _data_only_readers(original_reference):
        reads: list[str] = []
        with pytest.raises(ProjectionSourceUnsupported, match=CUSTODY):
            component(original_reference, reader=reader, reads=reads)
        # Source/AST/implementation/template predicates ran on genuine bytes;
        # no TeX source, compiler, font, XDV or PDF byte was consumed.
        assert raw["template_tool_artifact"]["path"] in reads
        assert not set(reads) & _custody_gated_paths(raw)


def test_fresh_reader_source_compilation_requires_original_launch_custody(original_reference):
    directory = original_reference["root"] / "output/readiness/fresh-reader-reference"
    for reader in _data_only_readers(original_reference):
        reads: list[str] = []
        with pytest.raises(ProjectionSourceUnsupported, match=CUSTODY):
            reproduce(
                original_reference, directory, original_reference["raw"], original_reference["raster"], reader, reads
            )
        assert reads == [] and not directory.exists()


PRE_CUSTODY_TAMPER = {
    "source-ast": "original AST bytes differ",
    "implementation": "current loaded implementation bytes",
    "template-command": "command/outcome/custody differs",
    "template-outcome": "command/outcome/custody differs",
}
CUSTODY_GATED_TAMPER = ("tex-source", "font", "compiler-command", "compiler-outcome")


@pytest.mark.parametrize("kind", [*PRE_CUSTODY_TAMPER, *CUSTODY_GATED_TAMPER])
def test_rehashed_original_artifact_tamper_refused(original_reference, kind):
    raw = copy.deepcopy(original_reference["raw"])
    if kind == "source-ast":
        binding = raw["source_ast"]
    elif kind == "tex-source":
        binding = raw["source"]
    elif kind.startswith("template-"):
        binding = raw["template_tool_artifact"]
    elif kind.startswith("compiler-"):
        binding = next(
            row["artifact"]
            for row in raw["tool_artifacts"]
            if json.loads((original_reference["root"] / row["artifact"]["path"]).read_bytes())["purpose"]
            == "reference-final-compiler"
        )
    elif kind == "font":
        binding = next(
            row["artifact"] for row in raw["dependencies_before"] if Path(row["resolved_path"]).suffix == ".otf"
        )
    else:
        binding = raw["implementation"][0]["artifact"]
    path = original_reference["root"] / binding["path"]
    original = path.read_bytes()
    if kind.endswith(("-command", "-outcome")):
        process = json.loads(original)
        if kind.endswith("-command"):
            process["command"].append("--source-unowned")
        else:
            process["original_exit_code"] = 1
        changed = json.dumps(process).encode()
    else:
        changed = original + b"changed"
    reads: list[str] = []
    try:
        path.write_bytes(changed)
        binding["sha256"] = hashlib.sha256(changed).hexdigest()
        if kind in PRE_CUSTODY_TAMPER:
            with pytest.raises(ValueError, match=PRE_CUSTODY_TAMPER[kind]) as refused:
                component(original_reference, raw, reads=reads)
            assert not isinstance(refused.value, ProjectionSourceUnsupported)
            assert binding["path"] in reads
        else:
            # Without original launch custody the rehashed bytes are never consumed.
            with pytest.raises(ProjectionSourceUnsupported, match=CUSTODY):
                component(original_reference, raw, reads=reads)
            assert binding["path"] not in reads
    finally:
        path.write_bytes(original)


@pytest.mark.parametrize("kind", ["xdv", "vector", "pixels"])
def test_rehashed_native_substitution_never_consumed_without_original_custody(original_reference, kind):
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
    assert changed != original
    try:
        path.write_bytes(changed)
        binding["sha256"] = hashlib.sha256(changed).hexdigest()
        directory = original_reference["root"] / "output/readiness" / ("fresh-reader-negative-" + kind)
        reads: list[str] = []
        with pytest.raises(ProjectionSourceUnsupported, match=CUSTODY):
            reproduce(original_reference, directory, raw, raster, SnapshotReader(original_reference["root"]), reads)
        assert reads == [] and not directory.exists()
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
    binding = original_reference["raster"]["tool_artifact"]
    process = strict_json_object((root / binding["path"]).read_bytes())

    def validate(value):
        validate_original_raster_process(
            value,
            original_reference["raw"],
            producer_path=_producer_path,
            original_run_id=original_reference["run_id"],
        )

    # The genuine relocated pdftoppm record satisfies the exact DATA predicate.
    validate(process)
    process["diagnostic"] = diagnostic
    with pytest.raises(ValueError, match="command/outcome/custody differs"):
        validate(process)
