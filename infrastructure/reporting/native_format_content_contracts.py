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
from infrastructure.validation.publication.rendered_provenance import validate_rendered_provenance

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
    if artifact.format != "pdf" or not validate_rendered_provenance(root, scope).valid:
        raise ValueError("PDF source obligations require current validated consumed hydration")
    reader.read(f"projects/{scope}/manuscript/config.yaml")
    manuscript = render_config_manuscript_dir(root / "projects" / scope)
    paths = discover_manuscript_files(manuscript)
    if artifact.id.startswith("section:") and artifact.id.endswith(":pdf"):
        name = artifact.id.removeprefix("section:").removesuffix(":pdf")
        paths = [path for path in paths if path.name == name]
    snapshots: tuple[ArtifactSnapshot, ...] = tuple(reader.read(path.relative_to(root).as_posix()) for path in paths)
    contract = content_contract_from_bytes(artifact.id, tuple((item.relative, item.content) for item in snapshots))
    if artifact.id != "manuscript:pdf" and not (artifact.id.startswith("section:") and artifact.id.endswith(":pdf")):
        # Decks, print editions and picture books do not consume full manuscript
        # prose as a literal ordered projection. Keep their native census only.
        contract = NativeContentContract(
            artifact.id, contract.sources, (), (f"{artifact.id}: domain/projection source binding unsupported",)
        )
    if not reader.unchanged() or not validate_rendered_provenance(root, scope).valid or time.monotonic() >= deadline:
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

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "projection_schema": "template-pandoc-semantic-content-v1",
                "ast_sha256": self.ast_sha256,
                "mathematical_sources": [list(item) for item in self.mathematical_sources],
                "image_sources": [list(item) for item in self.image_sources],
                "link_sources": [list(item) for item in self.link_sources],
                "citation_sources": [[identity, list(keys)] for identity, keys in self.citation_sources],
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
    import json

    if not sources or len(ast_bytes) > 32 * 1024 * 1024 or sum(len(data) for _, data in sources) > MAX_SOURCE_BYTES:
        raise ValueError("semantic source contract exceeds its finite input budget")
    document = json.loads(ast_bytes)
    if (
        not isinstance(document, dict)
        or not isinstance(document.get("blocks"), list)
        or not document.get("pandoc-api-version")
    ):
        raise ValueError("semantic source contract requires actual Pandoc JSON")
    blocks: list[ContentBlock] = []
    maths: list[tuple[str, str]] = []
    images: list[tuple[str, str, str]] = []
    links: list[tuple[str, str]] = []
    citations: list[tuple[str, tuple[str, ...]]] = []
    blockers: list[str] = []
    node_count = 0

    def identity() -> str:
        return f"ast:{node_count}"

    def inline(nodes: list[dict[str, Any]], kind: str) -> None:
        pending: list[str] = []

        def flush() -> None:
            if pending and text_tokens("".join(pending)):
                blocks.append(ContentBlock(f"{identity()}:text:{len(blocks)}", kind, 0, text_tokens("".join(pending))))
            pending.clear()

        def visit(node: dict[str, Any]) -> None:
            nonlocal node_count
            node_count += 1
            tag = node.get("t")
            content: Any = node.get("c")
            if tag == "Str":
                pending.append(content)
            elif tag in {"Space", "SoftBreak", "LineBreak"}:
                pending.append(" ")
            elif tag in {"Emph", "Strong", "Underline", "Strikeout", "SmallCaps", "Superscript", "Subscript"}:
                for child in content:
                    visit(child)
            elif tag == "Code":
                pending.append(content[1])
            elif tag == "Span":
                for child in content[1]:
                    visit(child)
            elif tag == "Quoted":
                pending.append("“" if content[0]["t"] == "DoubleQuote" else "‘")
                for child in content[1]:
                    visit(child)
                pending.append("”" if content[0]["t"] == "DoubleQuote" else "’")
            elif tag == "Link":
                links.append((identity(), content[2][0]))
                for child in content[1]:
                    visit(child)
            elif tag == "Cite":
                citations.append((identity(), tuple(item["citationId"] for item in content[0])))
                for child in content[1]:
                    visit(child)
            elif tag == "Math":
                flush()
                maths.append((identity(), content[1]))
            elif tag == "Image":
                flush()
                alt = " ".join(child.get("c", "") for child in content[1] if child.get("t") == "Str")
                images.append((identity(), content[2][0], alt))
            elif tag == "Note":
                flush()
                blockers.append(f"{identity()}: footnote placement requires separate semantic layout observation")
            else:
                flush()
                blockers.append(f"{identity()}: unsupported inline {tag}")
            if node_count > 100000:
                raise ValueError("semantic source node budget exceeded")

        for node in nodes:
            visit(node)
        flush()

    def nested(value: Any) -> None:
        if isinstance(value, dict) and value.get("t") in {
            "Para",
            "Plain",
            "Header",
            "CodeBlock",
            "Div",
            "BlockQuote",
            "BulletList",
            "OrderedList",
            "DefinitionList",
            "Table",
            "Figure",
            "RawBlock",
            "HorizontalRule",
        }:
            block(value)
        elif isinstance(value, list):
            for child in value:
                nested(child)

    def block(node: dict[str, Any]) -> None:
        nonlocal node_count
        node_count += 1
        tag = node.get("t")
        content: Any = node.get("c")
        if tag in {"Para", "Plain"}:
            inline(content, "body")
        elif tag == "Header":
            inline(content[2], f"heading:{content[0]}")
        elif tag == "CodeBlock":
            blocks.append(ContentBlock(f"{identity()}:code", "code", 0, text_tokens(content[1])))
        elif tag == "Div":
            for child in content[1]:
                block(child)
        elif tag == "OrderedList":
            nested(content[1])
        elif tag == "DefinitionList":
            for term, definitions in content:
                inline(term, "body")
                nested(definitions)
        elif tag in {"BlockQuote", "BulletList", "Table", "Figure"}:
            if tag == "Table":
                blockers.append(f"{identity()}: independent table cell geometry projection unsupported")
            nested(content)
        elif tag == "HorizontalRule":
            pass
        else:
            blockers.append(f"{identity()}: unsupported block {tag}")
        if node_count > 100000 or len(blocks) > MAX_BLOCKS:
            raise ValueError("semantic source projection budget exceeded")

    for item in document["blocks"]:
        block(item)
    if not blocks and not maths and not images:
        blockers.append("semantic source contains no obligations")
    if sum(len(item.tokens) for item in blocks) > MAX_TOKENS:
        raise ValueError("semantic source token budget exceeded")
    return SemanticContentContract(
        artifact_id,
        tuple((name, hashlib.sha256(data).hexdigest()) for name, data in sources),
        tuple(blocks),
        tuple(blockers),
        hashlib.sha256(ast_bytes).hexdigest(),
        tuple(maths),
        tuple(images),
        tuple(links),
        tuple(citations),
    )
