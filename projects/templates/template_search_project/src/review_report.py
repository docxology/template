"""Deep-review report generation for template_search_project.

Extracted from ``scripts/zz_generate_review_report.py`` (thin-orchestrator
refactor): the script now only resolves paths and calls
:func:`generate_review_report`, which owns the inventory scan,
documentation/bibliography/infrastructure audits, review-summary
subprocess invocation, and markdown report assembly.
"""

from __future__ import annotations

import ast
import datetime
import importlib.util
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import yaml


def project_paths() -> tuple[Path, Path, Path]:
    """Resolve the three paths ``generate_review_report`` needs: this
    project's root, the repository root (derived from this file's
    location), and the ``output/review`` directory the report is written
    into.
    """
    project_root = Path(__file__).resolve().parent.parent
    # project_root is projects/templates/<name>/; repo root is three levels up.
    template_root = project_root.parents[2]
    review_dir = project_root / "output" / "review"
    return project_root, template_root, review_dir


def H(text: str, level: int = 1) -> str:
    """Render *text* as a Markdown ATX heading at the given *level* (e.g.
    ``H("Title", level=2)`` returns ``"## Title"``).
    """
    return "#" * level + f" {text}"


def check_anchors(text: str) -> list[str]:
    """Check anchors."""
    anchors = re.findall(r"#([\w-]+)", text)
    broken = []
    for a in set(anchors):
        if re.search(rf"^#{{1,3}} .*\b{a}\b", text, flags=re.MULTILINE) or re.search(rf"<a[^>]+id=['\"]{a}['\"]", text):
            continue
        broken.append(a)
    return broken


def _subprocess_env() -> dict[str, str]:
    env = dict(os.environ)
    # This module lives at projects/templates/<name>/src/review_report.py,
    # the same depth as the original scripts/ location; repo root is five
    # levels up from this file.
    template_root = str(Path(__file__).resolve().parents[4])
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
    """Scan every non-underscore ``src/*.py`` module via ``ast`` and record
    which real ``infrastructure.*`` modules each one imports.

    Returns a ``module -> {importing filenames}`` map (section 4 of the
    review report renders this directly). An import is only counted when
    the target module/package actually exists on disk under
    ``template_root / "infrastructure"``; unresolvable imports are
    silently skipped rather than reported as usage.
    """
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
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("infrastructure."):
                parts = node.module.split(".")
                rel = Path(*parts[1:])
                exists = (infra_root_p / rel.with_suffix(".py")).exists() or (
                    infra_root_p / rel / "__init__.py"
                ).exists()
                if exists:
                    infra_imports_used[node.module].add(py.name)
    return infra_imports_used


def _bs(project_root: Path, d: str) -> int:
    return len(os.listdir(project_root / d))


def generate_review_report(project_root: Path, template_root: Path, review_dir: Path) -> int:
    """Run the review subprocess (if needed), audit the project, and write
    ``output/review/REVIEW_REPORT.md``. Also prints a short summary block.

    Returns 0 (the report is always written; a failing review subprocess is
    reflected in the report body, not the process exit code).
    """
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
    entries = sorted(e for e in os.listdir(project_root) if e not in ignored and not e.startswith("."))
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
    agents_sects = [line[4:].strip() for line in agents_text.splitlines() if line.startswith("### ")]
    readme_sects = [line[3:].strip() for line in readme_text.splitlines() if line.startswith("## ")]
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
    #
    # Every gap/action string below is derived from a live computation this
    # function already performs (cite_keys, review_cfg stage list, real
    # filesystem checks) rather than a fixed narrative string. This keeps the
    # table internally consistent with sections 3/4/6 for any input, instead
    # of hardcoding facts (e.g. "0 inline citations") that only matched one
    # historical fixture and silently contradicted the live-computed count
    # reported a few sections above.
    lines.append(H("7.  GAPS & IMMEDIATE RECOMMENDATIONS", 2))
    lines.append("")

    def _stage_enabled(name: str) -> bool:
        return next(
            (bool(st.get("enabled", True)) for st in review_cfg["review"]["stages"] if st["name"] == name),
            False,
        )

    if cite_keys:
        bib_gap = f"99_references.md defers to .bib; {len(cite_keys)} inline citation(s) present in manuscript."
        bib_action = "Citations present — confirm every key resolves in references.bib (see section 3)."
    else:
        bib_gap = "99_references.md defers to .bib; 0 inline citations in manuscript."
        bib_action = "Manually insert citations OR regenerate after z script."

    reading_report_present = (project_root / "output" / "reading_report.md").exists()
    pdf_dir = project_root / "output" / "pdf"
    pdf_present = pdf_dir.exists() and any(pdf_dir.glob("*_combined.pdf"))
    output_gap = (
        f"output/reading_report.md {'present' if reading_report_present else 'absent'}; "
        f"final PDF {'present' if pdf_present else 'absent'}."
    )
    output_action = (
        "Re-run the top-level PDF-rendering pipeline stage periodically to keep the PDF fresh."
        if pdf_present
        else "Run z_generate_manuscript_variables.py then render PDF."
    )

    links_enabled = _stage_enabled("markdown_links")
    links_gap = (
        "`markdown_links` stage is enabled — see output/review/stage_markdown_links.json for the current count."
        if links_enabled
        else "`markdown_links` stage is disabled by default (avoids false positives on infra/external docs)."
    )
    links_action = (
        "Review stage_markdown_links.json and fix or allowlist flagged links."
        if links_enabled
        else "Enable `markdown_links` once an allowlist covers infra dirs + external docs."
    )

    prerender_enabled = _stage_enabled("prerender_validation")
    prerender_gap = (
        "`prerender_validation` stage is enabled — see "
        "output/review/stage_prerender_validation.json for the current findings."
        if prerender_enabled
        else "`prerender_validation` stage is disabled by default."
    )
    prerender_action = (
        "Add stub @misc entries for figure/section labels flagged as undefined citations."
        if prerender_enabled
        else "Enable `prerender_validation` once pandoc-crossref labels are allowlisted."
    )

    test_suite_enabled = _stage_enabled("test_suite_health")
    pytest_available = importlib.util.find_spec("pytest") is not None
    test_gap = (
        f"`test_suite_health` stage is {'enabled' if test_suite_enabled else 'disabled by default'}; "
        f"pytest is {'available' if pytest_available else 'unavailable'} in this environment."
    )
    test_action = (
        "Enable `test_suite_health` to enforce the coverage gate as part of the review run."
        if pytest_available
        else "Install dev deps (`uv pip install -e .[dev]`) OR keep `test_suite_health` disabled."
    )

    rows = [
        ("1", "Bibliography", bib_gap, bib_action),
        ("2", "Output artifacts", output_gap, output_action),
        ("3", "Markdown links", links_gap, links_action),
        ("4", "Prerender", prerender_gap, prerender_action),
        ("5", "Test suite", test_gap, test_action),
    ]
    header = "| # | Category   | Gap                                          | Recommended Action                    |"  # noqa: E501
    divider = (
        "|---|------------|----------------------------------------------|---------------------------------------|"  # noqa: E501
    )
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
        ("  7.  `output/reading_report.md` summarises search strategy, backend results, token counts."),
        ("  8.  Consider adding `docs/analysis/` linking findings to infrastructure methods."),
        ("  9.  Keep thin orchestration — src modules call infra methods; document in AGENTS.md."),
        "",
        "**E.  Configuration Hygiene**",
        (" 10.  Exclude `.venv/` from link-validation in CI via allowlist, or keep `markdown_links` disabled."),
        "",
    ]
    lines.extend(nxt)

    # 9. Intelligence augmentation facts
    #
    # As with section 7, these bullets reference the same live-computed
    # variables used elsewhere in this report (infra_imports_used from
    # section 4, cite_keys from section 3, pdf_present from section 7)
    # instead of a separately hardcoded fact list that could drift out of
    # sync with them.
    lines.append(H("9.  INTELLIGENCE AUGMENTATION — FACTS MEMORISED", 2))
    infra_mods_summary = ", ".join(sorted(infra_imports_used)) if infra_imports_used else "none detected"
    next_step = (
        "run the top-level pipeline's PDF-rendering stage to refresh the combined PDF"
        if pdf_present
        else "run z_generate_manuscript_variables.py to substitute {{...}}, then enable "
        "variables_resolved/output_integrity and proceed to PDF rendering"
    )
    lines.append(
        f"""
  • Template_search_project: literature-search exemplar using infrastructure.search
    + infrastructure.reference, orchestrated by thin scripts pipeline.
  • Review system: scripts/review + review_config.yaml + src/analysis.
  • Infra usage ({len(infra_imports_used)} module(s)): {infra_mods_summary}.
  • Bibliography: {len(cite_keys)} inline citation key(s) detected in manuscript (see section 3).
  • Next: {next_step}.
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

    print(f"  • Inventory: src({_bs(project_root, 'src')}) tests({_bs(project_root, 'tests')})")
    scripts_list = ", ".join(sorted(os.listdir(project_root / "scripts")))
    print("  • Scripts: " + scripts_list)
    print("  • Review system: scripts/review + review_config.yaml")
    print(f"  • Review subprocess exit: {review_exit}")
    cite_note = f"  • Bibliography: {bib_entries} bib entries; {len(cite_keys)} inline citations detected"
    print(cite_note)
    print(f"  • Infra modules used: {dict(infra_imports_used)}")
    print(sep)
    return 0


__all__ = [
    "H",
    "check_anchors",
    "collect_infra_imports",
    "ensure_review_summary",
    "generate_review_report",
    "project_paths",
]
