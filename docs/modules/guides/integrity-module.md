# Integrity & Validation Module

> **File integrity and cross-reference validation**

**Location:** `infrastructure/validation/integrity/checks.py`
**Quick Reference:** [Modules Guide](../modules-guide.md) | [API Reference](../../reference/api-reference.md)

---

## Key Features

- **File Integrity**: SHA256-based verification of output files
- **Cross-Reference Validation**: LaTeX reference integrity checking
- **Data Consistency**: Format and structure validation
- **Academic Standards**: Compliance with writing standards
- **Build Artifact Verification**: output validation

---

## Usage Examples

### Integrity Check

```python
from infrastructure.validation import verify_output_integrity
from pathlib import Path

# Verify entire output directory
report = verify_output_integrity(Path("output/"))

if report.overall_integrity:
    print("All integrity checks passed")
else:
    print("Integrity issues found:")
    for issue in report.issues:
        print(f"- {issue}")
    for warning in report.warnings:
        print(f"  {warning}")
```

### Cross-Reference Validation

```python
from infrastructure.validation import verify_cross_references
from pathlib import Path

# Check markdown files for reference integrity
markdown_files = [
    Path("manuscript/01_abstract.md"),
    Path("manuscript/02_introduction.md"),
]
integrity_status = verify_cross_references(markdown_files)

for ref_type, is_valid in integrity_status.items():
    print(f"{ref_type}: {'ok' if is_valid else 'FAIL'}")
```

---

## CLI Integration

```bash
# Automatic integrity validation (via pipeline)
uv run python scripts/04_validate_output.py --project template_code_project

# Manual integrity check
uv run python -m infrastructure.validation.cli integrity output/template_code_project/
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| File hash mismatches | Check if outputs are deterministic |
| Cross-reference errors | Verify all labels are properly defined |
| Data format issues | Ensure consistent data serialization |

---

**Related:** [Publishing Module](publishing-module.md) | [Reporting Module](reporting-module.md)
