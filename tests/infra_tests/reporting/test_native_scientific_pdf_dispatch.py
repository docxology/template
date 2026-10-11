"""Real source parsing/assets retain scientific PDF acceptance obligations."""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

import pytest

from infrastructure.reporting.native_format_pdf_semantic_plan import (
    compile_pdf_semantic_plan,
)
from infrastructure.reporting.native_format_pdf_source import PDFSourceInputs
from infrastructure.reporting.native_format_pdf_source_witness import (
    inspect_pdf_source_witness,
)
from infrastructure.reporting.native_format_scientific_pdf_observer import (
    ENCLOSING_BLOCKERS,
    compile_scientific_pdf_assets,
    replay_current_scientific_pdf_ast,
    require_scientific_pdf_source_context,
    scientific_pdf_source_observation,
    verify_scientific_pdf_reader_input,
)
from infrastructure.reporting.native_projection_contracts import (
    ProjectionSourceUnsupported,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

from .test_native_pdf_source_witness import SOURCE, native_pdf, parsed, source_asset

SCOPE = "templates/template_code_project"


def inputs(source: bytes) -> PDFSourceInputs:
    relative = f"projects/{SCOPE}/output/manuscript/source.md"
    return PDFSourceInputs(
        source,
        ((relative, source),),
        (f"projects/{SCOPE}/output/manuscript/config.yaml", b"{}"),
        None,
        (),
        (),
    )


def test_actual_scientific_source_asset_and_native_witness_stay_scoped(
    tmp_path: Path,
) -> None:
    original = inputs(SOURCE)
    plan = compile_pdf_semantic_plan("manuscript:pdf", original.sources, parsed(SOURCE))
    asset = tmp_path / "projects" / SCOPE / "output/figures/asset.png"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(source_asset())
    reader = SnapshotReader(tmp_path)
    deadline = time.monotonic() + 30
    assets = compile_scientific_pdf_assets(tmp_path, SCOPE, original, plan, reader, deadline=deadline)
    pdf, pixels = native_pdf(tmp_path / "native.pdf", "baseline")
    witness = inspect_pdf_source_witness(
        pdf,
        pixels,
        plan,
        assets={
            identity: (binding["path"], reader.read(binding["path"]).content) for identity, binding in assets.items()
        },
        deadline=deadline,
    )
    observation = scientific_pdf_source_observation(witness, original.blockers)
    assert not observation["findings"]
    assert observation["status"] == "blocked"
    assert all(blocker in observation["blockers"] for blocker in ENCLOSING_BLOCKERS)
    assert any("independently admitted source figure/caption positions" in item for item in observation["blockers"])


def test_source_repeated_images_keep_each_occurrence(tmp_path: Path) -> None:
    source = b"![First](asset.png)\n\n![Second](asset.png)\n"
    original = inputs(source)
    plan = compile_pdf_semantic_plan("manuscript:pdf", original.sources, parsed(source))
    asset = tmp_path / "projects" / SCOPE / "output/figures/asset.png"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(source_asset())
    bindings = compile_scientific_pdf_assets(
        tmp_path,
        SCOPE,
        original,
        plan,
        SnapshotReader(tmp_path),
        deadline=time.monotonic() + 10,
    )
    assert len(bindings) == 2
    assert len({binding["path"] for binding in bindings.values()}) == 1


@pytest.mark.parametrize(
    "target",
    ["https://example.invalid/asset.png", "../../../../../../asset.png", "absent.png"],
)
def test_original_source_asset_cannot_use_external_or_unadmitted_resource(tmp_path: Path, target: str) -> None:
    source = f"![Original]({target})\n".encode()
    original = inputs(source)
    plan = compile_pdf_semantic_plan("manuscript:pdf", original.sources, parsed(source))
    with pytest.raises(ProjectionSourceUnsupported):
        compile_scientific_pdf_assets(
            tmp_path,
            SCOPE,
            original,
            plan,
            SnapshotReader(tmp_path),
            deadline=time.monotonic() + 10,
        )


def test_scientific_source_requires_actual_immutable_source_context(
    tmp_path: Path,
) -> None:
    with pytest.raises(ProjectionSourceUnsupported, match="immutable source"):
        require_scientific_pdf_source_context(
            tmp_path,
            SnapshotReader(tmp_path),
            None,
            None,
            deadline=time.monotonic() + 10,
        )


@pytest.mark.parametrize("replace_identity", [False, True])
def test_reader_actual_source_corruption_and_substitution_are_refused(tmp_path: Path, replace_identity: bool) -> None:
    path = tmp_path / "output/readiness/original/source-only.md"
    path.parent.mkdir(parents=True)
    path.write_bytes(SOURCE)
    reader = SnapshotReader(tmp_path)
    original = reader.read(path.relative_to(tmp_path).as_posix())
    verify_scientific_pdf_reader_input(original, reader)
    if replace_identity:
        replacement = path.with_name("replacement.md")
        replacement.write_bytes(SOURCE)
        replacement.replace(path)
    else:
        path.write_bytes(b"Changed source value +3.26 mV.\n")
    with pytest.raises(ValueError, match="source input changed"):
        verify_scientific_pdf_reader_input(original, reader)


def test_actual_retained_parser_process_cannot_mint_current_source_authority(
    tmp_path: Path,
) -> None:
    from infrastructure.reporting.native_format_acceptance_checks import (
        native_tool_record,
    )
    from infrastructure.reporting.native_format_acceptance_validation import native_environment_for_replay

    if shutil.which("pandoc") is None:
        pytest.skip("actual Pandoc required for retained native-process refusal")
    directory = tmp_path / "output/readiness/retained-parser"
    directory.mkdir(parents=True)
    path = directory / "source-only.md"
    path.write_bytes(SOURCE)
    deadline = time.monotonic() + 30
    env = native_environment_for_replay(tmp_path)
    record = native_tool_record(
        tmp_path,
        directory,
        "pandoc",
        [str(path), "--to=json"],
        env=env,
        deadline=deadline,
        run_id="retained-data-only",
        purpose="retained-parser-without-source-admission",
    )
    data = SnapshotReader(tmp_path).read(record["artifact"]["path"]).json_object()
    assert data["original_exit_code"] == 0 and data["owner_pid"] == os.getpid()
    reader = SnapshotReader(tmp_path, native_operation=data)
    original = reader.read(path.relative_to(tmp_path).as_posix())
    with pytest.raises(ProjectionSourceUnsupported, match="externally admitted source"):
        replay_current_scientific_pdf_ast(
            tmp_path,
            original,
            reader,
            env=env,
            deadline=deadline,
        )
    assert not (tmp_path / "output/readiness/current-native-readers").exists()
