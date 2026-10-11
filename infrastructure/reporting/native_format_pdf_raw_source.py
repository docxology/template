"""Real original-Pandoc interpretation of bounded source TeX occurrences.

Pandoc's LaTeX reader is a semantic witness, not permission to drop arbitrary
commands. The original command census and every residual raw node survive.
Complete native font/layout/figure/math/citation witnesses remain mandatory.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
from infrastructure.reporting.native_format_pdf_semantic_plan import PDFSemanticPlan, strict_ast
from infrastructure.reporting.native_format_portable_custody import validate_executable_observation
from infrastructure.reporting.native_scientific_reference_replay import TOOL_FIELDS
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

from infrastructure.reporting.native_format_pdf_tex_policy import (
    DYNAMIC_COMMANDS,
    ENVIRONMENTS,
    LAYOUT_COMMANDS,
    SEMANTIC_COMMANDS,
)


SCHEMA = "template-native-pdf-original-tex-semantics-v1"


def tex_command_census(source: str) -> dict[str, Any]:
    """Retain commands in comments/verbatim correctly and refuse dynamic scope."""
    if len(source.encode()) > 4 * 1024 * 1024:
        raise ValueError("original raw TeX exceeds its finite byte budget")
    commands = []
    blockers = []
    index = 0
    while index < len(source):
        char = source[index]
        if char == "%":
            end = source.find("\n", index)
            index = len(source) if end < 0 else end + 1
            continue
        if char != "\\":
            index += 1
            continue
        match = re.match(r"\\([A-Za-z]+|.)", source[index:], re.DOTALL)
        if match is None:
            blockers.append(f"offset {index}: incomplete TeX command")
            break
        name = match[1]
        end = index + match.end()
        row: dict[str, Any] = {"offset": index, "command": name}
        if name == "verb":
            delimiter_index = end + (1 if source[end : end + 1] == "*" else 0)
            delimiter = source[delimiter_index : delimiter_index + 1]
            close = source.find(delimiter, delimiter_index + 1) if delimiter else -1
            if close < 0 or delimiter.isspace():
                blockers.append(f"offset {index}: unterminated original verbatim command")
                break
            row["verbatim_sha256"] = hashlib.sha256(source[delimiter_index + 1 : close].encode()).hexdigest()
            end = close + 1
        elif name in {"begin", "end"}:
            environment = re.match(r"\s*\{([^{}]+)\}", source[end:])
            if environment is None or environment[1] not in ENVIRONMENTS:
                blockers.append(f"offset {index}: unsupported original TeX environment")
            else:
                row["environment"] = environment[1]
                end += environment.end()
                if name == "begin" and environment[1] == "verbatim":
                    close = source.find(r"\end{verbatim}", end)
                    if close < 0:
                        blockers.append(f"offset {index}: unterminated original verbatim environment")
                        break
                    row["verbatim_sha256"] = hashlib.sha256(source[end:close].encode()).hexdigest()
                    end = close + len(r"\end{verbatim}")
        elif name in DYNAMIC_COMMANDS:
            blockers.append(f"offset {index}: original TeX {name} requires consumed dynamic-input admission")
        elif name in LAYOUT_COMMANDS:
            blockers.append(f"offset {index}: original TeX {name} requires independent native layout interpretation")
        elif name not in SEMANTIC_COMMANDS and name not in {
            "verb",
            "\\",
            "%",
            "&",
            "#",
            "$",
            "_",
            "{",
            "}",
            " ",
            ",",
            ";",
            ":",
            "!",
            "(",
            ")",
            "[",
            "]",
            "'",
            '"',
            "`",
            "~",
            "^",
            "=",
        }:
            blockers.append(f"offset {index}: unknown original TeX command {name}")
        commands.append(row)
        if len(commands) > 100_000:
            raise ValueError("original TeX command census exceeds its finite budget")
        index = end
    return {"commands": commands, "blockers": blockers}


def _residual_raw(ast: bytes) -> list[str]:
    pending = [(strict_ast(ast)["blocks"], "blocks")]
    result = []
    visited = 0
    while pending:
        value, path = pending.pop()
        visited += 1
        if visited > 100_000:
            raise ValueError("raw TeX interpreted AST exceeds its node budget")
        if isinstance(value, dict):
            if value.get("t") in {"RawInline", "RawBlock"}:
                result.append(f"{path}: interpreted original TeX retains {value['t']}")
            pending.extend((child, f"{path}/{key}") for key, child in value.items())
        elif isinstance(value, list):
            pending.extend((child, f"{path}/{index}") for index, child in enumerate(value))
    return sorted(result)


def observe_pdf_raw_source(
    root: Path,
    directory: Path,
    plan: PDFSemanticPlan,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> dict[str, Any]:
    """Run the genuine original reader on every source raw-TeX occurrence."""
    rows = []
    for occurrence in plan.occurrences:
        if occurrence["kind"] not in {"RawInline", "RawBlock"}:
            continue
        if time.monotonic() >= deadline:
            raise TimeoutError("original TeX semantic observer exhausted its finite deadline")
        form, source = occurrence["content"]
        census = tex_command_census(source)
        if form not in {"tex", "latex"}:
            rows.append({"identity": occurrence["identity"], "blockers": [f"unsupported original raw format {form}"]})
            continue
        leaf = directory / f"raw-{len(rows):05d}"
        path = leaf / "original-source.tex"
        atomic_write_bytes_confined(root, path, source.encode(), mode=0o600)
        tool = native_tool_record(
            root,
            leaf,
            "pandoc",
            [str(path), "--from=latex", "--to=json"],
            env=env,
            deadline=deadline,
            run_id=run_id,
            purpose="pdf-original-tex-semantics",
        )
        process = json.loads(SnapshotReader(root).read(tool["artifact"]["path"]).content)
        if process["exit_code"] != 0 or process["original_exit_code"] != 0 or process["timed_out"]:
            raise ValueError("actual original TeX reader failed")
        ast = process["stdout"].encode()
        target = leaf / "interpreted.ast.json"
        atomic_write_bytes_confined(root, target, ast, mode=0o600)
        rows.append(
            {
                "identity": occurrence["identity"],
                "source_content_sha256": occurrence["content_sha256"],
                "source": {
                    "path": path.relative_to(root).as_posix(),
                    "sha256": hashlib.sha256(source.encode()).hexdigest(),
                },
                "ast": {"path": target.relative_to(root).as_posix(), "sha256": hashlib.sha256(ast).hexdigest()},
                "parser_artifact": tool["artifact"],
                "census": census,
                "blockers": [*census["blockers"], *_residual_raw(ast)],
            }
        )
    return {"schema_version": SCHEMA, "run_id": run_id, "source_plan_digest": plan.digest, "rows": rows}


def replay_pdf_raw_source(
    raw: dict[str, Any],
    plan: PDFSemanticPlan,
    *,
    read_artifact: Callable[[dict[str, Any]], bytes],
    producer_path: Callable[[str], str],
    run_id: str,
    deadline: float,
) -> dict[str, bytes]:
    """Recompute command/AST predicates from portable original process bytes."""
    if (
        set(raw) != {"schema_version", "run_id", "source_plan_digest", "rows"}
        or raw["schema_version"] != SCHEMA
        or raw["run_id"] != run_id
        or raw["source_plan_digest"] != plan.digest
    ):
        raise ValueError("original raw-TeX receipt differs from admitted source plan")
    source_rows = [row for row in plan.occurrences if row["kind"] in {"RawInline", "RawBlock"}]
    if len(raw["rows"]) != len(source_rows):
        raise ValueError("original raw-TeX receipt omitted or repeated a source occurrence")
    expansions = {}

    def admitted(binding: dict[str, Any]) -> bytes:
        if time.monotonic() >= deadline:
            raise TimeoutError("portable raw-TeX replay exhausted its finite deadline")
        if set(binding) != {"path", "sha256"}:
            raise ValueError("raw-TeX artifact binding fieldset differs")
        content = read_artifact(binding)
        if hashlib.sha256(content).hexdigest() != binding["sha256"]:
            raise ValueError("original raw-TeX artifact differs from its binding")
        return content

    for row, occurrence in zip(raw["rows"], source_rows, strict=True):
        if row["identity"] != occurrence["identity"]:
            raise ValueError("original raw-TeX occurrence order differs")
        form, source = occurrence["content"]
        if form not in {"tex", "latex"}:
            if row != {"identity": occurrence["identity"], "blockers": [f"unsupported original raw format {form}"]}:
                raise ValueError("unsupported raw source obligation changed")
            continue
        if (
            set(row) != {"identity", "source_content_sha256", "source", "ast", "parser_artifact", "census", "blockers"}
            or row["source_content_sha256"] != occurrence["content_sha256"]
        ):
            raise ValueError("original raw-TeX source occurrence binding differs")
        if admitted(row["source"]) != source.encode():
            raise ValueError("original raw-TeX process consumed different source bytes")
        ast = admitted(row["ast"])
        process = json.loads(admitted(row["parser_artifact"]))
        if (
            set(process) != TOOL_FIELDS
            or process["run_id"] != run_id
            or process["purpose"] != "pdf-original-tex-semantics"
            or process["tool"] != "pandoc"
            or process["exit_code"] != 0
            or process["original_exit_code"] != 0
            or process["timed_out"]
            or process["custody_refused"]
        ):
            raise ValueError("original raw-TeX parser process was not admitted success")
        if (
            process["command"]
            != [process["executable"], producer_path(row["source"]["path"]), "--from=latex", "--to=json"]
            or process["stdout"].encode() != ast
        ):
            raise ValueError("original raw-TeX parser command or exact stdout differs")
        validate_executable_observation(
            process["executable_observation_before"], process["executable"], process["executable_sha256"]
        )
        validate_executable_observation(
            process["executable_observation_after"], process["executable"], process["executable_sha256"]
        )
        if process["executable_observation_before"] != process["executable_observation_after"]:
            raise ValueError("original raw-TeX parser executable changed during execution")
        census = tex_command_census(source)
        if row["census"] != census or row["blockers"] != [*census["blockers"], *_residual_raw(ast)]:
            raise ValueError("original raw-TeX semantic blockers were changed or waived")
        expansions[row["identity"]] = ast
    return expansions
