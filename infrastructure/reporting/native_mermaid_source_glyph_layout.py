"""Actual Source-only label layout, separate from physical font authority.

SVG character baselines/rotations and HTML text ranges are observed while the
real supervised Source browser is live. These observations can position held
Source glyph contours; they do not claim Chrome's selected glyph IDs, cached
font bytes or shaping engine equivalence. Every original text owner is kept.
"""

from __future__ import annotations

from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_browser_driver import DevTools
from infrastructure.reporting.native_tool_process import NativeLiveToolProcess

SCHEMA = "template-native-original-source-svg-label-layout-v1"
_LAYOUT = r"""(async()=>{
await document.fonts.ready;
const svg=document.querySelector('svg');
const elements=[svg,...svg.querySelectorAll('*')];
if(elements.length>20000)throw Error('Source label element budget');
const box=r=>({x:r.x,y:r.y,width:r.width,height:r.height});
const owners=[];let characters=0;let positions=0;
for(let index=0;index<elements.length;index++){
 const element=elements[index];
 if(['style','title','desc'].includes(element.localName))continue;
 const nodes=[...element.childNodes].filter(n=>n.nodeType===3);
 const text=nodes.map(n=>n.textContent).join('');
 if(!text.trim())continue;
 if(text.length>100000||(characters+=text.length)>200000||owners.length>=1000)
  throw Error('Source label character/owner budget');
 const style=getComputedStyle(element);
 const row={owner_index:owners.length,element_index:index-1,tag:element.localName,
  id:element.id,text,box:box(element.getBoundingClientRect()),
  style:Object.fromEntries(['fontFamily','fontSize','fontWeight','fontStyle','fontStretch',
   'fontKerning','fontVariantLigatures','fontFeatureSettings','fontVariationSettings',
   'letterSpacing','wordSpacing','lineHeight','whiteSpace','textTransform','direction',
   'writingMode','textAnchor','dominantBaseline','display','visibility','opacity'].map(k=>[k,style[k]]))};
 if(element instanceof SVGTextContentElement){
  const count=element.getNumberOfChars();
  if(!Number.isInteger(count)||count<0||count>200000||positions+count>200000)
   throw Error('Source aggregate actual label position budget');
  positions+=count;
  row.kind='svg-character-positions';row.characters=[];
  const matrix=element.getCTM();
  if(!matrix)throw Error('Source SVG text actual CTM absent');
  row.local_to_svg_viewport=[matrix.a,matrix.b,matrix.c,matrix.d,matrix.e,matrix.f];
  row.includes_descendant_svg_text=[...element.children].some(e=>e.textContent.trim());
  row.computed_text_length=element.getComputedTextLength();
  for(let ordinal=0;ordinal<count;ordinal++){
   const start=element.getStartPositionOfChar(ordinal),end=element.getEndPositionOfChar(ordinal);
   row.characters.push({ordinal,start:[start.x,start.y],end:[end.x,end.y],
    rotation:element.getRotationOfChar(ordinal),extent:box(element.getExtentOfChar(ordinal))});
  }
 }else{
  row.kind='html-original-text-ranges';row.characters=[];
  let offset=0;
  for(const node of nodes){
   let local=0;
   for(const character of node.textContent){
    if(positions>=200000)throw Error('Source aggregate actual label position budget');
    positions++;
    const range=document.createRange();range.setStart(node,local);
    range.setEnd(node,local+character.length);
    const fragments=range.getClientRects();
    if(positions+fragments.length>200000)
     throw Error('Source aggregate actual label position/fragment budget');
    positions+=fragments.length;
    row.characters.push({ordinal:row.characters.length,character,utf16_start:offset+local,
     utf16_end:offset+local+character.length,boxes:Array.from(fragments,box)});
    local+=character.length;
   }
   offset+=node.textContent.length;
  }
 }
 owners.push(row);
}
return {owners,utf16_source_character_count:characters,actual_source_position_count:positions,
 source_root_box:box(svg.getBoundingClientRect()),fonts_status:document.fonts.status};
})()"""


def observe_source_glyph_layout(
    client: DevTools,
    session: str,
    owners: list[dict[str, Any]],
    *,
    live: NativeLiveToolProcess,
    deadline: float,
) -> dict[str, Any]:
    remaining(deadline)
    live.verify_live()
    if deadline > live.deadline:
        raise ValueError("Source glyph layout cannot extend the genuine original process clock")
    response = client.call(
        "Runtime.evaluate",
        {
            "expression": _LAYOUT,
            "returnByValue": True,
            "awaitPromise": True,
        },
        session=session,
    )
    raw = response.get("result", {}).get("value")
    if "exceptionDetails" in response or not isinstance(raw, dict) or raw.get("fonts_status") != "loaded":
        raise ValueError("genuine Source-only browser did not observe its original label layout")
    rows = raw.get("owners")
    if not isinstance(rows, list) or len(rows) != len(owners):
        raise ValueError("Source-only layout/platform-font original text-owner census differs")
    emitted = 0
    for row, owner in zip(rows, owners, strict=True):
        if any(row.get(key) != owner[key] for key in ("owner_index", "tag", "text")):
            raise ValueError("Source-only label layout differs from the exact actual native font text owner")
        positions = row.get("characters")
        if not isinstance(positions, list):
            raise ValueError("Source-only original label positions are absent")
        emitted += len(positions)
        if row.get("kind") == "html-original-text-ranges":
            emitted += sum(len(position["boxes"]) for position in positions)
        if emitted > 200_000:
            raise ValueError("Source-only retained aggregate position/fragment allowance changed")
    if type(raw.get("actual_source_position_count")) is not int or raw["actual_source_position_count"] != emitted:
        raise ValueError("Source-only retained emitted position/fragment census differs")
    live.verify_live()
    remaining(deadline)
    body = {
        "schema_version": SCHEMA,
        **raw,
        "full_selected_font_or_ink_admission": False,
        "remaining_admission": [
            "actual Chrome consumed face/body/cache and native shaper equivalence",
            "independent held glyph contours at complete Source CSS line/baseline positions",
        ],
    }
    return {**body, "content_digest": canonical_digest(body)}
