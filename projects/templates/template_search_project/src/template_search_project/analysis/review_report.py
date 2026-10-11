"""Deep-review report generation for template_search_project.

Extracted from ``scripts/zz_generate_review_report.py`` (thin-orchestrator
refactor): the script now only resolves paths and calls
:func:`generate_review_report`, which owns the inventory scan,
documentation/bibliography/infrastructure audits and stable current-source
report assembly. Local operational receipt inspection is a separate utility.
"""

from __future__ import annotations

import ast
import hashlib
import datetime
import importlib.util
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

from .provider_paths import platform_import_modules, platform_module_exists, platform_package_root
from .review_execution import DEFAULT_REVIEW_TIMEOUT, run_review_child, review_output_settings, review_stage_key
from infrastructure.core.files.secure_write import atomic_write_text_confined, read_text_confined
from tempfile import TemporaryDirectory
from .report_inputs import capture_report_inputs, ReportInputs
from .analysis import validate_bibliography_completeness, audit_infrastructure_imports


def project_paths(project_root: Path) -> tuple[Path, Path]:
    """Resolve explicit project data paths independently of provider location."""
    project = project_root.resolve(strict=True)
    return project, project / "output" / "review"


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


def _subprocess_env(base_env: dict[str, str] | None = None) -> dict[str, str]:
    """Keep application settings without propagating ambient Python imports."""
    env = dict(os.environ if base_env is None else base_env)
    env.pop("PYTHONPATH", None)
    return env


def configured_review_paths(project_root: Path) -> tuple[Path, str]:
    """Read actual local operational configuration; history never supplies it."""
    project = project_root.resolve(strict=True)
    config_path = project / "review_config.yaml"
    if config_path.exists() or config_path.is_symlink():
        config = yaml.safe_load(read_text_confined(project, config_path))
        if not isinstance(config, dict) or not isinstance(config.get("review"), dict):
            raise ValueError("review configuration must contain a review mapping")
        review = config["review"]
    else:
        review = {}
    rows = review.get("stages", [])
    if not isinstance(rows, list) or any(
        not isinstance(row, dict) or not isinstance(row.get("name"), str) for row in rows
    ):
        raise ValueError("review stages must be named mappings")
    names: set[str] = set()
    for row in rows:
        names.add(review_stage_key(row, names))
    directory, summary = review_output_settings(review, names)
    candidate = project / directory
    current = project
    for part in candidate.relative_to(project).parts:
        current /= part
        if current.is_symlink() or current.exists() and not current.is_dir():
            raise ValueError("local review receipts require confined real directories")
    if candidate.resolve() != candidate:
        raise ValueError("local review receipt directory cannot redirect outside the project")
    return candidate, summary


def ensure_review_summary(
    project_root: Path,
    review_dir: Path | None = None,
    *,
    timeout: float = DEFAULT_REVIEW_TIMEOUT,
) -> tuple[dict, int, str]:
    """Inspect local operational data and process diagnostics, never public acceptance.

    Public report generation does not consume these cached/runtime claims.
    The actual review coordinator remains responsible for fresh completion.
    """
    configured, summary_name = configured_review_paths(project_root)
    if review_dir is not None and review_dir.absolute() != configured:
        raise ValueError("review receipt reader must use the configured local operational directory")
    review_dir = configured
    summary_path = review_dir / summary_name
    if summary_path.exists() or summary_path.is_symlink():
        summary = json.loads(read_text_confined(project_root, summary_path))
        return summary, summary.get("overall_exit_code", 0), ""

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

    proc = run_review_child(
        [sys.executable, "-I", str(review_exe), "--project-root", str(project_root)],
        cwd=project_root,
        env=_subprocess_env(),
        timeout=timeout,
        policy_id="search-review-report",
    )
    tail = ""
    if proc.stdout or proc.stderr or proc.command_error:
        tail = (proc.stdout + "\n" + proc.stderr + "\n" + proc.command_error)[-2000:]

    if summary_path.exists() or summary_path.is_symlink():
        summary = json.loads(read_text_confined(project_root, summary_path))
        return summary, proc.returncode, tail

    placeholder = {
        "total": 0,
        "passed": 0,
        "failed": 1,
        "skipped": 0,
        "overall_exit_code": 1,
    }
    return placeholder, proc.returncode or 1, tail or "review finished without summary.json"


def collect_infra_imports(project_root: Path) -> defaultdict[str, set[str]]:
    """Scan every non-underscore ``src/*.py`` module via ``ast`` and record
    which real ``infrastructure.*`` modules each one imports.

    Returns a ``module -> {importing filenames}`` map (section 4 of the
    review report renders this directly). An import is only counted when
    the target module/package exists under the actual loaded platform
    package. An unrelated ancestor or reference checkout cannot supply it;
    unresolvable imports are omitted from this usage inventory.
    """
    infra_root_p = platform_package_root()
    infra_imports_used: defaultdict[str, set[str]] = defaultdict(set)
    for py in sorted((project_root / "src").rglob("*.py")):
        if py.name.startswith("_"):
            continue
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for module in platform_import_modules(tree):
            if platform_module_exists(module, infra_root_p):
                infra_imports_used[module].add(py.name)
    return infra_imports_used


def _bs(project_root: Path, d: str) -> int:
    return len(os.listdir(project_root / d))


def _stable_report_timestamp() -> str:
    """Return a reproducible report timestamp from ``SOURCE_DATE_EPOCH``.

    A missing epoch is represented explicitly instead of consulting the wall
    clock, so two offline report generations remain byte-identical by default.
    """
    raw_epoch = os.environ.get("SOURCE_DATE_EPOCH", "").strip()
    if not raw_epoch:
        return "SOURCE_DATE_EPOCH unset (deterministic build)"
    try:
        epoch = int(raw_epoch)
    except ValueError:
        return "invalid SOURCE_DATE_EPOCH (deterministic build)"
    return datetime.datetime.fromtimestamp(epoch, tz=datetime.timezone.utc).isoformat(timespec="seconds")


def _stable_project_label(project_root: Path) -> str:
    """Label the own project without guessing a repository or exposing paths."""
    project = project_root.resolve()
    if project.name != "template_search_project":
        return "fixture-project"
    if project.parent.name == "templates" and project.parent.parent.name == "projects":
        return "projects/templates/template_search_project"
    return project.name


def generate_review_report(project_root: Path, review_dir: Path) -> int:
    """Generate informational findings only from one held own-input snapshot."""
    original = project_root.resolve(strict=True)
    admitted = original.stat()
    root_identity = (admitted.st_dev, admitted.st_ino)
    # Validate actual configured local paths before any pure snapshot work.
    configured_review_paths(original)
    inputs = capture_report_inputs(original, root_identity)
    with TemporaryDirectory(prefix="search-report-inputs-") as temporary:
        snapshot = Path(temporary) / original.name
        snapshot.mkdir()
        inputs.materialize(snapshot)
        return _generate_review_report(
            snapshot, review_dir, publication_root=original, root_identity=root_identity, inputs=inputs
        )


def _generate_review_report(
    project_root: Path,
    review_dir: Path,
    *,
    publication_root: Path,
    root_identity: tuple[int, int],
    inputs: ReportInputs,
) -> int:
    """Audit current own source/domain inputs and write
    ``output/review/REVIEW_REPORT.md``. Also prints a short summary block.

    Returns 0 when this informational artifact is generated from stable current
    inputs. This does not execute or accept the configured review pipeline.
    """
    project_root = project_root.resolve(strict=True)
    source_before = dict(inputs.manifest)
    frozen_stat = project_root.stat()
    frozen_identity = (frozen_stat.st_dev, frozen_stat.st_ino)
    frozen_before = capture_report_inputs(project_root, frozen_identity)
    if frozen_before.files != inputs.files or frozen_before.directories != inputs.directories:
        raise ValueError("materialized report input snapshot differs from admitted bytes/inventory")
    review_cfg = yaml.safe_load(read_text_confined(project_root, project_root / "review_config.yaml"))
    operational_dir, summary_name = configured_review_paths(project_root)
    bibliography = validate_bibliography_completeness(project_root)
    imports = audit_infrastructure_imports(project_root)

    bib_path = project_root / "manuscript" / "references.bib"
    bib_text = bib_path.read_text(encoding="utf-8")
    bib_entries = bib_text.count("@")

    infra_imports_used = collect_infra_imports(project_root)

    lines: list[str] = []

    lines.append(H("TEMPLATE SEARCH PROJECT — DEEP REVIEW REPORT", 1))
    project_label = _stable_project_label(publication_root)
    lines.append(f"**Generated:** {_stable_report_timestamp()}")
    lines.append(f"**Project root:** `{project_label}`")
    lines.append("**Repository root:** `.` (portable report label)")
    lines.append("**Review orchestrator:** `scripts/review`")
    lines.append("**Purpose:** informational current-source findings; this report is not run or release acceptance.")
    lines.append("**Operational completion:** run `scripts/review`; local receipts are separate from this report.")
    local_summary = (operational_dir / summary_name).relative_to(project_root).as_posix()
    lines.append(f"**Configured local summary:** `{local_summary}` (not public acceptance)")
    source_digest = hashlib.sha256(json.dumps(source_before, sort_keys=True).encode()).hexdigest()
    lines.append(f"**Consumed own-source and presence snapshot SHA-256:** `{source_digest}`")
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
bespoke checks implemented in template_search_project.analysis.

**Artifacts:**
  • review_config.yaml        stage enable/disable configuration
  • scripts/review            unified single-entrypoint orchestrator
  • scripts/zz_generate_review_report.py  informational source/domain reporter
  • src/template_search_project/analysis/           custom-stage functions

**Default enabled stages (when run via scripts/review):**
  1. bibtex_validation         infrastructure.reference.citation.cli validate
  2. bibliography_completeness custom — all [@key]s exist in references.bib
  3. infrastructure_usage      custom — audit src/ import paths
  4. determinism_check          custom — cache/seed + temperature=0

**Disabled by default** (require pipeline completion / dev deps):
  prerender_validation, markdown_links, variables_resolved,
  output_integrity, test_suite_health

**Run:**  uv run python scripts/review   (or add --list, --stage …)
**Operational outputs:** configured output/.pipeline/review/stage_*.json + summary.json (local only)
**Public report:** output/review/REVIEW_REPORT.md (recomputed source/domain findings)
"""
    )
    lines.append("")

    # 6. Current domain findings are recomputed, never imported from receipts.
    lines.append(H("6.  CURRENT SOURCE AND DOMAIN FINDINGS", 2))
    lines.append(f"**Bibliography completeness:** {bibliography.status}")
    missing_keys = (bibliography.details or {}).get("missing_keys", [])
    lines.append(f"**Missing bibliography keys:** {len(missing_keys)}")
    lines.append(f"**Infrastructure import validity:** {imports.status}")
    lines.append(f"**Infrastructure import issues:** {len((imports.details or {}).get('issues', []))}")
    lines.append("**Configured stages (execution results remain local):**")
    for stage in review_cfg["review"]["stages"]:
        enabled = stage.get("enabled", True)
        if type(enabled) is not bool:
            raise ValueError("configured review stage enabled must be a boolean")
        lines.append(f"  {'ENABLED' if enabled else 'DISABLED'}  {stage['name']}")
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

    reading_report_present = inputs.presence["reading_report"]
    pdf_present = inputs.presence["combined_pdf"]
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
        "`markdown_links` stage is enabled — see `scripts/review` local stage receipt for the current count."
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
        "`prerender_validation` stage is enabled — see `scripts/review` local stage receipt for the current findings."
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
  • Review system: scripts/review + review_config.yaml + src/template_search_project/analysis.
  • Infra usage ({len(infra_imports_used)} module(s)): {infra_mods_summary}.
  • Bibliography: {len(cite_keys)} inline citation key(s) detected in manuscript (see section 3).
  • Next: {next_step}.
"""
    )

    current = capture_report_inputs(publication_root, root_identity)
    if dict(current.manifest) != source_before or current.identities != inputs.identities:
        raise ValueError("report source/data changed during current findings computation")
    frozen_after = capture_report_inputs(project_root, frozen_identity)
    if frozen_after.manifest != frozen_before.manifest or frozen_after.identities != frozen_before.identities:
        raise ValueError("frozen report source/data changed during findings computation")
    public_dir = publication_root / "output" / "review"
    if review_dir.absolute() != public_dir.absolute():
        raise ValueError("public review report must use output/review independently of local receipts")
    out = public_dir / "REVIEW_REPORT.md"
    atomic_write_text_confined(
        publication_root, out, "\n".join(lines).rstrip() + "\n", expected_root_identity=root_identity
    )
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
    actual_operational_dir = publication_root / operational_dir.relative_to(project_root)
    print(f"  • Operational receipts (local only): {actual_operational_dir}")
    print("  • Informational report generation; configured execution is not accepted here")
    cite_note = f"  • Bibliography: {bib_entries} bib entries; {len(cite_keys)} inline citations detected"
    print(cite_note)
    print(f"  • Infra modules used: {dict(infra_imports_used)}")
    print(sep)
    return 0


__all__ = [
    "H",
    "check_anchors",
    "collect_infra_imports",
    "configured_review_paths",
    "ensure_review_summary",
    "generate_review_report",
    "project_paths",
]
