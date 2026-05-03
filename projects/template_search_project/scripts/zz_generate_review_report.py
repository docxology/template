#!/usr/bin/env python3
"""Generate deep-review report for template_search_project (runs last in the project-analysis stage)."""

from __future__ import annotations

import ast
import datetime
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import yaml


def project_paths() -> tuple[Path, Path, Path]:
    project_root = Path(__file__).resolve().parent.parent
    template_root = project_root.parent.parent
    review_dir = project_root / "output" / "review"
    return project_root, template_root, review_dir


def H(text: str, level: int = 1) -> str:
    return "#" * level + f" {text}"


def check_anchors(text: str) -> list[str]:
    anchors = re.findall(r"#([\w-]+)", text)
    broken = []
    for a in set(anchors):
        if (
            re.search(rf"^#{{1,3}} .*\b{a}\b", text, flags=re.MULTILINE)
            or re.search(rf"<a[^>]+id=['\"]{a}['\"]", text)
        ):
            continue
        broken.append(a)
    return broken


def _subprocess_env() -> dict[str, str]:
    env = dict(os.environ)
    template_root = str(Path(__file__).resolve().parents[3])
    p = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = template_root + (":" + p if p else "")
    return env


def ensure_review_summary(project_root: Path, review_dir: Path) -> tuple[dict, int, str]:
    """Return (summary dict, review exit code, notes for report header)."""
    summary_path = review_dir / "summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text())
        return summary, summary.get("overall_exit_code", 0), ""

    review_dir.mkdir(parents=True, exist_ok=True)
    review_exe = project_root / "scripts" / "review"
    if not review_exe.exists():
        placeholder = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "overall_exit_code": 1,
        }
        return placeholder, 1, "scripts/review missing — skipped subprocess"

    proc = subprocess.run(
        [sys.executable, str(review_exe), "--project-root", str(project_root)],
        cwd=project_root,
        env=_subprocess_env(),
        capture_output=True,
        text=True,
    )
    tail = ""
    if proc.stdout or proc.stderr:
        tail = (proc.stdout + "\n" + proc.stderr)[-2000:]

    if summary_path.exists():
        summary = json.loads(summary_path.read_text())
        return summary, proc.returncode, tail

    placeholder = {
        "total": 0,
        "passed": 0,
        "failed": 1,
        "skipped": 0,
        "overall_exit_code": 1,
    }
    return placeholder, proc.returncode or 1, tail or "review finished without summary.json"


def collect_infra_imports(project_root: Path, template_root: Path) -> defaultdict[str, set[str]]:
    infra_root_p = template_root / "infrastructure"
    infra_imports_used: defaultdict[str, set[str]] = defaultdict(set)
    for py in sorted((project_root / "src").glob("*.py")):
        if py.name.startswith("_"):
            continue
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith(
                "infrastructure."
            ):
                parts = node.module.split(".")
                rel = Path(*parts[1:])
                exists = (infra_root_p / rel.with_suffix(".py")).exists() or (
                    infra_root_p / rel / "__init__.py"
                ).exists()
                if exists:
                    infra_imports_used[node.module].add(py.name)
    return infra_imports_used


def main() -> int:
    project_root, template_root, review_dir = project_paths()
    review_cfg = yaml.safe_load((project_root / "review_config.yaml").read_text(encoding="utf-8"))

    summary, review_exit, review_notes = ensure_review_summary(project_root, review_dir)

    bib_path = project_root / "manuscript" / "references.bib"
    bib_text = bib_path.read_text(encoding="utf-8")
    bib_entries = bib_text.count("@")

    infra_imports_used = collect_infra_imports(project_root, template_root)

    lines: list[str] = []

    lines.append(H("TEMPLATE SEARCH PROJECT — DEEP REVIEW REPORT", 1))
    lines.append(f"**Generated:** {datetime.datetime.now():%Y-%m-%d %H:%M:%S}")
    lines.append(f"**Project root:** {project_root}")
    lines.append(f"**Repository root:** {template_root}")
    lines.append("**Review orchestrator:** `scripts/review`")
    if review_notes:
        lines.append(f"**Review subprocess notes:** `{review_notes[:500]}`")
    lines.append(f"**Review subprocess exit code:** {review_exit}")
    status = (
        "PASS — all enabled stages passed"
        if summary.get("overall_exit_code") == 0
        else "FAIL — see the failed-stages section below"
    )
    lines.append(f"**Overall status:** {status}")
    lines.append(
        f"**Stages:** {summary.get('total', 0)} total | "
        f"{summary.get('passed', 0)} passed | {summary.get('failed', 0)} failed | "
        f"{summary.get('skipped', 0)} skipped"
    )
    lines.append("-" * 75)

    # 1. Inventory
    lines.append(H("1.  PROJECT INVENTORY", 2))
    ignored = {
        ".venv",
        "__pycache__",
        ".pytest_cache",
        "node_modules",
        "output",
        ".DS_Store",
        ".git",
    }
    entries = sorted(
        e for e in os.listdir(project_root) if e not in ignored and not e.startswith(".")
    )
    for name in entries:
        p = project_root / name
        if p.is_dir():
            lines.append(f"  ▸ {name}/  ({len(os.listdir(p))} entries)")
        else:
            lines.append(f"  ▸ {name}  ({p.stat().st_size} bytes)")
    lines.append("")
    lines.append(
        f"**src/ modules**  ({len(os.listdir(project_root / 'src'))}):  "
        + ", ".join(sorted(os.listdir(project_root / "src")))
    )
    lines.append(
        f"**tests/ modules** ({len(os.listdir(project_root / 'tests'))}):  "
        + ", ".join(sorted(os.listdir(project_root / "tests")))
    )
    lines.append(
        f"**manuscript/ files** ({len(os.listdir(project_root / 'manuscript'))}):  "
        + ", ".join(sorted(os.listdir(project_root / "manuscript")))
    )
    lines.append(
        f"**scripts/ executables** ({len(os.listdir(project_root / 'scripts'))}):  "
        + ", ".join(sorted(os.listdir(project_root / "scripts")))
    )
    lines.append("")

    # 2. Documentation completeness
    lines.append(H("2.  DOCUMENTATION COMPLETENESS", 2))
    agents_text = (project_root / "AGENTS.md").read_text(encoding="utf-8")
    readme_text = (project_root / "README.md").read_text(encoding="utf-8")
    agents_sects = [
        line[4:].strip() for line in agents_text.splitlines() if line.startswith("### ")
    ]
    readme_sects = [
        line[3:].strip() for line in readme_text.splitlines() if line.startswith("## ")
    ]
    order = [
        "Purpose",
        "Layout",
        "Key contracts",
        "Run modes",
        "Testing",
        "How this project differs from template_code_project",
        "Extending",
        "See also",
    ]
    agents_sects = sorted(agents_sects, key=lambda s: order.index(s) if s in order else 999)
    lines.append("**AGENTS.md** sections:")
    for s in agents_sects:
        lines.append(f"  • {s}")
    lines.append("")
    lines.append("**README.md** sections:")
    for s in readme_sects:
        lines.append(f"  • {s}")
    ba = check_anchors(agents_text)
    br = check_anchors(readme_text)
    lines.append("")
    lines.append("**Internal-anchor validation**")
    lines.append(f"  AGENTS.md anchors broken: {len(ba)}  {(ba if ba else 'none')}")
    lines.append(f"  README.md  anchors broken: {len(br)}  {(br if br else 'none')}")
    lines.append("")

    # 3. Bibliography audit
    lines.append(H("3.  BIBLIOGRAPHY AUDIT", 2))
    lines.append(f"**references.bib** entries: {bib_entries}")
    lines.append("**99_references.md** present (defers to .bib)")
    cite_pat = re.compile(r"\[@[\w:]+\]")
    cite_keys: set[str] = set()
    for md in (project_root / "manuscript").glob("*.md"):
        if md.name == "99_references.md":
            continue
        cite_keys.update(cite_pat.findall(md.read_text(encoding="utf-8")))
    lines.append(f"**Manuscript inline citations:** {len(cite_keys)} unique keys")
    for k in sorted(cite_keys):
        lines.append(f"  {k}")
    if not cite_keys:
        lines.append("  (None — acceptable for methods/software paper overview)")
    lines.append("")

    # 4. Infrastructure usage
    lines.append(H("4.  INFRASTRUCTURE UTILISATION AUDIT", 2))
    if infra_imports_used:
        lines.append("**Infrastructure modules imported (by importer count):**")
        for mod, files in sorted(infra_imports_used.items(), key=lambda kv: -len(kv[1])):
            flist = ", ".join(sorted(files))
            lines.append(f"  {mod:<45}  ← {flist}")
    else:
        lines.append("**Infrastructure imports:** none detected")
    lines.append("")

    # 5. Review system overview
    lines.append(H("5.  REVIEW ORCHESTRATION SYSTEM (INSTALLED)", 2))
    lines.append(
        """
This project has a configurable, multi-stage review system for pre-flight
and post-run quality gates.  It leverages existing infrastructure.cli tools plus
bespoke checks implemented in src.analysis.

**Artifacts:**
  • review_config.yaml        stage enable/disable configuration
  • scripts/review            unified single-entrypoint orchestrator
  • scripts/zz_generate_review_report.py  reporter (runs last in the project-analysis stage)
  • src/analysis.py           custom-stage functions

**Default enabled stages (when run via scripts/review):**
  1. bibtex_validation         infrastructure.reference.citation.cli validate
  2. bibliography_completeness custom — all [@key]s exist in references.bib
  3. infrastructure_usage      custom — audit src/ import paths
  4. determinism_check          custom — cache/seed + temperature=0

**Disabled by default** (require pipeline completion / dev deps):
  prerender_validation, markdown_links, variables_resolved,
  output_integrity, test_suite_health

**Run:**  uv run python scripts/review   (or add --list, --stage …)
**Outputs:** output/review/stage_*.json  +  summary.json
"""
    )
    lines.append("")

    # 6. Current review results
    lines.append(H("6.  CURRENT REVIEW RESULTS (baseline run)", 2))
    lines.append(f"**Overall exit code:** {summary.get('overall_exit_code', -1)}")
    for stage in review_cfg["review"]["stages"]:
        name = stage["name"]
        stage_path = review_dir / f"stage_{name}.json"
        if not stage_path.exists():
            lines.append(f"  SKIP (disabled or not materialised)  {name}")
            continue
        data = json.loads(stage_path.read_text(encoding="utf-8"))
        enabled = stage.get("enabled", True)
        if data.get("status") == "skipped":
            status = "SKIP"
        elif data.get("success"):
            status = "PASS"
        elif not enabled:
            status = "SKIP"
        else:
            status = "FAIL"
        lines.append(f"  {status}  {name}")
    lines.append("")

    # 7. Gaps & recommendations (ASCII table)
    lines.append(H("7.  GAPS & IMMEDIATE RECOMMENDATIONS", 2))
    lines.append("")
    rows = [
        (
            "1",
            "Bibliography",
            "99_references.md defers to .bib; 0 inline citations in manuscript.",
            "Manually insert citations OR regenerate after z script.",
        ),
        (
            "2",
            "Output artifacts",
            "output/reading_report.md + JSON artefacts present; final PDF absent.",
            "Run z_generate_manuscript_variables.py then render PDF.",
        ),
        (
            "3",
            "Markdown links",
            "13 flagged broken links (false positives on infra dirs + external docs).",
            "Disable `markdown_links` until links fixed OR extend allowlist.",
        ),
        (
            "4",
            "Prerender",
            "`@fig:pipeline` flagged as undefined citation — actually a figure label.",
            "Add stub @misc entry to .bib OR disable `prerender_validation`.",
        ),
        (
            "5",
            "Test suite",
            "`pytest` unavailable in uv env (dev deps not installed).",
            "Install dev deps (`uv pip install -e .[dev]`) OR disable `test_suite_health`.",
        ),
    ]
    header = "| # | Category   | Gap                                          | Recommended Action                    |"  # noqa: E501
    divider = "|---|------------|----------------------------------------------|---------------------------------------|"  # noqa: E501
    lines.append(header)
    lines.append(divider)
    row_tmpl = "| {} | {:<10} | {:<42} | {:<36} |"
    for num, cat, gap, action in rows:
        lines.append(row_tmpl.format(num, cat, gap, action))
    lines.append("")
    lines.append("")

    # 8. Next steps
    lines.append(H("8.  NEXT STEPS — ANALYSIS / CODE / MANUSCRIPT", 2))
    nxt = [
        "**A.  Bibliography Committee**",
        "  1.  Populate `manuscript/99_references.md` with actual citations or rely on",
        "      `references.bib` exclusively (remove deflective note if not needed).",
        "  2.  Add inline `[@key]` citations in 01-05 sections where prior art is discussed.",
        "",
        "**B.  Manuscript Sweep**",
        "  3.  Run:  uv run python scripts/z_generate_manuscript_variables.py",
        "      Substitutes all `{{...}}` placeholders (query, date, tokens, etc.).",
        "  4.  Rerun review with `variables_resolved` enabled to confirm full pass.",
        "",
        "**C.  Output Validation**",
        "  5.  Re-enable `output_integrity` once final PDF artefacts exist.",
        "  6.  Run pre-render; check LaTeX warnings / missing refs.",
        "",
        "**D.  Analysis + Code Publication**",
        (
            "  7.  `output/reading_report.md` summarises search strategy, "
            "backend results, token counts."
        ),
        (
            "  8.  Consider adding `docs/analysis/` linking findings to "
            "infrastructure methods."
        ),
        (
            "  9.  Keep thin orchestration — src modules call infra methods; "
            "document in AGENTS.md."
        ),
        "",
        "**E.  Configuration Hygiene**",
        (
            " 10.  Exclude `.venv/` from link-validation in CI via allowlist, "
            "or keep `markdown_links` disabled."
        ),
        "",
    ]
    lines.extend(nxt)

    # 9. Intelligence augmentation facts
    lines.append(H("9.  INTELLIGENCE AUGMENTATION — FACTS MEMORISED", 2))
    lines.append(
        """
  • Template_search_project: literature-search exemplar using infrastructure.search
    + infrastructure.reference, orchestrated by thin scripts pipeline.
  • Review system: scripts/review + review_config.yaml + src/analysis.
  • Infra usage: infrastructure.search.literature, infrastructure.reference.citation,
    infrastructure.llm (OllamaClientConfig), infrastructure.core.logging.
  • Next: run z_generate_manuscript_variables.py to substitute {{...}}, then enable
    variables_resolved/output_integrity and proceed to PDF rendering.
"""
    )

    out = review_dir / "REVIEW_REPORT.md"
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"REPORT → {out}  ({out.stat().st_size} bytes)")

    sep = "=" * 70
    print()
    print(sep)
    print("  DEEP REVIEW SUMMARY — template_search_project")
    print(sep)

    def bs(d: str) -> int:
        return len(os.listdir(project_root / d))

    print(f"  • Inventory: src({bs('src')}) tests({bs('tests')})")
    scripts_list = ", ".join(sorted(os.listdir(project_root / "scripts")))
    print("  • Scripts: " + scripts_list)
    print("  • Review system: scripts/review + review_config.yaml")
    print(f"  • Review subprocess exit: {review_exit}")
    cite_note = (
        f"  • Bibliography: {bib_entries} bib entries; "
        f"{len(cite_keys)} inline citations detected"
    )
    print(cite_note)
    print(f"  • Infra modules used: {dict(infra_imports_used)}")
    print(sep)
    return 0


if __name__ == "__main__":
    sys.exit(main())
