"""Interpret literal labels in original source TeX and its source-only AUX.

This bounded leaf reads data; it executes neither AUX nor SourceDATA helpers.
The enclosing portable reader admits original source projection/compiler/FLS,
SDK, hydration, controls and current-source reproduction before using numbers.
Candidate AUX is never an input to this API.
"""

from __future__ import annotations

import hashlib
import math
import re
import time
from collections.abc import Callable
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest

SCHEMA = "template-native-original-source-label-numbers-v1"
MAX_BYTES = 4 * 1024 * 1024
MAX_LABELS = 20_000
MAX_COMMANDS = 100_000
LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,255}\Z")
NUMBER = re.compile(r"[A-Za-z0-9][A-Za-z0-9.():/-]{0,127}\Z")
COMMAND = re.compile(r"\\([A-Za-z]+|.)", re.DOTALL)


def _text(content: bytes) -> str:
    if not content or len(content) > MAX_BYTES or b"\x00" in content:
        raise ValueError("original source label input exceeds its bounded text policy")
    return content.decode("utf-8", errors="strict")


def _group(text: str, offset: int) -> tuple[str, int]:
    while offset < len(text) and text[offset].isspace():
        offset += 1
    if text[offset : offset + 1] != "{":
        raise ValueError("original source label has a malformed balanced group")
    start, depth, offset = offset + 1, 1, offset + 1
    while offset < len(text):
        char = text[offset]
        if char == "\\":
            offset += 2
            continue
        if char == "{":
            depth += 1
            if depth > 256:
                raise ValueError("original source label exceeds its group-depth budget")
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:offset], offset + 1
        offset += 1
    raise ValueError("original source label has an unterminated balanced group")


def _uncommented(text: str) -> str:
    # Preserve positions while excluding ordinary TeX comments. Escaped percent
    # signs are control symbols and cannot start a comment.
    result = list(text)
    index = 0
    while index < len(text):
        if text[index] == "\\":
            index += 2
        elif text[index] == "%":
            end = text.find("\n", index)
            end = len(text) if end < 0 else end
            result[index:end] = " " * (end - index)
            index = end
        else:
            index += 1
    return "".join(result)


def original_source_labels(source_tex: bytes) -> tuple[dict[str, Any], ...]:
    """Census exact literal label declarations, excluding comments/verbatim.

    Labels synthesized by macros, external inputs or altered TeX catcodes are
    outside this leaf and remain source-projection/raw admission obligations.
    Any original AUX label absent from this census is rejected, not inferred.
    """
    source = _uncommented(_text(source_tex))
    rows: list[dict[str, Any]] = []
    labels: set[str] = set()
    index = 0
    commands = 0
    while index < len(source):
        if source[index] != "\\":
            index += 1
            continue
        command = COMMAND.match(source, index)
        if command is None:
            raise ValueError("original source label census has an incomplete command")
        commands += 1
        if commands > MAX_COMMANDS:
            raise ValueError("original source label census exceeds its command-occurrence budget")
        end = command.end()
        if command[1] == "verb":
            end += int(source[end : end + 1] == "*")
            delimiter = source[end : end + 1]
            close = source.find(delimiter, end + 1) if delimiter and not delimiter.isspace() else -1
            if close < 0:
                raise ValueError("original source label census has unterminated verbatim")
            end = close + 1
        elif command[1] == "begin":
            environment, after = _group(source, end)
            if environment in {"verbatim", "Verbatim", "lstlisting"}:
                close = source.find("\\end{" + environment + "}", after)
                if close < 0:
                    raise ValueError("original source label census has unterminated verbatim environment")
                end = close + len(environment) + 6
        elif command[1] == "label":
            label, end = _group(source, end)
            if LABEL.fullmatch(label) is None:
                raise ValueError("original source label is dynamic or outside the literal policy")
            if label in labels:
                raise ValueError("original source repeats a label declaration")
            labels.add(label)
            rows.append({"label": label, "offset": index})
            if len(rows) > MAX_LABELS:
                raise ValueError("original source exceeds its label-occurrence budget")
        index = end
    return tuple(rows)


def reconstruct_source_reference_labels(
    source_tex: bytes,
    original_source_aux: bytes,
    *,
    requested_labels: tuple[str, ...] | None = None,
    allowed_unnumbered_labels: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Reconstruct numbers from literal source labels and genuine source-only AUX.

    Hyperref's extra fields are parsed as inert balanced groups. Cref companion
    labels and unknown/synthesized labels require an explicit independent policy.
    No command from an AUX file is executed or expanded.
    """
    declared = original_source_labels(source_tex)
    expected = {row["label"] for row in declared}
    if len(set(allowed_unnumbered_labels)) != len(allowed_unnumbered_labels) or any(
        LABEL.fullmatch(label) is None or label not in expected for label in allowed_unnumbered_labels
    ):
        raise ValueError("unnumbered source section-label policy differs from exact declared literals")
    allowed_unnumbered = set(allowed_unnumbered_labels)
    aux = _uncommented(_text(original_source_aux))
    numbers: dict[str, str] = {}
    unnumbered: dict[str, str] = {}
    for line in aux.splitlines():
        line = line.strip()
        if not line.startswith(r"\newlabel"):
            continue
        if not line.startswith(r"\newlabel{"):
            raise ValueError("original source AUX has a malformed newlabel declaration")
        label, offset = _group(line, len(r"\newlabel"))
        fields, offset = _group(line, offset)
        if line[offset:].strip():
            raise ValueError("original source AUX has residual commands on a label declaration")
        if LABEL.fullmatch(label) is None or label not in expected:
            raise ValueError("original source AUX invents an undeclared or dynamic label")
        if label in numbers or label in unnumbered:
            raise ValueError("original source AUX repeats a label declaration")
        number, after = _group(fields, 0)
        # A real TeX \newlabel has at least a page field; validate the entire
        # field closure rather than matching a prefix and dropping residual data.
        page, after = _group(fields, after)
        if NUMBER.fullmatch(page) is None:
            raise ValueError("original source AUX has an unresolved literal page field")
        count = 2
        while fields[after:].strip():
            _, after = _group(fields, after)
            count += 1
            if count > 8:
                raise ValueError("original source AUX exceeds its label-field budget")
        if not number and label in allowed_unnumbered:
            unnumbered[label] = page
        elif NUMBER.fullmatch(number) is None:
            raise ValueError("original source AUX has an unresolved literal label number")
        else:
            numbers[label] = number
        if len(numbers) + len(unnumbered) > MAX_LABELS:
            raise ValueError("original source AUX exceeds its label-occurrence budget")
    if set(numbers) | set(unnumbered) != expected:
        raise ValueError("original source AUX omits a declared source label")
    requested = tuple(sorted(numbers)) if requested_labels is None else requested_labels
    if len(set(requested)) != len(requested) or any(label not in expected for label in requested):
        raise ValueError("requested source reference label inventory differs from original source")
    if any(label in unnumbered for label in requested):
        raise ValueError("requested source numeric reference lacks an independently numbered witness")
    return {
        "schema_version": SCHEMA,
        "source_tex_sha256": hashlib.sha256(source_tex).hexdigest(),
        "source_aux_sha256": hashlib.sha256(original_source_aux).hexdigest(),
        "declared_labels": list(declared),
        "requested_labels": list(requested),
        "allowed_unnumbered_labels": list(allowed_unnumbered_labels),
        "unnumbered_labels": [{"label": label, "page": unnumbered[label]} for label in sorted(unnumbered)],
        "label_numbers": {label: numbers[label] for label in requested},
        "component_status": "pass",
        "scope": "literal labels in admitted original source-only TeX/AUX",
    }


def replay_source_reference_labels(
    original: dict[str, Any],
    whole_reference: dict[str, Any],
    *,
    read_artifact: Callable[[dict[str, Any]], bytes],
    deadline: float,
) -> dict[str, Any]:
    """Recompute the retained label leaf from portable original reference bytes.

    This leaf cannot certify the enclosing whole-source admission. The caller
    independently replays every original projection/compiler/FLS/raster/tool and
    source/hydration/SDK predicate before exporting the returned numeric map.
    """
    if not math.isfinite(deadline) or time.monotonic() >= deadline:
        raise TimeoutError("portable source label interpretation has no finite budget")
    if (
        whole_reference.get("schema_version") != "template-native-whole-source-pdf-reference-v1"
        or whole_reference.get("component_status") != "pass"
    ):
        raise ValueError("original whole-source reference did not complete its native component")

    reference = whole_reference["references"]["uninstrumented"]
    return replay_source_reference_label_bytes(
        original,
        source_tex_binding=reference["tex"],
        projection_tex_binding=whole_reference["projection"]["source_tex"],
        original_aux_binding=reference["aux"],
        read_artifact=read_artifact,
        deadline=deadline,
    )


def replay_source_reference_label_bytes(
    original: dict[str, Any],
    *,
    source_tex_binding: dict[str, Any],
    projection_tex_binding: dict[str, Any],
    original_aux_binding: dict[str, Any],
    read_artifact: Callable[[dict[str, Any]], bytes],
    deadline: float,
) -> dict[str, Any]:
    """Recompute the label data leaf; enclosing process/source admission is required."""
    if not math.isfinite(deadline) or time.monotonic() >= deadline:
        raise TimeoutError("portable source label interpretation has no finite budget")

    def admitted(binding: dict[str, Any]) -> bytes:
        if set(binding) != {"path", "sha256"} or not isinstance(binding["path"], str) or not binding["path"]:
            raise ValueError("original source label artifact binding is malformed")
        if time.monotonic() >= deadline:
            raise TimeoutError("portable source label interpretation exhausted its finite deadline")
        content = read_artifact(binding)
        _text(content)
        if hashlib.sha256(content).hexdigest() != binding["sha256"]:
            raise ValueError("original source label artifact bytes differ from custody")
        return content

    source_tex = admitted(source_tex_binding)
    projection_tex = admitted(projection_tex_binding)
    if source_tex != projection_tex:
        raise ValueError("original source-only reference TeX differs from original source projection")
    current = reconstruct_source_reference_labels(
        source_tex,
        admitted(original_aux_binding),
        requested_labels=tuple(original["requested_labels"]),
        allowed_unnumbered_labels=tuple(original["allowed_unnumbered_labels"]),
    )
    if canonical_digest(current) != canonical_digest(original):
        raise ValueError("retained original label map differs from portable source-only interpretation")
    return current
