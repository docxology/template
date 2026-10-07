"""Fresh source-only canonical PDF TeX projection, before native compilation."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import time
from pathlib import Path
from typing import Any

import yaml

from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
from infrastructure.reporting.native_format_acceptance_checks import NativeToolUnavailable, native_tool_record
from infrastructure.reporting.native_format_pdf_source import PDFSourceInputs
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def observe_pdf_source_projection(
    root: Path,
    directory: Path,
    inputs: PDFSourceInputs,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> dict[str, Any]:
    """Project current admitted sources through their actual declared writer.

    This is a source projection receipt, not a document acceptance result.
    Figures and domain editions remain explicit obligations of the caller.
    """
    from infrastructure.rendering._pdf_combined_bibliography import inject_bibliography
    from infrastructure.rendering._pdf_combined_latex import fix_starred_section_nameref_labels, postprocess_latex
    from infrastructure.rendering._pdf_combined_pandoc import build_pandoc_tex_command
    from infrastructure.rendering._pdf_combined_preamble import inject_latex_preamble
    from infrastructure.rendering._pdf_title_page_config import _rendering_options
    from infrastructure.rendering.config import RenderingConfig
    from infrastructure.transmission.transmission_bookends import transmission_bookends_enabled

    started = time.monotonic()
    if not 0 < deadline - started <= 3600:
        raise ValueError("source PDF projection requires an original finite budget")
    if len(inputs.content) > 4 * 1024 * 1024:
        raise ValueError("source PDF projection exceeds its Markdown budget")
    source_dir = directory / "source"
    snapshots = []
    names: set[str] = set()
    for original, content in (inputs.config, *((inputs.preamble,) if inputs.preamble else ()), *inputs.bibliographies):
        name = Path(original).name
        if name in names:
            raise ValueError("source PDF projection has ambiguous frozen basenames")
        names.add(name)
        target = source_dir / name
        atomic_write_bytes_confined(root, target, content, mode=0o600)
        snapshots.append((target, content))
    if Path(inputs.config[0]).name != "config.yaml":
        raise ValueError("source projection requires the actual declared config.yaml")
    source = source_dir / "source-only.md"
    atomic_write_bytes_confined(root, source, inputs.content, mode=0o600)
    snapshots.append((source, inputs.content))
    config = yaml.safe_load(inputs.config[1])
    if not isinstance(config, dict):
        raise ValueError("source PDF projection config is not a mapping")
    crossref = shutil.which("pandoc-crossref", path=env.get("PATH"))
    if crossref is None:
        raise NativeToolUnavailable("the actual source cross-reference filter is unavailable")
    crossref_path = Path(crossref).resolve(strict=True)
    crossref_bytes = read_bytes_confined(crossref_path.parent, crossref_path, max_bytes=512 * 1024 * 1024)
    version = native_tool_record(
        root,
        directory,
        "pandoc-crossref",
        ["--version"],
        env=env,
        deadline=deadline,
        run_id=run_id,
        purpose="source-crossref-version",
    )
    rendering = RenderingConfig(figures_dir=str(directory / "figures"))
    tex = directory / "source-only.tex"
    command = build_pandoc_tex_command(rendering, source, tex, source_dir)
    filter_bindings = []
    for index, argument in enumerate(command[:-1]):
        if argument == "--lua-filter":
            original = Path(command[index + 1]).resolve(strict=True)
            content = read_bytes_confined(original.parent, original, max_bytes=4 * 1024 * 1024)
            target = directory / "filters" / original.name
            atomic_write_bytes_confined(root, target, content, mode=0o600)
            snapshots.append((target, content))
            command[index + 1] = str(target)
            filter_bindings.append(
                {
                    "original_path": str(original),
                    "path": target.relative_to(root).as_posix(),
                    "sha256": hashlib.sha256(content).hexdigest(),
                }
            )
    if len(filter_bindings) != 1:
        raise ValueError("source projection omitted its frozen formalism filter")
    # The source builder resolves the same named filter. Bind that consumed
    # executable to the explicitly observed version/runtime before execution.
    for index, argument in enumerate(command[:-1]):
        if argument == "--filter":
            if Path(command[index + 1]).resolve(strict=True) != crossref_path:
                raise ValueError("source cross-reference executable differs from its declared observation")
    process = native_tool_record(
        root,
        directory,
        "pandoc",
        command[1:],
        env=env,
        deadline=deadline,
        run_id=run_id,
        purpose="source-only-pdf-projection",
    )
    receipt = json.loads(SnapshotReader(root).read(process["artifact"]["path"]).content)
    version_receipt = json.loads(SnapshotReader(root).read(version["artifact"]["path"]).content)
    if any(row["original_exit_code"] != 0 or row["exit_code"] != 0 for row in (receipt, version_receipt)):
        raise ValueError("actual source writer or cross-reference version failed")
    text = SnapshotReader(root).read(tex.relative_to(root).as_posix()).content.decode()
    options = _rendering_options(config)
    metadata = config.get("metadata", {})
    text = postprocess_latex(
        text,
        language=str(metadata.get("language", "en")),
        figure_height_fraction=options["figure_height_fraction"],
        front_matter_figure_height_fraction=options["front_matter_figure_height_fraction"],
    )
    bookends = transmission_bookends_enabled(source_dir / "config.yaml")
    text = inject_latex_preamble(text, source_dir, skip_title_page=bookends)
    text = inject_bibliography(
        text,
        bool(inputs.bibliographies),
        ",".join(Path(path).stem for path, _ in inputs.bibliographies),
        before_end_transmission=bookends,
    )
    text, _ = fix_starred_section_nameref_labels(text)
    projected = directory / "source-reference.tex"
    atomic_write_bytes_confined(root, projected, text.encode(), mode=0o600)
    blockers = list(inputs.blockers)
    if re.search(r"\\includegraphics\b", text):
        blockers.append("source figures require independently bound assets and native figure/domain observations")
    # The source-owned postprocessor emits one deterministic PDF trailer-ID
    # special. Admit only that exact generated form; other specials retain the
    # dynamic-scope blocker and never disappear from the source ledger.
    scope_text = re.sub(r"(?m)^\\special\{pdf:trailerid \[ <([0-9a-f]{32})> <\1> \]\}\s*$", "", text)
    if re.search(r"\\(?:input|include|openin|openout|read|write|catcode|special)\b", scope_text):
        blockers.append("source TeX external or dynamic scope requires explicit consumed-input admission")
    if any(path.read_bytes() != content for path, content in snapshots):
        raise ValueError("frozen source projection inputs changed during execution")
    crossref_after = read_bytes_confined(crossref_path.parent, crossref_path, max_bytes=512 * 1024 * 1024)
    if crossref_after != crossref_bytes:
        raise ValueError("actual source cross-reference executable changed during execution")
    if time.monotonic() >= deadline:
        raise TimeoutError("source PDF projection exhausted its original budget")
    return {
        "schema_version": "template-native-source-pdf-projection-v1",
        "source_tex": {
            "path": projected.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
        },
        "markdown": {"path": source.relative_to(root).as_posix(), "sha256": hashlib.sha256(inputs.content).hexdigest()},
        "source_inputs": [
            {"path": path, "sha256": hashlib.sha256(content).hexdigest()}
            for path, content in (
                *inputs.sources,
                inputs.config,
                *((inputs.preamble,) if inputs.preamble else ()),
                *inputs.bibliographies,
            )
        ],
        "filters": filter_bindings,
        "crossref": {
            "original_path": str(crossref_path),
            "sha256": hashlib.sha256(crossref_bytes).hexdigest(),
            "size_bytes": len(crossref_bytes),
            "observation_before": {
                "sha256": hashlib.sha256(crossref_bytes).hexdigest(),
                "size_bytes": len(crossref_bytes),
            },
            "observation_after": {
                "sha256": hashlib.sha256(crossref_after).hexdigest(),
                "size_bytes": len(crossref_after),
            },
            "retention_policy": "original process/tool byte metadata under enclosing source/SDK custody; executable bytes are not redistributed",
        },
        "tool_artifacts": [version["artifact"], process["artifact"]],
        "execution_budget_seconds": deadline - started,
        "elapsed_seconds": time.monotonic() - started,
        "blockers": blockers,
        "status": "blocked" if blockers else "projected",
    }
