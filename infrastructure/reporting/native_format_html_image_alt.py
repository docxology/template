"""Occurrence-complete original image alternatives and observed native alt."""

from __future__ import annotations

import hashlib
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.release_readiness_snapshot import json_object_from_bytes

ALT_SCHEMA = "template-native-html-original-image-alt-v1"
ALT_SCRIPT = r"""
 for(const [i,e] of [...document.images].entries()){
  data.images[i].alt_present=e.hasAttribute('alt');data.images[i].alt=e.getAttribute('alt');
 }
"""


def _images(ast_bytes: bytes) -> list[dict[str, Any]]:
    document = json_object_from_bytes(ast_bytes)
    images: list[dict[str, Any]] = []
    notes: list[tuple[Any, str]] = []
    nodes = 0

    def walk(value: Any, path: str, depth: int) -> None:
        nonlocal nodes
        nodes += 1
        if nodes > 100000 or depth > 64:
            raise ValueError("original image alternatives exceed the finite source AST bound")
        if isinstance(value, dict):
            if value.get("t") == "Note":
                notes.append((value["c"], path + "/c"))
                return
            if value.get("t") == "Image":
                content = value["c"]
                if not isinstance(content, list) or len(content) != 3 or not isinstance(content[1], list):
                    raise ValueError("original image alternative AST is malformed")
                images.append(
                    {
                        "source_id": "image-alt:" + path,
                        "attributes": content[0],
                        "alternative_ast": content[1],
                        "target": content[2],
                    }
                )
            for key, child in value.items():
                walk(child, path + "/" + key, depth + 1)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, path + "/" + str(index), depth + 1)

    walk(document.get("blocks"), "blocks", 0)
    cursor = 0
    while cursor < len(notes):
        value, path = notes[cursor]
        cursor += 1
        walk(value, path, 0)
    return images


def figure_caption_image_aliases(ast_bytes: bytes) -> dict[str, dict[str, Any]]:
    """Exact modern caption/alt aliases with a finite Pandoc HTML string rule.

    Pandoc 3.12 HTML Image uses stringifyInlines: Str is literal, Space is one
    space and Math is its exact TeX source. This projects an alternative
    attribute, never visible mathematical glyphs. Other rich nodes, empty
    captions, short captions and explicit alt overrides stay unsupported.
    """
    from infrastructure.reporting.native_format_pdf_semantic_plan import exact_figure_caption_alias

    document = json_object_from_bytes(ast_bytes)
    aliases: dict[str, dict[str, Any]] = {}
    count = 0

    def walk(value: Any, path: str, depth: int) -> None:
        nonlocal count
        count += 1
        if count > 100000 or depth > 256:
            raise ValueError("Figure caption aliases exceed the finite Source AST bound")
        if isinstance(value, dict):
            alias = exact_figure_caption_alias(value)
            if alias is not None:
                alternative, relative_image = alias
                image = value
                for member in relative_image:
                    image = image[member]
                attributes = image["c"][0]
                if (
                    isinstance(attributes, list)
                    and len(attributes) == 3
                    and isinstance(attributes[2], list)
                    and not any(item[0] == "alt" for item in attributes[2])
                ):
                    pieces: list[str] = []
                    for node in alternative:
                        if isinstance(node, dict) and node.get("t") == "Str" and isinstance(node.get("c"), str):
                            pieces.append(node["c"])
                        elif isinstance(node, dict) and node.get("t") == "Space":
                            pieces.append(" ")
                        elif (
                            isinstance(node, dict)
                            and node.get("t") == "Math"
                            and isinstance(node.get("c"), list)
                            and len(node["c"]) == 2
                            and node["c"][0] in ({"t": "InlineMath"}, {"t": "DisplayMath"})
                            and isinstance(node["c"][1], str)
                        ):
                            pieces.append(node["c"][1])
                        else:
                            break
                    else:
                        expected = "".join(pieces)
                        if expected.strip():
                            image_path = path + "/" + "/".join(map(str, relative_image))
                            aliases[image_path] = {
                                "figure_path": path,
                                "caption_path": path + "/c/1/1/0/c",
                                "image_path": image_path,
                                "alternative_ast": alternative,
                                "expected_alt": expected,
                                "model": "pandoc-html-Str-Space-Math-caption-alias-v1",
                            }
            for key, child in value.items():
                walk(child, path + "/" + key, depth + 1)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, path + "/" + str(index), depth + 1)

    walk(document.get("blocks"), "blocks", 0)
    return aliases


def compile_original_image_alt(original_ast: bytes, projected_ast: bytes) -> dict[str, Any]:
    """Retain every rich alternative before transformation; never flatten it away.

    Literal Str/Space and exact modern Figure Str/Space/Math caption aliases
    have a finite independent HTML alt string model. Other rich, raw, empty
    and line-breaking alternatives retain their complete explicit obligations.
    Original/projected target rewrites are owned by the authenticated source
    transformation reader, rather than accepted on a basename match here.
    """
    original, projected = _images(original_ast), _images(projected_ast)
    aliases = figure_caption_image_aliases(original_ast)
    findings: list[dict[str, Any]] = []
    blockers: list[str] = []
    rows = []
    if len(original) != len(projected):
        findings.append({"code": "html.figure.alt-source-count"})
    for index, image in enumerate(original):
        expected: str | None = ""
        alternative = image["alternative_ast"]
        for node in alternative:
            if node.get("t") == "Str" and isinstance(node.get("c"), str):
                expected += node["c"]
            elif node.get("t") == "Space":
                if expected is None:
                    raise ValueError("literal image alternative lost its exact source text")
                expected += " "
            else:
                expected = None
                break
        alias = aliases.get(image["source_id"].removeprefix("image-alt:"))
        if alias is not None:
            expected = alias["expected_alt"]
        if not expected:
            blockers.append(
                image["source_id"]
                + ": rich/empty/line-breaking original alt needs a specific independent writer string model"
            )
            expected = None
        projection = projected[index] if index < len(projected) else None
        if projection is not None and (
            projection["alternative_ast"] != alternative
            or (alias is not None and any(item[0] == "alt" for item in projection["attributes"][2]))
        ):
            findings.append({"code": "html.figure.alt-source", "source_id": image["source_id"]})
        rows.append(
            {
                **image,
                "native_target": projection["target"][0] if projection else None,
                "projected_alternative_ast": projection["alternative_ast"] if projection else None,
                "expected_alt": expected,
                **({"caption_alias": alias} if alias is not None else {}),
            }
        )
    base = {
        "schema_version": ALT_SCHEMA,
        "original_ast_sha256": hashlib.sha256(original_ast).hexdigest(),
        "projected_ast_sha256": hashlib.sha256(projected_ast).hexdigest(),
        "images": rows,
        "findings": findings,
        "blockers": blockers,
    }
    return {**base, "digest": canonical_digest(base)}


def inspect_original_image_alt(source: dict[str, Any], dom: dict[str, Any]) -> dict[str, Any]:
    """Bind each complete source occurrence to a distinct actual native image."""
    if source.get("schema_version") != ALT_SCHEMA or source.get("digest") != canonical_digest(
        {key: value for key, value in source.items() if key != "digest"}
    ):
        raise ValueError("original image alternative source witness changed")
    used: set[int] = set()
    findings = list(source["findings"])
    observations = []
    for row in source["images"]:
        selected = next(
            (
                index
                for index, image in enumerate(dom["images"])
                if index not in used and image["src"] == row["native_target"]
            ),
            None,
        )
        if selected is None:
            findings.append({"code": "html.figure.alt-source", "source_id": row["source_id"]})
            continue
        used.add(selected)
        image = dom["images"][selected]
        if type(image.get("alt_present")) is not bool or not (
            image.get("alt") is None or isinstance(image.get("alt"), str)
        ):
            raise ValueError("actual browser omitted image alt attribute observation")
        if row["expected_alt"] is not None and (not image["alt_present"] or image["alt"] != row["expected_alt"]):
            findings.append({"code": "html.figure.alt", "source_id": row["source_id"], "image_index": selected})
        observations.append(
            {
                "source_id": row["source_id"],
                "image_index": selected,
                "alt_present": image["alt_present"],
                "native_alt": image["alt"],
                "alternative_ast_digest": canonical_digest(row["alternative_ast"]),
            }
        )
    result = {
        "source_digest": source["digest"],
        "images": observations,
        "findings": findings,
        "blockers": list(source["blockers"]),
    }
    return {**result, "status": "fail" if findings else "blocked" if result["blockers"] else "pass"}


def replay_original_image_alt(
    original_ast: bytes, projected_ast: bytes, dom: dict[str, Any], raw: dict[str, Any]
) -> dict[str, Any]:
    result = inspect_original_image_alt(compile_original_image_alt(original_ast, projected_ast), dom)
    if result != raw:
        raise ValueError("independent original rich image alternative replay differs")
    return result
