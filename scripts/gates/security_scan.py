"""Security scanning gate for the template pipeline.

This gate runs security scanners (bandit, safety, pip-audit) on the repository
and aggregates findings. It fails if any HIGH severity issues are found.

Tools run (gracefully skipped if not installed):
  - bandit: Python security linter (JSON output)
  - safety: Checks dependencies for known vulnerabilities (JSON if available)
  - pip-audit: Audits installed packages for vulnerabilities (JSON if available)

Report written to .cache/template/security_report.json with counts by severity and tool.
Exit codes:
  0 - No HIGH severity findings (or tools missing - non-blocking)
  1 - HIGH severity findings detected
  2 - Gate execution error
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Configuration
REPO_ROOT = Path(__file__).parents[2].resolve()
REPORT_PATH = REPO_ROOT / '.cache' / 'template' / 'security_report.json'

# Severity levels we care about
SEVERITY_LEVELS = ['LOW', 'MEDIUM', 'HIGH']
TOOLS = ['bandit', 'safety', 'pip_audit']


def _run_bandit() -> Dict[str, Any]:
    """Run bandit security scanner on Python files.

    Returns:
        Dict with findings summary or empty dict if bandit not available.
    """
    try:
        # Check if bandit is available
        subprocess.run(
            ['bandit', '--version'],
            capture_output=True,
            text=True,
            check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("WARNING: bandit not installed, skipping")
        return {}

    # Run bandit with JSON output on the repository (excluding virtualenvs and caches)
    cmd = [
        'bandit',
        '-r',               # Recursive
        '-f', 'json',       # JSON format
        '-q',               # Quiet: suppress non-JSON logs
        '--severity-level', 'LOW',  # Include all severities
        '--exclude', '.venv,venv,env,.git,__pycache__,.cache,build,dist',
        str(REPO_ROOT),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )

        # bandit returns non-zero if issues found, which is expected
        # We still want to parse output
        output = result.stdout if result.stdout else result.stderr

        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            print("WARNING: bandit output not valid JSON")
            return {}

        findings = data.get('results', [])
        summary = {'total': len(findings)}

        for severity in SEVERITY_LEVELS:
            count = sum(1 for f in findings if f.get('issue_severity', '').upper() == severity)
            summary[severity.lower()] = count

        print(f"bandit: {summary.get('total', 0)} issues found")
        return {'findings': findings, 'summary': summary, 'tool': 'bandit'}

    except subprocess.TimeoutExpired:
        print("WARNING: bandit timed out")
        return {}
    except Exception as e:
        print(f"WARNING: bandit execution error: {e}")
        return {}


def _run_safety() -> Dict[str, Any]:
    """Run safety check on dependencies.

    Returns:
        Dict with findings summary or empty dict if safety not available.
    """
    try:
        subprocess.run(
            ['safety', '--version'],
            capture_output=True,
            text=True,
            check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("WARNING: safety not installed, skipping")
        return {}

    # Check if pyproject.toml or requirements exist
    has_deps = any(REPO_ROOT.glob(p) for p in ['pyproject.toml', 'requirements*.txt'])
    if not has_deps:
        print("No dependency files found, skipping safety")
        return {}

    # Run safety in JSON mode (check-mode=full for local files)
    cmd = [
        'safety',
        'check',
        '--json',  # JSON output
        '--full-report',  # Full details
        '-r', str(REPO_ROOT / 'pyproject.toml'),  # Check pyproject.toml
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )

        # Safety exits with code 0 for no vulnerabilities, non-zero for vulns
        # Parse JSON output
        try:
            data = json.loads(result.stdout) if result.stdout else {}
        except json.JSONDecodeError:
            print("WARNING: safety output not valid JSON")
            return {}

        # Safety JSON structure: {'vulnerabilities': [{...}]}
        vulns = data.get('vulnerabilities', [])
        summary = {'total': len(vulns)}

        for severity in SEVERITY_LEVELS:
            # Safety uses lowercase severity names
            count = sum(1 for v in vulns if v.get('severity', '').upper() == severity)
            summary[severity.lower()] = count

        print(f"safety: {summary.get('total', 0)} vulnerabilities found")
        return {'findings': vulns, 'summary': summary, 'tool': 'safety'}

    except subprocess.TimeoutExpired:
        print("WARNING: safety timed out")
        return {}
    except Exception as e:
        print(f"WARNING: safety execution error: {e}")
        return {}


def _run_pip_audit() -> Dict[str, Any]:
    """Run pip-audit on installed packages and dependency files.

    Returns:
        Dict with findings summary or empty dict if pip-audit not available.
    """
    try:
        subprocess.run(
            ['pip-audit', '--version'],
            capture_output=True,
            text=True,
            check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("WARNING: pip-audit not installed, skipping")
        return {}

    # Run pip-audit on the environment and local dependencies
    cmd = [
        'pip-audit',
        '--format', 'json',  # JSON output
        '--requirement', str(REPO_ROOT / 'pyproject.toml'),  # Scan project deps
        '--progress-spinner', 'off',  # Avoid terminal control chars
        '--desc',  # Include vulnerability descriptions
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )

        # pip-audit exits non-zero if vulnerabilities found (expected)
        try:
            data = json.loads(result.stdout) if result.stdout else {}
        except json.JSONDecodeError:
            # pip-audit may output to stderr on some versions
            try:
                data = json.loads(result.stderr) if result.stderr else {}
            except json.JSONDecodeError:
                print("WARNING: pip-audit output not valid JSON")
                return {}

        vulns = data.get('vulnerabilities', [])
        summary = {'total': len(vulns)}

        for severity in SEVERITY_LEVELS:
            # pip-audit uses 'low', 'medium', 'high' typically
            count = sum(1 for v in vulns if v.get('severity', '').lower() == severity.lower())
            summary[severity.lower()] = count

        print(f"pip-audit: {summary.get('total', 0)} vulnerabilities found")
        return {'findings': vulns, 'summary': summary, 'tool': 'pip_audit'}

    except subprocess.TimeoutExpired:
        print("WARNING: pip-audit timed out")
        return {}
    except Exception as e:
        print(f"WARNING: pip-audit execution error: {e}")
        return {}


def _aggregate_findings(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate findings from all tools into a summary report.

    Args:
        results: List of tool result dicts.

    Returns:
        Aggregated report dict.
    """
    aggregated = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'severity_counts': {s: 0 for s in SEVERITY_LEVELS},
        'tool_counts': {t: 0 for t in TOOLS},
        'tools_run': [],
        'total_findings': 0,
        'has_high_severity': False,
    }

    for result in results:
        tool = result.get('tool', 'unknown')
        aggregated['tools_run'].append(tool)

        summary = result.get('summary', {})
        for severity in SEVERITY_LEVELS:
            key = severity.lower()
            count = summary.get(key, 0)
            aggregated['severity_counts'][severity] += count

        aggregated['tool_counts'][tool] = summary.get('total', 0)
        aggregated['total_findings'] += summary.get('total', 0)

    # Check for any HIGH severity
    aggregated['has_high_severity'] = aggregated['severity_counts']['HIGH'] > 0

    return aggregated


def _write_report(report: Dict[str, Any]) -> None:
    """Write security report to JSON file.

    Args:
        report: Report dict to write.
    """
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Security report written to {REPORT_PATH}")


def run_gate() -> int:
    """Execute the security scanning gate.

    Runs bandit, safety, and pip-audit (if available), aggregates findings,
    and writes a JSON report. Fails if any HIGH severity issues are found.

    Returns:
        Exit code: 0 if no HIGH findings, 1 if HIGH found, 2 on error.
    """
    print("=" * 60)
    print("SECURITY SCAN GATE")
    print("=" * 60)

    # Collect results from all tools
    results: List[Dict[str, Any]] = []

    # Run bandit
    print("\n[1/3] Running bandit...")
    bandit_result = _run_bandit()
    if bandit_result:
        results.append(bandit_result)

    # Run safety
    print("\n[2/3] Running safety...")
    safety_result = _run_safety()
    if safety_result:
        results.append(safety_result)

    # Run pip-audit
    print("\n[3/3] Running pip-audit...")
    pip_audit_result = _run_pip_audit()
    if pip_audit_result:
        results.append(pip_audit_result)

    # Aggregate findings
    print("\nAggregating findings...")
    report = _aggregate_findings(results)

    # Print summary
    print("\n" + "=" * 60)
    print("SECURITY SCAN SUMMARY")
    print("=" * 60)
    print(f"Tools run: {', '.join(report['tools_run']) if report['tools_run'] else 'none'}")
    print(f"Total findings: {report['total_findings']}")
    print("\nSeverity breakdown:")
    for severity in SEVERITY_LEVELS:
        count = report['severity_counts'][severity]
        marker = " [HIGH - FAIL]" if severity == 'HIGH' and count > 0 else ""
        print(f"  {severity}: {count}{marker}")

    print("\nTool breakdown:")
    for tool, count in report['tool_counts'].items():
        print(f"  {tool}: {count}")

    # Write report
    _write_report(report)

    # Determine exit code
    if report['has_high_severity']:
        print("\nFAILURE: HIGH severity security issues detected!")
        return 1

    print("\nSUCCESS: No HIGH severity issues found.")
    return 0


if __name__ == '__main__':
    try:
        exit_code = run_gate()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nGate interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"FATAL: Security gate crashed: {e}")
        sys.exit(2)
