"""Genuine bounded scientific native Office controls, including preserved-content ink mutants."""

from __future__ import annotations

import hashlib
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.reporting.native_format_acceptance_checks import native_tool_record, parse_native_bytes
from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory
from infrastructure.reporting.native_office_content_witness import inspect_office_source_survival
from infrastructure.reporting.native_office_reference import read_office_package_ast
from infrastructure.reporting.native_office_reference_visual import (
    inspect_office_reference_projection,
    observe_reference_conversion,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SCHEMA = "template-native-office-scientific-controls-v2"

CONTROL_CODES = {
    "baseline": None,
    "changed-equation": "office.source.math",
    "changed-citation": "office.source.citation_rendering",
    "changed-table": "office.source.table_cells",
    "changed-figure": "office.source.image_content",
    "wrong-alternative": "office.source.image_alternative",
    "lost-pagebreak": "office.source.page_breaks",
    "lost-label": "office.source.label",
    "tiny-math": "office.reference.pixels",
    "invisible-math": "office.reference.pixels",
}

CONTROL_SOURCE = """# Scientific control

Before $\\alpha + 1$ after. Measured [@invented].

\\begin{equation}
\\label{eq:control}
\\frac{3.25}{7}
\\end{equation}

| Quantity | Measured |
|---|---|
| Offset | 19.75 mV |

<!-- alt: Measured alternative description. -->
![Visible source figure caption.](control.png)

```{=latex}
\\newpage
```

## Final paragraph

The source remains visible after the declared page break.
"""
CONTROL_BIBLIOGRAPHY = (
    "@article{invented, author={Doe, Jane}, title={Invented measurement}, year={2020}, journal={Invented Journal}}\n"
)


def mutate_office_scientific_package(original: bytes, kind: str, name: str) -> bytes:
    """Mutate valid actual writer output; never construct a fake native receipt."""
    if name not in CONTROL_CODES or kind not in {"docx", "epub"}:
        raise ValueError("unknown actual Office scientific control")
    if name == "baseline":
        return original
    output = BytesIO()
    changes = 0
    with zipfile.ZipFile(BytesIO(original)) as source, zipfile.ZipFile(output, "w") as destination:
        for member in source.infolist():
            data = source.read(member)
            changed = data
            if member.filename.endswith((".xml", ".xhtml")):
                if name == "changed-equation":
                    changed = data.replace(b"3.25", b"4.25")
                elif name == "changed-citation":
                    changed = data.replace(b"2020", b"2099")
                elif name == "changed-table":
                    changed = data.replace(b"19.75", b"29.75")
                elif name == "wrong-alternative":
                    changed = data.replace(b"Measured alternative description.", b"Incorrect alternative description.")
                elif name == "lost-label":
                    digest = hashlib.sha1(b"eq:control", usedforsecurity=False).hexdigest()
                    marker = ("_" + digest[1:]).encode() if kind == "docx" else b"eq:control"
                    changed = data.replace(marker, b"changed-source-label")
                elif name == "lost-pagebreak":
                    import re

                    changed = (
                        re.sub(rb'<w:br\s+w:type="page"\s*/>', b"", data)
                        if kind == "docx"
                        else data.replace(b"template-office-pagebreak", b"ordinary-div").replace(
                            b"break-after: page; page-break-after: always;", b""
                        )
                    )
                elif (
                    name in {"tiny-math", "invisible-math"}
                    and kind == "docx"
                    and member.filename == "word/document.xml"
                ):
                    # The actual OMML expression and reader AST survive. Only
                    # native mathematical typography/ink changes.
                    from defusedxml.ElementTree import fromstring
                    import re

                    fromstring(data)
                    names = (b"sz", b"szCs") if name == "tiny-math" else (b"color",)
                    value = b"8" if name == "tiny-math" else b"FFFFFF"

                    def alter_run(match):
                        opening, body, closing = match.groups()
                        properties = re.search(rb"<w:rPr>(.*?)</w:rPr>", body, re.DOTALL)
                        content = properties.group(1) if properties else b""
                        for key in names:
                            content = re.sub(rb"<w:" + key + rb"\b[^>]*/>", b"", content)
                            content += b"<w:" + key + b' w:val="' + value + b'"/>'
                        replacement = b"<w:rPr>" + content + b"</w:rPr>"
                        if properties:
                            body = body[: properties.start()] + replacement + body[properties.end() :]
                        else:
                            # Preserve original namespace declarations and
                            # prefixes; native readers require their QName
                            # compatibility attributes to remain meaningful.
                            position = body.find(b"</m:rPr>")
                            position = 0 if position < 0 else position + len(b"</m:rPr>")
                            body = body[:position] + replacement + body[position:]
                        return opening + body + closing

                    changed = re.sub(rb"(<m:r(?:\s[^>]*)?>)(.*?)(</m:r>)", alter_run, data, flags=re.DOTALL)
                    fromstring(changed)
            if name in {"tiny-math", "invisible-math"} and kind == "epub" and member.filename.endswith(".css"):
                rule = b"font-size: 4px !important;" if name == "tiny-math" else b"color: white !important;"
                changed = data + b"\nspan.math, math {" + rule + b"}\n"
            if name == "changed-figure" and member.filename.endswith(".png"):
                from PIL import Image

                with Image.open(BytesIO(data)) as image:
                    image.load()
                    rgb = image.convert("RGB")
                    rgb.putpixel((rgb.width // 2, rgb.height // 2), (250, 20, 20))
                    buffer = BytesIO()
                    rgb.save(buffer, format="PNG")
                    changed = buffer.getvalue()
            changes += changed != data
            destination.writestr(member, changed)
    if not changes:
        raise ValueError(f"actual native Office mutant {name} changed no package member")
    return output.getvalue()


def run_office_scientific_controls(
    root: Path,
    directory: Path,
    kind: str,
    *,
    reader: SnapshotReader,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    epubcheck_jar: Path | None = None,
    java_executable: Path | None = None,
    frozen_epub_engine: Path | None = None,
    control_name: str | None = None,
) -> dict[str, Any]:
    """Execute genuine writer, package reader, validator, native reader and raster controls.

    The caller schedules this inside its original finite supervised phase.
    A semantic mutant must trigger its exact source finding; preserved-content
    ink mutants must additionally retain semantic survival and change pixels.
    """
    from infrastructure.reporting.native_tool_producer import current_native_producer_operation

    owner = current_native_producer_operation()
    if (
        kind not in {"docx", "epub"}
        or owner is None
        or reader.native_producer_operation is not owner
        or owner.run_id != run_id
        or owner.deadline != deadline
    ):
        raise ValueError("Office scientific controls require their actual genuine Source/ToolAPI owner/run/clock")
    owner.verify(reader, run_id=run_id, deadline=deadline)
    from PIL import Image
    from infrastructure.rendering.office_native_projection import (
        office_semantics_filter_path,
        project_docx_transmission_layout,
    )
    from infrastructure.rendering._pandoc_filters import formalism_filter_path
    from infrastructure.rendering._epub_xhtml_sanitizer import sanitize_epub_xhtml
    import shutil

    from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime

    runtime = CitationRuntime(root, directory / "source", env=env, deadline=deadline, run_id=run_id)
    source_dir = runtime.directory
    source_path = runtime.freeze("source.md", CONTROL_SOURCE.encode())
    bibliography = runtime.freeze("references.bib", CONTROL_BIBLIOGRAPHY.encode())

    def source_tool(arguments: list[str], purpose: str) -> dict[str, Any]:
        original = runtime.tool("pandoc", arguments, purpose, input_paths=tuple(runtime.inputs))
        owner.validate_tool(runtime.tools[-1], original, reader, run_id=run_id)
        return {
            "artifact": runtime.tools[-1],
            "exit_code": original["exit_code"],
            "original_exit_code": original["original_exit_code"],
        }

    image = Image.new("RGB", (64, 48), (255, 255, 255))
    for x in range(8, 56):
        for y in range(8, 40):
            image.putpixel((x, y), (40, 80, 160))
    image_bytes = BytesIO()
    image.save(image_bytes, format="PNG")
    runtime.freeze("control.png", image_bytes.getvalue())
    filters = []
    for index, path in enumerate((office_semantics_filter_path(), formalism_filter_path())):
        consumed = runtime.freeze(f"filter-{index}.lua", path.read_bytes())
        filters.extend(["--lua-filter", str(consumed)])
    crossref = shutil.which("pandoc-crossref", path=env.get("PATH"))
    if not crossref:
        raise ValueError("scientific native controls require the configured actual crossref provider")
    crossref_path = Path(crossref).resolve(strict=True)
    crossref_size = crossref_path.stat().st_size
    if crossref_size > 512 * 1024 * 1024:
        raise ValueError("scientific native crossref exceeds finite runtime budget")
    with crossref_path.open("rb") as handle:
        crossref_digest = hashlib.file_digest(handle, "sha256").hexdigest()
    crossref_runtime = {"path": str(crossref_path), "sha256": crossref_digest, "bytes": crossref_size}
    crossref = str(crossref_path)
    common = [
        *filters,
        "--filter",
        crossref,
        "--citeproc",
        f"--bibliography={bibliography}",
        f"--resource-path={source_dir}",
        "--metadata=title:Scientific control",
        "--lua-filter",
        str(source_dir / "filter-0.lua"),
    ]
    if kind == "epub":
        from infrastructure.rendering.epub_renderer import _EPUB_IDENTIFIER_PLACEHOLDER

        common.append(f"--metadata=identifier:{_EPUB_IDENTIFIER_PLACEHOLDER}")
    inventory_tool = source_tool(
        [str(source_path), "--from=markdown+yaml_metadata_block", "--to=json", "--standalone"],
        "office-scientific-control-source",
    )
    filtered_tool = source_tool(
        [
            str(source_path),
            "--from=markdown+yaml_metadata_block",
            "--to=json",
            "--standalone",
            f"--metadata=office-native-target:{kind}",
            *common,
        ],
        "office-scientific-control-filtered",
    )
    baseline_path = source_dir / f"baseline.{kind}"
    writer = source_tool(
        [
            str(source_path),
            "--from=markdown+yaml_metadata_block",
            f"--to={kind}",
            "--standalone",
            *common,
            "--output",
            str(baseline_path),
        ],
        "office-scientific-control-writer",
    )
    if any(row["original_exit_code"] != 0 or row["exit_code"] != 0 for row in (inventory_tool, filtered_tool, writer)):
        raise ValueError("actual scientific native source parser/writer failed")
    with crossref_path.open("rb") as handle:
        after_crossref_digest = hashlib.file_digest(handle, "sha256").hexdigest()
    if crossref_path.stat().st_size != crossref_size or after_crossref_digest != crossref_digest:
        raise ValueError("actual scientific native crossref changed during source parsing/writing")
    if kind == "docx":
        project_docx_transmission_layout(baseline_path)
    else:
        sanitize_epub_xhtml(baseline_path)
    source_ast = reader.read(inventory_tool["artifact"]["path"]).json_object()["stdout"].encode()
    filtered_ast = reader.read(filtered_tool["artifact"]["path"]).json_object()["stdout"].encode()
    baseline = reader.read(baseline_path.relative_to(root).as_posix())
    rows = []
    baseline_native = None
    if control_name is not None and control_name not in CONTROL_CODES:
        raise ValueError("unknown supervised scientific native control")
    names = (
        tuple(CONTROL_CODES)
        if control_name is None
        else ("baseline",)
        if control_name == "baseline"
        else ("baseline", control_name)
    )
    for name in names:
        required = CONTROL_CODES[name]
        leaf = directory / name
        create_private_native_directory(root, leaf)
        package = leaf / f"control.{kind}"
        atomic_write_bytes_confined(
            root, package, mutate_office_scientific_package(baseline.content, kind, name), mode=0o600
        )
        if kind == "epub":
            from infrastructure.rendering.epub_renderer import _normalize_epub_archive

            _normalize_epub_archive(package, source_date_epoch=int(env.get("SOURCE_DATE_EPOCH", "946684800")))
        snapshot = reader.read(package.relative_to(root).as_posix())
        parse_native_bytes(kind, snapshot.content)
        binding = {"path": snapshot.relative, "sha256": snapshot.sha256}
        readback_leaf, native_leaf = leaf / "readback", leaf / "native"
        create_private_native_directory(root, readback_leaf)
        create_private_native_directory(root, native_leaf)
        readback = read_office_package_ast(
            root, readback_leaf, binding, kind, env=env, deadline=deadline, run_id=run_id
        )
        survival = inspect_office_source_survival(
            source_ast,
            filtered_ast,
            reader.read(readback["ast"]["path"]).content,
            snapshot.content,
            kind,
            (image_bytes.getvalue(),),
            {"title": "Scientific control"},
        )
        native = observe_reference_conversion(
            root,
            native_leaf,
            binding,
            kind,
            env=env,
            deadline=deadline,
            run_id=run_id,
            epubcheck_jar=epubcheck_jar,
            java_executable=java_executable,
            frozen_engine=frozen_epub_engine,
        )
        observed = (
            reader.read(native["conversion"]["pdf"]["path"]).content,
            tuple(reader.read(row["path"]).content for row in native["raster"]["rasters"]),
        )
        if name == "baseline":
            baseline_native = observed
        if baseline_native is None:
            raise ValueError("scientific native controls omitted original positive baseline")
        projection = inspect_office_reference_projection(*baseline_native, *observed, deadline=deadline)
        codes = {row["code"] for result in (survival, projection) for row in result["findings"]}
        if survival["blockers"] or (required is None and codes) or (required is not None and required not in codes):
            raise ValueError(
                f"actual scientific native control {name} did not produce intended independent finding: "
                f"{sorted(codes)}; {survival['blockers']}"
            )
        if name in {"tiny-math", "invisible-math"} and survival["status"] != "observed":
            raise ValueError("native ink control changed source mathematical/package semantics")
        rows.append(
            {
                "name": name,
                "package": binding,
                "readback": readback,
                "native": native,
                "source_survival": survival,
                "projection": projection,
                "required_finding": required,
            }
        )
    runtime.unchanged()
    owner.verify(reader, run_id=run_id, deadline=deadline)
    if not reader.unchanged():
        raise ValueError("actual original scientific native control custody changed")
    return {
        "schema_version": SCHEMA,
        "run_id": run_id,
        "kind": kind,
        "source": {
            "path": source_path.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(CONTROL_SOURCE.encode()).hexdigest(),
        },
        "source_package": {"path": baseline.relative, "sha256": baseline.sha256},
        "source_tools": [inventory_tool, filtered_tool, writer],
        "crossref_runtime": crossref_runtime,
        "source_date_epoch": int(env.get("SOURCE_DATE_EPOCH", "946684800")) if kind == "epub" else None,
        "control": control_name,
        "controls": rows,
        "oracle_exit_code": int(control_name not in {None, "baseline"}),
    }


def office_scientific_epub_arguments(kind: str, arguments: tuple[str, ...]) -> tuple[str, ...]:
    """Preserve original nominated labels; reader never reopens those engines."""
    allowed = {"--epubcheck-jar", "--java-executable", "--frozen-epub-engine"}
    options = arguments[::2]
    if (
        kind not in {"docx", "epub"}
        or len(arguments) % 2
        or len(set(options)) != len(options)
        or any(option not in allowed for option in options)
        or any(not isinstance(value, str) or not Path(value).is_absolute() for value in arguments[1::2])
        or (kind == "docx" and arguments)
    ):
        raise ValueError("Office scientific original EPUB engine arguments differ")
    if kind == "epub" and not {"--epubcheck-jar", "--java-executable"} <= set(options):
        raise ValueError("Office scientific EPUB requires its actual admitted validator/Java nominations")
    return arguments


def supervise_office_scientific_controls(
    root: Path,
    directory: Path,
    kind: str,
    *,
    scope: str,
    interpreter: Path,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    epubcheck_jar: Path | None = None,
    java_executable: Path | None = None,
    frozen_epub_engine: Path | None = None,
) -> list[dict[str, Any]]:
    """Every scientific name gets an actual source-admitted child and OS oracle."""
    import json
    import os
    import platform
    import time
    from infrastructure.project.public_reference_git import remaining
    from infrastructure.project.public_acceptance_evidence import write_json
    from infrastructure.reporting.native_print_child_custody import (
        OFFICE_SCIENTIFIC_CHILD_SCHEMA,
        OFFICE_SCIENTIFIC_WORKER,
        OfficeScientificControlReaderOperation,
    )
    from infrastructure.reporting.native_source_provider_bootstrap import format_selected_sdk_native_bootstrap
    from infrastructure.reporting.native_tool_producer import current_native_producer_operation

    owner = current_native_producer_operation()
    if owner is None or owner.run_id != run_id or owner.deadline != deadline:
        raise ValueError("Office scientific supervisor needs its actual genuine enclosing Source/ToolAPI owner")
    source = owner.source
    parent_reader = SnapshotReader(root, native_producer_operation=owner)
    owner.verify(parent_reader, run_id=run_id, deadline=deadline)
    arguments: list[str] = []
    for option, value in (
        ("--epubcheck-jar", epubcheck_jar),
        ("--java-executable", java_executable),
        ("--frozen-epub-engine", frozen_epub_engine),
    ):
        if value is not None:
            arguments.extend((option, str(value)))
    epub_arguments = office_scientific_epub_arguments(kind, tuple(arguments))
    records = []
    for ordinal, (name, required) in enumerate(CONTROL_CODES.items()):
        remaining(deadline)
        child_deadline = min(deadline, time.monotonic() + 120.0)
        leaf = directory / f"{kind}-scientific-control-{ordinal:04d}"
        create_private_native_directory(root, leaf)
        create_private_native_directory(root, leaf / "closure")
        source.verify_correspondence(source.reference, root, parent_reader, child_deadline)
        implementation_path = leaf / "implementation.json"
        atomic_write_bytes_confined(
            root, implementation_path, source.bindings.expected_implementation_bytes, mode=0o600
        )
        implementation = parent_reader.read(implementation_path.relative_to(root).as_posix())
        closure = (leaf / "closure").stat()
        expected = int(required is not None)
        specification = {
            "schema_version": OFFICE_SCIENTIFIC_CHILD_SCHEMA,
            "scope": scope,
            "name": name,
            "run_id": run_id,
            "directory": leaf.relative_to(root).as_posix(),
            "source": json.loads(source.descriptor(scope, deadline=child_deadline)),
            "implementation": {"path": implementation.relative, "sha256": implementation.sha256},
            "expected_exit": expected,
            "parent_pid": os.getpid(),
            "parent_platform": platform.system(),
            "deadline_monotonic": child_deadline,
            "caller_deadline_monotonic": deadline,
            "closure_identity": [closure.st_dev, closure.st_ino],
            "kind": kind,
            "epub_arguments": list(epub_arguments),
        }
        spec = write_json(root, leaf / "specification.json", specification)
        hook = source.current_source_reader.read("infrastructure/core/bytecode_audit.py").content
        if (
            json.loads(source.bindings.expected_implementation_bytes)["files"]["infrastructure/core/bytecode_audit.py"]
            != hashlib.sha256(hook).hexdigest()
        ):
            raise ValueError("Office scientific child raw hook differs from its genuine selected SDK")
        bootstrap = format_selected_sdk_native_bootstrap(
            hook,
            source.bindings.selected_sdk_package_root,
            (),
            implementation_path,
            implementation.sha256,
            leaf / "closure",
            (closure.st_dev, closure.st_ino),
            child_deadline,
            required_worker_module=OFFICE_SCIENTIFIC_WORKER,
        )
        command = [
            str(interpreter),
            "-I",
            "-c",
            bootstrap,
            "--root",
            str(root),
            "--specification",
            spec["path"],
            "--specification-sha256",
            spec["sha256"],
            "--implementation-sha256",
            implementation.sha256,
            "--deadline",
            repr(child_deadline),
            "--run-id",
            run_id,
        ]
        process = native_tool_record(
            root,
            leaf,
            str(interpreter),
            command[1:],
            env=env,
            deadline=child_deadline,
            run_id=run_id,
            purpose="office-scientific-child",
            preserve_nominated_launcher=True,
        )
        if process["exit_code"] != expected or process["original_exit_code"] != expected:
            raise ValueError("actual Office scientific child lost its required original OS outcome")
        observed = parent_reader.read((leaf / "control-observation.json").relative_to(root).as_posix())
        closure_receipt = parent_reader.read((leaf / "closure/receipt.json").relative_to(root).as_posix())
        item = {
            "name": name,
            "artifact": {"path": observed.relative, "sha256": observed.sha256},
            "process_artifact": process["artifact"],
            "specification_artifact": spec,
            "closure_artifact": {"path": closure_receipt.relative, "sha256": closure_receipt.sha256},
            "original_exit_code": expected,
        }
        context = OfficeScientificControlReaderOperation(
            source, parent_reader, [item], scope=scope, run_id=run_id, deadline=deadline
        )
        context.child(item, parent_reader)
        records.append(item)
        owner.verify(parent_reader, run_id=run_id, deadline=deadline)
    return records


def main() -> int:
    """Re-admit exact genuine Source, installed SDK and clock in each actual child."""
    import argparse
    import json
    import os
    import platform
    import sys
    import infrastructure
    from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
    from infrastructure.project.public_acceptance_evidence import write_json
    from infrastructure.reporting.native_format_acceptance_contracts import native_deadline_guard, native_environment
    from infrastructure.reporting.native_print_child_custody import OFFICE_SCIENTIFIC_CHILD_SCHEMA
    from infrastructure.reporting.native_source_external_admission import admit_explicitly_bound_native_source
    from infrastructure.reporting.native_tool_producer import native_producer_operation

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--specification", required=True)
    parser.add_argument("--specification-sha256", required=True)
    parser.add_argument("--implementation-sha256", required=True)
    parser.add_argument("--deadline", type=float, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    with native_deadline_guard(args.deadline):
        root = args.root.absolute()
        reader = SnapshotReader(root)
        specification = reader.read(args.specification)
        spec = specification.json_object()
        keys = {
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
            "kind",
            "epub_arguments",
        }
        if (
            set(spec) != keys
            or specification.sha256 != args.specification_sha256
            or spec["schema_version"] != OFFICE_SCIENTIFIC_CHILD_SCHEMA
            or spec["deadline_monotonic"] != args.deadline
            or spec["run_id"] != args.run_id
            or spec["scope"] not in PUBLIC_PROJECT_NAMES
            or spec["name"] not in CONTROL_CODES
            or type(spec["expected_exit"]) is not int
            or spec["expected_exit"] != int(CONTROL_CODES[spec["name"]] is not None)
            or not isinstance(spec["epub_arguments"], list)
        ):
            raise ValueError("Office scientific child differs from actual source-owned role/roster/specification")
        epub_arguments = office_scientific_epub_arguments(spec["kind"], tuple(spec["epub_arguments"]))
        implementation = reader.read(spec["implementation"]["path"])
        if (
            implementation.sha256 != args.implementation_sha256
            or implementation.sha256 != spec["implementation"]["sha256"]
            or infrastructure.__file__ is None
        ):
            raise ValueError("Office scientific actual child SDK nomination differs")
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
        if source is None or json.loads(source.descriptor(spec["scope"], deadline=args.deadline)) != spec["source"]:
            raise ValueError("Office scientific actual child lacks fresh genuine Source correspondence")
        leaf = root / spec["directory"]
        if (
            specification.path != leaf / "specification.json"
            or spec["parent_pid"] != os.getppid()
            or spec["parent_platform"] != platform.system()
        ):
            raise ValueError("Office scientific child differs from actual parent/root/platform")
        selected = dict(zip(epub_arguments[::2], epub_arguments[1::2], strict=True))
        with native_producer_operation(source, run_id=args.run_id, deadline=args.deadline) as owner:
            reader = SnapshotReader(root, native_producer_operation=owner)
            create_private_native_directory(root, leaf / "fixture")
            result = run_office_scientific_controls(
                root,
                leaf / "fixture",
                spec["kind"],
                reader=reader,
                env=native_environment(root, Path(sys.executable), leaf),
                deadline=args.deadline,
                run_id=args.run_id,
                epubcheck_jar=Path(selected["--epubcheck-jar"]) if "--epubcheck-jar" in selected else None,
                java_executable=Path(selected["--java-executable"]) if "--java-executable" in selected else None,
                frozen_epub_engine=Path(selected["--frozen-epub-engine"])
                if "--frozen-epub-engine" in selected
                else None,
                control_name=spec["name"],
            )
            result.update({"scope": spec["scope"], "worker_pid": os.getpid(), "worker_platform": platform.system()})
            if result["oracle_exit_code"] != spec["expected_exit"]:
                raise ValueError("Office scientific actual native oracle differs from source-owned expected exit")
            write_json(root, leaf / "control-observation.json", result)
            source.verify_correspondence(source.reference, root, reader, args.deadline)
            observed = reader.read((leaf / "control-observation.json").relative_to(root).as_posix())
            sys.stdout.write(
                f"OFFICE_SCIENTIFIC_OBSERVATION_V1 {specification.sha256} {observed.sha256} "
                f"{args.run_id} {result['oracle_exit_code']}\n"
            )
            sys.stdout.flush()
            return int(result["oracle_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
