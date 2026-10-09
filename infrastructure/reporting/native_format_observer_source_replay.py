"""Independent current-reader semantic source and Office conversion replay."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any

from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_format_content_contracts import NativeContentContract
from infrastructure.reporting.native_format_portable_custody import producer_path
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader


def replay_office_conversion(
    root: Path,
    directory: Path,
    original: ArtifactSnapshot,
    raw: dict[str, Any],
    reader: SnapshotReader,
    *,
    run_id: str,
    custody: dict[str, str],
) -> ArtifactSnapshot:
    """Replay exact Office input, conversion command and original PDF bytes."""
    from infrastructure.reporting.native_format_acceptance_validation import _file, _tool
    from infrastructure.reporting.native_format_acceptance_checks import parse_native_bytes

    kind = raw.get("kind")
    if raw.get("schema_version") != "template-native-office-conversion-v2" or kind not in {"docx", "pptx"}:
        raise ValueError("invalid actual Office conversion identity")
    consumed = _file(raw.get("input"), reader)
    pdf = _file(raw.get("pdf"), reader)
    if consumed.path != directory / f"input.{kind}" or consumed.content != original.content:
        raise ValueError("native Office did not consume exact source artifact")
    if pdf.path != directory / "input.pdf" or raw.get("observation") != parse_native_bytes("pdf", pdf.content):
        raise ValueError("native Office PDF bytes/structural observation differ")
    tools = raw.get("tool_artifacts")
    if not isinstance(tools, list) or len(tools) != 2:
        raise ValueError("Office conversion omitted its actual process receipts")
    version = _tool(tools[0], reader, run_id, "soffice", "office-version", ["--version"])
    profile = producer_path(custody, root, directory / "office-profile")
    filter_name = "writer_pdf_Export" if kind == "docx" else "impress_pdf_Export"
    args = [
        f"-env:UserInstallation={profile.as_uri()}",
        "--headless",
        "--nologo",
        "--nodefault",
        "--nolockcheck",
        "--nofirststartwizard",
        "--convert-to",
        f"pdf:{filter_name}",
        "--outdir",
        str(producer_path(custody, root, directory)),
        str(producer_path(custody, root, consumed.path)),
    ]
    conversion = _tool(tools[1], reader, run_id, "soffice", "office-conversion", args)
    if any(version.get(key) != conversion.get(key) for key in ("executable", "executable_sha256")):
        raise ValueError("Office probe and conversion used different executable bytes")
    from infrastructure.project.native_reader_runtime_custody import replay_retained_native_reader_runtime

    replay_retained_native_reader_runtime(
        raw["reader_runtime_before"],
        raw["reader_runtime_after"],
        read_artifact=lambda binding: _file(binding, reader).content,
        run_id=run_id,
        executable=conversion["executable"],
        executable_sha256=conversion["executable_sha256"],
    )
    return pdf


def replay_html_source(
    root: Path,
    directory: Path,
    scope: str,
    artifact: NativeArtifact,
    raw: dict[str, Any],
    reader: SnapshotReader,
    *,
    run_id: str,
    custody: dict[str, str],
    deadline: float,
    env: dict[str, str],
) -> NativeContentContract:
    """Reparse current admitted sources with reader-local Pandoc, without producer access."""
    import shutil
    import tempfile
    from dataclasses import replace
    from infrastructure.core.execution_boundary import run_bounded_subprocess
    from infrastructure.reporting.native_format_acceptance_validation import _file, _tool
    from infrastructure.reporting.native_format_content_contracts import semantic_content_contract_from_ast
    from infrastructure.reporting.native_format_semantic_source import semantic_source_plan

    content, sources, bibliographies = semantic_source_plan(root, scope, artifact, reader)
    if raw.get("schema_version") != "template-native-semantic-source-observation-v1":
        raise ValueError("invalid semantic source observation")
    consumed = _file(raw.get("source"), reader)
    ast = _file(raw.get("ast"), reader)
    if consumed.path != directory / "semantic-source.md" or consumed.content != content:
        raise ValueError("semantic parse consumed different reconstructed source")
    if ast.path != directory / "semantic-ast.json":
        raise ValueError("semantic AST belongs to another attempt")
    contract = semantic_content_contract_from_ast(artifact.id, (*sources, *bibliographies), ast.content)
    from infrastructure.reporting.native_format_semantic_original import replay_original_source

    contract = replay_original_source(
        root,
        directory,
        (*sources, *bibliographies),
        contract,
        raw["original_source"],
        reader,
        run_id=run_id,
        custody=custody,
        env=env,
        deadline=deadline,
    )
    if artifact.id != "manuscript:html" and not (artifact.id.startswith("section:") and artifact.id.endswith(":html")):
        contract = replace(
            contract,
            blockers=(*contract.blockers, f"{artifact.id}: domain projection is not a literal full manuscript"),
        )
    if raw.get("contract") != contract.to_dict():
        raise ValueError("source semantic contract is not derived from actual admitted AST bytes")
    original_args = [
        str(producer_path(custody, root, consumed.path)),
        "--from=markdown+tex_math_dollars+raw_tex+header_attributes",
        "--to=json",
    ]
    filters = raw.get("filters")
    if not isinstance(filters, list) or len(filters) != 1:
        raise ValueError("semantic source omitted the source-owned formalism filter")
    sdk_reader = SnapshotReader(Path(__file__).absolute().parents[2])
    filter_bytes = sdk_reader.read("infrastructure/rendering/formalism.lua")
    copied = _file(filters[0].get("consumed"), reader)
    if (
        filters[0].get("source") != {"path": filter_bytes.relative, "sha256": filter_bytes.sha256}
        or copied.path != directory / "semantic-filter-0.lua"
        or copied.content != filter_bytes.content
    ):
        raise ValueError("semantic formalism filter differs from current source")
    original_args.extend(["--lua-filter", str(producer_path(custody, root, copied.path))])
    expected_bibs = [{"path": path, "sha256": hashlib.sha256(data).hexdigest()} for path, data in bibliographies]
    if raw.get("bibliographies") != expected_bibs:
        raise ValueError("semantic bibliography source identity differs")
    for index, (_, data) in enumerate(bibliographies):
        bib = reader.read((directory / f"semantic-bibliography-{index}.bib").relative_to(root).as_posix())
        if bib.content != data:
            raise ValueError("semantic bibliography consumed bytes differ")
        original_args.append(f"--bibliography={producer_path(custody, root, bib.path)}")
    if bibliographies:
        original_args.extend(["--citeproc", "--metadata=link-citations:true"])
    transcript = _file(raw["tool"]["artifact"], reader).json_object()
    tail = transcript.get("command", [])[1 + len(original_args) :]
    if tail:
        if (
            artifact.id != "manuscript:html"
            or len(tail) != 2
            or tail[0] != "--filter"
            or Path(tail[1]).name != "pandoc-crossref"
        ):
            raise ValueError("semantic source parser used undeclared arguments")
        original_args.extend(tail)
    transcript = _tool(raw["tool"]["artifact"], reader, run_id, "pandoc", "semantic-pandoc", original_args)
    if transcript.get("stdout", "").encode() != ast.content:
        raise ValueError("semantic AST differs from original Pandoc stdout")
    pandoc = shutil.which("pandoc", path=env.get("PATH"))
    crossref = shutil.which("pandoc-crossref", path=env.get("PATH")) if tail else None
    if not pandoc or (tail and not crossref):
        raise ValueError("independent reader lacks declared semantic parsing tools")
    with tempfile.TemporaryDirectory(prefix="native-semantic-replay-") as private:
        work = Path(private).resolve()
        source = work / "source.md"
        source.write_bytes(content)
        filter_path = work / "formalism.lua"
        filter_path.write_bytes(filter_bytes.content)
        args = [
            pandoc,
            str(source),
            "--from=markdown+tex_math_dollars+raw_tex+header_attributes",
            "--to=json",
            "--lua-filter",
            str(filter_path),
        ]
        for index, (_, data) in enumerate(bibliographies):
            bib_path = work / f"bibliography-{index}.bib"
            bib_path.write_bytes(data)
            args.append(f"--bibliography={bib_path}")
        if bibliographies:
            args.extend(["--citeproc", "--metadata=link-citations:true"])
        if crossref:
            args.extend(["--filter", crossref])
        result = run_bounded_subprocess(args, cwd=work, env=env, timeout=min(60.0, deadline - time.monotonic()))
        if result.returncode != 0 or result.original_returncode != 0 or result.timed_out or result.custody_refused:
            raise ValueError("independent actual source parse failed")
        independent = semantic_content_contract_from_ast(
            artifact.id, (*sources, *bibliographies), result.stdout.encode()
        )
        if contract.blockers != (
            *independent.blockers,
            *raw["original_source"]["survival"]["blockers"],
        ) and artifact.id.startswith(("section:", "manuscript:")):
            raise ValueError("independent source unsupported obligations differ")
        independent = replace(
            independent,
            blockers=(*independent.blockers, *raw["original_source"]["survival"]["blockers"]),
            original_ast_sha256=contract.original_ast_sha256,
            original_source_occurrences=contract.original_source_occurrences,
        )
        expected = contract.to_dict()
        actual = independent.to_dict()
        expected.pop("ast_sha256", None)
        actual.pop("ast_sha256", None)
        if artifact.id != "manuscript:html" and not artifact.id.startswith("section:"):
            actual["blockers"] = list(contract.blockers)
        if expected != actual:
            raise ValueError("independent reader source AST semantics differ")
    if not sdk_reader.unchanged():
        raise ValueError("current reader semantic SDK source changed")
    return contract
