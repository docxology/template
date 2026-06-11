"""Project context packing for deep research jobs."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable

from infrastructure.search.deep_research.models import DeepResearchRequest
from infrastructure.validation.content.pdf_validator import PDFValidationError, extract_text_from_pdf

TEXT_EXTENSIONS = {".md", ".markdown", ".txt", ".json", ".yaml", ".yml", ".toml", ".csv", ".log", ".bib"}
DEFAULT_CONTEXT_FILES = ("README.md", "AGENTS.md", "manuscript/config.yaml", "manuscript/config.yml")
# "manuscript" first: paper sources are the canonical contents to dispatch and
# must be packaged even when the project has never been rendered (fresh clone).
DEFAULT_CONTEXT_DIRS = ("manuscript", "output/manuscript", "output/pdf", "output/reports", "output/data", "docs")


@dataclass(frozen=True)
class DeepResearchProjectContext:
    """Packed project context suitable for provider prompts."""

    project_root: Path
    project_name: str
    artifact_paths: tuple[Path, ...]
    context_text: str


def collect_project_context(
    project_root: str | Path,
    *,
    max_files: int = 64,
    max_chars_per_file: int = 8000,
    max_total_chars: int = 500000,
) -> DeepResearchProjectContext:
    """Collect a bounded context bundle from a project tree."""
    root = Path(project_root).expanduser().resolve()
    artifacts = _select_artifacts(root, max_files=max_files)
    context_text = _render_context(
        root,
        artifacts,
        max_chars_per_file=max_chars_per_file,
        max_total_chars=max_total_chars,
    )
    return DeepResearchProjectContext(
        project_root=root,
        project_name=root.name,
        artifact_paths=tuple(artifacts),
        context_text=context_text,
    )


def build_project_deep_research_request(
    project_root: str | Path,
    query: str,
    *,
    request: DeepResearchRequest | None = None,
    max_files: int = 64,
    max_chars_per_file: int = 8000,
    max_total_chars: int = 500000,
) -> DeepResearchRequest:
    """Create a deep research request preloaded with project context."""
    project_context = collect_project_context(
        project_root,
        max_files=max_files,
        max_chars_per_file=max_chars_per_file,
        max_total_chars=max_total_chars,
    )
    base = request or DeepResearchRequest(query=query)
    instructions = _combine_instructions(project_context.context_text, base.instructions)
    return replace(base, query=query, instructions=instructions)


def _select_artifacts(root: Path, *, max_files: int) -> list[Path]:
    artifacts: list[Path] = []
    seen: set[Path] = set()

    def add(path: Path) -> None:
        if len(artifacts) >= max_files:
            return
        if not path.is_file():
            return
        if (
            path.suffix.lower() not in TEXT_EXTENSIONS
            and path.suffix.lower() != ".pdf"
            and path.name
            not in {
                "README.md",
                "AGENTS.md",
            }
        ):
            return
        resolved = path.resolve()
        if resolved in seen:
            return
        seen.add(resolved)
        artifacts.append(resolved)

    for relative in DEFAULT_CONTEXT_FILES:
        add(root / relative)

    for relative_dir in DEFAULT_CONTEXT_DIRS:
        directory = root / relative_dir
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*")):
            if len(artifacts) >= max_files:
                break
            add(path)

    return artifacts


def _render_context(root: Path, artifacts: Iterable[Path], *, max_chars_per_file: int, max_total_chars: int) -> str:
    lines: list[str] = [
        "Project context bundle for deep research.",
        f"- Project root: {root}",
        f"- Project name: {root.name}",
        "",
        "Included artifacts:",
    ]

    rendered_chars = len("\n".join(lines))
    for path in artifacts:
        rel = path.relative_to(root)
        body = _read_artifact_text(path, max_chars=max_chars_per_file)
        block = "\n".join(
            [
                "",
                f"## Artifact: {rel}",
                "```text",
                body,
                "```",
            ]
        )
        if rendered_chars + len(block) > max_total_chars:
            break
        lines.append(f"- {rel}")
        lines.append(block)
        rendered_chars += len(block)

    if len(lines) == 5:
        lines.append("- No text artifacts found.")
    return "\n".join(lines)


def _read_text(path: Path, *, max_chars: int) -> str:
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 80].rstrip() + "\n\n[truncated for prompt budget]"


def _read_artifact_text(path: Path, *, max_chars: int) -> str:
    if path.suffix.lower() == ".pdf":
        try:
            text = extract_text_from_pdf(path).strip()
        except PDFValidationError as exc:
            return f"[PDF extraction unavailable for {path.name}: {exc}]"
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 80].rstrip() + "\n\n[truncated for prompt budget]"
    return _read_text(path, max_chars=max_chars)


def _combine_instructions(project_context: str, existing: str | None) -> str:
    if not existing:
        return project_context
    return f"{existing.rstrip()}\n\n{project_context}"


__all__ = [
    "DEFAULT_CONTEXT_DIRS",
    "DEFAULT_CONTEXT_FILES",
    "DeepResearchProjectContext",
    "build_project_deep_research_request",
    "collect_project_context",
]
