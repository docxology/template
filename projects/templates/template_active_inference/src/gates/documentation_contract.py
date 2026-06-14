"""Fail-closed documentation contract checks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

SKIP_PARTS = {
    ".git",
    ".lake",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
}
PAIR_SKIP_PARTS = {*SKIP_PARTS, "output"}
DOC_EXTENSIONS = {".md", ".yaml", ".yml"}
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
REFERENCE_DEFINITION_RE = re.compile(r"(?m)^[ \t]{0,3}\[([^\]\n]+)\]:[ \t]*(\S.*)$")
REFERENCE_USAGE_RE = re.compile(r"(?<!!)\[([^\]\n]+)\]\[([^\]\n]*)\]")
HEADING_RE = re.compile(r"(?m)^(#{1,6})\s+(.+?)\s*$")
EXPLICIT_ANCHOR_RE = re.compile(r"\{#([A-Za-z0-9_.:-]+)\}")
CURRENT_EVIDENCE_RE = re.compile(
    r"uv run pytest tests/ --cov=src --cov-fail-under=90`\s+passed \d+ tests with\s+\d+(?:\.\d+)?% coverage",
    re.MULTILINE,
)
LEGACY_EVIDENCE_RE = re.compile(r"(153-test|92\.03%|348 tests|364 tests|90\.70%)")
FORBIDDEN_COMMAND_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "root-directory-uv-run",
        re.compile(r"\buv\s+run\s+--directory\s+projects/templates/template_active_inference\b"),
    ),
    (
        "root-path-pytest",
        re.compile(r"\b(?:uv\s+run\s+pytest|python\s+-m\s+pytest)\s+projects/templates/template_active_inference"),
    ),
)
REQUIRED_REFERENCE_PHRASES = (
    "single hydration boundary",
    "Generated artifacts",
    "Authored surfaces",
    "Root output parity",
    "Figure rendering contract",
)
REQUIRED_SIGNPOSTS: dict[str, tuple[str, ...]] = {
    "README.md": (
        "scripts/check_documentation_contract.py --check",
        "scripts/generate_method_inventory.py --check",
        "scripts/validate_outputs.py",
    ),
    "docs/README.md": (
        "scripts/check_documentation_contract.py --check",
        "scripts/generate_method_inventory.py --check",
        "scripts/validate_outputs.py",
    ),
    "docs/reference/README.md": (
        "scripts/check_documentation_contract.py --check",
        "scripts/generate_method_inventory.py --check",
        "scripts/validate_outputs.py",
    ),
    "docs/reference/AGENTS.md": (
        "scripts/check_documentation_contract.py --check",
        "scripts/generate_method_inventory.py --check",
        "scripts/validate_outputs.py",
    ),
}


@dataclass(frozen=True)
class DocumentationIssue:
    """A documentation contract violation with a stable diagnostic code."""

    code: str
    path: str
    message: str
    target: str = ""

    def format(self) -> str:
        """Return a compact CLI-friendly issue string."""
        suffix = f" -> {self.target}" if self.target else ""
        return f"{self.code}: {self.path}: {self.message}{suffix}"


def _has_skip_part(path: Path, root: Path, skip_parts: set[str]) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        parts = path.parts
    return any(part in skip_parts for part in parts)


def _iter_files(project_root: Path, *, extensions: set[str], skip_parts: set[str]) -> list[Path]:
    root = Path(project_root).resolve()
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix in extensions and not _has_skip_part(path, root, skip_parts)
    )


def _read_text_if_present(path: Path) -> str | None:
    """Read text while tolerating concurrent generated-output refreshes."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _trim_link_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<"):
        close_index = target.find(">")
        target = target[1:close_index] if close_index >= 0 else target[1:]
    else:
        target = target.split()[0]
    return unquote(target)


def _split_link_target(raw_target: str) -> tuple[str, str]:
    target = _trim_link_target(raw_target)
    if "#" not in target:
        return target, ""
    path, fragment = target.split("#", 1)
    return path, fragment


def _heading_anchor(heading: str) -> str:
    heading = re.sub(r"`([^`]*)`", r"\1", heading)
    heading = re.sub(r"\{#[A-Za-z0-9_.:-]+\}\s*$", "", heading)
    heading = re.sub(r"<[^>]+>", "", heading)
    heading = heading.strip().strip("#").strip().lower()
    heading = re.sub(r"[^a-z0-9 _.-]+", "", heading)
    return re.sub(r"[\s]+", "-", heading).strip("-")


def _markdown_anchors(path: Path) -> set[str]:
    if path.suffix.lower() not in {".md", ".markdown"} or not path.is_file():
        return set()
    text = _read_text_if_present(path)
    if text is None:
        return set()
    anchors = set(EXPLICIT_ANCHOR_RE.findall(text))
    for match in HEADING_RE.finditer(text):
        heading = match.group(2).strip()
        if heading.endswith("#"):
            heading = heading.rstrip("#").strip()
        anchor = _heading_anchor(heading)
        if anchor:
            anchors.add(anchor)
    return anchors


def _reference_label(label: str) -> str:
    return re.sub(r"\s+", " ", label.strip()).casefold()


def _reference_definitions(text: str) -> set[str]:
    return {_reference_label(match.group(1)) for match in REFERENCE_DEFINITION_RE.finditer(text)}


def _iter_markdown_targets(text: str) -> list[tuple[int, str]]:
    """Return inline and reference-style Markdown link targets."""
    targets = [(match.start(), match.group(1)) for match in MARKDOWN_LINK_RE.finditer(text)]
    targets.extend((match.start(2), match.group(2)) for match in REFERENCE_DEFINITION_RE.finditer(text))
    return sorted(targets)


def check_markdown_links(project_root: Path) -> list[DocumentationIssue]:
    """Validate relative Markdown links, including generated Markdown outputs."""
    root = Path(project_root).resolve()
    issues: list[DocumentationIssue] = []
    for path in _iter_files(root, extensions={".md"}, skip_parts=SKIP_PARTS):
        text = _read_text_if_present(path)
        if text is None:
            continue
        definitions = _reference_definitions(text)
        for match in REFERENCE_USAGE_RE.finditer(text):
            label = match.group(2) or match.group(1)
            if _reference_label(label) not in definitions:
                issues.append(
                    DocumentationIssue(
                        code="markdown-reference-missing",
                        path=f"{path.relative_to(root).as_posix()}:{_line_number(text, match.start())}",
                        message="reference-style Markdown link definition is missing",
                        target=match.group(0),
                    )
                )
        for offset, raw_target in _iter_markdown_targets(text):
            target, fragment = _split_link_target(raw_target)
            if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target):
                if fragment and not target:
                    anchors = _markdown_anchors(path)
                    if fragment not in anchors:
                        issues.append(
                            DocumentationIssue(
                                code="markdown-anchor-missing",
                                path=f"{path.relative_to(root).as_posix()}:{_line_number(text, offset)}",
                                message="relative Markdown anchor target is missing",
                                target=raw_target,
                            )
                        )
                continue
            candidate = (path.parent / target).resolve()
            if not candidate.exists():
                issues.append(
                    DocumentationIssue(
                        code="markdown-link-missing",
                        path=f"{path.relative_to(root).as_posix()}:{_line_number(text, offset)}",
                        message="relative Markdown link target is missing",
                        target=raw_target,
                    )
                )
            elif fragment and candidate.suffix.lower() in {".md", ".markdown"}:
                anchors = _markdown_anchors(candidate)
                if fragment not in anchors:
                    issues.append(
                        DocumentationIssue(
                            code="markdown-anchor-missing",
                            path=f"{path.relative_to(root).as_posix()}:{_line_number(text, offset)}",
                            message="relative Markdown anchor target is missing",
                            target=raw_target,
                        )
                    )
    return issues


def check_hydrated_output_links(project_root: Path) -> list[DocumentationIssue]:
    """Hydrated manuscript copies must link relative to output/manuscript/."""
    root = Path(project_root).resolve()
    resolved_dir = root / "output" / "manuscript"
    issues: list[DocumentationIssue] = []
    if not resolved_dir.is_dir():
        return issues
    for path in sorted(resolved_dir.glob("*.md")):
        text = _read_text_if_present(path)
        if text is None:
            continue
        for pattern in ("](../output/", "](<../output/"):
            index = text.find(pattern)
            if index >= 0:
                issues.append(
                    DocumentationIssue(
                        code="hydrated-output-link",
                        path=f"{path.relative_to(root).as_posix()}:{_line_number(text, index)}",
                        message="hydrated manuscript should link to sibling output assets without ../output/",
                    )
                )
    return issues


def check_readme_agents_pairs(project_root: Path) -> list[DocumentationIssue]:
    """Require README.md and AGENTS.md to appear as a pair in source docs."""
    root = Path(project_root).resolve()
    issues: list[DocumentationIssue] = []
    for directory in sorted(path for path in root.rglob("*") if path.is_dir()):
        if _has_skip_part(directory, root, PAIR_SKIP_PARTS):
            continue
        has_readme = (directory / "README.md").is_file()
        has_agents = (directory / "AGENTS.md").is_file()
        if has_readme != has_agents:
            missing = "README.md" if not has_readme else "AGENTS.md"
            issues.append(
                DocumentationIssue(
                    code="readme-agents-pair",
                    path=directory.relative_to(root).as_posix() or ".",
                    message=f"missing paired {missing}",
                )
            )
    return issues


def check_project_local_commands(project_root: Path) -> list[DocumentationIssue]:
    """Reject stale root-shaped commands in project-local documentation."""
    root = Path(project_root).resolve()
    issues: list[DocumentationIssue] = []
    for path in _iter_files(root, extensions=DOC_EXTENSIONS, skip_parts={*SKIP_PARTS, "output"}):
        text = _read_text_if_present(path)
        if text is None:
            continue
        for code, pattern in FORBIDDEN_COMMAND_PATTERNS:
            for match in pattern.finditer(text):
                issues.append(
                    DocumentationIssue(
                        code=code,
                        path=f"{path.relative_to(root).as_posix()}:{_line_number(text, match.start())}",
                        message="use project-local command wording or label the command as template-root only",
                        target=match.group(0),
                    )
                )
    return issues


def _paragraphs(text: str) -> list[str]:
    return [paragraph.strip() for paragraph in re.split(r"\n\s*\n", text) if paragraph.strip()]


def check_historical_test_evidence(project_root: Path) -> list[DocumentationIssue]:
    """Keep stale suite-count evidence clearly archived and current evidence singular."""
    root = Path(project_root).resolve()
    issues: list[DocumentationIssue] = []
    current_evidence: list[str] = []
    stale_full_suite_evidence: list[str] = []
    unlabeled_full_suite_evidence = False
    for path in _iter_files(root, extensions={".md"}, skip_parts={*SKIP_PARTS, "output"}):
        text = _read_text_if_present(path)
        if text is None:
            continue
        rel = path.relative_to(root).as_posix()
        for match in CURRENT_EVIDENCE_RE.finditer(text):
            paragraph = next(
                (
                    paragraph
                    for paragraph in _paragraphs(text)
                    if match.group(0) in paragraph or match.group(0).replace("\n", " ") in paragraph.replace("\n", " ")
                ),
                "",
            )
            lower = paragraph.lower()
            location = f"{rel}:{_line_number(text, match.start())}"
            if "historical" in lower and "stale" in lower:
                stale_full_suite_evidence.append(location)
            elif "historical" in lower or "before later" in lower or "stale" in lower:
                unlabeled_full_suite_evidence = True
                issues.append(
                    DocumentationIssue(
                        code="historical-evidence-unlabeled",
                        path=location,
                        message="non-current full-suite evidence must be explicitly historical and stale",
                    )
                )
            else:
                current_evidence.append(location)
        for paragraph in _paragraphs(text):
            if not LEGACY_EVIDENCE_RE.search(paragraph):
                continue
            lower = paragraph.lower()
            if "historical" not in lower or not (
                "stale" in lower or "do not reuse" in lower or "must not be used" in lower
            ):
                issues.append(
                    DocumentationIssue(
                        code="historical-evidence-unlabeled",
                        path=rel,
                        message="legacy test-count evidence must be explicitly historical and stale",
                    )
                )
    if (
        not unlabeled_full_suite_evidence
        and len(current_evidence) != 1
        and not (len(current_evidence) == 0 and len(stale_full_suite_evidence) == 1)
    ):
        issues.append(
            DocumentationIssue(
                code="current-evidence-count",
                path=".",
                message=(
                    "expected exactly one explicit current full-suite evidence line, or one explicitly "
                    f"historical stale full-suite evidence line while recertification is open; found "
                    f"{len(current_evidence)} current and {len(stale_full_suite_evidence)} stale"
                ),
                target=", ".join([*current_evidence, *stale_full_suite_evidence]),
            )
        )
    return issues


def check_reference_signposts(project_root: Path) -> list[DocumentationIssue]:
    """Require canonical verification and reference signposts in reader docs."""
    root = Path(project_root).resolve()
    issues: list[DocumentationIssue] = []
    reference = root / "docs" / "reference" / "rendering-reproducibility.md"
    if not reference.is_file():
        issues.append(
            DocumentationIssue(
                code="reference-missing",
                path="docs/reference/rendering-reproducibility.md",
                message="rendering reproducibility reference is missing",
            )
        )
    else:
        text = _read_text_if_present(reference) or ""
        for phrase in REQUIRED_REFERENCE_PHRASES:
            if phrase not in text:
                issues.append(
                    DocumentationIssue(
                        code="reference-phrase-missing",
                        path="docs/reference/rendering-reproducibility.md",
                        message="required rendering-reproducibility phrase is missing",
                        target=phrase,
                    )
                )
    for rel_path, phrases in REQUIRED_SIGNPOSTS.items():
        path = root / rel_path
        if not path.is_file():
            issues.append(
                DocumentationIssue(
                    code="signpost-file-missing", path=rel_path, message="required signpost file is missing"
                )
            )
            continue
        signpost_text = _read_text_if_present(path)
        if signpost_text is None:
            continue
        for phrase in phrases:
            if phrase not in signpost_text:
                issues.append(
                    DocumentationIssue(
                        code="signpost-missing",
                        path=rel_path,
                        message="required verification signpost is missing",
                        target=phrase,
                    )
                )
    return issues


def check_documentation_contract(project_root: Path) -> list[DocumentationIssue]:
    """Run all documentation contract checks."""
    root = Path(project_root).resolve()
    issues: list[DocumentationIssue] = []
    for check in (
        check_markdown_links,
        check_hydrated_output_links,
        check_readme_agents_pairs,
        check_project_local_commands,
        check_historical_test_evidence,
        check_reference_signposts,
    ):
        issues.extend(check(root))
    return sorted(issues, key=lambda issue: (issue.code, issue.path, issue.target))
