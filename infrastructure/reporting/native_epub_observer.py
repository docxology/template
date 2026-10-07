"""Real EPUBCheck and native reader conversion with exact byte custody."""

from __future__ import annotations

import hashlib
import shutil
import time
from pathlib import Path
from infrastructure.reporting.native_epub_replay import replay_epub_conversion as replay_epub_conversion
from typing import Any
from infrastructure.reporting.native_format_content_contracts import NativeContentContract

from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
from infrastructure.reporting.native_format_acceptance_checks import (
    NativeToolUnavailable,
    native_tool_record,
    parse_native_bytes,
)
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader
from infrastructure.project.native_reader_runtime_custody import (
    observe_native_reader_runtime,
    retain_native_reader_runtime,
    validate_native_reader_runtime,
    require_native_reader_plugin_trace,
)


def inspect_epub(
    root: Path,
    directory: Path,
    artifact: ArtifactSnapshot,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    epubcheck_jar: Path | None = None,
    java_executable: Path | None = None,
    frozen_engine: Path | None = None,
) -> dict[str, Any]:
    """Run actual validator and Calibre reader on a fresh exact EPUB copy.

    Successful conversion alone does not establish complete spine/layout parity.
    Missing tools propagate NativeToolUnavailable; no parser substitutes for them.
    """
    if epubcheck_jar is None or java_executable is None:
        raise NativeToolUnavailable("EPUBCheck requires reviewed exact JAR and actual Java runtime executable")
    selected = shutil.which("ebook-convert", path=env.get("PATH"))
    if selected is None:
        raise NativeToolUnavailable("actual native Calibre reader is unavailable")
    consumed_plugin = "Contents/Frameworks/plugins/headless.so"
    try:
        runtime_before = observe_native_reader_runtime(
            Path(selected), deadline=deadline, consumed_members=(consumed_plugin,)
        )
    except ValueError as error:
        if "dedicated app/resource prefix" in str(error):
            raise NativeToolUnavailable(str(error)) from error
        raise
    before_binding = retain_native_reader_runtime(root, runtime_before, run_id=run_id)
    engine = bind_epubcheck_engine(epubcheck_jar, java_executable, deadline=deadline)
    tool_env = dict(env)
    for key in ("CLASSPATH", "JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS", "_JAVA_OPTIONS"):
        tool_env.pop(key, None)
    tool_env["CALIBRE_CONFIG_DIRECTORY"] = str(directory / "calibre-profile")
    tool_env["CALIBRE_CACHE_DIRECTORY"] = str(directory / "calibre-cache")
    tool_env.pop("QTWEBENGINE_DISABLE_SANDBOX", None)
    # Official Qt diagnostic: use software rendering without changing process
    # isolation or renderer/network sandbox policy.
    tool_env["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu"
    tool_env["QT_DEBUG_PLUGINS"] = "1"
    tool_env["QT_LOGGING_RULES"] = "qt.core.plugin.factoryloader.debug=false;qt.core.plugin.loader.debug=false"
    from infrastructure.project.public_acceptance_evidence import write_json

    environment = write_json(
        root,
        directory / "epub-reader-environment.json",
        {
            "schema_version": "template-native-epub-reader-environment-v2",
            "run_id": run_id,
            "CALIBRE_CONFIG_DIRECTORY": tool_env["CALIBRE_CONFIG_DIRECTORY"],
            "CALIBRE_CACHE_DIRECTORY": tool_env["CALIBRE_CACHE_DIRECTORY"],
            "QTWEBENGINE_CHROMIUM_FLAGS": "--disable-gpu",
            "QT_DEBUG_PLUGINS": "1",
            "QT_LOGGING_RULES": tool_env["QT_LOGGING_RULES"],
        },
    )
    private_jar = (
        freeze_epubcheck_bundle(root, directory, engine, deadline=deadline)
        if frozen_engine is None
        else frozen_engine / Path(engine["jar"]).name
    )
    if frozen_engine is not None:
        SnapshotReader(root).public_path(private_jar.relative_to(root).as_posix())
        expected_files = {row["path"] for row in engine["files"] if row["category"] == "epubcheck-bundle"}
        actual_files = {path.relative_to(frozen_engine).as_posix() for path in frozen_engine.rglob("*.jar")}
        if expected_files != actual_files:
            raise ValueError("shared private EPUBCheck file set differs from admitted engine")
    parse_native_bytes("epub", artifact.content)
    source, target = directory / "input.epub", directory / "reader.pdf"
    if source.exists() or target.exists():
        raise ValueError("native EPUB inspection requires fresh input/output")
    atomic_write_bytes_confined(root, source, artifact.content, mode=0o600)
    reader = SnapshotReader(root)
    consumed = reader.read(source.relative_to(root).as_posix())
    if consumed.sha256 != artifact.sha256:
        raise ValueError("EPUB reader input differs from admitted bytes")
    consumed_jars = []
    for row in engine["files"]:
        if row["category"] == "epubcheck-bundle":
            copied = reader.read((private_jar.parent / row["path"]).relative_to(root).as_posix())
            if copied.sha256 != row["sha256"]:
                raise ValueError("actual private EPUBCheck JAR differs from admitted engine bytes")
            consumed_jars.append({"path": copied.relative, "sha256": copied.sha256})
    tools = []
    for name, args, purpose in (
        (str(java_executable), ["-version"], "java-runtime-version"),
        (str(java_executable), ["-jar", str(private_jar), "--version"], "epubcheck-version"),
        (str(java_executable), ["-jar", str(private_jar), str(source)], "epubcheck-validation"),
        ("ebook-convert", ["--version"], "epub-reader-version"),
        ("ebook-convert", [str(source), str(target), "--disable-font-rescaling"], "epub-reader-conversion"),
    ):
        record = native_tool_record(
            root, directory, name, args, env=tool_env, deadline=deadline, run_id=run_id, purpose=purpose
        )
        tools.append(record["artifact"])
        if record["exit_code"] != 0 or record["original_exit_code"] != 0:
            raise ValueError(f"actual {purpose} failed")
    runtime_after = observe_native_reader_runtime(
        Path(selected), deadline=deadline, consumed_members=(consumed_plugin,)
    )
    native_reader = reader.read(tools[-1]["path"]).json_object()
    validate_native_reader_runtime(
        runtime_before,
        runtime_after,
        executable_sha256=native_reader["executable_sha256"],
        consumed_members=(consumed_plugin,),
    )
    require_native_reader_plugin_trace(runtime_after, native_reader["stderr"], consumed_plugin)
    after_binding = retain_native_reader_runtime(root, runtime_after, run_id=run_id)
    converted = reader.read(target.relative_to(root).as_posix())
    observation = parse_native_bytes("pdf", converted.content)
    if engine != bind_epubcheck_engine(epubcheck_jar, java_executable, deadline=deadline):
        raise ValueError("EPUBCheck engine/runtime changed during actual validation")
    if not reader.unchanged():
        raise ValueError("EPUB input/reader output changed during inspection")
    private_binding = reader.read(private_jar.relative_to(root).as_posix())
    return {
        "schema_version": "template-native-epub-reader-v2",
        "input": {"path": consumed.relative, "sha256": consumed.sha256},
        "pdf": {"path": converted.relative, "sha256": converted.sha256},
        "observation": observation,
        "engine": engine,
        "consumed_jar": {"path": private_binding.relative, "sha256": private_binding.sha256},
        "consumed_jars": consumed_jars,
        "tool_artifacts": tools,
        "reader_environment_artifact": environment,
        "reader_runtime_before": before_binding,
        "reader_runtime_after": after_binding,
        "status": "blocked",
        "blockers": ["complete spine/source/layout and valid reader visual controls required"],
    }


def bind_epubcheck_engine(jar: Path, java: Path, *, deadline: float) -> dict[str, Any]:
    """Bind actual Java runtime and all EPUBCheck bundle JARs, never a wrapper.

    File sets are reconstructed again after validation. Escaping symlinks,
    unbounded runtime trees, and system launcher stubs are refused explicitly.
    """
    actual_java = java.resolve(strict=True)
    if actual_java.parent.name != "bin" or actual_java.name != "java":
        raise ValueError("EPUBCheck requires actual runtime bin/java, not a launcher wrapper")
    runtime = actual_java.parent.parent
    if not (runtime / "release").is_file():
        raise NativeToolUnavailable("actual Java runtime release identity is unavailable")
    actual_jar = jar.resolve(strict=True)
    bundle = actual_jar.parent
    import zipfile
    from urllib.parse import urlsplit, unquote

    with zipfile.ZipFile(actual_jar) as archive:
        manifest = archive.read("META-INF/MANIFEST.MF").decode("utf-8")
    unfolded = manifest.replace("\r\n ", "").replace("\n ", "")
    for line in unfolded.splitlines():
        if line.startswith("Class-Path:"):
            for entry in line.partition(":")[2].split():
                parsed = urlsplit(entry)
                if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
                    raise ValueError("EPUBCheck manifest class path is outside reviewed bundle")
                dependency = (bundle / unquote(parsed.path)).resolve(strict=True)
                if not dependency.is_relative_to(bundle) or dependency.suffix != ".jar":
                    raise ValueError("EPUBCheck dependency escapes reviewed bundle JARs")
    if not actual_jar.name.endswith(".jar"):
        raise ValueError("EPUBCheck engine must be a reviewed JAR")
    rows: list[dict[str, Any]] = []
    total = 0
    for category, base, paths in (
        ("java-runtime", runtime, sorted(runtime.rglob("*"))),
        ("epubcheck-bundle", bundle, sorted(bundle.rglob("*.jar"))),
    ):
        if len(paths) > 20_000:
            raise ValueError("Java/EPUBCheck binding exceeds file-count budget")
        for path in paths:
            if time.monotonic() >= deadline:
                raise TimeoutError("Java/EPUBCheck binding exhausted original deadline")
            if path.is_dir():
                if not path.resolve(strict=True).is_relative_to(base):
                    raise ValueError("native engine directory symlink escapes reviewed runtime")
                continue
            resolved = path.resolve(strict=True)
            if not resolved.is_relative_to(base):
                raise ValueError("native engine symlink escapes reviewed runtime")
            content = read_bytes_confined(base, resolved, max_bytes=512 * 1024 * 1024)
            total += len(content)
            if total > 2 * 1024 * 1024 * 1024:
                raise ValueError("Java/EPUBCheck binding exceeds byte budget")
            rows.append(
                {
                    "category": category,
                    "path": path.relative_to(base).as_posix(),
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "bytes": len(content),
                }
            )
    return {
        "schema_version": "template-native-epubcheck-engine-v1",
        "java": str(actual_java),
        "jar": str(actual_jar),
        "files": rows,
    }


def freeze_epubcheck_bundle(root: Path, directory: Path, engine: dict[str, Any], *, deadline: float) -> Path:
    """Execute exact admitted private JAR copies, preserving manifest dependency paths."""
    from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory

    bundle = Path(engine["jar"]).parent
    frozen = directory / "epubcheck-engine"
    create_private_native_directory(root, frozen)
    for row in engine["files"]:
        if row["category"] != "epubcheck-bundle":
            continue
        if time.monotonic() >= deadline:
            raise TimeoutError("EPUBCheck freezing exhausted original deadline")
        source = (bundle / row["path"]).resolve(strict=True)
        content = read_bytes_confined(bundle, source, max_bytes=512 * 1024 * 1024)
        if hashlib.sha256(content).hexdigest() != row["sha256"]:
            raise ValueError("EPUBCheck bundle changed before its private copy")
        atomic_write_bytes_confined(root, frozen / row["path"], content, mode=0o600)
    return frozen / Path(engine["jar"]).name


def inspect_epub_spine(epub_bytes: bytes, chapters: tuple[NativeContentContract, ...]) -> dict[str, Any]:
    """Compare every OPF spine body against independently source-owned chapters.

    Chapter contracts include cover/title/navigation entries when those are in
    the spine. No linear=no, empty or decorative entry is silently skipped.
    Unknown source projection syntax remains an explicit inherited blocker.
    """
    import zipfile
    from io import BytesIO
    from pathlib import PurePosixPath
    from defusedxml.ElementTree import fromstring
    from infrastructure.reporting.native_format_content_contracts import text_tokens
    from infrastructure.rendering._epub_package_validation import _resolve_reference

    parse_native_bytes("epub", epub_bytes)
    if not chapters:
        raise ValueError("EPUB spine requires independently reconstructed source chapter contracts")
    observed = []
    findings = []
    blockers: list[str] = []
    with zipfile.ZipFile(BytesIO(epub_bytes)) as archive:
        container = fromstring(archive.read("META-INF/container.xml"))
        rootfile = container.find(
            "{urn:oasis:names:tc:opendocument:xmlns:container}rootfiles/"
            "{urn:oasis:names:tc:opendocument:xmlns:container}rootfile"
        )
        if rootfile is None:
            raise ValueError("EPUB container has no package")
        package_path = rootfile.attrib["full-path"]
        opf = fromstring(archive.read(package_path))
        ns = "{http://www.idpf.org/2007/opf}"
        manifest = opf.find(ns + "manifest")
        spine = opf.find(ns + "spine")
        if manifest is None or spine is None:
            raise ValueError("EPUB package has no manifest/spine")
        items = {item.attrib["id"]: item for item in manifest}
        for ordinal, reference in enumerate(spine):
            item = items[reference.attrib["idref"]]
            member = _resolve_reference(
                item.attrib["href"], base=PurePosixPath(package_path).parent, allow_fragment=False
            )
            if member is None:
                raise ValueError("EPUB spine member escapes its package")
            document = fromstring(archive.read(member))
            body = document.find("{http://www.w3.org/1999/xhtml}body")
            if body is None:
                raise ValueError("EPUB spine document lacks body")
            text = " ".join(body.itertext())
            actual_tokens = text_tokens(text)
            row = {
                "ordinal": ordinal,
                "member": member,
                "sha256": hashlib.sha256(archive.read(member)).hexdigest(),
                "tokens": list(actual_tokens),
            }
            observed.append(row)
            if ordinal < len(chapters):
                contract = chapters[ordinal]
                expected = tuple(token for block in contract.blocks for token in block.tokens)
                blockers.extend(contract.blockers)
                if not expected:
                    blockers.append(f"spine {ordinal}: source nontext/image projection required")
                elif actual_tokens != expected:
                    findings.append({"code": "epub.spine.content", "ordinal": ordinal})
        if len(observed) != len(chapters):
            findings.append({"code": "epub.spine.count"})
    return {
        "schema_version": "template-native-epub-spine-v1",
        "epub_sha256": hashlib.sha256(epub_bytes).hexdigest(),
        "source_contract_digests": [chapter.digest for chapter in chapters],
        "spine": observed,
        "findings": findings,
        "blockers": blockers,
        "status": "fail" if findings else "blocked" if blockers else "pass",
    }


def inspect_epub_reader_layout(
    pdf: bytes, rasters: tuple[bytes, ...], chapters: tuple[NativeContentContract, ...], *, deadline: float
) -> dict[str, Any]:
    """Require all source chapter occurrences in the complete actual reader PDF.

    Reflow changes page breaks, so ordered occurrence mappings carry each
    chapter into its observed page ranges; every page is independently checked
    by the shared glyph/geometry/pixel observer. Nontext source projections
    remain explicit blockers until source image expectations are supplied.
    """
    from infrastructure.reporting.native_format_content_contracts import NativeContentContract, ContentBlock
    from infrastructure.reporting.native_format_pdf_oracles import inspect_pdf_content

    if not chapters:
        raise ValueError("reader layout requires complete source chapter contracts")
    blocks = tuple(
        ContentBlock(f"chapter:{index}:{block.id}", block.kind, block.line, block.tokens)
        for index, chapter in enumerate(chapters)
        for block in chapter.blocks
    )
    sources = tuple(source for chapter in chapters for source in chapter.sources)
    contract = NativeContentContract(
        "epub:complete-reader", sources, blocks, tuple(reason for chapter in chapters for reason in chapter.blockers)
    )
    observation = inspect_pdf_content(pdf, rasters, contract, deadline=deadline)
    if not blocks:
        raise ValueError("reader layout cannot accept empty source obligations")
    return observation


EPUB_CONTROL_CODES: dict[str, str | None] = {
    "baseline": None,
    "changed-number": "epub.spine.content",
    "reordered-spine": "epub.spine.content",
    "omitted-text": "epub.spine.content",
    "tiny-text": "pdf.layout.font",
    "clipped-text": "pdf.content.missing",
    "opaque-overlay": "pdf.visual.invisible",
}


def epub_control_bytes(name: str) -> tuple[bytes, tuple[NativeContentContract, ...]]:
    """Build actual valid EPUB3 baseline and source-preserving native layout mutants."""
    from io import BytesIO
    import zipfile
    from infrastructure.reporting.native_format_content_contracts import content_contract_from_bytes

    if name not in EPUB_CONTROL_CODES:
        raise ValueError("unknown source-owned EPUB control")
    chapters = (
        content_contract_from_bytes(
            "epub:chapter:1", (("first.md", b"# First measurement\n\nMeasured offset -3.25 mV.\n"),)
        ),
        content_contract_from_bytes(
            "epub:chapter:2", (("second.md", b"# Independent repetition\n\nRepeated offset -3.25 mV.\n"),)
        ),
    )
    style = "body { font-family: serif; font-size: 16px; } h1 { font-size: 24px; }"
    if name == "tiny-text":
        style += " p {font-size: 4px;}"
    elif name == "clipped-text":
        style += " p {position: relative; left: -110px;}"
    elif name == "opaque-overlay":
        style += " div.native-overlay {position:relative; top:-2.5em; height:2.5em; width:100%;} div.native-overlay img {display:block; width:100%; height:100%;}"
    first = "Measured offset -3.26 mV." if name == "changed-number" else "Measured offset -3.25 mV."
    if name == "omitted-text":
        first = ""
    bodies = (("First measurement", first), ("Independent repetition", "Repeated offset -3.25 mV."))
    order = (
        '<itemref idref="c2"/><itemref idref="c1"/>'
        if name == "reordered-spine"
        else '<itemref idref="c1"/><itemref idref="c2"/>'
    )
    package = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="id">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="id">urn:uuid:1acb1635-3212-4b03-8a09-665222c222e3</dc:identifier>
<dc:title>Invented reader control</dc:title><dc:language>en</dc:language>
<meta property="dcterms:modified">2020-01-01T00:00:00Z</meta></metadata>
<manifest><item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
<item id="css" href="style.css" media-type="text/css"/>
<item id="c1" href="c1.xhtml" media-type="application/xhtml+xml"/>
<item id="c2" href="c2.xhtml" media-type="application/xhtml+xml"/></manifest><spine>{order}</spine></package>"""
    overlay = b""
    if name == "opaque-overlay":
        from PIL import Image

        pixels = BytesIO()
        Image.new("RGB", (64, 64), "white").save(pixels, format="PNG")
        overlay = pixels.getvalue()
        package = package.replace(
            "</manifest>", '<item id="overlay" href="overlay.png" media-type="image/png"/></manifest>'
        )
    navigation = """<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en">
<head><title>Contents</title></head><body><nav epub:type="toc"><h1>Contents</h1><ol>
<li><a href="c1.xhtml">First measurement</a></li><li><a href="c2.xhtml">Independent repetition</a></li>
</ol></nav></body></html>"""
    output = BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr(
            zipfile.ZipInfo("mimetype", date_time=(2020, 1, 1, 0, 0, 0)),
            "application/epub+zip",
            compress_type=zipfile.ZIP_STORED,
        )
        archive.writestr(
            zipfile.ZipInfo("META-INF/container.xml", date_time=(2020, 1, 1, 0, 0, 0)),
            """<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
<rootfiles><rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/></rootfiles></container>""",
        )
        archive.writestr(zipfile.ZipInfo("EPUB/package.opf", date_time=(2020, 1, 1, 0, 0, 0)), package)
        archive.writestr(zipfile.ZipInfo("EPUB/nav.xhtml", date_time=(2020, 1, 1, 0, 0, 0)), navigation)
        archive.writestr(zipfile.ZipInfo("EPUB/style.css", date_time=(2020, 1, 1, 0, 0, 0)), style)
        if overlay:
            archive.writestr(zipfile.ZipInfo("EPUB/overlay.png", date_time=(2020, 1, 1, 0, 0, 0)), overlay)
        for ordinal, (title, body) in enumerate(bodies, 1):
            cover = (
                '<div class="native-overlay"><img src="overlay.png" alt="" role="presentation"/></div>'
                if overlay
                else ""
            )
            archive.writestr(
                zipfile.ZipInfo(f"EPUB/c{ordinal}.xhtml", date_time=(2020, 1, 1, 0, 0, 0)),
                f"""<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head><title>{title}</title><link rel="stylesheet" type="text/css" href="style.css"/></head>
<body><h1>{title}</h1><p>{body}</p>{cover}</body></html>""",
            )
    return output.getvalue(), chapters


def run_epub_control(
    root: Path,
    directory: Path,
    name: str,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    epubcheck_jar: Path,
    java_executable: Path,
    frozen_engine: Path | None = None,
) -> dict[str, Any]:
    """Require EPUBCheck success, real reader rasterization and intended native diagnosis."""
    from infrastructure.reporting.native_format_acceptance_checks import audit_pdf_raster

    content, chapters = epub_control_bytes(name)
    source = directory / "fixture.epub"
    atomic_write_bytes_confined(root, source, content, mode=0o600)
    reader = SnapshotReader(root)
    artifact = reader.read(source.relative_to(root).as_posix())
    converted = inspect_epub(
        root,
        directory,
        artifact,
        env=env,
        deadline=deadline,
        run_id=run_id,
        epubcheck_jar=epubcheck_jar,
        java_executable=java_executable,
        frozen_engine=frozen_engine,
    )
    pdf = reader.read(converted["pdf"]["path"])
    raster = audit_pdf_raster(
        root, directory, pdf, converted["observation"], env=env, deadline=deadline, run_id=run_id, ordinal=0
    )
    pixels = tuple(reader.read(row["path"]).content for row in raster["rasters"])
    spine = inspect_epub_spine(content, chapters)
    layout = inspect_epub_reader_layout(pdf.content, pixels, chapters, deadline=deadline)
    expected = EPUB_CONTROL_CODES[name]
    codes = {item["code"] for item in spine["findings"] + layout["findings"]}
    if (
        spine["blockers"]
        or layout["blockers"]
        or (expected is None and codes)
        or (expected is not None and expected not in codes)
    ):
        raise ValueError("actual valid EPUB control did not produce intended native reader diagnostic")
    if not reader.unchanged():
        raise ValueError("native EPUB control reader/raster custody changed")
    return {
        "schema_version": "template-native-epub-valid-control-v1",
        "name": name,
        "expected_code": expected,
        "conversion": converted,
        "raster": raster,
        "spine": spine,
        "layout": layout,
        "oracle_exit_code": 0 if expected is None else 1,
    }


def supervise_epub_controls(
    root: Path,
    directory: Path,
    *,
    interpreter: Path,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    epubcheck_jar: Path,
    java_executable: Path,
    frozen_engine: Path | None = None,
) -> list[dict[str, Any]]:
    """Supervise baseline-first EPUBCheck plus real-reader valid native mutants."""
    import json
    from infrastructure.core.execution_boundary import run_bounded_subprocess
    from infrastructure.project.public_acceptance_evidence import bootstrap_command, write_json
    from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory

    engine = bind_epubcheck_engine(epubcheck_jar, java_executable, deadline=deadline)
    private_jar = (
        freeze_epubcheck_bundle(root, directory, engine, deadline=deadline)
        if frozen_engine is None
        else frozen_engine / Path(engine["jar"]).name
    )
    SnapshotReader(root).public_path(private_jar.relative_to(root).as_posix())
    records = []
    for ordinal, (name, diagnostic) in enumerate(EPUB_CONTROL_CODES.items()):
        child = directory / f"epub-control-{ordinal}"
        create_private_native_directory(root, child)
        command = bootstrap_command(
            interpreter,
            root,
            __name__,
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
            "--epubcheck-jar",
            str(epubcheck_jar),
            "--java-executable",
            str(java_executable),
            "--frozen-engine",
            str(private_jar.parent),
        )
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("EPUB controls exhausted original deadline")
        process = run_bounded_subprocess(command, cwd=root, env=env, timeout=min(remaining, 120))
        receipt = write_json(
            root,
            directory / f"epub-control-{ordinal}-process.json",
            {
                "schema_version": "template-native-epub-control-process-v1",
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
            raise NativeToolUnavailable(f"actual EPUB control {name} requires missing native engine")
        expected = 0 if diagnostic is None else 1
        if (
            process.timed_out
            or process.custody_refused
            or process.returncode != expected
            or process.original_returncode != expected
        ):
            raise ValueError("actual EPUB control did not preserve intended original outcome")
        result = SnapshotReader(root).read((child / "observation.json").relative_to(root).as_posix())
        payload = json.loads(result.content)
        codes = {item["code"] for item in payload["spine"]["findings"] + payload["layout"]["findings"]}
        if (
            payload["name"] != name
            or payload["expected_code"] != diagnostic
            or payload["spine"]["blockers"]
            or payload["layout"]["blockers"]
        ):
            raise ValueError("actual EPUB control receipt differs from source-owned obligations")
        if diagnostic is not None and diagnostic not in codes:
            raise ValueError("actual EPUB mutant has no intended native diagnostic")
        records.append(
            {
                "name": name,
                "process_artifact": receipt,
                "artifact": {"path": result.relative, "sha256": result.sha256},
                "original_exit_code": expected,
            }
        )
    return records


def main() -> int:
    """Private supervised EPUB control entry point."""
    import argparse
    import os
    from infrastructure.project.public_acceptance_evidence import write_json

    parser = argparse.ArgumentParser()
    parser.add_argument("--control", choices=tuple(EPUB_CONTROL_CODES), required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--deadline", type=float, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--epubcheck-jar", type=Path, required=True)
    parser.add_argument("--java-executable", type=Path, required=True)
    parser.add_argument("--frozen-engine", type=Path)
    args = parser.parse_args()
    try:
        result = run_epub_control(
            args.root,
            args.directory,
            args.control,
            env=dict(os.environ),
            deadline=args.deadline,
            run_id=args.run_id,
            epubcheck_jar=args.epubcheck_jar,
            java_executable=args.java_executable,
            frozen_engine=args.frozen_engine,
        )
    except NativeToolUnavailable:
        return 75
    write_json(args.root, args.directory / "observation.json", result)
    return int(result["oracle_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
