"""Real supervised math, citation and source-figure native browser controls."""

from __future__ import annotations

import argparse
import hashlib
import sys
import time
from io import BytesIO
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.reporting.native_format_browser_oracles import audit_browser_html
from infrastructure.reporting.native_format_content_contracts import semantic_content_contract_from_ast
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SEMANTIC_CONTROL_CODES = {
    "baseline": None,
    "changed-math": "html.math.source",
    "changed-citation": "html.citation.source",
    "hidden-math": "html.math.invisible",
    "distorted-figure": "html.figure.distortion",
    "opaque-figure": "html.figure.visual",
    "single-pixel-figure": "html.figure.pixels",
    "baseline-structure": None,
    "changed-table-cell": "html.table.content",
    "changed-table-span": "html.table.span",
    "reordered-table-cell": "html.table.content",
    "hidden-table-cell": "html.table.visibility",
    "changed-footnote": "html.footnote.content",
    "hidden-footnote": "html.footnote.visibility",
    "wrong-footnote-target": "html.footnote.target",
    "opaque-footnote": "html.visual.invisible",
    "changed-alpha-pixel": "html.figure.pixels",
    "opaque-alpha-figure": "html.figure.visual",
}
SOURCE = b"# Invented measurement\n\nMeasured value -3.25 mV.\n\n$x^2 + \\frac{1}{2}$\n\nInvented reference [@invented].\n\n![Invented pixels](figure.png)\n"
BIBLIOGRAPHY = b"@article{invented,author={Example, Ada},title={Invented measurement fixture},journal={Example Journal},year={2020}}\n"

STRUCTURE_SOURCE = SOURCE + (
    b"\n| Invented channel | Invented value |\n|---|---:|\n| A | -9.25 |\n| B | 2.75 |\n\n"
    b"Invented footer reference.[^invented-note]\n\n"
    b"[^invented-note]: Invented footer offset -6.25 mV.\n\n"
    b"![Invented alpha pixels](alpha.png)\n"
)


def semantic_control_source(name: str) -> bytes:
    if name not in SEMANTIC_CONTROL_CODES:
        raise ValueError("unknown source-owned semantic browser control")
    return STRUCTURE_SOURCE if list(SEMANTIC_CONTROL_CODES).index(name) >= 7 else SOURCE


def alpha_figure_bytes(*, mutant: bool = False) -> bytes:
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (160, 80), (32, 64, 144, 128))
    ImageDraw.Draw(image).rectangle((10, 10, 80, 60), fill=(240, 176, 48, 192))
    if mutant:
        image.putpixel((40, 40), (0, 0, 0, 255))
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def figure_bytes(*, mutant: bool = False) -> bytes:
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (160, 80), "#204090")
    ImageDraw.Draw(image).rectangle((10, 10, 80, 60), fill="#f0b030")
    if mutant:
        image.putpixel((1, 1), (0, 0, 0))
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def mutate_html(content: str, name: str) -> str:
    if name not in SEMANTIC_CONTROL_CODES:
        raise ValueError("unknown source-owned semantic browser control")
    if name == "changed-math":
        return content.replace("x^2", "x^3")
    if name == "changed-citation":
        return content.replace('data-cites="invented"', 'data-cites="wrong"')
    if name == "single-pixel-figure":
        return content.replace('src="figure.png"', 'src="figure.png" srcset="wrong.png 1x"')
    if name == "changed-table-cell":
        return content.replace(">-9.25<", ">-8.25<")
    if name == "changed-table-span":
        return content.replace("<td", '<td colspan="2"', 1)
    if name == "reordered-table-cell":
        return content.replace(">-9.25<", ">SWAP<").replace(">2.75<", ">-9.25<").replace(">SWAP<", ">2.75<")
    if name == "changed-footnote":
        return content.replace("footer offset -6.25", "footer offset -5.25")
    if name == "wrong-footnote-target":
        return content.replace('href="#fn1"', 'href="#fn999"')
    if name == "changed-alpha-pixel":
        return content.replace('src="alpha.png"', 'src="alpha.png" srcset="wrong-alpha.png 1x"')
    styles = {
        "hidden-math": ".math{opacity:0}",
        "hidden-table-cell": "td:first-child{visibility:hidden}",
        "hidden-footnote": "section.footnotes{visibility:hidden}",
        "opaque-footnote": "section.footnotes li{position:relative}section.footnotes li:after{content:'';position:absolute;inset:0;background:white;z-index:99}",
        "opaque-alpha-figure": 'figure:has(img[src="alpha.png"]){position:relative}figure:has(img[src="alpha.png"]):after{content:\'\';position:absolute;inset:0;background:white;z-index:99}',
        "distorted-figure": "img{width:160px;height:20px}",
        "opaque-figure": "figure{position:relative}figure:after{content:'';position:absolute;inset:0;background:white;z-index:99}",
    }
    return content.replace("</head>", f"<style>{styles[name]}</style></head>") if name in styles else content


def require_semantic_control_result(name: str, raw: dict[str, Any]) -> int:
    if name not in SEMANTIC_CONTROL_CODES or raw.get("blockers") or len(raw.get("viewports", [])) != 2:
        raise ValueError("semantic browser control omitted complete unblocked native observations")
    for viewport in raw["viewports"]:
        codes = {item["code"] for item in viewport["findings"]}
        expected = SEMANTIC_CONTROL_CODES[name]
        if viewport["blockers"] or (codes if expected is None else expected not in codes):
            raise ValueError("semantic control did not reach its intended genuine native diagnostic")
    if any(tool["exit_code"] != 0 or tool["original_exit_code"] != 0 for tool in raw["tools"]):
        raise ValueError("semantic control substituted a native process failure")
    return 0 if SEMANTIC_CONTROL_CODES[name] is None else 1


def run_semantic_control(
    root: Path, directory: Path, name: str, *, env: dict[str, str], deadline: float, run_id: str
) -> dict[str, Any]:
    from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
    from infrastructure.reporting.native_format_observer_dispatch import _chrome
    from infrastructure.rendering._web_assets import harden_mathjax_script

    for filename, content in (
        ("source.md", semantic_control_source(name)),
        ("references.bib", BIBLIOGRAPHY),
        ("figure.png", figure_bytes()),
        ("wrong.png", figure_bytes(mutant=True)),
        ("alpha.png", alpha_figure_bytes()),
        ("wrong-alpha.png", alpha_figure_bytes(mutant=True)),
    ):
        atomic_write_bytes_confined(root, directory / filename, content, mode=0o600)
    source = directory / "source.md"
    bib = directory / "references.bib"
    common = [
        str(source),
        "--from=markdown+tex_math_dollars+raw_tex+header_attributes",
        f"--bibliography={bib}",
        "--citeproc",
        "--metadata=link-citations:true",
    ]
    ast_tool = native_tool_record(
        root,
        directory,
        "pandoc",
        [*common, "--to=json"],
        env=env,
        deadline=deadline,
        run_id=run_id,
        purpose="semantic-control-ast",
    )
    html_path = directory / "pandoc.html"
    html_tool = native_tool_record(
        root,
        directory,
        "pandoc",
        [
            *common,
            "--standalone",
            "--mathjax=https://cdn.jsdelivr.net/npm/mathjax@4.0.0/tex-chtml.js",
            "-o",
            str(html_path),
        ],
        env=env,
        deadline=deadline,
        run_id=run_id,
        purpose="semantic-control-html",
    )
    if any(tool["exit_code"] != 0 or tool["original_exit_code"] != 0 for tool in (ast_tool, html_tool)):
        raise ValueError("actual source-owned semantic fixture producer failed")
    reader = SnapshotReader(root)
    ast = reader.read(ast_tool["artifact"]["path"]).json_object()["stdout"].encode()
    ast_path = directory / "source-ast.json"
    atomic_write_bytes_confined(root, ast_path, ast, mode=0o600)
    baseline = directory / "baseline.html"
    atomic_write_bytes_confined(root, baseline, html_path.read_bytes(), mode=0o600)
    harden_mathjax_script(baseline)
    original = directory / "original.html"
    atomic_write_bytes_confined(root, original, mutate_html(baseline.read_text(), name).encode(), mode=0o600)
    original_snapshot = reader.read(original.relative_to(root).as_posix())
    sources = (
        (source.relative_to(root).as_posix(), semantic_control_source(name)),
        (bib.relative_to(root).as_posix(), BIBLIOGRAPHY),
    )
    contract = semantic_content_contract_from_ast("semantic-browser-control", sources, ast)
    evidence = directory / "observation"
    evidence.mkdir(mode=0o700)
    observed = audit_browser_html(
        root,
        evidence,
        original_snapshot.content,
        contract,
        chrome=_chrome(env),
        env=env,
        deadline=deadline,
        run_id=run_id,
        artifact=original_snapshot,
    )

    def binding(path: Path) -> dict[str, str]:
        return {"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    return {
        "schema_version": "template-native-browser-semantic-control-v1",
        "name": name,
        "run_id": run_id,
        "original": binding(original),
        "baseline": binding(baseline),
        "pandoc_html": binding(html_path),
        "ast": binding(ast_path),
        "producer_tools": [ast_tool, html_tool],
        "contract": contract.to_dict(),
        "observation": observed,
        "oracle_exit_code": require_semantic_control_result(name, observed),
    }


def main() -> int:
    from infrastructure.core.execution_boundary import build_bounded_env
    from infrastructure.project.public_acceptance_evidence import write_json

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control", choices=tuple(SEMANTIC_CONTROL_CODES), required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--deadline", type=float, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    if (
        args.deadline <= time.monotonic()
        or len(args.run_id) != 32
        or any(c not in "0123456789abcdef" for c in args.run_id)
    ):
        raise ValueError("semantic browser control requires original bounded run identity")
    raw = run_semantic_control(
        args.root, args.directory, args.control, env=build_bounded_env(), deadline=args.deadline, run_id=args.run_id
    )
    write_json(args.root, args.directory / "control-observation.json", raw)
    return int(raw["oracle_exit_code"])


if __name__ == "__main__":
    sys.exit(main())
