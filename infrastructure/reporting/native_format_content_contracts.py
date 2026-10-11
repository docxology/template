"""Bounded, explicit text obligations from the exact consumed manuscript bytes.

This is a deliberately narrow projection, not a Markdown renderer. Unknown
syntax remains blocked rather than silently removing scientific information.
"""

from __future__ import annotations

import hashlib
import math
import re
import time
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader
from infrastructure.rendering.manuscript_discovery import discover_manuscript_files
from infrastructure.validation.output.render_formats import render_config_manuscript_dir
from infrastructure.validation.publication.rendered_provenance import validate_current_rendered_provenance

CONTENT_SCHEMA = "template-native-source-content-v1"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_BLOCKS = 20_000
MAX_TOKENS = 250_000
TEXT_POLICY: dict[str, Any] = {
    "schema_version": CONTENT_SCHEMA,
    "normalization": "Unicode NFC, whitespace boundaries, explicit presentation ligatures",
    "ligatures": {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl"},
    "projection": "plain paragraphs, ATX headings and plain list items only",
    "max_source_bytes": MAX_SOURCE_BYTES,
    "max_blocks": MAX_BLOCKS,
    "max_tokens": MAX_TOKENS,
}


def text_tokens(text: str) -> tuple[str, ...]:
    """Keep every sign, punctuation mark, number and unit; never case-fold."""
    normalized = unicodedata.normalize("NFC", text)
    for ligature, expanded in TEXT_POLICY["ligatures"].items():
        normalized = normalized.replace(ligature, expanded)
    return tuple(re.findall(r"[^\W_]+|[^\w\s]|_", normalized, flags=re.UNICODE))


@dataclass(frozen=True)
class ContentBlock:
    """An occurrence, with an independent stable source/line identity."""

    id: str
    kind: str
    line: int
    tokens: tuple[str, ...]


@dataclass(frozen=True)
class NativeContentContract:
    """Immutable ordered supported obligations and explicit projection limits."""

    artifact_id: str
    sources: tuple[tuple[str, str], ...]
    blocks: tuple[ContentBlock, ...]
    blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": CONTENT_SCHEMA,
            "artifact_id": self.artifact_id,
            "policy_digest": canonical_digest(TEXT_POLICY),
            "sources": [{"path": path, "sha256": digest} for path, digest in self.sources],
            "blocks": [{**asdict(block), "tokens": list(block.tokens)} for block in self.blocks],
            "blockers": list(self.blockers),
        }

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())


def content_contract_from_bytes(artifact_id: str, sources: tuple[tuple[str, bytes], ...]) -> NativeContentContract:
    """Compile bounded invented or admitted bytes, preserving unsupported syntax."""
    if not artifact_id or not sources or len({path for path, _ in sources}) != len(sources):
        raise ValueError("native content needs unique nonempty ordered source identities")
    if sum(len(content) for _, content in sources) > MAX_SOURCE_BYTES:
        raise ValueError("native content exceeds its source-byte budget")
    blocks: list[ContentBlock] = []
    blockers: list[str] = []
    for path, content in sources:
        if Path(path).suffix != ".md":
            blockers.append(f"{path}: unsupported source projection")
            continue
        text = content.decode("utf-8")
        paragraph: list[str] = []
        start = 0
        fenced = False
        frontmatter = False

        def flush() -> None:
            if paragraph:
                blocks.append(ContentBlock(f"{path}:{start}", "body", start, text_tokens(" ".join(paragraph))))
                paragraph.clear()

        for line_number, raw in enumerate(text.splitlines(), 1):
            line = raw.strip()
            if line_number == 1 and line == "---":
                frontmatter = True
                blockers.append(f"{path}: metadata-frontmatter projection unsupported")
                continue
            if frontmatter:
                if line in {"---", "..."}:
                    frontmatter = False
                continue
            if line.startswith(("```", "~~~")):
                flush()
                fenced = not fenced
                blockers.append(f"{path}:{line_number}: code-fence projection unsupported")
                continue
            if fenced:
                continue
            if not line:
                flush()
                continue
            heading = re.match(r"^#{1,6}\s+(.+?)(?:\s+#+)?$", line)
            listing = re.match(r"^(?:[-+*]|[0-9]+[.)])\s+(.+)$", line)
            projected = heading.group(1) if heading else listing.group(1) if listing else line
            # These constructs require an actual syntax-aware scientific projection.
            if raw.startswith(("    ", "\t")) or re.search(r"[\\$`*_[\]{}<>|~]|(?:^|\s)@", projected):
                flush()
                blockers.append(f"{path}:{line_number}: markup/math/citation projection unsupported")
                continue
            if re.fullmatch(r"[-=]{3,}", projected):
                flush()
                blockers.append(f"{path}:{line_number}: structural projection unsupported")
                continue
            if heading or listing:
                flush()
                blocks.append(
                    ContentBlock(
                        f"{path}:{line_number}", "heading" if heading else "body", line_number, text_tokens(projected)
                    )
                )
            else:
                if not paragraph:
                    start = line_number
                paragraph.append(projected)
            if len(blocks) > MAX_BLOCKS:
                raise ValueError("native content exceeds its block budget")
        flush()
        if fenced:
            blockers.append(f"{path}: unclosed code fence")
        if frontmatter:
            blockers.append(f"{path}: unclosed metadata frontmatter")
    if not blocks:
        blockers.append("no supported source-text obligations collected")
    if len(blocks) > MAX_BLOCKS or sum(len(block.tokens) for block in blocks) > MAX_TOKENS:
        raise ValueError("native content exceeds its block/token budget")
    return NativeContentContract(
        artifact_id,
        tuple((path, hashlib.sha256(content).hexdigest()) for path, content in sources),
        tuple(blocks),
        tuple(blockers),
    )


def compile_pdf_content_contract(
    root: Path, scope: str, artifact: NativeArtifact, reader: SnapshotReader, *, deadline: float
) -> NativeContentContract:
    """Use current validated hydration and the renderer's actual source ordering."""
    if type(deadline) not in {int, float} or not math.isfinite(deadline) or time.monotonic() >= deadline:
        raise TimeoutError("native source-content admission deadline expired")
    if artifact.format != "pdf" or not validate_current_rendered_provenance(root, scope).valid:
        raise ValueError("PDF source obligations require current validated consumed hydration")
    reader.read(f"projects/{scope}/manuscript/config.yaml")
    manuscript = render_config_manuscript_dir(root / "projects" / scope)
    paths = discover_manuscript_files(manuscript)
    if artifact.id.startswith("section:") and artifact.id.endswith(":pdf"):
        name = artifact.id.removeprefix("section:").removesuffix(":pdf")
        paths = [path for path in paths if path.relative_to(manuscript).as_posix() == name]
        if len(paths) != 1:
            raise ValueError("section identity requires one exact source-relative manuscript")
    snapshots: tuple[ArtifactSnapshot, ...] = tuple(reader.read(path.relative_to(root).as_posix()) for path in paths)
    contract = content_contract_from_bytes(artifact.id, tuple((item.relative, item.content) for item in snapshots))
    if artifact.id != "manuscript:pdf" and not (artifact.id.startswith("section:") and artifact.id.endswith(":pdf")):
        # Decks, print editions and picture books do not consume full manuscript
        # prose as a literal ordered projection. Keep their native census only.
        contract = NativeContentContract(
            artifact.id, contract.sources, (), (f"{artifact.id}: domain/projection source binding unsupported",)
        )
    if (
        not reader.unchanged()
        or not validate_current_rendered_provenance(root, scope).valid
        or time.monotonic() >= deadline
    ):
        raise ValueError("native consumed source custody or admission budget changed")
    return contract


@dataclass(frozen=True)
class SemanticContentContract(NativeContentContract):
    """Syntax-aware source obligations, retaining mathematical occurrences."""

    ast_sha256: str = ""
    mathematical_sources: tuple[tuple[str, str], ...] = ()
    image_sources: tuple[tuple[str, str, str], ...] = ()
    link_sources: tuple[tuple[str, str], ...] = ()
    citation_sources: tuple[tuple[str, tuple[str, ...]], ...] = ()
    table_sources: tuple[dict[str, Any], ...] = ()
    footnote_sources: tuple[dict[str, Any], ...] = ()
    source_occurrences: tuple[dict[str, Any], ...] = ()
    original_ast_sha256: str = ""
    original_source_occurrences: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "projection_schema": "template-pandoc-semantic-content-v2",
                "ast_sha256": self.ast_sha256,
                "mathematical_sources": [list(item) for item in self.mathematical_sources],
                "image_sources": [list(item) for item in self.image_sources],
                "link_sources": [list(item) for item in self.link_sources],
                "citation_sources": [[identity, list(keys)] for identity, keys in self.citation_sources],
                "table_sources": list(self.table_sources),
                "footnote_sources": list(self.footnote_sources),
                "source_occurrences": list(self.source_occurrences),
                "original_ast_sha256": self.original_ast_sha256,
                "original_source_occurrences": list(self.original_source_occurrences),
            }
        )
        return result


def semantic_content_contract_from_ast(
    artifact_id: str, sources: tuple[tuple[str, bytes], ...], ast_bytes: bytes
) -> SemanticContentContract:
    """Project actual admitted Pandoc JSON without deleting unknown constructs.

    This pure compiler does not authenticate the AST producer. Dispatch binds
    actual parse commands and exact consumed source; replay reruns reconstruction.
    """
    from infrastructure.reporting.native_format_semantic_ast import compile_semantic_ast

    result = compile_semantic_ast(sources, ast_bytes)
    return SemanticContentContract(
        artifact_id=artifact_id,
        sources=tuple((name, hashlib.sha256(data).hexdigest()) for name, data in sources),
        blocks=tuple(result["blocks"]),
        blockers=tuple(result["blockers"]),
        ast_sha256=hashlib.sha256(ast_bytes).hexdigest(),
        mathematical_sources=tuple(result["maths"]),
        image_sources=tuple(result["images"]),
        link_sources=tuple(result["links"]),
        citation_sources=tuple(result["citations"]),
        table_sources=tuple(result["tables"]),
        footnote_sources=tuple(result["footnotes"]),
        source_occurrences=tuple(result["occurrences"]),
    )
