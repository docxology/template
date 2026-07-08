"""Interactive multi-view simulation dashboard generator.

Generates a single self-contained HTML page with Plotly panels, controls,
invariants, and reproducibility metadata. Library split: ``_interactive_models``
(data types), ``_interactive_html`` (page assembly), this module (builder API).
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Sequence

from infrastructure.reporting._interactive_html import PLOTLY_CDN, render_interactive_dashboard_html
from infrastructure.reporting._interactive_models import (
    Control,
    Invariant,
    Panel,
    _git_dirty,
    _git_rev,
    _to_jsonable,
    _utc_now,
)


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
        """Process set hyperparameters."""
        self.hyperparameters = _to_jsonable(hp)  # type: ignore[assignment]
        return self

    def set_meta(self, **kwargs: Any) -> "InteractiveDashboard":
        """Process set meta."""
        self._extra_meta.update(kwargs)
        return self

    def add_table(self, name: str, rows: list[dict[str, Any]]) -> "InteractiveDashboard":
        """Add table to the collection."""
        self.tables[name] = [_to_jsonable(r) for r in rows]  # type: ignore[misc]
        return self

    def add_panel(self, panel: "Panel") -> "InteractiveDashboard":
        """Add panel to the collection."""
        if any(p.panel_id == panel.panel_id for p in self.panels):
            raise ValueError(f"duplicate panel_id: {panel.panel_id!r}")
        self.panels.append(panel)
        return self

    def add_control(self, control: "Control") -> "InteractiveDashboard":
        """Add control to the collection."""
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
        """Add slider to the collection."""
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
        """Add dropdown to the collection."""
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
        """Add toggle to the collection."""
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
        """Add invariant to the collection."""
        self.invariants.append(inv)
        return self

    def add_note(self, note: str) -> "InteractiveDashboard":
        """Add note to the collection."""
        self.notes.append(note)
        return self

    # -- output ------------------------------------------------------------

    def evaluate_invariants(self) -> list[dict[str, Any]]:
        """Process evaluate invariants."""
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
        """Render invariants text."""
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
        """Render summary text."""
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
        """Serialize this object to a JSON string."""
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

        html_path.write_text(
            render_interactive_dashboard_html(
                title=self.title,
                subtitle=self.subtitle,
                project_name=self.project_name,
                repo_root=self.repo_root,
                panel_count=len(self.panels),
                control_count=len(self.controls),
                invariant_count=len(self.invariants),
                bundle_json=bundle_json,
            ),
            encoding="utf-8",
        )

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


__all__ = [
    "Control",
    "Invariant",
    "InteractiveDashboard",
    "PLOTLY_CDN",
    "Panel",
    "_git_rev",
    "_git_dirty",
    "_utc_now",
    "_to_jsonable",
]
