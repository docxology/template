"""Source-owned controls mutating actual original Mermaid SVG output bytes.

Run only in Root's scheduled phase with genuine producer/paint custody already
admitted. No source data is executed and no original producer receipt is forged.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import SubElement, tostring

from defusedxml.ElementTree import fromstring

from infrastructure.reporting.native_mermaid_svg_geometry import SvgGeometry
from infrastructure.reporting.native_mermaid_svg_topology import (
    inspect_original_mermaid_svg,
    _plain,
)

CONTROL_CODES = {
    "baseline": None,
    "changed-label": "mermaid.source.label",
    "moved-node": "mermaid.source.clipped_node",
    "removed-edge": "mermaid.source.edge_count",
    "reversed-arrow": "mermaid.source.arrow",
    "changed-endpoint": "mermaid.source.edge",
    "changed-member": "mermaid.source.member",
    "changed-cardinality": "mermaid.source.cardinality",
    "changed-class-cardinality": "mermaid.source.class_cardinality",
    "changed-message-order": "mermaid.source.message_order",
    "lost-state-start": "mermaid.source.state_endpoint",
}


def mutate_original_mermaid_svg(source: bytes, original: bytes, control: str) -> tuple[bytes, str | None]:
    """Apply one meaningful valid-XML mutant of genuine original graphics."""
    if control not in CONTROL_CODES:
        raise ValueError("unknown original Mermaid SVG control")
    if control == "baseline":
        return original, None
    parsed = SvgGeometry(original)
    baseline = inspect_original_mermaid_svg(source, original)
    if baseline["status"] != "pass":
        raise ValueError("original Mermaid control baseline lacks complete topology")
    graph = baseline["source_graph"]
    family = graph["family"]
    required = CONTROL_CODES[control]
    node = next(witness for witness in baseline["witnesses"] if witness["kind"] == "node")
    if family == "sequenceDiagram":
        groups = [
            element
            for element in parsed.elements
            if element.get("data-et") == "participant" and element.get("data-id") == node["source_identity"]
        ]
        group = min(groups, key=lambda element: parsed.frame(element)["box"][1])
    else:
        group = parsed.ids[node["svg_id"]]
    if control == "changed-label":
        changed = False
        for element in group.iter():
            if parsed.local(element) in {"text", "p", "span", "tspan"} and element.text and _plain(element.text):
                element.text = "Changed original node label"
                changed = True
                break
        if not changed:
            raise ValueError("actual SVG source label is split; select a supported actual leaf control")
    elif control == "moved-node":
        targets = (
            [
                element
                for element in parsed.elements
                if element.get("data-et") == "participant" and element.get("data-id") == graph["nodes"][0]["identity"]
            ]
            if family == "sequenceDiagram"
            else [group]
        )
        for target in targets:
            target.set("transform", "translate(900000,900000)")
    elif control == "lost-state-start":
        if family != "stateDiagram-v2":
            raise ValueError("state-start mutant requires a state source")
        groups = [
            element
            for element in parsed.elements
            if parsed.local(element) == "g" and "_start-" in element.get("id", "")
        ]
        if len(groups) != 1:
            raise ValueError("actual state start is not unique")
        parsed.parents[groups[0]].remove(groups[0])
    elif control == "changed-class-cardinality":
        if family != "classDiagram":
            raise ValueError("class cardinality mutant requires a class source")
        terminals = [element for element in parsed.elements if "edgeTerminals" in element.get("class", "").split()]
        leaves = [
            element
            for terminal in terminals
            for element in terminal.iter()
            if element.text and _plain(element.text) == "*"
        ]
        if not leaves:
            raise ValueError("select an actual original class relationship with a many terminal")
        leaves[0].text = "1"
    elif control == "changed-member":
        if family != "classDiagram":
            raise ValueError("member mutant requires a class source")
        changed = False
        for element in group.iter():
            if element.text and _plain(element.text).startswith("+"):
                element.text = "-int changed_member"
                changed = True
                break
        if not changed:
            raise ValueError("actual class SVG omitted its member leaf")
    else:
        edge = next(witness for witness in baseline["witnesses"] if witness["kind"] in {"edge", "message"})
        if family == "sequenceDiagram":
            elements = [element for element in parsed.elements if element.get("data-et") == "message"]
            target = elements[0]
        else:
            target = next(
                element for element in parsed.elements if element.get("data-id", element.get("id")) == edge["svg_id"]
            )
        if control == "removed-edge":
            parsed.parents[target].remove(target)
        elif control == "changed-endpoint":
            if family == "sequenceDiagram":
                target.set("data-to", "ChangedEndpoint")
                required = "mermaid.source.edge"
            else:
                # Keep source identities/marker/labels while moving the actual
                # decoded edge endpoints far from both declared node frames.
                target.set("transform", "translate(10000,10000)")
        elif control == "changed-message-order":
            if family != "sequenceDiagram" or len(elements) < 2:
                raise ValueError("message-order mutant requires two actual messages")
            for key in ("y1", "y2"):
                first, second = elements[0].get(key), elements[1].get(key)
                if first is None or second is None:
                    raise ValueError("actual ordered message is not a line")
                elements[0].set(key, second)
                elements[1].set(key, first)
        elif control == "changed-cardinality":
            if family != "erDiagram":
                raise ValueError("cardinality mutant requires an ER source")
            marker = parsed.ids[edge["end_marker"]["id"]]
            for child in list(marker):
                marker.remove(child)
            namespace = "{http://www.w3.org/2000/svg}"
            SubElement(marker, namespace + "path", {"d": "M3,0 L3,18 M9,0 L9,18"})
            # Select the zero-or-more relationship so its changed actual bars
            # cannot accidentally preserve an original exactly-one endpoint.
            if edge["source_edge"].get("to_cardinality") == "||":
                raise ValueError("select an actual ER many endpoint for this mutant")
        elif control == "reversed-arrow":
            if family == "erDiagram":
                raise ValueError("ER arrows are cardinalities; select changed-cardinality")
            marker = parsed.ids[edge["marker"]["id"] if family == "sequenceDiagram" else edge["end_marker"]["id"]]
            marker.set("orient", "180")
        else:
            raise ValueError("actual original Mermaid control cannot be applied")
    data = tostring(parsed.root, encoding="utf-8", xml_declaration=True)
    fromstring(data)
    if data == original:
        raise ValueError("actual original Mermaid control did not change bytes")
    return data, required


def run_original_mermaid_svg_control(
    root: Path, directory: Path, source: bytes, original: bytes, control: str
) -> dict[str, Any]:
    """Recompute the oracle; Root supervises actual original zero/one processes."""
    from infrastructure.core.files.secure_write import atomic_write_bytes_confined
    from infrastructure.reporting.native_format_acceptance_contracts import (
        create_private_native_directory,
    )

    create_private_native_directory(root, directory)
    candidate, required = mutate_original_mermaid_svg(source, original, control)
    atomic_write_bytes_confined(root, directory / "original.mmd", source, mode=0o600)
    atomic_write_bytes_confined(root, directory / "original.svg", original, mode=0o600)
    atomic_write_bytes_confined(root, directory / "candidate.svg", candidate, mode=0o600)
    observation = inspect_original_mermaid_svg(source, candidate)
    codes = {finding["code"] for finding in observation["findings"]}
    intended = (
        observation["status"] == "pass" if required is None else observation["status"] == "failed" and required in codes
    )
    return {
        "schema_version": "template-native-mermaid-original-svg-control-v1",
        "name": control,
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "original_svg_sha256": hashlib.sha256(original).hexdigest(),
        "candidate_svg_sha256": hashlib.sha256(candidate).hexdigest(),
        "required_code": required,
        "intended_original_outcome": intended,
        "oracle_exit_code": int(required is not None) if intended else 2,
        "observation": observation,
    }


def main() -> int:
    import argparse
    from infrastructure.project.public_acceptance_evidence import write_json

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--svg", type=Path, required=True)
    parser.add_argument("--control", choices=tuple(CONTROL_CODES), required=True)
    args = parser.parse_args()
    result = run_original_mermaid_svg_control(
        args.root,
        args.directory,
        args.source.read_bytes(),
        args.svg.read_bytes(),
        args.control,
    )
    write_json(args.root, args.directory / "observation.json", result)
    return int(result["oracle_exit_code"])


def replay_original_mermaid_svg_control(
    source: bytes, original: bytes, control: str, candidate: bytes, raw: dict[str, Any]
) -> None:
    """Recompute retained control bytes/oracle after Root admits its real child.

    Root must separately validate the original supervised process, exact SDK
    command/inputs, runtime custody and actual zero/one exit. This check does
    not manufacture or replace that original process receipt.
    """
    expected_fields = {
        "schema_version",
        "name",
        "source_sha256",
        "original_svg_sha256",
        "candidate_svg_sha256",
        "required_code",
        "intended_original_outcome",
        "oracle_exit_code",
        "observation",
    }
    rebuilt, required = mutate_original_mermaid_svg(source, original, control)
    observation = inspect_original_mermaid_svg(source, candidate)
    if (
        set(raw) != expected_fields
        or candidate != rebuilt
        or raw["schema_version"] != "template-native-mermaid-original-svg-control-v1"
        or raw["name"] != control
        or raw["source_sha256"] != hashlib.sha256(source).hexdigest()
        or raw["original_svg_sha256"] != hashlib.sha256(original).hexdigest()
        or raw["candidate_svg_sha256"] != hashlib.sha256(candidate).hexdigest()
        or raw["required_code"] != required
        or raw["observation"] != observation
        or raw["intended_original_outcome"] is not True
        or type(raw["oracle_exit_code"]) is not int
        or raw["oracle_exit_code"] != int(required is not None)
        or (required is None and observation["status"] != "pass")
        or (
            required is not None
            and (observation["status"] != "failed" or required not in {row["code"] for row in observation["findings"]})
        )
    ):
        raise ValueError("portable original Mermaid control mutation/source/independent oracle differs")


if __name__ == "__main__":
    raise SystemExit(main())
