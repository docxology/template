"""HTML/CSS/JS assembly for interactive simulation dashboards."""

from __future__ import annotations

import html as _html
from pathlib import Path

from infrastructure.reporting._interactive_models import _git_dirty, _git_rev, _utc_now

PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.35.2.min.js"


DASHBOARD_CSS = """
:root{
  --bg:#0f172a; --panel:#111827; --fg:#e5e7eb; --muted:#94a3b8;
  --accent:#38bdf8; --pass:#22c55e; --fail:#ef4444; --border:#1f2937;
  /* Shared design-token alias: keeps this surface tied to the report design
     system (see infrastructure.reporting.html_templates.shared_css). */
  --brand-1:#5b6ee0;
}
/* Dashboard is dark-by-default; honor an explicit light preference so every
   HTML surface carries a prefers-color-scheme block from one token source. */
@media (prefers-color-scheme: light){
  :root{
    --bg:#eef1f6; --panel:#ffffff; --fg:#1f2733; --muted:#5a6573;
    --accent:#5b6ee0; --border:#e3e8ef;
  }
}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--fg);
  font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
body{padding:24px;max-width:1480px;margin:0 auto}
h1{margin:0 0 4px 0;font-size:24px}
h2{margin:24px 0 8px 0;font-size:16px;color:var(--muted);
  text-transform:uppercase;letter-spacing:.08em}
.subtitle{color:var(--muted);margin:0 0 16px 0}
.row{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));
  gap:16px}
.panel{background:var(--panel);border:1px solid var(--border);
  border-radius:8px;padding:12px}
.panel h3{margin:0 0 8px 0;font-size:14px;color:var(--fg)}
.panel .desc{color:var(--muted);font-size:12px;margin:0 0 8px 0}
.controls{background:var(--panel);border:1px solid var(--border);
  border-radius:8px;padding:12px;margin-bottom:16px;
  display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));
  gap:12px}
.ctrl label{display:block;font-size:12px;color:var(--muted);
  margin-bottom:4px;text-transform:uppercase;letter-spacing:.05em}
.ctrl input[type=range]{width:100%}
.ctrl .value{color:var(--accent);font-variant-numeric:tabular-nums}
.invariants{margin-top:24px}
.invariants table{width:100%;border-collapse:collapse;font-size:13px;
  background:var(--panel);border:1px solid var(--border);border-radius:8px;
  overflow:hidden}
.invariants th,.invariants td{padding:8px 10px;text-align:left;
  border-bottom:1px solid var(--border)}
.invariants th{background:#0b1220;color:var(--muted);font-weight:600}
.pass{color:var(--pass);font-weight:700}
.fail{color:var(--fail);font-weight:700}
.tabs{display:flex;gap:4px;margin:16px 0 8px 0}
.tabs button{background:var(--panel);color:var(--muted);border:1px solid var(--border);
  padding:6px 12px;border-radius:6px;cursor:pointer;font-size:13px}
.tabs button.active{background:var(--accent);color:#0b1220;
  border-color:var(--accent)}
.tab-content{display:none}
.tab-content.active{display:block}
pre{background:#0b1220;border:1px solid var(--border);
  border-radius:6px;padding:12px;overflow:auto;max-height:520px;font-size:12px}
.meta{color:var(--muted);font-size:12px;margin-top:24px;padding-top:12px;
  border-top:1px solid var(--border)}
.kbd{background:#0b1220;border:1px solid var(--border);border-radius:4px;
  padding:1px 4px;font-family:ui-monospace,monospace;font-size:11px}
.summary-bar{display:flex;gap:12px;align-items:center;margin-top:8px}
.summary-bar .pill{background:var(--panel);border:1px solid var(--border);
  border-radius:999px;padding:4px 10px;font-size:12px;color:var(--muted)}
.summary-bar .pill.ok{color:var(--pass);border-color:#14532d}
.summary-bar .pill.bad{color:var(--fail);border-color:#7f1d1d}
"""

DASHBOARD_JS_TEMPLATE = """
const BUNDLE = __BUNDLE__;
const CONTROL_VALUES = {};
BUNDLE.controls.forEach(c => CONTROL_VALUES[c.control_id] = c.default);

function fmtNum(v){
  if (typeof v !== 'number' || !isFinite(v)) return String(v);
  return Math.abs(v) >= 1e4 || (Math.abs(v) < 1e-3 && v !== 0)
    ? v.toExponential(4) : v.toFixed(6);
}

function renderControls(){
  const root = document.getElementById('controls-root');
  root.innerHTML = '';
  BUNDLE.controls.forEach(c => {
    const wrap = document.createElement('div');
    wrap.className = 'ctrl';
    const label = document.createElement('label');
    label.htmlFor = 'ctrl-' + c.control_id;
    label.textContent = c.label + (c.description ? ' (' + c.description + ')' : '');
    wrap.appendChild(label);
    if (c.kind === 'slider' || c.kind === 'number'){
      const row = document.createElement('div');
      row.style.display='flex'; row.style.gap='10px'; row.style.alignItems='center';
      const inp = document.createElement('input');
      inp.type = c.kind === 'slider' ? 'range' : 'number';
      inp.id = 'ctrl-' + c.control_id;
      inp.min = c.min; inp.max = c.max; inp.step = c.step;
      inp.value = c.default;
      const val = document.createElement('span');
      val.className = 'value';
      val.id = 'ctrl-' + c.control_id + '-value';
      val.textContent = fmtNum(c.default);
      inp.addEventListener('input', () => {
        const v = parseFloat(inp.value);
        CONTROL_VALUES[c.control_id] = v;
        val.textContent = fmtNum(v);
        updatePanels(c.control_id);
      });
      row.appendChild(inp);
      row.appendChild(val);
      wrap.appendChild(row);
    } else if (c.kind === 'dropdown'){
      const sel = document.createElement('select');
      sel.id = 'ctrl-' + c.control_id;
      c.options.forEach((opt, i) => {
        const o = document.createElement('option');
        o.value = String(opt);
        o.textContent = c.option_labels && c.option_labels[i] ? c.option_labels[i] : String(opt);
        if (opt === c.default) o.selected = true;
        sel.appendChild(o);
      });
      sel.addEventListener('change', () => {
        // try numeric
        const raw = sel.value;
        const num = Number(raw);
        CONTROL_VALUES[c.control_id] = (raw !== '' && !Number.isNaN(num)) ? num : raw;
        updatePanels(c.control_id);
      });
      wrap.appendChild(sel);
    } else if (c.kind === 'toggle'){
      const inp = document.createElement('input');
      inp.type = 'checkbox';
      inp.id = 'ctrl-' + c.control_id;
      inp.checked = !!c.default;
      inp.addEventListener('change', () => {
        CONTROL_VALUES[c.control_id] = inp.checked;
        updatePanels(c.control_id);
      });
      wrap.appendChild(inp);
    }
    root.appendChild(wrap);
  });
}

function renderPanels(){
  const root = document.getElementById('panels-root');
  root.innerHTML = '';
  BUNDLE.panels.forEach(p => {
    const div = document.createElement('div');
    div.className = 'panel';
    div.innerHTML = '<h3>' + p.title + '</h3>' +
      (p.description ? '<div class="desc">' + p.description + '</div>' : '') +
      '<div id="plot-' + p.panel_id + '" style="height:340px"></div>';
    root.appendChild(div);
    const layout = Object.assign({
      paper_bgcolor:'#111827', plot_bgcolor:'#0b1220',
      font:{color:'#e5e7eb'},
      margin:{l:48,r:24,t:32,b:48},
    }, p.layout || {});
    Plotly.newPlot('plot-' + p.panel_id, p.traces, layout,
                   {displaylogo:false, responsive:true});
  });
}

function updatePanels(changedControlId){
  BUNDLE.panels.forEach(p => {
    if (changedControlId !== null && p.driven_by && p.driven_by.length &&
        !p.driven_by.includes(changedControlId)) return;
    if (!p.update_fn) return;
    try{
      const fn = new Function('payload','controls','Plotly','panelId', p.update_fn);
      fn(BUNDLE.payload, CONTROL_VALUES, Plotly, 'plot-' + p.panel_id);
    } catch(e){
      console.error('panel ' + p.panel_id + ' update_fn error:', e);
    }
  });
}

function renderInvariants(){
  const root = document.getElementById('invariants-root');
  if (!BUNDLE.invariants || !BUNDLE.invariants.length){
    root.innerHTML = '<p style="color:#94a3b8">(no invariants)</p>';
    return;
  }
  const total = BUNDLE.invariants.length;
  const passed = BUNDLE.invariants.filter(i => i.passed).length;
  const failed = total - passed;
  let html = '<div class="summary-bar">' +
    '<span class="pill ok">PASS: ' + passed + '</span>' +
    '<span class="pill ' + (failed?'bad':'') + '">FAIL: ' + failed + '</span>' +
    '<span class="pill">total: ' + total + '</span>' +
    '</div>';
  html += '<table><thead><tr><th>status</th><th>name</th><th>kind</th><th>tolerance</th><th>witness</th></tr></thead><tbody>';
  BUNDLE.invariants.forEach(i => {
    html += '<tr>' +
      '<td class="' + (i.passed?'pass':'fail') + '">' + (i.passed?'PASS':'FAIL') + '</td>' +
      '<td>' + i.name + '</td>' +
      '<td>' + i.kind + '</td>' +
      '<td>' + i.tolerance + '</td>' +
      '<td>' + i.witness + '</td>' +
      '</tr>';
  });
  html += '</tbody></table>';
  root.innerHTML = html;
}

function renderRawTab(){
  document.getElementById('payload-pre').textContent =
    JSON.stringify(BUNDLE.payload, null, 2);
  document.getElementById('hp-pre').textContent =
    JSON.stringify(BUNDLE.hyperparameters, null, 2);
  document.getElementById('meta-pre').textContent =
    JSON.stringify({git_rev:BUNDLE.git_rev, git_dirty:BUNDLE.git_dirty,
                    generated_utc:BUNDLE.generated_utc, project:BUNDLE.project,
                    meta:BUNDLE.meta, notes:BUNDLE.notes}, null, 2);
}

function setupTabs(){
  document.querySelectorAll('.tabs button').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tabs button').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  renderControls();
  renderPanels();
  renderInvariants();
  renderRawTab();
  setupTabs();
  // Initial drive (e.g. set heatmap from default slider).
  updatePanels(null);
});
"""


def render_interactive_dashboard_html(
    *,
    title: str,
    subtitle: str,
    project_name: str,
    repo_root: Path | None,
    panel_count: int,
    control_count: int,
    invariant_count: int,
    bundle_json: str,
) -> str:
    """Render the self-contained interactive dashboard HTML page."""
    title_esc = _html.escape(title)
    subtitle_esc = _html.escape(subtitle)
    project = _html.escape(project_name) or "(unknown)"
    gen = _utc_now()
    rev = _html.escape(_git_rev(repo_root))
    dirty = " (dirty)" if _git_dirty(repo_root) else ""
    js = DASHBOARD_JS_TEMPLATE.replace("__BUNDLE__", bundle_json)
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1.0" />
<title>{title_esc}</title>
<style>{DASHBOARD_CSS}</style>
<script src="{PLOTLY_CDN}"></script>
</head><body>
<h1>{title_esc}</h1>
{f'<p class="subtitle">{subtitle_esc}</p>' if subtitle else ""}

<div class="tabs">
  <button class="active" data-tab="dashboard">Dashboard</button>
  <button data-tab="invariants">Invariants</button>
  <button data-tab="raw">Raw payload</button>
</div>

<div id="tab-dashboard" class="tab-content active">
  <h2>Controls</h2>
  <div class="controls" id="controls-root"></div>
  <h2>Panels</h2>
  <div class="row" id="panels-root"></div>
</div>

<div id="tab-invariants" class="tab-content">
  <h2>Invariants</h2>
  <div class="invariants" id="invariants-root"></div>
</div>

<div id="tab-raw" class="tab-content">
  <h2>Hyperparameters</h2>
  <pre id="hp-pre"></pre>
  <h2>Provenance</h2>
  <pre id="meta-pre"></pre>
  <h2>Payload</h2>
  <pre id="payload-pre"></pre>
</div>

<div class="meta">
  project: <code>{project}</code> &middot;
  generated: <code>{gen}</code> &middot;
  git: <code>{rev}{dirty}</code> &middot;
  panels: {panel_count} &middot;
  controls: {control_count} &middot;
  invariants: {invariant_count}
</div>

<script>{js}</script>
</body></html>
"""
