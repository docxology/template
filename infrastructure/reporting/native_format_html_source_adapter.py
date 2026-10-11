"""Producer and portable reader adapters for body plus separate config metadata."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_format_acceptance_validation import _file, _tool
from infrastructure.reporting.native_format_content_contracts import NativeContentContract, SemanticContentContract
from infrastructure.reporting.native_format_current_pandoc import current_pandoc_reader
from infrastructure.reporting.native_format_html_source_metadata import (
    HTML_WITNESS_SCHEMA,
    METADATA_OBSERVATION_SCHEMA,
    METADATA_PURPOSE,
    binding,
    html_metadata_plan,
    metadata_contract,
    portable_metadata_document,
    remaining_seconds,
)
from infrastructure.reporting.native_format_observer_source_replay import replay_html_source
from infrastructure.reporting.native_format_portable_custody import producer_path
from infrastructure.reporting.native_format_semantic_source import observe_html_source, semantic_source_plan
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def _body_transcript(body: dict[str, Any], reader: SnapshotReader, run_id: str) -> dict[str, Any]:
    """Close genuine body parser outcome; reader first replays its source argv."""
    transcript = _file(body["tool"]["artifact"], reader).json_object()
    command = transcript.get("command")
    if not isinstance(command, list) or len(command) < 4 or any(not isinstance(item, str) for item in command):
        raise ValueError("HTML body parse omitted its actual native argv")
    return _tool(body["tool"]["artifact"], reader, run_id, "pandoc", "semantic-pandoc", command[1:])


def _argv_record(
    custody: dict[str, Any], consumed: dict[str, str], body: dict[str, Any], args: list[str]
) -> dict[str, Any]:
    """Bind exact source-derived CLI strings separately from manuscript bytes."""
    return {
        "schema_version": "template-native-html-config-argv-v1",
        "source_config": custody["consumed_config"],
        "consumed_config": consumed,
        "body_source": body["source"],
        "arguments": args,
    }


def _producer_bibliographies(
    root: Path, directory: Path, body: dict[str, Any], reader: SnapshotReader
) -> tuple[tuple[str, bytes], ...]:
    return tuple(
        (str(snapshot.path), snapshot.content)
        for index in range(len(body["bibliographies"]))
        for snapshot in [reader.read((directory / f"semantic-bibliography-{index}.bib").relative_to(root).as_posix())]
    )


def observe_html_source_witness(
    root: Path,
    directory: Path,
    scope: str,
    artifact: NativeArtifact,
    reader: SnapshotReader,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> tuple[SemanticContentContract, dict[str, Any], dict[str, Any] | None]:
    """Execute separately bound body/metadata parses with fresh filter children."""
    remaining_seconds(deadline)
    plan = html_metadata_plan(root, scope, artifact, reader)
    contract, body = observe_html_source(
        root, directory, scope, artifact, reader, env=env, deadline=deadline, run_id=run_id
    )
    if plan is None:
        remaining_seconds(deadline)
        return contract, {"schema_version": HTML_WITNESS_SCHEMA, "body": body, "source_metadata": None}, None
    config, source, custody = plan
    copied_path = directory / "semantic-config.yaml"
    atomic_write_bytes_confined(root, copied_path, config.content, mode=0o600)
    copied = reader.read(copied_path.relative_to(root).as_posix())
    transcript = _body_transcript(body, reader, run_id)
    args = [*transcript["command"][1:], *source["pandoc_args"]]
    crossref_filter = None
    if "--filter" in args:
        from infrastructure.reporting.native_crossref_pandoc import source_crossref_pandoc
        from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime

        from infrastructure.reporting.native_crossref_pair import parent_observation

        body_filter = parent_observation(body["crossref_filter"], reader)
        body_spec = _file(body_filter["specification"], reader).json_object()
        args[args.index("--filter") + 1] = body_spec["crossref"]["path"]
        runtime = CitationRuntime(
            root, directory / "metadata-crossref-owner", env=env, deadline=deadline, run_id=run_id
        )
        inputs = [
            _file(body["source"], reader).path,
            copied.path,
            *(_file(row["consumed"], reader).path for row in body["filters"]),
        ]
        inputs.extend(directory / f"semantic-bibliography-{index}.bib" for index in range(len(body["bibliographies"])))
        observed, crossref_filter = source_crossref_pandoc(
            runtime, scope, args, METADATA_PURPOSE, output_format="json", input_paths=tuple(inputs)
        )
        args = observed["command"][1:]
        tool = {
            "artifact": runtime.tools[-1],
            "exit_code": observed["exit_code"],
            "original_exit_code": observed["original_exit_code"],
        }
    else:
        tool = native_tool_record(
            root, directory, "pandoc", args, env=env, deadline=deadline, run_id=run_id, purpose=METADATA_PURPOSE
        )
    argv = write_json(
        root, directory / "semantic-config-metadata-argv.json", _argv_record(custody, binding(copied), body, args)
    )
    actual = _tool(tool["artifact"], reader, run_id, "pandoc", METADATA_PURPOSE, args)
    if (
        actual["executable_sha256"] != transcript["executable_sha256"]
        or actual["executable"] != transcript["executable"]
    ):
        raise ValueError("body and metadata source parses used different actual Pandoc bytes")
    ast_path = directory / "semantic-config-metadata-ast.json"
    atomic_write_bytes_confined(root, ast_path, actual["stdout"].encode(), mode=0o600)
    ast = reader.read(ast_path.relative_to(root).as_posix())
    body_ast = _file(body["ast"], reader)
    metadata = metadata_contract(
        source, ast.content, body_ast.content, _producer_bibliographies(root, directory, body, reader)
    )
    observation = {
        "schema_version": METADATA_OBSERVATION_SCHEMA,
        "config_custody": custody,
        "consumed_config": binding(copied),
        "argv": argv,
        "ast": binding(ast),
        "tool": tool,
        "contract": metadata,
        "crossref_filter": crossref_filter,
    }
    if not reader.unchanged():
        raise ValueError("HTML body/config/metadata artifacts changed during genuine observation")
    remaining_seconds(deadline)
    return contract, {"schema_version": HTML_WITNESS_SCHEMA, "body": body, "source_metadata": observation}, metadata


def replay_html_source_witness(
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
) -> tuple[NativeContentContract, dict[str, Any] | None]:
    """Rebuild current YAML/hydration and genuinely reparse reader-local metadata."""
    remaining_seconds(deadline)
    if raw.get("schema_version") != HTML_WITNESS_SCHEMA or set(raw) != {"schema_version", "body", "source_metadata"}:
        raise ValueError("HTML source witness omitted separate body and metadata custody")
    plan = html_metadata_plan(root, scope, artifact, reader)
    body = raw["body"]
    contract = replay_html_source(
        root, directory, scope, artifact, body, reader, run_id=run_id, custody=custody, deadline=deadline, env=env
    )
    observation = raw["source_metadata"]
    if plan is None:
        if observation is not None:
            raise ValueError("section/domain HTML received metadata argv the source renderer never consumes")
        remaining_seconds(deadline)
        return contract, None
    config, source, expected_custody = plan
    if (
        not isinstance(observation, dict)
        or set(observation)
        != {"schema_version", "config_custody", "consumed_config", "argv", "ast", "tool", "contract", "crossref_filter"}
        or observation.get("schema_version") != METADATA_OBSERVATION_SCHEMA
    ):
        raise ValueError("combined HTML omitted genuine separate config metadata evidence")
    if observation.get("config_custody") != expected_custody:
        raise ValueError("HTML metadata source config/current hydration differs from reader evidence")
    copied = _file(observation.get("consumed_config"), reader)
    ast = _file(observation.get("ast"), reader)
    if copied.path != directory / "semantic-config.yaml" or copied.content != config.content:
        raise ValueError("HTML metadata CLI was derived from different consumed YAML bytes")
    if ast.path != directory / "semantic-config-metadata-ast.json":
        raise ValueError("HTML metadata AST belongs to another artifact/attempt")
    transcript = _body_transcript(body, reader, run_id)
    args = [*transcript["command"][1:], *source["pandoc_args"]]
    if "--filter" in args:
        from infrastructure.reporting.native_crossref_replay import CrossrefFilterReaderOperation
        from infrastructure.reporting.native_format_joint_source import require_native_operation

        operation = require_native_operation(reader)
        CrossrefFilterReaderOperation(
            operation.source, observation["crossref_filter"], reader, scope=scope, run_id=run_id, deadline=deadline
        ).replay()
        from infrastructure.reporting.native_crossref_pair import parent_observation, parent_launcher_binding

        graph = parent_observation(observation["crossref_filter"], reader)
        wrapper = _file(parent_launcher_binding(graph), reader)
        args[args.index("--filter") + 1] = str(producer_path(custody, root, wrapper.path))
    elif observation["crossref_filter"] is not None:
        raise ValueError("HTML metadata without a filter cannot claim a crossref child")
    argv = _file(observation.get("argv"), reader)
    expected_argv = _argv_record(expected_custody, binding(copied), body, args)
    # The copied/body bindings are repository-relative; only actual command paths
    # carry the authenticated producer label after portable transport.
    if argv.path != directory / "semantic-config-metadata-argv.json" or argv.json_object() != expected_argv:
        raise ValueError("HTML config source values and actual consumed CLI argv differ")
    actual = _tool(observation["tool"]["artifact"], reader, run_id, "pandoc", METADATA_PURPOSE, args)
    if actual["stdout"].encode() != ast.content:
        raise ValueError("HTML metadata AST differs from genuine original Pandoc stdout")
    if any(actual[key] != transcript[key] for key in ("executable", "executable_sha256")):
        raise ValueError("HTML metadata parser used different actual native executable bytes")
    content, _, bibliographies = semantic_source_plan(root, scope, artifact, reader)
    original_bibs = tuple(
        (str(producer_path(custody, root, directory / f"semantic-bibliography-{index}.bib")), data)
        for index, (_, data) in enumerate(bibliographies)
    )
    body_ast = _file(body["ast"], reader)
    metadata = metadata_contract(source, ast.content, body_ast.content, original_bibs)
    if observation.get("contract") != metadata:
        raise ValueError("HTML metadata source contract was not derived from retained current-source native AST")
    with current_pandoc_reader(
        root,
        reader,
        env=env,
        deadline=deadline,
        purpose="html-metadata-ast",
        crossref="--filter" in transcript["command"],
    ) as current:
        local_source = current.runtime.freeze("source.md", content)
        local_filter = current.runtime.freeze("formalism.lua", _file(body["filters"][0]["consumed"], reader).content)
        local_args = [
            str(local_source),
            "--from=markdown+tex_math_dollars+raw_tex+header_attributes",
            "--to=json",
            "--lua-filter",
            str(local_filter),
        ]
        local_bibs: list[tuple[str, bytes]] = []
        for index, (_, data) in enumerate(bibliographies):
            path = current.runtime.freeze(f"bibliography-{index}.bib", data)
            local_args.append(f"--bibliography={path}")
            local_bibs.append((str(path), data))
        if bibliographies:
            local_args.extend(["--citeproc", "--metadata=link-citations:true"])
        if current.crossref is not None:
            local_args.extend(["--filter", current.crossref])
        local_args.extend(source["pandoc_args"])
        if current.crossref is not None:
            result, _ = current.source_crossref_tool(
                local_args, "current-html-metadata-ast", scope=scope, output_format="json"
            )
        else:
            result = current.tool("pandoc", local_args, "current-html-metadata-ast")
        independent = portable_metadata_document(result["stdout"].encode(), tuple(local_bibs))
        retained = portable_metadata_document(ast.content, original_bibs)
        if independent != retained:
            raise ValueError("independent full native source/metadata AST occurrences differ")
    if not reader.unchanged():
        raise ValueError("HTML reader config/body/hydration/native evidence changed during replay")
    remaining_seconds(deadline)
    return contract, metadata
