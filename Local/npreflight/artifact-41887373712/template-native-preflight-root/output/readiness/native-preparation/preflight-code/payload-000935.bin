"""Bounded archive Pandoc preparation and source-bound panel selection."""

from __future__ import annotations

import json
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.files.secure_write import atomic_write_text_confined
from infrastructure.rendering._slides_accessibility_limits import (
    read_bounded_pandoc_json,
    validate_accessible_ast_limits,
)
from infrastructure.rendering._slides_presentation_variants import (
    expand_presentation_variants,
    relocate_presentation_panels,
)
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.security import subprocess_options


def prepare_archive_source(
    config: RenderingConfig,
    source_file: Path,
    output_dir: Path,
    *,
    manuscript_dir: Path | None,
    figures_dir: Path | None,
    process_runner: Callable[..., object] = subprocess.run,
) -> tuple[Path, tuple[Path, ...]]:
    """Keep one conceptual Figure while selecting its source-bound panels."""
    profile = config.security()
    with tempfile.NamedTemporaryFile(
        prefix=f".{source_file.stem}-",
        suffix=".archive.json",
        dir=output_dir,
        delete=False,
    ) as handle:
        selected = Path(handle.name)
    completed = False
    try:
        profile.validate_output(selected)
        process_runner(
            [config.pandoc_path, str(source_file), "-t", "json", "-o", str(selected)],
            check=True,
            capture_output=True,
            text=True,
            **subprocess_options(profile, 600),
        )
        document = json.loads(read_bounded_pandoc_json(selected, source=str(source_file)))
        if not isinstance(document, dict) or not isinstance(document.get("blocks"), list):
            raise RenderingError("Archive source is not a Pandoc document")
        validate_accessible_ast_limits(document, source=str(source_file))
        roots = tuple(path for path in (source_file.parent, manuscript_dir, figures_dir) if path is not None)
        document = expand_presentation_variants(
            document,
            source=str(source_file),
            roots=roots,
            figure_root=figures_dir,
            preserve_figure_group=True,
        )
        relocate_presentation_panels(
            document,
            output_dir=output_dir,
            source=str(source_file),
            roots=roots,
            figure_root=figures_dir,
        )
        validate_accessible_ast_limits(document, source=str(source_file))
        atomic_write_text_confined(output_dir, selected, json.dumps(document, ensure_ascii=False) + "\n")
        completed = True
        return selected, (selected,)
    finally:
        if not completed:
            selected.unlink(missing_ok=True)
