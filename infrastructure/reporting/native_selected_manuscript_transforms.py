"""Fixed Source manuscript transformations, never execution or native authority.

Each function reconstructs complete held inputs. Generated variables, ledgers
and image bytes remain data; independent domain, actual stage-write origin and
consuming native checks stay mandatory in the enclosing Original/Current graph.
"""

from __future__ import annotations

import hashlib
import re
import tempfile
from pathlib import Path
from string import Template
from typing import Any, Iterator

import yaml

from infrastructure.project.public_reference_git import remaining
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.publishing.metadata.metadata_from_config import publication_metadata_from_config_dict
from infrastructure.rendering._pdf_mermaid import (
    _MERMAID_BLOCK_RE,
    _normalise_mermaid_source,
    _source_hash,
    inline_mermaid_figure_markdown,
)
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader
from infrastructure.transmission.transmission_bookends import (
    BEGIN_FILENAME,
    END_FILENAME,
    render_transmission_markdown,
    transmission_context_from_inputs,
)

PROJECT_WRITERS = {
    "templates/template_active_inference": "src/manuscript/hydrate.py",
    "templates/template_template": "src/template_template/metrics/inject_metrics.py",
    "templates/template_search_project": "src/template_search_project/publish/manuscript_variables.py",
}
_SNAKE_TOKEN = re.compile(r"\{\{([a-z][a-z0-9_]*)(?::\.(\d+)f)?\}\}")
_SINGLE_BRACE = re.compile(r"(?<!\{)\{([a-z][a-z0-9_]*)\}(?!\})")
_LATEX_FENCE = re.compile(r"```\{=latex\}.*?```", re.DOTALL)


def binding(item: ArtifactSnapshot) -> dict[str, Any]:
    """A complete retained byte binding, never an admitted original token."""
    return {"path": item.relative, "sha256": item.sha256, "bytes": len(item.content)}


def _bounded_matches(pattern: re.Pattern[str], text: str) -> list[re.Match[str]]:
    result: list[re.Match[str]] = []
    for match in pattern.finditer(text):
        if len(result) >= 10000:
            raise ValueError("custom hydration exceeds the complete token occurrence ceiling")
        result.append(match)
    return result


def _template_flatten(obj: object, prefix: str, out: dict[str, str]) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_key = f"{prefix}_{key}" if prefix else key
            _template_flatten(value, new_key, out)
    elif isinstance(obj, (list, tuple)):
        out[prefix] = str(len(obj))
    else:
        out[prefix] = str(obj) if obj is not None else ""


def _custom_output_occurrences(
    text: str,
    pattern: re.Pattern[str],
    passes: list[tuple[str, str] | list[tuple[int, int, str]]],
    output: bytes,
    tokens: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Follow actual edits to each authored span, never infer origin by value.

    A later Search replacement may expand within an earlier authored token.
    A replacement crossing its boundary cannot establish exclusive ownership;
    keep that precise DATA residual rather than inventing a cell attribution.
    """
    matches = _bounded_matches(pattern, text)
    if len(matches) != len(tokens):
        raise ValueError("custom hydration newline handling changed the authored occurrence roster")
    spans = [(match.start(), match.end(), False) for match in matches]
    for edit_pass in passes:
        literal = isinstance(edit_pass, tuple)
        edits: Iterator[tuple[int, int, str]]
        if isinstance(edit_pass, tuple):
            marker, replacement_text = edit_pass
            edits = ((match.start(), match.end(), replacement_text) for match in re.finditer(re.escape(marker), text))
        else:
            edits = iter(edit_pass)
        positions = sorted({position for start, end, _ in spans for position in (start, end)})
        bounds: dict[int, tuple[int, int, bool]] = {}
        point, delta = 0, 0
        parts: list[str] = []
        cursor = 0
        for start, end, replacement in edits:
            if not cursor <= start < end <= len(text):
                raise ValueError("custom hydration output edits are overlapping or outside the complete body")
            while point < len(positions) and positions[point] <= start:
                position = positions[point]
                bounds[position] = (position + delta, position + delta, False)
                point += 1
            while point < len(positions) and positions[point] < end:
                bounds[positions[point]] = (start + delta, start + delta + len(replacement), True)
                point += 1
            if not literal:
                parts.extend((text[cursor:start], replacement))
            delta += len(replacement) - (end - start)
            cursor = end
        while point < len(positions):
            position = positions[point]
            bounds[position] = (position + delta, position + delta, False)
            point += 1
        if isinstance(edit_pass, tuple):
            updated = text.replace(edit_pass[0], edit_pass[1])
        else:
            parts.append(text[cursor:])
            updated = "".join(parts)
        if len(updated.encode()) > 64 * 1024 * 1024:
            raise ValueError("custom hydration mapped output exceeds the existing complete byte ceiling")
        mapped: list[tuple[int, int, bool]] = []
        for start, end, ambiguous in spans:
            first, _, first_crossed = bounds[start]
            _, last, last_crossed = bounds[end]
            mapped.append((first, last, ambiguous or first_crossed or last_crossed))
        spans = mapped
        text = updated
    if text.encode() != output:
        raise ValueError("custom hydration occurrence mapping differs from the exact actual Source output")
    # Encode the ordered boundaries once; repeated prefix encoding would make
    # complete occurrence mapping quadratic in the manuscript size.
    offsets: dict[int, int] = {}
    cursor, byte_count = 0, 0
    for position in sorted({position for start, end, _ in spans for position in (start, end)}):
        if not cursor <= position <= len(text):
            raise ValueError("custom hydration mapped occurrence escaped the final output")
        byte_count += len(text[cursor:position].encode())
        offsets[position] = byte_count
        cursor = position
    result: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    previous_end = 0
    for token, (start, end, ambiguous) in zip(tokens, spans, strict=True):
        if not ambiguous and start < previous_end:
            raise ValueError("custom hydration final authored occurrence ownership overlaps")
        if ambiguous:
            blockers.append(
                {"ordinal": token["ordinal"], "reason": "later Source substitution crosses authored token boundary"}
            )
            result.append({**token, "output_start_byte": None, "output_end_byte": None, "replacement_sha256": None})
        else:
            first, last = offsets[start], offsets[end]
            result.append(
                {
                    **token,
                    "output_start_byte": first,
                    "output_end_byte": last,
                    "replacement_sha256": hashlib.sha256(output[first:last]).hexdigest(),
                }
            )
            previous_end = end
    return result, blockers


def reconstruct_project_authored_hydration(
    scope: str, source: bytes, variables: dict[str, Any]
) -> tuple[bytes, dict[str, Any]] | None:
    """Rebuild the fixed selected project writers from their full data.

    Source controls selection through its public scope, authenticated complete
    plan and held writer module. No receipt can nominate an arbitrary adapter.
    ActiveInference/Template use read_text universal newlines; Search preserves
    decoded raw byte newlines. Domain truth and
    the full generated registry remain separate even on exact byte equality.
    """
    if scope not in PROJECT_WRITERS:
        return None
    if not isinstance(source, bytes) or len(source) > 64 * 1024 * 1024:
        raise ValueError("custom authored hydration needs bounded exact Source bytes")
    text = source.decode("utf-8")
    if scope != "templates/template_search_project":
        text = text.replace("\r\n", "\n").replace("\r", "\n")
    input_text = text
    replacement_passes: list[tuple[str, str] | list[tuple[int, int, str]]] = []
    tokens: list[dict[str, Any]]
    if scope == "templates/template_search_project":
        fields = (
            "config_query",
            "config_max_results",
            "config_sources",
            "result_num_papers",
            "result_num_sources",
            "result_per_source",
            "result_errors",
            "result_year_min",
            "result_year_max",
            "result_with_abstract",
            "result_with_doi",
            "deep_max_results_per_keyword",
            "deep_keyword_count",
            "deep_keywords_joined",
            "deep_sources",
            "deep_unique_papers",
        )
        if set(variables) != set(fields):
            raise ValueError("Search hydration differs from the complete Source ManuscriptVariables fields")
        resolved = text
        tokens = []
        for name in fields:
            marker = "{{" + name.upper() + "}}"
            replacement = str(variables[name])
            size = len(resolved.encode()) + resolved.count(marker) * (len(replacement.encode()) - len(marker.encode()))
            if size > 64 * 1024 * 1024:
                raise ValueError("custom hydration exceeds its complete expanded byte ceiling")
            replacement_passes.append((marker, replacement))
            resolved = resolved.replace(marker, replacement)
        unresolved = re.findall(r"\{\{([A-Z][A-Z0-9_]*)\}\}", resolved)
        algorithm = "Source-search-dataclass-field-order-uppercase-marker-substitution-v1"
    elif scope == "templates/template_template":
        flat: dict[str, str] = {}
        _template_flatten(variables, "", flat)
        template_matches = _bounded_matches(Template.pattern, text)
        size = len(text.encode())
        template_edits: list[tuple[int, int, str]] = []
        for match in template_matches:
            groups = match.groupdict()
            key = groups.get("named") or groups.get("braced")
            replacement = (
                "$"
                if groups.get("escaped") is not None
                else flat.get(key, match.group())
                if key is not None
                else match.group()
            )
            size += len(replacement.encode()) - len(match.group().encode())
            template_edits.append((match.start(), match.end(), replacement))
        if size > 64 * 1024 * 1024:
            raise ValueError("custom hydration exceeds its complete expanded byte ceiling")
        resolved = Template(text).safe_substitute(flat)
        replacement_passes.append(template_edits)
        unresolved = re.findall(r"\$\{([_a-zA-Z][_a-zA-Z0-9]*)\}", resolved)
        algorithm = "Source-template-numbered-chapter-dollar-metrics-v1"
        tokens = [match.groupdict() for match in template_matches]
    else:
        malformed = sorted(set(_SINGLE_BRACE.findall(_LATEX_FENCE.sub("", text))))
        if malformed:
            raise ValueError("custom authored hydration retains malformed single-brace tokens")
        flat = {}
        for key, value in variables.items():
            if isinstance(value, float):
                flat[key] = f"{value:.4f}".rstrip("0").rstrip(".")
            elif isinstance(value, bool):
                flat[key] = str(value).lower()
            elif value is None:
                flat[key] = ""
            else:
                flat[key] = str(value)
        entropy = variables.get("si_tmaze_mean_belief_entropy")
        if isinstance(entropy, (int, float)):
            flat["si_tmaze_mean_belief_entropy_formatted"] = f"{float(entropy):.4f}"
        unresolved = []

        expanded_bytes = len(text.encode())
        snake_edits: list[tuple[int, int, str]] = []

        def replace(match: re.Match[str]) -> str:
            nonlocal expanded_bytes
            key, precision = match.group(1), match.group(2)
            if key not in flat:
                unresolved.append(key)
                return match.group(0)
            value = flat[key]
            if precision is not None:
                # The Source grammar allows authored precision, but release
                # reconstruction retains a finite independent byte ceiling.
                if len(precision) > 3 or int(precision) > 100:
                    raise ValueError("custom authored numeric precision exceeds the finite reconstruction ceiling")
                try:
                    value = f"{float(value):.{int(precision)}f}"
                except ValueError:
                    pass
            expanded_bytes += len(value.encode()) - len(match.group().encode())
            if expanded_bytes > 64 * 1024 * 1024:
                raise ValueError("custom hydration exceeds its complete expanded byte ceiling")
            snake_edits.append((match.start(), match.end(), value))
            return value

        snake_matches = _bounded_matches(_SNAKE_TOKEN, text)
        resolved = _SNAKE_TOKEN.sub(replace, text)
        replacement_passes.append(snake_edits)
        for original_link, retargeted_link in (("](../output/", "](../"), ("](<../output/", "](<../")):
            replacement_passes.append((original_link, retargeted_link))
            resolved = resolved.replace(original_link, retargeted_link)
        algorithm = "Source-active-inference-snake-format-and-output-link-retarget-v1"
        tokens = [
            {"key": match.group(1), "precision": match.group(2), "start": match.start(), "end": match.end()}
            for match in snake_matches
        ]
    raw_text = source.decode("utf-8")
    pattern = (
        Template.pattern
        if scope == "templates/template_template"
        else re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")
        if scope == "templates/template_search_project"
        else _SNAKE_TOKEN
    )
    raw_matches = _bounded_matches(pattern, raw_text)
    tokens = []
    for ordinal, match in enumerate(raw_matches, 1):
        details = (
            match.groupdict()
            if scope == "templates/template_template"
            else {
                "key": match.group(1),
                "precision": match.group(2) if scope == "templates/template_active_inference" else None,
            }
        )
        tokens.append(
            {
                "ordinal": ordinal,
                **details,
                "source_start_byte": len(raw_text[: match.start()].encode()),
                "source_end_byte": len(raw_text[: match.end()].encode()),
            }
        )
    if unresolved or len(resolved.encode()) > 64 * 1024 * 1024 or len(tokens) > 10000:
        raise ValueError("custom authored hydration is unresolved or exceeds its finite full-input ceiling")
    output = resolved.encode()
    tokens, mapping_blockers = _custom_output_occurrences(input_text, pattern, replacement_passes, output, tokens)
    return output, {
        "algorithm": algorithm,
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "output_sha256": hashlib.sha256(output).hexdigest(),
        "occurrences": tokens,
        "output_mapping_complete": not mapping_blockers,
        "output_mapping_blockers": mapping_blockers,
    }


def reconstruct_transmission_bookend(
    config: ArtifactSnapshot, ledger: ArtifactSnapshot | None, filename: str
) -> tuple[bytes, dict[str, Any]]:
    """Reconstruct the exact selected generated boundary without native IO."""
    if filename not in {BEGIN_FILENAME, END_FILENAME}:
        raise ValueError("transmission reconstruction accepts only the two Source boundary names")
    raw = yaml.safe_load(config.content)
    if not isinstance(raw, dict):
        raise ValueError("transmission reconstruction needs its complete actual config mapping")
    releases = {"schema": "template-publication-ledger-v1", "releases": []} if ledger is None else ledger.json_object()
    # Metadata fields consumed by bookends come from config. The metadata
    # parser's unrelated abstract/variables reads are pointed at fresh absent
    # paths, so this reconstruction cannot accidentally read another run.
    with tempfile.TemporaryDirectory(prefix="native-transmission-inputs-") as temporary:
        work = Path(temporary).resolve(strict=True)
        metadata = publication_metadata_from_config_dict(
            raw,
            work / "config.yaml",
            abstract_path=work / "absent-abstract.md",
            variables_path=work / "absent-variables.json",
            allow_draft_abstract=True,
        )
    context = transmission_context_from_inputs(
        raw, releases, title=metadata.title, version=metadata.paper_version, doi=metadata.doi
    )
    if context is None:
        raise ValueError("selected transmission boundary is disabled by its actual Source config")
    content = render_transmission_markdown(context, boundary="begin" if filename == BEGIN_FILENAME else "end").encode()
    return content, {
        "algorithm": "Source-transmission-config-ledger-context-and-boundary-v1",
        "config": binding(config),
        "ledger": None if ledger is None else binding(ledger),
        "boundary": "begin" if filename == BEGIN_FILENAME else "end",
        "output_sha256": hashlib.sha256(content).hexdigest(),
        "publication_history_is_data": True,
    }


def reconstruct_inline_mermaid_source(
    content: bytes, scope: str, reader: SnapshotReader, *, deadline: float
) -> tuple[bytes | None, list[dict[str, Any]], list[str]]:
    """Rebuild every positive Source fence replacement from exact held assets.

    This is textual transformation evidence only. A file, cache record or byte
    match cannot establish the original render process, actual native mappings,
    independent diagram semantics or native ink. Missing/fallback assets retain
    explicit unresolved edges; no native render or second Core run occurs.
    """
    remaining(deadline)
    if scope not in PUBLIC_PROJECT_NAMES or len(content) > 64 * 1024 * 1024:
        raise ValueError("Mermaid reconstruction requires an actual bounded public Source scope/body")
    text = content.decode("utf-8")
    matches: list[re.Match[str]] = []
    for match in _MERMAID_BLOCK_RE.finditer(text):
        remaining(deadline)
        if len(matches) >= 100:
            raise ValueError("Mermaid reconstruction exceeds its complete occurrence ceiling")
        matches.append(match)
    if not matches:
        return content, [], []
    rows: list[dict[str, Any]] = []
    gaps: list[str] = []
    parts: list[str] = []
    cursor = 0
    for ordinal, match in enumerate(matches, 1):
        remaining(deadline)
        raw = match.group("source").strip()
        normal = _normalise_mermaid_source(raw) if raw else ""
        stem = f"inline_mermaid_{ordinal:04d}_{_source_hash(normal)}"
        prefix = f"projects/{scope}/output/figures/mermaid_inline/{stem}"
        source_path, png_path = reader.root / (prefix + ".mmd"), reader.root / (prefix + ".png")
        row: dict[str, Any] = {
            "ordinal": ordinal,
            "source_start_byte": len(text[: match.start()].encode()),
            "source_end_byte": len(text[: match.end()].encode()),
            "raw_source_sha256": hashlib.sha256(raw.encode()).hexdigest(),
            "normal_source_sha256": hashlib.sha256(normal.encode()).hexdigest(),
            "production_stem": stem,
        }
        rows.append(row)
        if not normal or not source_path.is_file() or not png_path.is_file():
            gaps.append("selected-inline-mermaid-missing-positive-source-and-asset:" + stem)
            continue
        source = reader.read(prefix + ".mmd", max_bytes=8 * 1024 * 1024)
        png = reader.read(prefix + ".png", max_bytes=16 * 1024 * 1024)
        if source.content != (normal + "\n").encode():
            raise ValueError("selected inline Mermaid source differs from the exact Source normalization")
        if not png.content.startswith(b"\x89PNG\r\n\x1a\n") or len(png.content) < 33:
            raise ValueError("selected inline Mermaid positive is not a retained PNG; native decoding remains separate")
        replacement = inline_mermaid_figure_markdown(match, stem + ".png")
        row.update(
            source=binding(source),
            png=binding(png),
            replacement_sha256=hashlib.sha256(replacement.encode()).hexdigest(),
        )
        parts.extend((text[cursor : match.start()], replacement))
        cursor = match.end()
    if gaps:
        return None, rows, gaps
    parts.append(text[cursor:])
    rewritten = "".join(parts).encode()
    if len(rewritten) > 64 * 1024 * 1024:
        raise ValueError("Mermaid reconstruction exceeds the complete rewritten byte ceiling")
    remaining(deadline)
    return rewritten, rows, ["actual-inline-mermaid-render-cache-origin-and-consuming-native-asset-lineage"]
