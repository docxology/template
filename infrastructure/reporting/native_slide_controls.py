"""Actual baseline/later-page generic slide source/font/clipping/pixel controls."""

from __future__ import annotations

import time
from io import BytesIO
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.reporting.native_format_acceptance_checks import audit_pdf_raster, parse_native_bytes
from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory
from infrastructure.reporting.native_slide_source import compile_slide_source_contract, instrument_slide_source
from infrastructure.reporting.native_slide_checks import inspect_slide_source_paint
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SLIDE_CONTROL_CODES = {
    "baseline": None,
    "changed-sign-number": "slides.source.text",
    "omitted-later-occurrence": "slides.source.paint.missing",
    "tiny-later-page": "slides.typography.font",
    "clipped-later-page": "slides.layout.crop",
    "overlay-later-page": "slides.visual.invisible",
    "reordered-later-markers": "slides.source.text",
}
CONTROL_SOURCE = b"Measured offset -3.25 mV.\n\nMeasured offset -3.25 mV.\n"


def slide_source_control_fixture(name: str, ast: bytes) -> tuple[bytes, Any, tuple[dict[str, Any], ...]]:
    """Create genuinely valid native two-page PDFs; setup errors never mean fail."""
    from reportlab.pdfgen.canvas import Canvas

    if name not in SLIDE_CONTROL_CODES:
        raise ValueError("unknown source-owned generic slide control")
    contract = compile_slide_source_contract(
        "invented:slides", (("invented.md", CONTROL_SOURCE),), ast, profile="archive"
    )
    _, bindings = instrument_slide_source(ast, contract, target="beamer")
    if len(bindings) != 8:
        raise ValueError("actual source parser fixture unexpectedly changed original visible occurrences")
    stream = BytesIO()
    canvas = Canvas(stream, pagesize=(720, 405), invariant=1)
    for page in range(2):
        x = -40 if page == 1 and name == "clipped-later-page" else 40
        canvas.setFont("Helvetica", 5 if page == 1 and name == "tiny-later-page" else 18)
        for ordinal, binding in enumerate(bindings[page * 4 : (page + 1) * 4]):
            if page == 1 and name == "omitted-later-occurrence" and ordinal == 3:
                continue
            mcid = binding["mcid"]
            if page == 1 and name == "reordered-later-markers":
                mcid = bindings[page * 4 + (3 - ordinal)]["mcid"]
            canvas.addLiteral(f"/Span <</MCID {mcid}>> BDC")
            text = binding["source"]
            if page == 1 and name == "changed-sign-number" and text == "-3.25":
                text = "+3.26"
            canvas.drawString(x, 280, text)
            x += canvas.stringWidth(text, "Helvetica", 5 if page == 1 and name == "tiny-later-page" else 18) + 8
            canvas.addLiteral("EMC")
        if page == 1 and name == "overlay-later-page":
            # An opaque theme-coloured band occludes every later source glyph while
            # leaving visible page ink; a page-coloured band would make the whole
            # page uniform, which the raster reader refuses before slide oracles run.
            canvas.setFillColorRGB(0.12, 0.23, 0.45)
            canvas.rect(0, 250, 720, 70, fill=1, stroke=0)
        canvas.showPage()
    canvas.save()
    return stream.getvalue(), contract, bindings


def run_slide_source_control(
    root: Path, directory: Path, name: str, *, env: dict[str, str], deadline: float, run_id: str
) -> dict[str, Any]:
    """Real Pandoc source parse, valid PDF parser/raster, and intended diagnostics."""
    from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime

    create_private_native_directory(root, directory)
    runtime = CitationRuntime(root, directory / "parser", env=env, deadline=deadline, run_id=run_id)
    source = runtime.freeze("invented.md", CONTROL_SOURCE)
    parsed_source = runtime.tool("pandoc", [str(source), "--to=json"], "control-source-ast", input_paths=(source,))
    ast = parsed_source["stdout"].encode()
    pdf, contract, bindings = slide_source_control_fixture(name, ast)
    path = directory / "control.pdf"
    atomic_write_bytes_confined(root, path, pdf, mode=0o600)
    reader = SnapshotReader(root)
    snapshot = reader.read(path.relative_to(root).as_posix())
    parsed = parse_native_bytes("pdf", pdf)
    raster = audit_pdf_raster(root, directory, snapshot, parsed, env=env, deadline=deadline, run_id=run_id, ordinal=0)
    pixels = tuple(reader.read(row["path"]).content for row in raster["rasters"])
    observed = inspect_slide_source_paint(pdf, pixels, contract, bindings, deadline=deadline, source_images={})
    code = SLIDE_CONTROL_CODES[name]
    if (
        observed["blockers"]
        or (code is None and observed["status"] != "pass")
        or (code and (observed["status"] != "fail" or code not in {f["code"] for f in observed["findings"]}))
    ):
        raise ValueError("valid generic slide control did not preserve actual intended native diagnostic")
    if not reader.unchanged() or time.monotonic() >= deadline:
        raise ValueError("generic slide control custody changed or original deadline expired")
    return {
        "schema_version": "template-native-slide-source-valid-control-v1",
        "name": name,
        "expected_code": code,
        "input": {"path": snapshot.relative, "sha256": snapshot.sha256},
        "parser": parsed,
        "raster": raster,
        "source_tools": runtime.tools,
        "observation": observed,
        "oracle_exit_code": 0 if code is None else 1,
    }


def main() -> int:
    """Actual selected-SDK child; standalone DATA producers grant no custody."""
    import argparse
    import json
    import os
    import platform
    import sys

    import infrastructure
    from infrastructure.project.public_acceptance_evidence import write_json
    from infrastructure.project.public_reference_git import remaining
    from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
    from infrastructure.reporting.native_format_acceptance_contracts import native_deadline_guard, native_environment
    from infrastructure.reporting.native_print_child_custody import SLIDE_CHILD_SCHEMA
    from infrastructure.reporting.native_source_external_admission import admit_explicitly_bound_native_source
    from infrastructure.reporting.native_tool_producer import native_producer_operation

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--specification", required=True)
    parser.add_argument("--specification-sha256", required=True)
    parser.add_argument("--implementation-sha256", required=True)
    parser.add_argument("--deadline", type=float, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    with native_deadline_guard(args.deadline):
        remaining(args.deadline)
        root = args.root.absolute()
        reader = SnapshotReader(root)
        specification = reader.read(args.specification)
        spec = specification.json_object()
        if (
            set(spec)
            != {
                "schema_version",
                "scope",
                "name",
                "run_id",
                "directory",
                "source",
                "implementation",
                "expected_exit",
                "parent_pid",
                "parent_platform",
                "deadline_monotonic",
                "caller_deadline_monotonic",
                "closure_identity",
            }
            or specification.sha256 != args.specification_sha256
            or spec["schema_version"] != SLIDE_CHILD_SCHEMA
            or spec["deadline_monotonic"] != args.deadline
            or spec["run_id"] != args.run_id
        ):
            raise ValueError("slide child differs from actual parent prelaunch role/clock/Source bytes")
        scope, name = spec["scope"], spec["name"]
        if (
            scope not in PUBLIC_PROJECT_NAMES
            or name not in SLIDE_CONTROL_CODES
            or type(spec["expected_exit"]) is not int
            or spec["expected_exit"] != (0 if SLIDE_CONTROL_CODES[name] is None else 1)
        ):
            raise ValueError("slide child is outside the Source-owned named control roster")
        implementation = reader.read(spec["implementation"]["path"])
        if (
            implementation.sha256 != args.implementation_sha256
            or implementation.sha256 != spec["implementation"]["sha256"]
        ):
            raise ValueError("slide child selected implementation differs from its actual parent nomination")
        if infrastructure.__file__ is None:
            raise ValueError("slide child actual installed SDK origin is unavailable")
        metadata = root.stat()
        source = admit_explicitly_bound_native_source(
            root,
            environment=dict(os.environ),
            current_root_identity=(metadata.st_dev, metadata.st_ino),
            selected_sdk_package_root=Path(infrastructure.__file__).absolute().parent,
            expected_implementation_bytes=implementation.content,
            run_id=args.run_id,
            deadline=args.deadline,
            fresh_pycache_prefix=Path(sys.pycache_prefix) if sys.pycache_prefix else None,
        )
        if source is None or json.loads(source.descriptor(scope, deadline=args.deadline)) != spec["source"]:
            raise ValueError("slide child lacks fresh genuine original/current Source correspondence")
        directory = root / spec["directory"]
        if (
            specification.path != directory / "specification.json"
            or spec["parent_pid"] != os.getppid()
            or spec["parent_platform"] != platform.system()
        ):
            raise ValueError("slide child differs from actual original parent/root/platform")
        with native_producer_operation(source, run_id=args.run_id, deadline=args.deadline) as owner:
            reader = SnapshotReader(root, native_producer_operation=owner)
            result = run_slide_source_control(
                root,
                directory / "fixture",
                name,
                env=native_environment(root, Path(sys.executable), directory),
                deadline=args.deadline,
                run_id=args.run_id,
            )
            binding = write_json(root, directory / "control-observation.json", result)
            observation = reader.read(binding["path"])
            if observation.sha256 != binding["sha256"]:
                raise ValueError("slide child terminal observation changed during original custody")
            source.verify_correspondence(source.reference, root, reader, args.deadline)
            remaining(args.deadline)
            code = result["oracle_exit_code"]
            sys.stdout.write(f"SLIDE_OBSERVATION_V1 {specification.sha256} {observation.sha256} {args.run_id} {code}\n")
            sys.stdout.flush()
            remaining(args.deadline)
            return int(code)


if __name__ == "__main__":
    raise SystemExit(main())
