"""Interactive multi-view simulation dashboard generator.

Generates a single self-contained HTML page with:
- Multiple linked Plotly panels (data driven by JSON payload)
- Interactive controls (sliders, dropdowns, toggles) that drive panels
- A plaintext-rendered invariants table
- A raw-data inspector pane
- A reproducibility metadata footer (seed, git rev, commit time, hyperparameters)

Companion plaintext outputs (``invariants.txt``, ``payload.json``, ``summary.txt``)
let CI / agents validate the simulation without a browser.

Plotly is loaded from a CDN; **no new Python dependencies** are introduced.

This module is project-agnostic: every project that ships configurable
simulations can reuse it by building a list of ``Panel`` objects, a list of
``Control`` objects, and a list of ``Invariant`` checks. See
``projects/actinf_policy_entanglement_lean/scripts/build_dashboard.py``
|``projects/actinf_policy_entanglement_lean/scripts/build_dashboard.py``
for end-to-end examples. |
"""

import html as _html
import json
import math
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Sequence

PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.35.2.min.js"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Panel:
    """One Plotly figure on the dashboard.

    ``traces`` and ``layout`` are passed directly to ``Plotly.newPlot``;
    every value must be JSON-serialisable.

    ``driven_by`` lists control IDs that update this panel via the
    ``update_fn`` JavaScript snippet (string with the function body --
    ``payload``, ``controls``, ``Plotly``, ``panelId`` are in scope).
    Use it when the panel must re-compute from raw data (e.g. heatmap
    slice at a slider value).
    """

    panel_id: str
    title: str
    traces: list[dict[str, Any]]
    layout: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    driven_by: list[str] = field(default_factory=list)
    update_fn: str = ""  # JS body run on control change
    # Tabular preview row count (for the data-inspector tab); 0 == hide.
    preview_rows: int = 10


@dataclass
class Control:
    """One interactive control (slider / dropdown / toggle)."""

    control_id: str
    label: str
    kind: Literal["slider", "dropdown", "toggle", "number"] = "slider"
    # slider: min/max/step/default; dropdown: options/default;
    # toggle: default (bool); number: min/max/step/default.
    min: float | None = None
    max: float | None = None
    step: float | None = None
    default: Any = 0.0
    options: list[Any] = field(default_factory=list)  # dropdown values
    option_labels: list[str] = field(default_factory=list)  # optional labels
    description: str = ""


@dataclass
class Invariant:
    """A single numerical invariant to validate.

    ``kind`` selects the comparator:
      - ``"equal"``     : ``|actual - expected| <= tol``
      - ``"le"``        : ``actual <= expected + tol``
      - ``"ge"``        : ``actual >= expected - tol``
      - ``"in_range"``  : ``expected[0] - tol <= actual <= expected[1] + tol``
      - ``"monotone_increasing"`` / ``"monotone_decreasing"``:
          ``actual`` is the sequence; ``expected`` is ignored;
          checks the sequence is (weakly) monotone within ``tol``.
      - ``"finite"``    : ``actual`` is a finite float (or all-finite array)
      - ``"nonneg"``    : ``actual >= -tol`` (scalar or array)
      - ``"array_close"``: ``max |actual_i - expected_i| <= tol`` (elementwise)
    """

    name: str
    actual: float | Sequence[float]
    expected: float | tuple[float, float] | Sequence[float] | None = None
    tol: float = 1e-9
    kind: Literal[
        "equal",
        "le",
        "ge",
        "in_range",
        "monotone_increasing",
        "monotone_decreasing",
        "finite",
        "nonneg",
        "array_close",
    ] = "equal"
    description: str = ""

    def evaluate(self) -> tuple[bool, str]:
        """Return ``(passed, witness)``. ``witness`` is a human string."""
        try:
            if self.kind == "equal":
                a = float(self.actual)  # type: ignore[arg-type]
                e = float(self.expected)  # type: ignore[arg-type]
                diff = abs(a - e)
                return diff <= self.tol, (f"|{a:.6g} - {e:.6g}| = {diff:.3e} (tol={self.tol:.1e})")
            if self.kind == "le":
                a = float(self.actual)  # type: ignore[arg-type]
                e = float(self.expected)  # type: ignore[arg-type]
                return a <= e + self.tol, f"{a:.6g} <= {e:.6g} + {self.tol:.1e}"
            if self.kind == "ge":
                a = float(self.actual)  # type: ignore[arg-type]
                e = float(self.expected)  # type: ignore[arg-type]
                return a >= e - self.tol, f"{a:.6g} >= {e:.6g} - {self.tol:.1e}"
            if self.kind == "in_range":
                a = float(self.actual)  # type: ignore[arg-type]
                lo, hi = self.expected  # type: ignore[misc]
                lo, hi = float(lo), float(hi)
                ok = (lo - self.tol) <= a <= (hi + self.tol)
                return ok, f"{lo:.6g} <= {a:.6g} <= {hi:.6g} (tol={self.tol:.1e})"
            if self.kind in ("monotone_increasing", "monotone_decreasing"):
                seq = list(self.actual)  # type: ignore[arg-type]
                worst = 0.0
                inc = self.kind == "monotone_increasing"
                for x, y in zip(seq, seq[1:]):
                    delta = (y - x) if inc else (x - y)
                    if delta < -self.tol:
                        worst = min(worst, delta)
                ok = worst >= -self.tol
                arrow = "<=" if inc else ">="
                return ok, (
                    f"worst out-of-order step = {worst:.3e} (tol={self.tol:.1e}, "
                    f"sequence length {len(seq)}, expect a_i {arrow} a_{{i+1}})"
                )
            if self.kind == "finite":
                if hasattr(self.actual, "__iter__"):
                    bad = [
                        i
                        for i, v in enumerate(self.actual)  # type: ignore[arg-type]
                        if not math.isfinite(float(v))
                    ]
                    ok = not bad
                    return (
                        ok,
                        (
                            f"all finite ({len(list(self.actual))} values)"  # type: ignore[arg-type]
                            if ok
                            else f"non-finite at indices {bad[:8]}{'...' if len(bad) > 8 else ''}"
                        ),
                    )
                a = float(self.actual)  # type: ignore[arg-type]
                ok = math.isfinite(a)
                return ok, f"value = {a!r}"
            if self.kind == "nonneg":
                if hasattr(self.actual, "__iter__"):
                    vals = [float(v) for v in self.actual]  # type: ignore[arg-type]
                    worst = min(vals) if vals else 0.0
                    ok = worst >= -self.tol
                    return ok, f"min = {worst:.6g} (tol={self.tol:.1e})"
                a = float(self.actual)  # type: ignore[arg-type]
                return a >= -self.tol, f"value = {a:.6g} (tol={self.tol:.1e})"
            if self.kind == "array_close":
                a = list(self.actual)  # type: ignore[arg-type]
                e = list(self.expected)  # type: ignore[arg-type]
                if len(a) != len(e):
                    return False, f"length mismatch: actual={len(a)}, expected={len(e)}"
                worst = 0.0
                bad_idx = -1
                for i, (av, ev) in enumerate(zip(a, e)):
                    d = abs(float(av) - float(ev))
                    if d > worst:
                        worst, bad_idx = d, i
                return worst <= self.tol, (
                    f"max |Δ| = {worst:.3e} at index {bad_idx} (tol={self.tol:.1e}, length {len(a)})"
                )
        except Exception as exc:  # pragma: no cover - defensive
            return False, f"evaluation error: {exc!r}"
        return False, f"unknown kind {self.kind!r}"


# ---------------------------------------------------------------------------
# Provenance helpers
# ---------------------------------------------------------------------------


def _git_rev(repo_root: Path | None = None) -> str:
    cwd = str(repo_root) if repo_root else None
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=cwd,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        return out.decode().strip()
    except Exception:
        return "unknown"


def _git_dirty(repo_root: Path | None = None) -> bool:
    cwd = str(repo_root) if repo_root else None
    try:
        out = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=cwd,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        return bool(out.strip())
    except Exception:
        return False


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# JSON helpers (numpy arrays → lists)
# ---------------------------------------------------------------------------


def _to_jsonable(obj: Any) -> Any:
    """Recursively convert numpy arrays / Path / dataclasses to JSON-safe."""
    if obj is None or isinstance(obj, (bool, int, float, str)):
        if isinstance(obj, float) and not math.isfinite(obj):
            return None
        return obj
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {str(k): _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_to_jsonable(v) for v in obj]
    # numpy without import-cost
    cls = obj.__class__
    if cls.__module__.startswith("numpy"):
        if hasattr(obj, "tolist"):
            return _to_jsonable(obj.tolist())
        if hasattr(obj, "item"):
            return _to_jsonable(obj.item())
    if hasattr(obj, "__dataclass_fields__"):
        return _to_jsonable(asdict(obj))
    return repr(obj)


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


class InteractiveDashboard:
    """Build a single self-contained interactive simulation dashboard.

    Typical use::

        d = InteractiveDashboard(title="My sim", subtitle="K=2 Ising toy")
        d.set_payload({"lambda": [...], "mi": [...], "fe": [...]})
        d.add_slider("lam", "λ", min=0, max=6, step=0.05, default=2.0,
                     drives=["heatmap", "tc_pointer"])
        d.add_panel(Panel(panel_id="mi_curve", title="MI(λ)",
                          traces=[...], layout={...}))
        d.add_invariant(Invariant("TC_at_zero", actual=0.0, expected=0.0,
                                  tol=1e-12))
        d.write(html_path=..., json_path=..., txt_path=...)
    """

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        project_name: str = "",
        repo_root: Path | None = None,
    ) -> None:
        self.title = title
        self.subtitle = subtitle
        self.project_name = project_name
        self.repo_root = Path(repo_root) if repo_root else None
        self.panels: list[Panel] = []
        self.controls: list[Control] = []
        self.invariants: list[Invariant] = []
        self.payload: dict[str, Any] = {}
        self.hyperparameters: dict[str, Any] = {}
        self.notes: list[str] = []
        self.tables: dict[str, list[dict[str, Any]]] = {}
        self._extra_meta: dict[str, Any] = {}

    # -- setters -----------------------------------------------------------

    def set_payload(self, payload: dict[str, Any]) -> "InteractiveDashboard":
        """Set the raw simulation payload (numpy/list/dict tree)."""
        self.payload = _to_jsonable(payload)  # type: ignore[assignment]
        return self

    def set_hyperparameters(self, hp: dict[str, Any]) -> "InteractiveDashboard":
        self.hyperparameters = _to_jsonable(hp)  # type: ignore[assignment]
        return self

    def set_meta(self, **kwargs: Any) -> "InteractiveDashboard":
        self._extra_meta.update(kwargs)
        return self

    def add_table(self, name: str, rows: list[dict[str, Any]]) -> "InteractiveDashboard":
        self.tables[name] = [_to_jsonable(r) for r in rows]  # type: ignore[misc]
        return self

    def add_panel(self, panel: "Panel") -> "InteractiveDashboard":
        if any(p.panel_id == panel.panel_id for p in self.panels):
            raise ValueError(f"duplicate panel_id: {panel.panel_id!r}")
        self.panels.append(panel)
        return self

    def add_control(self, control: "Control") -> "InteractiveDashboard":
        if any(c.control_id == control.control_id for c in self.controls):
            raise ValueError(f"duplicate control_id: {control.control_id!r}")
        self.controls.append(control)
        return self

    def add_slider(
        self,
        control_id: str,
        label: str,
        min: float,
        max: float,
        step: float,
        default: float,
        description: str = "",
    ) -> "InteractiveDashboard":
        return self.add_control(
            Control(
                control_id=control_id,
                label=label,
                kind="slider",
                min=min,
                max=max,
                step=step,
                default=default,
                description=description,
            )
        )

    def add_dropdown(
        self,
        control_id: str,
        label: str,
        options: Sequence[Any],
        default: Any,
        option_labels: Sequence[str] | None = None,
        description: str = "",
    ) -> "InteractiveDashboard":
        return self.add_control(
            Control(
                control_id=control_id,
                label=label,
                kind="dropdown",
                options=list(options),
                option_labels=list(option_labels) if option_labels else [],
                default=default,
                description=description,
            )
        )

    def add_toggle(
        self,
        control_id: str,
        label: str,
        default: bool = False,
        description: str = "",
    ) -> "InteractiveDashboard":
        return self.add_control(
            Control(
                control_id=control_id,
                label=label,
                kind="toggle",
                default=bool(default),
                description=description,
            )
        )

    def add_invariant(self, inv: "Invariant") -> "InteractiveDashboard":
        self.invariants.append(inv)
        return self

    def add_note(self, note: str) -> "InteractiveDashboard":
        self.notes.append(note)
        return self

    # -- output ------------------------------------------------------------

    def evaluate_invariants(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for inv in self.invariants:
            ok, witness = inv.evaluate()
            results.append(
                {
                    "name": inv.name,
                    "passed": ok,
                    "kind": inv.kind,
                    "tolerance": inv.tol,
                    "witness": witness,
                    "description": inv.description,
                }
            )
        return results

    def render_invariants_text(self, results: Sequence[dict[str, Any]] | None = None) -> str:
        if results is None:
            results = self.evaluate_invariants()
        lines: list[str] = []
        title = f"Invariants for {self.title}"
        lines.append(title)
        lines.append("=" * len(title))
        lines.append(f"generated:    {_utc_now()}")
        lines.append(f"project:      {self.project_name or '(unknown)'}")
        lines.append(f"git rev:      {_git_rev(self.repo_root)}")
        if _git_dirty(self.repo_root):
            lines.append("git status:   dirty (uncommitted changes)")
        lines.append("")
        n_total = len(results)
        n_pass = sum(1 for r in results if r["passed"])
        n_fail = n_total - n_pass
        lines.append(f"summary:      {n_pass}/{n_total} passed, {n_fail} failed")
        lines.append("")
        if not n_total:
            lines.append("(no invariants registered)")
        else:
            name_w = max(len(r["name"]) for r in results)
            kind_w = max(len(r["kind"]) for r in results)
            for r in results:
                marker = "PASS" if r["passed"] else "FAIL"
                lines.append(f"  [{marker}] {r['name']:<{name_w}}  {r['kind']:<{kind_w}}  {r['witness']}")
                if r["description"]:
                    lines.append(f"         {r['description']}")
        lines.append("")
        return "\n".join(lines)

    def render_summary_text(self) -> str:
        lines: list[str] = []
        title = self.title
        lines.append(title)
        lines.append("=" * len(title))
        if self.subtitle:
            lines.append(self.subtitle)
            lines.append("")
        lines.append(f"project:           {self.project_name or '(unknown)'}")
        lines.append(f"generated:         {_utc_now()}")
        lines.append(f"git rev:           {_git_rev(self.repo_root)}")
        lines.append(f"panels:            {len(self.panels)}")
        lines.append(f"controls:          {len(self.controls)}")
        lines.append(f"invariants:        {len(self.invariants)}")
        if self.hyperparameters:
            lines.append("")
            lines.append("hyperparameters")
            lines.append("---------------")
            for k in sorted(self.hyperparameters):
                v = self.hyperparameters[k]
                if isinstance(v, (list, tuple)) and len(v) > 6:
                    v = f"[{v[0]!r} ... {v[-1]!r}] (len={len(v)})"
                lines.append(f"  {k}: {v}")
        if self.notes:
            lines.append("")
            lines.append("notes")
            lines.append("-----")
            for n in self.notes:
                lines.append(f"  - {n}")
        return "\n".join(lines) + "\n"

    def to_json(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "subtitle": self.subtitle,
            "project": self.project_name,
            "generated_utc": _utc_now(),
            "git_rev": _git_rev(self.repo_root),
            "git_dirty": _git_dirty(self.repo_root),
            "hyperparameters": self.hyperparameters,
            "meta": _to_jsonable(self._extra_meta),
            "controls": [asdict(c) for c in self.controls],
            "panels": [
                {
                    "panel_id": p.panel_id,
                    "title": p.title,
                    "description": p.description,
                    "driven_by": p.driven_by,
                    "preview_rows": p.preview_rows,
                }
                for p in self.panels
            ],
            "invariants": self.evaluate_invariants(),
            "tables": self.tables,
            "notes": self.notes,
        }

    def write(
        self,
        html_path: Path | str,
        json_path: Path | str | None = None,
        txt_path: Path | str | None = None,
        invariants_path: Path | str | None = None,
    ) -> dict[str, Path]:
        """Write the dashboard and companion plaintext outputs.

        Returns a dict mapping artefact name → absolute Path (resolved).
        """
        html_path = Path(html_path)
        html_path.parent.mkdir(parents=True, exist_ok=True)
        results = self.evaluate_invariants()

        # Build payload bundle exposed to the in-page JS.
        bundle = {
            "title": self.title,
            "subtitle": self.subtitle,
            "project": self.project_name,
            "generated_utc": _utc_now(),
            "git_rev": _git_rev(self.repo_root),
            "git_dirty": _git_dirty(self.repo_root),
            "hyperparameters": self.hyperparameters,
            "meta": _to_jsonable(self._extra_meta),
            "payload": self.payload,
            "panels": [
                {
                    "panel_id": p.panel_id,
                    "title": p.title,
                    "description": p.description,
                    "traces": _to_jsonable(p.traces),
                    "layout": _to_jsonable(p.layout),
                    "driven_by": p.driven_by,
                    "update_fn": p.update_fn,
                    "preview_rows": p.preview_rows,
                }
                for p in self.panels
            ],
            "controls": [asdict(c) for c in self.controls],
            "invariants": results,
            "tables": self.tables,
            "notes": self.notes,
        }
        bundle_json = json.dumps(bundle, ensure_ascii=False, allow_nan=False, indent=2)

        html_path.write_text(self._render_html(bundle_json), encoding="utf-8")

        out: dict[str, Path] = {"html": html_path.resolve()}
        if json_path is not None:
            jp = Path(json_path)
            jp.parent.mkdir(parents=True, exist_ok=True)
            jp.write_text(bundle_json, encoding="utf-8")
            out["json"] = jp.resolve()
        if invariants_path is not None:
            ip = Path(invariants_path)
            ip.parent.mkdir(parents=True, exist_ok=True)
            ip.write_text(self.render_invariants_text(results), encoding="utf-8")
            out["invariants"] = ip.resolve()
        if txt_path is not None:
            tp = Path(txt_path)
            tp.parent.mkdir(parents=True, exist_ok=True)
            tp.write_text(self.render_summary_text(), encoding="utf-8")
            out["summary"] = tp.resolve()
        return out

    # -- HTML --------------------------------------------------------------

    _CSS = """
:root{
  --bg:#0f172a; --panel:#111827; --fg:#e5e7eb; --muted:#94a3b8;
  --accent:#38bdf8; --pass:#22c55e; --fail:#ef4444; --border:#1f2937;
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

    _JS_TEMPLATE = """
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

    def _render_html(self, bundle_json: str) -> str:
        title = _html.escape(self.title)
        subtitle = _html.escape(self.subtitle)
        project = _html.escape(self.project_name) or "(unknown)"
        gen = _utc_now()
        rev = _html.escape(_git_rev(self.repo_root))
        dirty = " (dirty)" if _git_dirty(self.repo_root) else ""
        js = self._JS_TEMPLATE.replace("__BUNDLE__", bundle_json)
        return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1.0" />
<title>{title}</title>
<style>{self._CSS}</style>
<script src="{PLOTLY_CDN}"></script>
</head><body>
<h1>{title}</h1>
{f'<p class="subtitle">{subtitle}</p>' if subtitle else ""}

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
  panels: {len(self.panels)} &middot;
  controls: {len(self.controls)} &middot;
  invariants: {len(self.invariants)}
</div>

<script>{js}</script>
</body></html>
"""


__all__ = [
    "Control",
    "Invariant",
    "InteractiveDashboard",
    "Panel",
]
