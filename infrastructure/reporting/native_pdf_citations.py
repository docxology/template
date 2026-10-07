"""Independent source-only natbib/plainnat citation references for scientific PDFs.

The original pre-citeproc AST, bibliography union and source preamble are inputs.
Neither manuscript-produced TeX, aux/bbl nor extracted PDF text determines labels.
Real Pandoc/BibTeX/XeLaTeX handles names, modes, notes and year disambiguation.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

import yaml

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_format_content_contracts import MAX_BLOCKS, MAX_SOURCE_BYTES, text_tokens
from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime, budget, compile_reference
from infrastructure.rendering._pdf_latex_helpers import extract_preamble

CITATION_SCHEMA = "template-native-natbib-source-reference-v1"
CITATION_POLICY = {
    "schema_version": CITATION_SCHEMA,
    "style": "plainnat",
    "reference": "source-only Pandoc natbib writer, complete cited union, actual BibTeX/XeLaTeX",
    "producer_tex_aux_bbl": "diagnostic only",
    "normalization": "NFC/ligatures, non-whitespace glyphs; geometry-backed wrap hyphens joined only to exact reference",
    "assurance": "ordered citation glyphs and localized ink; full prose placement requires source observer",
}
_RAW_COMMANDS = frozenset({"cite", "citep", "citet", "citealp", "citealt", "citeauthor", "citeyear", "citeyearpar"})
_MODES = frozenset({"NormalCitation", "AuthorInText", "SuppressAuthor"})
_KEY = re.compile(r"[A-Za-z0-9_:.+/'-]+\Z")


@dataclass(frozen=True)
class CitationOccurrence:
    """An original source occurrence; Pandoc mode/prefix/suffix remain unmodified."""

    id: str
    keys: tuple[str, ...]
    source: dict[str, Any]
    inline: dict[str, Any]


def _group(text: str, start: int, opening: str, closing: str) -> tuple[str, int]:
    if start >= len(text) or text[start] != opening:
        raise ValueError("raw natbib citation omitted a balanced argument")
    depth, index = 1, start + 1
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == opening:
            depth += 1
            if depth > 256:
                raise ValueError("raw citation argument exceeds bounded nesting")
        elif char == closing:
            depth -= 1
            if not depth:
                return text[start + 1 : index], index + 1
        index += 1
    raise ValueError("raw natbib citation argument is unterminated")


def _space(text: str, index: int) -> int:
    while index < len(text) and text[index].isspace():
        index += 1
    return index


def _raw_command(text: str, start: int) -> tuple[dict[str, Any], int]:
    match = re.match(r"\\([A-Za-z]+)(\*)?", text[start:])
    if match is None:
        raise ValueError("raw citation command is malformed")
    name, starred = match[1], bool(match[2])
    index = _space(text, start + match.end())
    if name == "citetext":
        if starred:
            raise ValueError("starred citetext is unsupported")
        body, end = _group(text, index, "{", "}")
        children, _ = raw_citations(body)
        if not children:
            raise ValueError("raw citetext has no independently identified citations")
        return {
            "command": name,
            "starred": False,
            "keys": [key for row in children for key in row["keys"]],
            "notes": [],
            "children": children,
            "latex": text[start:end],
        }, end
    if name not in _RAW_COMMANDS and name != "nocite":
        raise ValueError(f"raw citation command {name!r} is outside the bound natbib subset")
    notes: list[str] = []
    while index < len(text) and text[index] == "[":
        note, index = _group(text, index, "[", "]")
        notes.append(note)
        index = _space(text, index)
        if len(notes) > 2:
            raise ValueError("raw natbib citation has more than two optional notes")
    keys_text, end = _group(text, index, "{", "}")
    keys = [key.strip() for key in keys_text.split(",")]
    if not keys or any(not _KEY.fullmatch(key) and not (name == "nocite" and key == "*") for key in keys):
        raise ValueError("raw natbib citation key expansion is unsupported")
    return {"command": name, "starred": starred, "keys": keys, "notes": notes, "latex": text[start:end]}, end


def raw_citations(text: str) -> tuple[list[dict[str, Any]], str]:
    """Balanced natbib commands; retain all residual raw content for admission."""
    rows, residual, cursor = [], [], 0
    pattern = re.compile(r"\\(?:[A-Za-z]*cite[A-Za-z]*)(?:\*)?\b")
    for match in pattern.finditer(text):
        if match.start() < cursor:
            continue
        residual.append(text[cursor : match.start()])
        row, cursor = _raw_command(text, match.start())
        rows.append(row)
    residual.append(text[cursor:])
    return rows, "".join(residual)


def citation_occurrences(
    ast_bytes: bytes, *, deadline: float, crossref_keys: tuple[str, ...] = ()
) -> tuple[dict[str, Any], tuple[CitationOccurrence, ...], tuple[dict[str, Any], ...], tuple[str, ...]]:
    """Read complete original Cite/raw occurrences without citeproc substitutions.

    Cross-reference exclusions must be a source-declared exact key inventory.
    Mixed crossref/bibliographic groups remain blocked until their source-owned
    filter projection is separately supplied; no prefix-based guess is admitted.
    """
    budget(deadline)
    if len(ast_bytes) > 32 * 1024 * 1024:
        raise ValueError("citation AST exceeds the existing semantic source byte bound")
    ast = json.loads(ast_bytes)
    if not isinstance(ast, dict) or not isinstance(ast.get("blocks"), list) or not isinstance(ast.get("meta"), dict):
        raise ValueError("citation reference requires an original Pandoc document AST")
    if len(set(crossref_keys)) != len(crossref_keys) or any(
        not isinstance(key, str) or not key for key in crossref_keys
    ):
        raise ValueError("crossref exclusions require unique exact declared source keys")
    exclusions = set(crossref_keys)
    occurrences: list[CitationOccurrence] = []
    nonvisible: list[dict[str, Any]] = []
    blockers: list[str] = []
    node_count = 0

    def add(keys: tuple[str, ...], source: dict[str, Any], inline: dict[str, Any]) -> None:
        if len(occurrences) >= MAX_BLOCKS:
            raise ValueError("citation occurrence census exceeds the source block bound")
        occurrences.append(CitationOccurrence(f"citation:{len(occurrences) + 1:06d}", keys, source, inline))

    def walk(node: Any, path: str, depth: int = 0) -> None:
        nonlocal node_count
        budget(deadline)
        node_count += 1
        if node_count > 100000 or depth > 256:
            raise ValueError("citation AST exceeds bounded semantic source nesting/census")
        if isinstance(node, list):
            for index, item in enumerate(node):
                walk(item, f"{path}/{index}", depth + 1)
        elif isinstance(node, dict):
            kind, value = node.get("t"), node.get("c")
            if kind == "Cite":
                if not isinstance(value, list) or len(value) != 2 or not isinstance(value[0], list) or not value[0]:
                    raise ValueError("original citation AST is malformed")
                for row in value[0]:
                    if (
                        not isinstance(row, dict)
                        or not isinstance(row.get("citationId"), str)
                        or not _KEY.fullmatch(row["citationId"])
                        or not isinstance(row.get("citationMode"), dict)
                        or row.get("citationMode", {}).get("t") not in _MODES
                        or not isinstance(row.get("citationPrefix"), list)
                        or not isinstance(row.get("citationSuffix"), list)
                    ):
                        raise ValueError("original citation ID/mode/notes are malformed")
                keys = tuple(row["citationId"] for row in value[0])
                crossed = [key for key in keys if key in exclusions]
                if crossed:
                    nonvisible.append({"kind": "declared-crossref", "path": path, "original": node})
                    if len(crossed) != len(keys):
                        blockers.append(f"{path}: mixed bibliographic/crossref group needs actual filter projection")
                    return
                add(keys, {"kind": "pandoc-cite", "path": path, "original": node}, node)
                return  # Never re-interpret literal Cite.content as another citation.
            if kind in {"Code", "CodeBlock"}:
                return  # Literal code is an independent visible-code obligation.
            if kind in {"RawInline", "RawBlock"} and isinstance(value, list) and len(value) == 2:
                if value[0] not in {"latex", "tex"}:
                    return
                text = value[1]
                if not isinstance(text, str):
                    raise ValueError("raw citation source is not text")
                if re.search(
                    r"\\(?:def|edef|gdef|newcommand|renewcommand|let|bibpunct|citestyle|setcitestyle"
                    r"|bibliographystyle|defcitealias|usepackage|RequirePackage|PassOptionsToPackage)\b",
                    text,
                ):
                    blockers.append(f"{path}: body macro/citation state change needs full source execution")
                    return
                try:
                    rows, residual = raw_citations(text)
                except ValueError as error:
                    blockers.append(f"{path}: {error}")
                    return
                if rows and residual.strip():
                    blockers.append(f"{path}: citation embedded in residual raw markup needs full source execution")
                for row in rows:
                    if row["command"] == "nocite":
                        nonvisible.append({"kind": "nocite", "path": path, "original": row})
                    else:
                        add(
                            tuple(row["keys"]),
                            {"kind": "raw-natbib", "path": path, "original": row},
                            {"t": "RawInline", "c": ["latex", row["latex"]]},
                        )
                return
            for key, item in node.items():
                if key != "t":
                    walk(item, f"{path}/{key}", depth + 1)

    walk(ast["blocks"], "blocks")
    visible_meta = {key: value for key, value in ast["meta"].items() if key != "nocite"}
    if re.search(r'"t"\s*:\s*"Cite"', json.dumps(visible_meta)):
        blockers.append("source metadata citation placement needs a full template reference")
    if ast["meta"].get("nocite"):
        nonvisible.append({"kind": "metadata-nocite", "original": ast["meta"]["nocite"]})
    return ast, tuple(occurrences), tuple(nonvisible), tuple(blockers)


def _bindings(items: tuple[tuple[str, bytes], ...]) -> list[dict[str, Any]]:
    if len({path for path, _ in items}) != len(items) or any(
        not path or not isinstance(data, bytes) for path, data in items
    ):
        raise ValueError("citation source bindings require unique nonempty names and bytes")
    return [{"path": path, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)} for path, data in items]


def _labels(
    pdf: bytes, native_text: str, occurrences: tuple[CitationOccurrence, ...], deadline: float
) -> list[dict[str, Any]]:
    import pdfplumber

    budget(deadline)
    with pdfplumber.open(BytesIO(pdf)) as document:
        if not document.pages or len(document.pages) > 500:
            raise ValueError("citation reference exceeds existing native page bounds")
        if sum(len(page.chars) for page in document.pages) > 2_000_000:
            raise ValueError("citation reference exceeds existing native glyph bounds")
        if len(native_text) > 2_000_000:
            raise ValueError("citation reference native text exceeds existing glyph bounds")
        text = native_text
    rows = []
    for ordinal, occurrence in enumerate(occurrences, 1):
        budget(deadline)
        begin, end = f"NCRBEGIN{ordinal:06d}", f"NCREND{ordinal:06d}"
        if text.count(begin) != 1 or text.count(end) != 1:
            raise ValueError("independent native citation reference lacks unique occurrence delimiters")
        start, finish = text.index(begin) + len(begin), text.index(end)
        if finish <= start:
            raise ValueError("independent citation occurrence delimiter order diverged")
        label = " ".join(text[start:finish].split())
        if not label or "?" in label:
            raise ValueError("independent native citation label is empty or unresolved")
        rows.append(
            {
                "id": occurrence.id,
                "keys": list(occurrence.keys),
                "source": occurrence.source,
                "native_text": label,
                "tokens": list(text_tokens(label)),
            }
        )
    return rows


def observe_natbib_reference(
    root: Path,
    directory: Path,
    *,
    ast_bytes: bytes,
    sources: tuple[tuple[str, bytes], ...],
    bibliographies: tuple[tuple[str, bytes], ...],
    config: tuple[tuple[str, bytes], ...] = (),
    preamble: tuple[str, bytes] | None = None,
    crossref_keys: tuple[str, ...] = (),
    env: dict[str, str],
    deadline: float,
    run_id: str,
    artifact_id: str,
) -> dict[str, Any]:
    """Render a fresh independent reference from exact admitted source inputs.

    ``directory`` is a fresh private confined leaf. Inputs are the PDF source
    worker's ordered source/config/preamble/bibliography bytes and original AST.
    Declared crossrefs remain explicit excluded occurrences owned by that worker.
    This API executes no document analysis, network, model or publication work.
    """
    if not artifact_id or not sources:
        raise ValueError("natbib reference needs an artifact and original source census")
    inputs = sources + bibliographies + config + ((preamble,) if preamble else ())
    if sum(len(data) for _, data in inputs) > MAX_SOURCE_BYTES:
        raise ValueError("citation inputs exceed the existing native source byte bound")
    source_bindings = {
        "sources": _bindings(sources),
        "bibliographies": _bindings(bibliographies),
        "config": _bindings(config),
        "preamble": _bindings((preamble,) if preamble else ()),
        "ast_sha256": hashlib.sha256(ast_bytes).hexdigest(),
        "crossref_keys": list(crossref_keys),
    }
    ast, occurrences, nonvisible, blockers = citation_occurrences(
        ast_bytes, deadline=deadline, crossref_keys=crossref_keys
    )
    runtime = CitationRuntime(root, directory, env=env, deadline=deadline, run_id=run_id)
    runtime.freeze("original-ast.json", ast_bytes)
    # Freeze the full original input census, including uncited entries and layout inputs.
    for number, (_, data) in enumerate(inputs):
        runtime.freeze(f"source-{number:06d}.input", data)
    rows = []
    for number, (_, data) in enumerate(bibliographies):
        rows.append(runtime.freeze(f"database-{number:06d}.bib", data).stem)
    if (occurrences or any(row["kind"] != "declared-crossref" for row in nonvisible)) and not rows:
        raise ValueError("source citations have no complete frozen bibliography union")
    projected = {"pandoc-api-version": ast.get("pandoc-api-version"), "meta": ast["meta"], "blocks": []}
    for number, occurrence in enumerate(occurrences, 1):
        projected["blocks"].append(
            {
                "t": "Para",
                "c": [
                    {"t": "Str", "c": f"NCRBEGIN{number:06d}"},
                    {"t": "Space"},
                    occurrence.inline,
                    {"t": "Space"},
                    {"t": "Str", "c": f"NCREND{number:06d}"},
                ],
            }
        )
    for row in nonvisible:
        if row["kind"] == "nocite":
            projected["blocks"].append({"t": "RawBlock", "c": ["latex", row["original"]["latex"]]})
    if not occurrences:
        return {
            "schema_version": CITATION_SCHEMA,
            "run_id": run_id,
            "artifact_id": artifact_id,
            "policy_digest": canonical_digest(CITATION_POLICY),
            "inputs": source_bindings,
            "occurrences": [],
            "nonvisible": list(nonvisible),
            "blockers": list(blockers),
            "tool_artifacts": [],
            "dependency_custody": None,
            "reference_pdf_sha256": None,
        }
    projected_path = runtime.freeze("citation-projection.json", json.dumps(projected, ensure_ascii=False).encode())
    dangerous = re.compile(
        r"\\(?:input|include|openin|openout|write|read|catcode|csname|directlua|special|immediate)\b"
    )
    if dangerous.search(json.dumps(projected)):
        raise ValueError("source citation notes/metadata need external or dynamic TeX scope admission")
    args = [str(projected_path), "--from=json", "--to=latex", "--standalone", "--natbib"]
    for _, config_bytes in config:
        settings = yaml.safe_load(config_bytes)
        if not isinstance(settings, dict):
            raise ValueError("source PDF citation configuration is malformed")
        metadata = settings.get("metadata", {})
        if not isinstance(metadata, dict):
            raise ValueError("source PDF citation typography metadata is malformed")
        for name in ("geometry", "documentclass", "fontsize"):
            if metadata.get(name):
                args.extend(["-V", f"{name}:{metadata[name]}"])
        if metadata.get("language"):
            args.append(f"--metadata=lang:{metadata['language']}")
    emitted = runtime.tool("pandoc", args, "citation-pandoc-natbib")["stdout"]
    if emitted.count(r"\bibliographystyle{plainnat}") != 1:
        raise ValueError("source metadata selects an unsupported non-plainnat bibliography style")
    preamble_text = ""
    if preamble:
        preamble_path = runtime.freeze("preamble.md", preamble[1])
        preamble_text = extract_preamble(preamble_path)
        # Such constructs require admitted external inputs or arbitrary native state.
        if dangerous.search(preamble_text):
            blockers += ("source citation preamble requires external/dynamic TeX scope admission",)
            raise ValueError(blockers[-1])
        if re.search(r"\\bibliographystyle\s*\{", preamble_text):
            raise ValueError("additional source bibliography style needs an explicit independent style contract")
    if emitted.count(r"\begin{document}") != 1 or emitted.count(r"\end{document}") != 1:
        raise ValueError("actual Pandoc citation reference document boundary is invalid")
    emitted = emitted.replace(r"\begin{document}", preamble_text + "\n" + r"\begin{document}", 1)
    # Reference line breaks are incidental. Preserve explicit author/note hyphens,
    # while preventing TeX from inventing discretionary hyphens in long names.
    emitted = emitted.replace(
        r"\begin{document}", r"\begin{document}" + "\n" + r"\hyphenpenalty=10000\exhyphenpenalty=10000\raggedright", 1
    )
    bibliography = r"\bibliography{" + ",".join(rows) + "}"
    if re.search(r"\\bibliography\{[^}]*\}", emitted):
        emitted = re.sub(r"\\bibliography\{[^}]*\}", lambda _: bibliography, emitted)
    else:
        emitted = emitted.replace(r"\end{document}", "\n" + bibliography + "\n" + r"\end{document}", 1)
    pdf, custody = compile_reference(runtime, emitted.encode())
    runtime.tool(
        "pdffonts", ["oracle.pdf"], "citation-reference-fonts", input_paths=(runtime.directory / "oracle.pdf",)
    )
    native_text = runtime.tool(
        "pdftotext",
        ["-layout", "oracle.pdf", "-"],
        "citation-reference-text",
        input_paths=(runtime.directory / "oracle.pdf",),
    )["stdout"]
    labels = _labels(pdf, native_text, occurrences, deadline)
    runtime.unchanged()
    return {
        "schema_version": CITATION_SCHEMA,
        "run_id": run_id,
        "artifact_id": artifact_id,
        "policy_digest": canonical_digest(CITATION_POLICY),
        "inputs": source_bindings,
        "occurrences": labels,
        "nonvisible": list(nonvisible),
        "blockers": list(blockers),
        "tool_artifacts": runtime.tools,
        "dependency_custody": custody,
        "reference_pdf_sha256": hashlib.sha256(pdf).hexdigest(),
    }
