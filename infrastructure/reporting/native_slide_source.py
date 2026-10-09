"""Complete manuscript slide occurrence contracts, independent of native output.

This compiler accounts for all Pandoc nodes and preserves unsupported constructs.
Its marked source is an observer-owned reference, never the publication source.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_format_content_contracts import text_tokens

MAX_AST_BYTES = 8 * 1024 * 1024
MAX_NODES = 100_000
MAX_OCCURRENCES = 10_000
STRUCTURAL = frozenset(
    {
        "Para",
        "Plain",
        "Header",
        "BlockQuote",
        "BulletList",
        "OrderedList",
        "DefinitionList",
        "Div",
        "Figure",
        "Table",
        "Note",
        "Emph",
        "Strong",
        "Underline",
        "Strikeout",
        "SmallCaps",
        "Superscript",
        "Subscript",
        "Span",
        "Quoted",
        "Cite",
        "Link",
        "Code",
        "CodeBlock",
        "Image",
        "Math",
        "Str",
        "Space",
        "SoftBreak",
        "LineBreak",
        "RawBlock",
        "RawInline",
        "HorizontalRule",
        "Decimal",
        "DefaultStyle",
        "Example",
        "LowerRoman",
        "UpperRoman",
        "LowerAlpha",
        "UpperAlpha",
        "Period",
        "OneParen",
        "TwoParens",
        "DefaultDelim",
        "AlignDefault",
        "AlignLeft",
        "AlignRight",
        "AlignCenter",
        "ColWidth",
        "ColWidthDefault",
        "InlineMath",
        "DisplayMath",
        "DoubleQuote",
        "SingleQuote",
        "NormalCitation",
        "AuthorInText",
        "SuppressAuthor",
    }
)
LAYOUT_RAW = re.compile(r"^\\(?:newpage|clearpage|pagebreak)\s*$")
COMMENT_RAW = re.compile(r"^\s*<!--(?:(?!-->).)*-->\s*$", re.DOTALL)
SOURCE_IO = re.compile(r"\\(?:input|include|openin|openout|read|write|catcode|special|csname)\b")
CROSSREF_PREFIXES = ("fig:", "eq:", "tbl:", "sec:", "lst:")
FORMAL_RAW = re.compile(
    r"^\s*\\begin\{(definition|proposition|hypothesis|theorem|lemma|corollary|proof)\}(?:\[([^]]*)\])?(.*?)\\end\{\1\}\s*$",
    re.DOTALL,
)
EQUATION_RAW = re.compile(r"^\s*\\begin\{(equation\*?|align\*?|gather\*?)\}(.*?)\\end\{\1\}\s*$", re.DOTALL)
TABLE_RAW = re.compile(r"^\s*\\begin\{table\}(?:\[[^]]*\])?(.*?)\\end\{table\}\s*$", re.DOTALL)


@dataclass(frozen=True)
class SlideOccurrence:
    identity: str
    ordinal: int
    kind: str
    role: str
    source: str
    tokens: tuple[str, ...] = ()
    target: str = ""
    minimum_font_pt: float = 0.0
    source_start: int | None = None
    source_end: int | None = None


@dataclass(frozen=True)
class SlideSourceContract:
    artifact_id: str
    profile: str
    ast_sha256: str
    sources: tuple[tuple[str, str], ...]
    occurrences: tuple[SlideOccurrence, ...]
    node_inventory: tuple[tuple[str, int], ...]
    blockers: tuple[str, ...]
    title_font_pt: float
    body_font_pt: float

    def record(self) -> dict[str, Any]:
        payload = {"schema_version": "template-native-slide-complete-source-v1", **asdict(self)}
        # JSON roundtrip removes tuple/list ambiguity in retained receipts.
        payload = json.loads(json.dumps(payload, ensure_ascii=False))
        return {**payload, "digest": canonical_digest(payload)}


def _raw_class(kind: str, source: str) -> str:
    if kind == "html" and COMMENT_RAW.fullmatch(source):
        return "comment"
    if kind in {"tex", "latex"}:
        if LAYOUT_RAW.fullmatch(source):
            return "layout"
        if re.fullmatch(r"\s*\\bibliography\{[A-Za-z0-9_,-]+\}\s*", source):
            return "bibliography"
        if EQUATION_RAW.fullmatch(source):
            return "raw-math"
        if FORMAL_RAW.fullmatch(source):
            return "raw-formalism"
        if TABLE_RAW.fullmatch(source):
            return "raw-table"
    return "unsupported-raw"


def compile_slide_source_contract(
    artifact_id: str,
    sources: tuple[tuple[str, bytes], ...],
    ast_bytes: bytes,
    *,
    profile: str,
    title_font_pt: float = 28.0,
    body_font_pt: float = 20.0,
    reference_displays: dict[str, str] | None = None,
) -> SlideSourceContract:
    """Census every actual source node; occurrence order and multiplicity are strict.

    Archive font minima are the historical Beamer 10pt body/14pt heading policy.
    Accessible floors come from the exact source configuration. This compiler
    supplies no native acceptance: every paint occurrence needs a native witness.
    """
    if profile not in {"archive", "accessible"} or not sources or len(ast_bytes) > MAX_AST_BYTES:
        raise ValueError("slide source requires bounded exact source and a declared profile")
    if len({p for p, _ in sources}) != len(sources) or sum(len(b) for _, b in sources) > MAX_AST_BYTES:
        raise ValueError("slide sources are duplicated or exceed their finite byte budget")
    ast = json.loads(ast_bytes)
    if not isinstance(ast, dict) or not isinstance(ast.get("blocks"), list) or not ast.get("pandoc-api-version"):
        raise ValueError("slide source requires actual Pandoc JSON")
    nodes = 0
    inventory: dict[str, int] = {}
    occurrences: list[SlideOccurrence] = []
    blockers: list[str] = []
    title_floor = float(title_font_pt) if profile == "accessible" else 14.0
    body_floor = float(body_font_pt) if profile == "accessible" else 10.0
    if not 0 < title_floor <= 96 or not 0 < body_floor <= 72:
        raise ValueError("slide source typography policy is invalid")

    def add(path: str, tag: str, role: str, source: str, tokens: tuple[str, ...] = (), target: str = "") -> None:
        occurrences.append(
            SlideOccurrence(
                path,
                len(occurrences),
                tag,
                role,
                source,
                tokens,
                target,
                title_floor if role == "title" else body_floor,
            )
        )
        if len(occurrences) > MAX_OCCURRENCES:
            raise ValueError("slide source exceeds its original occurrence bound")

    def visit(value: Any, path: str, role: str, paint: bool = True) -> None:
        nonlocal nodes
        nodes += 1
        if nodes > MAX_NODES:
            raise ValueError("slide source exceeds its original node bound")
        if isinstance(value, list):
            for i, child in enumerate(value):
                visit(child, f"{path}/{i}", role, paint)
            return
        if not isinstance(value, dict):
            return
        tag = value.get("t")
        content: Any = value.get("c")
        if tag is not None:
            inventory[tag] = inventory.get(tag, 0) + 1
            if tag not in STRUCTURAL:
                blockers.append(f"{path}: unsupported complete source node {tag}")
            if tag == "Header":
                role = "title"
            elif tag == "Table":
                role = "table-cell"
            elif tag == "Note":
                role = "footnote"
            elif tag == "Figure":
                role = "figure-caption"
            elif tag == "Str" and paint:
                add(path, "text", role, str(content), text_tokens(str(content)))
            elif tag in {"Code", "CodeBlock"} and paint:
                add(path, "code", role, str(content[1]), text_tokens(str(content[1])))
            elif tag == "Math" and paint:
                if content[0].get("t") not in {"InlineMath", "DisplayMath"} or not content[1]:
                    raise ValueError("slide source has an invalid mathematical occurrence")
                if SOURCE_IO.search(str(content[1])) or "^^" in str(content[1]):
                    blockers.append(f"{path}: mathematical source expands outside its admitted lexical scope")
                add(path, "math", role, str(content[1]))
            elif tag == "Image" and paint:
                add(
                    path,
                    "image",
                    role,
                    json.dumps(content, ensure_ascii=False, sort_keys=True),
                    target=str(content[2][0]),
                )
            elif tag == "Link" and paint:
                add(
                    path,
                    "link",
                    role,
                    json.dumps(content, ensure_ascii=False, sort_keys=True),
                    target=str(content[2][0]),
                )
            elif tag == "Cite" and paint:
                keys = tuple(str(row["citationId"]) for row in content[0])
                if not keys or any(not key for key in keys):
                    raise ValueError("slide source has an empty citation identity")
                encoded = json.dumps(list(keys), separators=(",", ":"))
                cross = tuple(key for key in keys if key.startswith(CROSSREF_PREFIXES))
                if cross:
                    displays = reference_displays or {}
                    if len(cross) == len(keys):
                        missing = [key for key in keys if key not in displays]
                        visible = " ".join(displays.get(key, "") for key in keys)
                    else:
                        # Mixed bibliographic/cross-reference citations require
                        # an independently projected complete visible display.
                        identity = "citation:" + encoded
                        missing = [] if identity in displays else [identity]
                        visible = displays.get(identity, "")
                    blockers.extend(
                        f"{path}: independent source reference display required for {key}" for key in missing
                    )
                    add(path, "reference", role, encoded, text_tokens(visible), encoded)
                    add(path + "/keys", "citation", role, encoded)
                else:
                    add(path, "citation", role, encoded)
            elif tag in {"RawBlock", "RawInline"} and paint:
                kind = _raw_class(str(content[0]), str(content[1]))
                if SOURCE_IO.search(str(content[1])) or "^^" in str(content[1]):
                    blockers.append(f"{path}: raw source expands outside its admitted lexical scope")
                if kind in {"raw-math", "raw-formalism", "raw-table"}:
                    from infrastructure.reporting.native_slide_raw_source import raw_slide_segments

                    segments, raw_blockers = raw_slide_segments(str(content[1]), kind, references=reference_displays)
                    add(path, "raw-container", role, str(content[1]))
                    for i, segment in enumerate(segments):
                        occurrences.append(
                            SlideOccurrence(
                                f"{path}/raw/{i}",
                                len(occurrences),
                                segment.kind,
                                role,
                                segment.source,
                                segment.tokens,
                                segment.target,
                                title_floor if role == "title" else body_floor,
                                segment.start,
                                segment.end,
                            )
                        )
                    blockers.extend(f"{path}: {item}" for item in raw_blockers)
                else:
                    add(path, kind, role, str(content[1]))
                if kind == "unsupported-raw":
                    blockers.append(f"{path}: independent semantics for raw {content[0]} are required")
        if tag == "Image":
            # Alternative text is complete source metadata, distinct from the
            # projected image/caption. The native witness checks its actual
            # image identity; Reveal additionally retains the real alt value.
            visit(content, f"{path}/c", "image-alternative", False)
            return
        if tag == "Cite":
            # Cite prefix/suffix/mode are source metadata. Citeproc's c[1]
            # contains their visible result exactly once, with original keys.
            visit(content[0], f"{path}/c/0", "citation-metadata", False)
            has_cross_reference = any(str(row["citationId"]).startswith(CROSSREF_PREFIXES) for row in content[0])
            visit(content[1], f"{path}/c/1", role, paint and not has_cross_reference)
            return
        for key, child in value.items():
            if key != "t":
                visit(child, f"{path}/{key}", role, paint)

    visit(ast["blocks"], "blocks", "body")
    if not occurrences or len(occurrences) > MAX_OCCURRENCES:
        raise ValueError("slide source has no complete bounded source occurrence set")
    return SlideSourceContract(
        artifact_id,
        profile,
        hashlib.sha256(ast_bytes).hexdigest(),
        tuple((p, hashlib.sha256(b).hexdigest()) for p, b in sources),
        tuple(occurrences),
        tuple(sorted(inventory.items())),
        tuple(blockers),
        title_floor,
        body_floor,
    )


def instrument_slide_source(
    ast_bytes: bytes, contract: SlideSourceContract, *, target: str
) -> tuple[bytes, tuple[dict[str, Any], ...]]:
    """Mark each original paint leaf without inventing a visible source glyph.

    The native reference must prove exact unmarked/marked glyph/vector/image/link
    and pixel noninterference. Structural containers have their own complete
    census but do not replace or double count their descendant paint.
    """
    if target not in {"beamer", "revealjs"} or hashlib.sha256(ast_bytes).hexdigest() != contract.ast_sha256:
        raise ValueError("source instrumentation differs from its exact original source")
    ast = copy.deepcopy(json.loads(ast_bytes))
    rows = []
    by_path = {row.identity: row for row in contract.occurrences}

    def marker(row: SlideOccurrence, start: bool, inline: bool) -> dict[str, Any]:
        if target == "beamer":
            text = rf"\special{{pdf:code /Span <</MCID {row.ordinal}>> BDC}}" if start else r"\special{pdf:code EMC}"
            return {"t": "RawInline" if inline else "RawBlock", "c": ["tex", text]}
        text = f'<span data-native-slide-source="{row.ordinal}">' if start else "</span>"
        return {"t": "RawInline" if inline else "RawBlock", "c": ["html", text]}

    def walk(value: Any, path: str) -> Any:
        if isinstance(value, list):
            result: list[Any] = []
            for i, child in enumerate(value):
                changed = walk(child, f"{path}/{i}")
                result.extend(changed if isinstance(changed, tuple) else [changed])
            return result
        if not isinstance(value, dict):
            return value
        row = by_path.get(path)
        tag = value.get("t")
        # Links and citations retain descendant text witnesses; their target/key
        # is checked separately against original source. Invisible syntax never
        # acquires a fabricated paint witness.
        if row and row.kind == "raw-container":
            children = [leaf for leaf in contract.occurrences if leaf.identity.startswith(path + "/raw/")]
            raw = value["c"][1]
            changes = []
            for child in children:
                rows.append({**asdict(child), "mcid": child.ordinal})
                inline = True
                changes.extend(
                    [
                        (child.source_start, marker(child, True, inline)["c"][1]),
                        (child.source_end, marker(child, False, inline)["c"][1]),
                    ]
                )
            for offset, insertion in sorted(changes, reverse=True):
                if offset is None:
                    raise ValueError("raw source marker has no original lexical offset")
                raw = raw[:offset] + insertion + raw[offset:]
            value["c"][1] = raw
            return value
        if row and row.kind in {"text", "code", "math", "image", "reference"}:
            inline = tag not in {"CodeBlock", "RawBlock"}
            rows.append({**asdict(row), "mcid": row.ordinal})
            return (marker(row, True, inline), value, marker(row, False, inline))
        return {key: walk(child, f"{path}/{key}") if key != "t" else child for key, child in value.items()}

    ast["blocks"] = walk(ast["blocks"], "blocks")
    expected = [
        row.identity for row in contract.occurrences if row.kind in {"text", "code", "math", "image", "reference"}
    ]
    if [row["identity"] for row in rows] != expected:
        raise ValueError("source instrumentation omitted or reordered an original paint occurrence")
    return (json.dumps(ast, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode(), tuple(rows)
