#!/usr/bin/env python3
"""Manuscript validation script for prose project.

This script performs comprehensive validation of the research manuscript including:
1. Markdown structure validation
2. Cross-reference integrity checking
3. Mathematical equation validation
4. Image reference validation
5. Link validation
6. Academic standards compliance
7. Output integrity verification
"""

import sys
from pathlib import Path
import json
from dataclasses import asdict

# Add project src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Add infrastructure imports (with graceful fallback)
try:
    # Ensure repo root is on path for infrastructure imports
    repo_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(repo_root))

    from infrastructure.validation import (
        validate_markdown,
        find_markdown_files,
        verify_file_integrity,
        verify_cross_references,
        verify_academic_standards,
        verify_output_integrity,
        generate_integrity_report,
        validate_copied_outputs,
        validate_output_structure,
        LinkValidator,
        run_comprehensive_audit,
        generate_audit_report,
    )
    INFRASTRUCTURE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Infrastructure modules not available: {e}")
    INFRASTRUCTURE_AVAILABLE = False


def audit_to_dict(audit_result):
    """Convert ScanResults object to dictionary for JSON serialization."""
    if audit_result is None:
        return {}

    # Check if it's a dataclass (ScanResults)
    if hasattr(audit_result, '__dataclass_fields__'):
        return asdict(audit_result)
    # Check if it has __dict__ attribute
    elif hasattr(audit_result, '__dict__'):
        return audit_result.__dict__
    # Otherwise, assume it's already a dict
    else:
        return audit_result


def validate_manuscript_structure():
    """Validate manuscript markdown structure."""
    if not INFRASTRUCTURE_AVAILABLE:
        print("⚠️  Skipping manuscript validation - infrastructure not available")
        return None

    print("Validating manuscript structure...")

    manuscript_dir = project_root / "manuscript"

    if not manuscript_dir.exists():
        print(f"❌ Manuscript directory not found: {manuscript_dir}")
        return None

    try:
        # Validate markdown files
        errors, exit_code = validate_markdown(manuscript_dir, project_root)

        if errors:
            print(f"❌ Found {len(errors)} validation errors:")
            for error in errors[:10]:  # Show first 10 errors
                print(f"   • {error}")
            if len(errors) > 10:
                print(f"   ... and {len(errors) - 10} more errors")
        else:
            print("✅ Manuscript structure is valid")

        return {
            "errors": errors,
            "exit_code": exit_code,
            "manuscript_dir": str(manuscript_dir)
        }

    except Exception as e:
        print(f"❌ Manuscript validation failed: {e}")
        return None


def validate_cross_references():
    """Validate cross-references across manuscript."""
    if not INFRASTRUCTURE_AVAILABLE:
        return None

    print("\nValidating cross-references...")

    manuscript_dir = project_root / "manuscript"
    markdown_files = list(manuscript_dir.glob("*.md"))

    if not markdown_files:
        print("⚠️  No markdown files found")
        return None

    try:
        # Check cross-references
        cross_ref_results = verify_cross_references(markdown_files)

        valid_refs = sum(1 for valid in cross_ref_results.values() if valid)
        total_refs = len(cross_ref_results)

        if total_refs == 0:
            print("⚠️  No cross-references found")
        else:
            print(f"✅ Cross-references: {valid_refs}/{total_refs} valid")

        return cross_ref_results

    except Exception as e:
        print(f"❌ Cross-reference validation failed: {e}")
        return None


def validate_academic_standards():
    """Validate compliance with academic writing standards."""
    if not INFRASTRUCTURE_AVAILABLE:
        return None

    print("\nValidating academic standards...")

    manuscript_dir = project_root / "manuscript"
    markdown_files = list(manuscript_dir.glob("*.md"))

    if not markdown_files:
        print("⚠️  No markdown files found")
        return None

    try:
        # Check academic standards
        standards_results = verify_academic_standards(markdown_files)

        compliant_standards = sum(1 for compliant in standards_results.values() if compliant)
        total_standards = len(standards_results)

        if total_standards == 0:
            print("⚠️  No standards to check")
        else:
            print(f"✅ Academic standards: {compliant_standards}/{total_standards} compliant")

        return standards_results

    except Exception as e:
        print(f"❌ Academic standards validation failed: {e}")
        return None


def validate_links():
    """Validate links and references in manuscript."""
    if not INFRASTRUCTURE_AVAILABLE:
        return None

    print("\nValidating links and references...")

    try:
        # Create link validator
        link_validator = LinkValidator(project_root)

        # Validate manuscript directory
        manuscript_dir = project_root / "manuscript"
        markdown_files = list(manuscript_dir.glob("*.md"))

        # Collect link issues from all markdown files
        all_link_issues = []
        for md_file in markdown_files:
            file_result = link_validator.validate_file_links(md_file)
            # file_result is a dict with 'valid' and 'broken' keys
            if isinstance(file_result, dict) and 'broken' in file_result:
                all_link_issues.extend(file_result['broken'])

        link_issues = all_link_issues

        if link_issues:
            print(f"❌ Found {len(link_issues)} link issues:")
            for issue in link_issues[:5]:  # Show first 5 issues
                if hasattr(issue, 'issue_type') and hasattr(issue, 'issue_message'):
                    issue_type = issue.issue_type
                    description = issue.issue_message
                else:
                    issue_type = 'unknown'
                    description = str(issue)
                print(f"   • {issue_type}: {description}")
            if len(link_issues) > 5:
                print(f"   ... and {len(link_issues) - 5} more issues")
        else:
            print("✅ All links and references are valid")

        return link_issues

    except Exception as e:
        print(f"❌ Link validation failed: {e}")
        return None


def validate_output_integrity():
    """Validate output directory integrity."""
    if not INFRASTRUCTURE_AVAILABLE:
        return None

    print("\nValidating output integrity...")

    output_dir = project_root / "output"

    if not output_dir.exists():
        print(f"⚠️  Output directory not found: {output_dir}")
        return None

    try:
        # Run comprehensive integrity check
        integrity_report = verify_output_integrity(output_dir)

        if integrity_report.issues:
            print(f"❌ Found {len(integrity_report.issues)} integrity errors:")
            for error in integrity_report.issues[:5]:
                print(f"   • {error}")
            if len(integrity_report.issues) > 5:
                print(f"   ... and {len(integrity_report.issues) - 5} more errors")

        if integrity_report.warnings:
            print(f"⚠️  Found {len(integrity_report.warnings)} integrity warnings:")
            for warning in integrity_report.warnings[:3]:
                print(f"   • {warning}")
            if len(integrity_report.warnings) > 3:
                print(f"   ... and {len(integrity_report.warnings) - 3} more warnings")

        if not integrity_report.issues and not integrity_report.warnings:
            print("✅ Output integrity is valid")

        return integrity_report

    except Exception as e:
        print(f"❌ Output integrity validation failed: {e}")
        return None


def run_comprehensive_audit():
    """Run comprehensive audit of the entire project."""
    if not INFRASTRUCTURE_AVAILABLE:
        return None

    print("\nRunning comprehensive project audit...")

    try:
        # Run full audit
        from infrastructure.validation import run_comprehensive_audit as audit_func
        audit_results = audit_func(project_root)

        if audit_results:
            print("✅ Comprehensive audit completed")

            # Generate audit report
            report_dir = project_root / "output" / "reports"
            report_dir.mkdir(parents=True, exist_ok=True)

            audit_report = generate_audit_report(audit_results, report_dir)
            if audit_report:
                print(f"✅ Audit report generated: {audit_report}")
                return audit_results

        return None

    except Exception as e:
        print(f"❌ Comprehensive audit failed: {e}")
        return None


def save_validation_report(results):
    """Save comprehensive validation report."""
    if not INFRASTRUCTURE_AVAILABLE or not results:
        return None

    print("\nSaving validation report...")

    report_dir = project_root / "output" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    # Create comprehensive report
    report = {
        "project": "prose_project",
        "timestamp": json.dumps(None, default=str),  # Will be filled by JSON
        "manuscript_validation": results.get("manuscript", {}),
        "cross_references": results.get("cross_refs", {}),
        "academic_standards": results.get("standards", {}),
        "link_validation": results.get("links", []),
        "output_integrity": {
            "errors": results.get("integrity", {}).issues if results.get("integrity") else [],
            "warnings": results.get("integrity", {}).warnings if results.get("integrity") else [],
            "recommendations": results.get("integrity", {}).recommendations if results.get("integrity") else [],
        } if results.get("integrity") else {},
        "comprehensive_audit": audit_to_dict(results.get("audit", {})),
    }

    # Add timestamp
    import datetime
    report["timestamp"] = datetime.datetime.now().isoformat()

    # Save JSON report
    json_path = report_dir / "manuscript_validation.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Generate markdown summary
    markdown_content = f"""# Manuscript Validation Report

**Project:** prose_project
**Timestamp:** {report["timestamp"]}

## Summary

"""

    # Add summary statistics
    total_issues = 0
    if results.get("manuscript", {}).get("errors"):
        total_issues += len(results["manuscript"]["errors"])
    if results.get("links"):
        total_issues += len(results["links"])
    if results.get("integrity"):
        total_issues += len(results["integrity"].issues)

    if total_issues == 0:
        markdown_content += "✅ **All validations passed!**\n\n"
    else:
        markdown_content += f"⚠️ **Found {total_issues} issues to address**\n\n"

    # Add detailed sections
    if results.get("manuscript"):
        ms = results["manuscript"]
        markdown_content += f"""## Manuscript Structure

- **Exit Code:** {ms.get('exit_code', 'Unknown')}
- **Errors:** {len(ms.get('errors', []))}
"""

        if ms.get("errors"):
            markdown_content += "\n**Validation Errors:**\n"
            for error in ms["errors"][:5]:
                markdown_content += f"- {error}\n"
            if len(ms["errors"]) > 5:
                markdown_content += f"- ... and {len(ms['errors']) - 5} more errors\n"

    if results.get("cross_refs"):
        cr = results["cross_refs"]
        valid_refs = sum(1 for valid in cr.values() if valid)
        total_refs = len(cr)
        markdown_content += f"\n## Cross-References\n\n- **Valid:** {valid_refs}/{total_refs}\n"

    if results.get("standards"):
        std = results["standards"]
        compliant = sum(1 for compliant in std.values() if compliant)
        total = len(std)
        markdown_content += f"\n## Academic Standards\n\n- **Compliant:** {compliant}/{total}\n"

    if results.get("links"):
        markdown_content += f"\n## Link Validation\n\n- **Issues:** {len(results['links'])}\n"

    if results.get("integrity"):
        integrity = results["integrity"]
        markdown_content += f"""\n## Output Integrity

- **Errors:** {len(integrity.issues)}
- **Warnings:** {len(integrity.warnings)}
- **Recommendations:** {len(integrity.recommendations)}
"""

        if integrity.recommendations:
            markdown_content += "\n**Recommendations:**\n"
            for rec in integrity.recommendations[:3]:
                markdown_content += f"- {rec}\n"

    # Save markdown report
    md_path = report_dir / "manuscript_validation.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"✅ Validation report saved:")
    print(f"   JSON: {json_path.name}")
    print(f"   Markdown: {md_path.name}")

    return {"json": json_path, "markdown": md_path}


def main():
    """Main validation function."""
    print("Starting manuscript validation...")
    print(f"Project root: {project_root}")

    if not INFRASTRUCTURE_AVAILABLE:
        print("❌ Infrastructure modules not available - cannot validate manuscript")
        return

    results = {}

    # Run all validations
    results["manuscript"] = validate_manuscript_structure()
    results["cross_refs"] = validate_cross_references()
    results["standards"] = validate_academic_standards()
    results["links"] = validate_links()
    results["integrity"] = validate_output_integrity()
    results["audit"] = run_comprehensive_audit()

    # Save comprehensive report
    reports = save_validation_report(results)

    print("\nManuscript validation complete!")

    # Summary
    success_count = sum(1 for result in results.values() if result is not None and not (
        hasattr(result, 'errors') and result.errors
    ) and not (
        isinstance(result, list) and len(result) > 0
    ))

    total_validations = len(results)

    if success_count == total_validations:
        print("🎉 All validations passed!")
    else:
        print(f"⚠️ {total_validations - success_count} validation(s) found issues")

    if reports:
        print(f"📊 Detailed reports saved to: output/reports/")

    print("\nOutput directory: output/reports/")


if __name__ == "__main__":
    main()