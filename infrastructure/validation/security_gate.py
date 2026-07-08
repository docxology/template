"""Security scanning gate — bandit, safety, pip-audit aggregation."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infrastructure.core.logging.constants import BANNER_WIDTH

SEVERITY_LEVELS = ("LOW", "MEDIUM", "HIGH")
REQUIRED_TOOLS = ("bandit", "pip_audit")
OPTIONAL_TOOLS = ("safety",)
TOOLS = (*REQUIRED_TOOLS, *OPTIONAL_TOOLS)


def _run_bandit(repo_root: Path) -> dict[str, Any]:
    try:
        subprocess.run(
            ["uv", "run", "bandit", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("WARNING: bandit not installed, skipping")
        return {"status": "skipped", "reason": "bandit not installed", "tool": "bandit"}

    cmd = [
        "uv",
        "run",
        "bandit",
        "-c",
        str(repo_root / "bandit.yaml"),
        "-r",
        "-ll",
        "-f",
        "json",
        "-q",
        str(repo_root / "infrastructure"),
        str(repo_root / "scripts"),
        str(repo_root / "projects"),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        output = result.stdout if result.stdout else result.stderr
        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            print("WARNING: bandit output not valid JSON")
            return {"status": "skipped", "reason": "bandit output not valid JSON", "tool": "bandit"}
        findings = data.get("results", [])
        summary: dict[str, int] = {"total": len(findings)}
        for severity in SEVERITY_LEVELS:
            summary[severity.lower()] = sum(1 for f in findings if f.get("issue_severity", "").upper() == severity)
        print(f"bandit: {summary.get('total', 0)} issues found")
        return {"findings": findings, "summary": summary, "tool": "bandit"}
    except subprocess.TimeoutExpired:
        print("WARNING: bandit timed out")
        return {"status": "skipped", "reason": "bandit timed out", "tool": "bandit"}
    except OSError as exc:
        print(f"WARNING: bandit execution error: {exc}")
        return {"status": "skipped", "reason": str(exc), "tool": "bandit"}


def _run_safety(repo_root: Path) -> dict[str, Any]:
    try:
        subprocess.run(
            ["safety", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("WARNING: safety not installed, skipping")
        return {"status": "skipped", "reason": "safety not installed", "tool": "safety"}

    if not any(repo_root.glob(p) for p in ("pyproject.toml", "requirements*.txt")):
        print("No dependency files found, skipping safety")
        return {"status": "skipped", "reason": "no dependency files found", "tool": "safety"}

    cmd = ["safety", "check", "--json", "--full-report", "-r", str(repo_root / "pyproject.toml")]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        try:
            data = json.loads(result.stdout) if result.stdout else {}
        except json.JSONDecodeError:
            print("WARNING: safety output not valid JSON")
            return {"status": "skipped", "reason": "safety output not valid JSON", "tool": "safety"}
        vulns = data.get("vulnerabilities", [])
        summary: dict[str, int] = {"total": len(vulns)}
        for severity in SEVERITY_LEVELS:
            summary[severity.lower()] = sum(1 for v in vulns if v.get("severity", "").upper() == severity)
        print(f"safety: {summary.get('total', 0)} vulnerabilities found")
        return {"findings": vulns, "summary": summary, "tool": "safety"}
    except subprocess.TimeoutExpired:
        print("WARNING: safety timed out")
        return {"status": "skipped", "reason": "safety timed out", "tool": "safety"}
    except OSError as exc:
        print(f"WARNING: safety execution error: {exc}")
        return {"status": "skipped", "reason": str(exc), "tool": "safety"}


def _run_pip_audit(repo_root: Path) -> dict[str, Any]:
    try:
        subprocess.run(
            ["uv", "run", "pip-audit", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("WARNING: pip-audit not installed, skipping")
        return {"status": "skipped", "reason": "pip-audit not installed", "tool": "pip_audit"}

    cmd = [
        "uv",
        "run",
        "pip-audit",
        "--format",
        "json",
        "--progress-spinner",
        "off",
        "--desc",
        *_pip_audit_ignore_args(repo_root),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        try:
            data = json.loads(result.stdout) if result.stdout else {}
        except json.JSONDecodeError:
            try:
                data = json.loads(result.stderr) if result.stderr else {}
            except json.JSONDecodeError:
                print("WARNING: pip-audit output not valid JSON")
                return {"status": "skipped", "reason": "pip-audit output not valid JSON", "tool": "pip_audit"}
        vulns = _pip_audit_vulnerabilities(data)
        summary: dict[str, int] = {"total": len(vulns)}
        for severity in SEVERITY_LEVELS:
            summary[severity.lower()] = sum(1 for v in vulns if v.get("severity", "").lower() == severity.lower())
        print(f"pip-audit: {summary.get('total', 0)} vulnerabilities found")
        return {"findings": vulns, "summary": summary, "tool": "pip_audit"}
    except subprocess.TimeoutExpired:
        print("WARNING: pip-audit timed out")
        return {"status": "skipped", "reason": "pip-audit timed out", "tool": "pip_audit"}
    except OSError as exc:
        print(f"WARNING: pip-audit execution error: {exc}")
        return {"status": "skipped", "reason": str(exc), "tool": "pip_audit"}


def _pip_audit_ignore_args(repo_root: Path) -> list[str]:
    ignore_file = repo_root / ".github" / "pip-audit-ignore.txt"
    if not ignore_file.exists():
        return []
    args: list[str] = []
    for raw in ignore_file.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            args.extend(["--ignore-vuln", line])
    return args


def _pip_audit_vulnerabilities(data: dict[str, Any]) -> list[dict[str, Any]]:
    top_level = data.get("vulnerabilities")
    if isinstance(top_level, list):
        return [v for v in top_level if isinstance(v, dict)]
    dependencies = data.get("dependencies")
    if not isinstance(dependencies, list):
        return []
    vulns: list[dict[str, Any]] = []
    for dependency in dependencies:
        if not isinstance(dependency, dict):
            continue
        for vuln in dependency.get("vulns", []):
            if isinstance(vuln, dict):
                vulns.append(vuln)
    return vulns


def aggregate_security_findings(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Process aggregate security findings."""
    aggregated: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "severity_counts": {s: 0 for s in SEVERITY_LEVELS},
        "tool_counts": {t: 0 for t in TOOLS},
        "required_tools": list(REQUIRED_TOOLS),
        "optional_tools": list(OPTIONAL_TOOLS),
        "tools_run": [],
        "skipped_tools": [],
        "failed_tools": [],
        "blocking_findings": [],
        "total_findings": 0,
        "has_high_severity": False,
        "has_required_tool_failures": False,
        "has_blocking_findings": False,
    }
    for result in results:
        tool = result.get("tool", "unknown")
        if result.get("status") == "skipped":
            skipped = {
                "tool": tool,
                "reason": result.get("reason", "unknown"),
                "required": tool in REQUIRED_TOOLS,
            }
            aggregated["skipped_tools"].append(skipped)
            if tool in REQUIRED_TOOLS:
                aggregated["failed_tools"].append(skipped)
            continue
        aggregated["tools_run"].append(tool)
        summary = result.get("summary", {})
        for severity in SEVERITY_LEVELS:
            aggregated["severity_counts"][severity] += summary.get(severity.lower(), 0)
        aggregated["tool_counts"][tool] = summary.get("total", 0)
        aggregated["total_findings"] += summary.get("total", 0)
        if tool in REQUIRED_TOOLS and summary.get("total", 0) > 0:
            aggregated["blocking_findings"].append({"tool": tool, "count": summary.get("total", 0)})
    aggregated["has_high_severity"] = aggregated["severity_counts"]["HIGH"] > 0
    aggregated["has_required_tool_failures"] = bool(aggregated["failed_tools"])
    aggregated["has_blocking_findings"] = bool(aggregated["blocking_findings"])
    return aggregated


def write_security_report(report: dict[str, Any], report_path: Path) -> None:
    """Process write security report."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Security report written to {report_path}")


def run_security_scan(repo_root: Path) -> tuple[dict[str, Any], int]:
    """Run security scanners and return (report, exit_code)."""
    print("=" * BANNER_WIDTH)
    print("SECURITY SCAN GATE")
    print("=" * BANNER_WIDTH)

    results: list[dict[str, Any]] = []
    print("\n[1/3] Running bandit...")
    bandit_result = _run_bandit(repo_root)
    results.append(bandit_result)

    print("\n[2/3] Running safety...")
    safety_result = _run_safety(repo_root)
    results.append(safety_result)

    print("\n[3/3] Running pip-audit...")
    pip_audit_result = _run_pip_audit(repo_root)
    results.append(pip_audit_result)

    print("\nAggregating findings...")
    report = aggregate_security_findings(results)

    print("\n" + "=" * BANNER_WIDTH)
    print("SECURITY SCAN SUMMARY")
    print("=" * BANNER_WIDTH)
    print(f"Tools run: {', '.join(report['tools_run']) if report['tools_run'] else 'none'}")
    print(f"Total findings: {report['total_findings']}")
    print("\nSeverity breakdown:")
    for severity in SEVERITY_LEVELS:
        count = report["severity_counts"][severity]
        marker = " [HIGH - FAIL]" if severity == "HIGH" and count > 0 else ""
        print(f"  {severity}: {count}{marker}")
    print("\nTool breakdown:")
    for tool, count in report["tool_counts"].items():
        print(f"  {tool}: {count}")
    if report["skipped_tools"]:
        print("\nSkipped tools:")
        for row in report["skipped_tools"]:
            requirement = "required" if row["required"] else "optional"
            print(f"  {row['tool']} ({requirement}): {row['reason']}")

    report_path = repo_root / ".cache" / "template" / "security_report.json"
    write_security_report(report, report_path)

    if report["has_required_tool_failures"]:
        failed = ", ".join(row["tool"] for row in report["failed_tools"])
        print(f"\nFAILURE: Required security tools did not complete: {failed}")
        return report, 1
    if report["has_blocking_findings"]:
        failed = ", ".join(f"{row['tool']} ({row['count']})" for row in report["blocking_findings"])
        print(f"\nFAILURE: Required security tools reported blocking findings: {failed}")
        return report, 1
    if report["has_high_severity"]:
        print("\nFAILURE: HIGH severity security issues detected!")
        return report, 1
    print("\nSUCCESS: No blocking security issues found.")
    return report, 0
