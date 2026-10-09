"""Real isolated Chromium DOM, reflow and screenshot observations.

This observer never grants unsupported scientific or domain parity. It consumes
an admitted standalone document and a separately reconstructed source contract.
"""

from __future__ import annotations

import html
import hashlib
from io import BytesIO
import math
import time
import sys
from pathlib import Path
from typing import Any, TYPE_CHECKING, cast

if TYPE_CHECKING:
    from infrastructure.reporting.native_format_html_admitted_source import (
        AdmittedHTMLSource,
    )

from infrastructure.core.files.secure_write import (
    atomic_write_bytes_confined,
    read_bytes_confined,
)
from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_format_html_child_custody import (
    html_child_custodian,
)
from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
from infrastructure.reporting.native_format_content_contracts import (
    NativeContentContract,
    text_tokens,
)
from infrastructure.reporting.native_tool_producer import (
    current_native_producer_operation,
)
from infrastructure.reporting.release_readiness_snapshot import (
    SnapshotReader,
    ArtifactSnapshot,
)
from infrastructure.reporting.native_format_browser_structure import STRUCTURE_SCRIPT
from infrastructure.reporting.native_format_html_metadata import (
    METADATA_SCRIPT,
    inspect_html_metadata,
)
from infrastructure.reporting.native_format_html_local_paint import (
    LOCAL_PAINT_SCRIPT,
    inspect_local_paint,
)

BROWSER_SCHEMA = "template-native-browser-observation-v2"
BROWSER_POLICY: dict[str, Any] = {
    "schema_version": BROWSER_SCHEMA,
    "widths_px": [390, 1280],
    "height_px": 900,
    "max_height_px": 30000,
    "virtual_time_ms": 5000,
    "overflow_tolerance_px": 2,
    "min_body_font_px": 12,
    "network": "Fetch admits its ephemeral server and exact lock-authenticated offline CDN responses; "
    "other requests blocked",
}
OBSERVER_SCRIPT = r"""
<script>
addEventListener('load', async () => {
 if(window.MathJax?.startup?.promise) await window.MathJax.startup.promise;
 if(window.templateSourceFontsPromise) await window.templateSourceFontsPromise;
 await document.fonts.ready;
 const rows=[],textNodes=[];
 const walk=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
 while(walk.nextNode()) {
  const n=walk.currentNode,p=n.parentElement;
  if(!n.textContent.trim() || p.closest('script,style,noscript')) continue;
  const s=getComputedStyle(p), r=document.createRange();r.selectNodeContents(n);
  const ancestors=[];for(let a=p;a;a=a.parentElement)ancestors.push(a);
  const invisible=ancestors.some(a=>parseFloat(getComputedStyle(a).opacity)===0);
  const boxes=[...r.getClientRects()].map(b=>[b.x,b.y,b.width,b.height]);
  textNodes.push(n);
  rows.push({text:n.textContent,boxes,font_px:parseFloat(s.fontSize),
    footnote_id:p.closest('section.footnotes li[id],.footnotes li[id],li[role="doc-endnote"][id]')?.id||null,
    hidden:s.display==='none'||s.visibility!=='visible'||invisible,
    overflow:boxes.some(b=>b[0]<-2||b[0]+b[2]>innerWidth+2),
    clipped:ancestors.some(a=>{const st=getComputedStyle(a),c=a.getBoundingClientRect();
     return ['hidden','clip'].includes(st.overflow)&&boxes.some(b=>
       b[0]<c.x-2||b[1]<c.y-2||b[0]+b[2]>c.right+2||b[1]+b[3]>c.bottom+2);})});
 }
 /*STRUCTURE*/
 const data={tables,footnotes,footnote_refs,config_metadata,math_leaf_census,
  width:innerWidth,height:document.documentElement.scrollHeight,
  scroll_width:document.documentElement.scrollWidth,ready:document.readyState,
  source_font_buffers:window.templateSourceFontBuffers||null,
  text:rows,images:[...document.images].map(i=>{
   const b=i.getBoundingClientRect(),s=getComputedStyle(i);
   let decoded=null;
   if(i.complete&&i.naturalWidth>0&&i.naturalWidth*i.naturalHeight<=4000000)try{
    const c=document.createElement('canvas');c.width=i.naturalWidth;c.height=i.naturalHeight;
    c.getContext('2d').drawImage(i,0,0);decoded=c.toDataURL('image/png');}catch(e){}
   const ancestors=[];for(let a=i;a;a=a.parentElement)ancestors.push(a);
   return {src:i.getAttribute('src'),alt:i.getAttribute('alt'),alt_present:i.hasAttribute('alt'),
    complete:i.complete,width:i.naturalWidth,height:i.naturalHeight,
    decoded_png:decoded,box:[b.x,b.y,b.width,b.height],
    background_layers:ancestors.map(a=>{const z=getComputedStyle(a);return {
     color:z.backgroundColor,image:z.backgroundImage,opacity:z.opacity}}),
    presentation:{filter:s.filter,transform:s.transform,mix_blend_mode:s.mixBlendMode,object_fit:s.objectFit,opacity:s.opacity},
    hidden:s.display==='none'||s.visibility!=='visible'||ancestors.some(a=>parseFloat(getComputedStyle(a).opacity)===0),
    clipped:ancestors.some(a=>{const st=getComputedStyle(a),c=a.getBoundingClientRect();
     return ['hidden','clip'].includes(st.overflow)&&
     (b.x<c.x-2||b.y<c.y-2||b.right>c.right+2||b.bottom>c.bottom+2);})};}),
  math:[...document.querySelectorAll('.math')].map(e=>({text:e.textContent,
   rendered:!!e.querySelector('mjx-container,math'),font_px:parseFloat(getComputedStyle(e).fontSize),
   box:(b=>[b.x,b.y,b.width,b.height])(e.getBoundingClientRect())})),
  assets:[...document.querySelectorAll('script[src],link[href]')].map(e=>e.src||e.href),
  source_math:window.MathJax?.startup?.document ? [...window.MathJax.startup.document.math].map(m=>m.math) : [],
  math_errors:document.querySelectorAll('mjx-merror,.MathJax_Error').length,
  citations:[...document.querySelectorAll('.citation[data-cites]')].map(c=>c.getAttribute('data-cites').split(/\s+/)),
  links:[...document.querySelectorAll('a[href]')].map(a=>a.getAttribute('href'))};
 const out=document.createElement('pre');out.id='native-browser-observation';
 out.hidden=true;out.textContent=JSON.stringify(data);document.body.append(out);
});
</script>
""".replace("/*STRUCTURE*/", STRUCTURE_SCRIPT + METADATA_SCRIPT + LOCAL_PAINT_SCRIPT)


def inspect_browser_dom(
    dom: dict[str, Any],
    contract: NativeContentContract,
    metadata_source: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Recompute semantic and viewport diagnostics from actual DOM observations."""
    if dom.get("ready") != "complete" or dom.get("width") not in BROWSER_POLICY["widths_px"]:
        raise ValueError("browser did not complete its declared viewport")
    rows = dom.get("text")
    if not isinstance(rows, list) or not rows:
        raise ValueError("actual browser omitted source text observations")
    tokens: list[str] = []
    owners: list[int] = []
    for i, row in enumerate(rows):
        if not isinstance(row, dict) or not isinstance(row.get("text"), str):
            raise ValueError("invalid browser text observation")
        if row.get("footnote_id"):
            continue
        current = text_tokens(row["text"])
        tokens.extend(current)
        owners.extend([i] * len(current))
    findings: list[dict[str, Any]] = []
    cursor = 0
    required: set[int] = set()
    for block in contract.blocks:
        match = next(
            (
                i
                for i in range(cursor, len(tokens) - len(block.tokens) + 1)
                if tuple(tokens[i : i + len(block.tokens)]) == block.tokens
            ),
            None,
        )
        if match is None:
            findings.append({"code": "html.content.missing", "block_id": block.id})
        else:
            required.update(owners[match : match + len(block.tokens)])
            cursor = match + len(block.tokens)
    for i, image in enumerate(dom["images"]):
        if not image["complete"] or min(image["width"], image["height"]) <= 0:
            findings.append({"code": "html.asset.image", "image_index": i})
    for i, equation in enumerate(dom["math"]):
        if not equation["rendered"]:
            findings.append({"code": "html.asset.math", "math_index": i})
    from infrastructure.reporting.native_format_content_contracts import (
        SemanticContentContract,
    )

    structure: dict[str, Any] | None = None
    if isinstance(contract, SemanticContentContract):
        from infrastructure.reporting.native_format_browser_structure import (
            inspect_browser_structure,
        )

        structure = inspect_browser_structure(dom, contract)
        findings.extend(structure["findings"])
        required.update(structure["source_text_indices"])
        expected_math = [tex for _, tex in contract.mathematical_sources]
        if dom.get("source_math") != expected_math:
            findings.append({"code": "html.math.source"})
        if dom.get("citations", []) != [list(keys) for _, keys in contract.citation_sources]:
            findings.append({"code": "html.citation.source"})
        if dom.get("math_errors"):
            findings.append({"code": "html.math.error"})
        for identity, target in contract.link_sources:
            if target not in dom.get("links", []):
                findings.append({"code": "html.link.source", "source_id": identity})
        used_images: set[int] = set()
        for identity, target, alt in contract.image_sources:
            selected = next(
                (
                    index
                    for index, image in enumerate(dom["images"])
                    if index not in used_images and image["src"] == target
                ),
                None,
            )
            if selected is None:
                findings.append({"code": "html.figure.source", "source_id": identity})
                continue
            used_images.add(selected)
            image = dom["images"][selected]
            if type(image.get("alt_present")) is not bool:
                raise ValueError("actual native browser omitted image alt presence")
            if alt and (not image["alt_present"] or image.get("alt") != alt):
                findings.append(
                    {
                        "code": "html.figure.alt",
                        "source_id": identity,
                        "image_index": selected,
                    }
                )
    metadata = inspect_html_metadata(dom, metadata_source) if metadata_source is not None else None
    if metadata is not None:
        findings.extend(metadata["findings"])
        required.update(metadata["source_text_indices"])
    for i in sorted(required):
        row = rows[i]
        if row["hidden"] or not row["boxes"]:
            findings.append({"code": "html.visual.hidden", "text_index": i})
        if row["clipped"]:
            findings.append({"code": "html.layout.clip", "text_index": i})
        if row["overflow"]:
            findings.append({"code": "html.layout.overflow", "text_index": i})
        if not math.isfinite(row["font_px"]) or row["font_px"] < BROWSER_POLICY["min_body_font_px"]:
            findings.append({"code": "html.layout.font", "text_index": i})
    blockers = list(contract.blockers)
    if structure is not None:
        blockers.extend(structure["blockers"])
    if metadata is not None:
        blockers.extend(metadata["blockers"])
    return {
        "findings": findings,
        "source_text_indices": sorted(required),
        "structure": structure,
        "metadata": metadata,
        "blockers": blockers,
        "status": "fail" if findings else "blocked" if blockers else "pass",
    }


def inspect_browser_pixels(dom: dict[str, Any], pixels: bytes, indices: list[int]) -> dict[str, Any]:
    """Observe actual fullpage pixels at every required text-line region."""
    from PIL import Image

    findings = []
    regions = []
    with Image.open(BytesIO(pixels)) as image:
        image.load()
        gray = image.convert("L")
        for index in indices:
            for box in dom["text"][index]["boxes"]:
                x, y, width, height = box
                if not all(math.isfinite(v) for v in box):
                    raise ValueError("native DOM text has nonfinite geometry")
                # Boundary pixels can contain ink outside the fractional DOM
                # range, including exposed descenders beneath an opaque cover.
                # Require contrast among pixels wholly inside the source box.
                roi = (
                    max(0, math.ceil(x)),
                    max(0, math.ceil(y)),
                    min(image.width, math.floor(x + width)),
                    min(image.height, math.floor(y + height)),
                )
                if roi[0] >= roi[2] or roi[1] >= roi[3]:
                    findings.append({"code": "html.visual.outside", "text_index": index})
                    continue
                low, high = cast(tuple[int, int], gray.crop(roi).getextrema())
                regions.append(
                    {
                        "text_index": index,
                        "box_px": list(roi),
                        "luminance_range": high - low,
                    }
                )
                if high - low < 32:
                    findings.append({"code": "html.visual.invisible", "text_index": index})
    from infrastructure.reporting.native_format_browser_figures import (
        inspect_browser_math_pixels,
    )

    maths = inspect_browser_math_pixels(dom, pixels)
    findings.extend(maths["findings"])
    local = inspect_local_paint(dom, pixels, indices)
    findings.extend(local["findings"])
    return {
        "regions": regions,
        "findings": findings,
        "math_regions": maths["regions"],
        "localized": local,
        "blockers": local["blockers"],
    }


def audit_browser_html(
    root: Path,
    directory: Path,
    html_bytes: bytes,
    contract: NativeContentContract,
    *,
    chrome: str,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    artifact: ArtifactSnapshot | None = None,
    metadata_source: dict[str, Any] | None = None,
    admitted_source: AdmittedHTMLSource | None = None,
) -> dict[str, Any]:
    """Run fresh native browser processes; bind input, process and pixel bytes.

    Caller must provide a private fresh evidence directory. Local relative assets
    remain blocked here until a source-owned asset manifest admits their closure.
    """
    if deadline <= time.monotonic() or b"native-browser-observation" in html_bytes:
        raise ValueError("browser requires fresh bounded non-observer input")
    from infrastructure.reporting.native_format_html_source_metadata import (
        remaining_seconds,
    )

    remaining_seconds(deadline)
    if admitted_source is not None and metadata_source != admitted_source.metadata:
        raise ValueError("HTML config witness differs from admitted original source operation")
    mirror = directory / "mirror"
    source_reader = SnapshotReader(root, native_producer_operation=current_native_producer_operation())
    asset_contract: dict[str, Any] = {
        "schema_version": "template-native-browser-assets-v1",
        "assets": [],
        "blockers": [],
    }
    if artifact:
        if artifact.content != html_bytes:
            raise ValueError("browser source bytes differ from admitted artifact")
        from infrastructure.reporting.native_format_browser_assets import (
            compile_browser_assets,
        )

        original = source_reader.read(artifact.relative)
        if original.content != html_bytes:
            raise ValueError("browser original artifact changed before admission")
        asset_contract = compile_browser_assets(root, original, source_reader)
    source = mirror / (artifact.relative if artifact else "admitted.html")
    source.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_bytes_confined(root, source, html_bytes, mode=0o600)
    observer_path = directory / "observer.js"
    observer_script = OBSERVER_SCRIPT
    if admitted_source is not None:
        from infrastructure.reporting.native_format_html_browser_extensions import (
            extend_browser_observer_script,
        )

        observer_script = extend_browser_observer_script(observer_script)
    script = observer_script.removeprefix("\n<script>\n").removesuffix("\n</script>\n")
    atomic_write_bytes_confined(root, observer_path, script.encode(), mode=0o600)
    driver_source = Path(__file__).with_name("native_format_browser_driver.py")
    driver_bytes = read_bytes_confined(driver_source.parent, driver_source, max_bytes=1024 * 1024)
    driver_path = directory / "browser-driver.py"
    atomic_write_bytes_confined(root, driver_path, driver_bytes, mode=0o600)
    runtime_source = driver_source.with_name("native_format_browser_runtime.py")
    runtime_bytes = read_bytes_confined(runtime_source.parent, runtime_source, max_bytes=1024 * 1024)
    atomic_write_bytes_confined(root, directory / "native_format_browser_runtime.py", runtime_bytes, mode=0o600)
    reader = SnapshotReader(root, native_producer_operation=current_native_producer_operation())
    input_snapshot = reader.read(source.relative_to(root).as_posix())
    reader.read(observer_path.relative_to(root).as_posix())
    reader.read(driver_path.relative_to(root).as_posix())
    reader.read((directory / "native_format_browser_runtime.py").relative_to(root).as_posix())
    font_observer = None
    if admitted_source is not None:
        from infrastructure.reporting.native_format_html_font_driver_adapter import (
            bind_html_font_driver,
        )

        font_observer = bind_html_font_driver(root, directory, reader, deadline=deadline)
    consumed_assets = []
    for binding in asset_contract["assets"]:
        snapshot = source_reader.read(binding["path"])
        target = mirror / snapshot.relative
        target.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_bytes_confined(root, target, snapshot.content, mode=0o600)
        consumed = reader.read(target.relative_to(root).as_posix())
        consumed_assets.append(
            {
                "source": binding,
                "consumed": {"path": consumed.relative, "sha256": consumed.sha256},
            }
        )
    cdn_map = directory / "cdn-map.json"
    cdn_bindings = []
    if asset_contract.get("cdn_assets"):
        import json
        from infrastructure.reporting.native_format_browser_cdn import cdn_member_bytes

        mapping = {}
        for index, row in enumerate(asset_contract["cdn_assets"]):
            target = mirror / f"native-cdn/{index:04d}"
            target.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_bytes_confined(root, target, cdn_member_bytes(row, source_reader), mode=0o600)
            mapping[row["url"]] = {
                "path": target.relative_to(mirror).as_posix(),
                "sha256": row["sha256"],
            }
            copy = reader.read(target.relative_to(root).as_posix())
            cdn_bindings.append(
                {
                    "url": row["url"],
                    "consumed": {"path": copy.relative, "sha256": copy.sha256},
                }
            )
        atomic_write_bytes_confined(root, cdn_map, json.dumps(mapping, sort_keys=True).encode(), mode=0o600)
        reader.read(cdn_map.relative_to(root).as_posix())
    tools: list[dict[str, Any]] = []
    viewports = []
    for width in BROWSER_POLICY["widths_px"]:
        profile = directory / f"profile-{width}"
        if profile.exists():
            raise ValueError("native browser must not reuse a profile")
        result_path = directory / f"browser-result-{width}.json"
        args = [
            str(driver_path),
            "--chrome",
            chrome,
            "--source",
            str(source),
            "--profile",
            str(profile),
            "--width",
            str(width),
            "--output",
            str(result_path),
            "--deadline",
            str(deadline),
            "--observer-script",
            str(observer_path),
            "--asset-root",
            str(mirror),
        ]
        if font_observer is not None:
            args.extend(
                [
                    "--platform-font-observer",
                    str(directory / "native_format_html_platform_font_dom.py"),
                ]
            )
        if cdn_bindings:
            args.extend(["--cdn-map", str(cdn_map)])
        with html_child_custodian(directory, directory, deadline=deadline, artifact_root=root):
            record = native_tool_record(
                root,
                directory,
                sys.executable,
                args,
                env=env,
                deadline=deadline,
                run_id=run_id,
                purpose=f"browser-cdp-{width}",
            )
        if record["exit_code"] != 0 or record["original_exit_code"] != 0:
            process = reader.read(record["artifact"]["path"]).json_object()
            diagnostic = {
                "artifact": record["artifact"],
                "exit_code": process.get("exit_code"),
                "original_exit_code": process.get("original_exit_code"),
                "diagnostic": process.get("diagnostic"),
                "stderr_tail": str(process.get("stderr", ""))[-2048:],
            }
            raise ValueError("actual native browser driver failed: " + json.dumps(diagnostic, sort_keys=True))
        driver = reader.read(result_path.relative_to(root).as_posix()).json_object()
        if driver["browser_original_exit"] != 0:
            raise ValueError("native browser did not exit successfully")
        if font_observer is not None:
            from infrastructure.reporting.native_format_html_font_driver_adapter import (
                replay_html_font_driver,
            )

            replay_html_font_driver(root, directory, reader, font_observer, driver, deadline=deadline)
        dom = driver["dom"]
        result = inspect_browser_dom(dom, contract, metadata_source)
        screenshot = result_path.with_suffix(".png")
        pixel_snapshot = reader.read(screenshot.relative_to(root).as_posix())
        from infrastructure.reporting.native_format_acceptance_checks import (
            parse_native_bytes,
        )

        dimensions = parse_native_bytes("png", pixel_snapshot.content)
        if dimensions["width_px"] != width or dimensions["height_px"] < dom["height"]:
            raise ValueError("native screenshot omitted page geometry")
        pixel_observation = inspect_browser_pixels(dom, pixel_snapshot.content, result["source_text_indices"])
        from infrastructure.reporting.native_format_browser_figures import (
            inspect_browser_figures,
        )

        figures = inspect_browser_figures(dom, pixel_snapshot.content, contract, artifact, source_reader)
        result["figures"] = figures
        result["findings"].extend(figures["findings"])
        result["blockers"].extend(figures["blockers"])
        result["pixels"] = pixel_observation
        result["findings"].extend(pixel_observation["findings"])
        result["blockers"].extend(pixel_observation["blockers"])
        if admitted_source is not None:
            if artifact is None:
                raise ValueError("source-bound HTML fidelity requires its original artifact locator")
            from infrastructure.reporting.native_format_html_fidelity_observer import (
                observe_html_fidelity,
            )

            fidelity = observe_html_fidelity(
                root,
                directory / f"fidelity-{width}",
                admitted_source,
                dom,
                pixel_snapshot.content,
                artifact,
                reader,
                chrome=chrome,
                env=env,
                deadline=deadline,
                run_id=run_id,
            )
            result["fidelity"] = fidelity
            result["findings"].extend(fidelity["findings"])
            result["blockers"].extend(fidelity["blockers"])
        result["status"] = "fail" if result["findings"] else "blocked" if result["blockers"] else result["status"]
        result["screenshot"] = {
            "path": pixel_snapshot.relative,
            "sha256": pixel_snapshot.sha256,
            **dimensions,
        }
        result["driver"] = {
            "path": result_path.relative_to(root).as_posix(),
            "sha256": reader.read(result_path.relative_to(root).as_posix()).sha256,
        }
        tools.append(record)
        viewports.append({"dom": dom, **result})
    if (
        not reader.unchanged()
        or not source_reader.unchanged()
        or read_bytes_confined(driver_source.parent, driver_source, max_bytes=1024 * 1024) != driver_bytes
    ):
        raise ValueError("admitted browser inputs changed during execution")
    if admitted_source is not None:
        admitted_source.close(root, reader, deadline=deadline)
    observation = {
        "schema_version": BROWSER_SCHEMA,
        "input": {"path": input_snapshot.relative, "sha256": input_snapshot.sha256},
        "driver_source_sha256": hashlib.sha256(driver_bytes).hexdigest(),
        "runtime_source_sha256": hashlib.sha256(runtime_bytes).hexdigest(),
        "observer_script_sha256": hashlib.sha256(observer_script.encode()).hexdigest(),
        "contract_digest": contract.digest,
        "metadata_source_digest": metadata_source["digest"] if metadata_source is not None else None,
        "fidelity_source_digest": admitted_source.fidelity["digest"] if admitted_source is not None else None,
        "font_observer": font_observer,
        "policy_digest": canonical_digest(BROWSER_POLICY),
        "deadline_monotonic": deadline,
        "asset_contract": asset_contract,
        "consumed_assets": consumed_assets,
        **({"consumed_cdn": cdn_bindings} if cdn_bindings else {}),
        "tools": tools,
        "viewports": viewports,
        "blockers": sorted(
            set(
                [
                    *contract.blockers,
                    *asset_contract["blockers"],
                    *(b for v in viewports for b in v["blockers"]),
                ]
            )
        ),
        "status": "fail"
        if any(v["findings"] for v in viewports)
        else "blocked"
        if any(v["blockers"] for v in viewports) or asset_contract["blockers"]
        else "pass",
    }

    remaining_seconds(deadline)
    return observation


BROWSER_CONTROL_CODES = {
    "baseline": None,
    "changed-number": "html.content.missing",
    "hidden-text": "html.visual.hidden",
    "tiny-text": "html.layout.font",
    "overflow-text": "html.layout.overflow",
    "broken-image": "html.asset.image",
    "clipped-text": "html.layout.clip",
    "opaque-overlay": "html.visual.invisible",
}


def browser_control_bytes(name: str) -> bytes:
    """Valid public HTML controls retain successful native browser execution."""
    if name not in BROWSER_CONTROL_CODES:
        raise ValueError("unknown browser control")
    value = "-8.25" if name == "changed-number" else "-3.25"
    style = {
        "hidden-text": "visibility:hidden",
        "tiny-text": "font-size:5px",
        "overflow-text": "position:absolute;left:2000px",
        "clipped-text": "height:0;overflow:hidden",
    }.get(name, "")
    image = '<img src="missing-public-control.png" alt="Invented control">' if name == "broken-image" else ""
    overlay = (
        '<style>p{position:relative}p::after{content:"";position:absolute;inset:0;background:white}</style>'
        if name == "opaque-overlay"
        else ""
    )
    return (
        f'<!doctype html><html><head><meta name="viewport" content="width=device-width">'
        f"<style>body{{font:16px Arial}}</style></head><body><h1>Invented public measurement</h1>"
        f'<p style="{html.escape(style)}">Measured offset {value} mV.</p>{image}{overlay}</body></html>'
    ).encode()


def browser_control_contract() -> NativeContentContract:
    """Exact independently authored source for all real valid HTML controls."""
    from infrastructure.reporting.native_format_content_contracts import (
        content_contract_from_bytes,
    )

    return content_contract_from_bytes(
        "invented-control:html",
        (
            (
                "invented-public-control.md",
                b"# Invented public measurement\n\nMeasured offset -3.25 mV.\n",
            ),
        ),
    )


def require_browser_control_result(name: str, observation: dict[str, Any]) -> int:
    """Only actual successful native execution with the intended fault counts."""
    expected = {
        "baseline": set(),
        "changed-number": {"html.content.missing"},
        "hidden-text": {"html.visual.hidden", "html.visual.invisible"},
        "tiny-text": {"html.layout.font"},
        "overflow-text": {"html.layout.overflow", "html.visual.outside"},
        "broken-image": {"html.asset.image"},
        "clipped-text": {"html.layout.clip", "html.visual.invisible"},
        "opaque-overlay": {"html.visual.invisible"},
    }
    if name not in expected or observation.get("schema_version") != BROWSER_SCHEMA:
        raise ValueError("unknown valid browser control observation")
    viewports = observation.get("viewports")
    if not isinstance(viewports, list) or [item["dom"]["width"] for item in viewports] != BROWSER_POLICY["widths_px"]:
        raise ValueError("browser control omitted actual required viewports")
    for viewport in viewports:
        codes = {item["code"] for item in viewport["findings"]}
        if viewport["blockers"] or codes != expected[name] or viewport["status"] != ("fail" if codes else "pass"):
            raise ValueError("browser control did not reach its exact intended original diagnostic")
    if any(item["exit_code"] != 0 or item["original_exit_code"] != 0 for item in observation["tools"]):
        raise ValueError("browser control substituted a setup/process failure for its intended diagnostic")
    return 0 if name == "baseline" else 1


def main() -> int:
    """Execute a real valid native control with its actual oracle process exit."""
    import argparse
    from infrastructure.core.execution_boundary import build_bounded_env
    from infrastructure.project.public_acceptance_evidence import write_json
    from infrastructure.reporting.native_format_observer_dispatch import _chrome

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control", choices=tuple(BROWSER_CONTROL_CODES), required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--deadline", type=float, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    if len(args.run_id) != 32 or any(c not in "0123456789abcdef" for c in args.run_id):
        raise ValueError("browser control requires admitted original run nonce")
    env = build_bounded_env()
    observation = audit_browser_html(
        args.root,
        args.directory,
        browser_control_bytes(args.control),
        browser_control_contract(),
        chrome=_chrome(env),
        env=env,
        deadline=args.deadline,
        run_id=args.run_id,
    )
    code = require_browser_control_result(args.control, observation)
    write_json(
        args.root,
        args.directory / "control-observation.json",
        {
            "schema_version": "template-native-browser-valid-control-v1",
            "name": args.control,
            "run_id": args.run_id,
            "observation": observation,
            "oracle_exit_code": code,
        },
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
