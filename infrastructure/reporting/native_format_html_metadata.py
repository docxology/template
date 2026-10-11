"""Config byte custody and literal HTML metadata placement witnesses.

The caller must independently authenticate the exact config and parser argv.
This module never authenticates a producer's metadata dict by itself.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

import yaml

from infrastructure.core.pipeline.fingerprints import canonical_digest

METADATA_SCHEMA = "template-native-html-config-metadata-v1"
METADATA_SCRIPT = r"""
 const metadataNode=e=>({...elementState(e),text:e.textContent,text_indices:textIndices(e)});
 const config_metadata={title:[...document.head.querySelectorAll('title')].map(e=>e.textContent),
  lang:document.documentElement.getAttribute('lang'),
  description:[...document.head.querySelectorAll('meta[name="description"]')].map(e=>e.content),
  author_meta:[...document.head.querySelectorAll('meta[name="author"]')].map(e=>e.content),
  title_block:[...document.querySelectorAll('header#title-block-header .title')].map(metadataNode),
  subtitle:[...document.querySelectorAll('header#title-block-header .subtitle')].map(metadataNode),
  author:[...document.querySelectorAll('header#title-block-header .author')].map(metadataNode)};
"""


def compile_html_config_metadata(relative: str, content: bytes) -> dict[str, Any]:
    """Reconstruct WebRenderer's exact metadata arguments from admitted YAML.

    Literal scalar placement is a finite supported form. Rich Markdown,
    multiline scalars and non-string coercions retain their exact source values
    and arguments, plus an explicit unsupported obligation.
    """
    if not relative or relative.startswith("/") or ".." in relative.split("/") or len(content) > 1024 * 1024:
        raise ValueError("HTML config metadata requires a bounded root-relative source")
    config = yaml.safe_load(content.decode("utf-8", errors="strict")) or {}
    if not isinstance(config, dict):
        raise ValueError("HTML config metadata source must be a YAML mapping")
    paper = config.get("paper") or {}
    if not isinstance(paper, dict):
        raise ValueError("HTML paper metadata must be a YAML mapping")
    records: list[dict[str, Any]] = []
    blockers: list[str] = []
    args = ["--metadata=linkReferences:true"]

    def add(key: str, value: Any, path: str, *, native: str | None = None) -> None:
        text = str(value)
        identity = f"config:{relative}:{path}:{key}"
        args.append(f"--metadata={key}:{text}")
        records.append(
            {
                "source_id": identity,
                "key": key,
                "source_path": path,
                "value": text,
                "value_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "native": native or key,
            }
        )
        # Pandoc parses CLI metadata as Markdown. Plain literals have exact
        # DOM text; other forms need a separately authenticated metadata AST.
        if not isinstance(value, str) or not text.strip() or re.search(r"[\r\n\t*_`$<>\\\[\]]", text):
            blockers.append(f"{identity}: rich/nonliteral config metadata needs an authenticated source AST witness")
        if any(char in text for char in ('"', "'")):
            blockers.append(f"{identity}: smart-quote metadata requires an authenticated source AST witness")

    title, subtitle = paper.get("title"), paper.get("subtitle")
    description = paper.get("description") or subtitle
    if title:
        add("title", title, "paper.title", native="title_block")
        add("pagetitle", title, "paper.title", native="title")
    if subtitle:
        add("subtitle", subtitle, "paper.subtitle")
    if description:
        add("description", description, "paper.description" if paper.get("description") else "paper.subtitle")
    authors = config.get("authors") or []
    if not isinstance(authors, list):
        raise ValueError("HTML authors must have a finite ordered YAML list")
    if len(authors) > 256:
        raise ValueError("HTML author metadata exceeds the finite occurrence budget")
    for index, author in enumerate(authors):
        if isinstance(author, dict) and author.get("name"):
            add("author", author["name"], f"authors.{index}.name")
        elif isinstance(author, str) and author:
            add("author", author, f"authors.{index}")
    metadata = config.get("metadata")
    language = str(metadata.get("language") or "en") if isinstance(metadata, dict) else "en"
    add("lang", language, "metadata.language")
    if not re.fullmatch(r"[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*", language):
        blockers.append(f"config:{relative}:metadata.language: unsupported HTML language declaration")
    # Repeated --metadata author semantics must be proven by an authenticated
    # native parser before multiple byline occurrences can grant approval.
    if sum(row["key"] == "author" for row in records) > 1:
        blockers.append(f"config:{relative}: repeated CLI author metadata needs authenticated native occurrence proof")
    result = {
        "schema_version": METADATA_SCHEMA,
        "source": {"path": relative, "sha256": hashlib.sha256(content).hexdigest()},
        "records": records,
        "pandoc_args": args,
        "blockers": blockers,
    }
    return {**result, "digest": canonical_digest(result)}


def inspect_html_metadata(dom: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    """Require source-exact head fields, byline occurrences and native boxes."""
    if source.get("schema_version") != METADATA_SCHEMA or source.get("digest") != canonical_digest(
        {key: value for key, value in source.items() if key != "digest"}
    ):
        raise ValueError("HTML metadata source witness digest changed")
    actual = dom.get("config_metadata")
    if not isinstance(actual, dict):
        raise ValueError("browser omitted native config metadata placement census")
    findings: list[dict[str, Any]] = []
    required: set[int] = set()
    placements = []
    expected: dict[str, list[dict[str, Any]]] = {}
    for record in source["records"]:
        expected.setdefault(record["native"], []).append(record)
    for key, records in expected.items():
        values = actual.get(key)
        if key == "lang":
            if values != records[0]["value"]:
                findings.append({"code": "html.metadata.lang", "source_id": records[0]["source_id"]})
            continue
        if not isinstance(values, list) or len(values) != len(records):
            findings.append({"code": "html.metadata.occurrences", "field": key})
            values = values if isinstance(values, list) else []
        for record, value in zip(records, values):
            identity = record["source_id"]
            if key in {"title", "description"}:
                if value != record.get("native_text", record["value"]):
                    findings.append({"code": "html.metadata.value", "source_id": identity})
                placements.append({"source_id": identity, "field": key, "text": value})
                continue
            if (
                not isinstance(value, dict)
                or value.get("text", "").strip() != record.get("native_text", record["value"]).strip()
            ):
                findings.append({"code": "html.metadata.value", "source_id": identity})
                continue
            from infrastructure.reporting.native_format_browser_structure import _box_findings

            findings.extend(_box_findings(value, dom, "metadata", identity))
            indices = value.get("text_indices")
            if not isinstance(indices, list) or any(
                type(i) is not int or not 0 <= i < len(dom["text"]) for i in indices
            ):
                raise ValueError("native metadata text indices escape actual census")
            required.update(indices)
            placements.append(
                {
                    "source_id": identity,
                    "field": key,
                    "text": value["text"],
                    "box_px": value["box"],
                    "text_indices": indices,
                }
            )
    # The byline must also agree with independently captured head author tags.
    if "author" in expected and actual.get("author_meta") != [
        row.get("native_text", row["value"]) for row in expected["author"]
    ]:
        findings.append({"code": "html.metadata.author-head"})
    return {
        "source_digest": source["digest"],
        "placements": placements,
        "source_text_indices": sorted(required),
        "findings": findings,
        "blockers": list(source["blockers"]),
    }


def bind_html_metadata_ast(source: dict[str, Any], ast_bytes: bytes) -> dict[str, Any]:
    """Bind placement text to an independently authenticated native source parse.

    Parent producer/reader must validate this parse's exact config-derived argv,
    source bytes, native executable and original successful exits. Every config
    record survives; lost repeated authors stay blocked. Math/raw/unknown rich
    metadata remains blocked until it has its own placement witness.
    """
    if len(ast_bytes) > 32 * 1024 * 1024 or source.get("digest") != canonical_digest(
        {key: value for key, value in source.items() if key != "digest"}
    ):
        raise ValueError("native metadata parse input or source identity changed")
    document = json.loads(ast_bytes)
    if (
        not isinstance(document, dict)
        or not document.get("pandoc-api-version")
        or not isinstance(document.get("meta"), dict)
    ):
        raise ValueError("HTML metadata requires actual source Pandoc JSON")

    def text(node: Any, depth: int = 0) -> str:
        if depth > 64:
            raise ValueError("metadata native source nesting budget exceeded")
        if isinstance(node, list):
            return "".join(text(item, depth + 1) for item in node)
        if not isinstance(node, dict):
            raise ValueError("unknown metadata native source form")
        tag, value = node.get("t"), node.get("c")
        if tag in {"MetaString", "Str"} and isinstance(value, str):
            return value
        if tag in {"Space", "SoftBreak", "LineBreak"}:
            return " "
        if tag in {"MetaInlines", "Emph", "Strong", "Underline", "SmallCaps"}:
            return text(value, depth + 1)
        if tag == "Span":
            if not isinstance(value, list) or len(value) != 2:
                raise ValueError("malformed metadata source span")
            if value[0] != ["", [], []]:
                raise ValueError("attributed metadata needs specific native style witness")
            return text(value[1], depth + 1)
        raise ValueError("rich math/raw/unknown metadata needs specific native placement witness")

    records = [dict(row) for row in source["records"]]
    blockers = list(source["blockers"])
    by_key: dict[str, list[dict[str, Any]]] = {}
    for row in records:
        by_key.setdefault(row["key"], []).append(row)
    proved = set()
    for key, rows in by_key.items():
        native = document["meta"].get(key)
        values = native.get("c") if isinstance(native, dict) and native.get("t") == "MetaList" else [native]
        if not isinstance(values, list) or len(values) != len(rows):
            blockers.append(f"{source['source']['path']}:{key}: native parser lost a config metadata occurrence")
            continue
        try:
            native_texts = [text(value) for value in values]
        except ValueError as exc:
            blockers.append(f"{source['source']['path']}:{key}: {exc}")
            continue
        for row, native_text in zip(rows, native_texts, strict=True):
            row["native_text"] = native_text
            proved.add(row["source_id"])
    blockers = [
        reason
        for reason in blockers
        if not any(
            reason.startswith(identity + ":")
            and any(term in reason for term in ("rich/nonliteral config metadata", "smart-quote metadata"))
            for identity in proved
        )
    ]
    if "author" in by_key and all(row["source_id"] in proved for row in by_key["author"]):
        blockers = [reason for reason in blockers if "repeated CLI author metadata" not in reason]
    result = {
        **source,
        "records": records,
        "blockers": blockers,
        "source_ast_sha256": hashlib.sha256(ast_bytes).hexdigest(),
    }
    result.pop("digest")
    return {**result, "digest": canonical_digest(result)}


def replay_html_metadata(
    dom: dict[str, Any], relative: str, content: bytes, raw: dict[str, Any], *, ast_bytes: bytes | None = None
) -> dict[str, Any]:
    """Rebuild metadata from current admitted config bytes before replay."""
    independent = compile_html_config_metadata(relative, content)
    if ast_bytes is not None:
        independent = bind_html_metadata_ast(independent, ast_bytes)
    result = inspect_html_metadata(dom, independent)
    if raw != result:
        raise ValueError("independent config metadata native placement replay differs")
    return result
