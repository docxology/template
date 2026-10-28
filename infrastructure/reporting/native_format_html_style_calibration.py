"""Actual independent Source writer/UA style expectations, never candidate px.

The Source-owned role markup passes through the actual standalone Pandoc html5
writer, the admitted stylesheet and unchanged licensed Source font buffers.
The genuine original/browser/portable custody remains in the existing ToolAPI.
"""

from __future__ import annotations

import copy
import hashlib
import math
import re
import tempfile
import time
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.rendering._web_font_assets import source_web_font_script
from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory
from infrastructure.reporting.native_format_html_admitted_source import AdmittedHTMLSource
from infrastructure.reporting.native_format_html_reference_runtime import (
    observe_glyph_reference,
    replay_glyph_reference,
)
from infrastructure.reporting.native_format_html_source_metadata import binding, remaining_seconds
from infrastructure.reporting.native_format_html_source_styles import SOURCE_UA_CALIBRATION_BLOCKER
from infrastructure.reporting.native_format_portable_custody import producer_path
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.reporting.native_tool_process import run_native_tool_process

CALIBRATION_SCRIPT = r"""
addEventListener('load',async()=>{
 if(window.templateSourceFontsPromise)await window.templateSourceFontsPromise;
 await document.fonts.ready;
 const rows=[],nodes=[];
 for(const element of document.querySelectorAll('[data-source-style]')){
  const node=element.firstChild,range=document.createRange();range.selectNodeContents(node);
  const box=range.getBoundingClientRect(),style=getComputedStyle(element);
  nodes.push(node);rows.push({source_id:element.dataset.sourceStyle,text:node.textContent,
   box:[box.x,box.y,box.width,box.height],font_px:parseFloat(style.fontSize),
   font_weight:style.fontWeight,font_style:style.fontStyle,font_family:style.fontFamily,
   color:style.color,kerning:style.fontKerning,ligatures:style.fontVariantLigatures});
 }
 globalThis.__native_glyph_text_nodes=nodes;
 const result={ready:document.readyState,width:innerWidth,height:document.documentElement.scrollHeight,
  text:rows,source_font_buffers:window.templateSourceFontBuffers||null};
 const output=document.createElement('pre');output.id='native-browser-observation';output.hidden=true;
 output.textContent=JSON.stringify(result);document.body.append(output);
});
"""


def _key(style: dict[str, Any]) -> str:
    return canonical_digest({key: value for key, value in style.items() if key != "independent_font_px"})


def _color(value: str) -> str:
    """Compare the finite authored Source colors with actual UA serialization."""
    colors = {"white": "#ffffff", "black": "#000000"}
    value = colors.get(value, value)
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise ValueError("independent Source style color has no finite authored model")
    channels = [int(value[index : index + 2], 16) for index in (1, 3, 5)]
    return "rgb(" + ", ".join(str(channel) for channel in channels) + ")"


def source_style_markup(source: dict[str, Any], *, deadline: float) -> bytes:
    """Derive original tag roles and symbolic defaults before any observation."""
    remaining_seconds(deadline)
    characters = source["characters"]
    profile = characters["source_style_profile"]
    if profile.get("font_provider") != "source-web-font-assets-v1":
        raise ValueError("Source UA/style calibration needs its independently admitted physical body cohort")
    styles = {_key(run["source_style"]): run["source_style"] for run in characters["runs"]}
    if not 0 < len(styles) <= 4096:
        raise ValueError("Source UA/style calibration exceeds its finite original role cohort")
    blocks = []
    for key, style in styles.items():
        ancestry = style["original_ancestry"]
        text = f'<span data-source-style="{key}">AV office é</span>'
        if "Emph" in ancestry:
            text = "<em>" + text + "</em>"
        if "Strong" in ancestry:
            text = "<strong>" + text + "</strong>"
        if "Link" in ancestry:
            text = '<a href="#source-calibration">' + text + "</a>"
        if "CodeBlock" in ancestry:
            text = '<pre class="sourceCode"><code class="sourceCode">' + text + "</code></pre>"
        elif "Code" in ancestry:
            text = "<code>" + text + "</code>"
        header = next((role for role in ancestry if role.startswith("Header:")), None)
        if header:
            level = int(header.split(":")[1])
            if not 1 <= level <= 6:
                raise ValueError("Source heading role exceeds its declared writer model")
            text = f"<h{level}>" + text + f"</h{level}>"
        elif "TableHead" in ancestry:
            text = "<table><thead><tr><th>" + text + "</th></tr></thead></table>"
        elif "TableRowHead" in ancestry:
            text = "<table><tbody><tr><th>" + text + "</th></tr></tbody></table>"
        elif "CodeBlock" not in ancestry:
            text = "<p>" + text + "</p>"
        blocks.append(text)
    result = ("\n\n".join(blocks) + "\n").encode()
    if len(result) > 1024 * 1024:
        raise ValueError("Source writer/style markup exceeds its finite input bound")
    remaining_seconds(deadline)
    return result


def _args(path: Path) -> list[str]:
    # The existing renderer's actual standalone writer and default stylesheet;
    # no template, CSS or font-size expectation is extracted from candidate HTML.
    return [
        str(path),
        "--from=markdown+raw_html",
        "--to=html5",
        "--standalone",
        "--metadata=title:Source style calibration",
    ]


def _page(source: dict[str, Any], template: bytes, *, deadline: float) -> bytes:
    remaining_seconds(deadline)
    if len(template) > 8 * 1024 * 1024:
        raise ValueError("Source writer style template exceeds its finite output bound")
    text = template.decode("utf-8")
    profile = source["characters"]["source_style_profile"]
    css = profile["stylesheet_text"]
    if hashlib.sha256(css.encode()).hexdigest() != profile["stylesheet_sha256"] or "</head>" not in text:
        raise ValueError("Source style template lacks the original admitted stylesheet/head")
    # Same Source font loader and actual authored CSS as the renderer. The native
    # writer template supplies its own defaults; a candidate supplies none.
    page = text.replace("</head>", "<style>" + css + "</style>" + source_web_font_script() + "</head>", 1).encode()
    remaining_seconds(deadline)
    return page


def apply_source_style_calibration(
    source: dict[str, Any], observed: dict[str, Any], *, deadline: float
) -> dict[str, Any]:
    """Bind independent actual styles to original roles; preserve other blockers."""
    remaining_seconds(deadline)
    profile = source["characters"]["source_style_profile"]
    expected_buffers = [
        {"schema_version": "template-source-web-font-buffer-v1", **row} for row in profile["physical_font_assets"]
    ]
    if observed.get("source_font_buffers") != expected_buffers or observed.get("ready") != "complete":
        raise ValueError("Source style calibration lacks genuine complete fixed buffer consumption")
    styles = {_key(run["source_style"]): run["source_style"] for run in source["characters"]["runs"]}
    rows = observed.get("text")
    if not isinstance(rows, list) or len(rows) != len(styles) or {row["source_id"] for row in rows} != set(styles):
        raise ValueError("independent Source style calibration omits/duplicates original roles")
    values = {}
    for row in rows:
        expected = styles[row["source_id"]]
        px = row["font_px"]
        if type(px) not in (int, float) or not math.isfinite(px) or not 0 < px <= 128:
            raise ValueError("independent Source UA/style font size exceeds its original bound")
        if any(row[key] != expected[key] for key in ("font_weight", "font_style")):
            raise ValueError("independent Source tag/writer UA disagrees with authored style ancestry")
        if row.get("text") != "AV office é" or row.get("color") != _color(expected["authored_color"]):
            raise ValueError("independent Source writer/UA text or color differs from the authored roles")
        fonts = row.get("platform_fonts")
        if (
            not isinstance(fonts, list)
            or len(fonts) != 1
            or fonts[0].get("postScriptName") != expected["expected_postscript_name"]
        ):
            raise ValueError("independent Source UA/style consumed an unexpected physical face")
        values[row["source_id"]] = float(px)
    result = copy.deepcopy(source)
    characters = result["characters"]
    characters.pop("digest")
    if SOURCE_UA_CALIBRATION_BLOCKER not in characters["blockers"]:
        raise ValueError("independent Source style calibration omitted its original explicit UA obligation")
    characters["blockers"].remove(SOURCE_UA_CALIBRATION_BLOCKER)
    for run in characters["runs"]:
        run["source_style"]["independent_font_px"] = values[_key(run["source_style"])]
    characters["digest"] = canonical_digest(characters)
    result.pop("digest")
    result["independent_style_calibration"] = {
        "writer_default_contract": profile["default_style_contract"],
        "Source_role_font_px": values,
    }
    result["digest"] = canonical_digest(result)
    remaining_seconds(deadline)
    return result


def observe_source_styles(
    root: Path,
    directory: Path,
    admitted: AdmittedHTMLSource,
    reader: SnapshotReader,
    *,
    chrome: str,
    width: int,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """The actual producer executes Source Pandoc and original audited browser."""
    admitted.close(root, reader, deadline=deadline)
    create_private_native_directory(root, directory)
    markup = source_style_markup(admitted.fidelity, deadline=deadline)
    path = directory / "source-style.md"
    atomic_write_bytes_confined(root, path, markup, mode=0o600)
    held = reader.read(path.relative_to(root).as_posix())
    args = _args(path)
    tool = native_tool_record(
        root, directory, "pandoc", args, env=env, deadline=deadline, run_id=run_id, purpose="html-source-style-template"
    )
    from infrastructure.reporting.native_format_acceptance_evidence import _tool

    transcript = _tool(tool["artifact"], reader, run_id, "pandoc", "html-source-style-template", args)
    template = transcript["stdout"].encode()
    page = _page(admitted.fidelity, template, deadline=deadline)
    browser = directory / "source-style-reference"
    create_private_native_directory(root, browser)
    dom, _, native = observe_glyph_reference(
        root,
        browser,
        page,
        width,
        reader,
        chrome=chrome,
        env=env,
        deadline=deadline,
        run_id=run_id,
        observer_script=CALIBRATION_SCRIPT,
    )
    calibrated = apply_source_style_calibration(admitted.fidelity, dom, deadline=deadline)
    admitted.close(root, reader, deadline=deadline)
    return calibrated, {
        "markup": binding(held),
        "template_tool": tool,
        "template_sha256": hashlib.sha256(template).hexdigest(),
        "reference": native,
        "deadline_monotonic": deadline,
    }


def replay_source_styles(
    root: Path,
    directory: Path,
    admitted: AdmittedHTMLSource,
    raw: dict[str, Any],
    reader: SnapshotReader,
    *,
    run_id: str,
    custody: dict[str, str],
    runtime: dict[str, Any],
    chrome: str,
    width: int,
    env: dict[str, str],
    deadline: float,
) -> dict[str, Any]:
    """Authenticate original Source-only native custody, then re-render freshly."""
    from infrastructure.reporting.native_format_acceptance_evidence import _file, _tool

    admitted.close(root, reader, deadline=deadline)
    markup = source_style_markup(admitted.fidelity, deadline=deadline)
    held = _file(raw["markup"], reader)
    path = directory / "source-style.md"
    if held.path != path or held.content != markup:
        raise ValueError("original Source-only style markup differs from current admitted roles")
    command = _args(producer_path(custody, root, path))
    original = _tool(raw["template_tool"]["artifact"], reader, run_id, "pandoc", "html-source-style-template", command)
    template = original["stdout"].encode()
    if hashlib.sha256(template).hexdigest() != raw["template_sha256"]:
        raise ValueError("original Source writer default template differs from authentic raw stdout")
    page = _page(admitted.fidelity, template, deadline=deadline)
    work = Path(tempfile.mkdtemp(prefix="native-html-source-style-reader-"))
    local = work / "source-style.md"
    local.write_bytes(markup)
    remaining_seconds(deadline)
    process = run_native_tool_process(
        work,
        "pandoc",
        _args(local),
        cwd=work,
        env=env,
        deadline=min(deadline, time.monotonic() + 120),
        purpose="reader-html-source-style-template",
    )
    if process["original_exit_code"] != 0 or not process["accepted"] or process["timed_out"]:
        raise ValueError("independent Source style writer did not preserve genuine original exit0")
    if process["stdout"].encode() != template:
        raise ValueError("independent current Source writer default stylesheet/template differs")
    browser = work / "reference"
    browser.mkdir(mode=0o700)
    dom, _ = replay_glyph_reference(
        root,
        directory / "source-style-reference",
        page,
        width,
        raw["reference"],
        reader,
        run_id=run_id,
        custody=custody,
        runtime=runtime,
        env=env,
        deadline=deadline,
        work=browser,
        chrome=chrome,
        observer_script=CALIBRATION_SCRIPT,
    )
    calibrated = apply_source_style_calibration(admitted.fidelity, dom, deadline=deadline)
    admitted.close(root, reader, deadline=deadline)
    return calibrated
