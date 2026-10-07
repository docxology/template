"""Original Darwin print witnesses with complete source, font and decoder custody.

These retained local observations require the enclosing auxiliary process and
same-run hosted source origin. Installed font/library/tool bytes are not copied.
"""

from __future__ import annotations

import os
import platform
import shutil
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from infrastructure.core.pipeline.fingerprints import tree_records, _observe_loaded_implementation
from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.project.native_format_library_custody import observe_native_library_custody
from infrastructure.project.public_acceptance_evidence import write_json, runtime_identity
from infrastructure.project.installed_acceptance_artifacts import write_binary
from infrastructure.reporting.native_format_acceptance_checks import (
    audit_pdf_raster,
    native_tool_record,
    parse_native_bytes,
)
from infrastructure.reporting.native_format_acceptance_contracts import native_deadline_guard, native_environment
from infrastructure.reporting.native_format_portable_custody import executable_observation
from infrastructure.reporting.native_newspaper_source import build_newspaper_reference, _fonts, _glyphs
from infrastructure.reporting.native_print_font_custody import observe_print_fonts
from infrastructure.reporting.native_storybook_source import (
    build_storybook_reference,
    inspect_storybook_artifact,
    source_package,
)
from infrastructure.reporting.native_pdf_stream_bounds import preflight_pdf_streams
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SCHEMA = "template-darwin-print-witness-v1"
KINDS = ("storybook", "newspaper")


def source_inventory(root: Path, *, original: bool = False) -> dict[str, Any]:
    """Observe the full current SDK and every admitted print source resource."""
    _observe_loaded_implementation()
    loaded_sdk = Path(__file__).resolve().parents[1]
    if loaded_sdk != (root / "infrastructure").resolve():
        if original or tree_records(loaded_sdk, source=True) != tree_records(root / "infrastructure", source=True):
            raise ValueError("print worker/reader differs from the current complete source SDK")
    roots = ["infrastructure", "pyproject.toml", "uv.lock"]
    for kind in KINDS:
        roots.extend(f"projects/templates/template_{kind}/{part}" for part in ("src", "content", "pyproject.toml"))
    records = {relative: [list(row) for row in tree_records(root / relative, source=True)] for relative in roots}
    if any(any(row[1] == "missing" for row in rows) for rows in records.values()):
        raise ValueError("original print source inventory is incomplete")
    return records


def run_print_witness(root: Path, directory: Path, budget: float) -> dict[str, str]:
    """Render both actual source exemplars privately and retain every PDF page."""
    if platform.system() != "Darwin":
        raise ValueError("original print/font witness requires Darwin")
    deadline = time.monotonic() + budget
    run_id = uuid.uuid4().hex
    directory.mkdir(parents=True, exist_ok=False)
    env = native_environment(root, Path(sys.executable), directory)
    with native_deadline_guard(deadline):
        before = source_inventory(root, original=True)
        runtime = runtime_identity()
        interpreter = executable_observation(Path(sys.executable))
        libraries = observe_native_library_custody(("pdf",), repo_root=root)
        fonts = {kind: observe_print_fonts(root / f"projects/templates/template_{kind}", kind) for kind in KINDS}
        versions = {}
        for name in ("pdftoppm", "pdffonts"):
            result = native_tool_record(
                root, directory, name, ["-v"], env=env, deadline=deadline, run_id=run_id, purpose=f"version-{name}"
            )
            if result["exit_code"] != 0 or result["original_exit_code"] != 0:
                raise ValueError("original print raster tool version failed")
            versions[name] = result["artifact"]
        rows: list[dict[str, Any]] = []
        for ordinal, kind in enumerate(KINDS):
            project = root / f"projects/templates/template_{kind}"
            work = directory / kind
            work.mkdir()
            provider = source_package(project, kind)
            source: dict[str, Any]
            if kind == "storybook":
                reference = build_storybook_reference(project, work / "source", deadline=deadline)
                producer = work / "producer"
                shutil.copytree(project / "content", producer / "content")
                produced = provider.build_storybook_pdf(producer)
                candidate = read_bytes_confined(work, produced.output_path, max_bytes=64 * 1024 * 1024)
                preflight_pdf_streams(candidate, deadline=deadline, max_bytes=250 * 1024 * 1024)
                semantic = inspect_storybook_artifact(candidate, reference, kind="pdf")
                source = {
                    "source_sha256": reference.source_sha256,
                    "dimensions": list(reference.dimensions),
                    "filenames": list(reference.filenames),
                    "pages": [
                        write_binary(root, work / f"source-page-{index:04d}.png", data)
                        for index, data in enumerate(reference.pages)
                    ],
                    "contact_sheet": write_binary(root, work / "source-contact.png", reference.contact_sheet),
                }
            else:
                newspaper = build_newspaper_reference(project, work / "source", deadline=deadline)
                path = work / "producer.pdf"
                provider.render_edition(
                    provider.load_edition(project / "content"),
                    provider.load_newspaper_config(project / "content"),
                    project_root=work / "source",
                    output_path=path,
                )
                candidate = read_bytes_confined(work, path, max_bytes=64 * 1024 * 1024)
                for content in (candidate, newspaper.pdf):
                    preflight_pdf_streams(content, deadline=deadline)
                if _fonts(candidate) != _fonts(newspaper.pdf) or _glyphs(candidate, newspaper) != _glyphs(
                    newspaper.pdf, newspaper
                ):
                    raise ValueError("newspaper source font/glyph projection differs")
                import hashlib

                semantic = {
                    "schema_version": "template-newspaper-print-projection-v1",
                    "source_sha256": newspaper.source_sha256,
                    "artifact_sha256": hashlib.sha256(candidate).hexdigest(),
                    "pages": len(newspaper.obligations),
                }
                source = {
                    "source_sha256": newspaper.source_sha256,
                    "dimensions": list(newspaper.dimensions),
                    "obligations": [list(page) for page in newspaper.obligations],
                    "pdf": write_binary(root, work / "source.pdf", newspaper.pdf),
                }
            binding = write_binary(root, work / "candidate.pdf", candidate)
            snapshot = SnapshotReader(root).read(binding["path"])
            observation = parse_native_bytes("pdf", candidate)
            raster = audit_pdf_raster(
                root, work, snapshot, observation, env=env, deadline=deadline, run_id=run_id, ordinal=ordinal
            )
            if kind == "newspaper":
                source_snapshot = SnapshotReader(root).read(source["pdf"]["path"])
                source_observation = parse_native_bytes("pdf", source_snapshot.content)
                source["raster"] = audit_pdf_raster(
                    root,
                    work,
                    source_snapshot,
                    source_observation,
                    env=env,
                    deadline=deadline,
                    run_id=run_id,
                    ordinal=ordinal + len(KINDS),
                )
            # Every page's original bounded 150-dpi process is retained.
            rows.append(
                {
                    "kind": kind,
                    "artifact": binding,
                    "observation": observation,
                    "source": source,
                    "semantic": semantic,
                    "raster": raster,
                }
            )
        after_fonts = {kind: observe_print_fonts(root / f"projects/templates/template_{kind}", kind) for kind in KINDS}
        after_libraries = observe_native_library_custody(("pdf",), repo_root=root)
        after = source_inventory(root, original=True)
        after_interpreter = executable_observation(Path(sys.executable))
        if before != after or fonts != after_fonts or interpreter != after_interpreter:
            raise ValueError("original print source/font/interpreter changed during execution")
        raster_artifacts: list[dict[str, str]] = []
        for row in rows:
            groups = [row["raster"]] + ([row["source"]["raster"]] if row["kind"] == "newspaper" else [])
            for group in groups:
                raster_artifacts.extend({"path": page["path"], "sha256": page["sha256"]} for page in group["rasters"])
        raw = {
            "schema_version": SCHEMA,
            "run_id": run_id,
            "producer_root": str(root.resolve()),
            "pid": os.getpid(),
            "platform": "Darwin",
            "runtime": runtime,
            "interpreter_before": interpreter,
            "interpreter_after": after_interpreter,
            "source_before": before,
            "source_after": after,
            "fonts_before": fonts,
            "fonts_after": after_fonts,
            "library_before": libraries,
            "library_after": after_libraries,
            "versions": versions,
            "prints": rows,
            "raster_artifacts": raster_artifacts,
        }
        binding = write_json(root, directory / "print-witness.json", raw)
    from infrastructure.reporting.native_print_witness_validation import validate_print_witness

    validate_print_witness(
        binding,
        SnapshotReader(root),
        expected_pid=os.getpid(),
        expected_runtime={"executable": sys.executable, "python_version": platform.python_version()},
        deadline=deadline,
    )
    return binding
