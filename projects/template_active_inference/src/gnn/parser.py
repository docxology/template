"""Spec-conformant GNN parser (project-owned, no upstream import)."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import numpy as np

from gnn.model import GnnConnection, GnnModel, GnnVariable

REQUIRED_SECTIONS = (
    "GNNSection",
    "GNNVersionAndFlags",
    "ModelName",
    "StateSpaceBlock",
    "Connections",
)

_DECL_RE = re.compile(r"^(?P<name>[^\s\[]+)\[(?P<body>[^\]]*)\]\s*(?:#\s*(?P<comment>.*))?$")
_EDGE_RE = re.compile(r"^(?P<src>[^\s>\-]+)\s*(?P<op>[>\-])\s*(?P<dst>[^\s:>\-]+)(?::(?P<label>[\w]+))?$")


class GNNParseError(Exception):
    """Raised on structural GNN parse failures."""


def _split_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = m.group(1).strip()
            buf = []
        elif current is not None:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf).strip()
    return sections


def _section(sections: dict[str, str], *names: str) -> str | None:
    for n in names:
        if n in sections:
            return sections[n]
    return None


def _parse_dims_and_type(name: str, body: str) -> tuple[tuple[int, ...], str]:
    dims: list[int] = []
    dtype: str | None = None
    for tok in (t.strip() for t in body.split(",")):
        if not tok:
            continue
        if "=" in tok:
            key, _, val = tok.partition("=")
            if key.strip() == "type":
                dtype = val.strip()
            continue
        if re.fullmatch(r"\d+", tok):
            dims.append(int(tok))
        else:
            raise GNNParseError(f"variable {name!r}: unsupported dimension token {tok!r}")
    if dtype is None:
        raise GNNParseError(f"variable {name!r}: missing required 'type=' declaration")
    if not dims:
        raise GNNParseError(f"variable {name!r}: no integer dimensions declared")
    return tuple(dims), dtype


def _parse_state_space(body: str) -> dict[str, tuple[tuple[int, ...], str, str]]:
    out: dict[str, tuple[tuple[int, ...], str, str]] = {}
    for raw in body.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _DECL_RE.match(line)
        if not m:
            raise GNNParseError(f"malformed StateSpaceBlock declaration: {line!r}")
        name = m.group("name")
        dims, dtype = _parse_dims_and_type(name, m.group("body"))
        out[name] = (dims, dtype, (m.group("comment") or "").strip())
    return out


def _parse_connections(body: str) -> list[GnnConnection]:
    edges: list[GnnConnection] = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _EDGE_RE.match(line)
        if not m:
            raise GNNParseError(f"malformed connection edge: {line!r}")
        edges.append(
            GnnConnection(
                source=m.group("src"),
                target=m.group("dst"),
                directed=(m.group("op") == ">"),
                label=m.group("label"),
            )
        )
    return edges


def _strip_comment_lines(body: str) -> str:
    return "\n".join(ln for ln in body.splitlines() if not ln.strip().startswith("#"))


def _parse_param_blocks(body: str) -> dict[str, np.ndarray]:
    text = _strip_comment_lines(body)
    out: dict[str, np.ndarray] = {}
    i = 0
    n = len(text)
    name_re = re.compile(r"([^\s=]+)\s*=\s*\{")
    while i < n:
        m = name_re.search(text, i)
        if not m:
            break
        name = m.group(1)
        depth = 0
        j = m.end() - 1
        start = j
        while j < n:
            ch = text[j]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if depth != 0:
            raise GNNParseError(f"unbalanced braces in InitialParameterization for {name!r}")
        block = text[start : j + 1]
        literal = block.replace("{", "[").replace("}", "]").replace("(", "[").replace(")", "]")
        parsed = ast.literal_eval(literal)
        out[name] = np.asarray(parsed, dtype=np.float64)
        i = j + 1
    return out


def _parse_kv(body: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in body.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            k, _, v = line.partition(":")
        elif "=" in line:
            k, _, v = line.partition("=")
        else:
            continue
        out[k.strip()] = v.strip()
    return out


def parse_gnn(text: str, *, source: str = "<string>") -> GnnModel:
    sections = _split_sections(text)
    for req in REQUIRED_SECTIONS:
        if req not in sections:
            raise GNNParseError(f"{source}: missing required section '## {req}'")

    declarations = _parse_state_space(sections["StateSpaceBlock"])
    params = _parse_param_blocks(sections.get("InitialParameterization", ""))
    variables: dict[str, GnnVariable] = {}
    for name, (dims, dtype, comment) in declarations.items():
        value = params.get(name)
        var = GnnVariable(name=name, dims=dims, dtype=dtype, comment=comment, value=value)
        if value is not None and value.size != var.size:
            raise GNNParseError(f"{source}: variable {name!r} size mismatch")
        variables[name] = var

    ontology = _parse_kv(_section(sections, "ActInf Ontology Annotation", "ActInfOntologyAnnotation") or "")
    return GnnModel(
        section=sections["GNNSection"].strip(),
        version=sections["GNNVersionAndFlags"].strip(),
        name=sections["ModelName"].strip(),
        variables=variables,
        connections=_parse_connections(sections["Connections"]),
        ontology=ontology,
        model_parameters=_parse_kv(sections.get("ModelParameters", "")),
        annotation=sections.get("ModelAnnotation", ""),
        equations=[ln for ln in sections.get("Equations", "").splitlines() if ln.strip()],
        time=sections.get("Time", "").strip(),
    )


def parse_gnn_file(path: str | Path) -> GnnModel:
    p = Path(path)
    return parse_gnn(p.read_text(encoding="utf-8"), source=str(p))
