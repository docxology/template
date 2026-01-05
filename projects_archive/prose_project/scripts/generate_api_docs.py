#!/usr/bin/env python3
"""API documentation generation script for prose project.

This script generates comprehensive API documentation from the project's source code:
1. Scans Python source files for functions, classes, and methods
2. Extracts docstrings and type hints
3. Generates markdown documentation tables
4. Integrates documentation into manuscript
"""

import sys
from pathlib import Path
import json

# Add project src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Add infrastructure imports (with graceful fallback)
try:
    # Ensure repo root is on path for infrastructure imports
    repo_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(repo_root))

    from infrastructure.documentation import (
        build_api_index,
        generate_markdown_table,
        inject_between_markers,
    )
    INFRASTRUCTURE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Infrastructure modules not available: {e}")
    INFRASTRUCTURE_AVAILABLE = False


def scan_source_code():
    """Scan project source code for API elements."""
    if not INFRASTRUCTURE_AVAILABLE:
        print("⚠️  Skipping API documentation - infrastructure not available")
        return None

    print("Scanning source code for API elements...")

    src_dir = project_root / "src"

    if not src_dir.exists():
        print(f"❌ Source directory not found: {src_dir}")
        return None

    try:
        # Build API index
        api_entries = build_api_index(str(src_dir))

        if not api_entries:
            print("⚠️  No API elements found in source code")
            return None

        print(f"✅ Found {len(api_entries)} API elements:")

        # Categorize by type
        functions = [e for e in api_entries if e.kind == 'function']
        classes = [e for e in api_entries if e.kind == 'class']
        methods = [e for e in api_entries if e.kind == 'method']
        constants = [e for e in api_entries if e.kind == 'constant']

        print(f"   • Functions: {len(functions)}")
        print(f"   • Classes: {len(classes)}")
        print(f"   • Methods: {len(methods)}")
        print(f"   • Constants: {len(constants)}")

        return {
            "all_entries": api_entries,
            "functions": functions,
            "classes": classes,
            "methods": methods,
            "constants": constants,
        }

    except Exception as e:
        print(f"❌ API scanning failed: {e}")
        return None


def generate_documentation_tables(api_data):
    """Generate markdown documentation tables."""
    if not api_data:
        return None

    print("\nGenerating documentation tables...")

    tables = {}

    try:
        # Generate table for all entries
        all_table = generate_markdown_table(api_data["all_entries"])
        if all_table:
            tables["complete_api"] = all_table
            print("✅ Generated complete API table")

        # Generate table for functions only
        if api_data["functions"]:
            functions_table = generate_markdown_table(api_data["functions"])
            if functions_table:
                tables["functions"] = functions_table
                print("✅ Generated functions table")

        # Generate table for classes only
        if api_data["classes"]:
            classes_table = generate_markdown_table(api_data["classes"])
            if classes_table:
                tables["classes"] = classes_table
                print("✅ Generated classes table")

        # Generate table for constants
        if api_data["constants"]:
            constants_table = generate_markdown_table(api_data["constants"])
            if constants_table:
                tables["constants"] = constants_table
                print("✅ Generated constants table")

        return tables

    except Exception as e:
        print(f"❌ Documentation table generation failed: {e}")
        return None


def save_documentation_files(tables):
    """Save generated documentation to files."""
    if not tables:
        return None

    print("\nSaving documentation files...")

    docs_dir = project_root / "output" / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    saved_files = {}

    try:
        # Save complete API reference
        if "complete_api" in tables:
            complete_path = docs_dir / "api_reference_complete.md"
            with open(complete_path, 'w', encoding='utf-8') as f:
                f.write("# Complete API Reference\n\n")
                f.write("This document contains a complete reference of all API elements in the project.\n\n")
                f.write(tables["complete_api"])
            saved_files["complete_api"] = complete_path
            print(f"✅ Saved complete API reference: {complete_path.name}")

        # Save individual tables
        for table_type, content in tables.items():
            if table_type != "complete_api":
                filename = f"api_reference_{table_type}.md"
                filepath = docs_dir / filename

                title = table_type.replace('_', ' ').title()

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"# API Reference - {title}\n\n")
                    f.write(f"This document contains {title.lower()} from the project API.\n\n")
                    f.write(content)

                saved_files[table_type] = filepath
                print(f"✅ Saved {table_type} reference: {filename}")

        # Save API statistics
        stats = {
            "total_entries": len(tables.get("complete_api", "").split('\n')) - 4 if "complete_api" in tables else 0,  # Subtract header lines
            "tables_generated": len(tables),
            "table_types": list(tables.keys()),
        }

        stats_path = docs_dir / "api_statistics.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)

        saved_files["statistics"] = stats_path
        print(f"✅ Saved API statistics: {stats_path.name}")

        return saved_files

    except Exception as e:
        print(f"❌ Failed to save documentation files: {e}")
        return None


def integrate_into_manuscript(tables):
    """Integrate API documentation into manuscript if markers exist."""
    if not tables or not INFRASTRUCTURE_AVAILABLE:
        return None

    print("\nChecking for manuscript integration markers...")

    manuscript_dir = project_root / "manuscript"
    integrated_files = []

    try:
        # Look for integration markers in manuscript files
        for md_file in manuscript_dir.glob("*.md"):
            content = md_file.read_text(encoding='utf-8')

            # Check for API reference markers
            begin_marker = "<!-- API_REFERENCE_BEGIN -->"
            end_marker = "<!-- API_REFERENCE_END -->"

            if begin_marker in content and end_marker in content:
                print(f"📝 Found integration markers in: {md_file.name}")

                # Use complete API table for integration
                if "complete_api" in tables:
                    new_content = inject_between_markers(
                        content,
                        begin_marker,
                        end_marker,
                        "\n## API Reference\n\n" + tables["complete_api"] + "\n"
                    )

                    # Save updated manuscript
                    with open(md_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)

                    integrated_files.append(md_file)
                    print(f"✅ Integrated API documentation into: {md_file.name}")

        if integrated_files:
            print(f"📄 Updated {len(integrated_files)} manuscript file(s)")
            return integrated_files
        else:
            print("ℹ️  No integration markers found in manuscript files")
            print("   (Add <!-- API_REFERENCE_BEGIN --> and <!-- API_REFERENCE_END --> to integrate)")
            return []

    except Exception as e:
        print(f"❌ Manuscript integration failed: {e}")
        return None


def generate_api_summary(api_data, tables):
    """Generate a summary of the API documentation."""
    if not api_data or not tables:
        return None

    print("\nGenerating API documentation summary...")

    try:
        summary = f"# API Documentation Summary\n\n"
        summary += f"This project contains {len(api_data['all_entries'])} API elements across {len(tables)} documentation tables.\n\n"
        summary += "## API Statistics\n\n"
        summary += f"- **Total API Elements**: {len(api_data['all_entries'])}\n"
        summary += f"- **Functions**: {len(api_data['functions'])}\n"
        summary += f"- **Classes**: {len(api_data['classes'])}\n"
        summary += f"- **Methods**: {len(api_data['methods'])}\n"
        summary += f"- **Constants**: {len(api_data['constants'])}\n"
        summary += f"- **Documentation Tables**: {len(tables)}\n\n"
        summary += "## Generated Files\n\n"

        # Add file list
        if "complete_api" in tables:
            summary += "- `api_reference_complete.md` - Complete API reference\n"
        if "functions" in tables:
            summary += "- `api_reference_functions.md` - Functions reference\n"
        if "classes" in tables:
            summary += "- `api_reference_classes.md` - Classes reference\n"
        if "constants" in tables:
            summary += "- `api_reference_constants.md` - Constants reference\n"

        summary += "- `api_statistics.json` - API documentation statistics\n\n"
        summary += "## Location\n\n"
        summary += "All API documentation files are saved in the `output/docs/` directory.\n\n"
        summary += "## Integration\n\n"
        summary += "API documentation can be automatically integrated into manuscript files by adding integration markers:\n\n"
        summary += "```markdown\n"
        summary += "<!-- API_REFERENCE_BEGIN -->\n"
        summary += "<!-- API_REFERENCE_END -->\n"
        summary += "```\n\n"
        summary += "When these markers are present in manuscript files, the complete API reference will be automatically inserted between them during documentation generation.\n"

        # Save summary
        docs_dir = project_root / "output" / "docs"
        summary_path = docs_dir / "api_documentation_summary.md"

        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)

        print(f"✅ Saved API documentation summary: {summary_path.name}")
        return summary_path

    except Exception as e:
        print(f"❌ Summary generation failed: {e}")
        return None


def main():
    print("Starting API documentation generation...")
    print(f"Project root: {project_root}")

    if not INFRASTRUCTURE_AVAILABLE:
        print("❌ Infrastructure modules not available - cannot generate API documentation")
        return

    # Scan source code
    api_data = scan_source_code()

    if not api_data:
        print("❌ No API data found - exiting")
        return

    # Generate documentation tables
    tables = generate_documentation_tables(api_data)

    if not tables:
        print("❌ No documentation tables generated - exiting")
        return

    # Save documentation files
    saved_files = save_documentation_files(tables)

    # Integrate into manuscript (optional)
    integrated_files = integrate_into_manuscript(tables)

    # Generate summary
    summary_file = generate_api_summary(api_data, tables)

    print("\nAPI documentation generation complete!")

    if saved_files:
        print(f"📁 Generated {len(saved_files)} documentation file(s)")

    if integrated_files:
        print(f"📄 Integrated into {len(integrated_files)} manuscript file(s)")
    else:
        print("ℹ️  No manuscript integration performed")

    print(f"📊 API Summary: {len(api_data['all_entries'])} elements documented")

    print("\nOutput directory: output/docs/")


if __name__ == "__main__":
    main()