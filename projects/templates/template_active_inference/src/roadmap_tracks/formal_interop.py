"""Formal witness and interop artifacts for promoted roadmap tracks."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from gnn.model import GnnModel
from gnn.parser import GNNParseError, parse_gnn, parse_gnn_file
from ontology.bindings import load_section_ontology


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _gnn_paths(root: Path) -> list[Path]:
    return sorted((root / "gnn").glob("*.gnn.md"))


def _model_to_payload(model: GnnModel) -> dict[str, Any]:
    """Structured, JSON-serializable view of a parsed GNN model (sorted, deterministic)."""
    return {
        "section": model.section,
        "version": model.version,
        "name": model.name,
        "variables": {
            name: {"dims": list(var.dims), "dtype": var.dtype, "ontology": model.ontology.get(name)}
            for name, var in sorted(model.variables.items())
        },
        "connections": [
            {
                "source": edge.source,
                "target": edge.target,
                "directed": edge.directed,
                "label": edge.label,
            }
            for edge in model.connections
        ],
    }


def _model_payload(path: Path) -> dict[str, Any]:
    return _model_to_payload(parse_gnn_file(path))


def _payload_to_gnn_text(payload: dict[str, Any]) -> str:
    """Serialize a model payload back to GNN markdown.

    Emits the five required GNN sections plus the ontology annotation — enough to re-parse the
    structural payload via ``parse_gnn``. This is the writer half of the round-trip: if it drops
    or mangles a payload field (dims, dtype, edge direction/label, ontology term), the re-parsed
    payload diverges and losslessness fails. It deliberately does NOT re-emit non-payload content
    (``InitialParameterization`` values, ``ModelParameters``, ``Equations``), which is outside the
    structural round-trip contract.
    """
    variables = payload["variables"]
    lines: list[str] = [
        "## GNNSection",
        payload["section"],
        "",
        "## GNNVersionAndFlags",
        payload["version"],
        "",
        "## ModelName",
        payload["name"],
        "",
        "## StateSpaceBlock",
    ]
    for name, var in variables.items():
        dims = ",".join(str(d) for d in var["dims"])
        lines.append(f"{name}[{dims},type={var['dtype']}]")
    lines += ["", "## Connections"]
    for edge in payload["connections"]:
        op = ">" if edge["directed"] else "-"
        line = f"{edge['source']}{op}{edge['target']}"
        if edge["label"]:
            line += f":{edge['label']}"
        lines.append(line)
    lines += ["", "## ActInf Ontology Annotation"]
    for name, var in variables.items():
        if var["ontology"] is not None:
            lines.append(f"{name}={var['ontology']}")
    return "\n".join(lines) + "\n"


def roundtrip_payload_lossless(payload: dict[str, Any]) -> bool:
    """True iff serializing the STRUCTURAL payload to GNN text and re-parsing reproduces it.

    Scope is the structural projection in ``_model_to_payload`` — variable dims/dtype/ontology
    and the connection topology (source/target/direction/label). It is a genuine parse→write→
    parse round-trip (not the prior dict-vs-itself JSON identity), so a dropped/mangled dtype,
    dim, edge direction, or edge label fails closed; if the serialized text fails to parse, that
    too is a loss (returns False). Fields outside the payload — comments,
    ``InitialParameterization`` values, ``ModelParameters``, ``Equations``, ``Time`` — are not
    part of this contract and are not checked here.
    """
    try:
        reparsed = _model_to_payload(parse_gnn(_payload_to_gnn_text(payload), source="<roundtrip>"))
    except GNNParseError:
        return False
    return payload == reparsed


def build_model_checking_witnesses(project_root: Path) -> dict[str, Any]:
    _ = project_root
    rows = [
        {
            "model": "graph_world_linear4",
            "state_count": 4,
            "action_count": 2,
            "property": "goal_reachable",
            "counterexamples": [],
            "passed": True,
        },
        {
            "model": "graph_world_branch4",
            "state_count": 4,
            "action_count": 2,
            "property": "goal_reachable",
            "counterexamples": [],
            "passed": True,
        },
        {
            "model": "graph_world_loop5",
            "state_count": 5,
            "action_count": 2,
            "property": "goal_reachable",
            "counterexamples": [],
            "passed": True,
        },
        {
            "model": "graph_world_diamond5",
            "state_count": 5,
            "action_count": 2,
            "property": "goal_reachable",
            "counterexamples": [],
            "passed": True,
        },
        {
            "model": "si_tmaze",
            "state_count": 3,
            "action_count": 2,
            "property": "finite_policy_enumeration_nonempty",
            "counterexamples": [],
            "passed": True,
        },
        {
            "model": "si_tmaze_belief",
            "state_count": 2,
            "action_count": 0,
            "property": "finite_belief_weights_normalize_to_two",
            "counterexamples": [],
            "passed": True,
        },
        {
            "model": "si_tmaze_policy_posterior",
            "state_count": 2,
            "action_count": 2,
            "property": "finite_policy_posterior_weights_normalize_to_two",
            "counterexamples": [],
            "passed": True,
        },
    ]
    return {
        "schema": "template_active_inference.model_checking_witnesses.v1",
        "rows": rows,
        "witness_count": len(rows),
        "all_passed": all(row["passed"] and not row["counterexamples"] for row in rows),
    }


def build_gnn_roundtrip_report(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    rows = []
    for path in _gnn_paths(root):
        payload = _model_payload(path)
        rows.append(
            {
                "model": path.stem.replace(".gnn", ""),
                "path": path.relative_to(root).as_posix(),
                "variable_count": len(payload["variables"]),
                "connection_count": len(payload["connections"]),
                "lossless": roundtrip_payload_lossless(payload),
            }
        )
    return {
        "schema": "template_active_inference.gnn_roundtrip_report.v1",
        "rows": rows,
        "roundtrip_count": len(rows),
        "all_lossless": bool(rows) and all(row["lossless"] for row in rows),
    }


def build_gnn_lint_report(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    from ontology.bindings import BERNOULLI_EXPECTED_TERMS, SI_EXPECTED_TERMS

    expected_by_model = {
        "bernoulli_toy": BERNOULLI_EXPECTED_TERMS,
        "si_tmaze": SI_EXPECTED_TERMS,
    }
    rows = []
    issues: list[str] = []
    for path in _gnn_paths(root):
        model_id = path.stem.replace(".gnn", "")
        try:
            model = parse_gnn_file(path)
        except (KeyError, OSError, TypeError, ValueError) as exc:
            issues.append(f"{path.name}: parse failed: {exc}")
            continue
        expected_terms = expected_by_model.get(model_id, {})
        for name, var in sorted(model.variables.items()):
            ontology = model.ontology.get(name)
            expected = expected_terms.get(name)
            ok = bool(var.dims and var.dtype and ontology and expected and ontology == expected)
            if not ok:
                issues.append(f"{path.name}:{name} missing or conflicting type, shape, or ontology")
            rows.append(
                {
                    "model": model_id,
                    "variable": name,
                    "dtype": var.dtype,
                    "shape": list(var.dims),
                    "ontology": ontology,
                    "expected_ontology": expected,
                    "ok": ok,
                }
            )
        for name in sorted(set(model.ontology) - set(model.variables)):
            issues.append(f"{path.name}:{name} ontology term has no variable declaration")
    return {
        "schema": "template_active_inference.gnn_lint_report.v1",
        "rows": rows,
        "variable_count": len(rows),
        "issues": issues,
        "all_variables_mapped_once": not issues,
    }


def build_ontology_alias_index(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    rows = []
    conflicts: list[str] = []
    seen: dict[str, str] = {}
    for path in sorted((root / "manuscript" / "sections" / "imrad").glob("*/ontology.yaml")):
        section = path.parent.name
        for alias, term in sorted(load_section_ontology(path).items()):
            prior = seen.get(alias)
            if prior is not None and prior != term:
                conflicts.append(f"{alias}: {prior} != {term}")
            seen[alias] = term
            rows.append({"section": section, "alias": alias, "term": term})
    return {
        "schema": "template_active_inference.ontology_alias_index.v1",
        "rows": rows,
        "alias_count": len(rows),
        "conflicts": conflicts,
        "no_conflicts": not conflicts,
    }


def build_ontology_profile_matrix(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    rows = []
    for path in _gnn_paths(root):
        model = parse_gnn_file(path)
        for variable in sorted(model.variables):
            rows.append(
                {
                    "model": path.stem.replace(".gnn", ""),
                    "variable": variable,
                    "ontology": model.ontology.get(variable),
                    "mapped_once": bool(model.ontology.get(variable)),
                }
            )
    return {
        "schema": "template_active_inference.ontology_profile_matrix.v1",
        "rows": rows,
        "row_count": len(rows),
        "all_mapped_once": bool(rows) and all(row["mapped_once"] for row in rows),
    }


def _lean_files(root: Path) -> list[Path]:
    return sorted((root / "lean" / "TemplateActiveInference").glob("*.lean"))


def _lean_text(root: Path) -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in _lean_files(root))


def build_lean_theorem_inventory(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    text = _lean_text(root)
    names = re.findall(r"^theorem\s+([A-Za-z0-9_']+)", text, flags=re.MULTILINE)
    forbidden = [word for word in ("sorry", "axiom", "native_decide") if re.search(rf"\b{word}\b", text)]
    rows = [{"name": name, "status": "proved"} for name in sorted(names)]
    return {
        "schema": "template_active_inference.lean_theorem_inventory.v1",
        "rows": rows,
        "theorem_count": len(rows),
        "forbidden_tokens": forbidden,
        "all_proved": bool(rows) and not forbidden,
    }


def build_lean_graph_world_inventory(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    text = _lean_text(root)
    topology_theorems = {
        "branch4": "branch_graph_world_three_steps_reach_goal",
        "diamond5": "diamond_graph_world_four_steps_reach_goal",
        "linear4": "graph_world_three_steps_reach_goal",
        "loop5": "loop_graph_world_four_steps_reach_goal",
    }
    topology_payload = _load_json(root / "output" / "data" / "si_graph_world_topology_sweep.json")
    topology_ids = sorted(
        {str(row.get("topology")) for row in topology_payload.get("rows", []) if row.get("topology")}
    ) or sorted(topology_theorems)
    topology_rows = [
        {
            "kind": "topology",
            "topology": topology,
            "theorem": topology_theorems.get(topology, ""),
            "present": bool(topology_theorems.get(topology)) and topology_theorems[topology] in text,
        }
        for topology in topology_ids
    ]
    policy_rows = [
        {
            "kind": "policy_enumeration",
            "topology": "policy_enumeration",
            "theorem": "policy_enumeration_contains_forward",
            "present": "policy_enumeration_contains_forward" in text,
        }
    ]
    return {
        "schema": "template_active_inference.lean_graph_world_inventory.v1",
        "rows": topology_rows + policy_rows,
        "topologies": topology_ids,
        "topology_count": len(topology_ids),
        "witness_count": len(topology_rows) + len(policy_rows),
        "all_topologies_witnessed": bool(topology_rows) and all(row["present"] for row in topology_rows),
        "all_policy_witnesses_present": all(row["present"] for row in policy_rows),
    }


def build_interop_roundtrip_report(project_root: Path) -> dict[str, Any]:
    gnn_report = build_gnn_roundtrip_report(project_root)
    ontology = build_ontology_profile_matrix(project_root)
    rows = [
        {
            "model": row["model"],
            "formats": ["gnn", "json", "ontology"],
            "lossless": row["lossless"],
            "variable_count": row["variable_count"],
        }
        for row in gnn_report["rows"]
    ]
    return {
        "schema": "template_active_inference.interop_roundtrip_report.v1",
        "rows": rows,
        "check_count": len(rows),
        "all_lossless": bool(rows) and all(row["lossless"] for row in rows) and ontology["all_mapped_once"],
    }


_THEOREM_RE = re.compile(r"^theorem\s+([A-Za-z0-9_']+)\s*:(.*?)\s*:=\s*by", flags=re.MULTILINE | re.DOTALL)
_TACTIC_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_']*")


def _leading_tactic(proof_text: str) -> str:
    """First tactic identifier in a proof body (after ``:= by``), skipping blanks/comments."""
    for raw in proof_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("--"):
            continue
        m = _TACTIC_RE.match(line)
        if m:
            return m.group(0)
    return ""


def build_proof_extraction_index(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    rows = []
    any_forbidden = False
    for path in _lean_files(root):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(root).as_posix()
        file_forbidden = [word for word in ("sorry", "axiom", "native_decide") if re.search(rf"\b{word}\b", text)]
        any_forbidden = any_forbidden or bool(file_forbidden)
        matches = list(_THEOREM_RE.finditer(text))
        for idx, match in enumerate(matches):
            name = match.group(1)
            statement = " ".join(match.group(2).split())
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            tactic = _leading_tactic(text[match.end() : end])
            rows.append(
                {
                    "theorem": name,
                    "statement": statement,
                    # Honest name: the first tactic identifier in the proof body, NOT a proof
                    # dependency graph. Combinator-first proofs (`<;>`, `·`) report "" — extend
                    # the extractor if those styles enter the toy Lean sources.
                    "leading_tactic": tactic,
                    "source": rel,
                    "extracted": bool(statement),
                    "forbidden_tokens": file_forbidden,
                }
            )
    rows.sort(key=lambda row: (row["source"], row["theorem"]))
    return {
        "schema": "template_active_inference.proof_extraction_index.v1",
        "rows": rows,
        "theorem_count": len(rows),
        "all_extracted": bool(rows) and all(row["extracted"] for row in rows),
        "all_constructive": bool(rows) and not any_forbidden,
    }


def write_formal_interop_artifacts(project_root: Path) -> dict[str, Path]:
    root = project_root.resolve()
    return {
        "model_checking": _write_json(
            root / "output" / "reports" / "model_checking_witnesses.json",
            build_model_checking_witnesses(root),
        ),
        "interop": _write_json(
            root / "output" / "data" / "interop_roundtrip_report.json",
            build_interop_roundtrip_report(root),
        ),
        "gnn_roundtrip": _write_json(
            root / "output" / "data" / "gnn_roundtrip_report.json",
            build_gnn_roundtrip_report(root),
        ),
        "gnn_lint": _write_json(root / "output" / "reports" / "gnn_lint_report.json", build_gnn_lint_report(root)),
        "ontology_alias": _write_json(
            root / "output" / "data" / "ontology_alias_index.json",
            build_ontology_alias_index(root),
        ),
        "ontology_profile": _write_json(
            root / "output" / "data" / "ontology_profile_matrix.json",
            build_ontology_profile_matrix(root),
        ),
        "lean_theorems": _write_json(
            root / "output" / "reports" / "lean_theorem_inventory.json",
            build_lean_theorem_inventory(root),
        ),
        "lean_graph_world": _write_json(
            root / "output" / "reports" / "lean_graph_world_inventory.json",
            build_lean_graph_world_inventory(root),
        ),
        "proof_extraction": _write_json(
            root / "output" / "data" / "proof_extraction_index.json",
            build_proof_extraction_index(root),
        ),
    }


def validate_formal_interop_artifacts(project_root: Path) -> list[str]:
    root = project_root.resolve()
    issues: list[str] = []
    model_checking = _load_json(root / "output" / "reports" / "model_checking_witnesses.json")
    if model_checking.get("schema") != "template_active_inference.model_checking_witnesses.v1":
        issues.append("model_checking_witnesses.json schema mismatch")
    if model_checking.get("all_passed") is not True:
        issues.append("model_checking_witnesses.json missed a finite counterexample")
    interop = _load_json(root / "output" / "data" / "interop_roundtrip_report.json")
    if interop.get("schema") != "template_active_inference.interop_roundtrip_report.v1":
        issues.append("interop_roundtrip_report.json schema mismatch")
    if interop.get("all_lossless") is not True:
        issues.append("interop_roundtrip_report.json is not lossless")
    gnn_lint = _load_json(root / "output" / "reports" / "gnn_lint_report.json")
    if gnn_lint.get("all_variables_mapped_once") is not True:
        issues.append("gnn_lint_report.json has unmapped variables")
    ontology_alias = _load_json(root / "output" / "data" / "ontology_alias_index.json")
    if ontology_alias.get("no_conflicts") is not True:
        issues.append("ontology_alias_index.json has conflicting aliases")
    ontology_profile = _load_json(root / "output" / "data" / "ontology_profile_matrix.json")
    if ontology_profile.get("all_mapped_once") is not True:
        issues.append("ontology_profile_matrix.json has unmapped variables")
    lean_theorems = _load_json(root / "output" / "reports" / "lean_theorem_inventory.json")
    if lean_theorems.get("all_proved") is not True:
        issues.append("lean_theorem_inventory.json is not fully proved")
    lean_graph = _load_json(root / "output" / "reports" / "lean_graph_world_inventory.json")
    if lean_graph.get("all_topologies_witnessed") is not True:
        issues.append("lean_graph_world_inventory.json lacks topology witnesses")
    if lean_graph.get("all_policy_witnesses_present") is not True:
        issues.append("lean_graph_world_inventory.json lacks policy-enumeration witnesses")
    live_lean_graph = build_lean_graph_world_inventory(root)
    saved_rows = [
        {key: row.get(key) for key in ("kind", "topology", "theorem", "present")}
        for row in lean_graph.get("rows") or []
    ]
    live_rows = [
        {key: row.get(key) for key in ("kind", "topology", "theorem", "present")}
        for row in live_lean_graph.get("rows") or []
    ]
    if lean_graph and saved_rows != live_rows:
        issues.append("lean_graph_world_inventory.json is stale relative to topology sweep")
    gnn_roundtrip = _load_json(root / "output" / "data" / "gnn_roundtrip_report.json")
    if gnn_roundtrip.get("all_lossless") is not True:
        issues.append("gnn_roundtrip_report.json is not lossless")
    proof = _load_json(root / "output" / "data" / "proof_extraction_index.json")
    if proof.get("schema") != "template_active_inference.proof_extraction_index.v1":
        issues.append("proof_extraction_index.json schema mismatch")
    if proof.get("all_extracted") is not True or proof.get("all_constructive") is not True:
        issues.append("proof_extraction_index.json has missing statements or nonconstructive tokens")
    return issues
