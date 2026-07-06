"""Single-source-of-truth stage-table generation.

The canonical pipeline definition lives in
``infrastructure/core/pipeline/pipeline.yaml``. Several Markdown files
(``README.md``, ``.github/README.md``, ``scripts/AGENTS.md``,
``docs/RUN_GUIDE.md``, ``docs/core/workflow.md``) used to hand-maintain a
copy of the same stage table. This module renders that table from the
YAML and injects it between
``<!-- BEGIN:STAGE_TABLE -->`` / ``<!-- END:STAGE_TABLE -->`` markers,
reusing :func:`infrastructure.documentation.glossary_gen.inject_between_markers`.

The two public entry points are:

* :func:`build_stage_table` — render a Markdown table from the YAML.
* :func:`inject_stage_table` — replace the marked block in a Markdown file.

The generator is **idempotent**: running it twice with no YAML change makes
no diff. The "Stage" column reflects the 0-based position of each stage in
the YAML; this index intentionally does **not** match the ``NN_*.py`` numeric
prefixes used by the script filenames (e.g. stage 6 runs ``05_copy_outputs.py``).
The caption notes this caveat explicitly so historical pitfalls are not
re-introduced.
"""

from pathlib import Path

import yaml

from infrastructure.core.logging.utils import get_logger
from infrastructure.documentation.glossary_gen import inject_between_markers

logger = get_logger(__name__)


#: Canonical set of Markdown files that embed the stage table.
DEFAULT_STAGE_TABLE_TARGETS = (
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    ".github/README.md",
    "scripts/AGENTS.md",
    "docs/RUN_GUIDE.md",
    "docs/core/workflow.md",
)


_DEFAULT_FAILURE_MODES: dict[str, str] = {
    "core": "hard fail",
    "llm": "skipped if Ollama absent",
    "clean": "soft fail",
    "tests": "configurable tolerance",
}


_PIPELINE_YAML_REL = "infrastructure/core/pipeline/pipeline.yaml"


def _stage_table_caption(yaml_link: str) -> str:
    """Return the standard caption line, embedding *yaml_link* as the YAML href."""
    return (
        "<!-- This block is generated from "
        f"[`{_PIPELINE_YAML_REL}`]({yaml_link}) "
        "by `scripts/docgen/stage_table.py`. Do not hand-edit. "
        "Stage indices are **0-based positions in the YAML** and intentionally do "
        "**not** match the `scripts/NN_*.py` numeric prefixes "
        "(for example, stage 9 runs `05_copy_outputs.py`). -->"
    )


# Default caption used when no relative path is supplied. Kept for backwards
# compatibility with callers that pre-date the per-target relative resolver.
_STAGE_TABLE_CAPTION = _stage_table_caption(f"../{_PIPELINE_YAML_REL}")


def _default_failure_mode(tags: list[str]) -> str:
    """Pick a sensible default failure-mode label from a stage's tags."""
    for tag in ("clean", "llm", "tests", "core"):
        if tag in tags:
            return _DEFAULT_FAILURE_MODES[tag]
    return "—"


def _render_script_cell(stage: dict[str, object]) -> str:
    """Render the "Script" column for a single stage entry."""
    script = stage.get("script")
    method = stage.get("method")
    args = stage.get("args") or []
    if isinstance(script, str) and script:
        if isinstance(args, list) and args:
            return f"`{script} {' '.join(str(a) for a in args)}`"
        return f"`{script}`"
    if isinstance(method, str) and method:
        return f"built-in `{method}`"
    return "—"


def _render_tags_cell(tags: list[str]) -> str:
    if not tags:
        return "—"
    return ", ".join(f"`{t}`" for t in tags)


def build_stage_table(
    yaml_path: Path,
    *,
    target_rel_to_repo: Path | None = None,
    repo_root: Path | None = None,
) -> str:
    """Render a Markdown stage table from ``pipeline.yaml``.

    The returned string is a fenced HTML caption followed by a four-column
    Markdown table: ``Stage | Script | Tags | Failure mode``. Stage indices
    are 0-based positions in the YAML (so ``Clean Output Directories`` is
    stage 0 and the nine numbered stages follow as 1–9).

    Args:
        yaml_path: Path to ``pipeline.yaml``.
        target_rel_to_repo: Optional Markdown target path (relative to the
            repo root). Used to compute a correct relative URL for the
            ``pipeline.yaml`` link in the caption. When ``None``, the caption
            uses the legacy ``../infrastructure/...`` form.
        repo_root: Optional repo-root path, only used when *target_rel_to_repo*
            is provided.

    Returns:
        The rendered Markdown block (no surrounding marker comments).

    Raises:
        FileNotFoundError: If ``yaml_path`` does not exist.
        ValueError: If the YAML lacks a top-level ``stages`` list.
    """
    if not yaml_path.exists():
        raise FileNotFoundError(f"pipeline.yaml not found: {yaml_path}")

    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "stages" not in raw:
        raise ValueError(f"pipeline.yaml must have a top-level 'stages' list: {yaml_path}")

    stages = raw["stages"]
    if not isinstance(stages, list):
        raise ValueError(f"pipeline.yaml 'stages' must be a list: {yaml_path}")

    if target_rel_to_repo is not None:
        # Compute a correct relative URL from the target back to pipeline.yaml.
        depth = len(Path(target_rel_to_repo).parts) - 1  # parts above the file
        prefix = "../" * depth if depth > 0 else ""
        caption = _stage_table_caption(f"{prefix}{_PIPELINE_YAML_REL}")
    else:
        caption = _STAGE_TABLE_CAPTION

    lines: list[str] = [
        caption,
        "",
        "| Stage | Script | Tags | Failure mode |",
        "| ----- | ------ | ---- | ------------ |",
    ]

    for index, entry in enumerate(stages):
        if not isinstance(entry, dict):
            raise ValueError(f"pipeline.yaml stage at index {index} is not a mapping")
        name = str(entry.get("name", ""))
        tags_raw = entry.get("tags", []) or []
        tags = [str(t) for t in tags_raw] if isinstance(tags_raw, list) else []
        failure_mode = entry.get("failure_mode")
        if not isinstance(failure_mode, str) or not failure_mode.strip():
            failure_mode = _default_failure_mode(tags)
        lines.append(
            f"| **{index}** {name} | {_render_script_cell(entry)} | {_render_tags_cell(tags)} | {failure_mode} |"
        )

    return "\n".join(lines)


def inject_stage_table(
    markdown_path: Path,
    table: str,
    marker: str = "STAGE_TABLE",
) -> bool:
    """Replace the stage-table block inside ``markdown_path``.

    Looks for ``<!-- BEGIN:{marker} -->`` and ``<!-- END:{marker} -->`` and
    replaces the content between them with ``table``. If the markers are not
    found, a new block is appended (matching the behaviour of
    :func:`infrastructure.documentation.glossary_gen.inject_between_markers`).

    The write is idempotent: if the rendered content matches what is already
    in the file, no write is performed.

    Args:
        markdown_path: Markdown file to mutate.
        table: Markdown block to inject (no marker comments).
        marker: Marker label used in ``<!-- BEGIN:{marker} -->`` /
            ``<!-- END:{marker} -->``. Defaults to ``"STAGE_TABLE"``.

    Returns:
        ``True`` if the file was changed on disk, ``False`` otherwise.
    """
    if not markdown_path.exists():
        raise FileNotFoundError(f"Markdown target not found: {markdown_path}")

    begin = f"<!-- BEGIN:{marker} -->"
    end = f"<!-- END:{marker} -->"

    text = markdown_path.read_text(encoding="utf-8")
    new_text = inject_between_markers(text, begin, end, table)

    if new_text == text:
        logger.debug(f"Stage table up-to-date: {markdown_path}")
        return False

    _tmp = markdown_path.with_suffix(markdown_path.suffix + ".tmp")
    try:
        _tmp.write_text(new_text, encoding="utf-8")
        _tmp.replace(markdown_path)
    except OSError:
        _tmp.unlink(missing_ok=True)
        raise

    logger.info(f"Updated stage table in {markdown_path}")
    return True


__all__ = ["DEFAULT_STAGE_TABLE_TARGETS", "build_stage_table", "inject_stage_table"]
