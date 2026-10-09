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
    from PIL import Image
    from infrastructure.rendering.office_native_projection import (
        office_semantics_filter_path,
        project_docx_transmission_layout,
    )
    from infrastructure.rendering._pandoc_filters import formalism_filter_path
    from infrastructure.rendering._epub_xhtml_sanitizer import sanitize_epub_xhtml
    import shutil

    create_private_native_directory(root, directory / "source")
    source_dir = directory / "source"
    source_path = source_dir / "source.md"
    bibliography = source_dir / "references.bib"
    atomic_write_bytes_confined(root, source_path, CONTROL_SOURCE.encode(), mode=0o600)
    atomic_write_bytes_confined(root, bibliography, CONTROL_BIBLIOGRAPHY.encode(), mode=0o600)
    image = Image.new("RGB", (64, 48), (255, 255, 255))
    for x in range(8, 56):
        for y in range(8, 40):
            image.putpixel((x, y), (40, 80, 160))
    image_bytes = BytesIO()
    image.save(image_bytes, format="PNG")
    atomic_write_bytes_confined(root, source_dir / "control.png", image_bytes.getvalue(), mode=0o600)
    filters = []
    for index, path in enumerate((office_semantics_filter_path(), formalism_filter_path())):
        consumed = source_dir / f"filter-{index}.lua"
        atomic_write_bytes_confined(root, consumed, path.read_bytes(), mode=0o600)
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
    inventory_tool = native_tool_record(
        root,
        source_dir,
        "pandoc",
        [str(source_path), "--from=markdown+yaml_metadata_block", "--to=json", "--standalone"],
        env=env,
        deadline=deadline,
        run_id=run_id,
        purpose="office-scientific-control-source",
    )
    filtered_tool = native_tool_record(
        root,
        source_dir,
        "pandoc",
        [
            str(source_path),
            "--from=markdown+yaml_metadata_block",
            "--to=json",
            "--standalone",
            f"--metadata=office-native-target:{kind}",
            *common,
        ],
        env=env,
        deadline=deadline,
        run_id=run_id,
        purpose="office-scientific-control-filtered",
    )
    baseline_path = source_dir / f"baseline.{kind}"
    writer = native_tool_record(
        root,
        source_dir,
        "pandoc",
        [
            str(source_path),
            "--from=markdown+yaml_metadata_block",
            f"--to={kind}",
            "--standalone",
            *common,
            "--output",
            str(baseline_path),
        ],
        env=env,
        deadline=deadline,
        run_id=run_id,
        purpose="office-scientific-control-writer",
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
    reader = SnapshotReader(root)
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
    if not reader.unchanged():
        raise ValueError("actual original scientific native control custody changed")
    return {
        "schema_version": "template-native-office-scientific-controls-v1",
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


def supervise_office_scientific_controls(
    root: Path,
    directory: Path,
    kind: str,
    *,
    interpreter: Path,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    epubcheck_jar: Path | None = None,
    java_executable: Path | None = None,
    frozen_epub_engine: Path | None = None,
) -> list[dict[str, Any]]:
    """Preserve every actual positive/negative child exit in the original budget."""
    import time
    from infrastructure.core.execution_boundary import run_bounded_subprocess
    from infrastructure.project.public_acceptance_evidence import bootstrap_command, write_json
    from infrastructure.reporting.native_format_acceptance_checks import NativeToolUnavailable

    records = []
    for ordinal, (name, required) in enumerate(CONTROL_CODES.items()):
        child = directory / f"{kind}-scientific-control-{ordinal}"
        create_private_native_directory(root, child)
        arguments = [
            "--kind",
            kind,
            "--control",
            name,
            "--root",
            str(root),
            "--directory",
            str(child),
            "--deadline",
            str(deadline),
            "--run-id",
            run_id,
        ]
        for option, value in (
            ("--epubcheck-jar", epubcheck_jar),
            ("--java-executable", java_executable),
            ("--frozen-epub-engine", frozen_epub_engine),
        ):
            if value is not None:
                arguments.extend((option, str(value)))
        command = bootstrap_command(interpreter, root, __name__, *arguments)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("scientific native controls exhausted their original deadline")
        process = run_bounded_subprocess(command, cwd=root, env=env, timeout=min(remaining, 120))
        receipt = write_json(
            root,
            directory / f"{kind}-scientific-control-{ordinal}-process.json",
            {
                "schema_version": "template-native-office-scientific-control-process-v1",
                "run_id": run_id,
                "command": list(command),
                "exit_code": process.returncode,
                "original_exit_code": process.original_returncode,
                "timed_out": process.timed_out,
                "custody_refused": process.custody_refused,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "diagnostic": process.command_error,
            },
        )
        if process.returncode == 75:
            raise NativeToolUnavailable(f"actual scientific native {kind} control {name} requires missing engine")
        expected = int(required is not None)
        if (
            process.returncode != expected
            or process.original_returncode != expected
            or process.timed_out
            or process.custody_refused
        ):
            raise ValueError("actual scientific native control lost its intended original outcome")
        observation = SnapshotReader(root).read((child / "observation.json").relative_to(root).as_posix())
        records.append(
            {
                "kind": kind,
                "name": name,
                "process_artifact": receipt,
                "artifact": {"path": observation.relative, "sha256": observation.sha256},
                "original_exit_code": expected,
            }
        )
    return records


def main() -> int:
    """Run one source-owned scientific control under the admitted supervisor."""
    import argparse
    import os
    from infrastructure.project.public_acceptance_evidence import write_json
    from infrastructure.reporting.native_format_acceptance_checks import NativeToolUnavailable

    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=("docx", "epub"), required=True)
    parser.add_argument("--control", choices=tuple(CONTROL_CODES), required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--deadline", type=float, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--epubcheck-jar", type=Path)
    parser.add_argument("--java-executable", type=Path)
    parser.add_argument("--frozen-epub-engine", type=Path)
    args = parser.parse_args()
    try:
        result = run_office_scientific_controls(
            args.root,
            args.directory,
            args.kind,
            env=dict(os.environ),
            deadline=args.deadline,
            run_id=args.run_id,
            epubcheck_jar=args.epubcheck_jar,
            java_executable=args.java_executable,
            frozen_epub_engine=args.frozen_epub_engine,
            control_name=args.control,
        )
    except NativeToolUnavailable:
        return 75
    write_json(args.root, args.directory / "observation.json", result)
    return int(result["oracle_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
