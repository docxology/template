"""Source-only Office references with unresolved scientific coverage retained."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.reporting.native_format_acceptance_checks import native_tool_record, parse_native_bytes
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_office_semantic_source import observe_office_semantic_source
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

MAX_REFERENCE_INPUT_BYTES = 250 * 1024 * 1024


def build_office_source_reference(
    root: Path,
    directory: Path,
    scope: str,
    artifact: NativeArtifact,
    reader: SnapshotReader,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> dict[str, Any]:
    """Build a real package from source; never read the candidate artifact.

    Caller supplies a fresh private directory. The filtered reference AST is
    distinct from the unfiltered occurrence census, which remains mandatory.
    Exact image bytes are frozen before the writer consumes them.
    """
    import yaml
    from infrastructure.rendering._pdf_title_page_config import build_pandoc_metadata
    from infrastructure.validation.output.render_formats import render_config_manuscript_dir

    ast, source = observe_office_semantic_source(
        root, directory, scope, artifact, reader, env=env, deadline=deadline, run_id=run_id
    )
    document = json.loads(ast)
    manuscript = render_config_manuscript_dir(root / "projects" / scope)
    project = root / "projects" / scope
    settings: dict[str, Any] = {}
    if source["config"]:
        config = reader.read(source["config"]["path"])
        if config.sha256 != source["config"]["sha256"]:
            raise ValueError("Office source reference config changed")
        loaded = yaml.safe_load(config.content)
        if isinstance(loaded, dict):
            settings = loaded
    metadata = build_pandoc_metadata(settings)
    raw_metadata = settings.get("metadata") or {}
    language = raw_metadata.get("language", "en") if isinstance(raw_metadata, dict) else "en"
    if artifact.format == "epub":
        authors = metadata.get("author") or []
        author = "; ".join(str(item) for item in authors) if isinstance(authors, list) else str(authors)
        metadata = {
            key: value
            for key, value in {"title": metadata.get("title"), "author": author, "lang": language}.items()
            if value
        }
    metadata_path = directory / "source-reference-metadata.yaml"
    atomic_write_bytes_confined(
        root, metadata_path, yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False).encode(), mode=0o600
    )
    figures: list[dict[str, Any]] = []
    pending = [document["blocks"]]
    total = len(ast)
    while pending:
        if time.monotonic() >= deadline:
            raise TimeoutError("Office source reference input freeze expired")
        value = pending.pop()
        if isinstance(value, dict):
            if value.get("t") == "Image":
                image = value.get("c")
                if not isinstance(image, list) or len(image) != 3 or not isinstance(image[2], list):
                    raise ValueError("Office source image AST is malformed")
                target = image[2][0]
                if not isinstance(target, str) or urlsplit(target).scheme or urlsplit(target).netloc:
                    raise ValueError("Office source reference requires local bound image bytes")
                # These are the production combined writer's resource roots.
                roots = (manuscript, project / "output/figures", project / "output", project / "output/web")
                original = next((base / target for base in roots if (base / target).is_file()), None)
                if original is None:
                    raise ValueError(f"Office source image has no admitted resource: {target}")
                original = original.resolve(strict=True)
                snapshot = reader.read(original.relative_to(root).as_posix())
                total += len(snapshot.content)
                if total > MAX_REFERENCE_INPUT_BYTES:
                    raise ValueError("Office source reference exceeds finite input-byte budget")
                frozen = directory / f"source-figure-{len(figures)}{original.suffix}"
                atomic_write_bytes_confined(root, frozen, snapshot.content, mode=0o600)
                image[2][0] = str(frozen)
                figures.append(
                    {
                        "target": target,
                        "source": {"path": snapshot.relative, "sha256": snapshot.sha256},
                        "consumed": {"path": frozen.relative_to(root).as_posix(), "sha256": snapshot.sha256},
                    }
                )
            pending.extend(reversed(list(value.values())))
        elif isinstance(value, list):
            pending.extend(reversed(value))
    reference_ast = directory / "source-reference-ast.json"
    atomic_write_bytes_confined(root, reference_ast, json.dumps(document, ensure_ascii=False).encode(), mode=0o600)
    package = directory / f"source-reference.{artifact.format}"
    args = [
        str(reference_ast),
        "--from=json",
        f"--to={artifact.format}",
        "--standalone",
        f"--metadata-file={metadata_path}",
        "--output",
        str(package),
    ]
    cover = None
    cover_alt = None
    source_epoch = None
    writer_env = dict(env)
    cover_declared = any(
        isinstance(settings.get(section), dict) and settings[section].get("cover") for section in ("book", "paper")
    )
    if artifact.format == "epub":
        from infrastructure.rendering._pdf_title_page_images import _cover_image_path, _cover_image_alt
        from infrastructure.rendering.epub_renderer import (
            _FIXED_EPUB_SOURCE_DATE_EPOCH,
            _MAX_SUPPORTED_SOURCE_DATE_EPOCH,
        )

        source_epoch = int(env.get("SOURCE_DATE_EPOCH", str(_FIXED_EPUB_SOURCE_DATE_EPOCH)))
        if not 0 <= source_epoch <= _MAX_SUPPORTED_SOURCE_DATE_EPOCH:
            raise ValueError("Office source reference requires a valid explicit EPUB epoch")
        writer_env["SOURCE_DATE_EPOCH"] = str(source_epoch)
        if source["config"]:
            cover_path = _cover_image_path(settings, root / source["config"]["path"])
            if cover_path is not None:
                snapshot = reader.read(cover_path.resolve(strict=True).relative_to(root).as_posix())
                total += len(snapshot.content)
                if total > MAX_REFERENCE_INPUT_BYTES:
                    raise ValueError("Office source reference cover exceeds finite input-byte budget")
                frozen_cover = directory / f"source-cover{cover_path.suffix}"
                atomic_write_bytes_confined(root, frozen_cover, snapshot.content, mode=0o600)
                cover_alt = _cover_image_alt(settings)
                if not cover_alt:
                    raise ValueError("source EPUB cover requires declared alternative text")
                cover = {
                    "source": {"path": snapshot.relative, "sha256": snapshot.sha256},
                    "consumed": {"path": frozen_cover.relative_to(root).as_posix(), "sha256": snapshot.sha256},
                    "alt": cover_alt,
                }
                args.append(f"--epub-cover-image={frozen_cover}")
        # Match the source writer's declared package identity finalizer.
        from infrastructure.rendering.epub_renderer import _EPUB_IDENTIFIER_PLACEHOLDER

        args.append(f"--metadata=identifier:{_EPUB_IDENTIFIER_PLACEHOLDER}")
    tool = native_tool_record(
        root,
        directory,
        "pandoc",
        args,
        env=writer_env,
        deadline=deadline,
        run_id=run_id,
        purpose="office-source-reference-writer",
    )
    if tool["original_exit_code"] != 0 or tool["exit_code"] != 0:
        raise ValueError("actual Office source reference writer failed")
    if artifact.format == "epub":
        from infrastructure.rendering.epub_renderer import _normalize_epub_archive

        if cover:
            from infrastructure.rendering._epub_cover_accessibility import apply_epub_cover_accessibility

            apply_epub_cover_accessibility(package, str(cover_alt))
        if source_epoch is None:
            raise ValueError("Office EPUB reference has no frozen writer epoch")
        _normalize_epub_archive(package, source_date_epoch=source_epoch)
    local = SnapshotReader(root)
    snapshot = local.read(package.relative_to(root).as_posix())
    parse_native_bytes(artifact.format, snapshot.content)
    frozen_ast = local.read(reference_ast.relative_to(root).as_posix())
    frozen_metadata = local.read(metadata_path.relative_to(root).as_posix())
    if not reader.unchanged() or not local.unchanged() or time.monotonic() >= deadline:
        raise ValueError("Office source reference custody changed")
    blockers = list(source["blockers"]) + list(source["source_coverage"]["blockers"])
    # Cover configuration is an additional source obligation outside body AST.
    if cover_declared:
        blockers.append("Office configured cover requires independent frozen asset/native witness")
    return {
        "schema_version": "template-native-office-source-reference-v1",
        "source": source,
        "package": {"path": snapshot.relative, "sha256": snapshot.sha256},
        "writer": tool,
        "ast": {"path": frozen_ast.relative, "sha256": frozen_ast.sha256},
        "metadata": {"path": frozen_metadata.relative, "sha256": frozen_metadata.sha256},
        "figures": figures,
        "cover": cover,
        "source_date_epoch": source_epoch,
        "status": "blocked" if blockers else "observed",
        "blockers": blockers,
        "assurance": "source-only native package; full native visual and occurrence witnesses still required",
    }


def read_office_package_ast(
    root: Path,
    directory: Path,
    package: dict[str, Any],
    kind: str,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> dict[str, Any]:
    """Run a genuine native-package reader with exact original input bytes."""
    if kind not in {"docx", "epub"}:
        raise ValueError("Office reference package reader requires DOCX or EPUB")
    reader = SnapshotReader(root)
    original = reader.read(package["path"])
    if original.sha256 != package["sha256"]:
        raise ValueError("Office reference readback input changed")
    frozen = directory / f"readback-input.{kind}"
    atomic_write_bytes_confined(root, frozen, original.content, mode=0o600)
    tool = native_tool_record(
        root,
        directory,
        "pandoc",
        [str(frozen), f"--from={kind}", "--to=json", "--standalone"],
        env=env,
        deadline=deadline,
        run_id=run_id,
        purpose="office-package-readback",
    )
    if tool["original_exit_code"] != 0 or tool["exit_code"] != 0:
        raise ValueError("actual Office native-package readback failed")
    local = SnapshotReader(root)
    content = local.read(tool["artifact"]["path"]).json_object()["stdout"].encode()
    json.loads(content)
    path = directory / "package-readback-ast.json"
    atomic_write_bytes_confined(root, path, content, mode=0o600)
    if not reader.unchanged() or not local.unchanged():
        raise ValueError("Office original/native-package readback custody changed")
    return {
        "ast": {"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(content).hexdigest()},
        "input": package,
        "tool": tool,
    }


def inspect_office_package_reference(
    reference_ast: bytes, candidate_ast: bytes, source_coverage: dict[str, Any]
) -> dict[str, Any]:
    """Compare complete actual reader blocks and retain source obligations.

    Package readback can differ from original mathematical/citation syntax.
    No general normalization is allowed; unknown differences require proof.
    Equality cannot clear a source occurrence lost by both writers.
    """
    documents = [json.loads(data) for data in (reference_ast, candidate_ast)]
    if any(
        not isinstance(row, dict) or not isinstance(row.get("blocks"), list) or not row.get("pandoc-api-version")
        for row in documents
    ):
        raise ValueError("Office package comparison requires genuine document ASTs")
    findings = []
    if documents[0]["pandoc-api-version"] != documents[1]["pandoc-api-version"]:
        findings.append({"code": "office.reference.package_reader_version"})
    if documents[0]["blocks"] != documents[1]["blocks"]:
        findings.append({"code": "office.reference.package_content"})
    blockers = list(source_coverage["blockers"])
    return {
        "schema_version": "template-native-office-package-reference-v1",
        "reference_ast_sha256": hashlib.sha256(reference_ast).hexdigest(),
        "candidate_ast_sha256": hashlib.sha256(candidate_ast).hexdigest(),
        "source_ast_sha256": source_coverage["source_ast_sha256"],
        "status": "failed" if findings else "blocked" if blockers else "observed",
        "findings": findings,
        "blockers": blockers,
    }
